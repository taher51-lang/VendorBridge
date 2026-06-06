"""
VendorBridge ERP – Purchase Order Routes
==========================================
Endpoints for PO management.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.po_service import PurchaseOrderService
from app.schemas.po_schema import POCreateSchema, POUpdateSchema, POResponseSchema
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role

po_bp = Blueprint("purchase_orders", __name__)


def _get_service():
    """Instantiate PurchaseOrderService with a fresh DB session."""
    db = next(get_db())
    return PurchaseOrderService(db), db


@po_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def create_po():
    """
    POST /api/v1/purchase-orders
    Issue a PO from an approved quotation.
    Accessible by: procurement_officer, admin.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    schema = POCreateSchema()
    errors = schema.validate(data)
    if errors:
        return error_response(str(errors), 422)

    validated = schema.load(data)
    user_id = get_current_user_id()

    try:
        service, _ = _get_service()
        po = service.create_po(
            quotation_id=validated["quotation_id"],
            data=validated,
            created_by=user_id,
        )
        response_schema = POResponseSchema()
        return success_response(
            response_schema.dump(po), "Purchase order created successfully.", 201
        )
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 400)


@po_bp.route("/", methods=["GET"])
@jwt_required()
def list_pos():
    """
    GET /api/v1/purchase-orders?page=1&status=issued
    List POs with pagination.
    Vendors see their own; officers/admins see all.
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
            results, total = service.get_vendor_pos(vendor.id, page, per_page)
        else:
            filters = {}
            if status:
                filters["status"] = status
            results, total = service.list_pos(page, per_page, filters)

        schema = POResponseSchema(many=True)
        return paginated_response(
            schema.dump(results), total, page, per_page,
            f"Found {total} purchase order(s)."
        )
    except Exception as e:
        return error_response(str(e), 500)


@po_bp.route("/<po_id>", methods=["GET"])
@jwt_required()
def get_po(po_id):
    """
    GET /api/v1/purchase-orders/<po_id>
    Get PO details.
    """
    role = get_current_user_role()
    user_id = get_current_user_id()

    try:
        service, db = _get_service()
        po = service.get_po(po_id)

        # Vendors can only see their own POs
        if role == "vendor":
            from app.models.vendor import Vendor
            vendor = db.query(Vendor).filter_by(user_id=user_id).first()
            if not vendor or po.vendor_id != vendor.id:
                return error_response("Access denied.", 403)

        schema = POResponseSchema()
        return success_response(schema.dump(po), "Purchase order retrieved.")
    except Exception as e:
        return error_response(str(e), 404)


@po_bp.route("/<po_id>", methods=["PUT"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def update_po(po_id):
    """
    PUT /api/v1/purchase-orders/<po_id>
    Update PO delivery info or terms.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", 400)

    schema = POUpdateSchema()
    errors = schema.validate(data)
    if errors:
        return error_response(str(errors), 422)

    validated = schema.load(data)

    try:
        service, _ = _get_service()
        po = service.update_po(po_id, validated)
        response_schema = POResponseSchema()
        return success_response(response_schema.dump(po), "Purchase order updated.")
    except Exception as e:
        return error_response(str(e), 400)


@po_bp.route("/<po_id>/acknowledge", methods=["POST"])
@jwt_required()
@roles_required("vendor")
def acknowledge_po(po_id):
    """
    POST /api/v1/purchase-orders/<po_id>/acknowledge
    Vendor acknowledges the PO.
    """
    user_id = get_current_user_id()

    try:
        service, db = _get_service()
        from app.models.vendor import Vendor
        vendor = db.query(Vendor).filter_by(user_id=user_id).first()
        if not vendor:
            return error_response("Vendor profile not found.", 404)

        po = service.acknowledge_po(po_id, vendor.id)
        schema = POResponseSchema()
        return success_response(schema.dump(po), "Purchase order acknowledged.")
    except Exception as e:
        return error_response(str(e), 400)


@po_bp.route("/<po_id>/fulfill", methods=["POST"])
@jwt_required()
@roles_required("vendor")
def fulfill_po(po_id):
    """
    POST /api/v1/purchase-orders/<po_id>/fulfill
    Mark a PO as fulfilled.
    Accessible by: vendor.
    """
    user_id = get_current_user_id()

    try:
        service, db = _get_service()
        from app.models.vendor import Vendor
        vendor = db.query(Vendor).filter_by(user_id=user_id).first()
        if not vendor:
            return error_response("Vendor profile not found.", 404)

        po = service.fulfill_po(po_id, vendor.id)
        schema = POResponseSchema()
        return success_response(schema.dump(po), "Purchase order marked as fulfilled.")
    except Exception as e:
        return error_response(str(e), 400)


@po_bp.route("/<po_id>/cancel", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def cancel_po(po_id):
    """
    POST /api/v1/purchase-orders/<po_id>/cancel
    Cancel a PO.
    """
    data = request.get_json(silent=True) or {}
    reason = data.get("reason")
    user_id = get_current_user_id()

    try:
        service, _ = _get_service()
        po = service.cancel_po(po_id, user_id, reason)
        schema = POResponseSchema()
        return success_response(schema.dump(po), "Purchase order cancelled.")
    except Exception as e:
        return error_response(str(e), 400)
