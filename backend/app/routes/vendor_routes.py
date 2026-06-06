"""
VendorBridge ERP – Vendor Routes
==================================
Endpoints for vendor profiles, categories, ratings, and approval status.
All routes require JWT authentication. Role guards are applied per endpoint.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.vendor_service import VendorService
from app.schemas.vendor_schema import (
    VendorCreateSchema,
    VendorUpdateSchema,
    VendorStatusUpdateSchema,
    VendorCategorySchema,
    VendorRatingCreateSchema,
)
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import roles_required, get_current_user_role
from app.exceptions.handlers import (
    AppError,
    NotFoundError,
    BusinessLogicError,
    ForbiddenError,
)

vendor_bp = Blueprint("vendors", __name__)

_vendor_create_schema = VendorCreateSchema()
_vendor_update_schema = VendorUpdateSchema()
_vendor_status_schema = VendorStatusUpdateSchema()
_category_schema = VendorCategorySchema()
_rating_create_schema = VendorRatingCreateSchema()


def _get_service() -> VendorService:
    """Instantiate VendorService with a fresh DB session."""
    db = next(get_db())
    return VendorService(db)


# ── Vendor CRUD ───────────────────────────────────────────────────

@vendor_bp.route("/", methods=["POST"])
@jwt_required()
def register_vendor():
    """
    POST /api/v1/vendors/
    Register a new vendor. Creates a User (role='vendor') + Vendor profile.
    Accessible by: admin.

    Required body fields: name, email
    Optional: phone, password, gst_number, category, address, city, state, pincode, website
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can register vendors.", 403)

    errors = _vendor_create_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _vendor_create_schema.load(data)

    try:
        svc = _get_service()
        result = svc.register_vendor(validated)
        vendor = result["vendor"]
        user = result["user"]

        response_data = vendor.to_dict()
        response_data["email"] = user.email
        response_data["phone"] = user.phone
        response_data["full_name"] = user.full_name

        return success_response(response_data, "Vendor registered successfully.", 201)
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception as e:
        return error_response("Vendor registration failed. Please try again.", 500)


@vendor_bp.route("/", methods=["GET"])
@jwt_required()
def list_vendors():
    """
    GET /api/v1/vendors?page=1&per_page=20&status=active&search=...&category_id=...
    List vendors with pagination and filtering.
    Accessible by: admin, procurement_officer, manager.
    """
    role = get_current_user_role()
    if role not in ("admin", "procurement_officer", "manager"):
        return error_response("Access denied.", 403)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    filters = {}

    if request.args.get("search"):
        filters["search"] = request.args.get("search").strip()
    if request.args.get("status"):
        filters["status"] = request.args.get("status")
    if request.args.get("category_id"):
        filters["category_id"] = request.args.get("category_id")

    try:
        svc = _get_service()
        vendors, total = svc.list_vendors(page, per_page, filters)
        items = [v.to_dict() for v in vendors]
        return paginated_response(items, total, page, per_page, "Vendors retrieved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to retrieve vendors.", 500)


@vendor_bp.route("/<vendor_id>", methods=["GET"])
@jwt_required()
def get_vendor(vendor_id):
    """
    GET /api/v1/vendors/<vendor_id>
    Get vendor details. Accessible by any authenticated user.
    """
    try:
        svc = _get_service()
        vendor = svc.get_vendor(vendor_id)
        return success_response(vendor.to_dict(), "Vendor retrieved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to retrieve vendor.", 500)


@vendor_bp.route("/<vendor_id>", methods=["PUT"])
@jwt_required()
def update_vendor(vendor_id):
    """
    PUT /api/v1/vendors/<vendor_id>
    Update vendor profile.
    Accessible by: the vendor themselves or admin/manager.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    errors = _vendor_update_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _vendor_update_schema.load(data)
    requester_id = get_jwt_identity()
    requester_role = get_current_user_role()

    try:
        svc = _get_service()
        vendor = svc.update_vendor(vendor_id, validated, requester_id, requester_role)
        return success_response(vendor.to_dict(), "Vendor updated successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to update vendor.", 500)


@vendor_bp.route("/<vendor_id>", methods=["DELETE"])
@jwt_required()
def delete_vendor(vendor_id):
    """
    DELETE /api/v1/vendors/<vendor_id>
    Soft-delete a vendor (sets deleted_at, never hard-deletes).
    Accessible by: admin only.
    """
    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can delete vendors.", 403)

    requester_id = get_jwt_identity()

    try:
        svc = _get_service()
        svc.soft_delete_vendor(vendor_id, requester_id)
        return success_response(None, "Vendor deleted successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to delete vendor.", 500)


@vendor_bp.route("/<vendor_id>/status", methods=["PATCH"])
@jwt_required()
def change_vendor_status(vendor_id):
    """
    PATCH /api/v1/vendors/<vendor_id>/status
    Change vendor status (active / suspended / blacklisted).
    Body: {"status": "active", "reason": "optional reason"}
    Accessible by: admin only.
    """
    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can change vendor status.", 403)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    errors = _vendor_status_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _vendor_status_schema.load(data)
    actor_id = get_jwt_identity()

    try:
        svc = _get_service()
        vendor = svc.change_status(
            vendor_id,
            validated["status"],
            actor_id,
            validated.get("reason"),
        )
        return success_response(vendor.to_dict(), f"Vendor status updated to '{validated['status']}'.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to update vendor status.", 500)


# ── Existing Approval / Suspend / Blacklist Endpoints ─────────────

@vendor_bp.route("/<vendor_id>/approve", methods=["POST"])
@jwt_required()
def approve_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/approve
    Approve a pending vendor (status: pending → active).
    Accessible by: admin only.
    """
    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can approve vendors.", 403)

    admin_id = get_jwt_identity()

    try:
        svc = _get_service()
        vendor = svc.approve_vendor(vendor_id, admin_id)
        return success_response(vendor.to_dict(), "Vendor approved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to approve vendor.", 500)


@vendor_bp.route("/<vendor_id>/suspend", methods=["POST"])
@jwt_required()
def suspend_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/suspend
    Suspend an active vendor.
    Body (optional): {"reason": "..."}
    Accessible by: admin only.
    """
    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can suspend vendors.", 403)

    admin_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")

    try:
        svc = _get_service()
        vendor = svc.suspend_vendor(vendor_id, admin_id, reason)
        return success_response(vendor.to_dict(), "Vendor suspended successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to suspend vendor.", 500)


@vendor_bp.route("/<vendor_id>/blacklist", methods=["POST"])
@jwt_required()
def blacklist_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/blacklist
    Permanently blacklist a vendor. Also deactivates the linked user account.
    Body (optional): {"reason": "..."}
    Accessible by: admin only.
    """
    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can blacklist vendors.", 403)

    admin_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")

    try:
        svc = _get_service()
        vendor = svc.blacklist_vendor(vendor_id, admin_id, reason)
        return success_response(vendor.to_dict(), "Vendor blacklisted successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to blacklist vendor.", 500)


# ── Rating Endpoints ──────────────────────────────────────────────

@vendor_bp.route("/<vendor_id>/ratings", methods=["GET"])
@jwt_required()
def list_ratings(vendor_id):
    """
    GET /api/v1/vendors/<vendor_id>/ratings?page=1&per_page=20
    List all ratings for a vendor.
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    try:
        svc = _get_service()
        ratings, total = svc.get_vendor_ratings(vendor_id, page, per_page)
        items = [r.to_dict() for r in ratings]
        return paginated_response(items, total, page, per_page, "Ratings retrieved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to retrieve ratings.", 500)


@vendor_bp.route("/<vendor_id>/ratings", methods=["POST"])
@jwt_required()
def rate_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/ratings
    Submit a rating for a vendor.
    Accessible by: procurement_officer, manager.
    """
    role = get_current_user_role()
    if role not in ("procurement_officer", "manager", "admin"):
        return error_response("Access denied. Only officers and managers can rate vendors.", 403)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    # Inject vendor_id from URL into the body for schema validation
    data["vendor_id"] = vendor_id

    errors = _rating_create_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _rating_create_schema.load(data)
    rated_by = get_jwt_identity()

    try:
        svc = _get_service()
        rating = svc.rate_vendor(validated, rated_by)
        return success_response(rating.to_dict(), "Rating submitted successfully.", 201)
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to submit rating.", 500)


# ── Category Endpoints ────────────────────────────────────────────

@vendor_bp.route("/categories", methods=["GET"])
@jwt_required()
def list_categories():
    """
    GET /api/v1/vendors/categories
    List all vendor categories (hierarchical tree).
    """
    try:
        svc = _get_service()
        categories = svc.list_categories()
        items = [c.to_dict() for c in categories]
        return success_response(items, "Categories retrieved successfully.")
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to retrieve categories.", 500)


@vendor_bp.route("/categories", methods=["POST"])
@jwt_required()
def create_category():
    """
    POST /api/v1/vendors/categories
    Create a vendor category.
    Body: {"name": "IT", "description": "...", "parent_id": null}
    Accessible by: admin.
    """
    role = get_current_user_role()
    if role != "admin":
        return error_response("Access denied. Only admins can create categories.", 403)

    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    errors = _category_schema.validate(data)
    if errors:
        return error_response("Validation failed.", 422, errors=errors)

    validated = _category_schema.load(data)

    try:
        svc = _get_service()
        category = svc.create_category(validated)
        return success_response(category.to_dict(), "Category created successfully.", 201)
    except AppError as e:
        return error_response(e.message, e.status_code)
    except Exception:
        return error_response("Failed to create category.", 500)
