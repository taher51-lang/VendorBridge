"""
VendorBridge ERP – Audit & Notification Models
================================================
ActivityLog: append-only audit trail (no updated_at / deleted_at).
Notification: per-user notification feed.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, DateTime, JSON, ForeignKey, Boolean, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import BaseModel


class ActivityLog(Base):
    """
    Immutable audit log.  Overrides BaseModel intentionally so that
    updated_at and deleted_at are excluded — this table is APPEND ONLY.
    """
    __tablename__ = "activity_logs"

    # ── Primary key & timestamp (hand-rolled, not from BaseModel) ─
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Audit fields ──────────────────────────────────────────────
    actor_id = Column(
        String(36), ForeignKey("users.id"), nullable=True,
    )  # nullable for system-initiated actions
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)

    def to_dict(self) -> dict:
        """Serialize to dict (no soft-delete field to exclude)."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "actor_id": self.actor_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "metadata": self.metadata_,
            "ip_address": self.ip_address,
        }

    def __repr__(self) -> str:
        return f"<ActivityLog id={self.id}>"


class Notification(BaseModel, Base):
    """
    In-app notification for a user.
    """
    __tablename__ = "notifications"

    user_id = Column(
        String(36), ForeignKey("users.id"), nullable=False, index=True,
    )
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    user = relationship("User", back_populates="notifications")

    # ── Methods ───────────────────────────────────────────────────

    def mark_as_read(self) -> None:
        from datetime import datetime
        self.is_read = True
        self.read_at = datetime.utcnow()

Index('ix_notifications_user_unread', Notification.user_id, Notification.is_read)
