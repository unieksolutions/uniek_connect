"""
Database models and session management for uNiek Connect.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, create_engine, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from api.config import get_settings

Base = declarative_base()

# Get settings
settings = get_settings()


class Organization(Base):
    """Organization model for multi-tenant support."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User model within organizations."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_users_org", "organization_id"),
        Index("idx_users_email", "email"),
        Index("idx_users_org_email", "organization_id", "email", unique=True),
    )


class OAuthToken(Base):
    """OAuth tokens for external providers."""
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'google', 'microsoft', 'apple', 'nextcloud'
    account_email = Column(String(255), nullable=False)

    # Tokens
    access_token = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text)  # Fernet encrypted
    token_expiry = Column(DateTime, nullable=False)

    # Metadata
    scopes = Column(Text)  # Comma-separated list
    token_type = Column(String(50), default="Bearer")

    # Status
    is_valid = Column(Boolean, default=True)
    last_refresh_at = Column(DateTime)
    revoked_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_oauth_tokens_user", "user_id"),
        Index("idx_oauth_tokens_provider", "provider"),
        Index("idx_oauth_tokens_expiry", "token_expiry"),
        Index("idx_oauth_tokens_valid", "is_valid"),
        Index("idx_oauth_tokens_user_provider_email", "user_id", "provider", "account_email", unique=True),
    )


class APIKey(Base):
    """API keys for consuming services."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)  # SHA256 hash
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    name = Column(String(255), nullable=False)  # "Organaizer API Key"

    # Permissions
    scopes = Column(Text)  # Comma-separated: 'tokens.read', 'calendars.read', etc.

    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_api_keys_org", "organization_id"),
    )


class AuditLog(Base):
    """Security audit trail."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    # Event details
    action = Column(String(100), nullable=False)  # 'oauth.authorized', 'token.refreshed', 'api.called'
    resource_type = Column(String(50))  # 'oauth_token', 'api_key', etc.
    resource_id = Column(Integer)

    # Request details
    ip_address = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(Text)

    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_audit_logs_org", "organization_id"),
        Index("idx_audit_logs_user", "user_id"),
        Index("idx_audit_logs_action", "action"),
    )


# Database engine and session
engine = create_engine(
    settings.database_url,
    echo=(settings.environment == "dev"),
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables."""
    Base.metadata.create_all(bind=engine)

    # Create default organization and user for MVP
    db = SessionLocal()
    try:
        # Check if default organization exists
        org = db.query(Organization).filter(Organization.slug == "default").first()
        if not org:
            org = Organization(name="Default Organization", slug="default")
            db.add(org)
            db.commit()
            db.refresh(org)

            # Create default user
            user = User(
                organization_id=org.id,
                email="niek@uniek.solutions",
                name="Niek",
                is_active=True
            )
            db.add(user)
            db.commit()
    finally:
        db.close()


def get_db() -> Session:
    """Get database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
