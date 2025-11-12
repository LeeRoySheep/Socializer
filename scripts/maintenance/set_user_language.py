"""
Set User Language Preference
=============================

Helper script to set the preferred language for users.

This ensures the AI always responds in the user's preferred language.

Usage:
    # Set language for a specific user
    python set_user_language.py --user_id 2 --language German
    
    # Set language by username
    python set_user_language.py --username human2 --language German
    
    # Interactive mode (prompts for user and language)
    python set_user_language.py

Supported languages: Any language (English, German, Spanish, French, etc.)

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from datamanager.data_manager import DataManager
from app.config import SQLALCHEMY_DATABASE_URL


def set_user_language(user_id: int, language: str, dm: DataManager) -> bool:
    """
    Set the preferred language for a user.
    
    Args:
        user_id: User ID
        language: Language name (e.g., "German", "English", "Spanish")
        dm: DataManager instance
        
    Returns:
        bool: True if successful
    """
    # Get user
    user = dm.get_user(user_id)
    if not user:
        print(f"❌ User {user_id} not found")
        return False
    
    # Set preference
    success = dm.set_user_preference(
        user_id=user_id,
        preference_type="communication",
        preference_key="preferred_language",
        preference_value=language,
        confidence=1.0
    )
    
    if success:
        print(f"✅ Set language for {user.username} (ID: {user_id}) to: {language}")
        return True
    else:
        print(f"❌ Failed to set language for user {user_id}")
        return False


def get_user_language(user_id: int, dm: DataManager) -> str:
    """
    Get the current language preference for a user.
    
    Args:
        user_id: User ID
        dm: DataManager instance
        
    Returns:
        str: Current language preference or "Not set"
    """
    prefs = dm.get_user_preferences(user_id, preference_type="communication")
    return prefs.get("communication.preferred_language", "Not set")


def list_all_user_languages(dm: DataManager):
    """
    List language preferences for all users.
    
    Args:
        dm: DataManager instance
    """
    print("\n" + "="*70)
    print("USER LANGUAGE PREFERENCES")
    print("="*70)
    
    # Get all users
    with dm.get_session() as session:
        from datamanager.data_model import User
        users = session.query(User).all()
    
    print(f"\nTotal users: {len(users)}\n")
    
    for user in users:
        language = get_user_language(user.id, dm)
        status = "✅" if language != "Not set" else "⚠️ "
        print(f"{status} {user.username} (ID: {user.id}): {language}")
    
    print("\n" + "="*70)


def interactive_mode(dm: DataManager):
    """
    Interactive mode to set user language.
    
    Args:
        dm: DataManager instance
    """
    print("\n" + "="*70)
    print("SET USER LANGUAGE - Interactive Mode")
    print("="*70)
    
    # Get user input
    user_input = input("\nEnter user ID or username: ").strip()
    
    # Try to find user
    user = None
    if user_input.isdigit():
        user = dm.get_user(int(user_input))
    else:
        user = dm.get_user_by_username(user_input)
    
    if not user:
        print(f"❌ User '{user_input}' not found")
        return
    
    # Show current language
    current_language = get_user_language(user.id, dm)
    print(f"\nUser: {user.username} (ID: {user.id})")
    print(f"Current language: {current_language}")
    
    # Get new language
    print("\nCommon languages: English, German, Spanish, French, Italian, Portuguese, Chinese, Japanese, etc.")
    new_language = input("Enter new language (or press Enter to cancel): ").strip()
    
    if not new_language:
        print("Cancelled.")
        return
    
    # Confirm
    confirm = input(f"\nSet language to '{new_language}' for {user.username}? (y/n): ").strip().lower()
    
    if confirm == 'y':
        set_user_language(user.id, new_language, dm)
    else:
        print("Cancelled.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set user language preference for AI responses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user_id 2 --language German
  %(prog)s --username human2 --language Spanish
  %(prog)s --list
  %(prog)s (interactive mode)
        """
    )
    
    parser.add_argument('--user_id', type=int, help='User ID')
    parser.add_argument('--username', type=str, help='Username')
    parser.add_argument('--language', type=str, help='Language name (e.g., German, Spanish)')
    parser.add_argument('--list', action='store_true', help='List all user language preferences')
    
    args = parser.parse_args()
    
    # Initialize DataManager
    db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
    dm = DataManager(db_path)
    
    # List mode
    if args.list:
        list_all_user_languages(dm)
        return
    
    # Direct mode (command-line arguments)
    if args.language:
        user_id = None
        
        if args.user_id:
            user_id = args.user_id
        elif args.username:
            user = dm.get_user_by_username(args.username)
            if user:
                user_id = user.id
            else:
                print(f"❌ User '{args.username}' not found")
                return
        else:
            print("❌ Error: Must provide either --user_id or --username with --language")
            return
        
        if user_id:
            set_user_language(user_id, args.language, dm)
            return
    
    # Interactive mode (no arguments or incomplete arguments)
    interactive_mode(dm)


if __name__ == "__main__":
    main()
