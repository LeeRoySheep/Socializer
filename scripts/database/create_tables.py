"""Script to initialize the database and create all required tables."""
from datamanager.data_model import DataModel, Base

def create_tables():
    """Create all database tables."""
    print("Initializing database...")
    data_model = DataModel()
    print("Creating database tables...")
    data_model.create_db_and_tables()
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
