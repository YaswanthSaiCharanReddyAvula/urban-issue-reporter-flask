"""
Configuration settings for Urban Issue Reporter Flask App
"""
import os

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Database settings
    DATABASE_NAME = os.environ.get('DATABASE_PATH', 'urban_issues.db')
    
    # Email configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'satishchandala834@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'oqqv jvjk byzf kbhn'
    
    # Admin user default credentials
    DEFAULT_ADMIN_NAME = 'Admin User'
    DEFAULT_ADMIN_EMAIL = 'admin@example.com'
    DEFAULT_ADMIN_PASSWORD = 'admin123'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Override sensitive settings for production
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
