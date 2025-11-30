"""
Database Migration: Add LLM Configuration Fields to Users Table

This migration adds three new columns to the users table:
- llm_provider: Stores the selected LLM provider (lm_studio, ollama, etc.)
- llm_endpoint: Stores the custom endpoint URL (e.g., http://192.168.1.100:1234)
- llm_model: Stores the model name (e.g., llama-3.2)

Usage:
    python migrations/add_llm_config_fields.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from datamanager.data_model import Base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.sqlite.db")


def run_migration():
    """
    Execute the migration to add LLM configuration fields.
    
    This function safely adds the new columns if they don't already exist.
    """
    print("=" * 60)
    print("LLM Configuration Fields Migration")
    print("=" * 60)
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)
    
    try:
        with engine.connect() as conn:
            print("\n[1/4] Checking if llm_provider column exists...")
            
            # Check if columns already exist (SQLite-specific query)
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            needs_migration = not all([
                'llm_provider' in columns,
                'llm_endpoint' in columns,
                'llm_model' in columns
            ])
            
            if not needs_migration:
                print("✅ LLM configuration columns already exist. No migration needed.")
                return True
            
            print("[2/4] Adding llm_provider column...")
            if 'llm_provider' not in columns:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN llm_provider VARCHAR
                """))
                conn.commit()
                print("✅ Added llm_provider column")
            else:
                print("⏭️  llm_provider column already exists")
            
            print("[3/4] Adding llm_endpoint column...")
            if 'llm_endpoint' not in columns:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN llm_endpoint VARCHAR
                """))
                conn.commit()
                print("✅ Added llm_endpoint column")
            else:
                print("⏭️  llm_endpoint column already exists")
            
            print("[4/4] Adding llm_model column...")
            if 'llm_model' not in columns:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN llm_model VARCHAR
                """))
                conn.commit()
                print("✅ Added llm_model column")
            else:
                print("⏭️  llm_model column already exists")
            
            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
            print("\nNew columns added to users table:")
            print("  - llm_provider (VARCHAR, nullable)")
            print("  - llm_endpoint (VARCHAR, nullable)")
            print("  - llm_model (VARCHAR, nullable)")
            print("\nUsers can now configure custom LLM endpoints via the UI.")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nRollback not needed for failed ALTER TABLE in SQLite.")
        return False


def verify_migration():
    """
    Verify that the migration was successful.
    
    Returns:
        bool: True if verification passed, False otherwise
    """
    print("\n" + "=" * 60)
    print("Verifying Migration")
    print("=" * 60)
    
    engine = create_engine(DATABASE_URL, echo=False)
    
    try:
        with engine.connect() as conn:
            # Get table schema
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = {row[1]: row[2] for row in result}  # name: type
            
            required_columns = {
                'llm_provider': 'VARCHAR',
                'llm_endpoint': 'VARCHAR',
                'llm_model': 'VARCHAR'
            }
            
            print("\nChecking for required columns:")
            all_present = True
            
            for col_name, col_type in required_columns.items():
                if col_name in columns:
                    print(f"  ✅ {col_name} ({columns[col_name]})")
                else:
                    print(f"  ❌ {col_name} - MISSING!")
                    all_present = False
            
            if all_present:
                print("\n✅ All columns verified successfully!")
                
                # Check if we can select from the new columns
                result = conn.execute(text("""
                    SELECT llm_provider, llm_endpoint, llm_model 
                    FROM users 
                    LIMIT 1
                """))
                print("✅ Columns are queryable")
                
                return True
            else:
                print("\n❌ Verification failed - some columns are missing")
                return False
                
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting LLM Configuration Migration...\n")
    
    # Run migration
    success = run_migration()
    
    if success:
        # Verify migration
        verify_success = verify_migration()
        
        if verify_success:
            print("\n🎉 Migration and verification completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Migration completed but verification failed")
            sys.exit(1)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)
