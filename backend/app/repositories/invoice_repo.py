"""
VendorBridge ERP – Invoice Repository
=======================================
Data-access layer for Invoice, InvoiceItem, and InvoiceEmail models.
"""

from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceItem, InvoiceEmail
from app.repositories.base_repo import BaseRepository


class InvoiceRepository(BaseRepository):
    """Queries for invoices."""

    model = Invoice

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_number(self, invoice_number: str):
        """
        Look up an invoice by its human-readable number.
        """
        # TODO: Query Invoice where invoice_number == invoice_number
        pass

    def get_by_po(self, po_id: str):
        """
        Fetch the invoice linked to a specific purchase order.
        """
        # TODO: Query Invoice where po_id == po_id
        pass

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all invoices for a given vendor.
        """
        # TODO: Implement paginated query
        pass

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List invoices filtered by status (draft, sent, paid, overdue, cancelled).
        """
        # TODO: Implement paginated query
        pass

    def get_overdue(self, page: int = 1, per_page: int = 20):
        """
        List invoices where due_date < today AND status not in ('paid', 'cancelled').
        Useful for automated overdue flagging.
        """
        # TODO: Implement:
        #   1. Query where due_date < date.today()
        #   2. Filter status NOT IN ('paid', 'cancelled')
        #   3. Paginate
        pass

    def mark_paid(self, invoice_id: str):
        """
        Set status='paid' and paid_at=utcnow for the given invoice.
        """
        # TODO: Implement status transition + timestamp
        pass


class InvoiceItemRepository(BaseRepository):
    """Queries for invoice line items."""

    model = InvoiceItem

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_invoice(self, invoice_id: str):
        """Return all items for a given invoice."""
        # TODO: Query InvoiceItem where invoice_id
        pass


class InvoiceEmailRepository(BaseRepository):
    """Queries for invoice email dispatch records."""

    model = InvoiceEmail

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_invoice(self, invoice_id: str):
        """Return all email records for a given invoice."""
        # TODO: Query InvoiceEmail where invoice_id, order_by created_at DESC
        pass

    def get_failed(self, page: int = 1, per_page: int = 20):
        """
        List emails with status='failed' for retry processing.
        """
        # TODO: Implement paginated query where status == 'failed'
        pass
