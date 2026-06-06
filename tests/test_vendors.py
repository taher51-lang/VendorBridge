"""
VendorBridge ERP – Vendor Tests
=================================
Test suite for vendor management endpoints.
"""

import pytest


class TestVendorListing:
    """Tests for GET /api/v1/vendors"""

    def test_list_vendors(self, client, admin_headers):
        """
        Test listing vendors with pagination.
        """
        # TODO: Implement:
        #   1. Create a few test vendors
        #   2. GET /api/v1/vendors with admin_headers
        #   3. Assert status == 200
        #   4. Assert response contains 'data' list and 'meta' pagination
        pass

    def test_list_vendors_filter_by_status(self, client, admin_headers):
        """
        Test filtering vendors by status.
        """
        # TODO: GET /api/v1/vendors?status=active
        pass

    def test_list_vendors_unauthorized(self, client):
        """
        Test that unauthenticated access returns 401.
        """
        # TODO: GET without auth headers
        pass


class TestVendorDetail:
    """Tests for GET /api/v1/vendors/<id>"""

    def test_get_vendor(self, client, admin_headers):
        """
        Test fetching a vendor by ID.
        """
        # TODO: Create vendor, then GET by ID
        pass

    def test_get_vendor_not_found(self, client, admin_headers):
        """
        Test fetching non-existent vendor returns 404.
        """
        # TODO: GET with random UUID
        pass


class TestVendorApproval:
    """Tests for POST /api/v1/vendors/<id>/approve"""

    def test_approve_vendor(self, client, admin_headers):
        """
        Test admin approving a pending vendor.
        """
        # TODO: Implement:
        #   1. Create a vendor with status='pending'
        #   2. POST /api/v1/vendors/<id>/approve with admin_headers
        #   3. Assert status == 200
        #   4. Assert vendor status is now 'active'
        pass

    def test_approve_vendor_non_admin(self, client, auth_headers):
        """
        Test that non-admin cannot approve vendors.
        """
        # TODO: Assert 403
        pass


class TestVendorRating:
    """Tests for POST /api/v1/vendors/<id>/ratings"""

    def test_rate_vendor(self, client, auth_headers):
        """
        Test submitting a vendor rating.
        """
        # TODO: Implement:
        #   1. Create vendor and fulfilled PO
        #   2. POST rating data
        #   3. Assert overall_score is calculated correctly
        pass

    def test_duplicate_rating(self, client, auth_headers):
        """
        Test that rating the same vendor+PO twice returns 409.
        """
        # TODO: Submit same rating twice
        pass


class TestVendorCategories:
    """Tests for /api/v1/vendors/categories"""

    def test_list_categories(self, client, admin_headers):
        """
        Test listing vendor categories.
        """
        # TODO: Create categories, GET, assert hierarchy
        pass

    def test_create_category(self, client, admin_headers):
        """
        Test creating a new category.
        """
        # TODO: POST category data
        pass
