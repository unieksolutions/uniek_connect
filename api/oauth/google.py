"""
Google OAuth implementation for uNiek Connect.
Handles OAuth 2.0 authorization flow for Google APIs.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from api.config import get_settings
from api.database import get_db, OAuthToken, User
from api.oauth.encryption import encrypt_token, decrypt_token

router = APIRouter()
settings = get_settings()

# Google OAuth scopes for calendar and tasks
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/tasks.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]


def create_oauth_flow(redirect_uri: Optional[str] = None) -> Flow:
    """Create Google OAuth flow."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    client_config = {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri or settings.google_redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=GOOGLE_SCOPES,
        redirect_uri=redirect_uri or settings.google_redirect_uri,
    )

    return flow


@router.get("/login")
async def google_login(
    request: Request,
    user_id: Optional[int] = 1,  # MVP: hardcoded user
    redirect_after: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Initiate Google OAuth flow.

    Query params:
    - user_id: User ID (default: 1 for MVP)
    - redirect_after: URL to redirect after successful auth
    """
    # Create OAuth flow
    flow = create_oauth_flow()

    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type="offline",  # Request refresh token
        include_granted_scopes="true",  # Incremental authorization
        prompt="consent",  # Force consent screen to get refresh token
    )

    # Store state in session for CSRF protection
    request.session["oauth_state"] = state
    request.session["user_id"] = user_id
    if redirect_after:
        request.session["redirect_after"] = redirect_after

    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Exchange authorization code for tokens and store in database.
    """
    # Check for errors
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {error}"
        )

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing code or state parameter"
        )

    # Validate state (CSRF protection)
    session_state = request.session.get("oauth_state")
    if not session_state or session_state != state:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter (CSRF protection)"
        )

    # Get user_id from session
    user_id = request.session.get("user_id", 1)

    # Exchange code for tokens
    try:
        flow = create_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code for token: {str(e)}"
        )

    # Get user email from token
    try:
        from googleapiclient.discovery import build
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        account_email = user_info.get("email")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user email: {str(e)}"
        )

    # Encrypt refresh token
    refresh_token_encrypted = None
    if credentials.refresh_token:
        refresh_token_encrypted = encrypt_token(credentials.refresh_token)

    # Calculate token expiry
    token_expiry = datetime.utcnow() + timedelta(seconds=3600)  # Google tokens expire in 1 hour
    if credentials.expiry:
        token_expiry = credentials.expiry

    # Check if token already exists
    existing_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == "google",
        OAuthToken.account_email == account_email
    ).first()

    if existing_token:
        # Update existing token
        existing_token.access_token = credentials.token
        existing_token.refresh_token_encrypted = refresh_token_encrypted
        existing_token.token_expiry = token_expiry
        existing_token.scopes = ",".join(GOOGLE_SCOPES)
        existing_token.is_valid = True
        existing_token.last_refresh_at = datetime.utcnow()
        existing_token.updated_at = datetime.utcnow()
    else:
        # Create new token
        new_token = OAuthToken(
            user_id=user_id,
            provider="google",
            account_email=account_email,
            access_token=credentials.token,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expiry=token_expiry,
            scopes=",".join(GOOGLE_SCOPES),
            token_type="Bearer",
            is_valid=True,
            last_refresh_at=datetime.utcnow(),
        )
        db.add(new_token)

    db.commit()

    # Get redirect URL from session
    redirect_after = request.session.get("redirect_after", "/")

    # Clear session
    request.session.pop("oauth_state", None)
    request.session.pop("user_id", None)
    request.session.pop("redirect_after", None)

    # Return success response or redirect
    return {
        "success": True,
        "provider": "google",
        "account_email": account_email,
        "scopes": GOOGLE_SCOPES,
        "message": "Google account connected successfully",
        "redirect": redirect_after
    }


@router.delete("/revoke")
async def google_revoke(
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Revoke Google OAuth token.
    Removes token from database and revokes with Google.
    """
    # Find token
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == "google",
        OAuthToken.account_email == account_email
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail=f"No Google token found for {account_email}"
        )

    # Try to revoke with Google
    try:
        if token.refresh_token_encrypted:
            refresh_token = decrypt_token(token.refresh_token_encrypted)
            credentials = Credentials(
                token=token.access_token,
                refresh_token=refresh_token,
            )
            credentials.revoke(GoogleRequest())
    except Exception as e:
        # Log error but continue with local deletion
        print(f"Warning: Failed to revoke token with Google: {str(e)}")

    # Mark as revoked in database
    token.is_valid = False
    token.revoked_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": f"Google token revoked for {account_email}"
    }


async def get_valid_token(
    account_email: str,
    user_id: int,
    db: Session
) -> str:
    """
    Get valid access token for Google account.
    Refreshes token if expired.
    """
    # Find token
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == "google",
        OAuthToken.account_email == account_email,
        OAuthToken.is_valid == True
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail=f"No valid Google token found for {account_email}"
        )

    # Check if token is expired
    if token.token_expiry < datetime.utcnow():
        # Refresh token
        if not token.refresh_token_encrypted:
            raise HTTPException(
                status_code=401,
                detail="Token expired and no refresh token available"
            )

        try:
            refresh_token = decrypt_token(token.refresh_token_encrypted)
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
            )

            # Refresh
            credentials.refresh(GoogleRequest())

            # Update token in database
            token.access_token = credentials.token
            token.token_expiry = credentials.expiry
            token.last_refresh_at = datetime.utcnow()
            token.updated_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Failed to refresh token: {str(e)}"
            )

    return token.access_token
