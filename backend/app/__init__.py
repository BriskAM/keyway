from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, session_manager, cors

def create_app(config_class=Config, overrides=None):
    app = Flask(__name__)
    app.config.from_object(config_class)
    if overrides:
        app.config.update(overrides)

    
    # Initialize extensions
    cors.init_app(app, supports_credentials=True, origins=["http://localhost:5173", "http://localhost:8080", "http://127.0.0.1:5173", "http://127.0.0.1:8080"])
    db.init_app(app)
    login_manager.init_app(app)
    session_manager.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"
    
    # User loader for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.secrets import secrets_bp
    from app.api.healthcheck import healthcheck_bp
    from app.api.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(secrets_bp, url_prefix="/api/secrets")
    app.register_blueprint(healthcheck_bp, url_prefix="/api/secrets")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    
    # Create DB tables (for development/SQLite)
    with app.app_context():
        db.create_all()
        
    return app
