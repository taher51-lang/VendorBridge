"""
VendorBridge ERP – Response Helper
====================================
Standardized JSON response formatting for all API endpoints.
"""

import math
from flask import jsonify


def success_response(data=None, message: str = "Success", status_code: int = 200, meta: dict = None):
    response = {"success": True, "message": message, "data": data}
    if meta:
        response["meta"] = meta
    return jsonify(response), status_code


def error_response(message: str = "An error occurred", status_code: int = 400, errors: dict = None):
    response = {"success": False, "message": message}
    if errors:
        response["errors"] = errors
    return jsonify(response), status_code


def paginated_response(items: list, total: int, page: int, per_page: int, message: str = "Success"):
    total_pages = math.ceil(total / per_page) if per_page else 1
    meta = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
    return success_response(data=items, message=message, meta=meta)
