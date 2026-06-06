"""
VendorBridge ERP – Purchase Order Service
==========================================
Business logic for PO issuance, status transitions, and activity logging.
"""

from sqlalchemy.orm import Session

from app.repositories.po_repo import PurchaseOrderRepository
from app.repositories.quotation_repo import QuotationRepository
from app.models.purchase_order import PurchaseOrder, POItem
from app.models.audit import ActivityLog
from app.utils.number_generator import generate_po_number

# ── Status Constants ───────────────────────────────────────────────────────────
# Confirmed with Dev 2: quotation status after approval workflow completes.
# Change only this constant if Dev 2 uses a different value.
QUOTATION_APPROVED_STATUS = "selected"

# PO can be created when quotation is in this status (Option A — hackathon flow)
PO_CREATEABLE_FROM = {QUOTATION_APPROVED_STATUS}

# PO statuses that allow cancellation
PO_CANCELLABLE_STATUSES = {"issued", "acknowledged"}


class PurchaseOrderService:
    """
    Handles all PO-related business logic.
    Orchestrates PurchaseOrderRepository, QuotationRepository, and number_generator.
    """

    def __init__(self, db: Session):
        self.db = db
        self.po_repo = PurchaseOrderRepository(db)
        self.quotation_repo = QuotationRepository(db)

    # ── Create ────────────────────────────────────────────────────────────────

    def create_po(self, quotation_id: str, data: dict, created_by: str) -> PurchaseOrder:
        """
        Issue a Purchase Order from an approved quotation.

        Args:
            quotation_id: UUID of the approved quotation.
            data:         Validated dict from POCreateSchema.
            created_by:   UUID of the issuing procurement officer.

        Returns:
            The newly created PurchaseOrder.

        Raises:
            ValueError: If quotation not found, wrong status, or PO already exists.
        """
        # 1. Fetch quotation
        quotation = self.quotation_repo.get_by_id(quotation_id)
        if not quotation:
            raise ValueError(f"Quotation not found: {quotation_id}")

        # 2. Validate quotation status
        if quotation.status not in PO_CREATEABLE_FROM:
            raise ValueError(
                f"Quotation must be in '{QUOTATION_APPROVED_STATUS}' status to create a PO. "
                f"Current status: '{quotation.status}'"
            )

        # 3. Check no duplicate PO for this quotation
        existing = self.po_repo.get_by_quotation(quotation_id)
        if existing:
            raise ValueError(
                f"A Purchase Order already exists for this quotation: {existing.po_number}"
            )

        # 4. Generate unique PO number
        po_number = generate_po_number(self.db)

        # 5. Resolve workflow_id from the quotation's approval workflow (if any)
        workflow_id = None
        if quotation.workflow:
            workflow_id = quotation.workflow.id

        # 6. Create PurchaseOrder – copy financials from quotation
        po = PurchaseOrder(
            po_number=po_number,
            quotation_id=quotation_id,
            vendor_id=quotation.vendor_id,
            created_by=created_by,
            workflow_id=workflow_id,
            delivery_address=data.get("delivery_address"),
            expected_delivery=data.get("expected_delivery"),
            subtotal=quotation.subtotal,
            tax_amount=quotation.tax_amount,
            total_amount=quotation.total_amount,
            currency=quotation.currency,
            terms_conditions=data.get("terms_conditions"),
            status="issued",
        )
        self.db.add(po)
        self.db.flush()  # flush to get po.id before inserting child POItems

        # 7. Copy quotation items → POItem (denormalized snapshot)
        for q_item in quotation.items:
            item_name = "Item"
            if q_item.rfq_item:
                item_name = q_item.rfq_item.item_name

            po_item = POItem(
                po_id=po.id,
                rfq_item_id=q_item.rfq_item_id,
                item_name=item_name,
                quantity=q_item.quantity,
                unit_price=q_item.unit_price,
                tax_rate=q_item.tax_rate,
                line_total=q_item.line_total,
            )
            self.db.add(po_item)

        self.db.commit()
        self.db.refresh(po)

        # 8. Audit log
        self._log("purchase_order", po.id, "PO_CREATED", created_by, {"po_number": po_number})

        return po

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_po(self, po_id: str) -> PurchaseOrder:
        """Fetch a PO by ID. Raises ValueError if not found."""
        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise ValueError(f"Purchase Order not found: {po_id}")
        return po

    def list_pos(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """
        Paginated PO listing with optional filters.
        Supported filter keys: vendor_id, status, created_by.
        Returns: (results, total)
        """
        filters = filters or {}

        if "vendor_id" in filters:
            return self.po_repo.get_by_vendor(filters["vendor_id"], page, per_page)
        if "status" in filters:
            return self.po_repo.get_by_status(filters["status"], page, per_page)
        if "created_by" in filters:
            return self.po_repo.get_by_creator(filters["created_by"], page, per_page)

        return self.po_repo.get_all(page=page, per_page=per_page)

    def get_vendor_pos(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """List POs for a specific vendor. Returns: (results, total)."""
        return self.po_repo.get_by_vendor(vendor_id, page, per_page)

    # ── Update ────────────────────────────────────────────────────────────────

    def update_po(self, po_id: str, data: dict) -> PurchaseOrder:
        """
        Update delivery info or terms on a PO.
        Only allowed while status='issued'.
        """
        po = self.get_po(po_id)
        if po.status != "issued":
            raise ValueError(
                f"PO can only be updated when status is 'issued'. Current: '{po.status}'"
            )

        for field in ("delivery_address", "expected_delivery", "terms_conditions"):
            value = data.get(field)
            if value is not None:
                setattr(po, field, value)

        return self.po_repo.update(po)

    # ── Status Transitions ────────────────────────────────────────────────────

    def acknowledge_po(self, po_id: str, vendor_user_id: str) -> PurchaseOrder:
        """
        Vendor acknowledges receipt of the PO.
        Transitions status from 'issued' → 'acknowledged'.

        Args:
            po_id:          UUID of the PO.
            vendor_user_id: JWT user ID of the vendor acknowledging the PO.
        """
        po = self.get_po(po_id)

        if po.status != "issued":
            raise ValueError(
                f"PO must be in 'issued' status to acknowledge. Current: '{po.status}'"
            )

        # Verify the current user's vendor record matches this PO
        from app.models.vendor import Vendor
        vendor = (
            self.db.query(Vendor)
            .filter(
                Vendor.user_id == vendor_user_id,
                Vendor.deleted_at.is_(None),
            )
            .first()
        )
        if not vendor or vendor.id != po.vendor_id:
            raise PermissionError("You are not authorized to acknowledge this Purchase Order.")

        po.status = "acknowledged"
        result = self.po_repo.update(po)
        self._log("purchase_order", po_id, "PO_ACKNOWLEDGED", vendor_user_id, {})
        return result

    def fulfill_po(self, po_id: str, officer_id: str) -> PurchaseOrder:
        """
        Mark a PO as fulfilled after goods/services are delivered.
        Transitions status from 'acknowledged' → 'fulfilled'.
        Note: fulfillment is NOT required before invoice creation (Option A).
        """
        po = self.get_po(po_id)

        if po.status != "acknowledged":
            raise ValueError(
                f"PO must be in 'acknowledged' status to fulfill. Current: '{po.status}'"
            )

        po.status = "fulfilled"
        result = self.po_repo.update(po)
        self._log("purchase_order", po_id, "PO_FULFILLED", officer_id, {})
        return result

    def cancel_po(self, po_id: str, officer_id: str, reason: str = None) -> PurchaseOrder:
        """
        Cancel a PO. Only allowed from 'issued' or 'acknowledged' status.
        """
        po = self.get_po(po_id)

        if po.status not in PO_CANCELLABLE_STATUSES:
            raise ValueError(
                f"PO can only be cancelled when status is 'issued' or 'acknowledged'. "
                f"Current: '{po.status}'"
            )

        po.status = "cancelled"
        result = self.po_repo.update(po)
        self._log("purchase_order", po_id, "PO_CANCELLED", officer_id, {"reason": reason})
        return result

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_id: str,
        metadata: dict,
    ) -> None:
        """
        Append an immutable audit log entry.
        Failures are silently swallowed so logging never breaks the main operation.
        """
        try:
            log = ActivityLog(
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                metadata_=metadata,
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            pass
