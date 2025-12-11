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
    
    # Import tools lazily to avoid circular imports
    from tools.search.tavily_search_tool import TavilySearchTool
    from tools.conversation.recall_tool import ConversationRecallTool
    from tools.skills.evaluator_tool import SkillEvaluator
    from tools.user.preference_tool import UserPreferenceTool
    from tools.events.life_event_tool import LifeEventTool
    from data_manager import DataManager
    
    # Initialize data manager
    dm = DataManager(db=db, user=user)
    
    if tool_name == "web_search":
        # Web search tool
        query = args.get("query", "")
        if not query:
            return "No search query provided"
        
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            search_tool = TavilySearchResults(max_results=3)
            tool = TavilySearchTool(search_tool=search_tool)
            result = tool._run(query=query)
            return result
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return f"Search failed: {str(e)}"
    
    elif tool_name == "recall_last_conversation":
        # Conversation recall tool
        try:
            tool = ConversationRecallTool(dm)
            result = tool._run(user_id=user.id)
            return result
        except Exception as e:
            logger.error(f"Recall error: {e}")
            return f"Could not recall conversation: {str(e)}"
    
    elif tool_name == "skill_evaluator":
        # Skill evaluation tool
        try:
            tool = SkillEvaluator(dm)
            skill_type = args.get("skill_type", "general")
            result = tool._run(user_id=user.id, skill_type=skill_type)
            return result
        except Exception as e:
            logger.error(f"Skill evaluator error: {e}")
            return f"Could not evaluate skills: {str(e)}"
    
    elif tool_name == "user_preference":
        # User preference tool
        try:
            tool = UserPreferenceTool(dm)
            preference_type = args.get("preference_type", "general")
            result = tool._run(user_id=user.id, preference_type=preference_type)
            return result
        except Exception as e:
            logger.error(f"Preference error: {e}")
            return f"Could not get preferences: {str(e)}"
    
    elif tool_name == "life_event":
        # Life event tool
        try:
            tool = LifeEventTool(dm)
            event_type = args.get("event_type", "general")
            description = args.get("description", "")
            result = tool._run(
                user_id=user.id,
                event_type=event_type,
                description=description
            )
            return result
        except Exception as e:
            logger.error(f"Life event error: {e}")
            return f"Could not record event: {str(e)}"
    
    else:
        return f"Unknown tool: {tool_name}"


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
