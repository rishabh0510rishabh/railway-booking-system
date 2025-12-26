from flask import Flask
from flask_mail import Mail
from models import db
from config import Config
from flask_wtf.csrf import CSRFProtect

mail = Mail()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.booking import booking_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(admin_bp)

    return app