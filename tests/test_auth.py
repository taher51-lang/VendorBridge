"""
VendorBridge ERP – Auth Tests
===============================
Test suite for authentication endpoints.
"""

import pytest


class TestRegistration:
    """Tests for POST /api/v1/auth/register"""

    def test_register_success(self, client):
        """
        Test successful user registration.
        """
        # TODO: Implement:
        #   1. POST valid user data to /api/v1/auth/register
        #   2. Assert response status == 201
        #   3. Assert response contains user id and email
        #   4. Assert password_hash is NOT in response
        pass

    def test_register_duplicate_email(self, client):
        """
        Test that registering with an existing email returns 409.
        """
        # TODO: Implement:
        #   1. Register a user
        #   2. Try to register again with the same email
        #   3. Assert response status == 409
        pass

    def test_register_invalid_data(self, client):
        """
        Test that invalid data returns 422 with field errors.
        """
        # TODO: Implement:
        #   1. POST with missing required fields
        #   2. Assert response status == 422
        #   3. Assert 'errors' key in response
        pass

    def test_register_weak_password(self, client):
        """
        Test that a password shorter than 8 chars is rejected.
        """
        # TODO: Implement
        pass


class TestLogin:
    """Tests for POST /api/v1/auth/login"""

    def test_login_success(self, client):
        """
        Test successful login returns access and refresh tokens.
        """
        # TODO: Implement:
        #   1. Register a user
        #   2. POST credentials to /api/v1/auth/login
        #   3. Assert response status == 200
        #   4. Assert 'access_token' and 'refresh_token' in response
        pass

    def test_login_wrong_password(self, client):
        """
        Test login with incorrect password returns 401.
        """
        # TODO: Implement
        pass

    def test_login_nonexistent_email(self, client):
        """
        Test login with unknown email returns 401.
        """
        # TODO: Implement
        pass

    def test_login_inactive_user(self, client):
        """
        Test login with deactivated account returns 403.
        """
        # TODO: Implement
        pass


class TestTokenRefresh:
    """Tests for POST /api/v1/auth/refresh"""

    def test_refresh_success(self, client, auth_headers):
        """
        Test exchanging a refresh token for a new access token.
        """
        # TODO: Implement
        pass

    def test_refresh_with_access_token_fails(self, client, auth_headers):
        """
        Test that using an access token (not refresh) returns 422.
        """
        # TODO: Implement
        pass


class TestProfile:
    """Tests for GET/PUT /api/v1/auth/profile"""

    def test_get_profile(self, client, auth_headers):
        """
        Test fetching the authenticated user's profile.
        """
        # TODO: Implement:
        #   1. GET /api/v1/auth/profile with auth_headers
        #   2. Assert status == 200
        #   3. Assert response contains user fields
        pass

    def test_get_profile_unauthorized(self, client):
        """
        Test accessing profile without auth returns 401.
        """
        # TODO: Implement
        pass
