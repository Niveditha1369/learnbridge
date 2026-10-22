import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'learnbridge-secret-key-production-change-in-env-9482751')
    
    # Handle Render / Heroku postgres:// -> postgresql:// dialect fix
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = database_url or f"sqlite:///{os.path.join(basedir, 'learnbridge.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session security
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Use secure cookies in production if HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('RENDER') is not None
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
