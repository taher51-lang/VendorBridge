"""
VendorBridge ERP – Invoice Repository
=======================================
Data-access layer for Invoice, InvoiceItem, and InvoiceEmail models.
"""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.invoice import Invoice, InvoiceItem, InvoiceEmail
from app.repositories.base_repo import BaseRepository


class InvoiceRepository(BaseRepository):
    """Queries for invoices."""

    model = Invoice

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_id(self, entity_id: str):
        """Override to eagerly load items, emails, vendor, and po."""
        return (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.items),
                joinedload(Invoice.emails),
                joinedload(Invoice.vendor),
                joinedload(Invoice.po),
            )
            .filter(
                Invoice.id == entity_id,
                Invoice.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_number(self, invoice_number: str):
        """
        Look up an invoice by its human-readable number.
        """
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.items))
            .filter(
                Invoice.invoice_number == invoice_number,
                Invoice.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_po(self, po_id: str):
        """
        Fetch the invoice linked to a specific purchase order.
        """
        return (
            self.db.query(Invoice)
            .options(joinedload(Invoice.items))
            .filter(
                Invoice.po_id == po_id,
                Invoice.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all invoices for a given vendor, paginated.
        """
        query = (
            self.db.query(Invoice)
            .options(joinedload(Invoice.items))
            .filter(
                Invoice.vendor_id == vendor_id,
                Invoice.deleted_at.is_(None),
            )
            .order_by(Invoice.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List invoices filtered by status (draft, sent, paid, overdue, cancelled).
        """
        query = (
            self.db.query(Invoice)
            .options(joinedload(Invoice.items))
            .filter(
                Invoice.status == status,
                Invoice.deleted_at.is_(None),
            )
            .order_by(Invoice.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_overdue(self, page: int = 1, per_page: int = 20):
        """
        List invoices where due_date < today AND status not in ('paid', 'cancelled').
        """
        today = date.today()
        query = (
            self.db.query(Invoice)
            .filter(
                Invoice.due_date < today,
                Invoice.status.notin_(["paid", "cancelled", "overdue"]),
                Invoice.deleted_at.is_(None),
            )
            .order_by(Invoice.due_date.asc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def mark_paid(self, invoice_id: str):
        """
        Set status='paid' and paid_at=utcnow for the given invoice.
        """
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.status = "paid"
            invoice.paid_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(invoice)
        return invoice

    def get_all_paginated(self, page: int = 1, per_page: int = 20):
        """
        Return all non-deleted invoices, paginated.
        """
        query = (
            self.db.query(Invoice)
            .options(
                joinedload(Invoice.items),
                joinedload(Invoice.vendor),
                joinedload(Invoice.po),
            )
            .filter(Invoice.deleted_at.is_(None))
            .order_by(Invoice.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total


class InvoiceItemRepository(BaseRepository):
    """Queries for invoice line items."""

    model = InvoiceItem

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_invoice(self, invoice_id: str):
        """Return all items for a given invoice."""
        return (
            self.db.query(InvoiceItem)
            .filter(
                InvoiceItem.invoice_id == invoice_id,
                InvoiceItem.deleted_at.is_(None),
            )
            .all()
        )


class InvoiceEmailRepository(BaseRepository):
    """Queries for invoice email dispatch records."""

    model = InvoiceEmail

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_invoice(self, invoice_id: str):
        """Return all email records for a given invoice."""
        return (
            self.db.query(InvoiceEmail)
            .filter(InvoiceEmail.invoice_id == invoice_id)
            .order_by(InvoiceEmail.created_at.desc())
            .all()
        )

    def get_failed(self, page: int = 1, per_page: int = 20):
        """
        List emails with status='failed' for retry processing.
        """
        query = (
            self.db.query(InvoiceEmail)
            .filter(InvoiceEmail.status == "failed")
            .order_by(InvoiceEmail.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total
