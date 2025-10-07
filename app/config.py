"""Configuration settings for the application."""
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Security settings
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY environment variable set. Please set it in .env file.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Database settings
import os
from pathlib import Path

# Ensure the database directory exists
db_dir = Path("data")
db_dir.mkdir(exist_ok=True)

# Use a consistent database path
DATABASE_PATH = db_dir / "socializer.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
PROJECT_NAME = os.getenv("PROJECT_NAME", "Socializer")
PROJECT_VERSION = os.getenv("PROJECT_VERSION", "0.1.0")

# CORS settings
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

# WebSocket settings
WEBSOCKET_PATH = "/ws/chat"
WEBSOCKET_RECONNECT_DELAY = 5  # seconds
