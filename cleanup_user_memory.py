"""
Clean Up User Memory - Remove Internal System Prompts
======================================================

This script removes internal system prompts that were incorrectly saved
to user memory due to a bug in the save_combined_memory method.

Bug: Internal "CONVERSATION MONITORING REQUEST" prompts were being saved
     to encrypted user memory instead of being filtered out.

Fix: Updated save_combined_memory() to filter prompts before saving.

This cleanup script:
1. Loads user's encrypted memory
2. Filters out internal system prompts
3. Saves the cleaned memory back

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from datamanager.data_manager import DataManager
from datamanager.data_model import User
from memory.memory_encryptor import UserMemoryEncryptor
from app.config import SQLALCHEMY_DATABASE_URL


def is_internal_prompt(content: str) -> bool:
    """
    Check if content is an internal system prompt.
    
    Args:
        content: Message content to check
        
    Returns:
        bool: True if internal prompt, False otherwise
    """
    internal_phrases = [
        'CONVERSATION MONITORING REQUEST',
        'INSTRUCTIONS:',
        'Should you intervene',
        'NO_INTERVENTION_NEEDED',
        'You are monitoring this conversation',
        'Analyze if intervention is needed'
    ]
    
    return any(phrase in content for phrase in internal_phrases)


def cleanup_user_memory(user_id: int, dm: DataManager, dry_run: bool = False) -> dict:
    """
    Clean internal prompts from a user's memory.
    
    Args:
        user_id: User ID to clean
        dm: DataManager instance
        dry_run: If True, only count without modifying
        
    Returns:
        dict: Statistics about the cleanup
    """
    # Get user
    user = dm.get_user(user_id)
    if not user:
        return {"error": f"User {user_id} not found"}
    
    # Get encrypted memory
    encrypted_memory = dm.get_user_memory(user_id)
    if not encrypted_memory:
        return {"error": f"No memory found for user {user_id}"}
    
    # Decrypt
    encryptor = UserMemoryEncryptor(user)
    if not encryptor.is_encrypted(encrypted_memory):
        return {"error": "Memory is not encrypted"}
    
    try:
        memory = encryptor.decrypt_memory(encrypted_memory)
    except Exception as e:
        return {"error": f"Failed to decrypt memory: {e}"}
    
    # Count and filter messages
    original_count = len(memory.get("messages", []))
    blocked_count = 0
    
    # Filter all message lists
    filtered_messages = []
    for msg in memory.get("messages", []):
        content = str(msg.get('content', ''))
        if is_internal_prompt(content):
            blocked_count += 1
        else:
            filtered_messages.append(msg)
    
    # Filter general_chat
    filtered_general = []
    for msg in memory.get("general_chat", []):
        content = str(msg.get('content', ''))
        if not is_internal_prompt(content):
            filtered_general.append(msg)
    
    # Filter ai_conversation
    filtered_ai = []
    for msg in memory.get("ai_conversation", []):
        content = str(msg.get('content', ''))
        if not is_internal_prompt(content):
            filtered_ai.append(msg)
    
    # Statistics
    stats = {
        "user_id": user_id,
        "username": user.username,
        "original_messages": original_count,
        "blocked_prompts": blocked_count,
        "clean_messages": len(filtered_messages),
        "dry_run": dry_run
    }
    
    # Save if not dry run
    if not dry_run and blocked_count > 0:
        # Update memory
        memory["messages"] = filtered_messages
        memory["general_chat"] = filtered_general
        memory["ai_conversation"] = filtered_ai
        
        # Update metadata
        memory["metadata"]["message_counts"] = {
            "general": len(filtered_general),
            "ai": len(filtered_ai),
            "total": len(filtered_messages)
        }
        
        # Encrypt and save
        encrypted_clean = encryptor.encrypt_memory(memory)
        success = dm.update_user_memory(user_id, encrypted_clean)
        
        stats["saved"] = success
    
    return stats


def cleanup_all_users(dm: DataManager, dry_run: bool = True):
    """
    Clean internal prompts from all users' memory.
    
    Args:
        dm: DataManager instance
        dry_run: If True, only report without modifying
    """
    print("="*70)
    print("USER MEMORY CLEANUP - Remove Internal System Prompts")
    print("="*70)
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify data)'}")
    print()
    
    # Get all users with memory
    with dm.get_session() as session:
        users = session.query(User).filter(User.conversation_memory.isnot(None)).all()
        user_ids = [u.id for u in users]
    
    print(f"Found {len(user_ids)} users with memory data")
    print()
    
    total_blocked = 0
    cleaned_users = 0
    
    for user_id in user_ids:
        stats = cleanup_user_memory(user_id, dm, dry_run=dry_run)
        
        if "error" in stats:
            print(f"❌ User {user_id}: {stats['error']}")
            continue
        
        if stats["blocked_prompts"] > 0:
            status = "🧹" if not dry_run else "📊"
            print(f"{status} User {stats['username']} (ID: {user_id}):")
            print(f"   Original messages: {stats['original_messages']}")
            print(f"   Internal prompts: {stats['blocked_prompts']}")
            print(f"   Clean messages: {stats['clean_messages']}")
            
            if not dry_run and stats.get("saved"):
                print(f"   ✅ Memory cleaned and saved")
            
            print()
            
            total_blocked += stats["blocked_prompts"]
            cleaned_users += 1
        else:
            print(f"✅ User {stats['username']} (ID: {user_id}): No internal prompts found")
    
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Users checked: {len(user_ids)}")
    print(f"Users with internal prompts: {cleaned_users}")
    print(f"Total internal prompts blocked: {total_blocked}")
    
    if dry_run:
        print()
        print("⚠️  DRY RUN - No changes were made")
        print("💡 Run with --live to actually clean the data")
    else:
        print()
        print("✅ Memory cleanup complete!")


if __name__ == "__main__":
    # Initialize DataManager
    db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
    dm = DataManager(db_path)
    
    # Check for --live flag
    dry_run = "--live" not in sys.argv
    
    # Run cleanup
    cleanup_all_users(dm, dry_run=dry_run)
    
    print()
    print("="*70)
