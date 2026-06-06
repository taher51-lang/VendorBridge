"""
VendorBridge ERP – RFQ Repository
===================================
Data-access layer for RFQ, RFQItem, and RFQVendorAssignment models.
"""

from sqlalchemy.orm import Session

from app.models.rfq import RFQ, RFQItem, RFQVendorAssignment
from app.repositories.base_repo import BaseRepository


class RFQRepository(BaseRepository):
    """Queries for Requests for Quotation."""

    model = RFQ

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_number(self, rfq_number: str):
        """
        Look up an RFQ by its human-readable number (e.g. RFQ-2024-0001).
        """
        # TODO: Query RFQ where rfq_number == rfq_number
        pass

    def get_by_creator(self, user_id: str, page: int = 1, per_page: int = 20):
        """
        List RFQs created by a specific procurement officer.
        """
        # TODO: Implement paginated query filtered by created_by
        pass

    def get_by_status(self, status: str, page: int = 1, per_page: int = 20):
        """
        List RFQs filtered by status (draft, open, closed, cancelled).
        """
        # TODO: Implement paginated + status filter
        pass

    def get_open_for_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List open RFQs where the vendor has been invited.
        Joins through RFQVendorAssignment.
        """
        # TODO: Implement:
        #   1. Join RFQ with RFQVendorAssignment
        #   2. Filter assignment.vendor_id == vendor_id
        #   3. Filter RFQ.status == 'open'
        #   4. Paginate
        pass

    def assign_vendors(self, rfq_id: str, vendor_ids: list[str]):
        """
        Bulk-create RFQVendorAssignment rows for a list of vendor IDs.

        Args:
            rfq_id: The RFQ to assign vendors to.
            vendor_ids: List of vendor UUID strings.
        """
        # TODO: Implement:
        #   1. For each vendor_id, create an RFQVendorAssignment
        #   2. Bulk add_all + commit
        #   3. Return list of created assignments
        pass

    def mark_vendor_viewed(self, rfq_id: str, vendor_id: str):
        """
        Set viewed_at timestamp on the vendor's assignment.
        Called when a vendor first opens the RFQ detail page.
        """
        # TODO: Implement:
        #   1. Query RFQVendorAssignment for (rfq_id, vendor_id)
        #   2. Set viewed_at = utcnow, status = 'acknowledged'
        #   3. Commit
        pass


class RFQItemRepository(BaseRepository):
    """Queries for RFQ line items."""

    model = RFQItem

    def __init__(self, db: Session):
        # TODO: Call super().__init__(db)
        pass

    def get_by_rfq(self, rfq_id: str):
        """
        Return all items for a given RFQ, ordered by sort_order.
        """
        # TODO: Query RFQItem where rfq_id, order_by sort_order
        pass
