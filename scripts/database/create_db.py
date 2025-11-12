from datamanager.data_model import DataModel

if __name__ == "__main__":
    data_model = DataModel()
    print("Creating database and tables...")
    data_model.create_db_and_tables()
    print("Database created successfully!")
