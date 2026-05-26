"""
Token API routes for retrieving valid OAuth tokens.
Used by consuming services (e.g., Organaizer) to get access tokens.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from api.database import get_db, OAuthToken
from api.oauth.google import get_valid_token as get_google_token

router = APIRouter()


@router.get("/{provider}/{account_email}")
async def get_token(
    provider: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Get valid access token for provider and account.
    Automatically refreshes token if expired.

    Path params:
    - provider: OAuth provider (google, microsoft)
    - account_email: Email of connected account

    Query params:
    - user_id: User ID (default: 1 for MVP)
    """
    if provider == "google":
        access_token = await get_google_token(account_email, user_id, db)

        # Get token from database for metadata
        token = db.query(OAuthToken).filter(
            OAuthToken.user_id == user_id,
            OAuthToken.provider == provider,
            OAuthToken.account_email == account_email,
            OAuthToken.is_valid == True
        ).first()

        expires_in = int((token.token_expiry - datetime.utcnow()).total_seconds())

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": expires_in,
            "scope": token.scopes
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{provider}' not supported yet"
        )


@router.get("/{provider}/{account_email}/status")
async def get_token_status(
    provider: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Check token status without retrieving the token.

    Path params:
    - provider: OAuth provider (google, microsoft)
    - account_email: Email of connected account

    Query params:
    - user_id: User ID (default: 1 for MVP)
    """
    token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.provider == provider,
        OAuthToken.account_email == account_email
    ).first()

    if not token:
        raise HTTPException(
            status_code=404,
            detail=f"No {provider} token found for {account_email}"
        )

    expires_in = int((token.token_expiry - datetime.utcnow()).total_seconds())
    is_expired = expires_in <= 0

    return {
        "is_valid": token.is_valid and not is_expired,
        "is_expired": is_expired,
        "expires_in": expires_in if not is_expired else 0,
        "last_refresh": token.last_refresh_at.isoformat() if token.last_refresh_at else None,
        "scopes": token.scopes.split(",") if token.scopes else []
    }
