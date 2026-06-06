"""
VendorBridge ERP – Models Package Init
=======================================
Import every model class so that:
  1. SQLAlchemy's Base.metadata knows about all tables.
  2. Alembic can detect all models during autogenerate.
  3. Base.metadata.create_all() works from a single `import app.models`.
"""

# ── Base & database ───────────────────────────────────────────────
from app.models.base import BaseModel  # noqa: F401

# ── Domain models ─────────────────────────────────────────────────
from app.models.user import User  # noqa: F401

from app.models.vendor import (  # noqa: F401
    VendorCategory,
    Vendor,
    VendorRating,
)

from app.models.rfq import (  # noqa: F401
    RFQ,
    RFQItem,
    RFQVendorAssignment,
)

from app.models.quotation import (  # noqa: F401
    Quotation,
    QuotationItem,
)

from app.models.approval import (  # noqa: F401
    ApprovalWorkflow,
    ApprovalStep,
)

from app.models.purchase_order import (  # noqa: F401
    PurchaseOrder,
    POItem,
)

from app.models.invoice import (  # noqa: F401
    Invoice,
    InvoiceItem,
    InvoiceEmail,
)

from app.models.audit import (  # noqa: F401
    ActivityLog,
    Notification,
)
