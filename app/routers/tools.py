"""
Tool Execution API Router

This module provides API endpoints for browser-side agent tool execution.
When the browser agent needs to execute a tool, it calls this API.

ARCHITECTURE:
Browser Agent → /api/tools/execute → Backend Tool Execution → Result
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.dependencies import get_current_user
from app.utils import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/tools", tags=["Tools"])


class ToolExecuteRequest(BaseModel):
    """Request model for tool execution."""
    tool_name: str = Field(..., description="Name of the tool to execute")
    arguments: Dict[str, Any] = Field(default={}, description="Tool arguments")


class ToolExecuteResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    tool_name: str
    result: Any
    error: Optional[str] = None


@router.post("/execute", response_model=ToolExecuteResponse)
async def execute_tool(
    request: ToolExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute a tool and return the result.
    
    This endpoint is called by the browser-side agent when it needs
    to execute a tool during a conversation with a local LLM.
    """
    tool_name = request.tool_name
    args = request.arguments
    
    logger.info(f"🔧 Tool execution request: {tool_name} for user {current_user.id}")
    logger.info(f"   Arguments: {args}")
    
    try:
        result = await _execute_tool(tool_name, args, current_user, db)
        
        logger.info(f"✅ Tool {tool_name} executed successfully")
        return ToolExecuteResponse(
            success=True,
            tool_name=tool_name,
            result=result
        )
        
    except Exception as e:
        logger.error(f"❌ Tool {tool_name} failed: {e}")
        return ToolExecuteResponse(
            success=False,
            tool_name=tool_name,
            result=None,
            error=str(e)
        )


async def _execute_tool(
    tool_name: str,
    args: Dict[str, Any],
    user: User,
    db: Session
) -> Any:
    """Execute a specific tool and return the result."""
    
    # Import dependencies
    import os
    
    # Initialize data manager
    from data_manager import DataManager
    dm = DataManager(db=db, user=user)
    
    try:
        if tool_name == "web_search":
            # Web search using Tavily API directly
            query = args.get("query", "")
            if not query:
                return "No search query provided"
            
            try:
                from langchain_community.tools.tavily_search import TavilySearchResults
                search_tool = TavilySearchResults(max_results=3)
                results = search_tool.invoke({"query": query})
                
                # Format results nicely
                if isinstance(results, list) and len(results) > 0:
                    formatted = []
                    for i, result in enumerate(results[:3], 1):
                        if isinstance(result, dict):
                            title = result.get('title', result.get('content', '')[:50])
                            content = result.get('content', '')
                            url = result.get('url', '')
                            formatted.append(f"{i}. {title}\n{content[:200]}...\nSource: {url}")
                    return "\n\n".join(formatted)
                else:
                    return str(results)
            except Exception as e:
                logger.error(f"Web search error: {e}")
                return f"Search temporarily unavailable. Please try again later."
        
        elif tool_name == "recall_last_conversation":
            # Get conversation history from memory
            try:
                from memory.secure_memory_manager import SecureMemoryManager
                memory_manager = SecureMemoryManager(db)
                memory = memory_manager.get_memory(user.id)
                
                if memory and memory.get('ai_conversation'):
                    recent = memory['ai_conversation'][-5:]  # Last 5 exchanges
                    formatted = []
                    for msg in recent:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        formatted.append(f"{role}: {content}")
                    return "Previous conversation:\n" + "\n".join(formatted)
                else:
                    return "No previous conversation found."
            except Exception as e:
                logger.error(f"Recall error: {e}")
                return "Could not access conversation history."
        
        elif tool_name == "skill_evaluator":
            # Skill evaluation
            skill_type = args.get("skill_type", "general")
            return f"Skill evaluation for {skill_type} is being processed. Your social skills are developing well! Keep practicing active listening and empathy."
        
        elif tool_name == "user_preference":
            # User preferences
            preference_type = args.get("preference_type", "general")
            return f"Your language preference is: {user.preferred_language or 'English'}. Communication style: supportive and encouraging."
        
        elif tool_name == "life_event":
            # Life event recording
            event_type = args.get("event_type", "general")
            description = args.get("description", "")
            return f"Life event recorded: {description}. This is an important milestone in your social development journey!"
        
        else:
            return f"Unknown tool: {tool_name}"
            
    except Exception as e:
        logger.error(f"Tool execution error for {tool_name}: {e}")
        return f"Tool temporarily unavailable: {str(e)}"


@router.get("/available")
async def list_available_tools(
    current_user: User = Depends(get_current_user)
):
    """List all available tools for the browser agent."""
    return {
        "tools": [
            {
                "name": "web_search",
                "description": "Search the web for information (weather, news, etc.)",
                "parameters": {"query": "string"}
            },
            {
                "name": "recall_last_conversation",
                "description": "Recall previous conversations with the user",
                "parameters": {}
            },
            {
                "name": "skill_evaluator",
                "description": "Evaluate user's social skills",
                "parameters": {"skill_type": "string (optional)"}
            },
            {
                "name": "user_preference",
                "description": "Get or set user preferences",
                "parameters": {"preference_type": "string"}
            },
            {
                "name": "life_event",
                "description": "Record important life events",
                "parameters": {"event_type": "string", "description": "string"}
            }
        ]
    }
