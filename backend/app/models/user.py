"""
VendorBridge ERP – User Model
==============================
Represents an authenticated user in the system.
Roles: admin, procurement_officer, manager, vendor.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel

# bcrypt is used for password hashing; import the global instance
# initialised in app.__init__  OR use flask_bcrypt standalone.
from flask_bcrypt import generate_password_hash, check_password_hash


class User(BaseModel, Base):
    __tablename__ = "users"

    # ── Columns ───────────────────────────────────────────────────
    email = Column(
        String(255), unique=True, nullable=False, index=True,
    )
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(
        SAEnum(
            "admin", "procurement_officer", "manager", "vendor",
            name="user_role_enum",
        ),
        nullable=False,
        index=True,
    )
    phone = Column(String(20), nullable=True)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    vendor = relationship(
        "Vendor", back_populates="user", uselist=False,
    )
    rfqs = relationship(
        "RFQ", back_populates="creator",
    )
    notifications = relationship(
        "Notification", back_populates="user",
    )
    initiated_workflows = relationship(
        "ApprovalWorkflow", back_populates="initiator",
    )
    approval_steps = relationship(
        "ApprovalStep", back_populates="approver",
    )

    # ── Password helpers ──────────────────────────────────────────
    def to_dict(self):
        d = super().to_dict()
        d.pop("password_hash", None)
        return d
        
    def set_password(self, raw_password: str) -> None:
        """Hash *raw_password* with bcrypt and store in password_hash."""
        self.password_hash = generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        """Return True if *raw_password* matches the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    # ── Role convenience checks ───────────────────────────────────

    def is_vendor(self) -> bool:
        return self.role == "vendor"

    def is_admin(self) -> bool:
        return self.role == "admin"

    def is_officer(self) -> bool:
        return self.role == "procurement_officer"

    def is_manager(self) -> bool:
        return self.role == "manager"
