"""
VendorBridge ERP – Purchase Order Model
========================================
Issued after a quotation has been approved.
Links 1:1 to a Quotation and eventually to an Invoice.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Date, DateTime, Numeric,
    ForeignKey, Enum as SAEnum, SmallInteger,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class PurchaseOrder(BaseModel, Base):
    """
    An official purchase order sent to a vendor after approval.
    """
    __tablename__ = "purchase_orders"

    po_number = Column(
        String(30), unique=True, nullable=False, index=True,
    )
    quotation_id = Column(
        String(36),
        ForeignKey("quotations.id"),
        unique=True,
        nullable=False,
    )
    vendor_id = Column(
        String(36), ForeignKey("vendors.id"), nullable=False,
    )
    created_by = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )
    workflow_id = Column(
        String(36), ForeignKey("approval_workflows.id"),
        nullable=True, index=True,
    )

    # ── Delivery ──────────────────────────────────────────────────
    delivery_address = Column(Text, nullable=True)
    expected_delivery = Column(Date, nullable=True)

    # ── Financial ─────────────────────────────────────────────────
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    # ── Terms ─────────────────────────────────────────────────────
    terms_conditions = Column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────────────
    status = Column(
        SAEnum(
            "issued", "acknowledged", "fulfilled", "cancelled",
            name="po_status_enum",
        ),
        default="issued",
        index=True,
        nullable=False,
    )
    issued_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    quotation = relationship("Quotation")
    vendor = relationship("Vendor", back_populates="purchase_orders")
    creator = relationship("User")
    workflow = relationship(
        "ApprovalWorkflow", back_populates="purchase_order",
    )
    items = relationship(
        "POItem",
        back_populates="po",
        cascade="all, delete-orphan",
    )
    invoice = relationship(
        "Invoice", back_populates="po", uselist=False,
    )
    ratings = relationship("VendorRating")


class POItem(BaseModel, Base):
    """
    Denormalized line item snapshot on a Purchase Order.
    A PO is a legal document — prices/quantities may differ from the
    quotation, so items are stored independently rather than referencing
    quotation_items.
    """
    __tablename__ = "po_items"

    po_id = Column(
        String(36),
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    rfq_item_id = Column(
        String(36),
        ForeignKey("rfq_items.id"),
        nullable=True,  # soft reference only, no cascade
    )
    item_name = Column(String(200), nullable=False)   # denormalized snapshot
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0, nullable=False)
    line_total = Column(Numeric(15, 2), nullable=True)  # stored, not computed on read
    hsn_code = Column(String(20), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    po = relationship("PurchaseOrder", back_populates="items")
