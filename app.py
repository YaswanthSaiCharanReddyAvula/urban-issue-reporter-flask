"""
Urban Issue Reporter Flask Application - Modular Version
Main application factory and configuration
"""
from flask import Flask
import os
import json
from config import config
from models import init_db
import routes
import time
import threading
import os as _os

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Add custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Convert JSON string to Python object"""
        try:
            if isinstance(value, str):
                return json.loads(value)
            return value
        except (ValueError, TypeError):
            return {}
    
    # Initialize routes
    routes.init_routes(app)
    
    return app

def main():
    """Main function to run the application (development convenience)"""
    start_time = time.time()
    # Ensure directories (Render can mount a disk at /data). Use env overrides if provided.
    upload_dir = os.environ.get('UPLOAD_FOLDER', 'uploads')
    models_dir = os.environ.get('MODELS_FOLDER', 'models')
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # Initialize database (idempotent)
    init_db()

    # Create application (use development config explicitly here)
    app = create_app('development')

    # Lazy/background ML model load (non-blocking)
    def _warm_models():
        try:
            from ml_models import initialize_ml_models
            print("🤖 (bg) Initializing ML models...")
            initialize_ml_models()
            print("✅ (bg) ML models ready")
        except Exception as e:
            print(f"⚠️  (bg) ML warm-up failed: {e}")
    threading.Thread(target=_warm_models, daemon=True).start()

    print(f"⏱ Startup prep took {time.time() - start_time:.2f}s")
    
    # Print startup information
    print("✅ Database initialized successfully")
    print("🚀 Starting Urban Issue Reporter Flask App...")
    print("🌐 Open: http://localhost:5000")
    print("👤 Admin Login: admin@example.com / admin123")
    print("🤖 ML Automation: Category classification and priority detection enabled")
    print("📧 Email notifications enabled with Gmail")
    print(f"📮 Sending emails from: {app.config['MAIL_USERNAME']}")
    
    # Run the application
    app.run(
        debug=app.config.get('DEBUG', False),
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000)
    )

if __name__ == '__main__':
    main()
