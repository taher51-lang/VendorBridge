"""
VendorBridge ERP – Test Configuration
=======================================
pytest fixtures shared across the test suite.
"""

import pytest

from app import create_app
from app.database import Base, get_db


@pytest.fixture(scope="session")
def app():
    """
    Create the Flask app with testing configuration.

    Implementation:
        1. Call create_app('testing')
        2. Yield the app
        3. Teardown: drop all tables
    """
    # TODO: Implement:
    #   app = create_app('testing')
    #   with app.app_context():
    #       yield app
    #       # optional: Base.metadata.drop_all(bind=engine)
    pass


@pytest.fixture(scope="function")
def client(app):
    """
    Provide a Flask test client for each test function.

    Implementation:
        1. Return app.test_client()
    """
    # TODO: return app.test_client()
    pass


@pytest.fixture(scope="function")
def db_session(app):
    """
    Provide a database session that rolls back after each test.

    Implementation:
        1. Get a session from get_db()
        2. Begin a nested transaction (savepoint)
        3. Yield the session
        4. Rollback the transaction
        5. Close the session
    """
    # TODO: Implement transactional test isolation
    pass


@pytest.fixture
def auth_headers(client):
    """
    Register a test user, log in, and return Authorization headers.

    Returns:
        Dict with Authorization header: {"Authorization": "Bearer <token>"}
    """
    # TODO: Implement:
    #   1. POST /api/v1/auth/register with test user data
    #   2. POST /api/v1/auth/login
    #   3. Extract access_token from response
    #   4. Return {"Authorization": f"Bearer {access_token}"}
    pass


@pytest.fixture
def admin_headers(client):
    """
    Auth headers for an admin user.
    """
    # TODO: Similar to auth_headers but with role='admin'
    pass


@pytest.fixture
def vendor_headers(client):
    """
    Auth headers for a vendor user.
    """
    # TODO: Similar to auth_headers but with role='vendor'
    pass
