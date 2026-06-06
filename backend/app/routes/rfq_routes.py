from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.rfq_service import RFQService
from app.schemas.rfq_schema import RFQCreateSchema, RFQUpdateSchema, RFQResponseSchema
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role
from app.models.vendor import Vendor

rfq_bp = Blueprint("rfqs", __name__)


@rfq_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def create_rfq():
    """
    POST /api/v1/rfqs
    Create a new RFQ.
    Accessible by: procurement_officer, admin.
    """
    db = next(get_db())
    officer_id = get_current_user_id()
    
    schema = RFQCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)

    data = schema.load(request.json)
    service = RFQService(db)
    try:
        rfq = service.create_rfq(data, officer_id)
        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "RFQ created successfully.", 201)
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/", methods=["GET"])
@jwt_required()
def list_rfqs():
    """
    GET /api/v1/rfqs?page=1&per_page=20&status=open
    List RFQs with pagination.
    Officers see all; vendors see only their assigned RFQs.
    """
    db = next(get_db())
    service = RFQService(db)
    response_schema = RFQResponseSchema(many=True)

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    status = request.args.get("status")

    role = get_current_user_role()
    user_id = get_current_user_id()

    try:
        if role == "vendor":
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor:
                return error_response("Vendor profile not found.", 404)
            results, total = service.get_vendor_rfqs(vendor.id, page, per_page)
        else:
            filters = {}
            if status:
                filters['status'] = status
            results, total = service.list_rfqs(page, per_page, filters)

        return success_response(
            response_schema.dump(results),
            f"Found {total} RFQ(s).",
            meta={"page": page, "per_page": per_page, "total": total}
        )
    except Exception as e:
        return error_response(str(e), 500)


@rfq_bp.route("/<rfq_id>", methods=["GET"])
@jwt_required()
def get_rfq(rfq_id):
    """
    GET /api/v1/rfqs/<rfq_id>
    Get RFQ details with items and vendor assignments.
    If caller is a vendor, mark the assignment as viewed.
    """
    db = next(get_db())
    user_id = get_current_user_id()
    role = get_current_user_role()
    service = RFQService(db)

    try:
        rfq = service.get_rfq(rfq_id)
        if role == "vendor":
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor:
                return error_response("Vendor profile not found.", 404)
            service.acknowledge_rfq(rfq_id, vendor.id)

        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "RFQ retrieved successfully.")
    except Exception as e:
        return error_response(str(e), 404)


@rfq_bp.route("/<rfq_id>", methods=["PUT"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def update_rfq(rfq_id):
    """
    PUT /api/v1/rfqs/<rfq_id>
    Update a draft RFQ.
    Accessible by: the creating procurement_officer or admin.
    """
    db = next(get_db())
    officer_id = get_current_user_id()
    
    schema = RFQUpdateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)

    data = schema.load(request.json)
    service = RFQService(db)
    try:
        rfq = service.update_rfq(rfq_id, data, officer_id)
        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "RFQ updated successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/<rfq_id>/publish", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def publish_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/publish
    Publish a draft RFQ (status → open).
    """
    db = next(get_db())
    officer_id = get_current_user_id()
    service = RFQService(db)
    try:
        rfq = service.publish_rfq(rfq_id, officer_id)
        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "RFQ published successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/<rfq_id>/close", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def close_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/close
    Close an open RFQ (no more quotations).
    """
    db = next(get_db())
    officer_id = get_current_user_id()
    service = RFQService(db)
    try:
        rfq = service.close_rfq(rfq_id, officer_id)
        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "RFQ closed successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/<rfq_id>/cancel", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def cancel_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/cancel
    Cancel an RFQ.
    """
    db = next(get_db())
    officer_id = get_current_user_id()
    service = RFQService(db)
    try:
        rfq = service.cancel_rfq(rfq_id, officer_id)
        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "RFQ cancelled successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/<rfq_id>/invite-vendors", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def invite_vendors(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/invite-vendors
    Body: {"vendor_ids": ["uuid1", "uuid2"]}
    Invite additional vendors to an RFQ.
    """
    db = next(get_db())
    vendor_ids = request.json.get("vendor_ids", [])
    service = RFQService(db)
    try:
        rfq = service.invite_vendors(rfq_id, vendor_ids)
        response_schema = RFQResponseSchema()
        return success_response(response_schema.dump(rfq), "Vendors invited successfully.")
    except Exception as e:
        return error_response(str(e), 400)

