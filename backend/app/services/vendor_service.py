"""
VendorBridge ERP – Vendor Service
==================================
Business logic for vendor registration, approval, search, and ratings.
Sits between vendor_routes and vendor repositories. Never touches the HTTP layer.
"""

import uuid

from sqlalchemy.orm import Session

from app.repositories.vendor_repo import (
    VendorRepository,
    VendorCategoryRepository,
    VendorRatingRepository,
)
from app.repositories.user_repo import UserRepository
from app.models.vendor import Vendor, VendorCategory, VendorRating
from app.models.user import User
from app.services.notification_service import NotificationService
from app.exceptions.handlers import (
    NotFoundError,
    ConflictError,
    BusinessLogicError,
    ForbiddenError,
)


class VendorService:
    """
    Handles all vendor-related business logic.
    Called by vendor_routes. Never touches the HTTP layer.
    """

    def __init__(self, db: Session):
        self.db = db
        self.vendor_repo = VendorRepository(db)
        self.category_repo = VendorCategoryRepository(db)
        self.rating_repo = VendorRatingRepository(db)
        self.user_repo = UserRepository(db)
        self.notification_svc = NotificationService(db)

    # ── Vendor Registration ───────────────────────────────────────

    def register_vendor(self, data: dict) -> dict:
        """
        Register a new vendor by creating a User (role='vendor') and a
        linked Vendor profile atomically.

        The API accepts 'name' (mapped to User.full_name + Vendor.company_name),
        'email', 'phone', and optional 'password'.

        Args:
            data: Validated dict from VendorCreateSchema.

        Returns:
            dict with 'user' and 'vendor' keys.

        Raises:
            ConflictError: If email is already registered.
        """
        email = data["email"].lower().strip()

        # Check for duplicate email
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ConflictError("A user with this email already exists.")

        # Resolve company_name: prefer explicit company_name field, else use name
        company_name = data.get("company_name") or data.get("name", "")

        # Create the User account
        raw_password = data.get("password") or "Vendor@123!"
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=data.get("name", company_name),
            role="vendor",
            phone=data.get("phone"),
        )
        user.set_password(raw_password)
        self.user_repo.create(user)

        # Resolve category_id from string category name if provided
        category_id = data.get("category_id")
        if not category_id and data.get("category"):
            cat = self.category_repo.get_by_name(data["category"])
            if cat:
                category_id = cat.id

        # Create the Vendor profile linked to the user
        vendor = Vendor(
            id=str(uuid.uuid4()),
            user_id=user.id,
            company_name=company_name,
            gst_number=data.get("gst_number"),
            pan_number=data.get("pan_number"),
            address=data.get("address"),
            city=data.get("city"),
            state=data.get("state"),
            pincode=data.get("pincode"),
            website=data.get("website"),
            category_id=category_id,
            status="pending",
        )
        self.vendor_repo.create(vendor)

        # Audit log
        self.notification_svc.log_activity(
            actor_id=user.id,
            entity_type="vendor",
            entity_id=vendor.id,
            action="registered",
        )

        return {"user": user, "vendor": vendor}

    # ── CRUD ──────────────────────────────────────────────────────

    def list_vendors(self, page: int = 1, per_page: int = 20, filters: dict = None):
        """
        Paginated listing of vendors with optional filters.

        Supported filters keys: 'search', 'status', 'category_id'.

        Returns:
            Tuple of (vendors_list, total_count).
        """
        filters = filters or {}

        if filters.get("search"):
            return self.vendor_repo.search(filters["search"], page, per_page)

        if filters.get("status"):
            return self.vendor_repo.get_by_status(filters["status"], page, per_page)

        if filters.get("category_id"):
            return self.vendor_repo.get_by_category(filters["category_id"], page, per_page)

        return self.vendor_repo.get_all_paginated(page, per_page)

    def get_vendor(self, vendor_id: str) -> Vendor:
        """
        Fetch a single vendor by ID.

        Raises:
            NotFoundError: If vendor doesn't exist or is soft-deleted.
        """
        vendor = self.vendor_repo.get_by_id(vendor_id)
        if not vendor:
            raise NotFoundError(f"Vendor with ID '{vendor_id}' not found.")
        return vendor

    def get_vendor_by_user_id(self, user_id: str) -> Vendor:
        """
        Fetch the vendor profile linked to a user account.

        Raises:
            NotFoundError: If no vendor profile exists for this user.
        """
        vendor = self.vendor_repo.get_by_user_id(user_id)
        if not vendor:
            raise NotFoundError("No vendor profile found for this user.")
        return vendor

    def update_vendor(self, vendor_id: str, data: dict, requester_id: str, requester_role: str) -> Vendor:
        """
        Update a vendor's profile fields.

        Access rules:
          - The vendor (linked user) can update their own profile.
          - Admin can update any vendor.

        Args:
            data: Validated dict from VendorUpdateSchema.
            requester_id: User ID of the caller.
            requester_role: Role of the caller.

        Returns:
            Updated Vendor instance.

        Raises:
            NotFoundError, ForbiddenError.
        """
        vendor = self.get_vendor(vendor_id)

        # Authorization check
        if requester_role not in ("admin", "manager"):
            if vendor.user_id != requester_id:
                raise ForbiddenError("You can only update your own vendor profile.")

        # Apply fields from validated data (only non-None values)
        vendor_fields = [
            "company_name", "gst_number", "pan_number", "address",
            "city", "state", "pincode", "website", "category_id",
        ]
        for field in vendor_fields:
            if data.get(field) is not None:
                setattr(vendor, field, data[field])

        # Update linked user fields if provided
        if data.get("phone") is not None or data.get("full_name") is not None:
            user = self.user_repo.get_by_id(vendor.user_id)
            if user:
                if data.get("phone") is not None:
                    user.phone = data["phone"]
                if data.get("full_name") is not None:
                    user.full_name = data["full_name"]
                self.user_repo.update(user)

        updated = self.vendor_repo.update(vendor)

        self.notification_svc.log_activity(
            actor_id=requester_id,
            entity_type="vendor",
            entity_id=vendor_id,
            action="updated",
        )
        return updated

    def soft_delete_vendor(self, vendor_id: str, requester_id: str) -> None:
        """
        Soft-delete a vendor by setting deleted_at timestamp.
        Never hard-deletes.

        Raises:
            NotFoundError: If vendor not found.
        """
        vendor = self.get_vendor(vendor_id)
        deleted = self.vendor_repo.soft_delete(vendor_id)
        if not deleted:
            raise NotFoundError(f"Vendor with ID '{vendor_id}' not found.")

        self.notification_svc.log_activity(
            actor_id=requester_id,
            entity_type="vendor",
            entity_id=vendor_id,
            action="deleted",
        )

    # ── Status Transitions ────────────────────────────────────────

    def change_status(self, vendor_id: str, new_status: str, actor_id: str, reason: str = None) -> Vendor:
        """
        Change a vendor's status.

        Valid transitions:
          pending  → active     (approve)
          active   → suspended  (suspend)
          *        → blacklisted

        Raises:
            NotFoundError, BusinessLogicError.
        """
        vendor = self.get_vendor(vendor_id)
        current = vendor.status

        VALID_TRANSITIONS = {
            "pending": ["active", "blacklisted"],
            "active": ["suspended", "blacklisted"],
            "suspended": ["active", "blacklisted"],
            "blacklisted": [],
        }

        allowed = VALID_TRANSITIONS.get(current, [])
        if new_status not in allowed:
            raise BusinessLogicError(
                f"Cannot transition vendor from '{current}' to '{new_status}'."
            )

        vendor.status = new_status

        # If blacklisting, also deactivate the linked user account
        if new_status == "blacklisted":
            self.user_repo.deactivate(vendor.user_id)

        self.vendor_repo.update(vendor)

        # Notify the vendor
        action_map = {
            "active": ("vendor_approved", "Your vendor account has been approved."),
            "suspended": ("vendor_suspended", f"Your vendor account has been suspended.{' Reason: ' + reason if reason else ''}"),
            "blacklisted": ("vendor_blacklisted", "Your vendor account has been permanently blacklisted."),
        }
        notif_type, notif_msg = action_map.get(new_status, ("status_changed", "Your vendor status has changed."))
        try:
            self.notification_svc.create_notification(
                user_id=vendor.user_id,
                type=notif_type,
                title="Account Status Update",
                body=notif_msg,
                entity_type="vendor",
                entity_id=vendor_id,
            )
        except Exception:
            pass  # Non-fatal

        self.notification_svc.log_activity(
            actor_id=actor_id,
            entity_type="vendor",
            entity_id=vendor_id,
            action=f"status_changed_to_{new_status}",
            metadata={"old_status": current, "new_status": new_status, "reason": reason},
        )

        return vendor

    def approve_vendor(self, vendor_id: str, admin_id: str) -> Vendor:
        """Transition vendor status from 'pending' to 'active'."""
        return self.change_status(vendor_id, "active", admin_id)

    def suspend_vendor(self, vendor_id: str, admin_id: str, reason: str = None) -> Vendor:
        """Suspend a vendor (status → 'suspended')."""
        return self.change_status(vendor_id, "suspended", admin_id, reason)

    def blacklist_vendor(self, vendor_id: str, admin_id: str, reason: str = None) -> Vendor:
        """Blacklist a vendor permanently."""
        return self.change_status(vendor_id, "blacklisted", admin_id, reason)

    # ── Ratings ───────────────────────────────────────────────────

    def rate_vendor(self, data: dict, rated_by: str) -> VendorRating:
        """
        Submit a rating for a vendor after PO fulfillment.

        Args:
            data: Validated dict from VendorRatingCreateSchema.
            rated_by: UUID of the user submitting the rating.

        Returns:
            The created VendorRating.

        Raises:
            NotFoundError, ConflictError.
        """
        vendor = self.get_vendor(data["vendor_id"])

        # Prevent duplicate rating for same (vendor, po) pair
        existing = self.rating_repo.get_by_vendor_and_po(data["vendor_id"], data["po_id"])
        if existing:
            raise ConflictError("A rating for this vendor and purchase order already exists.")

        rating = VendorRating(
            id=str(uuid.uuid4()),
            vendor_id=data["vendor_id"],
            po_id=data["po_id"],
            rated_by=rated_by,
            quality_score=data["quality_score"],
            delivery_score=data["delivery_score"],
            pricing_score=data["pricing_score"],
            comments=data.get("comments"),
        )
        rating.calculate_overall()
        self.rating_repo.create(rating)

        # Recalculate vendor's aggregate average rating
        self.vendor_repo.update_avg_rating(data["vendor_id"])

        return rating

    def get_vendor_ratings(self, vendor_id: str, page: int = 1, per_page: int = 20):
        """
        List ratings for a vendor.

        Returns:
            Tuple of (ratings_list, total_count).
        """
        self.get_vendor(vendor_id)  # Validate vendor exists
        return self.rating_repo.get_by_vendor(vendor_id, page, per_page)

    # ── Category Management ───────────────────────────────────────

    def list_categories(self):
        """
        Return hierarchical category tree (root categories with subcategories).
        """
        return self.category_repo.get_root_categories()

    def create_category(self, data: dict) -> VendorCategory:
        """
        Create a new vendor category.

        Raises:
            ConflictError: If a category with the same name already exists.
        """
        existing = self.category_repo.get_by_name(data["name"])
        if existing:
            raise ConflictError(f"Category '{data['name']}' already exists.")

        category = VendorCategory(
            id=str(uuid.uuid4()),
            name=data["name"],
            description=data.get("description"),
            parent_id=data.get("parent_id"),
        )
        return self.category_repo.create(category)
