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
        self.quotation_repo = QuotationRepository(db)
        self.item_repo = QuotationItemRepository(db)
        self.rfq_repo = RFQRepository(db)

    def create_quotation(self, data: dict, vendor_id: str):
        """
        Create a new quotation (or a new revision) for an RFQ.
        """
        from datetime import datetime, timezone
        from app.exceptions import NotFoundError, BusinessLogicError
        from app.models.rfq import RFQVendorAssignment
        from app.utils.number_generator import generate_quote_number
        from app.services.notification_service import NotificationService

        # 1. Verify the RFQ exists and status == 'open'
        rfq = self.rfq_repo.get_by_id(data['rfq_id'])
        if not rfq:
            raise NotFoundError("RFQ not found")
        if rfq.status != 'open':
            raise BusinessLogicError("RFQ is not open for bidding")

        # 2. Verify the vendor is assigned to this RFQ
        assignment = self.db.query(RFQVendorAssignment).filter_by(
            rfq_id=rfq.id, vendor_id=vendor_id
        ).first()
        if not assignment:
            raise BusinessLogicError("Vendor is not assigned to this RFQ")

        # 3. Check for existing quotation → increment revision_no if found
        latest_quotation = self.quotation_repo.get_latest_revision(rfq.id, vendor_id)
        revision_no = 1
        if latest_quotation:
            revision_no = latest_quotation.revision_no + 1

        # 4. Generate quote_number using number_generator.generate_quote_number()
        quote_number = generate_quote_number(self.db)

        # 5. Create Quotation model
        quotation = Quotation(
            quote_number=quote_number,
            rfq_id=rfq.id,
            vendor_id=vendor_id,
            revision_no=revision_no,
            delivery_days=data['delivery_days'],
            validity_days=data.get('validity_days'),
            notes=data.get('notes'),
            is_interstate=data.get('is_interstate', False),
            currency=data.get('currency', 'INR'),
            status='draft'
        )

        # 6. Create QuotationItem instances from data['items']
        for item_data in data['items']:
            item = QuotationItem(
                rfq_item_id=item_data.get('rfq_item_id'),
                unit_price=item_data['unit_price'],
                quantity=item_data['quantity'],
                tax_rate=item_data.get('tax_rate', 0),
                notes=item_data.get('notes')
            )
            item.calculate_line_total()
            quotation.items.append(item)

        # 7. Call quotation.calculate_totals()
        quotation.calculate_totals(is_interstate=quotation.is_interstate)

        # 8. Persist via quotation_repo.create()
        self.quotation_repo.create(quotation)

        # 9. Log activity
        notifier = NotificationService(self.db)
        # Find vendor's user ID to associate actor
        vendor_profile = latest_quotation.vendor if latest_quotation else quotation.vendor
        actor_id = vendor_profile.user_id if vendor_profile else None
        notifier.log_activity(
            actor_id=actor_id,
            entity_type='quotation',
            entity_id=quotation.id,
            action='created',
            metadata={'quote_number': quote_number, 'revision_no': revision_no}
        )

        # 10. Return quotation
        return quotation

    def get_quotation(self, quotation_id: str):
        """Fetch a single quotation with items."""
        from app.exceptions import NotFoundError
        quotation = self.quotation_repo.get_by_id(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        return quotation

    def update_quotation(self, quotation_id: str, data: dict, vendor_id: str):
        """
        Update a draft quotation.

        Only allowed when status='draft' and by the owning vendor.
        """
        from app.exceptions import NotFoundError, ForbiddenError, BusinessLogicError
        from app.services.notification_service import NotificationService

        quotation = self.quotation_repo.get_by_id(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.vendor_id != vendor_id:
            raise ForbiddenError("You do not own this quotation")
        if quotation.status != 'draft':
            raise BusinessLogicError("Only draft quotations can be updated")

        # 2. Apply data fields
        if 'delivery_days' in data:
            quotation.delivery_days = data['delivery_days']
        if 'validity_days' in data:
            quotation.validity_days = data['validity_days']
        if 'notes' in data:
            quotation.notes = data['notes']
        if 'is_interstate' in data:
            quotation.is_interstate = data['is_interstate']
        if 'currency' in data:
            quotation.currency = data['currency']

        # 3. If 'items' updated, recalculate line totals and totals
        if 'items' in data:
            # Clear old items
            quotation.items = []
            for item_data in data['items']:
                item = QuotationItem(
                    rfq_item_id=item_data.get('rfq_item_id'),
                    unit_price=item_data['unit_price'],
                    quantity=item_data['quantity'],
                    tax_rate=item_data.get('tax_rate', 0),
                    notes=item_data.get('notes')
                )
                item.calculate_line_total()
                quotation.items.append(item)

        quotation.calculate_totals(is_interstate=quotation.is_interstate)

        # 4. Persist and return
        self.quotation_repo.update(quotation)
        
        # Log activity
        notifier = NotificationService(self.db)
        notifier.log_activity(
            actor_id=quotation.vendor.user_id,
            entity_type='quotation',
            entity_id=quotation.id,
            action='updated'
        )
        return quotation

    def submit_quotation(self, quotation_id: str, vendor_id: str):
        """
        Transition a quotation from 'draft' to 'submitted'.
        """
        from datetime import datetime, timezone
        from app.exceptions import NotFoundError, ForbiddenError, BusinessLogicError
        from app.services.notification_service import NotificationService

        quotation = self.quotation_repo.get_by_id(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.vendor_id != vendor_id:
            raise ForbiddenError("You do not own this quotation")
        if quotation.status != 'draft':
            raise BusinessLogicError("Only draft quotations can be submitted")

        # 2. Set status='submitted', submitted_at=utcnow
        quotation.status = 'submitted'
        quotation.submitted_at = datetime.now(timezone.utc)

        # 3. Persist
        self.quotation_repo.update(quotation)

        # 4. Notify procurement officer
        notifier = NotificationService(self.db)
        rfq_creator_id = quotation.rfq.created_by
        notifier.create_notification(
            user_id=rfq_creator_id,
            type='quotation_submitted',
            title=f"Quotation Submitted: {quotation.quote_number}",
            body=f"Vendor {quotation.vendor.company_name} has submitted quotation {quotation.quote_number} for RFQ {quotation.rfq.rfq_number}.",
            entity_type='quotation',
            entity_id=quotation.id
        )

        # 5. Log activity
        notifier.log_activity(
            actor_id=quotation.vendor.user_id,
            entity_type='quotation',
            entity_id=quotation.id,
            action='submitted'
        )
        return quotation

    def compare_quotations(self, rfq_id: str):
        """
        Return all submitted quotations for an RFQ in a comparison view.
        """
        from app.exceptions import NotFoundError
        rfq = self.rfq_repo.get_by_id(rfq_id)
        if not rfq:
            raise NotFoundError("RFQ not found")

        quotations = self.quotation_repo.get_for_comparison(rfq_id)
        recommended_id = quotations[0].id if quotations else None

        return {
            "rfq_id": rfq.id,
            "rfq_title": rfq.title,
            "rfq_number": rfq.rfq_number,
            "quotations": quotations,
            "recommended_quotation_id": recommended_id
        }

    def select_quotation(self, quotation_id: str, officer_id: str):
        """
        Select a quotation as the winner and reject all others for the RFQ.
        Triggers the approval workflow.
        """
        from app.exceptions import NotFoundError, BusinessLogicError
        from app.services.notification_service import NotificationService

        quotation = self.quotation_repo.get_by_id(quotation_id)
        if not quotation:
            raise NotFoundError("Quotation not found")
        if quotation.status != 'submitted':
            raise BusinessLogicError("Only submitted quotations can be selected")

        # 2. Call quotation_repo.mark_selected(quotation_id)
        self.quotation_repo.mark_selected(quotation_id)

        # Update RFQ status to 'awarded'
        rfq = quotation.rfq
        rfq.status = 'awarded'
        self.rfq_repo.update(rfq)

        # 3. Notify the winning vendor
        notifier = NotificationService(self.db)
        notifier.create_notification(
            user_id=quotation.vendor.user_id,
            type='quotation_selected',
            title=f"Quotation Selected: {quotation.quote_number}",
            body=f"Your quotation {quotation.quote_number} for RFQ {rfq.rfq_number} has been selected.",
            entity_type='quotation',
            entity_id=quotation.id
        )

        # 4. Notify rejected vendors
        for q in rfq.quotations:
            if q.id != quotation_id and q.status == 'rejected':
                notifier.create_notification(
                    user_id=q.vendor.user_id,
                    type='quotation_rejected',
                    title=f"Quotation Rejected: {q.quote_number}",
                    body=f"Your quotation {q.quote_number} for RFQ {rfq.rfq_number} was not selected.",
                    entity_type='quotation',
                    entity_id=q.id
                )

        # 5. Log activity
        notifier.log_activity(
            actor_id=officer_id,
            entity_type='quotation',
            entity_id=quotation.id,
            action='selected'
        )

        # 6. Return the selected quotation
        return quotation

    def list_vendor_quotations(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """List all quotations by a vendor."""
        results, total = self.quotation_repo.get_by_vendor(vendor_id, page, per_page)
        return results, total

    def list_rfq_quotations(self, rfq_id: str, page: int = 1, per_page: int = 20):
        """List all quotations for an RFQ."""
        results, total = self.quotation_repo.get_by_rfq(rfq_id, page, per_page)
        return results, total
