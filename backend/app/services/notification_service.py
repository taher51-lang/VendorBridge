"""
VendorBridge ERP – Notification Service
========================================
Handles in-app notifications and email dispatch coordination.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.repositories.base_repo import BaseRepository
from app.models.audit import Notification, ActivityLog
from app.models.user import User
from app.utils.email_sender import send_notification_email, send_password_reset as utils_send_password_reset


class NotificationService:
    """
    Creates in-app notifications and coordinates email alerts.
    Also handles audit logging.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_notification(self, user_id: str, type: str, title: str, body: str = None,
                            entity_type: str = None, entity_id: str = None):
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
            read_at=None
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_read(self, notification_id: str, user_id: str):
        """
        Mark a notification as read.

        Args:
            notification_id: UUID of the notification.
            user_id: Must match the notification's user_id (authorization check).
        """
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.deleted_at.is_(None)
        ).first()
        if not notification:
            return None
        if notification.user_id != user_id:
            from app.exceptions import ForbiddenError
            raise ForbiddenError("You are not authorized to read this notification.")
        
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        self.db.commit()
        return notification

    def mark_all_read(self, user_id: str):
        """
        Mark all unread notifications for a user as read.
        """
        unread = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.deleted_at.is_(None)
        ).all()
        now = datetime.now(timezone.utc)
        for notif in unread:
            notif.is_read = True
            notif.read_at = now
        self.db.commit()

    def get_user_notifications(self, user_id: str, page: int = 1, per_page: int = 20,
                                unread_only: bool = False):
        """
        Paginated list of notifications for a user.
        """
        query = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.deleted_at.is_(None)
        )
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc())
        total = query.count()
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_unread_count(self, user_id: str) -> int:
        """
        Return the count of unread notifications for a user.
        """
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.deleted_at.is_(None)
        ).count()

    # ── Convenience methods for specific notification types ───────

    def notify_vendors_rfq_invite(self, rfq, vendor_ids: list[str]):
        """
        Send 'rfq_invite' notifications to a list of vendors.
        Also queue email notifications.
        """
        from app.models.vendor import Vendor
        for vendor_id in vendor_ids:
            vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
            if vendor and vendor.user_id:
                title = f"Invitation to bid for RFQ: {rfq.title}"
                body = f"You have been invited to submit a quotation for RFQ {rfq.rfq_number}. Deadline is {rfq.deadline}."
                self.create_notification(
                    user_id=vendor.user_id,
                    type="rfq_invite",
                    title=title,
                    body=body,
                    entity_type="rfq",
                    entity_id=rfq.id
                )
                if vendor.user and vendor.user.email:
                    send_notification_email(vendor.user.email, title, body)

    def notify_approval_required(self, workflow, approver_id: str):
        """
        Notify an approver that a workflow step is awaiting their action.
        """
        user = self.db.query(User).filter(User.id == approver_id).first()
        if user:
            title = f"Approval Required for Quotation {workflow.quotation.quote_number}"
            body = f"Quotation {workflow.quotation.quote_number} is selected and requires your approval step."
            self.create_notification(
                user_id=approver_id,
                type="approval_required",
                title=title,
                body=body,
                entity_type="approval_workflow",
                entity_id=workflow.id
            )
            if user.email:
                send_notification_email(user.email, title, body)

    def notify_po_issued(self, po):
        """
        Notify vendor that a PO has been issued.
        """
        from app.models.vendor import Vendor
        vendor = self.db.query(Vendor).filter(Vendor.id == po.vendor_id).first()
        if vendor and vendor.user_id:
            title = f"Purchase Order {po.po_number} Issued"
            body = f"Purchase Order {po.po_number} has been issued to you for RFQ {po.rfq.rfq_number}."
            self.create_notification(
                user_id=vendor.user_id,
                type="po_issued",
                title=title,
                body=body,
                entity_type="purchase_order",
                entity_id=po.id
            )
            if vendor.user and vendor.user.email:
                send_notification_email(vendor.user.email, title, body)

    def send_password_reset(self, user: User, reset_link: str):
        """
        Send a password reset email.
        """
        if user.email:
            utils_send_password_reset(user.email, reset_link)

    # ── Audit Logging ─────────────────────────────────────────────

    def log_activity(self, actor_id: str, entity_type: str, entity_id: str,
                     action: str, metadata: dict = None, ip_address: str = None):
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
        log = ActivityLog(
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            metadata_=metadata,
            ip_address=ip_address
        )
        self.db.add(log)
        self.db.commit()
