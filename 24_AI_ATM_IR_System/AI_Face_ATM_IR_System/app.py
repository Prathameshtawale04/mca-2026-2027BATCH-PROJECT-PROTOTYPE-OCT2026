"""Main Flask Application Factory for AI Face ATM & Information Retrieval System."""

import os
from pathlib import Path
from flask import Flask, render_template, session, g
from config import Config
from database.db import close_db, init_db
from database.seed_demo_data import seed_all

def create_app(config_class=Config):
    """Application factory initializing extensions, database, and blueprints."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object(config_class)

    # Ensure required data directories exist
    os.makedirs(app.config["BASE_DIR"] / "data", exist_ok=True)
    os.makedirs(app.config["FACE_SAMPLES_DIR"], exist_ok=True)
    os.makedirs(app.config["FACE_MODELS_DIR"], exist_ok=True)
    os.makedirs(app.config["DOCUMENTS_DIR"], exist_ok=True)

    # Teardown database connection after request
    app.teardown_appcontext(close_db)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.main_routes import main_bp
    from routes.face_routes import face_bp
    from routes.atm_routes import atm_bp
    from routes.finance_routes import finance_bp
    from routes.ir_routes import ir_bp
    from routes.search_routes import search_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(face_bp)
    app.register_blueprint(atm_bp)
    app.register_blueprint(finance_bp)
    app.register_blueprint(ir_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)

    # Context processor injecting global session and auth variables into all templates
    @app.context_processor
    def inject_user_context():
        return {
            "current_user": {
                "id": session.get("user_id"),
                "username": session.get("username"),
                "full_name": session.get("full_name"),
                "role": session.get("role"),
                "account_number": session.get("account_number"),
                "balance": session.get("balance", 0.0),
                "is_authenticated": "user_id" in session
            }
        }

    # Custom HTTP error handlers
    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("errors/500.html"), 500

    # Auto-initialize and seed database if not already present
    with app.app_context():
        try:
            init_db()
            seed_all()
        except Exception as e:
            app.logger.error(f"Database initialization error: {e}")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n========================================================")
    print(f" MIRA AI FACE ATM & INFORMATION RETRIEVAL SYSTEM")
    print(f" Running at: http://127.0.0.1:{port}")
    print(f"========================================================\n")
    app.run(host="127.0.0.1", port=port, debug=True)
