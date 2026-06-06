"""
VendorBridge ERP – RFQ Service
================================
Business logic for creating, updating, and managing RFQs.
Sits between rfq_routes and rfq repositories. Never touches the HTTP layer.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.rfq_repo import RFQRepository, RFQItemRepository
from app.repositories.vendor_repo import VendorRepository
from app.models.rfq import RFQ, RFQItem
from app.services.notification_service import NotificationService
from app.utils.number_generator import generate_rfq_number
from app.exceptions.handlers import (
    NotFoundError,
    BusinessLogicError,
    ForbiddenError,
)


class RFQService:
    """
    Handles all business logic related to RFQs.
    Sits between routes and repositories. Never touches the HTTP layer.
    """

    def __init__(self, db: Session):
        self.db = db
        self.rfq_repo = RFQRepository(db)
        self.item_repo = RFQItemRepository(db)
        self.vendor_repo = VendorRepository(db)
        self.notification_svc = NotificationService(db)

    # ── Create ────────────────────────────────────────────────────

    def create_rfq(self, data: dict, officer_id: str) -> RFQ:
        """
        Create a new RFQ and optionally invite vendors.

        Args:
            data: Validated dict from RFQCreateSchema.
            officer_id: UUID of the procurement officer creating the RFQ.

        Returns:
            The created RFQ object (with items loaded).
        """
        # 1. Generate human-readable RFQ number
        rfq_number = generate_rfq_number(self.db)

        # 2. Normalize deadline to UTC-aware datetime
        deadline = data["deadline"]
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        # 3. Create the RFQ
        rfq = RFQ(
            id=str(uuid.uuid4()),
            rfq_number=rfq_number,
            title=data["title"],
            description=data.get("description"),
            created_by=officer_id,
            deadline=deadline,
            status="draft",
            notes=data.get("notes"),
            attachment_urls=data.get("attachment_urls"),
        )
        self.rfq_repo.create(rfq)

        # 4. Create line items
        for idx, item_data in enumerate(data.get("items", [])):
            item = RFQItem(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                item_name=item_data["item_name"],
                description=item_data.get("description"),
                quantity=item_data["quantity"],
                unit=item_data.get("unit"),
                specifications=item_data.get("specifications"),
                sort_order=item_data.get("sort_order", idx),
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(rfq)

        # 5. Assign vendors if vendor_ids provided
        vendor_ids = data.get("vendor_ids") or []
        if vendor_ids:
            self.rfq_repo.assign_vendors(rfq.id, vendor_ids)

        # 6. Audit log
        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="rfq",
            entity_id=rfq.id,
            action="created",
            metadata={"rfq_number": rfq_number, "vendor_count": len(vendor_ids)},
        )

        return rfq

    # ── Read ──────────────────────────────────────────────────────

    def get_rfq(self, rfq_id: str) -> RFQ:
        """
        Fetch a single RFQ by ID with items and assignments loaded via relationship.

        Raises:
            NotFoundError: If RFQ doesn't exist or is soft-deleted.
        """
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError(f"RFQ with ID '{rfq_id}' not found.")
        return rfq

    def list_rfqs(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """
        Paginated listing of RFQs.

        Supported filter keys: 'status', 'created_by'.

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        filters = filters or {}

        if filters.get("status"):
            return self.rfq_repo.get_by_status(filters["status"], page, per_page)

        if filters.get("created_by"):
            return self.rfq_repo.get_by_creator(filters["created_by"], page, per_page)

        return self.rfq_repo.get_all_paginated(page, per_page)

    def get_vendor_rfqs(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List RFQs that a vendor has been invited to (all statuses).

        Returns:
            Tuple of (list[RFQ], total_count).
        """
        return self.rfq_repo.get_for_vendor_all(vendor_id, page, per_page)

    # ── Update ────────────────────────────────────────────────────

    def update_rfq(self, rfq_id: str, data: dict, officer_id: str) -> RFQ:
        """
        Update an RFQ. Only allowed while status='draft'.

        Args:
            data: Validated dict from RFQUpdateSchema.
            officer_id: The calling user's ID (must be creator).

        Returns:
            Updated RFQ instance.

        Raises:
            NotFoundError, ForbiddenError, BusinessLogicError.
        """
        rfq = self.get_rfq(rfq_id)

        if rfq.created_by != officer_id:
            raise ForbiddenError("Only the RFQ creator can update this RFQ.")

        if rfq.status != "draft":
            raise BusinessLogicError(
                f"RFQ cannot be updated in '{rfq.status}' status. Only draft RFQs can be edited."
            )

        # Apply simple scalar fields
        updatable = ["title", "description", "notes", "attachment_urls"]
        for field in updatable:
            if data.get(field) is not None:
                setattr(rfq, field, data[field])

        if data.get("deadline") is not None:
            deadline = data["deadline"]
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            rfq.deadline = deadline

        # Replace items if provided
        if data.get("items") is not None:
            self.item_repo.replace_items(rfq_id, data["items"])

        # Update vendor assignments if provided
        if data.get("vendor_ids") is not None:
            self.rfq_repo.assign_vendors(rfq_id, data["vendor_ids"])

        self.rfq_repo.update(rfq)

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="rfq",
            entity_id=rfq_id,
            action="updated",
        )

        self.db.refresh(rfq)
        return rfq

    # ── State Transitions ─────────────────────────────────────────

    def publish_rfq(self, rfq_id: str, officer_id: str) -> RFQ:
        """
        Transition RFQ from 'draft' to 'open', making it visible to vendors.

        Validates:
          - Status must be 'draft'
          - Deadline must be in the future
          - Must have at least one line item

        Also sends 'rfq_invite' notifications to all assigned vendors.

        Raises:
            NotFoundError, ForbiddenError, BusinessLogicError.
        """
        rfq = self.get_rfq(rfq_id)

        if rfq.created_by != officer_id:
            raise ForbiddenError("Only the RFQ creator can publish this RFQ.")

        if rfq.status != "draft":
            raise BusinessLogicError(
                f"Cannot publish RFQ in '{rfq.status}' status. Only draft RFQs can be published."
            )

        # Validate deadline is in the future
        now = datetime.now(timezone.utc)
        deadline = rfq.deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        if deadline <= now:
            raise BusinessLogicError("Cannot publish RFQ with a past deadline.")

        # Validate at least one item exists
        items = self.item_repo.get_by_rfq(rfq_id)
        if not items:
            raise BusinessLogicError("Cannot publish RFQ with no line items.")

        rfq.status = "open"
        self.rfq_repo.update(rfq)

        # Notify assigned vendors
        vendor_ids = self.rfq_repo.get_assigned_vendor_ids(rfq_id)
        if vendor_ids:
            self.notification_svc.notify_vendors_rfq_invite(rfq, vendor_ids)

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="rfq",
            entity_id=rfq_id,
            action="published",
            metadata={"vendor_count": len(vendor_ids)},
        )

        return rfq

    def close_rfq(self, rfq_id: str, officer_id: str) -> RFQ:
        """
        Close an RFQ (no more quotations accepted).

        Valid from: 'open' or 'under_review' status.

        Raises:
            NotFoundError, ForbiddenError, BusinessLogicError.
        """
        rfq = self.get_rfq(rfq_id)

        if rfq.created_by != officer_id:
            raise ForbiddenError("Only the RFQ creator can close this RFQ.")

        if rfq.status not in ("open", "under_review"):
            raise BusinessLogicError(
                f"Cannot close RFQ in '{rfq.status}' status. RFQ must be 'open' or 'under_review'."
            )

        rfq.status = "closed"
        self.rfq_repo.update(rfq)

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="rfq",
            entity_id=rfq_id,
            action="closed",
        )

        return rfq

    def cancel_rfq(self, rfq_id: str, officer_id: str) -> RFQ:
        """
        Cancel an RFQ (from any non-terminal status).

        Raises:
            NotFoundError, ForbiddenError, BusinessLogicError.
        """
        rfq = self.get_rfq(rfq_id)

        if rfq.created_by != officer_id:
            raise ForbiddenError("Only the RFQ creator can cancel this RFQ.")

        TERMINAL_STATUSES = ("cancelled", "awarded", "closed")
        if rfq.status in TERMINAL_STATUSES:
            raise BusinessLogicError(
                f"Cannot cancel RFQ in '{rfq.status}' status."
            )

        rfq.status = "cancelled"
        self.rfq_repo.update(rfq)

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="rfq",
            entity_id=rfq_id,
            action="cancelled",
        )

        return rfq

    # ── Vendor Invitation ─────────────────────────────────────────

    def invite_vendors(self, rfq_id: str, vendor_ids: list, officer_id: str) -> list:
        """
        Add vendors to an existing RFQ's invite list.
        Allowed when RFQ is in 'draft' or 'open' status.

        Args:
            rfq_id: The RFQ to add vendors to.
            vendor_ids: List of Vendor UUID strings.
            officer_id: Caller's user ID.

        Returns:
            List of newly created RFQVendorAssignment objects.

        Raises:
            NotFoundError, ForbiddenError, BusinessLogicError.
        """
        rfq = self.get_rfq(rfq_id)

        if rfq.status not in ("draft", "open"):
            raise BusinessLogicError(
                f"Cannot invite vendors to RFQ in '{rfq.status}' status."
            )

        new_assignments = self.rfq_repo.assign_vendors(rfq_id, vendor_ids)

        # If RFQ is already open, notify the newly invited vendors immediately
        if rfq.status == "open" and new_assignments:
            new_vendor_ids = [a.vendor_id for a in new_assignments]
            self.notification_svc.notify_vendors_rfq_invite(rfq, new_vendor_ids)

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="rfq",
            entity_id=rfq_id,
            action="vendors_invited",
            metadata={"vendor_ids": vendor_ids, "new_count": len(new_assignments)},
        )

        return new_assignments

    # ── Vendor Acknowledgement ────────────────────────────────────

    def acknowledge_rfq(self, rfq_id: str, vendor_id: str) -> None:
        """
        Vendor acknowledges they've seen the RFQ.
        Sets viewed_at and status='acknowledged' on the assignment.
        Silent if vendor is not assigned.
        """
        self.rfq_repo.mark_vendor_viewed(rfq_id, vendor_id)
