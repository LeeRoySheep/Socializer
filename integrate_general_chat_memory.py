"""
Script to integrate memory system into general chat handlers.

This adds encrypted memory storage for general chat messages.

Author: Socializer Development Team
Date: 2024-11-12
"""

import os
import shutil
from datetime import datetime


def update_websocket_routes():
    """Update app/websocket/routes.py to save to memory."""
    
    print("\n📝 Updating WebSocket routes handler...")
    
    # Read the file
    filepath = "app/websocket/routes.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add memory imports at the top
    memory_import = """
# Memory system imports for general chat
from memory.secure_memory_manager import SecureMemoryManager
"""
    
    # Find where to add imports (after other imports)
    if "from memory.secure_memory_manager" not in content:
        import_pos = content.find("from datamanager.data_manager import DataManager")
        if import_pos > 0:
            content = content[:import_pos] + memory_import + "\n" + content[import_pos:]
            print("   ✅ Added memory imports")
    
    # Add memory saving code after the existing save
    memory_save_code = """
                # Also save to encrypted memory for recall
                try:
                    user_obj = dm.get_user(int(user_id))
                    if user_obj:
                        memory_manager = SecureMemoryManager(dm, user_obj)
                        memory_manager.add_message({
                            "type": "general",
                            "sender": username,
                            "content": text,
                            "room_id": room_id,
                            "timestamp": datetime.utcnow().isoformat()
                        }, message_type="general")
                        # Auto-save every few messages
                        if len(memory_manager._current_memory.get("general_chat", [])) >= 3:
                            memory_manager.save_combined_memory(
                                memory_manager._current_memory.get("messages", []),
                                max_general=10,  # Keep last 10 general chat
                                max_ai=20        # Keep last 20 AI messages
                            )
                            logger.debug(f"Saved general chat to encrypted memory for user {user_id}")
                except Exception as mem_error:
                    logger.error(f"Error saving to memory: {mem_error}")
                    # Don't fail the chat if memory save fails
"""
    
    # Find where to add memory saving (after dm.save_messages)
    save_pos = content.find("# Don't fail the chat if saving fails")
    if save_pos > 0 and "Also save to encrypted memory" not in content:
        content = content[:save_pos] + memory_save_code + "\n                " + content[save_pos:]
        print("   ✅ Added memory saving code")
    
    # Save the file
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("   ✅ Updated app/websocket/routes.py")
    return True


def update_main_websocket():
    """Update app/main.py WebSocket endpoint to save to memory."""
    
    print("\n📝 Updating main WebSocket endpoint...")
    
    filepath = "app/main.py"
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add memory imports
    memory_import = """from memory.secure_memory_manager import SecureMemoryManager
"""
    
    if "from memory.secure_memory_manager" not in content:
        # Find a good place to add import
        import_pos = content.find("from datamanager.data_manager import DataManager")
        if import_pos > 0:
            content = content[:import_pos] + memory_import + content[import_pos:]
            print("   ✅ Added memory import")
    
    # Add memory saving after message is saved to database
    memory_code = """
                        # Also save to encrypted memory
                        try:
                            memory_manager = SecureMemoryManager(dm, user)
                            memory_manager.add_message({
                                "type": "general",
                                "sender": user.username,
                                "content": content,
                                "room_id": room_id,
                                "timestamp": datetime.utcnow().isoformat()
                            }, message_type="general")
                            # Auto-save periodically
                            if len(memory_manager._current_memory.get("messages", [])) % 5 == 0:
                                memory_manager.save_combined_memory(
                                    memory_manager._current_memory.get("messages", []),
                                    max_general=10,
                                    max_ai=20
                                )
                        except Exception as mem_e:
                            logger.debug(f"Memory save error: {mem_e}")
"""
    
    # Find where to add (after database save)
    save_location = content.find('logger.info(f"Saved message to database:')
    if save_location > 0 and "Also save to encrypted memory" not in content:
        # Find the end of the try block
        next_except = content.find("except Exception as e:", save_location)
        if next_except > 0:
            # Insert before the except
            content = content[:next_except] + memory_code + "\n                    " + content[next_except:]
            print("   ✅ Added memory saving for general chat")
    
    # Save the file
    with open(filepath, 'w') as f:
        f.write(content)
    
    print("   ✅ Updated app/main.py")
    return True


def create_test_general_chat():
    """Create a test script for general chat memory."""
    
    print("\n📝 Creating test script...")
    
    test_code = '''"""
Test general chat memory integration.

This verifies that general chat messages are saved to encrypted memory.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datamanager.data_manager import DataManager
from memory.secure_memory_manager import SecureMemoryManager
import json


def test_general_chat_saving():
    """Test that general chat is saved to memory."""
    
    print("\\n" + "="*60)
    print("🧪 TESTING GENERAL CHAT MEMORY")
    print("="*60)
    
    dm = DataManager()
    
    # Test with a user
    user = dm.get_user(1)
    if not user:
        print("❌ User not found")
        return False
    
    print(f"\\n👤 Testing with user: {user.username}")
    
    # Create memory manager
    memory_manager = SecureMemoryManager(dm, user)
    
    # Clear for clean test
    memory_manager.clear_memory()
    print("🗑️  Cleared existing memory")
    
    # Simulate general chat messages
    print("\\n💬 Simulating general chat...")
    
    test_messages = [
        {"type": "general", "sender": "alice", "content": "Hey everyone!"},
        {"type": "general", "sender": user.username, "content": "Hi Alice!"},
        {"type": "general", "sender": "bob", "content": "How's it going?"},
        {"type": "general", "sender": user.username, "content": "Great, working on a project"},
        {"type": "general", "sender": "charlie", "content": "Cool! What project?"},
    ]
    
    for msg in test_messages:
        msg["timestamp"] = "2024-11-12T10:00:00"
        memory_manager.add_message(msg, message_type="general")
    
    # Save
    memory_manager.save_combined_memory(
        test_messages,
        max_general=10,
        max_ai=20
    )
    print(f"   ✅ Saved {len(test_messages)} general chat messages")
    
    # Recall
    print("\\n🔍 Recalling memory...")
    recalled = memory_manager.recall_conversation_memory()
    
    if recalled:
        general = recalled.get("general_chat", [])
        print(f"\\n📊 Results:")
        print(f"   • General chat messages: {len(general)}")
        
        # Check content
        has_project = any("project" in str(msg).lower() for msg in general)
        print(f"   • Contains 'project': {'✅' if has_project else '❌'}")
        
        if general:
            print(f"\\n💬 Saved general chat:")
            for msg in general[-3:]:
                if isinstance(msg, dict):
                    sender = msg.get('sender', 'unknown')
                    content = msg.get('content', '')[:50]
                    print(f"   {sender}: {content}...")
        
        return len(general) == len(test_messages)
    
    return False


if __name__ == "__main__":
    if test_general_chat_saving():
        print("\\n✅ General chat memory is working!")
    else:
        print("\\n❌ General chat memory test failed")
'''
    
    with open('test_general_chat_memory.py', 'w') as f:
        f.write(test_code)
    
    print("   ✅ Created test_general_chat_memory.py")
    return True


def main():
    """Main integration function."""
    
    print("\n" + "🔧"*30)
    print("GENERAL CHAT MEMORY INTEGRATION")
    print("🔧"*30)
    
    # Check if files exist
    files_to_update = [
        "app/websocket/routes.py",
        "app/main.py"
    ]
    
    missing = []
    for filepath in files_to_update:
        if not os.path.exists(filepath):
            missing.append(filepath)
    
    if missing:
        print(f"\n❌ Missing files:")
        for f in missing:
            print(f"   • {f}")
        print("\nThese files are needed for WebSocket chat integration.")
        return
    
    # Backup files
    print("\n📦 Creating backups...")
    for filepath in files_to_update:
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"   ✅ {backup_path}")
    
    # Update files
    success = []
    
    if update_websocket_routes():
        success.append("WebSocket routes")
    
    if update_main_websocket():
        success.append("Main WebSocket endpoint")
    
    if create_test_general_chat():
        success.append("Test script")
    
    # Summary
    print("\n" + "="*60)
    print("📊 INTEGRATION SUMMARY")
    print("="*60)
    
    if len(success) == 3:
        print("\n✅ All integrations complete!")
        print("""
General chat messages will now be:
1. Saved to encrypted memory automatically
2. Limited to last 10 messages
3. Isolated per user
4. Recallable via ConversationRecallTool

To test:
1. Send messages in the general chat
2. Run: python test_general_chat_memory.py
3. Use recall tool to verify messages are saved
""")
    else:
        print(f"\n⚠️ Partial success: {success}")
        print("\nCheck the error messages above for details.")


if __name__ == "__main__":
    main()
