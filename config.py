# config.py
import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    # Normalize legacy postgres:// to postgresql:// for SQLAlchemy
    SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional but helpful when using serverless Postgres + pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,     # refresh stale connections
        "pool_recycle": 300,       # seconds before recycling
        "pool_size": 5,            # keep it small on free tiers
        "max_overflow": 2,
    }
