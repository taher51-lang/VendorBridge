"""
VendorBridge ERP – Invoice Service
====================================
Business logic for invoice generation, GST, PDF, and email dispatch.
"""

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.repositories.invoice_repo import (
    InvoiceRepository,
    InvoiceItemRepository,
    InvoiceEmailRepository,
)
from app.repositories.po_repo import PurchaseOrderRepository
from app.models.invoice import Invoice, InvoiceItem, InvoiceEmail
from app.services.notification_service import NotificationService
from app.utils.number_generator import generate_invoice_number


class InvoiceService:
    """
    Handles all invoice-related business logic.
    """

    def __init__(self, db: Session):
        self.db = db
        self.invoice_repo = InvoiceRepository(db)
        self.item_repo = InvoiceItemRepository(db)
        self.email_repo = InvoiceEmailRepository(db)
        self.po_repo = PurchaseOrderRepository(db)
        self.notification_svc = NotificationService(db)

    def create_invoice(self, data: dict, generated_by: str):
        """
        Generate an invoice from a fulfilled PO.

        Args:
            data: Validated dict from InvoiceCreateSchema.
                  Must include po_id. Items are auto-copied from PO.
            generated_by: UUID of the user generating the invoice.

        Returns:
            The created Invoice.
        """
        from app.exceptions import NotFoundError, ConflictError, BusinessLogicError

        po_id = data["po_id"]

        # 1. Fetch PO → validate status == 'fulfilled'
        po = self.po_repo.get_by_id(po_id)
        if not po:
            raise NotFoundError("Purchase order not found")
        if po.status != "fulfilled":
            raise BusinessLogicError(
                "Invoice can only be generated from a fulfilled PO"
            )

        # 2. Check no existing invoice for this PO
        existing = self.invoice_repo.get_by_po(po_id)
        if existing:
            raise ConflictError("An invoice already exists for this PO")

        # 3. Generate invoice_number
        invoice_number = generate_invoice_number(self.db)

        # 4. Determine dates
        invoice_date = data.get("invoice_date") or date.today()
        due_date = data.get("due_date")
        is_interstate = data.get("is_interstate", False)

        # 5. Create Invoice model
        invoice = Invoice(
            invoice_number=invoice_number,
            po_id=po_id,
            vendor_id=po.vendor_id,
            generated_by=generated_by,
            invoice_date=invoice_date,
            due_date=due_date,
            subtotal=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            status="draft",
            notes=data.get("notes"),
        )

        # 6. Create InvoiceItem instances from PO items
        subtotal = Decimal("0.00")
        tax_total = Decimal("0.00")

        for po_item in po.items:
            qty = Decimal(str(po_item.quantity))
            price = Decimal(str(po_item.unit_price))
            line_total = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            tax_rate = Decimal(str(po_item.tax_rate or 0))
            item_tax = (line_total * tax_rate / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            inv_item = InvoiceItem(
                item_name=po_item.item_name,
                quantity=po_item.quantity,
                unit_price=po_item.unit_price,
                tax_rate=po_item.tax_rate,
                line_total=line_total,
                hsn_code=po_item.hsn_code,
            )
            invoice.items.append(inv_item)

            subtotal += line_total
            tax_total += item_tax

        # 7. Set financial fields and compute GST
        invoice.subtotal = subtotal.quantize(Decimal("0.01"))
        invoice.calculate_gst(is_interstate, tax_total)

        # 8. Persist
        self.invoice_repo.create(invoice)

        # 9. Log activity
        self.notification_svc.log_activity(
            actor_id=generated_by,
            entity_type="invoice",
            entity_id=invoice.id,
            action="created",
            metadata={
                "invoice_number": invoice_number,
                "po_id": po_id,
            },
        )

        return invoice

    def get_invoice(self, invoice_id: str):
        """Fetch an invoice by ID with items and emails."""
        from app.exceptions import NotFoundError

        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")
        return invoice

    def list_invoices(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """Paginated listing with optional filters."""
        filters = filters or {}

        if "vendor_id" in filters and filters["vendor_id"]:
            return self.invoice_repo.get_by_vendor(
                filters["vendor_id"], page, per_page
            )
        if "status" in filters and filters["status"]:
            return self.invoice_repo.get_by_status(
                filters["status"], page, per_page
            )

        return self.invoice_repo.get_all_paginated(page, per_page)

    def update_invoice(self, invoice_id: str, data: dict):
        """
        Update invoice fields (only while status='draft').
        """
        from app.exceptions import NotFoundError, BusinessLogicError

        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")
        if invoice.status != "draft":
            raise BusinessLogicError("Only draft invoices can be updated")

        if "due_date" in data:
            invoice.due_date = data["due_date"]
        if "notes" in data:
            invoice.notes = data["notes"]

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def generate_pdf(self, invoice_id: str):
        """
        Render the invoice as a PDF and store the file path.

        Returns:
            The URL/path of the generated PDF.
        """
        from app.exceptions import NotFoundError
        from app.utils.pdf_generator import generate_invoice_pdf

        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")

        # Build data dict for the PDF template
        invoice_data = {
            "invoice_number": invoice.invoice_number,
            "invoice_date": str(invoice.invoice_date),
            "due_date": str(invoice.due_date) if invoice.due_date else "N/A",
            "vendor_name": invoice.vendor.company_name if invoice.vendor else "N/A",
            "vendor_gst": invoice.vendor.gst_number if invoice.vendor else "",
            "vendor_address": invoice.vendor.address if invoice.vendor else "",
            "vendor_city": invoice.vendor.city if invoice.vendor else "",
            "vendor_state": invoice.vendor.state if invoice.vendor else "",
            "po_number": invoice.po.po_number if invoice.po else "N/A",
            "subtotal": str(invoice.subtotal),
            "cgst_amount": str(invoice.cgst_amount),
            "sgst_amount": str(invoice.sgst_amount),
            "igst_amount": str(invoice.igst_amount),
            "total_amount": str(invoice.total_amount),
            "notes": invoice.notes or "",
            "items": [],
        }

        for item in invoice.items:
            invoice_data["items"].append(
                {
                    "item_name": item.item_name,
                    "quantity": str(item.quantity),
                    "unit_price": str(item.unit_price),
                    "tax_rate": str(item.tax_rate),
                    "line_total": str(item.line_total),
                    "hsn_code": item.hsn_code or "",
                }
            )

        pdf_path = generate_invoice_pdf(invoice_data)

        # Save path to invoice
        invoice.pdf_url = pdf_path
        self.db.commit()

        return pdf_path

    def send_invoice_email(self, invoice_id: str, data: dict, sent_by: str):
        """
        Email the invoice PDF to a recipient.
        """
        from app.exceptions import NotFoundError, BusinessLogicError
        from app.utils.email_sender import send_invoice_email as email_send

        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")

        # Ensure PDF exists (generate if not)
        if not invoice.pdf_url:
            self.generate_pdf(invoice_id)
            invoice = self.invoice_repo.get_by_id(invoice_id)

        recipient_email = data["recipient_email"]
        subject = data.get("subject") or f"Invoice {invoice.invoice_number} from VendorBridge"

        # Create InvoiceEmail record with status='queued'
        email_record = InvoiceEmail(
            invoice_id=invoice.id,
            sent_by=sent_by,
            recipient_email=recipient_email,
            subject=subject,
            status="queued",
        )
        self.db.add(email_record)
        self.db.commit()
        self.db.refresh(email_record)

        # Try to send
        try:
            success = email_send(
                to=recipient_email,
                subject=subject,
                invoice_data={"invoice_number": invoice.invoice_number},
                pdf_path=invoice.pdf_url,
            )
            if success:
                email_record.status = "sent"
                email_record.sent_at = datetime.now(timezone.utc)
                # Update invoice status to 'sent' if currently draft
                if invoice.status == "draft":
                    invoice.status = "sent"
            else:
                email_record.status = "failed"
                email_record.error_message = "Email sending returned False"
        except Exception as e:
            email_record.status = "failed"
            email_record.error_message = str(e)

        self.db.commit()
        self.db.refresh(email_record)

        # Log
        self.notification_svc.log_activity(
            actor_id=sent_by,
            entity_type="invoice",
            entity_id=invoice.id,
            action="email_sent",
            metadata={
                "recipient": recipient_email,
                "email_status": email_record.status,
            },
        )

        return email_record

    def mark_paid(self, invoice_id: str, officer_id: str):
        """
        Record payment for an invoice.
        """
        from app.exceptions import NotFoundError, BusinessLogicError

        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")
        if invoice.status not in ("sent", "overdue", "draft"):
            raise BusinessLogicError(
                "Only sent, overdue, or draft invoices can be marked as paid"
            )

        self.invoice_repo.mark_paid(invoice_id)

        # Notify vendor of payment confirmation
        if invoice.vendor and invoice.vendor.user_id:
            self.notification_svc.create_notification(
                user_id=invoice.vendor.user_id,
                type="payment_received",
                title=f"Payment Received: {invoice.invoice_number}",
                body=f"Payment for invoice {invoice.invoice_number} has been confirmed.",
                entity_type="invoice",
                entity_id=invoice.id,
            )

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="invoice",
            entity_id=invoice_id,
            action="marked_paid",
        )

        return self.invoice_repo.get_by_id(invoice_id)

    def cancel_invoice(self, invoice_id: str, officer_id: str):
        """
        Cancel an invoice (only from draft or sent status).
        """
        from app.exceptions import NotFoundError, BusinessLogicError

        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError("Invoice not found")
        if invoice.status not in ("draft", "sent"):
            raise BusinessLogicError(
                "Only draft or sent invoices can be cancelled"
            )

        invoice.status = "cancelled"
        self.db.commit()
        self.db.refresh(invoice)

        self.notification_svc.log_activity(
            actor_id=officer_id,
            entity_type="invoice",
            entity_id=invoice_id,
            action="cancelled",
        )

        return invoice

    def get_vendor_invoices(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """List invoices for a vendor."""
        return self.invoice_repo.get_by_vendor(vendor_id, page, per_page)
