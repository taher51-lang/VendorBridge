"""
VendorBridge ERP – Application Configuration
=============================================
Defines configuration classes for different environments.
Loaded by the app factory based on FLASK_ENV or the config_name argument.
"""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """
    Shared configuration inherited by all environments.
    All values should come from environment variables with sensible defaults.
    """

    # ── Flask Core ────────────────────────────────────────────────
    # SECRET_KEY: used for session signing, CSRF tokens, etc.
    # Must be overridden in production via the SECRET_KEY env var.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-key")

    # ── Database (SQLAlchemy) ─────────────────────────────────────
    # DATABASE_URL: full PostgreSQL connection string.
    # Format: postgresql://user:pass@host:port/dbname
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vendorbridge:vendorbridge@localhost:5432/vendorbridge_db")

    # ── JWT ───────────────────────────────────────────────────────
    # JWT_SECRET_KEY: signing key for JSON Web Tokens.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-fallback")
    # JWT_ACCESS_TOKEN_EXPIRES: lifetime of access tokens.
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600")))
    # JWT_REFRESH_TOKEN_EXPIRES: lifetime of refresh tokens.
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "2592000")))

    # ── Flask-Mail ────────────────────────────────────────────────
    # MAIL_SERVER: SMTP host (e.g. smtp.gmail.com)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    # MAIL_PORT: SMTP port
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    # MAIL_USE_TLS: enable STARTTLS
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
    # MAIL_USERNAME / MAIL_PASSWORD: SMTP credentials
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    # MAIL_DEFAULT_SENDER: default "From" address
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@vendorbridge.com")

    # ── CORS ──────────────────────────────────────────────────────
    # CORS_ORIGINS: comma-separated allowed origins
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    # ── File Uploads ──────────────────────────────────────────────
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16 MB

    # ── PDF ───────────────────────────────────────────────────────
    PDF_OUTPUT_DIR = os.getenv("PDF_OUTPUT_DIR", "generated_pdfs")


class DevelopmentConfig(BaseConfig):
    """Development-specific overrides."""
    # TODO: Enable debug mode and any dev-only extensions.
    # - Set DEBUG = True
    # - Optionally enable SQL echo for query logging
    pass


class ProductionConfig(BaseConfig):
    """Production-specific overrides."""
    # TODO: Harden settings for production.
    # - Set DEBUG = False
    # - Enforce that SECRET_KEY and JWT_SECRET_KEY come from env
    # - Consider stricter CORS, HTTPS-only cookies, etc.
    pass


class TestingConfig(BaseConfig):
    """Test-specific overrides."""
    # TODO: Point at an isolated test database.
    # - Set TESTING = True
    # - Override DATABASE_URL to use a test-specific database
    #   e.g. postgresql://vendorbridge:vendorbridge@localhost:5432/vendorbridge_test
    # - Disable CSRF, rate limiting, email sending, etc.
    pass


# ── Config selector ──────────────────────────────────────────────
# Maps a human-readable name (used by the app factory) to a class.
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
