"""
VendorBridge ERP – Security Utilities
=======================================
JWT helpers, role-based access decorators, and request context utilities.
"""

from functools import wraps

from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt, verify_jwt_in_request


def roles_required(*allowed_roles):
    """
    Decorator that restricts endpoint access to users with specific roles.

    Usage:
        @roles_required('admin', 'procurement_officer')
        def my_endpoint():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in allowed_roles:
                return jsonify({
                    "success": False,
                    "message": f"Access denied. Required roles: {', '.join(allowed_roles)}"
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id() -> str:
    """Return the current user's UUID from the JWT token."""
    return get_jwt_identity()


def get_current_user_role() -> str:
    """Extract the user's role from JWT additional_claims."""
    claims = get_jwt()
    return claims.get("role")


def get_client_ip() -> str:
    """
    Extract the client IP address from the request,
    accounting for reverse proxies (X-Forwarded-For).
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr
