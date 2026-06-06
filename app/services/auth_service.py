"""
VendorBridge ERP – Auth Service
================================
Handles registration, login, token refresh, and password management.
"""

import uuid
from datetime import datetime

from flask_jwt_extended import create_access_token, create_refresh_token
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repo import UserRepository


class AuthService:
    """Business logic for authentication and account lifecycle."""

    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)
        self.db = db

    def register(self, data: dict) -> User:
        """
        Register a new user account.
        Raises ValueError if email already exists.
        """
        existing = self.user_repo.get_by_email(data["email"])
        if existing:
            raise ValueError("An account with this email already exists.")

        user = User(
            id=str(uuid.uuid4()),
            email=data["email"].lower().strip(),
            full_name=data.get("full_name", ""),
            role=data["role"],
            phone=data.get("phone"),
        )
        user.set_password(data["password"])

        # If registering as vendor, a Vendor profile will be created
        # by VendorService after this returns — keep auth concerns separate.

        self.user_repo.create(user)
        return user

    def login(self, email: str, password: str) -> dict:
        """
        Authenticate a user and return JWT tokens.
        Raises ValueError on bad credentials or inactive account.
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password.")

        if not user.check_password(password):
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise PermissionError("This account has been deactivated. Contact support.")

        self.user_repo.update_last_login(user.id)

        additional_claims = {"role": user.role}
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims,
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            additional_claims=additional_claims,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }

    def refresh_token(self, user_id: str) -> dict:
        """
        Issue a new access token from a valid refresh token.
        Raises ValueError if user not found or inactive.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        if not user.is_active:
            raise PermissionError("Account is deactivated.")

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"role": user.role},
        )
        return {"access_token": access_token}

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        """
        Change a user's password after verifying the current one.
        Raises ValueError if current password is wrong.
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        if not user.check_password(current_password):
            raise ValueError("Current password is incorrect.")

        user.set_password(new_password)
        self.user_repo.update(user)

    def request_password_reset(self, email: str) -> None:
        """
        Generate a password-reset token and email it.
        Silently does nothing if email not found (no leak).
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return  # Silent — don't reveal whether email exists

        # Generate a short-lived reset token using JWT
        reset_token = create_access_token(
            identity=user.id,
            additional_claims={"purpose": "password_reset"},
            expires_delta=__import__("datetime").timedelta(minutes=30),
        )

        # TODO: plug into email_sender when Flask-Mail is configured:
        # email_sender.send_password_reset(user.email, reset_token)
        print(f"[DEV] Password reset token for {email}: {reset_token}")

    def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset a user's password using a valid reset token.
        Raises ValueError if token is invalid or expired.
        """
        from flask_jwt_extended import decode_token
        try:
            decoded = decode_token(token)
        except Exception:
            raise ValueError("Invalid or expired reset token.")

        claims = decoded.get("additional_claims", {}) or decoded.get("sub", {})
        if decoded.get("additional_claims", {}).get("purpose") != "password_reset":
            raise ValueError("Invalid reset token.")

        user_id = decoded.get("sub")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        user.set_password(new_password)
        self.user_repo.update(user)

    def get_profile(self, user_id: str) -> dict:
        """Return the authenticated user's profile data."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")
        return user.to_dict()

    def update_profile(self, user_id: str, data: dict) -> User:
        """Update allowed profile fields (full_name, phone, avatar_url)."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found.")

        allowed_fields = ["full_name", "phone", "avatar_url"]
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        self.user_repo.update(user)
        return user
