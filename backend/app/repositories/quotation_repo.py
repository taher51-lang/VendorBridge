"""
VendorBridge ERP – Quotation Repository
=========================================
Data-access layer for Quotation and QuotationItem models.
"""

from sqlalchemy.orm import Session

from app.models.quotation import Quotation, QuotationItem
from app.repositories.base_repo import BaseRepository


class QuotationRepository(BaseRepository):
    """Queries for vendor quotations."""

    model = Quotation

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_number(self, quote_number: str):
        """
        Look up a quotation by its human-readable number.
        """
        # TODO: Query Quotation where quote_number == quote_number
        pass

    def get_by_rfq(self, rfq_id: str, page: int = 1, per_page: int = 20):
        """
        List all quotations submitted against a given RFQ.
        """
        # TODO: Implement paginated query filtered by rfq_id
        pass

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all quotations submitted by a given vendor.
        """
        # TODO: Implement paginated query filtered by vendor_id
        pass

    def get_latest_revision(self, rfq_id: str, vendor_id: str):
        """
        Return the most recent revision of a quotation for a given
        (rfq_id, vendor_id) pair.
        """
        # TODO: Implement:
        #   1. Query Quotation where rfq_id AND vendor_id
        #   2. Order by revision_no DESC
        #   3. Return .first()
        pass

    def get_for_comparison(self, rfq_id: str):
        """
        Return all submitted quotations for an RFQ, suitable for
        side-by-side comparison.
        """
        # TODO: Implement:
        #   1. Query Quotation where rfq_id AND status == 'submitted'
        #   2. Eagerly load items
        #   3. Order by total_amount ASC
        #   4. Return list
        pass

    def mark_selected(self, quotation_id: str):
        """
        Set a quotation's status to 'selected' and reject all
        other quotations for the same RFQ.
        """
        # TODO: Implement:
        #   1. Fetch quotation by id
        #   2. Set status = 'selected'
        #   3. Fetch all other quotations for the same rfq_id
        #   4. Set their status = 'rejected'
        #   5. Commit
        pass


class QuotationItemRepository(BaseRepository):
    """Queries for quotation line items."""

    model = QuotationItem

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_quotation(self, quotation_id: str):
        """
        Return all items for a given quotation.
        """
        # TODO: Query QuotationItem where quotation_id
        pass
