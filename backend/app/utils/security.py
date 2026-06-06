"""
VendorBridge ERP – Security Utilities
=======================================
JWT helpers, role-based access decorators, and request context utilities.
"""

from functools import wraps

from flask import request
from flask_jwt_extended import get_jwt_identity, get_jwt


def roles_required(*allowed_roles):
    """
    Decorator that restricts endpoint access to users with specific roles.

    Usage:
        @roles_required('admin', 'procurement_officer')
        def my_endpoint():
            ...

    Args:
        *allowed_roles: One or more role strings that are permitted.

    Implementation:
        1. Extract the JWT claims from the current request.
        2. Read the 'role' field from additional_claims.
        3. If role not in allowed_roles, abort(403) with a message.
        4. Otherwise, call the wrapped function normally.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # TODO: Implement role check:
            #   claims = get_jwt()
            #   user_role = claims.get('role')
            #   if user_role not in allowed_roles:
            #       return {'error': 'Insufficient permissions'}, 403
            #   return fn(*args, **kwargs)
            pass
        return wrapper
    return decorator


def get_current_user_id() -> str:
    """
    Convenience wrapper around get_jwt_identity().
    Returns the current user's UUID from the JWT token.
    """
    # TODO: return get_jwt_identity()
    pass


def get_current_user_role() -> str:
    """
    Extract the user's role from JWT additional_claims.

    Returns:
        Role string (e.g. 'admin', 'vendor').
    """
    # TODO:
    #   claims = get_jwt()
    #   return claims.get('role')
    pass


def get_client_ip() -> str:
    """
    Extract the client IP address from the request,
    accounting for reverse proxies (X-Forwarded-For).

    Returns:
        IP address string.
    """
    # TODO:
    #   1. Check request.headers.get('X-Forwarded-For')
    #   2. If present, return the first IP in the comma-separated list
    #   3. Otherwise, return request.remote_addr
    pass
