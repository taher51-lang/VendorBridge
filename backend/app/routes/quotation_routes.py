from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.quotation_service import QuotationService
from app.schemas.quotation_schema import QuotationCreateSchema, QuotationUpdateSchema, QuotationResponseSchema
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role
from app.models.vendor import Vendor

quotation_bp = Blueprint("quotations", __name__)


@quotation_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("vendor")
def create_quotation():
    """
    POST /api/v1/quotations
    Submit a new quotation for an RFQ.
    Accessible by: vendor.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    vendor = db.query(Vendor).filter_by(user_id=user_id).first()
    if not vendor:
        return error_response("Vendor profile not found.", 404)

    schema = QuotationCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)

    data = schema.load(request.json)
    service = QuotationService(db)
    try:
        quotation = service.create_quotation(data, vendor.id)
        response_schema = QuotationResponseSchema()
        return success_response(response_schema.dump(quotation), "Quotation created successfully.", 201)
    except Exception as e:
        return error_response(str(e), 400)


@quotation_bp.route("/", methods=["GET"])
@jwt_required()
def list_quotations():
    """
    GET /api/v1/quotations?rfq_id=...&page=1
    List quotations.
    Vendors see their own; officers/managers see all for an RFQ.
    """
    db = next(get_db())
    service = QuotationService(db)
    schema = QuotationResponseSchema(many=True)

    rfq_id    = request.args.get("rfq_id")
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 20))

    try:
        role = get_current_user_role()
        user_id = get_current_user_id()
        if role == "vendor":
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor:
                return error_response("Vendor profile not found.", 404)
            results, total = service.list_vendor_quotations(vendor.id, page, per_page)
        else:
            if rfq_id:
                results, total = service.list_rfq_quotations(rfq_id, page, per_page)
            else:
                return error_response("rfq_id query param is required.", 400)

        return success_response(
            schema.dump(results),
            f"Found {total} quotation(s).",
            meta={"page": page, "per_page": per_page, "total": total}
        )
    except Exception as e:
        return error_response(str(e), 500)


@quotation_bp.route("/<quotation_id>", methods=["GET"])
@jwt_required()
def get_quotation(quotation_id):
    """
    GET /api/v1/quotations/<quotation_id>
    Get quotation details with items.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    role = get_current_user_role()
    service = QuotationService(db)

    try:
        quotation = service.get_quotation(quotation_id)
        if role == "vendor":
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor or quotation.vendor_id != vendor.id:
                return error_response("Access denied.", 403)

        schema = QuotationResponseSchema()
        return success_response(schema.dump(quotation), "Quotation retrieved successfully.")
    except Exception as e:
        return error_response(str(e), 404)


@quotation_bp.route("/<quotation_id>", methods=["PUT"])
@jwt_required()
@roles_required("vendor")
def update_quotation(quotation_id):
    """
    PUT /api/v1/quotations/<quotation_id>
    Edit a draft quotation.
    Accessible by: owning vendor only.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    vendor = db.query(Vendor).filter_by(user_id=user_id).first()
    if not vendor:
        return error_response("Vendor profile not found.", 404)

    schema = QuotationUpdateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)

    data = schema.load(request.json)
    service = QuotationService(db)
    try:
        quotation = service.update_quotation(quotation_id, data, vendor.id)
        response_schema = QuotationResponseSchema()
        return success_response(response_schema.dump(quotation), "Quotation updated successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@quotation_bp.route("/<quotation_id>/submit", methods=["POST"])
@jwt_required()
@roles_required("vendor")
def submit_quotation(quotation_id):
    """
    POST /api/v1/quotations/<quotation_id>/submit
    Submit a draft quotation.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    vendor = db.query(Vendor).filter_by(user_id=user_id).first()
    if not vendor:
        return error_response("Vendor profile not found.", 404)

    service = QuotationService(db)
    try:
        quotation = service.submit_quotation(quotation_id, vendor.id)
        response_schema = QuotationResponseSchema()
        return success_response(response_schema.dump(quotation), "Quotation submitted successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@quotation_bp.route("/compare/<rfq_id>", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin")
def compare_quotations(rfq_id):
    """
    GET /api/v1/quotations/compare/<rfq_id>
    Side-by-side comparison of all submitted quotations for an RFQ.
    Accessible by: procurement_officer, manager, admin.
    """
    db = next(get_db())
    service = QuotationService(db)
    try:
        compare_data = service.compare_quotations(rfq_id)
        # Manually serialize since it is a comparison structure with nesting
        from app.schemas.quotation_schema import QuotationCompareSchema
        schema = QuotationCompareSchema()
        return success_response(schema.dump(compare_data), "Comparison retrieved successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@quotation_bp.route("/<quotation_id>/select", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer")
def select_quotation(quotation_id):
    """
    POST /api/v1/quotations/<quotation_id>/select
    Select a quotation as the winner.
    Accessible by: procurement_officer.
    """
    db = next(get_db())
    officer_id = get_current_user_id()
    service = QuotationService(db)
    try:
        quotation = service.select_quotation(quotation_id, officer_id)
        response_schema = QuotationResponseSchema()
        return success_response(response_schema.dump(quotation), "Quotation selected successfully. Approval workflow initiated.")
    except Exception as e:
        return error_response(str(e), 400)

