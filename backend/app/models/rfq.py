"""
VendorBridge ERP – RFQ Models
==============================
Request for Quotation, RFQ line items, and vendor assignment junction.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, DateTime, SmallInteger, ForeignKey, JSON,
    Numeric, Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class RFQ(BaseModel, Base):
    """
    A Request for Quotation issued by a procurement officer.
    """
    __tablename__ = "rfqs"

    rfq_number = Column(
        String(30), unique=True, nullable=False, index=True,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )
    deadline = Column(DateTime, nullable=False)
    # State machine:
    #   draft → open → under_review → awarded → closed
    #   Any state → cancelled
    #
    # Definitions:
    #   draft        = created, not yet published to vendors
    #   open         = published, vendors can submit quotations
    #   under_review = deadline passed, team comparing quotations
    #   awarded      = a quotation selected, PO being prepared
    #   closed       = PO has been issued
    #   cancelled    = abandoned at any stage
    status = Column(
        SAEnum(
            "draft", "open", "under_review", "awarded", "closed", "cancelled",
            name="rfq_status_enum",
        ),
        default="draft",
        index=True,
        nullable=False,
    )
    attachment_urls = Column(JSON, nullable=True)  # list of file URL strings
    notes = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    creator = relationship("User", back_populates="rfqs")
    items = relationship(
        "RFQItem",
        back_populates="rfq",
        cascade="all, delete-orphan",
        order_by="RFQItem.sort_order",
    )
    vendor_assignments = relationship(
        "RFQVendorAssignment",
        back_populates="rfq",
        cascade="all, delete-orphan",
    )
    quotations = relationship("Quotation", back_populates="rfq")


class RFQItem(BaseModel, Base):
    """
    Individual line item within an RFQ.
    """
    __tablename__ = "rfq_items"

    rfq_id = Column(
        String(36),
        ForeignKey("rfqs.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit = Column(String(20), nullable=True)          # e.g. "kg", "pcs"
    specifications = Column(Text, nullable=True)
    sort_order = Column(SmallInteger, default=0)

    # ── Relationships ─────────────────────────────────────────────
    rfq = relationship("RFQ", back_populates="items")
    quotation_items = relationship("QuotationItem", back_populates="rfq_item")


class RFQVendorAssignment(BaseModel, Base):
    """
    Junction table: which vendors have been invited to respond to an RFQ.
    """
    __tablename__ = "rfq_vendor_assignments"
    __table_args__ = (
        UniqueConstraint("rfq_id", "vendor_id", name="uq_rfq_vendor"),
    )

    rfq_id = Column(
        String(36), ForeignKey("rfqs.id"), nullable=False,
    )
    vendor_id = Column(
        String(36), ForeignKey("vendors.id"), nullable=False,
    )
    invited_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
    )
    viewed_at = Column(DateTime, nullable=True)
    status = Column(
        SAEnum(
            "invited", "acknowledged", "declined",
            name="rfq_assignment_status_enum",
        ),
        default="invited",
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────
    rfq = relationship("RFQ", back_populates="vendor_assignments")
    vendor = relationship("Vendor", back_populates="rfq_assignments")
