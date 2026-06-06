"""
Seeder script to populate local database with minimal RFQ, RFQ item, and user data.
Outputs access tokens and UUIDs so you can immediately test Quotations and Approvals in Postman.
"""

from datetime import datetime, timedelta, timezone
import uuid

from app import create_app
from app.database import SessionLocal
from app.models.user import User
from app.models.vendor import Vendor
from app.models.rfq import RFQ, RFQItem, RFQVendorAssignment
from flask_jwt_extended import create_access_token

def seed():
    app = create_app()
    with app.app_context():
        db = SessionLocal()
        try:
            # 1. Clean up existing tables to keep it fresh
            db.query(RFQVendorAssignment).delete()
            db.query(RFQItem).delete()
            db.query(RFQ).delete()
            db.query(Vendor).delete()
            db.query(User).delete()
            db.commit()

            # 2. Seed Users
            officer = User(
                id=str(uuid.uuid4()),
                email="officer@company.com",
                full_name="Procurement Officer",
                role="procurement_officer",
                is_active=True
            )
            officer.set_password("SecurePassword123")
            db.add(officer)

            vendor_user = User(
                id=str(uuid.uuid4()),
                email="vendor@company.com",
                full_name="Vendor Representative",
                role="vendor",
                is_active=True
            )
            vendor_user.set_password("SecurePassword123")
            db.add(vendor_user)

            manager = User(
                id=str(uuid.uuid4()),
                email="manager@company.com",
                full_name="Procurement Manager",
                role="manager",
                is_active=True
            )
            manager.set_password("SecurePassword123")
            db.add(manager)

            db.commit()

            # 3. Seed Vendor Profile
            vendor_profile = Vendor(
                id=str(uuid.uuid4()),
                user_id=vendor_user.id,
                company_name="Vendor Elite Corp",
                status="active"
            )
            db.add(vendor_profile)
            db.commit()

            # 4. Seed RFQ
            rfq = RFQ(
                id=str(uuid.uuid4()),
                rfq_number="RFQ-2026-0001",
                title="Office Laptops Purchase",
                description="Laptops for development team",
                created_by=officer.id,
                deadline=datetime.utcnow() + timedelta(days=30),
                status="open"
            )
            db.add(rfq)
            db.commit()

            # 5. Seed RFQ Item
            rfq_item = RFQItem(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                item_name="Core i9 Developer Laptop",
                quantity=10,
                unit="pcs",
                sort_order=1
            )
            db.add(rfq_item)
            db.commit()

            # 6. Assign Vendor to RFQ
            assignment = RFQVendorAssignment(
                id=str(uuid.uuid4()),
                rfq_id=rfq.id,
                vendor_id=vendor_profile.id,
                status="acknowledged"
            )
            db.add(assignment)
            db.commit()

            # 7. Generate access tokens
            officer_token = create_access_token(identity=officer.id, additional_claims={"role": officer.role})
            vendor_token = create_access_token(identity=vendor_user.id, additional_claims={"role": vendor_user.role})
            manager_token = create_access_token(identity=manager.id, additional_claims={"role": manager.role})

            print("\n" + "="*50)
            print("DATABASE SEEDED SUCCESSFULLY!")
            print("="*50)
            print(f"RFQ ID:          {rfq.id}")
            print(f"RFQ Item ID:     {rfq_item.id}")
            print(f"Vendor Profile ID: {vendor_profile.id}")
            print(f"Manager User ID:  {manager.id}")
            print("="*50)
            print("BEARER TOKENS FOR YOUR POSTMAN HEADERS:")
            print("="*50)
            print(f"1. VENDOR BEARER TOKEN:\nBearer {vendor_token}\n")
            print(f"2. PROCUREMENT OFFICER BEARER TOKEN:\nBearer {officer_token}\n")
            print(f"3. MANAGER BEARER TOKEN:\nBearer {manager_token}\n")
            print("="*50)

        except Exception as e:
            db.rollback()
            print(f"Seeding failed: {str(e)}")
        finally:
            db.close()

if __name__ == "__main__":
    seed()
