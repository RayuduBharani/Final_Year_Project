from .auth import auth_bp
from .jobs import jobs_bp
from .applications import applications_bp
from .analytics import analytics_bp

__all__ = ['auth_bp', 'jobs_bp', 'applications_bp', 'analytics_bp']
