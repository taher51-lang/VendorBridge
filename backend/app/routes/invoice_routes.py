"""
VendorBridge ERP – Invoice Routes
===================================
Endpoints for invoice CRUD, PDF generation, and email dispatch.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoice_schema import (
    InvoiceCreateSchema,
    InvoiceUpdateSchema,
    SendInvoiceEmailSchema,
)
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required

invoice_bp = Blueprint("invoices", __name__)


@invoice_bp.route("/", methods=["POST"])
@jwt_required()
def create_invoice():
    """
    POST /api/v1/invoices
    Generate an invoice from a fulfilled PO.
    Accessible by: procurement_officer.
    """
    # 1. Validate body with InvoiceCreateSchema
    # 2. Call InvoiceService(db).create_invoice(data, generated_by=user_id)
    # 3. Return created invoice (201)
    pass


@invoice_bp.route("/", methods=["GET"])
@jwt_required()
def list_invoices():
    """
    GET /api/v1/invoices?page=1&status=sent
    List invoices with pagination.
    """
    # 1. Extract query params
    # 2. Route to service based on filters and role
    pass


@invoice_bp.route("/<invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice(invoice_id):
    """
    GET /api/v1/invoices/<invoice_id>
    Get invoice details with items and email history.
    """
    # 1. Call InvoiceService(db).get_invoice(invoice_id)
    pass


@invoice_bp.route("/<invoice_id>", methods=["PUT"])
@jwt_required()
def update_invoice(invoice_id):
    """
    PUT /api/v1/invoices/<invoice_id>
    Edit a draft invoice.
    """
    # 1. Validate with InvoiceUpdateSchema
    # 2. Call InvoiceService(db).update_invoice(invoice_id, data)
    pass


@invoice_bp.route("/<invoice_id>/pdf", methods=["POST"])
@jwt_required()
def generate_pdf(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/pdf
    Generate (or regenerate) the invoice PDF.
    Returns the PDF URL.
    """
    # 1. Call InvoiceService(db).generate_pdf(invoice_id)
    # 2. Return {pdf_url: ...}
    pass


@invoice_bp.route("/<invoice_id>/send", methods=["POST"])
@jwt_required()
def send_invoice(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/send
    Email the invoice to a recipient.
    Body: {"recipient_email": "...", "subject": "..."}
    """
    # 1. Validate with SendInvoiceEmailSchema
    # 2. Call InvoiceService(db).send_invoice_email(invoice_id, data, sent_by)
    pass


@invoice_bp.route("/<invoice_id>/mark-paid", methods=["POST"])
@jwt_required()
def mark_paid(invoice_id):
    """
    POST /api/v1/invoices/<invoice_id>/mark-paid
    Record payment.
    """
    # 1. Call InvoiceService(db).mark_paid(invoice_id, officer_id)
    pass
