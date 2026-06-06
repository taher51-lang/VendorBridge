"""
VendorBridge ERP – BaseModel Mixin
===================================
A reusable mixin that provides common columns and helper methods
for every model in the application.

Every domain model inherits from both BaseModel (this mixin)
and Base (the declarative base defined in app.database).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.inspection import inspect


class BaseModel:
    """
    Mixin that adds id, timestamps, soft-delete marker,
    to_dict(), and a human-readable __repr__ to any SQLAlchemy model.
    """

    # ── Primary Key ───────────────────────────────────────────────
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    # ── Timestamps ────────────────────────────────────────────────
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    # ── Soft Delete ───────────────────────────────────────────────
    deleted_at = Column(DateTime, nullable=True)

    # ── Helpers ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Serialize all column values to a plain Python dict.
        Excludes the soft-delete marker (deleted_at) and converts
        datetime objects to ISO-8601 strings for JSON friendliness.
        """
        result = {}
        for column in inspect(self.__class__).columns:
            if column.key == "deleted_at":
                continue
            value = getattr(self, column.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[column.key] = value
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"
