"""
VendorBridge ERP – Vendor Repository
======================================
Data-access layer for Vendor, VendorCategory, and VendorRating models.
"""

from sqlalchemy.orm import Session

from app.models.vendor import Vendor, VendorCategory, VendorRating
from app.repositories.base_repo import BaseRepository


class VendorCategoryRepository(BaseRepository):
    """Queries for vendor categories (hierarchical)."""

    model = VendorCategory

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_root_categories(self):
        """
        Return all top-level categories (parent_id IS NULL).
        """
        # TODO: Implement:
        #   1. Query VendorCategory where parent_id IS NULL
        #   2. Filter deleted_at IS NULL
        #   3. Return list
        pass

    def get_by_name(self, name: str):
        """
        Look up a category by its unique name.
        """
        # TODO: Implement case-insensitive lookup
        pass


class VendorRepository(BaseRepository):
    """Queries for vendor profiles."""

    model = Vendor

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_user_id(self, user_id: str):
        """
        Fetch the vendor profile linked to a user account.
        """
        # TODO: Query Vendor where user_id == user_id, deleted_at IS NULL
        pass

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List vendors filtered by their approval status.

        Args:
            status: One of 'pending', 'active', 'suspended', 'blacklisted'.
        """
        # TODO: Implement paginated + filtered query
        pass

    def get_by_category(self, category_id: str, page: int = 1, per_page: int = 20):
        """
        List vendors within a specific category.
        """
        # TODO: Implement paginated query filtered by category_id
        pass

    def update_avg_rating(self, vendor_id: str):
        """
        Recalculate and persist the vendor's average rating
        from all VendorRating rows.
        """
        # TODO: Implement:
        #   1. Query AVG(overall_score) from VendorRating where vendor_id
        #   2. Update vendor.avg_rating
        #   3. Commit
        pass

    def search(self, query: str, page: int = 1, per_page: int = 20):
        """
        Full-text search across company_name, city, state, gst_number.
        """
        # TODO: Implement ILIKE search across multiple columns
        pass


class VendorRatingRepository(BaseRepository):
    """Queries for vendor ratings."""

    model = VendorRating

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all ratings for a specific vendor.
        """
        # TODO: Implement paginated query
        pass

    def get_by_po(self, po_id: str):
        """
        Get the rating (if any) for a specific purchase order.
        """
        # TODO: Query VendorRating where po_id == po_id
        pass
