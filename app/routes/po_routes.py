"""
VendorBridge ERP – Purchase Order Routes
==========================================
REST API endpoints for PO management.
All routes are JWT-protected and role-gated.
Consumed by React frontend via Axios at /api/v1/purchase-orders/...
"""

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required

from app.database import SessionLocal
from app.services.po_service import PurchaseOrderService
from app.schemas.po_schema import POCreateSchema, POUpdateSchema, POResponseSchema
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role

po_bp = Blueprint("purchase_orders", __name__)

# Schema instances (reused across requests for performance)
_create_schema   = POCreateSchema()
_update_schema   = POUpdateSchema()
_response_schema = POResponseSchema()


# ── POST /api/v1/purchase-orders/ ─────────────────────────────────────────────

@po_bp.route("/", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def create_po():
    """
    Issue a Purchase Order from an approved quotation.
    Body: { quotation_id, delivery_address?, expected_delivery?, terms_conditions? }
    """
    body = request.get_json(silent=True) or {}

    errors = _create_schema.validate(body)
    if errors:
        return error_response("Validation failed", 422, errors)

    data    = _create_schema.load(body)
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.create_po(data["quotation_id"], data, user_id)
        return success_response(_response_schema.dump(po), "Purchase Order created successfully", 201)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── GET /api/v1/purchase-orders/ ──────────────────────────────────────────────

@po_bp.route("/", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin")
def list_pos():
    """
    List purchase orders with optional filters.
    Query params: page, per_page, status, vendor_id
    Vendors see only their own POs (handled separately via /vendors endpoint).
    """
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    status   = request.args.get("status")

    filters = {}
    if status:
        filters["status"] = status

    # Officers can filter by their own POs
    role = get_current_user_role()
    if role == "procurement_officer":
        filters["created_by"] = get_current_user_id()

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        pos, total = service.list_pos(page, per_page, filters)
        return paginated_response(
            [_response_schema.dump(po) for po in pos],
            total, page, per_page,
            "Purchase Orders retrieved",
        )
    except Exception as exc:
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── GET /api/v1/purchase-orders/<po_id> ───────────────────────────────────────

@po_bp.route("/<po_id>", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin", "vendor")
def get_po(po_id):
    """Get full PO details including line items."""
    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.get_po(po_id)
        return success_response(_response_schema.dump(po))
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── PUT /api/v1/purchase-orders/<po_id> ───────────────────────────────────────

@po_bp.route("/<po_id>", methods=["PUT"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def update_po(po_id):
    """
    Update delivery info or terms on a PO.
    Only allowed while status='issued'.
    Body: { delivery_address?, expected_delivery?, terms_conditions? }
    """
    body = request.get_json(silent=True) or {}

    errors = _update_schema.validate(body)
    if errors:
        return error_response("Validation failed", 422, errors)

    data = _update_schema.load(body)

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.update_po(po_id, data)
        return success_response(_response_schema.dump(po), "Purchase Order updated")
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/purchase-orders/<po_id>/acknowledge ──────────────────────────

@po_bp.route("/<po_id>/acknowledge", methods=["POST"])
@jwt_required()
@roles_required("vendor")
def acknowledge_po(po_id):
    """
    Vendor acknowledges receipt of the PO.
    Transitions status: issued → acknowledged.
    """
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.acknowledge_po(po_id, user_id)
        return success_response(_response_schema.dump(po), "Purchase Order acknowledged")
    except PermissionError as exc:
        return error_response(str(exc), 403)
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/purchase-orders/<po_id>/fulfill ──────────────────────────────

@po_bp.route("/<po_id>/fulfill", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def fulfill_po(po_id):
    """
    Mark a PO as fulfilled after goods/services delivered.
    Transitions status: acknowledged → fulfilled.
    Note: This is optional — invoice can be created from 'issued' status too.
    """
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.fulfill_po(po_id, user_id)
        return success_response(_response_schema.dump(po), "Purchase Order marked as fulfilled")
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/purchase-orders/<po_id>/cancel ───────────────────────────────

@po_bp.route("/<po_id>/cancel", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def cancel_po(po_id):
    """
    Cancel a PO. Only allowed from 'issued' or 'acknowledged' status.
    Body (optional): { reason: "..." }
    """
    body    = request.get_json(silent=True) or {}
    reason  = body.get("reason")
    user_id = get_current_user_id()

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.cancel_po(po_id, user_id, reason)
        return success_response(_response_schema.dump(po), "Purchase Order cancelled")
    except ValueError as exc:
        return error_response(str(exc), 400)
    except Exception as exc:
        db.rollback()
        return error_response("Internal server error", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── POST /api/v1/purchase-orders/<po_id>/pdf ──────────────────────────────────

@po_bp.route("/<po_id>/pdf", methods=["POST"])
@jwt_required()
@roles_required("procurement_officer", "admin")
def generate_po_pdf(po_id):
    """
    Generate (or regenerate) the PO as a PDF.
    Returns the file path/URL of the generated PDF.
    """
    from app.utils import pdf_generator
    from flask import current_app

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.get_po(po_id)

        # Build PO data dict for the Jinja2 template
        po_data = {
            "po_number":         po.po_number,
            "issued_at":         po.issued_at.date() if po.issued_at else "",
            "expected_delivery": po.expected_delivery,
            "status":            po.status,
            "delivery_address":  po.delivery_address,
            "terms_conditions":  po.terms_conditions,
            "currency":          po.currency,
            "subtotal":          po.subtotal,
            "tax_amount":        po.tax_amount,
            "total_amount":      po.total_amount,
            "vendor_name":       po.vendor.company_name if po.vendor else "",
            "vendor_gst":        po.vendor.gst_number  if po.vendor else "",
            "vendor_address":    po.vendor.address      if po.vendor else "",
            "items": [
                {
                    "item_name":  item.item_name,
                    "quantity":   item.quantity,
                    "unit_price": item.unit_price,
                    "tax_rate":   item.tax_rate,
                    "line_total": item.line_total,
                }
                for item in po.items
            ],
        }

        output_dir = current_app.config.get("PDF_OUTPUT_DIR", "generated_pdfs")
        pdf_path   = pdf_generator.generate_po_pdf(po_data, output_dir)

        return success_response({"pdf_url": pdf_path}, "PO PDF generated successfully")
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response("PDF generation failed", 500, {"detail": str(exc)})
    finally:
        db.close()


# ── GET /api/v1/purchase-orders/<po_id>/pdf/download ──────────────────────────

@po_bp.route("/<po_id>/pdf/download", methods=["GET"])
@jwt_required()
@roles_required("procurement_officer", "manager", "admin", "vendor")
def download_po_pdf(po_id):
    """
    Download the PO as a binary PDF response.
    Auto-generates PDF if it doesn't exist yet.
    Used by the React Download PDF button.
    """
    from app.utils import pdf_generator
    from flask import current_app

    db = SessionLocal()
    try:
        service = PurchaseOrderService(db)
        po = service.get_po(po_id)

        po_data = {
            "po_number":         po.po_number,
            "issued_at":         po.issued_at.date() if po.issued_at else "",
            "expected_delivery": po.expected_delivery,
            "status":            po.status,
            "delivery_address":  po.delivery_address,
            "terms_conditions":  po.terms_conditions,
            "currency":          po.currency,
            "subtotal":          po.subtotal,
            "tax_amount":        po.tax_amount,
            "total_amount":      po.total_amount,
            "vendor_name":       po.vendor.company_name if po.vendor else "",
            "vendor_gst":        po.vendor.gst_number  if po.vendor else "",
            "vendor_address":    po.vendor.address      if po.vendor else "",
            "items": [
                {
                    "item_name":  item.item_name,
                    "quantity":   item.quantity,
                    "unit_price": item.unit_price,
                    "tax_rate":   item.tax_rate,
                    "line_total": item.line_total,
                }
                for item in po.items
            ],
        }

        output_dir = current_app.config.get("PDF_OUTPUT_DIR", "generated_pdfs")
        pdf_path   = pdf_generator.generate_po_pdf(po_data, output_dir)

        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{po.po_number}.pdf",
        )
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception as exc:
        return error_response("PDF generation failed", 500, {"detail": str(exc)})
    finally:
        db.close()
