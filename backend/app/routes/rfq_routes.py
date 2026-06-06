"""
VendorBridge ERP – RFQ Routes
================================
Endpoints for creating, managing, and viewing Requests for Quotation.
All routes require JWT authentication.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.rfq_service import RFQService
from app.services.vendor_service import VendorService
from app.schemas.rfq_schema import RFQCreateSchema, RFQUpdateSchema, VendorInviteSchema
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import get_current_user_role
from app.exceptions.handlers import AppError

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
def create_rfq():
    """
    POST /api/v1/rfqs/
    Create a new RFQ with line items and optional vendor invites.
    Accessible by: procurement_officer.

    Required body: title, deadline, items[]
    Optional: description, notes, attachment_urls, vendor_ids[]
    """
    role = get_current_user_role()
    if role not in ("procurement_officer", "admin", "manager"):
        return error_response(
            "Access denied. Only procurement officers can create RFQs.", 403
        )

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    errors = _rfq_create_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _rfq_create_schema.load(data)
    officer_id = get_jwt_identity()

    try:
        svc = _get_rfq_service()
        rfq = svc.create_rfq(validated, officer_id)
        return success_response(_rfq_to_dict(rfq), "RFQ created successfully.", 201)
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to create RFQ.", 500)


@rfq_bp.route("/", methods=["GET"])
@jwt_required()
def list_rfqs():
    """
    GET /api/v1/rfqs?page=1&per_page=20&status=open
    List RFQs with pagination.
      - Procurement officers / admins / managers: see all RFQs (with optional status filter).
      - Vendors: see only RFQs they have been invited to.
    """
    user_id = get_jwt_identity()
    role = get_current_user_role()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    try:
        rfq_svc = _get_rfq_service()

        if role == "vendor":
            # Find vendor profile for the current user, then get their RFQs
            vendor_svc = _get_vendor_service()
            vendor = vendor_svc.get_vendor_by_user_id(user_id)
            rfqs, total = rfq_svc.get_vendor_rfqs(vendor.id, page, per_page)
        else:
            filters = {}
            if request.args.get("status"):
                filters["status"] = request.args.get("status")
            rfqs, total = rfq_svc.list_rfqs(page, per_page, filters)

        items = [_rfq_to_dict(r) for r in rfqs]
        return paginated_response(items, total, page, per_page, "RFQs retrieved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to retrieve RFQs.", 500)


@rfq_bp.route("/<rfq_id>", methods=["GET"])
@jwt_required()
def get_rfq(rfq_id):
    """
    GET /api/v1/rfqs/<rfq_id>
    Get RFQ details with line items and vendor assignments.
    If caller is a vendor, marks their assignment as viewed/acknowledged.
    """
    user_id = get_jwt_identity()
    role = get_current_user_role()

    try:
        rfq_svc = _get_rfq_service()
        rfq = rfq_svc.get_rfq(rfq_id)

        # If caller is a vendor, acknowledge the RFQ
        if role == "vendor":
            vendor_svc = _get_vendor_service()
            try:
                vendor = vendor_svc.get_vendor_by_user_id(user_id)
                rfq_svc.acknowledge_rfq(rfq_id, vendor.id)
            except AppError:
                pass  # Non-fatal if vendor profile lookup fails

        return success_response(_rfq_to_dict(rfq), "RFQ retrieved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to retrieve RFQ.", 500)


@rfq_bp.route("/<rfq_id>", methods=["PUT"])
@jwt_required()
def update_rfq(rfq_id):
    """
    PUT /api/v1/rfqs/<rfq_id>
    Update a draft RFQ. Only the creating officer can update.
    Accessible by: procurement_officer (creator), admin.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    errors = _rfq_update_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _rfq_update_schema.load(data)
    officer_id = get_jwt_identity()
    role = get_current_user_role()

    if role not in ("procurement_officer", "admin", "manager"):
        return error_response("Access denied.", 403)

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
def publish_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/publish
    Publish a draft RFQ (status: draft → open).
    Validates: deadline in future, at least 1 line item.
    Sends rfq_invite notifications to all assigned vendors.
    Accessible by: procurement_officer (creator), admin.
    """
    role = get_current_user_role()
    if role not in ("procurement_officer", "admin", "manager"):
        return error_response("Access denied.", 403)

    officer_id = get_jwt_identity()

    try:
        svc = _get_rfq_service()
        rfq = svc.publish_rfq(rfq_id, officer_id)
        return success_response(_rfq_to_dict(rfq), "RFQ published successfully. Vendors have been notified.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to publish RFQ.", 500)


@rfq_bp.route("/<rfq_id>/close", methods=["POST"])
@jwt_required()
def close_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/close
    Close an open RFQ (no more quotations accepted).
    Accessible by: procurement_officer (creator), admin.
    """
    role = get_current_user_role()
    if role not in ("procurement_officer", "admin", "manager"):
        return error_response("Access denied.", 403)

    officer_id = get_jwt_identity()

    try:
        svc = _get_rfq_service()
        rfq = svc.close_rfq(rfq_id, officer_id)
        return success_response(_rfq_to_dict(rfq), "RFQ closed successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to close RFQ.", 500)


@rfq_bp.route("/<rfq_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/cancel
    Cancel an RFQ (from draft or open status).
    Accessible by: procurement_officer (creator), admin.
    """
    role = get_current_user_role()
    if role not in ("procurement_officer", "admin", "manager"):
        return error_response("Access denied.", 403)

    officer_id = get_jwt_identity()

    try:
        svc = _get_rfq_service()
        rfq = svc.cancel_rfq(rfq_id, officer_id)
        return success_response(_rfq_to_dict(rfq), "RFQ cancelled successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to cancel RFQ.", 500)


# ── Vendor Invite Endpoint ────────────────────────────────────────

@rfq_bp.route("/<rfq_id>/invite-vendors", methods=["POST"])
@jwt_required()
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
    d = rfq.to_dict()
    d["items"] = [item.to_dict() for item in (rfq.items or [])]
    d["vendor_assignments"] = [
        va.to_dict() for va in (rfq.vendor_assignments or [])
    ]
    return d
