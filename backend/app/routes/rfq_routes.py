"""
VendorBridge ERP – RFQ Routes
================================
Endpoints for creating, managing, and viewing Requests for Quotation.
All routes require JWT authentication.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.database import get_db
from app.services.rfq_service import RFQService
from app.schemas.rfq_schema import RFQCreateSchema, RFQUpdateSchema, RFQResponseSchema
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role
from app.models.vendor import Vendor

rfq_bp = Blueprint("rfqs", __name__)


def _get_service():
    db = next(get_db())
    return RFQService(db), db


# ── RFQ CRUD ──────────────────────────────────────────────────────

@rfq_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def create_rfq():
    """POST /api/v1/rfqs/ — Create a new RFQ."""
    officer_id = get_current_user_id()
    schema = RFQCreateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)
    data = schema.load(request.json)
    try:
        service, _ = _get_service()
        rfq = service.create_rfq(data, officer_id)
        return success_response(RFQResponseSchema().dump(rfq), "RFQ created successfully.", 201)
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/", methods=["GET"])
@jwt_required()
def list_rfqs():
    """GET /api/v1/rfqs/ — List RFQs. Vendors see only their assigned RFQs."""
    service, db = _get_service()
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
            RFQResponseSchema(many=True).dump(results),
            f"Found {total} RFQ(s).",
            meta={"page": page, "per_page": per_page, "total": total}
        )
    except Exception as e:
        return error_response(str(e), 500)


@rfq_bp.route("/<rfq_id>", methods=["GET"])
@jwt_required()
def get_rfq(rfq_id):
    """GET /api/v1/rfqs/<rfq_id> — Get RFQ details."""
    service, db = _get_service()
    user_id = get_current_user_id()
    role = get_current_user_role()

    try:
        rfq = service.get_rfq(rfq_id)
        if role == "vendor":
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor:
                return error_response("Vendor profile not found.", 404)
            service.acknowledge_rfq(rfq_id, vendor.id)
        return success_response(RFQResponseSchema().dump(rfq), "RFQ retrieved successfully.")
    except Exception as e:
        return error_response(str(e), 404)


@rfq_bp.route("/<rfq_id>", methods=["PUT"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def update_rfq(rfq_id):
    """PUT /api/v1/rfqs/<rfq_id> — Update a draft RFQ."""
    officer_id = get_current_user_id()
    schema = RFQUpdateSchema()
    errors = schema.validate(request.json)
    if errors:
        return error_response(str(errors), 422)
    data = schema.load(request.json)
    try:
        service, _ = _get_service()
        rfq = service.update_rfq(rfq_id, data, officer_id)
        return success_response(RFQResponseSchema().dump(rfq), "RFQ updated successfully.")
    except Exception as e:
        return error_response(str(e), 400)


# ── State Transitions ─────────────────────────────────────────────

@rfq_bp.route("/<rfq_id>/publish", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def publish_rfq(rfq_id):
    """POST /api/v1/rfqs/<rfq_id>/publish — Publish a draft RFQ."""
    officer_id = get_current_user_id()
    try:
        service, _ = _get_service()
        rfq = service.publish_rfq(rfq_id, officer_id)
        return success_response(RFQResponseSchema().dump(rfq), "RFQ published successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/<rfq_id>/close", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def close_rfq(rfq_id):
    """POST /api/v1/rfqs/<rfq_id>/close — Close an open RFQ."""
    officer_id = get_current_user_id()
    try:
        service, _ = _get_service()
        rfq = service.close_rfq(rfq_id, officer_id)
        return success_response(RFQResponseSchema().dump(rfq), "RFQ closed successfully.")
    except Exception as e:
        return error_response(str(e), 400)


@rfq_bp.route("/<rfq_id>/cancel", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def cancel_rfq(rfq_id):
    """POST /api/v1/rfqs/<rfq_id>/cancel — Cancel an RFQ."""
    officer_id = get_current_user_id()
    try:
        service, _ = _get_service()
        rfq = service.cancel_rfq(rfq_id, officer_id)
        return success_response(RFQResponseSchema().dump(rfq), "RFQ cancelled successfully.")
    except Exception as e:
        return error_response(str(e), 400)


# ── Vendor Invite ─────────────────────────────────────────────────

@rfq_bp.route("/<rfq_id>/invite-vendors", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def invite_vendors(rfq_id):
    """POST /api/v1/rfqs/<rfq_id>/invite-vendors — Invite vendors to an RFQ."""
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    vendor_ids = data.get("vendor_ids", [])
    if not vendor_ids:
        return error_response("vendor_ids is required.", 422)

    try:
        service, _ = _get_service()
        rfq = service.invite_vendors(rfq_id, vendor_ids)
        return success_response(
            RFQResponseSchema().dump(rfq),
            f"{len(vendor_ids)} vendor(s) invited successfully."
        )
    except Exception as e:
        return error_response(str(e), 400)