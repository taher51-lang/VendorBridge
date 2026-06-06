"""
VendorBridge ERP – RFQ Repository
===================================
Data-access layer for RFQ, RFQItem, and RFQVendorAssignment models.
Raw SQLAlchemy queries only — no business logic here.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.rfq import RFQ, RFQItem, RFQVendorAssignment
from app.repositories.base_repo import BaseRepository


class RFQRepository(BaseRepository):
    """Queries for Requests for Quotation."""

    model = RFQ

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_number(self, rfq_number: str):
        """
        Look up an RFQ by its human-readable number (e.g. RFQ-2024-0001).
        """
        return self.db.query(RFQ).filter(
            RFQ.rfq_number == rfq_number,
            RFQ.deleted_at.is_(None)
        ).first()

    def get_by_creator(self, user_id: str, page: int = 1, per_page: int = 20):
        """
        List RFQs created by a specific procurement officer, paginated.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        query = self.db.query(RFQ).filter(
            RFQ.created_by == user_id,
            RFQ.deleted_at.is_(None)
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List RFQs filtered by status, paginated.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        query = (
            self.db.query(RFQ)
            .filter(
                RFQ.status == status,
                RFQ.deleted_at.is_(None),
            )
            .order_by(RFQ.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_all_paginated(self, page: int = 1, per_page: int = 20):
        """
        Return all non-deleted RFQs, paginated.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        query = self.db.query(RFQ).filter(
            RFQ.status == status,
            RFQ.deleted_at.is_(None)
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_open_for_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List open RFQs where the vendor has been invited.
        Joins through RFQVendorAssignment.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        query = self.db.query(RFQ).join(
            RFQVendorAssignment, RFQVendorAssignment.rfq_id == RFQ.id
        ).filter(
            RFQVendorAssignment.vendor_id == vendor_id,
            RFQ.status == 'open',
            RFQ.deleted_at.is_(None),
            RFQVendorAssignment.deleted_at.is_(None)
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_for_vendor_all(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all RFQs (any status) where the vendor has been assigned.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        query = (
            self.db.query(RFQ)
            .join(
                RFQVendorAssignment,
                RFQVendorAssignment.rfq_id == RFQ.id,
            )
            .filter(
                RFQVendorAssignment.vendor_id == vendor_id,
                RFQ.deleted_at.is_(None),
            )
            .order_by(RFQ.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def assign_vendors(self, rfq_id: str, vendor_ids: list) -> list:
        """
        Bulk-create RFQVendorAssignment rows for a list of vendor IDs.
        """
        assignments = []
        for v_id in vendor_ids:
            # Check if assignment already exists
            existing = self.db.query(RFQVendorAssignment).filter_by(
                rfq_id=rfq_id, vendor_id=v_id
            ).first()
            if not existing:
                assignment = RFQVendorAssignment(
                    rfq_id=rfq_id,
                    vendor_id=v_id,
                    status='invited'
                )
                self.db.add(assignment)
                assignments.append(assignment)
        self.db.commit()
        return assignments

        return new_assignments

    def mark_vendor_viewed(self, rfq_id: str, vendor_id: str) -> bool:
        """
        Set viewed_at timestamp on the vendor's assignment.
        """
        from datetime import datetime, timezone
        assignment = self.db.query(RFQVendorAssignment).filter_by(
            rfq_id=rfq_id, vendor_id=vendor_id
        ).first()
        if assignment:
            assignment.viewed_at = datetime.now(timezone.utc)
            assignment.status = 'acknowledged'
            self.db.commit()
        return assignment


class RFQItemRepository(BaseRepository):
    """Queries for RFQ line items."""

    model = RFQItem

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_rfq(self, rfq_id: str) -> list:
        """
        Return all items for a given RFQ, ordered by sort_order.
        """
        return self.db.query(RFQItem).filter(
            RFQItem.rfq_id == rfq_id,
            RFQItem.deleted_at.is_(None)
        ).order_by(RFQItem.sort_order).all()

