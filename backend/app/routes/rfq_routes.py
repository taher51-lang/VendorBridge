"""
VendorBridge ERP – RFQ Routes
================================
Endpoints for creating, managing, and viewing Requests for Quotation.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.database import get_db
from app.services.rfq_service import RFQService
from app.schemas.rfq_schema import RFQCreateSchema, RFQUpdateSchema
from app.utils.response_helper import success_response, error_response
from app.utils.security import roles_required

rfq_bp = Blueprint("rfqs", __name__)


@rfq_bp.route("/", methods=["POST"])
@jwt_required()
def create_rfq():
    """
    POST /api/v1/rfqs
    Create a new RFQ.
    Accessible by: procurement_officer.
    """
    # 1. Verify role is procurement_officer
    # 2. Validate body with RFQCreateSchema
    # 3. Call RFQService(db).create_rfq(data, officer_id)
    # 4. Return created RFQ (201)
    pass


@rfq_bp.route("/", methods=["GET"])
@jwt_required()
def list_rfqs():
    """
    GET /api/v1/rfqs?page=1&per_page=20&status=open
    List RFQs with pagination.
    Officers see all; vendors see only their assigned RFQs.
    """
    # 1. Get current user's role
    # 2. If vendor → call service.get_vendor_rfqs(vendor_id, ...)
    # 3. Else → call service.list_rfqs(page, per_page, filters)
    # 4. Return paginated response
    pass


@rfq_bp.route("/<rfq_id>", methods=["GET"])
@jwt_required()
def get_rfq(rfq_id):
    """
    GET /api/v1/rfqs/<rfq_id>
    Get RFQ details with items and vendor assignments.
    If caller is a vendor, mark the assignment as viewed.
    """
    # 1. Call RFQService(db).get_rfq(rfq_id)
    # 2. If caller is vendor → call service.acknowledge_rfq()
    # 3. Return RFQ data
    pass


@rfq_bp.route("/<rfq_id>", methods=["PUT"])
@jwt_required()
def update_rfq(rfq_id):
    """
    PUT /api/v1/rfqs/<rfq_id>
    Update a draft RFQ.
    Accessible by: the creating procurement_officer.
    """
    # 1. Validate body with RFQUpdateSchema
    # 2. Call RFQService(db).update_rfq(rfq_id, data, officer_id)
    # 3. Return updated RFQ
    pass


@rfq_bp.route("/<rfq_id>/publish", methods=["POST"])
@jwt_required()
def publish_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/publish
    Publish a draft RFQ (status → open).
    """
    # 1. Call RFQService(db).publish_rfq(rfq_id, officer_id)
    pass


@rfq_bp.route("/<rfq_id>/close", methods=["POST"])
@jwt_required()
def close_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/close
    Close an open RFQ (no more quotations).
    """
    # 1. Call RFQService(db).close_rfq(rfq_id, officer_id)
    pass


@rfq_bp.route("/<rfq_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_rfq(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/cancel
    Cancel an RFQ.
    """
    # 1. Call RFQService(db).cancel_rfq(rfq_id, officer_id)
    pass


@rfq_bp.route("/<rfq_id>/invite-vendors", methods=["POST"])
@jwt_required()
def invite_vendors(rfq_id):
    """
    POST /api/v1/rfqs/<rfq_id>/invite-vendors
    Body: {"vendor_ids": ["uuid1", "uuid2"]}
    Invite additional vendors to an RFQ.
    """
    # 1. Extract vendor_ids from body
    # 2. Call RFQService(db).invite_vendors(rfq_id, vendor_ids)
    pass
