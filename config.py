# config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Fingerprint
    FINGERPRINT_PUBLIC_KEY = os.getenv("FINGERPRINT_PUBLIC_KEY", "")
    FINGERPRINT_SECRET_KEY = os.getenv("FINGERPRINT_SECRET_KEY", "")
    FINGERPRINT_REGION = os.getenv("FINGERPRINT_REGION")

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,     # refresh stale connections
        "pool_recycle": 300,       # seconds before recycling
        "pool_size": 5,            # keep it small on free tiers
        "max_overflow": 2,
    }