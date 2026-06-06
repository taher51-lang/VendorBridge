"""
VendorBridge ERP – Auth Routes
================================
Endpoints for registration, login, token refresh, profile, and password management.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.auth_service import AuthService
from app.utils.response_helper import success_response, error_response
from app.utils.security import get_current_user_id

auth_bp = Blueprint("auth", __name__)


def _get_service():
    """Instantiate AuthService with a fresh DB session."""
    db = next(get_db())
    return AuthService(db), db


@auth_bp.route("/register", methods=["POST"])
def register():
    """POST /api/v1/auth/register — Register a new user."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    required = ["email", "password", "role"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(
            f"Missing required fields: {', '.join(missing)}", 422
        )

    valid_roles = ["admin", "procurement_officer", "manager", "vendor"]
    if data["role"] not in valid_roles:
        return error_response(
            f"Invalid role. Must be one of: {', '.join(valid_roles)}", 422
        )

    try:
        service, _ = _get_service()
        user = service.register(data)
        return success_response(user.to_dict(), "Account created successfully.", 201)
    except ValueError as e:
        return error_response(str(e), 409)
    except Exception as e:
        return error_response("Registration failed. Please try again.", 500)


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/v1/auth/login — Authenticate and return JWT tokens."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return error_response("Email and password are required.", 422)

    try:
        service, _ = _get_service()
        result = service.login(email, password)
        return success_response(result, "Login successful.")
    except PermissionError as e:
        return error_response(str(e), 403)
    except ValueError as e:
        return error_response(str(e), 401)
    except Exception:
        return error_response("Login failed. Please try again.", 500)


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """POST /api/v1/auth/refresh — Exchange refresh token for new access token."""
    try:
        user_id = get_jwt_identity()
        service, _ = _get_service()
        result = service.refresh_token(user_id)
        return success_response(result, "Token refreshed.")
    except (ValueError, PermissionError) as e:
        return error_response(str(e), 401)
    except Exception:
        return error_response("Token refresh failed.", 500)


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """GET /api/v1/auth/profile — Return the authenticated user's profile."""
    try:
        user_id = get_jwt_identity()
        service, _ = _get_service()
        profile = service.get_profile(user_id)
        return success_response(profile)
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception:
        return error_response("Could not fetch profile.", 500)


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """PUT /api/v1/auth/profile — Update the authenticated user's profile."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    try:
        user_id = get_jwt_identity()
        service, _ = _get_service()
        user = service.update_profile(user_id, data)
        return success_response(user.to_dict(), "Profile updated.")
    except ValueError as e:
        return error_response(str(e), 404)
    except Exception:
        return error_response("Profile update failed.", 500)


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """POST /api/v1/auth/change-password — Change authenticated user's password."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    current = data.get("current_password", "")
    new = data.get("new_password", "")

    if not current or not new:
        return error_response("current_password and new_password are required.", 422)

    if len(new) < 8:
        return error_response("New password must be at least 8 characters.", 422)

    try:
        user_id = get_jwt_identity()
        service, _ = _get_service()
        service.change_password(user_id, current, new)
        return success_response(None, "Password changed successfully.")
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception:
        return error_response("Password change failed.", 500)


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """POST /api/v1/auth/forgot-password — Request a password reset email."""
    data = request.get_json(silent=True)
    email = (data or {}).get("email", "").strip()

    # Always return 200 — never reveal whether the email exists
    if email:
        try:
            service, _ = _get_service()
            service.request_password_reset(email)
        except Exception:
            pass  # Swallow all errors silently

    return success_response(
        None,
        "If an account exists for that email, a reset link has been sent."
    )


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """POST /api/v1/auth/reset-password — Reset password using a valid token."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    token = data.get("token", "")
    new_password = data.get("new_password", "")

    if not token or not new_password:
        return error_response("token and new_password are required.", 422)

    if len(new_password) < 8:
        return error_response("Password must be at least 8 characters.", 422)

    try:
        service, _ = _get_service()
        service.reset_password(token, new_password)
        return success_response(None, "Password reset successfully. Please log in.")
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception:
        return error_response("Password reset failed.", 500)
