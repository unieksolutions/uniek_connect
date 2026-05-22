"""
uNiek Connect - Central OAuth Connector Service
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config import get_settings
from api.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 uNiek Connect starting...")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Database: {settings.database_url}")
    logger.info(f"   API: {settings.api_host}:{settings.api_port}")

    # Initialize database
    init_db()
    logger.info("✅ Database initialized")

    # TODO: Start background scheduler for token refresh
    logger.info("⏰ Background scheduler: not yet implemented")

    yield

    # Shutdown
    logger.info("👋 uNiek Connect shutting down...")


# Create FastAPI app
app = FastAPI(
    title="uNiek Connect API",
    description="Central OAuth connector service for external APIs (calendars, tasks, email, messaging)",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "uniek-connect",
        "version": "0.1.0",
        "status": "running",
        "environment": settings.environment,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "oauth": "/auth/{provider}/",
            "tokens": "/api/tokens/",
            "calendars": "/calendars/{provider}/",
            "tasks": "/tasks/{provider}/",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "uniek-connect",
        "version": "0.1.0",
        "environment": settings.environment,
        "database": "connected",
        "token_refresh_scheduler": "not_yet_implemented"
    }


# TODO: Add route modules
# from api.routes import oauth, tokens, calendars, tasks, admin
# app.include_router(oauth.router, prefix="/auth", tags=["oauth"])
# app.include_router(tokens.router, prefix="/api/tokens", tags=["tokens"])
# app.include_router(calendars.router, prefix="/calendars", tags=["calendars"])
# app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.environment == "dev"),
        log_level=settings.log_level.lower()
    )
