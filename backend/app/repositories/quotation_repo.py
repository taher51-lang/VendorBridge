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
        super().__init__(db)

    def get_by_number(self, quote_number: str):
        """
        Look up a quotation by its human-readable number.
        """
        if not quote_number:
            return None
        return self.db.query(Quotation).filter(
            Quotation.quote_number == quote_number,
            Quotation.deleted_at == None
        ).first()

    def get_by_rfq(self, rfq_id: str, page: int = 1, per_page: int = 20):
        """
        List all quotations submitted against a given RFQ.
        """
        query = self.db.query(Quotation).filter(
            Quotation.rfq_id == rfq_id,
            Quotation.deleted_at == None
        )
        total_count = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total_count

    def get_by_vendor(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List all quotations submitted by a given vendor.
        """
        query = self.db.query(Quotation).filter(
            Quotation.vendor_id == vendor_id,
            Quotation.deleted_at == None
        )
        total_count = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total_count

    def get_latest_revision(self, rfq_id: str, vendor_id: str):
        """
        Return the most recent revision of a quotation for a given
        (rfq_id, vendor_id) pair.
        """
        return self.db.query(Quotation).filter(
            Quotation.rfq_id == rfq_id,
            Quotation.vendor_id == vendor_id,
            Quotation.deleted_at == None
        ).order_by(Quotation.revision_no.desc()).first()

    def get_for_comparison(self, rfq_id: str):
        """
        Return all submitted quotations for an RFQ, suitable for
        side-by-side comparison.
        """
        from sqlalchemy.orm import joinedload
        return self.db.query(Quotation).options(
            joinedload(Quotation.items)
        ).filter(
            Quotation.rfq_id == rfq_id,
            Quotation.status == "submitted",
            Quotation.deleted_at == None
        ).order_by(Quotation.total_amount.asc()).all()

    def mark_selected(self, quotation_id: str):
        """
        Set a quotation's status to 'selected' and reject all
        other quotations for the same RFQ.
        """
        winner = self.get_by_id(quotation_id)
        if not winner:
            return None

        # Mark winner as selected
        winner.status = "selected"

        # Reject all other quotations for the same RFQ
        others = self.db.query(Quotation).filter(
            Quotation.rfq_id == winner.rfq_id,
            Quotation.id != quotation_id,
            Quotation.deleted_at == None
        ).all()
        for q in others:
            q.status = "rejected"

        self.db.commit()
        self.db.refresh(winner)
        return winner


class QuotationItemRepository(BaseRepository):
    """Queries for quotation line items."""

    model = QuotationItem

    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_quotation(self, quotation_id: str):
        """
        Return all items for a given quotation.
        """
        return self.db.query(QuotationItem).filter(
            QuotationItem.quotation_id == quotation_id,
            QuotationItem.deleted_at == None
        ).all()
