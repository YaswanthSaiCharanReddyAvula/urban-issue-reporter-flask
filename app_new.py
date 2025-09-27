"""
Urban Issue Reporter Flask Application - Modular Version
Main application factory and configuration
"""
from flask import Flask
import os
from config import config
from models import init_db
import routes

def create_app(config_name='default'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize routes
    routes.init_routes(app)
    
    return app

def main():
    """Main function to run the application"""
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    # Initialize database
    init_db()
    
    # Create application
    app = create_app('development')
    
    # Print startup information
    print("🚀 Starting Urban Issue Reporter Flask App...")
    print("🌐 Open: http://localhost:5000")
    print("👤 Admin Login: admin@example.com / admin123")
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
