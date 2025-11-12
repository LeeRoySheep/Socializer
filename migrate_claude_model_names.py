"""
Migrate Claude Model Names in Database
=======================================

Updates all references to old Claude model names in the database
to use the new Claude 4.0 naming convention.
"""

import sys
from pathlib import Path
from sqlalchemy import text

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from datamanager.data_manager import DataManager


def migrate_claude_model_names():
    """Migrate all Claude 3.5 model references to Claude 4.0"""
    
    print("=" * 70)
    print("🔄 MIGRATING CLAUDE MODEL NAMES TO 4.0")
    print("=" * 70)
    
    dm = DataManager("data.sqlite.db")
    
    # Model name mapping
    migrations = {
        "claude-3-5-sonnet-20241022": "claude-sonnet-4-0",
        "claude-3-7-sonnet-20250219": "claude-sonnet-4-0",
        "claude-3-opus-20240229": "claude-3-opus-20240229",  # Keep legacy
        "claude-3-sonnet-20240229": "claude-3-sonnet-20240229",  # Keep legacy
    }
    
    with dm.get_session() as session:
        print("\n📊 Checking database for old Claude model names...")
        
        # 1. Check user_preferences table
        print("\n1️⃣ Checking user_preferences table...")
        try:
            result = session.execute(text("""
                SELECT id, user_id, preference_type, preference_key, preference_value 
                FROM user_preferences 
                WHERE preference_value LIKE '%claude%'
            """))
            
            prefs = result.fetchall()
            print(f"   Found {len(prefs)} Claude-related preferences")
            
            updated_count = 0
            for pref in prefs:
                pref_id, user_id, pref_type, pref_key, pref_value = pref
                
                # Check if value needs migration
                for old_name, new_name in migrations.items():
                    if old_name in pref_value:
                        new_value = pref_value.replace(old_name, new_name)
                        session.execute(text("""
                            UPDATE user_preferences 
                            SET preference_value = :new_value 
                            WHERE id = :pref_id
                        """), {"new_value": new_value, "pref_id": pref_id})
                        print(f"   ✅ Updated preference {pref_id} for user {user_id}")
                        print(f"      From: {pref_value}")
                        print(f"      To:   {new_value}")
                        updated_count += 1
                        break
            
            if updated_count > 0:
                session.commit()
                print(f"\n   ✅ Updated {updated_count} user preferences")
            else:
                print(f"   ℹ️  No user preferences needed updating")
                
        except Exception as e:
            print(f"   ⚠️  Error checking user_preferences: {e}")
            session.rollback()
        
        # 2. Check users.preferences JSON field
        print("\n2️⃣ Checking users.preferences JSON field...")
        try:
            from datamanager.data_model import User
            import json
            
            users = session.query(User).all()
            print(f"   Found {len(users)} users")
            
            updated_count = 0
            for user in users:
                if user.preferences and isinstance(user.preferences, dict):
                    updated = False
                    prefs = user.preferences.copy()
                    
                    # Check all preference values
                    for key, value in prefs.items():
                        if isinstance(value, str):
                            for old_name, new_name in migrations.items():
                                if old_name in value:
                                    prefs[key] = value.replace(old_name, new_name)
                                    updated = True
                    
                    if updated:
                        user.preferences = prefs
                        updated_count += 1
                        print(f"   ✅ Updated preferences for user {user.id} ({user.username})")
            
            if updated_count > 0:
                session.commit()
                print(f"\n   ✅ Updated {updated_count} user preference JSON fields")
            else:
                print(f"   ℹ️  No user preference JSON fields needed updating")
                
        except Exception as e:
            print(f"   ⚠️  Error checking users.preferences: {e}")
            session.rollback()
        
        # 3. Check configuration or settings tables (if they exist)
        print("\n3️⃣ Checking for system configuration...")
        try:
            # Check if there's a settings table
            result = session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name LIKE '%setting%' OR name LIKE '%config%'
            """))
            
            tables = result.fetchall()
            if tables:
                print(f"   Found {len(tables)} configuration tables: {[t[0] for t in tables]}")
                # You can add specific migration logic here if needed
            else:
                print(f"   ℹ️  No configuration tables found")
                
        except Exception as e:
            print(f"   ⚠️  Error checking configuration: {e}")
    
    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE!")
    print("=" * 70)
    print("\n📝 NEXT STEPS:")
    print("   1. Restart your backend server")
    print("   2. Clear browser cache")
    print("   3. Test with frontend")
    print("\n⚠️  If you still see errors, check the frontend code for hardcoded model names")
    print("=" * 70)


if __name__ == "__main__":
    migrate_claude_model_names()
