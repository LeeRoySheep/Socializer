from sqlalchemy import create_engine, text

def apply_migration():
    try:
        # Connect to the database
        engine = create_engine('sqlite:///data.sqlite.db')
        
        # Check if the column already exists
        with engine.connect() as conn:
            # SQLite doesn't support IF NOT EXISTS for ADD COLUMN, so we'll check first
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'is_active' not in columns:
                # Add the is_active column
                conn.execute(text('ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL'))
                conn.commit()
                print("Successfully added 'is_active' column to 'users' table")
            else:
                print("'is_active' column already exists in 'users' table")
                
    except Exception as e:
        print(f"Error applying migration: {e}")
        raise

if __name__ == "__main__":
    apply_migration()
