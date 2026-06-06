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

from sqlalchemy.orm import Session


def generate_rfq_number(db: Session) -> str:
    """
    Generate the next RFQ number in sequence.

    Format: RFQ-{YYYY}-{NNNN}

    Implementation:
        1. Query the latest RFQ ordered by created_at DESC.
        2. Extract the numeric suffix from its rfq_number.
        3. Increment by 1.
        4. If no existing RFQs, start at 0001.
        5. Return formatted string.
    """
    # TODO: Implement sequential number generation
    # Consider using a database sequence or MAX query for thread safety.
    pass


def generate_quote_number(db: Session) -> str:
    """
    Generate the next quotation number in sequence.

    Format: QUO-{YYYY}-{NNNN}
    """
    # TODO: Same pattern as generate_rfq_number
    pass


def generate_po_number(db: Session) -> str:
    """
    Generate the next PO number in sequence.

    Format: PO-{YYYY}-{NNNN}
    """
    # TODO: Same pattern
    pass


def generate_invoice_number(db: Session) -> str:
    """
    Generate the next invoice number in sequence.

    Format: INV-{YYYY}-{NNNN}
    """
    # TODO: Same pattern
    pass
