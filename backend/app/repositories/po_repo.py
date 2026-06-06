"""
VendorBridge ERP – Purchase Order Repository
==============================================
Data-access layer for PurchaseOrder model.
"""

from sqlalchemy.orm import Session, joinedload

from app.models.purchase_order import PurchaseOrder, POItem
from app.repositories.base_repo import BaseRepository


class PurchaseOrderRepository(BaseRepository):
    """Queries for purchase orders."""

    model = PurchaseOrder

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, entity_id: str):
        """Override to eagerly load items, vendor, and quotation."""
        return (
            self.db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.items),
                joinedload(PurchaseOrder.vendor),
                joinedload(PurchaseOrder.quotation),
            )
            .filter(
                PurchaseOrder.id == entity_id,
                PurchaseOrder.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_number(self, po_number: str):
        """
        Look up a PO by its human-readable number (e.g. PO-2024-0001).
        """
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
            .filter(
                PurchaseOrder.po_number == po_number,
                PurchaseOrder.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all purchase orders for a specific vendor, paginated.
        """
        query = (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
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
        """
        query = (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
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
        List POs created by a specific user (procurement officer).
        """
        query = (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
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
        """
        return (
            self.db.query(PurchaseOrder)
            .options(joinedload(PurchaseOrder.items))
            .filter(
                PurchaseOrder.quotation_id == quotation_id,
                PurchaseOrder.deleted_at.is_(None),
            )
            .first()
        )

    def get_all_paginated(self, page: int = 1, per_page: int = 20):
        """
        Return all non-deleted POs, paginated.
        """
        query = (
            self.db.query(PurchaseOrder)
            .options(
                joinedload(PurchaseOrder.items),
                joinedload(PurchaseOrder.vendor),
            )
            .filter(PurchaseOrder.deleted_at.is_(None))
            .order_by(PurchaseOrder.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total
