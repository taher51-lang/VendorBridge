from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

def generate_rfq_number(db: Session) -> str:
    """
    Generate the next RFQ number in sequence.
    Format: RFQ-{YYYY}-{NNNN}
    """
    from app.models.rfq import RFQ
    year = datetime.now(timezone.utc).year
    prefix = f"RFQ-{year}-"
    
    # Query for the highest RFQ number matching the prefix
    latest = db.query(RFQ.rfq_number).filter(
        RFQ.rfq_number.like(f"{prefix}%")
    ).order_by(RFQ.rfq_number.desc()).first()
    
    if not latest or not latest[0]:
        next_num = 1
    else:
        try:
            suffix = latest[0].split("-")[-1]
            next_num = int(suffix) + 1
        except ValueError:
            next_num = 1
            
    return f"{prefix}{next_num:04d}"


def generate_quote_number(db: Session) -> str:
    """
    Generate the next quotation number in sequence.
    Format: QUO-{YYYY}-{NNNN}
    """
    from app.models.quotation import Quotation
    year = datetime.now(timezone.utc).year
    prefix = f"QUO-{year}-"
    
    latest = db.query(Quotation.quote_number).filter(
        Quotation.quote_number.like(f"{prefix}%")
    ).order_by(Quotation.quote_number.desc()).first()
    
    if not latest or not latest[0]:
        next_num = 1
    else:
        try:
            suffix = latest[0].split("-")[-1]
            next_num = int(suffix) + 1
        except ValueError:
            next_num = 1
            
    return f"{prefix}{next_num:04d}"


def generate_po_number(db: Session) -> str:
    """
    Generate the next PO number in sequence.
    Format: PO-{YYYY}-{NNNN}
    """
    from app.models.purchase_order import PurchaseOrder
    year = datetime.now(timezone.utc).year
    prefix = f"PO-{year}-"
    
    latest = db.query(PurchaseOrder.po_number).filter(
        PurchaseOrder.po_number.like(f"{prefix}%")
    ).order_by(PurchaseOrder.po_number.desc()).first()
    
    if not latest or not latest[0]:
        next_num = 1
    else:
        try:
            suffix = latest[0].split("-")[-1]
            next_num = int(suffix) + 1
        except ValueError:
            next_num = 1
            
    return f"{prefix}{next_num:04d}"


def generate_invoice_number(db: Session) -> str:
    """
    Generate the next invoice number in sequence.
    Format: INV-{YYYY}-{NNNN}
    """
    from app.models.invoice import Invoice
    year = datetime.now(timezone.utc).year
    prefix = f"INV-{year}-"
    
    latest = db.query(Invoice.invoice_number).filter(
        Invoice.invoice_number.like(f"{prefix}%")
    ).order_by(Invoice.invoice_number.desc()).first()
    
    if not latest or not latest[0]:
        next_num = 1
    else:
        try:
            suffix = latest[0].split("-")[-1]
            next_num = int(suffix) + 1
        except ValueError:
            next_num = 1
            
    return f"{prefix}{next_num:04d}"

