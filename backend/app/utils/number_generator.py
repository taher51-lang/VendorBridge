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

NOTE ON THREAD SAFETY:
    This implementation uses MAX() which has a known race condition:
    two simultaneous requests could read the same MAX value and
    generate the same number. This is acceptable for hackathon/demo
    with a small team. For production, replace with PostgreSQL
    sequences or a dedicated numbering table with row locking.
"""

import re
from datetime import datetime

from sqlalchemy.orm import Session


def _next_sequence(db: Session, model_class, number_field: str, prefix: str) -> str:
    """
    Generate the next sequential number for the given prefix and year.

    Args:
        db:            SQLAlchemy session.
        model_class:   ORM model to query (e.g. PurchaseOrder).
        number_field:  Column name holding the formatted number (e.g. 'po_number').
        prefix:        Prefix string (e.g. 'PO', 'INV').

    Returns:
        Formatted string like 'PO-2025-0001'.
    """
    year = datetime.utcnow().year
    year_prefix = f"{prefix}-{year}-"

    column = getattr(model_class, number_field)

    # MAX() query – see thread-safety note above
    latest = (
        db.query(column)
        .filter(column.like(f"{year_prefix}%"))
        .order_by(column.desc())
        .first()
    )

    if latest is None:
        next_seq = 1
    else:
        match = re.search(r"-(\d+)$", latest[0])
        next_seq = int(match.group(1)) + 1 if match else 1

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
