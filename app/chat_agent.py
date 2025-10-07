"""Module for handling AI chat functionality using the AiChatagent with full tool integration."""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import required modules
from ai_chatagent import AiChatagent, dm, llm, tools, tool_node
from datamanager.data_manager import DataManager
from langchain.chat_models import init_chat_model

# Initialize DataManager with the correct database path
db_path = os.path.join(project_root, 'app', 'data.sqlite.db')
dm = DataManager(db_path)

# Initialize LLM if not already initialized
if 'llm' not in globals():
    llm = init_chat_model("openai:gpt-4o-mini")

# Initialize tools if not already done
if 'tools' not in globals():
    from ai_chatagent import tools as existing_tools
    tools = existing_tools

# Conversation history store
conversation_history = {}

class ChatState:
    """Maintains the state of the chat conversation."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.conversation_id = f"conv-{user_id}-{int(datetime.now().timestamp())}"
        self.messages = []
        
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Keep only the last 20 messages to manage memory
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]

def process_message(
    message: str, 
    conversation_id: Optional[str] = None, 
    user_id: int = 1,
    use_tools: bool = True
) -> Dict[str, Any]:
    """
    Process a chat message using the AiChatagent with full tool integration.
    
    Args:
        message: The user's message
        conversation_id: Optional conversation ID for multi-turn conversations
        user_id: User ID for the chat (defaults to 1 for testing)
        use_tools: Whether to enable tool usage (default: True)
        
    Returns:
        Dict containing the AI response, conversation ID, and metadata
    """
    try:
        # Get the user from the database
        user = dm.get_user(user_id)
        if not user:
            return {
                "response": "User not found. Please log in again.",
                "conversation_id": conversation_id or "error-conversation",
                "status": "error",
                "error": "user_not_found"
            }
        
        # Initialize or retrieve conversation state
        if not conversation_id:
            conversation_state = ChatState(user_id)
            conversation_id = conversation_state.conversation_id
            conversation_history[conversation_id] = conversation_state
        else:
            conversation_state = conversation_history.get(conversation_id, ChatState(user_id))
            conversation_history[conversation_id] = conversation_state
        
        # Add user message to conversation
        conversation_state.add_message("user", message)
        
        try:
            # Initialize the chat agent with tools and LLM
            chat_agent = AiChatagent(user=user, llm=llm)
            
            # Prepare the input for the chatbot
            chat_input = {
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    *[{"role": msg["role"], "content": msg["content"]} 
                      for msg in conversation_state.messages]
                ]
            }
            
            # Process the message with tools if enabled
            if use_tools and tools:
                # Use the tool node to process tool calls
                tool_response = tool_node(chat_input)
                
                # If tools were used, update the conversation with the tool responses
                if tool_response and "messages" in tool_response:
                    for msg in tool_response["messages"]:
                        conversation_state.add_message(msg["role"], msg["content"])
            
            # Get the final response from the LLM
            response = chat_agent.chatbot(chat_input)
            
            # Process the response
            if isinstance(response, dict) and "messages" in response:
                # Get the last assistant message
                assistant_messages = [
                    msg for msg in response["messages"] 
                    if msg["role"] == "assistant"
                ]
                
                if assistant_messages:
                    response_text = assistant_messages[-1].get(
                        "content", 
                        "I didn't understand that."
                    )
                    # Add assistant's response to conversation
                    conversation_state.add_message("assistant", response_text)
                else:
                    response_text = "I didn't receive a valid response. Please try again."
            else:
                response_text = str(response)
                conversation_state.add_message("assistant", response_text)
            
            # Prepare the response
            result = {
                "response": response_text,
                "conversation_id": conversation_id,
                "status": "success",
                "metadata": {
                    "message_count": len(conversation_state.messages),
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Save the conversation to the database
            try:
                dm.save_messages(
                    user_id=user_id,
                    messages=conversation_state.messages
                )
            except Exception as save_error:
                print(f"Error saving conversation: {str(save_error)}")
            
            return result
            
        except Exception as agent_error:
            error_msg = f"Error in chat agent: {str(agent_error)}"
            print(error_msg)
            raise RuntimeError(error_msg) from agent_error
        
    except Exception as e:
        # Log the error and return a friendly message
        error_msg = f"Error in process_message: {str(e)}"
        print(error_msg)
        
        return {
            "response": "I encountered an error processing your message. Please try again.",
            "conversation_id": conversation_id or "error-conversation",
            "status": "error",
            "error": str(e),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
        }

if __name__ == "__main__":
    # Simple console interface for testing
    print("Starting chat session. Type 'exit' to quit.")
    print("-" * 50)
    user
    user_id = 1  # Default user ID for testing
    conversation_id = "1"

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break

        response = process_message(
            message=user_input,
            conversation_id=conversation_id,
            user_id=user_id
        )

        print(f"\nAI: {response.get('response', 'No response')}")
        conversation_id = response.get("conversation_id", conversation_id)