import os
from dotenv import load_dotenv
import redis

# Load env variables from .env if present
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or "keyway-super-secret-development-key-12345"
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///keyway.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configurations
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    
    # Determine session type
    SESSION_REDIS_URL = os.environ.get("SESSION_REDIS_URL")
    if SESSION_REDIS_URL:
        SESSION_TYPE = "redis"
        SESSION_REDIS = redis.from_url(SESSION_REDIS_URL)
    else:
        SESSION_TYPE = "filesystem"
        SESSION_FILE_DIR = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 
            "flask_sessions"
        )
    
    # Security parameters
    PBKDF2_ITERATIONS = int(os.environ.get("PBKDF2_ITERATIONS", 480000))
    REVEAL_RATE_LIMIT_PER_MINUTE = int(os.environ.get("REVEAL_RATE_LIMIT_PER_MINUTE", 10))
    
    # Healthcheck limits
    HEALTHCHECK_TIMEOUT_SECONDS = int(os.environ.get("HEALTHCHECK_TIMEOUT_SECONDS", 5))
