"""
VendorBridge ERP – Analytics Routes
=====================================
Dashboard / reporting endpoints for procurement metrics.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, case, extract
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.vendor import Vendor
from app.models.rfq import RFQ, RFQVendorAssignment
from app.models.quotation import Quotation
from app.models.approval import ApprovalWorkflow
from app.models.purchase_order import PurchaseOrder
from app.models.invoice import Invoice
from app.models.audit import ActivityLog, Notification
from app.utils.response_helper import success_response, error_response, paginated_response
from app.utils.security import roles_required, get_current_user_id, get_current_user_role

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    """
    GET /api/v1/analytics/dashboard
    High-level dashboard metrics.
    Returns different data based on user role.
    """
    db = next(get_db())
    role = get_current_user_role()
    user_id = get_current_user_id()

    try:
        if role == "admin":
            data = _admin_dashboard(db)
        elif role == "procurement_officer":
            data = _officer_dashboard(db, user_id)
        elif role == "manager":
            data = _manager_dashboard(db, user_id)
        elif role == "vendor":
            data = _vendor_dashboard(db, user_id)
        else:
            data = {}

        return success_response(data, "Dashboard data retrieved.")
    except Exception as e:
        return error_response(str(e), 500)


def _admin_dashboard(db):
    """Admin dashboard: system-wide overview."""
    total_users = db.query(func.count(User.id)).filter(User.deleted_at.is_(None)).scalar() or 0
    total_vendors = db.query(func.count(Vendor.id)).filter(Vendor.deleted_at.is_(None)).scalar() or 0
    pending_vendors = db.query(func.count(Vendor.id)).filter(
        Vendor.status == "pending", Vendor.deleted_at.is_(None)
    ).scalar() or 0
    active_vendors = db.query(func.count(Vendor.id)).filter(
        Vendor.status == "active", Vendor.deleted_at.is_(None)
    ).scalar() or 0
    active_rfqs = db.query(func.count(RFQ.id)).filter(
        RFQ.status.in_(["draft", "open", "under_review"]),
        RFQ.deleted_at.is_(None),
    ).scalar() or 0
    total_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.deleted_at.is_(None)
    ).scalar() or 0
    total_invoices = db.query(func.count(Invoice.id)).filter(
        Invoice.deleted_at.is_(None)
    ).scalar() or 0
    pending_approvals = db.query(func.count(ApprovalWorkflow.id)).filter(
        ApprovalWorkflow.status == "pending",
        ApprovalWorkflow.deleted_at.is_(None),
    ).scalar() or 0

    # Recent activity
    recent_logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "total_users": total_users,
        "total_vendors": total_vendors,
        "pending_vendors": pending_vendors,
        "active_vendors": active_vendors,
        "active_rfqs": active_rfqs,
        "total_pos": total_pos,
        "total_invoices": total_invoices,
        "pending_approvals": pending_approvals,
        "recent_activity": [log.to_dict() for log in recent_logs],
    }


def _officer_dashboard(db, user_id):
    """Procurement Officer dashboard."""
    active_rfqs = db.query(func.count(RFQ.id)).filter(
        RFQ.status.in_(["draft", "open", "under_review"]),
        RFQ.deleted_at.is_(None),
    ).scalar() or 0

    quotations_received = db.query(func.count(Quotation.id)).filter(
        Quotation.status == "submitted",
        Quotation.deleted_at.is_(None),
    ).scalar() or 0

    pending_approvals = db.query(func.count(ApprovalWorkflow.id)).filter(
        ApprovalWorkflow.status == "pending",
        ApprovalWorkflow.deleted_at.is_(None),
    ).scalar() or 0

    now = datetime.now(timezone.utc)
    invoices_this_month = db.query(func.count(Invoice.id)).filter(
        extract("year", Invoice.created_at) == now.year,
        extract("month", Invoice.created_at) == now.month,
        Invoice.deleted_at.is_(None),
    ).scalar() or 0

    total_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.deleted_at.is_(None),
    ).scalar() or 0

    # Recent RFQs
    recent_rfqs = (
        db.query(RFQ)
        .filter(RFQ.deleted_at.is_(None))
        .order_by(RFQ.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "active_rfqs": active_rfqs,
        "quotations_received": quotations_received,
        "pending_approvals": pending_approvals,
        "invoices_this_month": invoices_this_month,
        "total_pos": total_pos,
        "recent_rfqs": [rfq.to_dict() for rfq in recent_rfqs],
    }


def _manager_dashboard(db, user_id):
    """Manager dashboard."""
    from app.models.approval import ApprovalStep

    pending_approvals = db.query(func.count(ApprovalWorkflow.id)).join(
        ApprovalStep, ApprovalStep.workflow_id == ApprovalWorkflow.id
    ).filter(
        ApprovalStep.approver_id == user_id,
        ApprovalStep.action == "pending",
        ApprovalStep.step_number == ApprovalWorkflow.current_step,
        ApprovalWorkflow.status == "pending",
        ApprovalWorkflow.deleted_at.is_(None),
    ).scalar() or 0

    now = datetime.now(timezone.utc)
    approved_this_month = db.query(func.count(ApprovalWorkflow.id)).filter(
        ApprovalWorkflow.status == "approved",
        extract("year", ApprovalWorkflow.completed_at) == now.year,
        extract("month", ApprovalWorkflow.completed_at) == now.month,
        ApprovalWorkflow.deleted_at.is_(None),
    ).scalar() or 0

    rejected_count = db.query(func.count(ApprovalWorkflow.id)).filter(
        ApprovalWorkflow.status == "rejected",
        ApprovalWorkflow.deleted_at.is_(None),
    ).scalar() or 0

    total_workflows = db.query(func.count(ApprovalWorkflow.id)).filter(
        ApprovalWorkflow.deleted_at.is_(None),
    ).scalar() or 0

    return {
        "pending_approvals": pending_approvals,
        "approved_this_month": approved_this_month,
        "rejected": rejected_count,
        "total_workflows": total_workflows,
    }


def _vendor_dashboard(db, user_id):
    """Vendor dashboard."""
    vendor = db.query(Vendor).filter_by(user_id=user_id).first()
    if not vendor:
        return {"error": "Vendor profile not found"}

    vendor_id = vendor.id

    open_rfqs = db.query(func.count(RFQ.id)).join(
        RFQVendorAssignment, RFQVendorAssignment.rfq_id == RFQ.id
    ).filter(
        RFQVendorAssignment.vendor_id == vendor_id,
        RFQ.status == "open",
        RFQ.deleted_at.is_(None),
    ).scalar() or 0

    submitted_quotes = db.query(func.count(Quotation.id)).filter(
        Quotation.vendor_id == vendor_id,
        Quotation.status == "submitted",
        Quotation.deleted_at.is_(None),
    ).scalar() or 0

    selected_quotes = db.query(func.count(Quotation.id)).filter(
        Quotation.vendor_id == vendor_id,
        Quotation.status == "selected",
        Quotation.deleted_at.is_(None),
    ).scalar() or 0

    active_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.status.in_(["issued", "acknowledged"]),
        PurchaseOrder.deleted_at.is_(None),
    ).scalar() or 0

    total_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.vendor_id == vendor_id,
        PurchaseOrder.deleted_at.is_(None),
    ).scalar() or 0

    # Recent RFQs the vendor is invited to
    recent_rfqs = (
        db.query(RFQ)
        .join(RFQVendorAssignment, RFQVendorAssignment.rfq_id == RFQ.id)
        .filter(
            RFQVendorAssignment.vendor_id == vendor_id,
            RFQ.deleted_at.is_(None),
        )
        .order_by(RFQ.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "open_rfqs": open_rfqs,
        "submitted_quotes": submitted_quotes,
        "selected_quotes": selected_quotes,
        "active_pos": active_pos,
        "total_pos": total_pos,
        "recent_rfqs": [rfq.to_dict() for rfq in recent_rfqs],
    }


@analytics_bp.route("/activity-logs", methods=["GET"])
@jwt_required()
def activity_logs():
    """
    GET /api/v1/analytics/activity-logs?page=1&entity_type=rfq
    Paginated activity log timeline.
    """
    db = next(get_db())
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    entity_type = request.args.get("entity_type")

    try:
        query = db.query(ActivityLog).order_by(ActivityLog.created_at.desc())

        if entity_type:
            query = query.filter(ActivityLog.entity_type == entity_type)

        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()

        return paginated_response(
            [log.to_dict() for log in results],
            total, page, per_page,
            f"Found {total} activity log(s)."
        )
    except Exception as e:
        return error_response(str(e), 500)


@analytics_bp.route("/spend-by-category", methods=["GET"])
@jwt_required()
@roles_required("admin", "manager", "procurement_officer")
def spend_by_category():
    """
    GET /api/v1/analytics/spend-by-category
    Procurement spend broken down by vendor category.
    """
    db = next(get_db())
    from app.models.vendor import VendorCategory

    try:
        results = (
            db.query(
                VendorCategory.name,
                func.coalesce(func.sum(PurchaseOrder.total_amount), 0).label("total_spend"),
                func.count(PurchaseOrder.id).label("po_count"),
            )
            .join(Vendor, Vendor.category_id == VendorCategory.id)
            .join(PurchaseOrder, PurchaseOrder.vendor_id == Vendor.id)
            .filter(
                PurchaseOrder.deleted_at.is_(None),
                PurchaseOrder.status != "cancelled",
            )
            .group_by(VendorCategory.name)
            .order_by(func.sum(PurchaseOrder.total_amount).desc())
            .all()
        )

        data = [
            {
                "category_name": r.name,
                "total_spend": str(r.total_spend),
                "po_count": r.po_count,
            }
            for r in results
        ]
        return success_response(data, "Spend by category retrieved.")
    except Exception as e:
        return error_response(str(e), 500)


@analytics_bp.route("/spend-by-vendor", methods=["GET"])
@jwt_required()
@roles_required("admin", "manager", "procurement_officer")
def spend_by_vendor():
    """
    GET /api/v1/analytics/spend-by-vendor?limit=10
    Top vendors by spend.
    """
    db = next(get_db())
    limit = int(request.args.get("limit", 10))

    try:
        results = (
            db.query(
                Vendor.company_name,
                func.coalesce(func.sum(PurchaseOrder.total_amount), 0).label("total_spend"),
                func.count(PurchaseOrder.id).label("po_count"),
            )
            .join(PurchaseOrder, PurchaseOrder.vendor_id == Vendor.id)
            .filter(
                PurchaseOrder.deleted_at.is_(None),
                PurchaseOrder.status != "cancelled",
            )
            .group_by(Vendor.company_name)
            .order_by(func.sum(PurchaseOrder.total_amount).desc())
            .limit(limit)
            .all()
        )

        data = [
            {
                "vendor_name": r.company_name,
                "total_spend": str(r.total_spend),
                "po_count": r.po_count,
            }
            for r in results
        ]
        return success_response(data, "Top vendors by spend retrieved.")
    except Exception as e:
        return error_response(str(e), 500)


@analytics_bp.route("/vendor-performance", methods=["GET"])
@jwt_required()
@roles_required("admin", "manager", "procurement_officer")
def vendor_performance():
    """
    GET /api/v1/analytics/vendor-performance
    Vendor performance summary.
    """
    db = next(get_db())
    from app.models.vendor import VendorRating

    try:
        results = (
            db.query(
                Vendor.id,
                Vendor.company_name,
                Vendor.avg_rating,
                func.count(PurchaseOrder.id).label("total_pos"),
                func.sum(
                    case((PurchaseOrder.status == "fulfilled", 1), else_=0)
                ).label("fulfilled_pos"),
                func.coalesce(func.sum(PurchaseOrder.total_amount), 0).label("total_spend"),
            )
            .outerjoin(PurchaseOrder, PurchaseOrder.vendor_id == Vendor.id)
            .filter(Vendor.deleted_at.is_(None))
            .group_by(Vendor.id, Vendor.company_name, Vendor.avg_rating)
            .order_by(Vendor.avg_rating.desc())
            .all()
        )

        data = [
            {
                "vendor_id": str(r.id),
                "vendor_name": r.company_name,
                "avg_rating": str(r.avg_rating or 0),
                "total_pos": r.total_pos,
                "fulfilled_pos": r.fulfilled_pos or 0,
                "total_spend": str(r.total_spend),
                "fulfillment_rate": round(
                    (r.fulfilled_pos or 0) / max(r.total_pos, 1) * 100, 1
                ),
            }
            for r in results
        ]
        return success_response(data, "Vendor performance retrieved.")
    except Exception as e:
        return error_response(str(e), 500)


@analytics_bp.route("/monthly-trends", methods=["GET"])
@jwt_required()
@roles_required("admin", "manager", "procurement_officer")
def monthly_trends():
    """
    GET /api/v1/analytics/monthly-trends
    Monthly procurement trends (PO count and spend).
    """
    db = next(get_db())

    try:
        results = (
            db.query(
                extract("year", PurchaseOrder.created_at).label("year"),
                extract("month", PurchaseOrder.created_at).label("month"),
                func.count(PurchaseOrder.id).label("po_count"),
                func.coalesce(func.sum(PurchaseOrder.total_amount), 0).label("total_spend"),
            )
            .filter(
                PurchaseOrder.deleted_at.is_(None),
                PurchaseOrder.status != "cancelled",
            )
            .group_by("year", "month")
            .order_by("year", "month")
            .all()
        )

        data = [
            {
                "year": int(r.year),
                "month": int(r.month),
                "po_count": r.po_count,
                "total_spend": str(r.total_spend),
            }
            for r in results
        ]
        return success_response(data, "Monthly trends retrieved.")
    except Exception as e:
        return error_response(str(e), 500)
