"""
VendorBridge ERP – Vendor Routes
==================================
Endpoints for vendor profiles, categories, ratings, and approval status.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.vendor_service import VendorService
from app.schemas.vendor_schema import (
    VendorCreateSchema,
    VendorUpdateSchema,
    VendorCategorySchema,
    VendorRatingCreateSchema,
)
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required

vendor_bp = Blueprint("vendors", __name__)


@vendor_bp.route("/", methods=["GET"])
@jwt_required()
def list_vendors():
    """
    GET /api/v1/vendors?page=1&per_page=20&status=active&search=...
    List vendors with pagination and filtering.
    Accessible by: admin, procurement_officer, manager.
    """
    # 1. Extract query params (page, per_page, status, category_id, search)
    # 2. Call VendorService(db).list_vendors(page, per_page, filters)
    # 3. Return paginated success_response
    pass


@vendor_bp.route("/<vendor_id>", methods=["GET"])
@jwt_required()
def get_vendor(vendor_id):
    """
    GET /api/v1/vendors/<vendor_id>
    Get vendor details.
    """
    # 1. Call VendorService(db).get_vendor(vendor_id)
    # 2. Return vendor.to_dict()
    pass


@vendor_bp.route("/<vendor_id>", methods=["PUT"])
@jwt_required()
def update_vendor(vendor_id):
    """
    PUT /api/v1/vendors/<vendor_id>
    Update vendor profile.
    Accessible by: the vendor themselves or admin.
    """
    # 1. Validate body with VendorUpdateSchema
    # 2. Check authorization (vendor can only update own profile)
    # 3. Call VendorService(db).update_vendor(vendor_id, data)
    # 4. Return updated vendor
    pass


@vendor_bp.route("/<vendor_id>/approve", methods=["POST"])
@jwt_required()
def approve_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/approve
    Approve a pending vendor.
    Accessible by: admin only.
    """
    # 1. Verify caller has admin role (via roles_required or manual check)
    # 2. Call VendorService(db).approve_vendor(vendor_id, admin_id)
    # 3. Return success message
    pass


@vendor_bp.route("/<vendor_id>/suspend", methods=["POST"])
@jwt_required()
def suspend_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/suspend
    Suspend an active vendor.
    Accessible by: admin only.
    """
    # 1. Verify admin role
    # 2. Extract optional 'reason' from body
    # 3. Call VendorService(db).suspend_vendor(vendor_id, admin_id, reason)
    pass


@vendor_bp.route("/<vendor_id>/blacklist", methods=["POST"])
@jwt_required()
def blacklist_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/blacklist
    Permanently blacklist a vendor.
    Accessible by: admin only.
    """
    # 1. Verify admin role
    # 2. Call VendorService(db).blacklist_vendor(vendor_id, admin_id, reason)
    pass


@vendor_bp.route("/<vendor_id>/ratings", methods=["GET"])
@jwt_required()
def list_ratings(vendor_id):
    """
    GET /api/v1/vendors/<vendor_id>/ratings
    List all ratings for a vendor.
    """
    # 1. Extract pagination params
    # 2. Call VendorService(db).get_vendor_ratings(vendor_id, page, per_page)
    pass


@vendor_bp.route("/<vendor_id>/ratings", methods=["POST"])
@jwt_required()
def rate_vendor(vendor_id):
    """
    POST /api/v1/vendors/<vendor_id>/ratings
    Submit a rating for a vendor.
    Accessible by: procurement_officer, manager.
    """
    # 1. Validate body with VendorRatingCreateSchema
    # 2. Call VendorService(db).rate_vendor(data, rated_by=current_user_id)
    pass


# ── Category Endpoints ────────────────────────────────────────────

@vendor_bp.route("/categories", methods=["GET"])
@jwt_required()
def list_categories():
    """
    GET /api/v1/vendors/categories
    List all vendor categories (hierarchical).
    """
    # 1. Call VendorService(db).list_categories()
    pass


@vendor_bp.route("/categories", methods=["POST"])
@jwt_required()
def create_category():
    """
    POST /api/v1/vendors/categories
    Create a vendor category.
    Accessible by: admin.
    """
    # 1. Validate body with VendorCategorySchema
    # 2. Call VendorService(db).create_category(data)
    pass
