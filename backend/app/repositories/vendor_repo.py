"""
VendorBridge ERP – Vendor Repository
======================================
Data-access layer for Vendor, VendorCategory, and VendorRating models.
Raw SQLAlchemy queries only — no business logic here.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.vendor import Vendor, VendorCategory, VendorRating
from app.repositories.base_repo import BaseRepository


class VendorCategoryRepository(BaseRepository):
    """Queries for vendor categories (hierarchical)."""

    model = VendorCategory

    def __init__(self, db: Session):
        super().__init__(db)

    def get_root_categories(self):
        """
        Return all top-level categories (parent_id IS NULL).
        Subcategories are loaded via the SQLAlchemy relationship.
        """
        return (
            self.db.query(VendorCategory)
            .filter(
                VendorCategory.parent_id.is_(None),
                VendorCategory.deleted_at.is_(None),
            )
            .order_by(VendorCategory.name)
            .all()
        )

    def get_by_name(self, name: str):
        """
        Look up a category by its unique name (case-insensitive).
        """
        return (
            self.db.query(VendorCategory)
            .filter(
                func.lower(VendorCategory.name) == name.lower(),
                VendorCategory.deleted_at.is_(None),
            )
            .first()
        )

    def get_all_flat(self):
        """Return all active categories as a flat list."""
        return (
            self.db.query(VendorCategory)
            .filter(VendorCategory.deleted_at.is_(None))
            .order_by(VendorCategory.name)
            .all()
        )


class VendorRepository(BaseRepository):
    """Queries for vendor profiles."""

    model = Vendor

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_user_id(self, user_id: str):
        """
        Fetch the vendor profile linked to a user account.
        """
        return (
            self.db.query(Vendor)
            .filter(
                Vendor.user_id == user_id,
                Vendor.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List vendors filtered by their approval status, paginated.

        Args:
            status: One of 'pending', 'active', 'suspended', 'blacklisted'.

        Returns:
            Tuple of (list[Vendor], total_count).
        """
        query = (
            self.db.query(Vendor)
            .filter(
                Vendor.status == status,
                Vendor.deleted_at.is_(None),
            )
            .order_by(Vendor.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_category(self, category_id: str, page: int = 1, per_page: int = 20):
        """
        List vendors within a specific category, paginated.

        Returns:
            Tuple of (list[Vendor], total_count).
        """
        query = (
            self.db.query(Vendor)
            .filter(
                Vendor.category_id == category_id,
                Vendor.deleted_at.is_(None),
            )
            .order_by(Vendor.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def update_avg_rating(self, vendor_id: str) -> None:
        """
        Recalculate and persist the vendor's average rating
        from all VendorRating rows.
        """
        avg = (
            self.db.query(func.avg(VendorRating.overall_score))
            .filter(VendorRating.vendor_id == vendor_id)
            .scalar()
        )
        vendor = self.get_by_id(vendor_id)
        if vendor:
            vendor.avg_rating = float(avg) if avg is not None else 0.00
            self.db.commit()

    def search(self, query_str: str, page: int = 1, per_page: int = 20):
        """
        Full-text search across company_name, city, state, gst_number.
        Uses ILIKE for case-insensitive partial matching.

        Returns:
            Tuple of (list[Vendor], total_count).
        """
        pattern = f"%{query_str}%"
        query = (
            self.db.query(Vendor)
            .filter(
                Vendor.deleted_at.is_(None),
                (
                    Vendor.company_name.ilike(pattern)
                    | Vendor.city.ilike(pattern)
                    | Vendor.state.ilike(pattern)
                    | Vendor.gst_number.ilike(pattern)
                ),
            )
            .order_by(Vendor.company_name)
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_all_paginated(self, page: int = 1, per_page: int = 20):
        """
        Return all non-deleted vendors, paginated.

        Returns:
            Tuple of (list[Vendor], total_count).
        """
        query = (
            self.db.query(Vendor)
            .filter(Vendor.deleted_at.is_(None))
            .order_by(Vendor.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total


class VendorRatingRepository(BaseRepository):
    """Queries for vendor ratings."""

    model = VendorRating

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all ratings for a specific vendor, paginated.

        Returns:
            Tuple of (list[VendorRating], total_count).
        """
        query = (
            self.db.query(VendorRating)
            .filter(
                VendorRating.vendor_id == vendor_id,
                VendorRating.deleted_at.is_(None),
            )
            .order_by(VendorRating.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_po(self, po_id: str):
        """
        Get the rating (if any) for a specific purchase order.
        """
        return (
            self.db.query(VendorRating)
            .filter(
                VendorRating.po_id == po_id,
                VendorRating.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_vendor_and_po(self, vendor_id: str, po_id: str):
        """
        Check if a rating already exists for a (vendor, po) pair.
        Used to enforce the UniqueConstraint at the service layer.
        """
        return (
            self.db.query(VendorRating)
            .filter(
                VendorRating.vendor_id == vendor_id,
                VendorRating.po_id == po_id,
                VendorRating.deleted_at.is_(None),
            )
            .first()
        )
