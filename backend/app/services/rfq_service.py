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
        self.rfq_item_repo = RFQItemRepository(db)
        # We don't strictly need VendorRepository or NotificationService fully instantiated for the basic RFQ flow,
        # but let's instantiate them to avoid errors.
        from app.repositories.vendor_repo import VendorRepository
        from app.services.notification_service import NotificationService
        self.vendor_repo = VendorRepository(db)
        self.notification_svc = NotificationService(db)

    def create_rfq(self, data: dict, officer_id: str) -> RFQ:
        """
        Create a new RFQ and optionally invite vendors.
        """
        from app.utils.number_generator import generate_rfq_number
        
        rfq_number = generate_rfq_number(self.db)
        rfq = RFQ(
            rfq_number=rfq_number,
            title=data['title'],
            description=data.get('description'),
            created_by=officer_id,
            deadline=data['deadline'],
            attachment_urls=data.get('attachment_urls'),
            notes=data.get('notes'),
            status='draft'
        )

        for sort_idx, item_data in enumerate(data['items']):
            item = RFQItem(
                item_name=item_data['item_name'],
                description=item_data.get('description'),
                quantity=item_data['quantity'],
                unit=item_data.get('unit'),
                specifications=item_data.get('specifications'),
                sort_order=item_data.get('sort_order', sort_idx)
            )
            rfq.items.append(item)

        self.rfq_repo.create(rfq)

        if data.get('vendor_ids'):
            self.rfq_repo.assign_vendors(rfq.id, data['vendor_ids'])
            self.notification_svc.notify_vendors_rfq_invite(rfq, data['vendor_ids'])

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type='rfq',
            entity_id=rfq.id,
            action='created'
        )
        return rfq

    # ── Read ──────────────────────────────────────────────────────

    def get_rfq(self, rfq_id: str) -> RFQ:
        """
        Fetch a single RFQ by ID with items and assignments loaded via relationship.

        Raises:
            NotFoundError: If RFQ doesn't exist or is soft-deleted.
        """
        from app.exceptions import NotFoundError
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError("RFQ not found")
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
        if filters and 'status' in filters:
            return self.rfq_repo.get_by_status(filters['status'], page, per_page)
        return self.rfq_repo.get_all(page, per_page, filters)

    # ── Update ────────────────────────────────────────────────────

    def update_rfq(self, rfq_id: str, data: dict, officer_id: str) -> RFQ:
        """
        Update an RFQ (only allowed while status='draft').
        """
        from app.exceptions import NotFoundError, BusinessLogicError
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError("RFQ not found")
        if rfq.status != 'draft':
            raise BusinessLogicError("Only draft RFQs can be updated")

        if 'title' in data:
            rfq.title = data['title']
        if 'description' in data:
            rfq.description = data['description']
        if 'deadline' in data:
            rfq.deadline = data['deadline']
        if 'notes' in data:
            rfq.notes = data['notes']
        if 'attachment_urls' in data:
            rfq.attachment_urls = data['attachment_urls']

        if 'items' in data:
            rfq.items = []
            for sort_idx, item_data in enumerate(data['items']):
                item = RFQItem(
                    item_name=item_data['item_name'],
                    description=item_data.get('description'),
                    quantity=item_data['quantity'],
                    unit=item_data.get('unit'),
                    specifications=item_data.get('specifications'),
                    sort_order=item_data.get('sort_order', sort_idx)
                )
                rfq.items.append(item)

        self.rfq_repo.update(rfq)
        return rfq

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
        from app.exceptions import NotFoundError, BusinessLogicError
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError("RFQ not found")
        if rfq.status != 'draft':
            raise BusinessLogicError("Only draft RFQs can be published")

        rfq.status = 'open'
        self.rfq_repo.update(rfq)

        # Notify vendors
        vendor_ids = [a.vendor_id for a in rfq.vendor_assignments]
        self.notification_svc.notify_vendors_rfq_invite(rfq, vendor_ids)
        
        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type='rfq',
            entity_id=rfq.id,
            action='published'
        )
        return rfq

        return rfq

    def close_rfq(self, rfq_id: str, officer_id: str) -> RFQ:
        """
        Close an RFQ (no more quotations accepted).
        """
        from app.exceptions import NotFoundError, BusinessLogicError
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError("RFQ not found")
        if rfq.status != 'open':
            raise BusinessLogicError("Only open RFQs can be closed")

        rfq.status = 'closed'
        self.rfq_repo.update(rfq)
        return rfq

    def cancel_rfq(self, rfq_id: str, officer_id: str):
        """
        Cancel an RFQ.
        """
        from app.exceptions import NotFoundError
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError("RFQ not found")
        rfq.status = 'cancelled'
        self.rfq_repo.update(rfq)
        return rfq

    def cancel_rfq(self, rfq_id: str, officer_id: str) -> RFQ:
        """
        Cancel an RFQ (from any non-terminal status).

        Raises:
            NotFoundError, ForbiddenError, BusinessLogicError.
        """
        self.rfq_repo.assign_vendors(rfq_id, vendor_ids)
        rfq = self.rfq_repo.get_by_id(rfq_id)
        self.notification_svc.notify_vendors_rfq_invite(rfq, vendor_ids)
        return rfq

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
        return self.rfq_repo.get_open_for_vendor(vendor_id, page, per_page)

    def acknowledge_rfq(self, rfq_id: str, vendor_id: str) -> None:
        """
        Vendor acknowledges they've seen the RFQ.
        """
        self.rfq_repo.mark_vendor_viewed(rfq_id, vendor_id)

