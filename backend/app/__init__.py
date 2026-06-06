"""
VendorBridge ERP – Application Factory
========================================
Creates and configures the Flask application using the factory pattern.
"""

from flask import Flask
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail

from app.config import config_map

# ── Extension instances (importable by other modules) ─────────────
cors = CORS()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()


def create_app(config_name: str = "development") -> Flask:
    """
    Application factory.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Selects the corresponding config class from config_map.

    Returns:
        A fully configured Flask application instance.
    """
    # 1. Instantiate the Flask app
    app = Flask(__name__)

    # 2. Load configuration
    cfg = config_map.get(config_name, config_map["development"])
    app.config.from_object(cfg)

    # 3. Initialize extensions (order matters for CORS)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # 4. Register blueprints (/api/v1/...)
    from app.routes.auth_routes import auth_bp
    from app.routes.vendor_routes import vendor_bp
    from app.routes.rfq_routes import rfq_bp
    from app.routes.quotation_routes import quotation_bp
    from app.routes.approval_routes import approval_bp
    from app.routes.po_routes import po_bp
    from app.routes.invoice_routes import invoice_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(vendor_bp, url_prefix="/api/v1/vendors")
    app.register_blueprint(rfq_bp, url_prefix="/api/v1/rfqs")
    app.register_blueprint(quotation_bp, url_prefix="/api/v1/quotations")
    app.register_blueprint(approval_bp, url_prefix="/api/v1/approvals")
    app.register_blueprint(po_bp, url_prefix="/api/v1/purchase-orders")
    app.register_blueprint(invoice_bp, url_prefix="/api/v1/invoices")
    app.register_blueprint(analytics_bp, url_prefix="/api/v1/analytics")

    # 5. Register global error handlers
    from app.exceptions.handlers import register_error_handlers
    register_error_handlers(app)

    # 6. Create database tables (dev convenience; use Alembic in production)
    _create_tables(app)

    return app


def _create_tables(app: Flask) -> None:
    """
    Ensure all database tables exist.

    Uses checkfirst=True so existing tables are left untouched.
    In production, prefer Alembic migrations instead.
    """
    with app.app_context():
        from app.database import engine, Base
        # Importing app.models triggers models/__init__.py which
        # registers every model class on Base.metadata.
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("[OK] Tables verified / created successfully")
