"""
AI/LLM API Router with Swagger Documentation

Provides REST API endpoints for testing and integrating with the AI system.
All endpoints require authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from datamanager.data_model import User
from ai_chatagent import AiChatagent, llm, dm
from app.ote_logger import get_logger

router = APIRouter(
    prefix="/api/ai",
    tags=["AI/LLM"],
    responses={401: {"description": "Not authenticated"}},
)

ote_logger = get_logger()


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    """Request model for chat completion."""
    message: str = Field(
        ..., 
        description="User's message to the AI",
        example="What's the weather in Paris?"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Optional conversation ID for context",
        example="conv_abc123"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's the weather in Paris?",
                "conversation_id": "conv_123"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat completion."""
    response: str = Field(..., description="AI's response")
    request_id: str = Field(..., description="Unique request identifier for tracing")
    conversation_id: str = Field(..., description="Conversation identifier")
    tools_used: List[str] = Field(default=[], description="List of tools used in this response")
    metrics: Dict[str, Any] = Field(default={}, description="Performance metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "The current weather in Paris is 15°C and cloudy.",
                "request_id": "req_abc123def456",
                "conversation_id": "conv_123",
                "tools_used": ["tavily_search"],
                "metrics": {
                    "duration_ms": 1234.56,
                    "tokens": 2769,
                    "cost_usd": 0.000419
                }
            }
        }


class UserPreferenceRequest(BaseModel):
    """Request model for managing user preferences."""
    action: str = Field(
        ...,
        description="Action to perform: 'get', 'set', or 'delete'",
        pattern="^(get|set|delete)$"
    )
    preference_type: Optional[str] = Field(
        None,
        description="Category of preference (required for set/delete)",
        example="personal_info"
    )
    preference_key: Optional[str] = Field(
        None,
        description="Specific preference key (required for set/delete)",
        example="favorite_color"
    )
    preference_value: Optional[str] = Field(
        None,
        description="Value to set (required for set action)",
        example="blue"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "set",
                "preference_type": "personal_info",
                "preference_key": "favorite_color",
                "preference_value": "blue"
            }
        }


class ConversationRecallResponse(BaseModel):
    """Response model for conversation history."""
    status: str
    messages: List[Dict[str, str]]
    total_messages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "messages": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hi! How can I help?"}
                ],
                "total_messages": 10
            }
        }


class SkillEvaluationRequest(BaseModel):
    """Request model for skill evaluation."""
    message: str = Field(..., description="Message to evaluate for social skills")
    cultural_context: str = Field(
        default="Western",
        description="Cultural context for evaluation",
        example="Western"
    )
    use_web_research: bool = Field(
        default=True,
        description="Whether to fetch latest empathy research from web"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I understand how you feel. That makes sense to me.",
                "cultural_context": "Western",
                "use_web_research": True
            }
        }


class MetricsSummaryResponse(BaseModel):
    """Response model for metrics summary."""
    total_requests: int
    success_rate: float
    avg_duration_ms: float
    total_tokens: int
    total_cost_usd: float
    avg_tokens_per_request: float
    most_used_tools: List[Dict[str, Any]]
    duplicate_blocks: int


# ==================== API Endpoints ====================

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with AI",
    description="Send a message to the AI and get a response. Supports tool usage, web search, and context management.",
    responses={
        200: {"description": "Successful response from AI"},
        401: {"description": "Not authenticated"},
        500: {"description": "Internal server error"}
    }
)
async def chat_with_ai(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the AI system.
    
    This endpoint provides full conversational AI capabilities including:
    - Natural language understanding
    - Tool usage (web search, skill evaluation, etc.)
    - Context management
    - Social skills training
    - Translation and clarification
    
    **Example:**
    ```json
    {
        "message": "What's the weather in Tokyo?",
        "conversation_id": "conv_123"
    }
    ```
    """
    try:
        # Create AI agent for this user
        agent = AiChatagent(current_user, llm)
        
        # Generate request ID for tracing
        request_id = ote_logger.generate_request_id()
        
        # Build graph and process message
        graph = agent.build_graph()
        config = {
            "configurable": {
                "thread_id": request.conversation_id or f"user_{current_user.id}"
            }
        }
        
        from langchain_core.messages import HumanMessage
        events = list(graph.stream(
            {"messages": [HumanMessage(content=request.message)]},
            config,
            stream_mode="values"
        ))
        
        # Extract response
        if events and "messages" in events[-1]:
            last_message = events[-1]["messages"][-1]
            response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response_text = "I couldn't process your message. Please try again."
        
        # Extract tools used
        tools_used = []
        for event in events:
            for msg in event.get("messages", []):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', 'unknown')
                        if tool_name not in tools_used:
                            tools_used.append(tool_name)
        
        return ChatResponse(
            response=response_text,
            request_id=request_id,
            conversation_id=request.conversation_id or f"user_{current_user.id}",
            tools_used=tools_used,
            metrics={
                "duration_ms": 0,  # TODO: Calculate from O-T-E logger
                "tokens": 0,
                "cost_usd": 0.0
            }
        )
        
    except Exception as e:
        ote_logger.logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )


@router.post(
    "/preferences",
    summary="Manage User Preferences",
    description="Get, set, or delete encrypted user preferences",
    responses={
        200: {"description": "Operation successful"},
        401: {"description": "Not authenticated"},
        400: {"description": "Invalid request"}
    }
)
async def manage_preferences(
    request: UserPreferenceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Manage user preferences with automatic encryption for sensitive data.
    
    **Supported preference types:**
    - `personal_info`: Name, DOB, address (encrypted)
    - `contact`: Email, phone (encrypted)
    - `interests`: Hobbies, topics
    - `skills`: User skills and progress
    - `preferences`: App settings
    
    **Actions:**
    - `get`: Retrieve preferences
    - `set`: Store preference (auto-encrypts sensitive data)
    - `delete`: Remove preference
    
    **Example GET:**
    ```json
    {
        "action": "get",
        "preference_type": "personal_info"
    }
    ```
    
    **Example SET:**
    ```json
    {
        "action": "set",
        "preference_type": "personal_info",
        "preference_key": "favorite_color",
        "preference_value": "blue"
    }
    ```
    """
    try:
        from ai_chatagent import UserPreferenceTool
        
        tool = UserPreferenceTool(dm)
        result = tool._run(
            action=request.action,
            user_id=current_user.id,
            preference_type=request.preference_type,
            preference_key=request.preference_key,
            preference_value=request.preference_value
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error managing preferences: {str(e)}"
        )


@router.get(
    "/conversation/history",
    response_model=ConversationRecallResponse,
    summary="Get Conversation History",
    description="Retrieve the last 20 messages for the current user",
)
async def get_conversation_history(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve conversation history for the authenticated user.
    
    Returns the last 20 messages (user and assistant) to provide context
    for ongoing conversations.
    """
    try:
        from tools.conversation_recall_tool import ConversationRecallTool
        
        tool = ConversationRecallTool(dm)
        result_json = tool._run(user_id=current_user.id)
        
        # Parse JSON string result
        import json
        result = json.loads(result_json) if isinstance(result_json, str) else result_json
        
        return ConversationRecallResponse(
            status=result.get("status", "success"),
            messages=result.get("data", []),
            total_messages=result.get("total_messages", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversation history: {str(e)}"
        )


@router.post(
    "/skills/evaluate",
    summary="Evaluate Social Skills",
    description="Analyze a message for social skills demonstration with cultural context",
)
async def evaluate_skills(
    request: SkillEvaluationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Evaluate social skills in a message using latest research.
    
    Analyzes messages for:
    - **Active listening**: Understanding and acknowledgment
    - **Empathy**: Emotional awareness and support
    - **Clarity**: Clear communication
    - **Engagement**: Conversation participation
    
    Uses web research to fetch the latest empathy and social skills standards
    based on cultural context.
    
    **Example:**
    ```json
    {
        "message": "I understand how you feel. That makes sense.",
        "cultural_context": "Western",
        "use_web_research": true
    }
    ```
    """
    try:
        from ai_chatagent import SkillEvaluator
        
        tool = SkillEvaluator(dm)
        result = tool._run(
            user_id=current_user.id,
            message=request.message,
            cultural_context=request.cultural_context,
            use_web_research=request.use_web_research
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating skills: {str(e)}"
        )


@router.get(
    "/metrics",
    response_model=MetricsSummaryResponse,
    summary="Get AI Metrics",
    description="Retrieve aggregated metrics for AI system performance and usage",
)
async def get_metrics(
    last_n: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI system metrics and analytics.
    
    Returns aggregated statistics for the last N requests:
    - Success rate
    - Average response time
    - Token usage and costs
    - Most used tools
    - Duplicate block frequency
    
    **Query Parameters:**
    - `last_n`: Number of recent requests to analyze (default: 100)
    """
    try:
        summary = ote_logger.get_metrics_summary(last_n=last_n)
        
        if "error" in summary:
            return MetricsSummaryResponse(
                total_requests=0,
                success_rate=0.0,
                avg_duration_ms=0.0,
                total_tokens=0,
                total_cost_usd=0.0,
                avg_tokens_per_request=0.0,
                most_used_tools=[],
                duplicate_blocks=0
            )
        
        return MetricsSummaryResponse(**summary)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving metrics: {str(e)}"
        )


@router.get(
    "/tools",
    summary="List Available Tools",
    description="Get a list of all available AI tools and their descriptions",
)
async def list_tools(current_user: User = Depends(get_current_user)):
    """
    List all available AI tools.
    
    Returns information about each tool including:
    - Name
    - Description
    - Parameters
    - Usage examples
    """
    try:
        agent = AiChatagent(current_user, llm)
        
        tools_info = []
        for tool_name, tool_instance in agent.tool_instances.items():
            if tool_instance:
                tools_info.append({
                    "name": tool_name,
                    "description": getattr(tool_instance, 'description', 'No description'),
                    "available": True
                })
        
        return {
            "total_tools": len(tools_info),
            "tools": tools_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tools: {str(e)}"
        )
