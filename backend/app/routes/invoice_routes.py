"""
VendorBridge ERP – Invoice Routes
===================================
REST API endpoints for invoice CRUD, PDF generation, and email dispatch.
All routes are JWT-protected and role-gated.
Consumed by React frontend via Axios at /api/v1/invoices/...
"""

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required

from app.database import SessionLocal
from app.services.invoice_service import InvoiceService
from app.schemas.invoice_schema import (
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    InvoiceResponseSchema,
    InvoiceEmailSchema,
    SendInvoiceEmailSchema,
)
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import roles_required, get_current_user_id

invoice_bp = Blueprint("invoices", __name__)

# Schema instances (reused across requests)
_create_schema      = InvoiceCreateSchema()
_update_schema      = InvoiceUpdateSchema()
_response_schema    = InvoiceResponseSchema()
_send_email_schema  = SendInvoiceEmailSchema()
_email_rec_schema   = InvoiceEmailSchema()


# ── POST /api/v1/invoices/ ────────────────────────────────────────────────────

@invoice_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def create_invoice():
    """
    Generate an invoice from an issued/acknowledged PO.
    Body: { po_id, invoice_date, is_interstate, items[], due_date?, notes? }

    Returns 201 with the created invoice including auto-generated invoice_number
    and computed GST breakdown (CGST/SGST or IGST).
    """
    body = request.get_json(silent=True) or {}

    errors = _create_schema.validate(body)
    if errors:
        return error_response("Validation failed", 422, errors)

    data    = _create_schema.load(body)
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service = InvoiceService(db)
        invoice = service.create_invoice(data, user_id)
        return success_response(
            _response_schema.dump(invoice),
            "Invoice created successfully",
            201,
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── GET /api/v1/invoices/ ─────────────────────────────────────────────────────

@invoice_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin")
def list_invoices():
    """
    List invoices with optional filters.
    Query params: page, per_page, status, vendor_id
    """
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 20))
    status    = request.args.get("status")
    vendor_id = request.args.get("vendor_id")

    filters = {}
    if status:
        filters["status"] = status
    if vendor_id:
        filters["vendor_id"] = vendor_id

    db = SessionLocal()
    try:
        service = InvoiceService(db)
        invoices, total = service.list_invoices(page, per_page, filters)
        return paginated_response(
            [_response_schema.dump(inv) for inv in invoices],
            total, page, per_page,
            "Invoices retrieved",
        )
    except Exception as exc:
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── GET /api/v1/invoices/<invoice_id> ─────────────────────────────────────────

@invoice_bp.route("/<invoice_id>", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin", "vendor")
def get_invoice(invoice_id):
    """
    Get full invoice details including line items and email history.
    Vendors can view their own invoices.
    """
    db = SessionLocal()
    try:
        service = InvoiceService(db)
        invoice = service.get_invoice(invoice_id)
        return success_response(_response_schema.dump(invoice))
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── PUT /api/v1/invoices/<invoice_id> ─────────────────────────────────────────

@invoice_bp.route("/<invoice_id>", methods=["PUT"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def update_invoice(invoice_id):
    """
    Edit a draft invoice (due_date and notes only).
    Only allowed while status='draft'.
    Body: { due_date?, notes? }
    """
    body = request.get_json(silent=True) or {}

    errors = _update_schema.validate(body)
    if errors:
        return error_response("Validation failed", 422, errors)

    data = _update_schema.load(body)

    db = SessionLocal()
    try:
        service = InvoiceService(db)
        invoice = service.update_invoice(invoice_id, data)
        return success_response(_response_schema.dump(invoice), "Invoice updated")
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/invoices/<invoice_id>/pdf ────────────────────────────────────

@invoice_bp.route("/<invoice_id>/pdf", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def generate_pdf(invoice_id):
    """
    Generate (or regenerate) the invoice PDF.
    Returns the saved PDF path in the response.
    The React frontend can use the /pdf/download endpoint to fetch the binary file.
    """
    db = SessionLocal()
    try:
        service  = InvoiceService(db)
        pdf_path = service.generate_pdf(invoice_id)
        return success_response({"pdf_url": pdf_path}, "PDF generated successfully")
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response("PDF generation failed", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── GET /api/v1/invoices/<invoice_id>/pdf/download ────────────────────────────

@invoice_bp.route("/<invoice_id>/pdf/download", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin", "vendor")
def download_pdf(invoice_id):
    """
    Download the invoice as a binary PDF file.
    Auto-generates PDF if not yet generated.
    Used by the React 'Download Invoice' button (opens/saves the PDF).

    Response: application/pdf binary stream (Content-Disposition: attachment)
    """
    db = SessionLocal()
    try:
        service = InvoiceService(db)
        invoice = service.get_invoice(invoice_id)

        # Auto-generate PDF if not yet done
        if not invoice.pdf_url:
            pdf_path = service.generate_pdf(invoice_id)
        else:
            pdf_path = invoice.pdf_url

        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{invoice.invoice_number}.pdf",
        )
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response("PDF download failed", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/invoices/<invoice_id>/send ───────────────────────────────────

@invoice_bp.route("/<invoice_id>/send", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def send_invoice(invoice_id):
    """
    Email the invoice PDF to a recipient.
    Auto-generates PDF if needed, then sends via Flask-Mail (SMTP).
    Creates an InvoiceEmail record tracking the dispatch status.
    Body: { recipient_email (required), subject (optional) }
    """
    body = request.get_json(silent=True) or {}

    errors = _send_email_schema.validate(body)
    if errors:
        return error_response("Validation failed", 422, errors)

    data    = _send_email_schema.load(body)
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service      = InvoiceService(db)
        email_record = service.send_invoice_email(invoice_id, data, user_id)
        return success_response(
            _email_rec_schema.dump(email_record),
            "Invoice email dispatched successfully"
            if email_record.status == "sent"
            else "Invoice email queued but delivery failed — check SMTP settings",
        )
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Email dispatch failed", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/invoices/<invoice_id>/mark-paid ──────────────────────────────

@invoice_bp.route("/<invoice_id>/mark-paid", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin")
def mark_paid(invoice_id):
    """
    Record payment confirmation for an invoice.
    Allowed only for invoices with status 'sent' or 'overdue'.
    Transitions status → 'paid' and records paid_at timestamp.
    """
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service = InvoiceService(db)
        invoice = service.mark_paid(invoice_id, user_id)
        return success_response(_response_schema.dump(invoice), "Invoice marked as paid")
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/invoices/flag-overdue ────────────────────────────────────────

@invoice_bp.route("/flag-overdue", methods=["POST"])
@jwt_required()
@roles_required("admin")
def flag_overdue():
    """
    Admin-only batch job: mark all past-due invoices as 'overdue'.
    In production, call this from a scheduler (e.g. APScheduler or cron).
    Returns count of invoices updated.
    """
    db = SessionLocal()
    try:
        service = InvoiceService(db)
        count   = service.flag_overdue()
        return success_response(
            {"updated_count": count},
            f"{count} invoice(s) flagged as overdue",
        )
    except Exception as exc:
        db.rollback()
        return error_response("Batch job failed", 500, {"detail": str(exc)})
    finally:
        db.close()
