"""
VendorBridge ERP – Purchase Order Service
==========================================
Business logic for PO issuance, status tracking, and fulfillment.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.repositories.po_repo import PurchaseOrderRepository
from app.repositories.quotation_repo import QuotationRepository
from app.repositories.approval_repo import ApprovalWorkflowRepository
from app.models.purchase_order import PurchaseOrder, POItem
from app.services.notification_service import NotificationService
from app.utils.number_generator import generate_po_number


class PurchaseOrderService:
    """
    Handles all PO-related business logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.po_repo = PurchaseOrderRepository(db)
        self.quotation_repo = QuotationRepository(db)
        self.workflow_repo = ApprovalWorkflowRepository(db)
        self.notification_svc = NotificationService(db)

    def create_po(self, quotation_id: str, data: dict, created_by: str):
        """
        Issue a Purchase Order from an approved quotation.

        Args:
            quotation_id: UUID of the approved quotation.
            data: Optional overrides (delivery_address, terms).
            created_by: UUID of the issuing user.

        Returns:
            The created PurchaseOrder.
        """
        from app.exceptions import NotFoundError, ConflictError, BusinessLogicError

        # 1. Fetch quotation → validate it exists and is selected
        quotation = self.quotation_repo.get_by_id(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.status != "selected":
            raise BusinessLogicError(
                "Quotation must be selected before a PO can be issued"
            )

        # 2. Check that an approved workflow exists for this quotation
        workflow = self.workflow_repo.get_by_quotation(quotation_id)
        if not workflow or workflow.status != "approved":
            raise BusinessLogicError(
                "Quotation must have a fully approved workflow before PO issuance"
            )

        # 3. Check no existing PO for this quotation
        existing = self.po_repo.get_by_quotation(quotation_id)
        if existing:
            raise ConflictError("A PO already exists for this quotation")

        # 4. Generate po_number
        po_number = generate_po_number(self.db)

        # 5. Create PurchaseOrder model
        po = PurchaseOrder(
            po_number=po_number,
            quotation_id=quotation_id,
            vendor_id=quotation.vendor_id,
            created_by=created_by,
            workflow_id=workflow.id,
            delivery_address=data.get("delivery_address"),
            expected_delivery=data.get("expected_delivery"),
            subtotal=quotation.subtotal,
            tax_amount=quotation.tax_amount,
            total_amount=quotation.total_amount,
            currency=quotation.currency,
            terms_conditions=data.get("terms_conditions"),
            status="issued",
        )

        # 6. Copy line items from quotation to PO
        for q_item in quotation.items:
            po_item = POItem(
                rfq_item_id=q_item.rfq_item_id,
                item_name=q_item.rfq_item.item_name if q_item.rfq_item else f"Item",
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                tax_rate=q_item.tax_rate,
                line_total=q_item.line_total,
            )
            po.items.append(po_item)

        # 7. Persist
        self.po_repo.create(po)

        # 8. Update RFQ status to closed
        rfq = quotation.rfq
        if rfq:
            rfq.status = "closed"
            self.db.commit()

        # 9. Notify vendor of new PO
        self.notification_svc.notify_po_issued(po)

        # 10. Log activity
        self.notification_svc.log_activity(
            actor_id=created_by,
            entity_type="purchase_order",
            entity_id=po.id,
            action="created",
            metadata={"po_number": po_number, "quotation_id": quotation_id},
        )

        return po

    def get_po(self, po_id: str):
        """Fetch a PO by ID."""
        from app.exceptions import NotFoundError

        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise NotFoundError("Purchase order not found")
        return po

    def list_pos(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """Paginated listing with optional filters (status, vendor_id, etc.)."""
        filters = filters or {}

        if "vendor_id" in filters and filters["vendor_id"]:
            return self.po_repo.get_by_vendor(
                filters["vendor_id"], page, per_page
            )
        if "status" in filters and filters["status"]:
            return self.po_repo.get_by_status(
                filters["status"], page, per_page
            )

        return self.po_repo.get_all_paginated(page, per_page)

    def update_po(self, po_id: str, data: dict):
        """
        Update delivery info or terms on a PO.
        Only allowed while status='issued'.
        """
        from app.exceptions import NotFoundError, BusinessLogicError

        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise NotFoundError("Purchase order not found")
        if po.status != "issued":
            raise BusinessLogicError(
                "Only issued POs can be updated"
            )

        allowed_fields = ["delivery_address", "expected_delivery", "terms_conditions"]
        for field in allowed_fields:
            if field in data and data[field] is not None:
                setattr(po, field, data[field])

        self.db.commit()
        self.db.refresh(po)
        return po

    def acknowledge_po(self, po_id: str, vendor_id: str):
        """
        Vendor acknowledges receipt of the PO.
        Transitions status from 'issued' to 'acknowledged'.
        """
        from app.exceptions import NotFoundError, ForbiddenError, BusinessLogicError

        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise NotFoundError("Purchase order not found")
        if po.vendor_id != vendor_id:
            raise ForbiddenError("This PO does not belong to your vendor profile")
        if po.status != "issued":
            raise BusinessLogicError(
                "Only issued POs can be acknowledged"
            )

        po.status = "acknowledged"
        self.db.commit()
        self.db.refresh(po)

        # Notify the creating officer
        self.notification_svc.create_notification(
            user_id=po.created_by,
            type="po_acknowledged",
            title=f"PO {po.po_number} Acknowledged",
            body=f"Vendor has acknowledged PO {po.po_number}.",
            entity_type="purchase_order",
            entity_id=po.id,
        )

        self.notification_svc.log_activity(
            actor_id=po.vendor.user_id if po.vendor else None,
            entity_type="purchase_order",
            entity_id=po.id,
            action="acknowledged",
        )

        return po

    def fulfill_po(self, po_id: str, vendor_id: str):
        """
        Mark a PO as fulfilled after goods/services delivered.
        Triggers invoice generation eligibility.
        """
        from app.exceptions import NotFoundError, ForbiddenError, BusinessLogicError

        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise NotFoundError("Purchase order not found")
        if po.vendor_id != vendor_id:
            raise ForbiddenError("This PO does not belong to your vendor profile")
        if po.status != "acknowledged":
            raise BusinessLogicError(
                "Only acknowledged POs can be marked as fulfilled"
            )

        po.status = "fulfilled"
        self.db.commit()
        self.db.refresh(po)

        # Notify the creating officer
        self.notification_svc.create_notification(
            user_id=po.created_by,
            type="po_fulfilled",
            title=f"PO {po.po_number} Fulfilled",
            body=f"Vendor has fulfilled PO {po.po_number}. You can now generate an invoice.",
            entity_type="purchase_order",
            entity_id=po.id,
        )

        self.notification_svc.log_activity(
            actor_id=po.vendor.user_id if po.vendor else None,
            entity_type="purchase_order",
            entity_id=po.id,
            action="fulfilled",
        )

        return po

    def cancel_po(self, po_id: str, officer_id: str, reason: str = None):
        """
        Cancel a PO (only from 'issued' or 'acknowledged').
        """
        from app.exceptions import NotFoundError, BusinessLogicError

        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise NotFoundError("Purchase order not found")
        if po.status not in ("issued", "acknowledged"):
            raise BusinessLogicError(
                "Only issued or acknowledged POs can be cancelled"
            )

        po.status = "cancelled"
        self.db.commit()
        self.db.refresh(po)

        # Notify vendor
        if po.vendor and po.vendor.user_id:
            self.notification_svc.create_notification(
                user_id=po.vendor.user_id,
                type="po_cancelled",
                title=f"PO {po.po_number} Cancelled",
                body=f"PO {po.po_number} has been cancelled.{' Reason: ' + reason if reason else ''}",
                entity_type="purchase_order",
                entity_id=po.id,
            )

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="purchase_order",
            entity_id=po.id,
            action="cancelled",
            metadata={"reason": reason} if reason else None,
        )

        return po

    def get_vendor_pos(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """List POs for a specific vendor."""
        return self.po_repo.get_by_vendor(vendor_id, page, per_page)
