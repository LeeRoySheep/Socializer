"""Script to apply database migrations."""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from alembic.config import Config
from alembic import command

def run_migrations():
    """Run database migrations."""
    # Path to the alembic.ini file
    alembic_cfg = Config("alembic.ini")
    
    # Set the script location to our migrations directory
    alembic_cfg.set_main_option("script_location", "migrations")
    
    # Set the SQLAlchemy URL
    from app.config import SQLALCHEMY_DATABASE_URL
    alembic_cfg.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)
    
    # Run the migrations
    print("Running database migrations...")
    command.upgrade(alembic_cfg, "head")
    print("Migrations completed successfully!")

if __name__ == "__main__":
    run_migrations()
