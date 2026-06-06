"""
VendorBridge ERP – Error Handlers
===================================
Custom exception classes and Flask error handler registration.
"""

from flask import Flask, jsonify


# ── Custom Exception Classes ──────────────────────────────────────

class AppError(Exception):
    """Base class for all application errors."""

    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        """
        Args:
            message: Human-readable error description.
            status_code: HTTP status code to return.
        """
        # TODO: Store message and status_code as instance attributes
        # self.message = message
        # self.status_code = status_code
        # super().__init__(self.message)
        pass


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        # TODO: Call super().__init__(message, 404)
        pass


class ConflictError(AppError):
    """Raised when a resource conflicts with existing data (e.g. duplicate email)."""

    def __init__(self, message: str = "Resource already exists"):
        # TODO: Call super().__init__(message, 409)
        pass


class AuthenticationError(AppError):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials"):
        # TODO: Call super().__init__(message, 401)
        pass


class ForbiddenError(AppError):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = "Access denied"):
        # TODO: Call super().__init__(message, 403)
        pass


class ValidationError(AppError):
    """Raised when input data fails validation."""

    def __init__(self, message: str = "Validation error", errors: dict = None):
        """
        Args:
            errors: Dict of field-level errors from Marshmallow.
        """
        # TODO:
        # self.errors = errors or {}
        # super().__init__(message, 422)
        pass


class BusinessLogicError(AppError):
    """Raised when a business rule is violated (e.g. invalid status transition)."""

    def __init__(self, message: str = "Operation not allowed"):
        # TODO: Call super().__init__(message, 400)
        pass


# ── Flask Error Handler Registration ─────────────────────────────

def register_error_handlers(app: Flask):
    """
    Register global error handlers on the Flask app.
    Called by the app factory in app/__init__.py.

    Implementation:
        1. Register handler for AppError (and all subclasses):
           - Return JSON: {"success": false, "message": e.message}
           - Status code from e.status_code
           - If ValidationError, include "errors" field.

        2. Register handler for Marshmallow's ValidationError:
           - Return 422 with field-level errors.

        3. Register handler for 404 (unknown routes):
           - Return {"success": false, "message": "Not found"}

        4. Register handler for 405 (method not allowed):
           - Return {"success": false, "message": "Method not allowed"}

        5. Register handler for 500 (unhandled exceptions):
           - Log the exception
           - Return {"success": false, "message": "Internal server error"}
    """
    # TODO: Implement all error handlers using @app.errorhandler
    #
    # @app.errorhandler(AppError)
    # def handle_app_error(e):
    #     response = {"success": False, "message": e.message}
    #     if isinstance(e, ValidationError) and e.errors:
    #         response["errors"] = e.errors
    #     return jsonify(response), e.status_code
    #
    # @app.errorhandler(404)
    # def handle_404(e):
    #     return jsonify({"success": False, "message": "Not found"}), 404
    #
    # ... etc.
    pass
