"""
Configuration management for uNiek Connect.
Uses Pydantic Settings to load from environment variables.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = Field(
        default="sqlite:///./data/dev.db",
        env="DATABASE_URL"
    )

    # Token encryption
    token_encryption_key: str = Field(
        default="",  # Must be set in production
        env="TOKEN_ENCRYPTION_KEY"
    )

    # API Server
    api_host: str = Field(default="127.0.0.1", env="API_HOST")
    api_port: int = Field(default=61300, env="API_PORT")
    environment: str = Field(default="dev", env="ENVIRONMENT")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://192.168.42.21:61050",
        env="CORS_ORIGINS"
    )

    # Google OAuth
    google_client_id: str = Field(default="", env="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(default="", env="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:61300/auth/google/callback",
        env="GOOGLE_REDIRECT_URI"
    )

    # Microsoft OAuth
    microsoft_client_id: str = Field(default="", env="MICROSOFT_CLIENT_ID")
    microsoft_client_secret: str = Field(default="", env="MICROSOFT_CLIENT_SECRET")
    microsoft_redirect_uri: str = Field(
        default="http://localhost:61300/auth/microsoft/callback",
        env="MICROSOFT_REDIRECT_URI"
    )
    microsoft_tenant: str = Field(default="common", env="MICROSOFT_TENANT")

    # Rate limiting (optional)
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
