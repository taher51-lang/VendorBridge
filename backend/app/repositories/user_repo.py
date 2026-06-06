"""
VendorBridge ERP – User Repository
====================================
Data-access layer for the User model.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):
    """Extends BaseRepository with User-specific queries."""

    model = User

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_email(self, email: str):
        """
        Look up a user by email address (case-insensitive).
        Returns User instance or None.
        """
        return (
            self.db.query(User)
            .filter(
                func.lower(User.email) == email.lower(),
                User.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_role(self, role: str, page: int = 1, per_page: int = 20):
        """
        List users filtered by role with pagination.
        Returns (list[User], total_count).
        """
        query = (
            self.db.query(User)
            .filter(User.role == role, User.deleted_at.is_(None))
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def update_last_login(self, user_id: str):
        """Set last_login_at to now for the given user."""
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            self.db.commit()

    def verify_email(self, user_id: str):
        """Mark a user's email as verified."""
        user = self.get_by_id(user_id)
        if user:
            user.email_verified_at = datetime.utcnow()
            self.db.commit()

    def deactivate(self, user_id: str):
        """Disable a user account (set is_active = False)."""
        user = self.get_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
