"""
VendorBridge ERP – Response Helper
====================================
Standardized JSON response formatting for all API endpoints.
"""

from flask import jsonify


def success_response(data=None, message: str = "Success", status_code: int = 200, meta: dict = None):
    """
    Build a standardized success response.

    Args:
        data: The response payload (dict, list, or None).
        message: Human-readable success message.
        status_code: HTTP status code (default 200).
        meta: Optional metadata dict (e.g. pagination info).

    Returns:
        Flask Response with JSON body.

    Response format:
        {
            "success": true,
            "message": "...",
            "data": {...},
            "meta": {...}  // only if provided
        }
    """
    # TODO: Implement:
    #   response = {"success": True, "message": message, "data": data}
    #   if meta:
    #       response["meta"] = meta
    #   return jsonify(response), status_code
    pass


def error_response(message: str = "An error occurred", status_code: int = 400,
                   errors: dict = None):
    """
    Build a standardized error response.

    Args:
        message: Human-readable error message.
        status_code: HTTP status code (4xx or 5xx).
        errors: Optional dict of field-level validation errors.

    Returns:
        Flask Response with JSON body.

    Response format:
        {
            "success": false,
            "message": "...",
            "errors": {...}  // only if provided
        }
    """
    # TODO: Implement:
    #   response = {"success": False, "message": message}
    #   if errors:
    #       response["errors"] = errors
    #   return jsonify(response), status_code
    pass


def paginated_response(items: list, total: int, page: int, per_page: int,
                       message: str = "Success"):
    """
    Build a paginated success response.

    Args:
        items: List of serialized items for the current page.
        total: Total number of items across all pages.
        page: Current page number.
        per_page: Items per page.
        message: Optional message.

    Returns:
        Flask Response with pagination metadata.

    Meta format:
        {
            "page": 1,
            "per_page": 20,
            "total": 100,
            "total_pages": 5,
            "has_next": true,
            "has_prev": false
        }
    """
    # TODO: Implement:
    #   import math
    #   total_pages = math.ceil(total / per_page)
    #   meta = {
    #       "page": page,
    #       "per_page": per_page,
    #       "total": total,
    #       "total_pages": total_pages,
    #       "has_next": page < total_pages,
    #       "has_prev": page > 1,
    #   }
    #   return success_response(data=items, message=message, meta=meta)
    pass
