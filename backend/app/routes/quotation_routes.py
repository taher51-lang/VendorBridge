"""
VendorBridge ERP – Quotation Routes
=====================================
Endpoints for quotation CRUD, submission, comparison, and selection.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.quotation_service import QuotationService
from app.schemas.quotation_schema import QuotationCreateSchema, QuotationUpdateSchema
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required

quotation_bp = Blueprint("quotations", __name__)


@quotation_bp.route("/", methods=["POST"])
@jwt_required()
def create_quotation():
    """
    POST /api/v1/quotations
    Submit a new quotation for an RFQ.
    Accessible by: vendor.
    """
    # 1. Verify role is vendor
    # 2. Validate body with QuotationCreateSchema
    # 3. Get vendor_id from current user's vendor profile
    # 4. Call QuotationService(db).create_quotation(data, vendor_id)
    # 5. Return created quotation (201)
    pass


@quotation_bp.route("/", methods=["GET"])
@jwt_required()
def list_quotations():
    """
    GET /api/v1/quotations?rfq_id=...&page=1
    List quotations.
    Vendors see their own; officers/managers see all for an RFQ.
    """
    # 1. Extract query params
    # 2. Route to appropriate service method based on role
    pass


@quotation_bp.route("/<quotation_id>", methods=["GET"])
@jwt_required()
def get_quotation(quotation_id):
    """
    GET /api/v1/quotations/<quotation_id>
    Get quotation details with items.
    """
    # 1. Call QuotationService(db).get_quotation(quotation_id)
    # 2. Verify authorization (vendor can only see own, officer sees all)
    pass


@quotation_bp.route("/<quotation_id>", methods=["PUT"])
@jwt_required()
def update_quotation(quotation_id):
    """
    PUT /api/v1/quotations/<quotation_id>
    Edit a draft quotation.
    Accessible by: owning vendor only.
    """
    # 1. Validate body with QuotationUpdateSchema
    # 2. Call QuotationService(db).update_quotation(quotation_id, data, vendor_id)
    pass


@quotation_bp.route("/<quotation_id>/submit", methods=["POST"])
@jwt_required()
def submit_quotation(quotation_id):
    """
    POST /api/v1/quotations/<quotation_id>/submit
    Submit a draft quotation.
    """
    # 1. Get vendor_id
    # 2. Call QuotationService(db).submit_quotation(quotation_id, vendor_id)
    pass


@quotation_bp.route("/compare/<rfq_id>", methods=["GET"])
@jwt_required()
def compare_quotations(rfq_id):
    """
    GET /api/v1/quotations/compare/<rfq_id>
    Side-by-side comparison of all submitted quotations for an RFQ.
    Accessible by: procurement_officer, manager, admin.
    """
    # 1. Call QuotationService(db).compare_quotations(rfq_id)
    # 2. Return comparison data
    pass


@quotation_bp.route("/<quotation_id>/select", methods=["POST"])
@jwt_required()
def select_quotation(quotation_id):
    """
    POST /api/v1/quotations/<quotation_id>/select
    Select a quotation as the winner.
    Accessible by: procurement_officer.
    """
    # 1. Verify role
    # 2. Call QuotationService(db).select_quotation(quotation_id, officer_id)
    pass
