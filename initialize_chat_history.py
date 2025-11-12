"""
Initialize the general chat history with some test messages.

This ensures there are messages to display when users connect.

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.websocket.general_chat_history import get_general_chat_history


def initialize_with_test_messages():
    """Add some test messages to the chat history."""
    
    print("\n📝 Initializing General Chat History with Test Messages...")
    
    history = get_general_chat_history()
    history.clear()
    
    # Create realistic test messages
    base_time = datetime.utcnow() - timedelta(minutes=30)
    
    test_messages = [
        ("Alice", "Good morning everyone! 👋", "1"),
        ("Bob", "Hey Alice! How are you?", "2"),
        ("Alice", "Doing great! Working on a new project", "1"),
        ("Charlie", "That sounds interesting! What kind of project?", "3"),
        ("Alice", "A chat application with real-time features", "1"),
        ("Bob", "Cool! Is it using Python?", "2"),
        ("Alice", "Yes, FastAPI for the backend", "1"),
        ("Charlie", "Nice choice! FastAPI is awesome", "3"),
        ("Bob", "And what about the frontend?", "2"),
        ("Alice", "JavaScript with WebSocket connections", "1"),
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
    
    current = history.get_history()
    print(f"\n✅ History initialized with {len(current)} messages")
    
    # Display current history
    print("\n📋 Current Chat History:")
    for i, msg in enumerate(current):
        print(f"   [{i}] {msg['username']}: {msg['content']}")
    
    return current


if __name__ == "__main__":
    messages = initialize_with_test_messages()
    print(f"\n✅ Ready! The general chat now has {len(messages)} messages in history.")
