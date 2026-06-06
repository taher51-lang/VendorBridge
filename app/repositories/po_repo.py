"""
VendorBridge ERP – Purchase Order Repository
==============================================
Data-access layer for PurchaseOrder model.
Extends BaseRepository for standard CRUD operations.
"""

from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrder
from app.repositories.base_repo import BaseRepository


class PurchaseOrderRepository(BaseRepository):
    """Queries for purchase orders."""

    model = PurchaseOrder

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_number(self, po_number: str):
        """
        Look up a PO by its human-readable number (e.g. PO-2025-0001).
        """
        return (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.po_number == po_number,
                PurchaseOrder.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all purchase orders for a specific vendor, newest first.
        Returns: (results, total)
        """
        query = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.vendor_id == vendor_id,
                PurchaseOrder.deleted_at.is_(None),
            )
            .order_by(PurchaseOrder.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List POs filtered by status (issued, acknowledged, fulfilled, cancelled).
        Returns: (results, total)
        """
        query = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.status == status,
                PurchaseOrder.deleted_at.is_(None),
            )
            .order_by(PurchaseOrder.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_creator(self, user_id: str, page: int = 1, per_page: int = 20):
        """
        List POs created by a specific procurement officer.
        Returns: (results, total)
        """
        query = (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.created_by == user_id,
                PurchaseOrder.deleted_at.is_(None),
            )
            .order_by(PurchaseOrder.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_quotation(self, quotation_id: str):
        """
        Fetch the PO linked to a specific approved quotation.
        Returns None if no PO has been issued for that quotation yet.
        """
        return (
            self.db.query(PurchaseOrder)
            .filter(
                PurchaseOrder.quotation_id == quotation_id,
                PurchaseOrder.deleted_at.is_(None),
            )
            .first()
        )
