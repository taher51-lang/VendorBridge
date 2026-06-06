"""
VendorBridge ERP – User Schemas
================================
Marshmallow schemas for User serialization and validation.
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class UserCreateSchema(Schema):
    """
    Validates incoming data when registering a new user.

    Fields to define:
        - email: Required, Email format, max 255
        - password: Required, min 8 chars
        - full_name: Required, max 150
        - role: Required, must be one of admin/procurement_officer/manager/vendor
        - phone: Optional, max 20
    """
    # TODO: Define fields with proper validators
    # Example:
    #   email = fields.Email(required=True, validate=validate.Length(max=255))
    #   password = fields.Str(required=True, validate=validate.Length(min=8))
    #   full_name = fields.Str(required=True, validate=validate.Length(max=150))
    #   role = fields.Str(required=True, validate=validate.OneOf([...]))
    #   phone = fields.Str(validate=validate.Length(max=20))
    pass


class UserUpdateSchema(Schema):
    """
    Validates data for updating an existing user profile.

    Fields to define:
        - full_name: Optional, max 150
        - phone: Optional, max 20
        - avatar_url: Optional, URL format
        - is_active: Optional, Boolean (admin only)
    """
    # TODO: Define partial update fields
    pass


class UserResponseSchema(Schema):
    """
    Serializes a User model instance for API responses.
    Excludes sensitive fields like password_hash.

    Fields to define:
        - id, email, full_name, role, phone, avatar_url
        - is_active, email_verified_at, last_login_at
        - created_at, updated_at
    """
    # TODO: Define output fields
    # Example:
    #   id = fields.Str()
    #   email = fields.Email()
    #   full_name = fields.Str()
    #   role = fields.Str()
    #   created_at = fields.DateTime()
    pass


class LoginSchema(Schema):
    """
    Validates login credentials.

    Fields:
        - email: Required
        - password: Required
    """
    # TODO: Define login validation fields
    pass


class PasswordChangeSchema(Schema):
    """
    Validates password change request.

    Fields:
        - current_password: Required
        - new_password: Required, min 8 chars
    """
    # TODO: Define password change fields with cross-field validation
    #   @validates('new_password') — ensure it differs from current
    pass
