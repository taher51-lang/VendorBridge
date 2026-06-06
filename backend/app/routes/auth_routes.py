"""
VendorBridge ERP – Auth Routes
================================
Endpoints for registration, login, token refresh, profile, and password management.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user_schema import (
    UserCreateSchema,
    LoginSchema,
    PasswordChangeSchema,
    UserUpdateSchema,
)
from app.utils.response_helper import success_response, error_response

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/v1/auth/register
    Register a new user.
    """
    # 1. Parse JSON body from request
    # 2. Validate with UserCreateSchema().load(data)
    # 3. Get db session via get_db()
    # 4. Call AuthService(db).register(validated_data)
    # 5. Return success_response(user.to_dict(), 201)
    # 6. Catch ValidationError → return error_response(422)
    # 7. Catch ConflictError → return error_response(409)
    pass


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/v1/auth/login
    Authenticate and return JWT tokens.
    """
    # 1. Parse JSON body
    # 2. Validate with LoginSchema().load(data)
    # 3. Call AuthService(db).login(email, password)
    # 4. Return success_response({access_token, refresh_token, user})
    # 5. Catch AuthenticationError → 401
    pass


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    POST /api/v1/auth/refresh
    Exchange a valid refresh token for a new access token.
    """
    # 1. Get user_id from get_jwt_identity()
    # 2. Call AuthService(db).refresh_token(user_id)
    # 3. Return new access_token
    pass


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """
    GET /api/v1/auth/profile
    Return the authenticated user's profile.
    """
    # 1. Get user_id from get_jwt_identity()
    # 2. Call AuthService(db).get_profile(user_id)
    # 3. Return success_response(profile)
    pass


@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """
    PUT /api/v1/auth/profile
    Update the authenticated user's profile.
    """
    # 1. Parse and validate with UserUpdateSchema
    # 2. Call service to update profile
    # 3. Return updated user
    pass


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    """
    POST /api/v1/auth/change-password
    Change the authenticated user's password.
    """
    # 1. Validate with PasswordChangeSchema
    # 2. Call AuthService(db).change_password(user_id, current, new)
    # 3. Return success message
    pass


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    POST /api/v1/auth/forgot-password
    Request a password reset email.
    """
    # 1. Extract email from body
    # 2. Call AuthService(db).request_password_reset(email)
    # 3. Always return 200 (don't leak whether email exists)
    pass


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    POST /api/v1/auth/reset-password
    Reset password using a valid token.
    """
    # 1. Extract token and new_password from body
    # 2. Call AuthService(db).reset_password(token, new_password)
    # 3. Return success message
    pass
