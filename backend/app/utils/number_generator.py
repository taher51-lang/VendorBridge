"""
VendorBridge ERP – Number Generator
=====================================
Generates unique, human-readable sequential numbers for
RFQs, Quotations, POs, and Invoices.

Format examples:
    RFQ-2024-0001
    QUO-2024-0001
    PO-2024-0001
    INV-2024-0001
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session


def _next_sequence(db: Session, model_class, number_column: str, prefix: str) -> str:
    """
    Generic helper that finds the MAX sequence number for the current year
    and returns the next formatted document number.

    Uses a single MAX query for thread-safety under moderate load.
    For high-concurrency environments, consider a DB sequence or advisory lock.
    """
    year = datetime.now(timezone.utc).year
    year_prefix = f"{prefix}-{year}-"

    # Fetch the latest number that matches this year's prefix
    column = getattr(model_class, number_column)
    row = (
        db.query(column)
        .filter(column.like(f"{year_prefix}%"))
        .order_by(column.desc())
        .first()
    )

    if row is None:
        next_seq = 1
    else:
        # Extract the numeric suffix: "RFQ-2024-0042" → 42
        latest_str = row[0]  # e.g. "RFQ-2024-0042"
        try:
            suffix = latest_str.rsplit("-", 1)[-1]
            next_seq = int(suffix) + 1
        except (ValueError, IndexError):
            next_seq = 1

    return f"{year_prefix}{next_seq:04d}"


def generate_rfq_number(db: Session) -> str:
    """
    Generate the next RFQ number in sequence.

    Format: RFQ-{YYYY}-{NNNN}
    """
    from app.models.rfq import RFQ
    return _next_sequence(db, RFQ, "rfq_number", "RFQ")


def generate_quote_number(db: Session) -> str:
    """
    Generate the next quotation number in sequence.

    Format: QUO-{YYYY}-{NNNN}
    """
    from app.models.quotation import Quotation
    return _next_sequence(db, Quotation, "quote_number", "QUO")


def generate_po_number(db: Session) -> str:
    """
    Generate the next PO number in sequence.

    Format: PO-{YYYY}-{NNNN}
    """
    from app.models.purchase_order import PurchaseOrder
    return _next_sequence(db, PurchaseOrder, "po_number", "PO")


def generate_invoice_number(db: Session) -> str:
    """
    Generate the next invoice number in sequence.

    Format: INV-{YYYY}-{NNNN}
    """
    from app.models.invoice import Invoice
    return _next_sequence(db, Invoice, "invoice_number", "INV")
