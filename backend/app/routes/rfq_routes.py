Endpoints for creating, managing, and viewing Requests for Quotation.
All routes require JWT authentication.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.rfq_service import RFQService
from app.schemas.rfq_schema import RFQCreateSchema, RFQUpdateSchema, RFQResponseSchema
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role
from app.models.vendor import Vendor

rfq_bp = Blueprint("rfqs", __name__)

_rfq_create_schema = RFQCreateSchema()
_rfq_update_schema = RFQUpdateSchema()
_vendor_invite_schema = VendorInviteSchema()


def _get_rfq_service() -> RFQService:
    """Instantiate RFQService with a fresh DB session."""
    db = next(get_db())
    return RFQService(db)


def _get_vendor_service() -> VendorService:
    """Instantiate VendorService with a fresh DB session."""
    db = next(get_db())
    return VendorService(db)


# ── RFQ CRUD ──────────────────────────────────────────────────────

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
      - Procurement officers / admins / managers: see all RFQs (with optional status filter).
      - Vendors: see only RFQs they have been invited to.
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
    Get RFQ details with line items and vendor assignments.
    If caller is a vendor, marks their assignment as viewed/acknowledged.
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

    try:
        svc = _get_rfq_service()
        rfq = svc.update_rfq(rfq_id, validated, officer_id)
        return success_response(_rfq_to_dict(rfq), "RFQ updated successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to update RFQ.", 500)


# ── State Transition Endpoints ────────────────────────────────────

@rfq_bp.route("/<rfq_id>/publish", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def publish_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/publish
    Publish a draft RFQ (status: draft → open).
    Validates: deadline in future, at least 1 line item.
    Sends rfq_invite notifications to all assigned vendors.
    Accessible by: procurement_officer (creator), admin.
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
    Close an open RFQ (no more quotations accepted).
    Accessible by: procurement_officer (creator), admin.
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
    Cancel an RFQ (from draft or open status).
    Accessible by: procurement_officer (creator), admin.
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


# ── Vendor Invite Endpoint ────────────────────────────────────────

@rfq_bp.route("/<rfq_id>/invite-vendors", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def invite_vendors(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/invite-vendors
    Invite additional vendors to an RFQ.
    Body: {"vendor_ids": ["uuid1", "uuid2"]}
    Accessible by: procurement_officer (creator), admin.
    """
    role = get_current_user_role()
    if role not in ("procurement_officer", "admin", "manager"):
        return error_response("Access denied.", 403)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    errors = _vendor_invite_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _vendor_invite_schema.load(data)
    officer_id = get_jwt_identity()

    try:
        svc = _get_rfq_service()
        new_assignments = svc.invite_vendors(rfq_id, validated["vendor_ids"], officer_id)
        return success_response(
            {"invited_count": len(new_assignments)},
            f"{len(new_assignments)} vendor(s) invited successfully.",
        )
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to invite vendors.", 500)


# ── Serialisation Helper ──────────────────────────────────────────

def _rfq_to_dict(rfq) -> dict:
    """
    Serialize an RFQ model to a response dict, including nested items
    and vendor_assignments loaded via SQLAlchemy relationships.
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

