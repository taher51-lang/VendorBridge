"""
VendorBridge ERP – Invoice Repository
=======================================
Data-access layer for Invoice, InvoiceItem, and InvoiceEmail models.
"""

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceItem, InvoiceEmail
from app.repositories.base_repo import BaseRepository


class InvoiceRepository(BaseRepository):
    """Queries for invoices."""

    model = Invoice

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_number(self, invoice_number: str):
        """
        Look up an invoice by its human-readable number (e.g. INV-2025-0001).
        """
        return (
            self.db.query(Invoice)
            .filter(
                Invoice.invoice_number == invoice_number,
                Invoice.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_po(self, po_id: str):
        """
        Fetch the invoice linked to a specific purchase order.
        Returns None if no invoice has been generated for that PO yet.
        """
        return (
            self.db.query(Invoice)
            .filter(
                Invoice.po_id == po_id,
                Invoice.deleted_at.is_(None),
            )
            .first()
        )

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all invoices for a given vendor, newest first.
        Returns: (results, total)
        """
        query = (
            self.db.query(Invoice)
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
        Returns: (results, total)
        """
        query = (
            self.db.query(Invoice)
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
        Used by the batch flag_overdue job.
        Returns: (results, total)
        """
        today = date.today()
        query = (
            self.db.query(Invoice)
            .filter(
                Invoice.due_date < today,
                Invoice.status.notin_(["paid", "cancelled"]),
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
        Commits the change and returns the refreshed invoice.
        """
        invoice = self.get_by_id(invoice_id)
        if invoice:
            invoice.status = "paid"
            invoice.paid_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(invoice)
        return invoice


class InvoiceItemRepository(BaseRepository):
    """Queries for invoice line items."""

    model = InvoiceItem

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_invoice(self, invoice_id: str):
        """Return all line items for a given invoice."""
        return (
            self.db.query(InvoiceItem)
            .filter(InvoiceItem.invoice_id == invoice_id)
            .all()
        )


class InvoiceEmailRepository(BaseRepository):
    """Queries for invoice email dispatch records."""

    model = InvoiceEmail

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_invoice(self, invoice_id: str):
        """
        Return all email records for a given invoice, most recent first.
        """
        return (
            self.db.query(InvoiceEmail)
            .filter(
                InvoiceEmail.invoice_id == invoice_id,
                InvoiceEmail.deleted_at.is_(None),
            )
            .order_by(InvoiceEmail.created_at.desc())
            .all()
        )

    def get_failed(self, page: int = 1, per_page: int = 20):
        """
        List emails with status='failed' for retry processing.
        Returns: (results, total)
        """
        query = (
            self.db.query(InvoiceEmail)
            .filter(
                InvoiceEmail.status == "failed",
                InvoiceEmail.deleted_at.is_(None),
            )
            .order_by(InvoiceEmail.created_at.desc())
        )
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total
