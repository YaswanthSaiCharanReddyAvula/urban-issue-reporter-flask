"""
Route initialization - imports all route modules
"""
from . import main
from . import auth  
from . import admin
from . import ml_routes
from . import profile
# from . import priority_routes  # Removed - using ML-based priority instead

def init_routes(app):
    """Initialize all routes with the Flask app"""
    main.init_routes(app)
    auth.init_routes(app)
    admin.init_routes(app)
    ml_routes.init_ml_routes(app)
    profile.init_profile_routes(app)
    # priority_routes.init_priority_routes(app)  # Removed
