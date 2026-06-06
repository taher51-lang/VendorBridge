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
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)


class ConflictError(AppError):
    """Raised when a resource conflicts with existing data (e.g. duplicate email)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, 409)


class AuthenticationError(AppError):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, 401)


class ForbiddenError(AppError):
    """Raised when a user lacks permission for an action."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)


class ValidationError(AppError):
    """Raised when input data fails validation."""

    def __init__(self, message: str = "Validation error", errors: dict = None):
        self.errors = errors or {}
        super().__init__(message, 422)


class BusinessLogicError(AppError):
    """Raised when a business rule is violated (e.g. invalid status transition)."""

    def __init__(self, message: str = "Operation not allowed"):
        super().__init__(message, 400)


# ── Flask Error Handler Registration ─────────────────────────────

def register_error_handlers(app: Flask):
    """
    Register global error handlers on the Flask app.
    Called by the app factory in app/__init__.py.
    """
    @app.errorhandler(AppError)
    def handle_app_error(e):
        response = {"success": False, "message": e.message}
        if isinstance(e, ValidationError) and e.errors:
            response["errors"] = e.errors
        return jsonify(response), e.status_code

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"success": False, "message": "Not found"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def handle_500(e):
        import logging
        logging.exception("Unhandled server exception:")
        return jsonify({"success": False, "message": "Internal server error"}), 500

