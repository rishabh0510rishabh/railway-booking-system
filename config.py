import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-for-local-use')
    MONGODB_SETTINGS = {
        'host': os.environ.get('MONGO_URI', 'mongodb://localhost:27017/railway_db')
    }
    # Mail Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.environ.get('EMAIL_USER')
    MAIL_PASSWORD = os.environ.get('EMAIL_PASS')
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    
    # App Constants
    UPLOAD_FOLDER = 'static/uploads/profiles'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024