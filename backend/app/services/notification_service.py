"""
VendorBridge ERP – Notification Service
========================================
Handles in-app notifications and email dispatch coordination.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.audit import Notification, ActivityLog
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Creates in-app notifications and coordinates email alerts.
    Also handles audit logging.
    """

    def __init__(self, db: Session):
        """
        Initialize with DB session and email_sender utility.
        """
        self.db = db

    def create_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        body: str = None,
        entity_type: str = None,
        entity_id: str = None,
    ) -> Notification:
        """
        Create an in-app notification for a user.

        Args:
            user_id: Recipient user UUID.
            type: Notification type (e.g. 'rfq_invite', 'approval_required').
            title: Short notification title.
            body: Optional longer description.
            entity_type: Related entity type (e.g. 'rfq', 'invoice').
            entity_id: Related entity UUID.

        Returns:
            The created Notification.
        """
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            entity_type=entity_type,
            entity_id=entity_id,
            is_read=False,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_read(self, notification_id: str, user_id: str) -> bool:
        """
        Mark a notification as read.

        Args:
            notification_id: UUID of the notification.
            user_id: Must match the notification's user_id (authorization check).

        Returns:
            True if updated, False if not found or unauthorized.
        """
        notification = (
            self.db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .first()
        )
        if not notification:
            return False
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def mark_all_read(self, user_id: str) -> None:
        """
        Mark all unread notifications for a user as read.
        """
        now = datetime.now(timezone.utc)
        (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .update({"is_read": True, "read_at": now}, synchronize_session=False)
        )
        self.db.commit()

    def get_user_notifications(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        unread_only: bool = False,
    ):
        """
        Paginated list of notifications for a user.

        Returns:
            Tuple of (notifications_list, total_count).
        """
        query = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.deleted_at.is_(None),
            )
            .order_by(Notification.created_at.desc())
        )
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))

        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_unread_count(self, user_id: str) -> int:
        """
        Return the count of unread notifications for a user.
        """
        return (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.deleted_at.is_(None),
            )
            .count()
        )

    # ── Convenience methods for specific notification types ───────

    def notify_vendors_rfq_invite(self, rfq, vendor_ids: list) -> None:
        """
        Send 'rfq_invite' notifications to a list of vendor IDs.
        Looks up the user_id linked to each vendor profile.

        Args:
            rfq: The RFQ model instance.
            vendor_ids: List of Vendor UUIDs (not User UUIDs).
        """
        from app.models.vendor import Vendor

        for vendor_id in vendor_ids:
            vendor = (
                self.db.query(Vendor)
                .filter(
                    Vendor.id == vendor_id,
                    Vendor.deleted_at.is_(None),
                )
                .first()
            )
            if not vendor or not vendor.user_id:
                continue
            try:
                self.create_notification(
                    user_id=vendor.user_id,
                    type="rfq_invite",
                    title=f"New RFQ: {rfq.title}",
                    body=(
                        f"You have been invited to submit a quotation for RFQ "
                        f"#{rfq.rfq_number}. Deadline: {rfq.deadline.strftime('%Y-%m-%d')}."
                    ),
                    entity_type="rfq",
                    entity_id=rfq.id,
                )
            except Exception:
                # Non-fatal: log and continue so one bad vendor ID doesn't
                # abort the entire publish flow.
                logger.warning(
                    "Failed to create rfq_invite notification for vendor %s", vendor_id,
                    exc_info=True,
                )

    def notify_approval_required(self, workflow, approver_id: str) -> None:
        """
        Notify an approver that a workflow step is awaiting their action.
        """
        self.create_notification(
            user_id=approver_id,
            type="approval_required",
            title="Approval Required",
            body=f"A workflow step is awaiting your approval.",
            entity_type="approval_workflow",
            entity_id=workflow.id,
        )

    def notify_po_issued(self, po) -> None:
        """
        Notify vendor that a PO has been issued.
        """
        if po.vendor and po.vendor.user_id:
            self.create_notification(
                user_id=po.vendor.user_id,
                type="po_issued",
                title=f"Purchase Order Issued: {po.po_number}",
                body="A purchase order has been issued to you. Please review and confirm.",
                entity_type="purchase_order",
                entity_id=po.id,
            )

    def send_password_reset(self, user: User, reset_link: str) -> None:
        """
        Send a password reset email.
        (Email integration deferred — logs to console in dev mode.)
        """
        logger.info("[DEV] Password reset link for %s: %s", user.email, reset_link)

    # ── Audit Logging ─────────────────────────────────────────────

    def log_activity(
        self,
        actor_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        metadata: dict = None,
        ip_address: str = None,
    ) -> None:
        """
        Create an append-only audit log entry.

        Args:
            actor_id: UUID of the acting user (None for system).
            entity_type: e.g. 'rfq', 'invoice', 'vendor'.
            entity_id: UUID of the affected entity.
            action: e.g. 'created', 'approved', 'rejected'.
            metadata: Optional dict with old/new values.
            ip_address: Client IP (from request).
        """
        try:
            log = ActivityLog(
                actor_id=actor_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                metadata_=metadata,
                ip_address=ip_address,
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            # Audit logging is non-fatal — never let it break the request.
            logger.warning("Failed to write activity log for %s/%s", entity_type, entity_id, exc_info=True)
            self.db.rollback()
