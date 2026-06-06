"""
VendorBridge ERP – Quotation Service
======================================
Business logic for quotation submission, comparison, and selection.
"""

from sqlalchemy.orm import Session

from app.repositories.quotation_repo import QuotationRepository, QuotationItemRepository
from app.repositories.rfq_repo import RFQRepository
from app.models.quotation import Quotation, QuotationItem


class QuotationService:
    """
    Handles all business logic related to vendor quotations.
    """

    def __init__(self, db: Session):
        """
        Initialize repositories and helpers.

        Dependencies:
            - QuotationRepository(db)
            - QuotationItemRepository(db)
            - RFQRepository(db)
            - NotificationService(db)
            - number_generator
        """
        # TODO: Instantiate dependencies
        pass

    def create_quotation(self, data: dict, vendor_id: str):
        """
        Create a new quotation (or a new revision) for an RFQ.

        Args:
            data: Validated dict from QuotationCreateSchema.
            vendor_id: UUID of the submitting vendor.

        Returns:
            The created Quotation object.
        """
        # 1. Verify the RFQ exists and status == 'open'
        # 2. Verify the vendor is assigned to this RFQ
        # 3. Check for existing quotation → increment revision_no if found
        # 4. Generate quote_number using number_generator.generate_quote_number()
        # 5. Create Quotation model
        # 6. Create QuotationItem instances from data['items']
        #    → call item.calculate_line_total() on each
        # 7. Call quotation.calculate_totals()
        # 8. Persist via quotation_repo.create()
        # 9. Log activity
        # 10. Return quotation
        pass

    def get_quotation(self, quotation_id: str):
        """Fetch a single quotation with items."""
        # 1. Call quotation_repo.get_by_id()
        # 2. Raise NotFoundError if None
        pass

    def update_quotation(self, quotation_id: str, data: dict, vendor_id: str):
        """
        Update a draft quotation.

        Only allowed when status='draft' and by the owning vendor.
        """
        # 1. Fetch quotation → validate status=='draft' AND vendor_id matches
        # 2. Apply data fields
        # 3. If 'items' updated, recalculate line totals and totals
        # 4. Persist and return
        pass

    def submit_quotation(self, quotation_id: str, vendor_id: str):
        """
        Transition a quotation from 'draft' to 'submitted'.
        """
        # 1. Fetch quotation → validate status=='draft' AND vendor ownership
        # 2. Set status='submitted', submitted_at=utcnow
        # 3. Persist
        # 4. Notify procurement officer
        # 5. Log activity
        pass

    def compare_quotations(self, rfq_id: str):
        """
        Return all submitted quotations for an RFQ in a comparison view.

        Returns:
            Dict with rfq info + list of quotations sorted by total_amount.
        """
        # 1. Call quotation_repo.get_for_comparison(rfq_id)
        # 2. Build comparison response with rfq_title, quotations list,
        #    and optional recommended_quotation_id (lowest total)
        pass

    def select_quotation(self, quotation_id: str, officer_id: str):
        """
        Select a quotation as the winner and reject all others for the RFQ.
        Triggers the approval workflow.
        """
        # 1. Fetch quotation → validate status=='submitted'
        # 2. Call quotation_repo.mark_selected(quotation_id)
        # 3. Notify the winning vendor
        # 4. Notify rejected vendors
        # 5. Log activity
        # 6. Return the selected quotation
        pass

    def list_vendor_quotations(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """List all quotations by a vendor."""
        # 1. Call quotation_repo.get_by_vendor(vendor_id, page, per_page)
        pass

    def list_rfq_quotations(self, rfq_id: str, page: int = 1, per_page: int = 20):
        """List all quotations for an RFQ."""
        # 1. Call quotation_repo.get_by_rfq(rfq_id, page, per_page)
        pass
