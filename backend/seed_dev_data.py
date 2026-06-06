"""
VendorBridge ERP – Dev Data Seeder
====================================
Populates the local database with minimal test data.
Outputs access tokens and UUIDs for immediate Postman testing.

Usage:
    python seed_dev_data.py
"""

from datetime import datetime, timedelta, timezone
import uuid

from app import create_app
from app.database import SessionLocal
from app.models.user import User
from app.models.vendor import Vendor, VendorCategory
from app.models.rfq import RFQ, RFQItem, RFQVendorAssignment
from app.models.quotation import Quotation, QuotationItem
from app.models.approval import ApprovalWorkflow, ApprovalStep
from app.models.purchase_order import PurchaseOrder, POItem
from app.models.invoice import Invoice, InvoiceItem, InvoiceEmail
from app.models.audit import ActivityLog, Notification
from flask_jwt_extended import create_access_token


def seed():
    app = create_app()
    with app.app_context():
        db = SessionLocal()
        try:
            # ── 1. Delete tables in correct FK order (children first) ──
            print("[INFO] Cleaning existing data...")
            db.query(ActivityLog).delete()
            db.query(Notification).delete()
            db.query(InvoiceEmail).delete()
            db.query(InvoiceItem).delete()
            db.query(Invoice).delete()
            db.query(POItem).delete()
            db.query(PurchaseOrder).delete()
            db.query(ApprovalStep).delete()
            db.query(ApprovalWorkflow).delete()
            db.query(QuotationItem).delete()
            db.query(Quotation).delete()
            db.query(RFQVendorAssignment).delete()
            db.query(RFQItem).delete()
            db.query(RFQ).delete()
            from app.models.vendor import VendorRating
            db.query(VendorRating).delete()
            db.query(Vendor).delete()
            db.query(VendorCategory).delete()
            db.query(User).delete()
            db.commit()
            print("[OK] Tables cleaned.")

            # ── 2. Seed Users (4 roles) ────────────────────────────────
            admin = User(
                id=str(uuid.uuid4()),
                email="admin@vendorbridge.com",
                full_name="System Admin",
                role="admin",
                is_active=True,
            )
            admin.set_password("Admin@123")
            db.add(admin)

            officer = User(
                id=str(uuid.uuid4()),
                email="officer@vendorbridge.com",
                full_name="Procurement Officer",
                role="procurement_officer",
                is_active=True,
            )
            officer.set_password("Officer@123")
            db.add(officer)

            manager = User(
                id=str(uuid.uuid4()),
                email="manager@vendorbridge.com",
                full_name="Procurement Manager",
                role="manager",
                is_active=True,
            )
            manager.set_password("Manager@123")
            db.add(manager)

            vendor_user = User(
                id=str(uuid.uuid4()),
                email="vendor@vendorbridge.com",
                full_name="Vendor Representative",
                role="vendor",
                is_active=True,
            )
            vendor_user.set_password("Vendor@123")
            db.add(vendor_user)

            db.commit()
            print("[OK] Users seeded (admin, officer, manager, vendor).")

            # ── 3. Seed Vendor Category ────────────────────────────────
            category = VendorCategory(
                id=str(uuid.uuid4()),
                name="IT Equipment",
                description="Information Technology hardware and peripherals",
            )
            db.add(category)
            db.commit()

            # ── 4. Seed Vendor Profile ─────────────────────────────────
            vendor_profile = Vendor(
                id=str(uuid.uuid4()),
                user_id=vendor_user.id,
                category_id=category.id,
                company_name="TechVendor Elite Corp",
                gst_number="29AABCU9603R1ZM",
                pan_number="AABCU9603R",
                address="42 Silicon Valley Road",
                city="Bangalore",
                state="Karnataka",
                pincode="560001",
                website="https://techvendor.example.com",
                status="active",
            )
            db.add(vendor_profile)
            db.commit()
            print("[OK] Vendor profile seeded.")

            # ── 5. Seed RFQ ───────────────────────────────────────────
            rfq = RFQ(
                id=str(uuid.uuid4()),
                rfq_number="RFQ-2026-0001",
                title="Office Laptops & Accessories",
                description="High-performance laptops and accessories for the development team.",
                created_by=officer.id,
                deadline=datetime.now(timezone.utc) + timedelta(days=30),
                status="open",
            )
            db.add(rfq)
            db.commit()

            # ── 6. Seed RFQ Items (2 line items) ──────────────────────
            rfq_item_1 = RFQItem(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                item_name="Core i9 Developer Laptop",
                description="14-inch, 32GB RAM, 1TB SSD",
                quantity=10,
                unit="pcs",
                sort_order=1,
            )
            rfq_item_2 = RFQItem(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                item_name="USB-C Docking Station",
                description="Dual 4K display, 100W PD charging",
                quantity=10,
                unit="pcs",
                sort_order=2,
            )
            db.add_all([rfq_item_1, rfq_item_2])
            db.commit()

            # ── 7. Assign Vendor to RFQ ────────────────────────────────
            assignment = RFQVendorAssignment(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                vendor_id=vendor_profile.id,
                status="acknowledged",
            )
            db.add(assignment)
            db.commit()
            print("[OK] RFQ seeded with 2 items + vendor assigned.")

            # ── 8. Generate JWT Access Tokens ──────────────────────────
            admin_token = create_access_token(
                identity=admin.id,
                additional_claims={"role": admin.role},
            )
            officer_token = create_access_token(
                identity=officer.id,
                additional_claims={"role": officer.role},
            )
            manager_token = create_access_token(
                identity=manager.id,
                additional_claims={"role": manager.role},
            )
            vendor_token = create_access_token(
                identity=vendor_user.id,
                additional_claims={"role": vendor_user.role},
            )

            # ── 9. Print Summary ───────────────────────────────────────
            print("\n" + "=" * 60)
            print("  DATABASE SEEDED SUCCESSFULLY!")
            print("=" * 60)
            print()
            print("──── UUIDs ────────────────────────────────────────────")
            print(f"  Admin User ID:        {admin.id}")
            print(f"  Officer User ID:      {officer.id}")
            print(f"  Manager User ID:      {manager.id}")
            print(f"  Vendor User ID:       {vendor_user.id}")
            print(f"  Vendor Profile ID:    {vendor_profile.id}")
            print(f"  Vendor Category ID:   {category.id}")
            print(f"  RFQ ID:               {rfq.id}")
            print(f"  RFQ Item 1 ID:        {rfq_item_1.id}")
            print(f"  RFQ Item 2 ID:        {rfq_item_2.id}")
            print()
            print("──── Credentials ──────────────────────────────────────")
            print("  All passwords follow the pattern: Role@123")
            print("  admin@vendorbridge.com     / Admin@123")
            print("  officer@vendorbridge.com   / Officer@123")
            print("  manager@vendorbridge.com   / Manager@123")
            print("  vendor@vendorbridge.com    / Vendor@123")
            print()
            print("──── Bearer Tokens (for Postman) ───────────────────────")
            print(f"\n  1. ADMIN:\n  Bearer {admin_token}\n")
            print(f"  2. PROCUREMENT OFFICER:\n  Bearer {officer_token}\n")
            print(f"  3. MANAGER:\n  Bearer {manager_token}\n")
            print(f"  4. VENDOR:\n  Bearer {vendor_token}\n")
            print("=" * 60)

        except Exception as e:
            db.rollback()
            print(f"\n[ERROR] Seeding failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()


if __name__ == "__main__":
    seed()
