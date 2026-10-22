# Routes package initialization
from .auth_routes import auth_bp
from .main_routes import main_bp

__all__ = ["auth_bp", "main_bp"]
