"""
VendorBridge ERP – Invoice Models
==================================
Invoice, InvoiceItem, and InvoiceEmail models.
Supports Indian GST (CGST/SGST for intra-state, IGST for inter-state).
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import (
    Column, String, Text, Date, DateTime, Numeric,
    ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class Invoice(BaseModel, Base):
    """
    Tax invoice generated from a fulfilled Purchase Order.
    """
    __tablename__ = "invoices"

    invoice_number = Column(
        String(30), unique=True, nullable=False, index=True,
    )
    po_id = Column(
        String(36),
        ForeignKey("purchase_orders.id"),
        unique=True,
        nullable=False,
    )
    vendor_id = Column(
        String(36), ForeignKey("vendors.id"), nullable=False,
    )
    generated_by = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )

    # ── Dates ─────────────────────────────────────────────────────
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)

    # ── Financial ─────────────────────────────────────────────────
    subtotal = Column(Numeric(15, 2), nullable=False)
    cgst_amount = Column(Numeric(15, 2), default=0, nullable=False)
    sgst_amount = Column(Numeric(15, 2), default=0, nullable=False)
    igst_amount = Column(Numeric(15, 2), default=0, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # ── Artifacts ─────────────────────────────────────────────────
    pdf_url = Column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────────────
    status = Column(
        SAEnum(
            "draft", "sent", "paid", "overdue", "cancelled",
            name="invoice_status_enum",
        ),
        default="draft",
        index=True,
        nullable=False,
    )
    paid_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    po = relationship("PurchaseOrder", back_populates="invoice")
    vendor = relationship("Vendor")
    generator = relationship("User")
    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    emails = relationship(
        "InvoiceEmail",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    # ── GST Calculation ───────────────────────────────────────────

    def calculate_gst(self, is_interstate: bool, tax_amount: Decimal | float) -> None:
        """
        Distribute tax between IGST (inter-state) or CGST+SGST (intra-state).

        Args:
            is_interstate: True → full IGST; False → split CGST/SGST.
            tax_amount: The total tax value (already computed from line items).
        """
        tax = Decimal(str(tax_amount)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )

        if is_interstate:
            self.igst_amount = tax
            self.cgst_amount = Decimal("0.00")
            self.sgst_amount = Decimal("0.00")
        else:
            half = (tax / Decimal("2")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            )
            self.cgst_amount = half
            self.sgst_amount = half
            self.igst_amount = Decimal("0.00")

        self.total_amount = (
            Decimal(str(self.subtotal))
            + self.cgst_amount
            + self.sgst_amount
            + self.igst_amount
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class InvoiceItem(BaseModel, Base):
    """
    Individual line item on an invoice.
    """
    __tablename__ = "invoice_items"

    invoice_id = Column(
        String(36),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    quotation_item_id = Column(
        String(36),
        ForeignKey("quotation_items.id"),
        nullable=True,
    )
    item_name = Column(String(200), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False)
    line_total = Column(Numeric(15, 2), nullable=False)
    hsn_code = Column(String(20), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    invoice = relationship("Invoice", back_populates="items")


class InvoiceEmail(BaseModel, Base):
    """
    Tracks every email dispatch attempt for an invoice.
    """
    __tablename__ = "invoice_emails"

    invoice_id = Column(
        String(36), ForeignKey("invoices.id"), nullable=False,
    )
    sent_by = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(300), nullable=False)
    status = Column(
        SAEnum(
            "queued", "sent", "failed", "bounced",
            name="invoice_email_status_enum",
        ),
        default="queued",
        nullable=False,
    )
    provider_msg_id = Column(String(200), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    invoice = relationship("Invoice", back_populates="emails")
