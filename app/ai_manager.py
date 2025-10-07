from typing import Dict, Optional, List, Any
import threading
from pathlib import Path
import sys

# Add project root to path for imports
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ai_chatagent import AiChatagent, dm, llm
from datamanager.data_model import User

class AIAgentManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AIAgentManager, cls).__new__(cls)
                cls._instance.agents: Dict[int, AiChatagent] = {}
                cls._instance.graphs: Dict[int, Any] = {}  # Store built graphs
                cls._instance.locks: Dict[int, threading.Lock] = {}
        return cls._instance
    
    def get_agent(self, user_id: int) -> tuple:
        """Get or create an AI agent and graph for the user.
        
        Returns:
            tuple: (agent, graph)
        """
        with self._lock:
            if user_id not in self.agents:
                # Get user from database
                user = dm.get_user(user_id)
                if not user:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Create AI agent
                agent = AiChatagent(user, llm)
                graph = agent.build_graph()
                
                self.agents[user_id] = agent
                self.graphs[user_id] = graph
                self.locks[user_id] = threading.Lock()
            
            return self.agents[user_id], self.graphs[user_id]
    
    async def get_response(self, user_id: int, message: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Get a response from the AI agent for the given user.
        
        Args:
            user_id: The ID of the user
            message: The user's message
            thread_id: Optional thread ID for conversation continuity
            
        Returns:
            Dict with 'response', 'thread_id', and 'tools_used'
        """
        try:
            agent, graph = self.get_agent(user_id)
            user_lock = self.locks[user_id]
            
            # Use thread_id or create one from user_id
            if not thread_id:
                thread_id = str(user_id)
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Use the lock to ensure thread safety for this session
            with user_lock:
                # Stream the graph and collect events
                events = list(graph.stream(
                    {"messages": [{"role": "user", "content": message}]},
                    config,
                    stream_mode="values"
                ))
                
                if not events:
                    return {
                        "response": "I'm sorry, I didn't receive a response.",
                        "thread_id": thread_id,
                        "tools_used": []
                    }
                
                # Get the last event and extract the AI response
                last_event = events[-1]
                last_message = last_event["messages"][-1]
                
                # Extract response content
                if hasattr(last_message, 'content'):
                    response_text = last_message.content
                elif isinstance(last_message, dict) and 'content' in last_message:
                    response_text = last_message['content']
                else:
                    response_text = str(last_message)
                
                # Extract tools used (if any)
                tools_used = []
                for event in events:
                    for msg in event.get("messages", []):
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                                if tool_name and tool_name not in tools_used:
                                    tools_used.append(tool_name)
                
                # Save the conversation to database
                dm.save_messages(user_id, [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response_text}
                ])
                
                return {
                    "response": response_text,
                    "thread_id": thread_id,
                    "tools_used": tools_used
                }
                
        except Exception as e:
            error_msg = f"Error processing AI message: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {
                "response": f"I'm sorry, I encountered an error: {str(e)}",
                "thread_id": thread_id or str(user_id),
                "tools_used": [],
                "error": str(e)
            }
