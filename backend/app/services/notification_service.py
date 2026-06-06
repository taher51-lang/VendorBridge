"""
VendorBridge ERP – Notification Service
========================================
Handles in-app notifications and email dispatch coordination.
"""

from sqlalchemy.orm import Session

from app.repositories.base_repo import BaseRepository
from app.models.audit import Notification, ActivityLog
from app.models.user import User


class NotificationService:
    """
    Creates in-app notifications and coordinates email alerts.
    Also handles audit logging.
    """

    def __init__(self, db: Session):
        """
        Initialize with DB session and email_sender utility.

        Dependencies:
            - db session
            - email_sender utility (from app.utils.email_sender)
        """
        # TODO: Store db session and initialize email_sender
        pass

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
        # 1. Instantiate Notification model
        # 2. Persist via db.add() + db.commit()
        # 3. Return notification
        pass

    def mark_read(self, notification_id: str, user_id: str):
        """
        Mark a notification as read.

        Args:
            notification_id: UUID of the notification.
            user_id: Must match the notification's user_id (authorization check).
        """
        # 1. Fetch notification by id
        # 2. Validate notification.user_id == user_id
        # 3. Set read_at = utcnow
        # 4. Persist
        pass

    def mark_all_read(self, user_id: str):
        """
        Mark all unread notifications for a user as read.
        """
        # 1. Query Notification where user_id AND read_at IS NULL
        # 2. Bulk update read_at = utcnow
        # 3. Commit
        pass

    def get_user_notifications(self, user_id: str, page: int = 1, per_page: int = 20,
                                unread_only: bool = False):
        """
        Paginated list of notifications for a user.
        """
        # 1. Build query filtered by user_id
        # 2. If unread_only, add read_at IS NULL filter
        # 3. Order by created_at DESC
        # 4. Paginate
        pass

    def get_unread_count(self, user_id: str) -> int:
        """
        Return the count of unread notifications for a user.
        """
        # 1. Query count of Notification where user_id AND read_at IS NULL
        pass

    # ── Convenience methods for specific notification types ───────

    def notify_vendors_rfq_invite(self, rfq, vendor_ids: list[str]):
        """
        Send 'rfq_invite' notifications to a list of vendors.
        Also queue email notifications.
        """
        # 1. For each vendor_id:
        #    a. Find user_id from vendor profile
        #    b. Create in-app notification
        #    c. Queue email via email_sender
        pass

    def notify_approval_required(self, workflow, approver_id: str):
        """
        Notify an approver that a workflow step is awaiting their action.
        """
        # 1. Create notification with type='approval_required'
        # 2. Queue email to approver
        pass

    def notify_po_issued(self, po):
        """
        Notify vendor that a PO has been issued.
        """
        # 1. Create notification for vendor's user
        # 2. Queue email
        pass

    def send_password_reset(self, user: User, reset_link: str):
        """
        Send a password reset email.
        """
        # 1. Call email_sender.send_password_reset(user.email, reset_link)
        pass

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
        # 1. Instantiate ActivityLog with all fields
        # 2. db.add() + db.commit()
        pass
