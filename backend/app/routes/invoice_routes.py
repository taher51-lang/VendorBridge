"""
VendorBridge ERP – Invoice Routes
===================================
Endpoints for invoice CRUD, PDF generation, and email dispatch.
"""

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoice_schema import (
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    InvoiceResponseSchema,
    InvoiceEmailSchema,
    SendInvoiceEmailSchema,
)
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role

invoice_bp = Blueprint("invoices", __name__)


def _get_service():
    """Instantiate InvoiceService with a fresh DB session."""
    db = next(get_db())
    return InvoiceService(db), db


@invoice_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def create_invoice():
    """
    POST /api/v1/invoices
    Generate an invoice from a fulfilled PO.
    Accessible by: procurement_officer, admin.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    schema = InvoiceCreateSchema()
    errors = schema.validate(data)
    if errors:
        return error_response(str(errors), 422)

    validated = schema.load(data)
    user_id = get_current_user_id()

    try:
        service, _ = _get_service()
        invoice = service.create_invoice(validated, generated_by=user_id)
        response_schema = InvoiceResponseSchema()
        return success_response(
            response_schema.dump(invoice), "Invoice created successfully.", 201
        )
    except Exception as e:
        return error_response(str(e), 400)


@invoice_bp.route("/", methods=["GET"])
@jwt_required()
def list_invoices():
    """
    GET /api/v1/invoices?page=1&status=sent
    List invoices with pagination.
    """
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    status = request.args.get("status")

    role = get_current_user_role()
    user_id = get_current_user_id()

    try:
        service, db = _get_service()

        if role == "vendor":
            from app.models.vendor import Vendor
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor:
                return error_response("Vendor profile not found.", 404)
            results, total = service.get_vendor_invoices(vendor.id, page, per_page)
        else:
            filters = {}
            if status:
                filters["status"] = status
            results, total = service.list_invoices(page, per_page, filters)

        schema = InvoiceResponseSchema(many=True)
        return paginated_response(
            schema.dump(results), total, page, per_page,
            f"Found {total} invoice(s)."
        )
    except Exception as e:
        return error_response(str(e), 500)


@invoice_bp.route("/<invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice(invoice_id):
    """
    GET /api/v1/invoices/<invoice_id>
    Get invoice details with items and email history.
    """
    role = get_current_user_role()
    user_id = get_current_user_id()

    try:
        service, db = _get_service()
        invoice = service.get_invoice(invoice_id)

        # Vendors can only see their own invoices
        if role == "vendor":
            from app.models.vendor import Vendor
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor or invoice.vendor_id != vendor.id:
                return error_response("Access denied.", 403)

        schema = InvoiceResponseSchema()
        return success_response(schema.dump(invoice), "Invoice retrieved.")
    except Exception as e:
        return error_response(str(e), 404)


@invoice_bp.route("/<invoice_id>", methods=["PUT"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def update_invoice(invoice_id):
    """
    PUT /api/v1/invoices/<invoice_id>
    Edit a draft invoice.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    schema = InvoiceUpdateSchema()
    errors = schema.validate(data)
    if errors:
        return error_response(str(errors), 422)

    validated = schema.load(data)

    try:
        service, _ = _get_service()
        invoice = service.update_invoice(invoice_id, validated)
        response_schema = InvoiceResponseSchema()
        return success_response(response_schema.dump(invoice), "Invoice updated.")
    except Exception as e:
        return error_response(str(e), 400)


@invoice_bp.route("/<invoice_id>/pdf", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def generate_pdf(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/pdf
    Generate (or regenerate) the invoice PDF.
    Returns the PDF file as binary.
    """
    try:
        service, _ = _get_service()
        pdf_path = service.generate_pdf(invoice_id)

        import os
        if pdf_path and os.path.exists(pdf_path):
            return send_file(
                pdf_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=os.path.basename(pdf_path),
            )
        else:
            return success_response(
                {"pdf_url": pdf_path}, "PDF generated (file may not exist on disk)."
            )
    except Exception as e:
        return error_response(str(e), 400)


@invoice_bp.route("/<invoice_id>/send", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def send_invoice(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/send
    Email the invoice to a recipient.
    Body: {"recipient_email": "...", "subject": "..."}
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    schema = SendInvoiceEmailSchema()
    errors = schema.validate(data)
    if errors:
        return error_response(str(errors), 422)

    validated = schema.load(data)
    user_id = get_current_user_id()

    try:
        service, _ = _get_service()
        email_record = service.send_invoice_email(invoice_id, validated, sent_by=user_id)
        email_schema = InvoiceEmailSchema()
        return success_response(
            email_schema.dump(email_record), "Invoice email dispatched."
        )
    except Exception as e:
        return error_response(str(e), 400)


@invoice_bp.route("/<invoice_id>/mark-paid", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def mark_paid(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/mark-paid
    Record payment.
    """
    user_id = get_current_user_id()

    try:
        service, _ = _get_service()
        invoice = service.mark_paid(invoice_id, user_id)
        schema = InvoiceResponseSchema()
        return success_response(schema.dump(invoice), "Invoice marked as paid.")
    except Exception as e:
        return error_response(str(e), 400)


@invoice_bp.route("/<invoice_id>/cancel", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def cancel_invoice(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/cancel
    Cancel an invoice.
    """
    user_id = get_current_user_id()

    try:
        service, _ = _get_service()
        invoice = service.cancel_invoice(invoice_id, user_id)
        schema = InvoiceResponseSchema()
        return success_response(schema.dump(invoice), "Invoice cancelled.")
    except Exception as e:
        return error_response(str(e), 400)
