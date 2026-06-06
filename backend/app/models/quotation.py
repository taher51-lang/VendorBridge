"""
VendorBridge ERP – Quotation Models
=====================================
Vendor-submitted quotations against an RFQ.
Includes per-item pricing and totals calculation.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import (
    Column, String, Text, Integer, SmallInteger, DateTime, Numeric,
    Boolean, ForeignKey, Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class Quotation(BaseModel, Base):
    """
    A price quote submitted by a vendor in response to an RFQ.
    """
    __tablename__ = "quotations"
    __table_args__ = (
        UniqueConstraint(
            "rfq_id", "vendor_id", "revision_no",
            name="uq_rfq_vendor_revision",
        ),
    )

    quote_number = Column(
        String(30), unique=True, nullable=False, index=True,
    )
    rfq_id = Column(
        String(36), ForeignKey("rfqs.id"), nullable=False,
    )
    vendor_id = Column(
        String(36), ForeignKey("vendors.id"), nullable=False,
    )
    revision_no = Column(SmallInteger, default=1, nullable=False)

    # ── Financial ─────────────────────────────────────────────────
    subtotal = Column(Numeric(15, 2), default=0, nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0, nullable=False)
    cgst_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    sgst_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    igst_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_amount = Column(Numeric(15, 2), default=0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    is_interstate = Column(Boolean, default=False, nullable=False)

    # ── Terms ─────────────────────────────────────────────────────
    delivery_days = Column(Integer, nullable=False)
    validity_days = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────────────
    status = Column(
        SAEnum(
            "draft", "submitted", "selected", "rejected",
            name="quotation_status_enum",
        ),
        default="draft",
        index=True,
        nullable=False,
    )
    submitted_at = Column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    rfq = relationship("RFQ", back_populates="quotations")
    vendor = relationship("Vendor", back_populates="quotations")
    items = relationship(
        "QuotationItem",
        back_populates="quotation",
        cascade="all, delete-orphan",
    )
    workflow = relationship(
        "ApprovalWorkflow",
        back_populates="quotation",
        uselist=False,
    )

    # ── Methods ───────────────────────────────────────────────────

    def calculate_totals(self, is_interstate: bool = False) -> None:
        """
        Iterate over self.items, sum line_total into subtotal,
        compute tax_amount from each item's tax_rate, distribute
        into CGST/SGST (intra-state) or IGST (inter-state), and
        set total_amount = subtotal + tax_amount.
        """
        subtotal = Decimal("0.00")
        raw_tax = Decimal("0.00")

        for item in self.items:
            if item.line_total is not None:
                line = Decimal(str(item.line_total))
                subtotal += line
                rate = Decimal(str(item.tax_rate or 0))
                raw_tax += (line * rate / Decimal("100")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP,
                )

        self.subtotal = subtotal.quantize(Decimal("0.01"))
        self.tax_amount = raw_tax.quantize(Decimal("0.01"))

        # GST split
        if is_interstate:
            self.igst_amount = self.tax_amount
            self.cgst_amount = Decimal("0.00")
            self.sgst_amount = Decimal("0.00")
        else:
            self.cgst_amount = (self.tax_amount / Decimal("2")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP,
            )
            self.sgst_amount = self.tax_amount - self.cgst_amount  # handles odd paise
            self.igst_amount = Decimal("0.00")

        self.total_amount = (self.subtotal + self.tax_amount).quantize(
            Decimal("0.01"),
        )
        self.is_interstate = is_interstate


class QuotationItem(BaseModel, Base):
    """
    A single line item within a quotation, tied back to an RFQ item.
    """
    __tablename__ = "quotation_items"

    quotation_id = Column(
        String(36),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    rfq_item_id = Column(
        String(36),
        ForeignKey("rfq_items.id"),
        nullable=True,
    )

    # ── Pricing ───────────────────────────────────────────────────
    unit_price = Column(Numeric(15, 4), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0, nullable=False)
    line_total = Column(Numeric(15, 2), nullable=True)
    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    quotation = relationship("Quotation", back_populates="items")
    rfq_item = relationship("RFQItem", back_populates="quotation_items")

    # ── Methods ───────────────────────────────────────────────────

    def calculate_line_total(self) -> None:
        """Set line_total = quantity × unit_price."""
        qty = Decimal(str(self.quantity))
        price = Decimal(str(self.unit_price))
        self.line_total = (qty * price).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP,
        )
