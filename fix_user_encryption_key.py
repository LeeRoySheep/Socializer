"""
Fix Missing Encryption Keys for Existing Users
===============================================

This script adds encryption keys to users who don't have them.

This fixes the error:
"User X does not have an encryption key"

Usage:
    # Fix specific user
    python fix_user_encryption_key.py --user_id 27
    
    # Fix all users missing keys
    python fix_user_encryption_key.py --all

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
from pathlib import Path
from cryptography.fernet import Fernet

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from datamanager.data_manager import DataManager
from datamanager.data_model import User
from app.config import SQLALCHEMY_DATABASE_URL


def fix_user_encryption_key(user_id: int, dm: DataManager) -> bool:
    """
    Add encryption key to a specific user.
    
    Args:
        user_id: User ID to fix
        dm: DataManager instance
        
    Returns:
        bool: True if successful
    """
    with dm.get_session() as session:
        try:
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                print(f"❌ User {user_id} not found")
                return False
            
            if user.encryption_key:
                print(f"✅ User {user.username} (ID: {user_id}) already has encryption key")
                return True
            
            # Generate new encryption key
            encryption_key = Fernet.generate_key().decode()
            user.encryption_key = encryption_key
            session.commit()
            
            print(f"✅ Generated encryption key for {user.username} (ID: {user_id})")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error fixing user {user_id}: {e}")
            return False


def fix_all_users(dm: DataManager):
    """
    Fix all users missing encryption keys.
    
    Args:
        dm: DataManager instance
    """
    print("\n" + "="*70)
    print("FIX MISSING ENCRYPTION KEYS")
    print("="*70)
    print()
    
    with dm.get_session() as session:
        # Find users without encryption keys
        users = session.query(User).filter(
            (User.encryption_key == None) | (User.encryption_key == '')
        ).all()
        
        if not users:
            print("✅ All users have encryption keys!")
            return
        
        print(f"Found {len(users)} users without encryption keys:\n")
        
        for user in users:
            print(f"  • {user.username} (ID: {user.id})")
        
        print()
        
        # Fix each user
        fixed = 0
        for user in users:
            try:
                encryption_key = Fernet.generate_key().decode()
                user.encryption_key = encryption_key
                session.commit()
                print(f"✅ Fixed: {user.username} (ID: {user.id})")
                fixed += 1
            except Exception as e:
                session.rollback()
                print(f"❌ Failed: {user.username} (ID: {user.id}) - {e}")
        
        print()
        print("="*70)
        print(f"SUMMARY: Fixed {fixed}/{len(users)} users")
        print("="*70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Fix missing encryption keys for users",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user_id 27          # Fix user ID 27
  %(prog)s --all                 # Fix all users
        """
    )
    
    parser.add_argument('--user_id', type=int, help='User ID to fix')
    parser.add_argument('--all', action='store_true', help='Fix all users missing keys')
    
    args = parser.parse_args()
    
    # Initialize DataManager
    db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
    dm = DataManager(db_path)
    
    if args.all:
        fix_all_users(dm)
    elif args.user_id:
        fix_user_encryption_key(args.user_id, dm)
    else:
        print("Error: Must specify either --user_id or --all")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
