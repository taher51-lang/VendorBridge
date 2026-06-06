"""
VendorBridge ERP – User Repository
====================================
Data-access layer for User model.
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):
    """
    Extends BaseRepository with User-specific queries.
    """

    model = User

    def __init__(self, db: Session):
        """Initialize with a SQLAlchemy session."""
        # TODO: Call super().__init__(db)
        pass

    def get_by_email(self, email: str):
        """
        Look up a user by their email address.

        Args:
            email: The email to search for (case-insensitive).

        Returns:
            User instance or None.
        """
        # TODO: Implement:
        #   1. Query User where func.lower(User.email) == email.lower()
        #   2. Filter deleted_at IS NULL
        #   3. Return .first()
        pass

    def get_by_role(self, role: str, page: int = 1, per_page: int = 20):
        """
        List users filtered by their role.

        Args:
            role: One of 'admin', 'procurement_officer', 'manager', 'vendor'.
            page, per_page: Pagination.

        Returns:
            Tuple of (list[User], total_count).
        """
        # TODO: Implement paginated query filtered by User.role == role
        pass

    def update_last_login(self, user_id: str):
        """
        Set last_login_at to now for the given user.

        Args:
            user_id: UUID of the user.
        """
        # TODO: Implement:
        #   1. Fetch user by id
        #   2. Set user.last_login_at = datetime.utcnow()
        #   3. Commit
        pass

    def verify_email(self, user_id: str):
        """
        Mark a user's email as verified.

        Args:
            user_id: UUID of the user.
        """
        # TODO: Implement:
        #   1. Fetch user by id
        #   2. Set user.email_verified_at = datetime.utcnow()
        #   3. Commit
        pass

    def deactivate(self, user_id: str):
        """
        Disable a user account (set is_active = False).
        """
        # TODO: Implement soft deactivation (not deletion)
        pass
