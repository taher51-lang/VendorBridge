"""VendorBridge ERP – Exceptions Package."""

# Re-export custom exceptions for convenient imports.
from app.exceptions.handlers import (
    AppError,
    NotFoundError,
    ConflictError,
    AuthenticationError,
    ForbiddenError,
    ValidationError,
    BusinessLogicError,
)

