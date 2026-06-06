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
        return (
            self.db.query(RFQ)
            .filter(
                RFQ.rfq_number == rfq_number,
                RFQ.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_creator(self, user_id: str, page: int = 1, per_page: int = 20):
        """
        List RFQs created by a specific procurement officer, paginated.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        query = (
            self.db.query(RFQ)
            .filter(
                RFQ.created_by == user_id,
                RFQ.deleted_at.is_(None),
            )
            .order_by(RFQ.created_at.desc())
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
        query = (
            self.db.query(RFQ)
            .filter(RFQ.deleted_at.is_(None))
            .order_by(RFQ.created_at.desc())
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
        query = (
            self.db.query(RFQ)
            .join(
                RFQVendorAssignment,
                RFQVendorAssignment.rfq_id == RFQ.id,
            )
            .filter(
                RFQVendorAssignment.vendor_id == vendor_id,
                RFQ.status == "open",
                RFQ.deleted_at.is_(None),
            )
            .order_by(RFQ.deadline.asc())
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
        Skips vendor IDs that already have an assignment for this RFQ.

        Args:
            rfq_id: The RFQ to assign vendors to.
            vendor_ids: List of vendor UUID strings.

        Returns:
            List of newly created RFQVendorAssignment objects.
        """
        # Find already-assigned vendor IDs to avoid unique constraint violations
        existing = {
            row.vendor_id
            for row in self.db.query(RFQVendorAssignment.vendor_id)
            .filter(RFQVendorAssignment.rfq_id == rfq_id)
            .all()
        }

        new_assignments = []
        for vendor_id in vendor_ids:
            if vendor_id in existing:
                continue
            assignment = RFQVendorAssignment(
                rfq_id=rfq_id,
                vendor_id=vendor_id,
            )
            self.db.add(assignment)
            new_assignments.append(assignment)

        if new_assignments:
            self.db.commit()
            for a in new_assignments:
                self.db.refresh(a)

        return new_assignments

    def mark_vendor_viewed(self, rfq_id: str, vendor_id: str) -> bool:
        """
        Set viewed_at timestamp and status='acknowledged' on the vendor's assignment.
        Called when a vendor first opens the RFQ detail page.

        Returns:
            True if updated, False if assignment not found.
        """
        assignment = (
            self.db.query(RFQVendorAssignment)
            .filter(
                RFQVendorAssignment.rfq_id == rfq_id,
                RFQVendorAssignment.vendor_id == vendor_id,
            )
            .first()
        )
        if not assignment:
            return False

        if assignment.viewed_at is None:
            assignment.viewed_at = datetime.now(timezone.utc)
        assignment.status = "acknowledged"
        self.db.commit()
        return True

    def get_assigned_vendor_ids(self, rfq_id: str) -> list:
        """
        Return a list of vendor IDs currently assigned to an RFQ.
        """
        rows = (
            self.db.query(RFQVendorAssignment.vendor_id)
            .filter(RFQVendorAssignment.rfq_id == rfq_id)
            .all()
        )
        return [row.vendor_id for row in rows]


class RFQItemRepository(BaseRepository):
    """Queries for RFQ line items."""

    model = RFQItem

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_rfq(self, rfq_id: str) -> list:
        """
        Return all items for a given RFQ, ordered by sort_order.
        """
        return (
            self.db.query(RFQItem)
            .filter(
                RFQItem.rfq_id == rfq_id,
                RFQItem.deleted_at.is_(None),
            )
            .order_by(RFQItem.sort_order, RFQItem.created_at)
            .all()
        )

    def replace_items(self, rfq_id: str, items_data: list) -> list:
        """
        Replace all existing items for an RFQ with a new set.
        Used when updating a draft RFQ.

        Args:
            rfq_id: The RFQ's ID.
            items_data: List of dicts with item field values.

        Returns:
            List of newly created RFQItem objects.
        """
        # Soft-delete existing items
        now = datetime.now(timezone.utc)
        (
            self.db.query(RFQItem)
            .filter(RFQItem.rfq_id == rfq_id, RFQItem.deleted_at.is_(None))
            .update({"deleted_at": now}, synchronize_session=False)
        )

        new_items = []
        for idx, item_data in enumerate(items_data):
            item = RFQItem(
                rfq_id=rfq_id,
                item_name=item_data["item_name"],
                description=item_data.get("description"),
                quantity=item_data["quantity"],
                unit=item_data.get("unit"),
                specifications=item_data.get("specifications"),
                sort_order=item_data.get("sort_order", idx),
            )
            self.db.add(item)
            new_items.append(item)

        self.db.commit()
        for item in new_items:
            self.db.refresh(item)
        return new_items
