"""Database utilities for the application."""
from sqlalchemy.orm import Session
from datamanager.data_model import DataModel

# Initialize the database
data_model = DataModel()
data_model.create_db_and_tables()

def get_db():
    """Get a database session."""
    db = data_model.SessionLocal()
    try:
        yield db
    finally:
        db.close()
