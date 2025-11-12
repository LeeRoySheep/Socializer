"""
Clear memory for specific users to start fresh.

This script clears the conversation memory for human2 and human3
to ensure clean testing.

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datamanager.data_manager import DataManager
from memory.secure_memory_manager import SecureMemoryManager


def clear_user_memories():
    """Clear memory for test users."""
    
    print("\n🧹 CLEARING USER MEMORIES")
    print("="*60)
    
    dm = DataManager()
    
    # Users to clear
    user_ids = [2, 3]  # human2 and human3
    
    for user_id in user_ids:
        user = dm.get_user(user_id)
        if user:
            print(f"\n📝 Clearing memory for: {user.username} (ID: {user_id})")
            
            try:
                # Create memory manager and clear
                memory_manager = SecureMemoryManager(dm, user)
                
                # Get current stats
                stats = memory_manager.get_memory_stats()
                print(f"   Before: {stats['total_messages']} total messages")
                print(f"          {stats['ai_conversation_count']} AI messages")
                print(f"          {stats['general_chat_count']} chat messages")
                
                # Clear the memory
                success = memory_manager.clear_memory()
                
                if success:
                    # Verify it's cleared
                    new_stats = memory_manager.get_memory_stats()
                    print(f"   ✅ Memory cleared successfully!")
                    print(f"   After:  {new_stats['total_messages']} total messages")
                else:
                    print(f"   ❌ Failed to clear memory")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ❌ User {user_id} not found")
    
    print("\n✅ Memory clearing complete!")


if __name__ == "__main__":
    clear_user_memories()
