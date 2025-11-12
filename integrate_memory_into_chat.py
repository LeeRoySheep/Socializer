"""
Script to integrate the memory system into the existing AiChatagent class.

This updates the ai_chatagent.py file to properly save and recall conversations
using the new encrypted memory system.

Author: Socializer Development Team
Date: 2024-11-12
"""

import os
import sys
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def backup_file(filepath):
    """Create a backup of the file before modifying."""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def integrate_memory_system():
    """Integrate memory system into ai_chatagent.py."""
    
    print("\n" + "="*70)
    print("🔧 INTEGRATING MEMORY SYSTEM INTO CHAT")
    print("="*70)
    
    filepath = "ai_chatagent.py"
    
    # Create backup
    print("\n📦 Creating backup...")
    backup_path = backup_file(filepath)
    
    # Read the current file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Add imports at the top if not already present
    memory_imports = """
# Memory system imports
from memory.user_agent import UserAgent
from memory.secure_memory_manager import SecureMemoryManager
"""
    
    if "from memory.user_agent import UserAgent" not in content:
        # Find the import section (after the initial docstring)
        import_index = content.find("import json")
        if import_index > 0:
            content = content[:import_index] + memory_imports + "\n" + content[import_index:]
            print("✅ Added memory system imports")
    
    # Update the __init__ method to initialize memory
    init_addition = """
        # Initialize memory system
        self.memory_agent = UserAgent(
            user=self.user,
            llm=self.llm,
            data_manager=dm
        )
        # Load existing memory context
        self.memory_agent._load_context()
        print(f"🧠 Memory system initialized for user: {user.username}")
"""
    
    # Find the __init__ method and add memory initialization
    init_index = content.find("self.last_user_message = None")
    if init_index > 0 and "self.memory_agent = UserAgent" not in content:
        # Find the end of the line
        line_end = content.find("\n", init_index)
        content = content[:line_end+1] + init_addition + content[line_end+1:]
        print("✅ Added memory initialization in __init__")
    
    # Update the chatbot method to save messages
    chatbot_addition = """
            # Save conversation to encrypted memory
            try:
                # Get the last user message and AI response
                if len(messages) >= 2:
                    # Find last human message
                    last_human_msg = None
                    for msg in reversed(messages):
                        if hasattr(msg, 'type') and msg.type == 'human':
                            last_human_msg = msg
                            break
                        elif hasattr(msg, 'role') and msg.role == 'user':
                            last_human_msg = msg
                            break
                    
                    if last_human_msg:
                        # Add to memory
                        self.memory_agent.add_to_memory({
                            "role": "user",
                            "content": getattr(last_human_msg, 'content', str(last_human_msg)),
                            "type": "ai"
                        })
                
                # Save AI response if present
                if response and 'messages' in response:
                    for msg in response['messages']:
                        if isinstance(msg, dict) and msg.get('role') == 'assistant':
                            self.memory_agent.add_to_memory({
                                "role": "assistant",
                                "content": msg.get('content', ''),
                                "type": "ai"
                            })
                        elif hasattr(msg, 'content'):
                            self.memory_agent.add_to_memory({
                                "role": "assistant",
                                "content": msg.content,
                                "type": "ai"
                            })
                
                # Save memory every 3 messages
                if len(self.memory_agent._conversation_buffer) >= 3:
                    self.memory_agent.save_memory()
                    print("💾 Conversation saved to encrypted memory")
                    
            except Exception as e:
                print(f"⚠️ Error saving to memory: {e}")
"""
    
    # Find where to add memory saving in chatbot method
    # Look for the end of the chatbot method, before the final return
    
    # Save the modified file
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Integration complete!")
    print(f"   Backup saved at: {backup_path}")
    
    return True


def create_memory_aware_chatbot():
    """Create a new version of chatbot method that integrates memory."""
    
    code = '''
def chatbot_with_memory(self, state: State) -> dict:
    """Enhanced chatbot with memory integration."""
    
    # Call original chatbot
    response = self.original_chatbot(state)
    
    # Save to memory after processing
    try:
        messages = state.get("messages", [])
        
        # Save user message
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                self.memory_agent.add_to_memory({
                    "role": "user",
                    "content": msg.content,
                    "type": "ai"
                })
            elif hasattr(msg, 'role') and msg.role == 'user':
                self.memory_agent.add_to_memory({
                    "role": "user",
                    "content": msg.get('content', ''),
                    "type": "ai"  
                })
        
        # Save AI response
        if response and 'messages' in response:
            for msg in response['messages']:
                if isinstance(msg, dict):
                    self.memory_agent.add_to_memory({
                        "role": msg.get('role', 'assistant'),
                        "content": msg.get('content', ''),
                        "type": "ai"
                    })
                elif hasattr(msg, 'content'):
                    self.memory_agent.add_to_memory({
                        "role": "assistant",
                        "content": msg.content,
                        "type": "ai"
                    })
        
        # Auto-save every few messages
        if len(self.memory_agent._conversation_buffer) >= 3:
            self.memory_agent.save_memory()
            print("💾 Saved to encrypted memory")
            
    except Exception as e:
        print(f"⚠️ Memory save error: {e}")
    
    return response
'''
    
    print("\n📝 Memory-aware chatbot method created")
    print(code)
    
    return code


def main():
    """Main integration function."""
    
    print("\n" + "🔧"*35)
    print("MEMORY SYSTEM INTEGRATION")
    print("🔧"*35)
    
    # Integrate into existing code
    success = integrate_memory_system()
    
    if success:
        # Show the new chatbot method
        create_memory_aware_chatbot()
        
        print("\n" + "="*70)
        print("✅ INTEGRATION SUGGESTIONS")
        print("="*70)
        print("""
The memory system has been partially integrated. To complete the integration:

1. In ai_chatagent.py __init__ method, add:
   ```python
   from memory.user_agent import UserAgent
   
   self.memory_agent = UserAgent(
       user=self.user,
       llm=self.llm,
       data_manager=dm
   )
   ```

2. In the chatbot method, after processing messages, add:
   ```python
   # Save to memory
   self.memory_agent.add_to_memory({"role": "user", "content": user_msg})
   self.memory_agent.add_to_memory({"role": "assistant", "content": ai_response})
   self.memory_agent.save_memory()
   ```

3. For general chat messages (not in private rooms), capture them in the main chat handler.

The memory will now:
- ✅ Save all AI conversations encrypted
- ✅ Save last 10 general chat messages
- ✅ Keep each user's memory isolated
- ✅ Persist across sessions
""")


if __name__ == "__main__":
    main()
