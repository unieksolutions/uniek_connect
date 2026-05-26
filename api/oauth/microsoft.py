"""
Microsoft OAuth implementation for uNiek Connect.
Handles OAuth 2.0 authorization flow for Microsoft Graph APIs.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
import msal
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx

from api.config import get_settings
from api.database import get_db, OAuthToken, User
from api.oauth.encryption import encrypt_token, decrypt_token

router = APIRouter()
settings = get_settings()

# Microsoft Graph scopes for calendar and tasks
MICROSOFT_SCOPES = [
    "https://graph.microsoft.com/Calendars.Read",
    "https://graph.microsoft.com/Tasks.Read",
    "https://graph.microsoft.com/User.Read",
    "offline_access",  # Required for refresh tokens
]


def get_msal_app(redirect_uri: Optional[str] = None) -> msal.ConfidentialClientApplication:
    """Create MSAL app for Microsoft OAuth."""
    if not settings.microsoft_client_id or not settings.microsoft_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Microsoft OAuth not configured. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET."
        )

    authority = f"https://login.microsoftonline.com/{settings.microsoft_tenant or 'common'}"

    return msal.ConfidentialClientApplication(
        client_id=settings.microsoft_client_id,
        client_credential=settings.microsoft_client_secret,
        authority=authority,
    )


@router.get("/login")
async def microsoft_login(
    request: Request,
    user_id: Optional[int] = 1,  # MVP: hardcoded user
    redirect_after: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Initiate Microsoft OAuth flow.

    Query params:
    - user_id: User ID (default: 1 for MVP)
    - redirect_after: URL to redirect after successful auth
    """
    # Create MSAL app
    msal_app = get_msal_app()

    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Get authorization URL
    auth_url = msal_app.get_authorization_request_url(
        scopes=MICROSOFT_SCOPES,
        state=state,
        redirect_uri=settings.microsoft_redirect_uri,
        prompt="consent",  # Force consent to ensure refresh token
    )

    # Store state in session for CSRF protection
    request.session["oauth_state"] = state
    request.session["user_id"] = user_id
    if redirect_after:
        request.session["redirect_after"] = redirect_after

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def microsoft_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Microsoft OAuth callback.
    Exchange authorization code for tokens and store in database.
    """
    # Check for errors
    if error:
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {error} - {error_description or 'No description'}"
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
        msal_app = get_msal_app()
        result = msal_app.acquire_token_by_authorization_code(
            code=code,
            scopes=MICROSOFT_SCOPES,
            redirect_uri=settings.microsoft_redirect_uri,
        )

        if "error" in result:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to acquire token: {result.get('error_description', result['error'])}"
            )

        access_token = result.get("access_token")
        refresh_token = result.get("refresh_token")
        expires_in = result.get("expires_in", 3600)

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to exchange code for token: {str(e)}"
        )

    # Get user email from Microsoft Graph
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            user_info = response.json()
            account_email = user_info.get("userPrincipalName") or user_info.get("mail")

            if not account_email:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get user email from Microsoft Graph"
                )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user email: {str(e)}"
        )

    # Encrypt refresh token
    refresh_token_encrypted = None
    if refresh_token:
        refresh_token_encrypted = encrypt_token(refresh_token)

    # Calculate token expiry
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

    # Check if token already exists
    existing_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == "microsoft",
        OAuthToken.account_email == account_email
    ).first()

    if existing_token:
        # Update existing token
        existing_token.access_token = access_token
        existing_token.refresh_token_encrypted = refresh_token_encrypted
        existing_token.token_expiry = token_expiry
        existing_token.scopes = ",".join(MICROSOFT_SCOPES)
        existing_token.is_valid = True
        existing_token.last_refresh_at = datetime.utcnow()
        existing_token.updated_at = datetime.utcnow()
    else:
        # Create new token
        new_token = OAuthToken(
            user_id=user_id,
            provider="microsoft",
            account_email=account_email,
            access_token=access_token,
            refresh_token_encrypted=refresh_token_encrypted,
            token_expiry=token_expiry,
            scopes=",".join(MICROSOFT_SCOPES),
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

    # Return success response
    return {
        "success": True,
        "provider": "microsoft",
        "account_email": account_email,
        "scopes": MICROSOFT_SCOPES,
        "message": "Microsoft account connected successfully",
        "redirect": redirect_after
    }


@router.delete("/revoke")
async def microsoft_revoke(
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Revoke Microsoft OAuth token.
    Removes token from database and marks as revoked.
    Note: Microsoft doesn't provide a simple token revocation endpoint.
    """
    # Find token
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == "microsoft",
        OAuthToken.account_email == account_email
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail=f"No Microsoft token found for {account_email}"
        )

    # Mark as revoked in database
    # Note: Microsoft doesn't have a simple revoke endpoint like Google
    # Users need to revoke access manually in their Microsoft account settings
    token.is_valid = False
    token.revoked_at = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "message": f"Microsoft token revoked locally for {account_email}. "
                   f"User should also revoke access in Microsoft account settings.",
        "revoke_url": "https://account.live.com/consent/Manage"
    }


async def get_valid_token(
    account_email: str,
    user_id: int,
    db: Session
) -> str:
    """
    Get valid access token for Microsoft account.
    Refreshes token if expired.
    """
    # Find token
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == "microsoft",
        OAuthToken.account_email == account_email,
        OAuthToken.is_valid == True
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail=f"No valid Microsoft token found for {account_email}"
        )

    # Check if token is expired (with 5-minute buffer)
    if token.token_expiry < datetime.utcnow() + timedelta(minutes=5):
        # Refresh token
        if not token.refresh_token_encrypted:
            raise HTTPException(
                status_code=401,
                detail="Token expired and no refresh token available"
            )

        try:
            refresh_token = decrypt_token(token.refresh_token_encrypted)
            msal_app = get_msal_app()

            # Refresh using MSAL
            result = msal_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=MICROSOFT_SCOPES,
            )

            if "error" in result:
                raise HTTPException(
                    status_code=401,
                    detail=f"Failed to refresh token: {result.get('error_description', result['error'])}"
                )

            # Update token in database
            token.access_token = result.get("access_token")
            expires_in = result.get("expires_in", 3600)
            token.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
            token.last_refresh_at = datetime.utcnow()
            token.updated_at = datetime.utcnow()

            # Update refresh token if new one provided
            if "refresh_token" in result:
                token.refresh_token_encrypted = encrypt_token(result["refresh_token"])

            db.commit()

        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Failed to refresh token: {str(e)}"
            )

    return token.access_token
