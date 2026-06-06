"""
VendorBridge ERP – Invoice Service
====================================
Business logic for invoice generation, GST calculation,
PDF rendering, and email dispatch.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.repositories.invoice_repo import (
    InvoiceRepository,
    InvoiceItemRepository,
    InvoiceEmailRepository,
)
from app.repositories.po_repo import PurchaseOrderRepository
from app.models.invoice import Invoice, InvoiceItem, InvoiceEmail
from app.models.audit import ActivityLog
from app.utils.number_generator import generate_invoice_number

# ── Status Constants ───────────────────────────────────────────────────────────
# Option A (hackathon): invoice can be created once PO is issued or acknowledged.
# Fulfilled status is NOT required (simpler demo flow).
INVOICE_CREATEABLE_PO_STATUSES = {"issued", "acknowledged"}

# Invoice must be in one of these statuses to be marked as paid
INVOICE_PAYABLE_STATUSES = {"sent", "overdue"}


class InvoiceService:
    """
    Handles all invoice-related business logic.
    Orchestrates repositories, PDF generation, and email sending.
    """

    def __init__(self, db: Session):
        self.db = db
        self.invoice_repo      = InvoiceRepository(db)
        self.invoice_item_repo = InvoiceItemRepository(db)
        self.invoice_email_repo = InvoiceEmailRepository(db)
        self.po_repo           = PurchaseOrderRepository(db)

    # ── Create ────────────────────────────────────────────────────────────────

    def create_invoice(self, data: dict, generated_by: str) -> Invoice:
        """
        Generate an invoice from an issued/acknowledged PO.

        Args:
            data:         Validated dict from InvoiceCreateSchema.
                          Must include: po_id, invoice_date, is_interstate, items.
            generated_by: UUID of the procurement officer creating the invoice.

        Returns:
            The newly created Invoice.

        Raises:
            ValueError: If PO not found, wrong status, or invoice already exists.
        """
        # 1. Fetch and validate PO
        po = self.po_repo.get_by_id(data["po_id"])
        if not po:
            raise ValueError(f"Purchase Order not found: {data['po_id']}")

        if po.status not in INVOICE_CREATEABLE_PO_STATUSES:
            raise ValueError(
                f"Purchase Order must be 'issued' or 'acknowledged' to create an invoice. "
                f"Current status: '{po.status}'"
            )

        # 2. Check no duplicate invoice for this PO
        existing = self.invoice_repo.get_by_po(data["po_id"])
        if existing:
            raise ValueError(
                f"An invoice already exists for this PO: {existing.invoice_number}"
            )

        # 3. Generate unique invoice number
        invoice_number = generate_invoice_number(self.db)

        # 4. Create Invoice stub (financials computed below)
        invoice = Invoice(
            invoice_number=invoice_number,
            po_id=data["po_id"],
            vendor_id=po.vendor_id,
            generated_by=generated_by,
            invoice_date=data["invoice_date"],
            due_date=data.get("due_date"),
            subtotal=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            status="draft",
            notes=data.get("notes"),
        )
        self.db.add(invoice)
        self.db.flush()  # need invoice.id for child InvoiceItems

        # 5. Create InvoiceItems and accumulate totals
        subtotal  = Decimal("0.00")
        tax_total = Decimal("0.00")

        for item_data in data["items"]:
            qty       = Decimal(str(item_data["quantity"]))
            price     = Decimal(str(item_data["unit_price"]))
            tax_rate  = Decimal(str(item_data["tax_rate"]))
            line_total = (qty * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            tax_amount = (line_total * tax_rate / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            subtotal  += line_total
            tax_total += tax_amount

            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                quotation_item_id=item_data.get("quotation_item_id"),
                item_name=item_data["item_name"],
                quantity=qty,
                unit_price=price,
                tax_rate=tax_rate,
                line_total=line_total,
                hsn_code=item_data.get("hsn_code"),
            )
            self.db.add(inv_item)

        # 6. Set subtotal and distribute GST (CGST/SGST or IGST)
        invoice.subtotal = subtotal.quantize(Decimal("0.01"))
        invoice.calculate_gst(data.get("is_interstate", False), tax_total)

        self.db.commit()
        self.db.refresh(invoice)

        # 7. Audit log
        self._log("invoice", invoice.id, "INVOICE_CREATED", generated_by, {
            "invoice_number": invoice_number,
            "po_id": data["po_id"],
        })

        return invoice

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_invoice(self, invoice_id: str) -> Invoice:
        """Fetch an invoice by ID. Raises ValueError if not found."""
        invoice = self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice not found: {invoice_id}")
        return invoice

    def list_invoices(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """
        Paginated invoice listing with optional filters.
        Supported filter keys: vendor_id, status.
        Returns: (results, total)
        """
        filters = filters or {}

        if "vendor_id" in filters:
            return self.invoice_repo.get_by_vendor(filters["vendor_id"], page, per_page)
        if "status" in filters:
            return self.invoice_repo.get_by_status(filters["status"], page, per_page)

        return self.invoice_repo.get_all(page=page, per_page=per_page)

    def get_vendor_invoices(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """List invoices for a specific vendor. Returns: (results, total)."""
        return self.invoice_repo.get_by_vendor(vendor_id, page, per_page)

    # ── Update ────────────────────────────────────────────────────────────────

    def update_invoice(self, invoice_id: str, data: dict) -> Invoice:
        """
        Update an invoice's due_date or notes.
        Only allowed while status='draft'.
        """
        invoice = self.get_invoice(invoice_id)
        if invoice.status != "draft":
            raise ValueError(
                f"Invoice can only be edited while in 'draft' status. Current: '{invoice.status}'"
            )

        for field in ("due_date", "notes"):
            value = data.get(field)
            if value is not None:
                setattr(invoice, field, value)

        return self.invoice_repo.update(invoice)

    # ── PDF Generation ────────────────────────────────────────────────────────

    def generate_pdf(self, invoice_id: str) -> str:
        """
        Render the invoice as a PDF and persist the file path on the invoice record.

        Returns:
            Absolute file path of the generated PDF.
        """
        from app.utils import pdf_generator
        from flask import current_app

        invoice = self.get_invoice(invoice_id)
        invoice_data = self._serialize_for_pdf(invoice)

        output_dir = current_app.config.get("PDF_OUTPUT_DIR", "generated_pdfs")
        pdf_path = pdf_generator.generate_invoice_pdf(invoice_data, output_dir)

        # Persist the PDF path on the invoice record
        invoice.pdf_url = pdf_path
        self.invoice_repo.update(invoice)

        self._log("invoice", invoice_id, "PDF_GENERATED", invoice.generated_by, {
            "pdf_path": pdf_path,
        })

        return pdf_path

    # ── Email Dispatch ────────────────────────────────────────────────────────

    def send_invoice_email(self, invoice_id: str, data: dict, sent_by: str) -> InvoiceEmail:
        """
        Email the invoice PDF to a recipient.

        Args:
            invoice_id: UUID of the invoice.
            data:       Validated dict from SendInvoiceEmailSchema.
                        Keys: recipient_email (required), subject (optional).
            sent_by:    UUID of the user dispatching the email.

        Returns:
            The InvoiceEmail record with final status ('sent' or 'failed').
        """
        from app.utils import email_sender

        invoice = self.get_invoice(invoice_id)

        # Auto-generate PDF if it doesn't exist yet
        if not invoice.pdf_url:
            self.generate_pdf(invoice_id)
            invoice = self.get_invoice(invoice_id)  # refresh after pdf_url update

        recipient = data["recipient_email"]
        subject   = data.get("subject") or f"Invoice {invoice.invoice_number} from VendorBridge"

        # Create email record in 'queued' state
        email_record = InvoiceEmail(
            invoice_id=invoice_id,
            sent_by=sent_by,
            recipient_email=recipient,
            subject=subject,
            status="queued",
        )
        self.db.add(email_record)
        self.db.flush()

        # Attempt email dispatch
        invoice_data = self._serialize_for_pdf(invoice)
        success = email_sender.send_invoice_email(
            to=recipient,
            subject=subject,
            invoice_data=invoice_data,
            pdf_path=invoice.pdf_url,
        )

        if success:
            email_record.status = "sent"
            email_record.sent_at = datetime.now(timezone.utc)
            # Transition invoice to 'sent' if it was in 'draft'
            if invoice.status == "draft":
                invoice.status = "sent"
                self.db.add(invoice)
        else:
            email_record.status = "failed"
            email_record.error_message = "Email delivery failed. Check SMTP configuration."

        self.db.commit()
        self.db.refresh(email_record)

        return email_record

    # ── Payment ───────────────────────────────────────────────────────────────

    def mark_paid(self, invoice_id: str, officer_id: str) -> Invoice:
        """
        Record payment confirmation for an invoice.
        Allowed only for invoices with status 'sent' or 'overdue'.
        """
        invoice = self.get_invoice(invoice_id)

        if invoice.status not in INVOICE_PAYABLE_STATUSES:
            raise ValueError(
                f"Invoice must be 'sent' or 'overdue' to mark as paid. "
                f"Current: '{invoice.status}'"
            )

        result = self.invoice_repo.mark_paid(invoice_id)
        self._log("invoice", invoice_id, "INVOICE_PAID", officer_id, {})
        return result

    def flag_overdue(self) -> int:
        """
        Batch job: flag all invoices past their due_date as 'overdue'.
        Returns the count of invoices updated.
        Called by a scheduled task or admin endpoint.
        """
        overdue_invoices, _ = self.invoice_repo.get_overdue()
        count = 0
        for invoice in overdue_invoices:
            invoice.status = "overdue"
            count += 1
        if count:
            self.db.commit()
        return count

    # ── Internal Helpers ──────────────────────────────────────────────────────

    def _serialize_for_pdf(self, invoice: Invoice) -> dict:
        """
        Serialize an Invoice ORM object into a plain dict
        suitable for Jinja2 template rendering via WeasyPrint.
        """
        return {
            "invoice_number": invoice.invoice_number,
            "invoice_date":   invoice.invoice_date,
            "due_date":       invoice.due_date,
            "status":         invoice.status,
            "subtotal":       invoice.subtotal,
            "cgst_amount":    invoice.cgst_amount,
            "sgst_amount":    invoice.sgst_amount,
            "igst_amount":    invoice.igst_amount,
            "total_amount":   invoice.total_amount,
            "notes":          invoice.notes,
            # Vendor details (lazy-loaded by SQLAlchemy)
            "vendor_name":    invoice.vendor.company_name if invoice.vendor else "",
            "vendor_gst":     invoice.vendor.gst_number  if invoice.vendor else "",
            "vendor_address": invoice.vendor.address      if invoice.vendor else "",
            # Line items
            "items": [
                {
                    "item_name":  item.item_name,
                    "quantity":   item.quantity,
                    "unit_price": item.unit_price,
                    "tax_rate":   item.tax_rate,
                    "line_total": item.line_total,
                    "hsn_code":   item.hsn_code,
                }
                for item in invoice.items
            ],
        }

    def _log(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor_id: str,
        metadata: dict,
    ) -> None:
        """Append an immutable audit log entry. Failures are silently swallowed."""
        try:
            log = ActivityLog(
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                metadata_=metadata,
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            pass
