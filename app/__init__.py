# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # where to redirect for @login_required


def create_app(config_class=Config):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)
    
    @app.context_processor
    def inject_fingerprint_keys():
        return {
            "FP_PUBLIC_KEY": app.config.get("FINGERPRINT_PUBLIC_KEY", ""),
            "FP_REGION": app.config.get("FINGERPRINT_REGION", ""),
        }

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .auth import bp as auth_bp
    from .routes import bp as main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

