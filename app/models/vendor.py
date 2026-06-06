"""
VendorBridge ERP – Vendor Models
=================================
Vendor, VendorCategory (hierarchical), and VendorRating.
"""

from sqlalchemy import (
    Column, String, Text, ForeignKey, Numeric, SmallInteger,
    Enum as SAEnum, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class VendorCategory(BaseModel, Base):
    """
    Hierarchical vendor categories (e.g. IT → Software, IT → Hardware).
    Self-referential via parent_id.
    """
    __tablename__ = "vendor_categories"

    parent_id = Column(
        String(36),
        ForeignKey("vendor_categories.id"),
        nullable=True,
    )
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # ── Self-referential relationships ────────────────────────────
    subcategories = relationship(
        "VendorCategory",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    parent = relationship(
        "VendorCategory",
        back_populates="subcategories",
        remote_side="VendorCategory.id",
    )

    # ── Vendors in this category ──────────────────────────────────
    vendors = relationship("Vendor", back_populates="category")


class Vendor(BaseModel, Base):
    """
    Company profile linked 1:1 to a User with role='vendor'.
    """
    __tablename__ = "vendors"

    # ── Foreign Keys ──────────────────────────────────────────────
    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )
    category_id = Column(
        String(36), ForeignKey("vendor_categories.id"), nullable=True,
    )

    # ── Company Details ───────────────────────────────────────────
    company_name = Column(String(200), nullable=False)
    gst_number = Column(String(20), unique=True, nullable=True)
    pan_number = Column(String(15), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    website = Column(String(255), nullable=True)

    # ── Status & Metrics ──────────────────────────────────────────
    status = Column(
        SAEnum(
            "pending", "active", "suspended", "blacklisted",
            name="vendor_status_enum",
        ),
        default="pending",
        index=True,
        nullable=False,
    )
    avg_rating = Column(Numeric(3, 2), default=0.00)

    # ── Relationships ─────────────────────────────────────────────
    user = relationship("User", back_populates="vendor")
    category = relationship("VendorCategory", back_populates="vendors")
    rfq_assignments = relationship(
        "RFQVendorAssignment", back_populates="vendor",
    )
    quotations = relationship("Quotation", back_populates="vendor")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor")
    ratings = relationship("VendorRating", back_populates="vendor")


class VendorRating(BaseModel, Base):
    """
    Per-PO rating left by a procurement officer / manager.
    One rating per (vendor, po) pair.
    """
    __tablename__ = "vendor_ratings"
    __table_args__ = (
        UniqueConstraint("vendor_id", "po_id", name="uq_vendor_po_rating"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────
    vendor_id = Column(
        String(36), ForeignKey("vendors.id"), nullable=False,
    )
    po_id = Column(
        String(36), ForeignKey("purchase_orders.id"), nullable=False,
    )
    rated_by = Column(
        String(36), ForeignKey("users.id"), nullable=False,
    )

    # ── Scores ────────────────────────────────────────────────────
    quality_score = Column(SmallInteger, nullable=False)    # 1-5
    delivery_score = Column(SmallInteger, nullable=False)   # 1-5
    pricing_score = Column(SmallInteger, nullable=False)    # 1-5
    overall_score = Column(Numeric(3, 2), nullable=True)
    comments = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    vendor = relationship("Vendor", back_populates="ratings")

    # ── Methods ───────────────────────────────────────────────────

    def calculate_overall(self) -> None:
        """
        Compute the average of the three individual scores and
        store the result in overall_score.
        """
        from decimal import Decimal, ROUND_HALF_UP

        total = self.quality_score + self.delivery_score + self.pricing_score
        avg = Decimal(total) / Decimal(3)
        self.overall_score = avg.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
