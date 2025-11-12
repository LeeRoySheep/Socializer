"""
Debug script to check chat history status.

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.websocket.general_chat_history import get_general_chat_history
from datetime import datetime, timedelta


def debug_chat_history():
    """Check and initialize chat history."""
    
    print("\n🔍 DEBUGGING CHAT HISTORY")
    print("="*60)
    
    # Get the singleton instance
    history = get_general_chat_history()
    
    # Check current state
    current = history.get_history()
    print(f"Current messages in history: {len(current)}")
    
    if len(current) > 0:
        print("\n📋 Current messages:")
        for i, msg in enumerate(current):
            print(f"   [{i}] {msg['username']}: {msg['content'][:50]}...")
    else:
        print("⚠️ History is empty! Initializing with test messages...")
        
        # Initialize with messages
        base_time = datetime.utcnow() - timedelta(minutes=30)
        
        test_messages = [
            ("Emma", "Hello everyone! Good morning! ☀️", "user1"),
            ("Tom", "Hey Emma! How's it going?", "user2"),
            ("Emma", "Great! Just working on a project", "user1"),
            ("Sarah", "What kind of project?", "user3"),
            ("Emma", "A chat app with real-time features", "user1"),
            ("Tom", "That sounds cool!", "user2"),
            ("Mike", "Anyone here using Python?", "user4"),
            ("Sarah", "Yes! Python is great for web apps", "user3"),
            ("Emma", "Using FastAPI with WebSocket support", "user1"),
            ("Tom", "FastAPI is amazing for real-time apps", "user2"),
            ("Mike", "The performance is really good", "user4"),
            ("Sarah", "And the automatic API docs are helpful", "user3"),
        ]
        
        for i, (username, content, user_id) in enumerate(test_messages):
            msg_time = base_time + timedelta(minutes=i*2)
            history.add_message({
                "username": username,
                "content": content,
                "user_id": user_id,
                "timestamp": msg_time.isoformat()
            })
            print(f"   ✅ Added: {username}: {content[:30]}...")
        
        # Verify
        current = history.get_history()
        print(f"\n✅ Initialized with {len(current)} messages")
    
    # Test JSON export
    json_str = history.get_history_json()
    print(f"\n📄 JSON export length: {len(json_str)} chars")
    
    print("\n✅ Chat history is ready for use!")
    print(f"   Messages: {len(current)}")
    print(f"   Singleton ID: {id(history)}")
    
    return current


if __name__ == "__main__":
    messages = debug_chat_history()
    
    print("\n" + "="*60)
    print("When you start the server with 'uvicorn app.main:app --reload'")
    print("Users connecting to the general chat should receive these messages.")
    print("\nCheck browser console for '[CHAT HISTORY]' logs to debug.")
