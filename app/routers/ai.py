"""
AI/LLM API Router with Swagger Documentation

Provides REST API endpoints for testing and integrating with the AI system.
All endpoints require authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.database import get_db
from datamanager.data_model import User
from ai_chatagent import AiChatagent, llm, dm
from app.ote_logger import get_logger
from app.schemas import LLMConfigCreate, LLMConfigResponse
from training import TrainingPlanManager

# Initialize training manager
training_manager = TrainingPlanManager(dm)

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
    model: Optional[str] = Field(
        "gpt-4o-mini",
        description="LLM model to use",
        example="gpt-4o-mini"
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

@router.get(
    "/training/login-reminder",
    summary="Get Training Reminder (Login Message)",
    description="Get personalized training reminders for user on login. Shows active training plans and progress.",
    responses={
        200: {"description": "Training reminder message"},
        401: {"description": "Not authenticated"}
    }
)
async def get_training_reminder(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Get personalized training reminder for user login.
    
    Returns a friendly welcome message with:
    - Active training plans
    - Current progress levels
    - Next milestones
    
    Example:
        GET /api/ai/training/login-reminder
        
        Response:
        {
            "message": "Welcome back, John! 🎯\\n\\nYour Active Trainings:\\n• Empathy: Level 3/10..."
        }
    """
    try:
        reminder = training_manager.get_login_reminder(current_user)
        return {"message": reminder}
    except Exception as e:
        ote_logger.logger.error(f"Error getting training reminder: {e}", exc_info=True)
        return {"message": f"Welcome back, {current_user.username}! 👋"}


@router.post(
    "/training/logout",
    summary="Save Training Progress (Logout)",
    description="Save all training progress data when user logs out. Ensures all progress is encrypted and persisted.",
    responses={
        200: {"description": "Progress saved successfully"},
        401: {"description": "Not authenticated"}
    }
)
async def save_training_on_logout(
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Save all training progress when user logs out.
    
    This endpoint:
    - Saves all training progress to encrypted storage
    - Updates database with latest skill levels
    - Ensures data persistence
    
    Example:
        POST /api/ai/training/logout
        
        Response:
        {
            "status": "success",
            "message": "Training progress saved"
        }
    """
    try:
        training_manager.save_logout_progress(current_user)
        return {
            "status": "success",
            "message": "Training progress saved"
        }
    except Exception as e:
        ote_logger.logger.error(f"Error saving logout progress: {e}", exc_info=True)
        return {
            "status": "error",
            "message": f"Could not save progress: {str(e)}"
        }


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
        # Get the selected model
        from llm_manager import LLMManager
        selected_model = request.model or "gpt-4o-mini"
        
        # Query user fresh from the current session to avoid session conflicts
        user = db.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Determine if we should use custom config based on selected model
        # Custom config is only used if the selected model matches the saved provider
        use_custom_config = False
        if user.llm_provider and user.llm_endpoint:
            # Check if selected model matches the saved provider
            if (user.llm_provider == "lm_studio" and "lm-studio" in selected_model.lower()) or \
               (user.llm_provider == "ollama" and "ollama" in selected_model.lower()) or \
               (user.llm_provider in ["openai", "claude", "gemini"] and user.llm_provider in selected_model.lower()):
                use_custom_config = True
        
        # Use custom LLM configuration if matching provider is selected
        if use_custom_config:
            provider = user.llm_provider
            endpoint = user.llm_endpoint
            model_name = user.llm_model or "local-model"
            
            # Ensure endpoint has /v1 suffix for OpenAI-compatible APIs (LM Studio, Ollama)
            if provider in ['lm_studio', 'ollama']:
                if not endpoint.endswith('/v1'):
                    endpoint = endpoint.rstrip('/') + '/v1'
            
            ote_logger.logger.info(
                f"Using custom LLM config for user {user.id}: "
                f"provider={provider}, endpoint={endpoint}, model={model_name}"
            )
            
            # Initialize LLM with custom endpoint
            if provider in ['lm_studio', 'ollama']:
                # For local models, use base_url parameter
                model_llm = LLMManager.get_llm(
                    provider=provider,
                    model=model_name,
                    temperature=user.temperature or 0.7,
                    base_url=endpoint
                )
            else:
                # For cloud providers (unlikely to have custom endpoint, but support it)
                model_llm = LLMManager.get_llm(
                    provider=provider,
                    model=model_name,
                    temperature=user.temperature or 0.7
                )
        
        # Use default LLM configuration based on selected model
        elif "lm-studio" in selected_model.lower():
            provider = "lm_studio"
            # LM Studio default endpoint
            model_llm = LLMManager.get_llm(
                provider=provider,
                model="local-model",  # LM Studio auto-detects
                temperature=user.temperature or 0.7,
                base_url="http://localhost:1234/v1"  # Default LM Studio port
            )
        elif "ollama" in selected_model.lower():
            provider = "ollama"
            # Ollama default endpoint
            model_llm = LLMManager.get_llm(
                provider=provider,
                model="llama2",  # Default Ollama model
                temperature=user.temperature or 0.7,
                base_url="http://localhost:11434"  # Default Ollama port
            )
        elif "claude" in selected_model.lower():
            provider = "claude"
            model_llm = LLMManager.get_llm(
                provider=provider,
                model=selected_model,
                temperature=user.temperature or 0.7
            )
        elif "gemini" in selected_model.lower():
            provider = "gemini"
            model_llm = LLMManager.get_llm(
                provider=provider,
                model=selected_model,
                temperature=user.temperature or 0.7
            )
        else:
            provider = "openai"
            model_llm = LLMManager.get_llm(
                provider=provider,
                model=selected_model,
                temperature=user.temperature or 0.7
            )
        
        # Create AI agent for this user with selected model
        agent = AiChatagent(user, model_llm)
        
        # Generate request ID for tracing
        request_id = ote_logger.generate_request_id()
        
        # Build graph and process message
        graph = agent.build_graph()
        config = {
            "configurable": {
                "thread_id": request.conversation_id or f"user_{user.id}"
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


# ==================== LLM Configuration Endpoints ====================

@router.get(
    "/llm-config",
    response_model=LLMConfigResponse,
    summary="Get User's LLM Configuration",
    description="Retrieve the current user's custom LLM configuration (provider, endpoint, model)",
)
async def get_llm_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the authenticated user's LLM configuration.
    
    Returns the user's configured LLM provider, custom endpoint (IP:port), 
    and model name. If no configuration is set, returns None values.
    
    **Example Response:**
    ```json
    {
        "user_id": 1,
        "provider": "lm_studio",
        "endpoint": "http://192.168.1.100:1234",
        "model": "llama-3.2"
    }
    ```
    """
    try:
        return LLMConfigResponse(
            user_id=current_user.id,
            provider=current_user.llm_provider,
            endpoint=current_user.llm_endpoint,
            model=current_user.llm_model
        )
    except Exception as e:
        ote_logger.logger.error(f"Error retrieving LLM config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving LLM configuration: {str(e)}"
        )


@router.post(
    "/llm-config",
    response_model=LLMConfigResponse,
    summary="Update User's LLM Configuration",
    description="Set or update the user's custom LLM configuration with IP, port, and provider",
)
async def update_llm_config(
    config: LLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the authenticated user's LLM configuration.
    
    Allows users to configure a custom local LLM endpoint by providing:
    - **provider**: LLM provider (e.g., 'lm_studio', 'ollama', 'openai')
    - **endpoint**: Full URL with IP and port (e.g., 'http://192.168.1.100:1234')
    - **model**: Model name (e.g., 'llama-3.2', 'local-model')
    
    All fields are optional. Providing None will clear the configuration.
    
    **Example Request:**
    ```json
    {
        "provider": "lm_studio",
        "endpoint": "http://192.168.1.100:1234",
        "model": "llama-3.2"
    }
    ```
    
    **Validation:**
    - Endpoint must start with http:// or https://
    - Endpoint must include a port number
    - Provider must be one of: lm_studio, ollama, openai, gemini, claude
    """
    try:
        # Query the user fresh from the current session to avoid session conflicts
        user = db.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user's LLM configuration in the database
        user.llm_provider = config.provider
        user.llm_endpoint = config.endpoint
        user.llm_model = config.model
        
        db.commit()
        db.refresh(user)
        
        ote_logger.logger.info(
            f"LLM config updated for user {user.id}: "
            f"provider={config.provider}, endpoint={config.endpoint}, model={config.model}"
        )
        
        return LLMConfigResponse(
            user_id=user.id,
            provider=user.llm_provider,
            endpoint=user.llm_endpoint,
            model=user.llm_model
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        ote_logger.logger.error(f"Error updating LLM config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating LLM configuration: {str(e)}"
        )


@router.delete(
    "/llm-config",
    summary="Clear User's LLM Configuration",
    description="Remove the user's custom LLM configuration and revert to system defaults",
)
async def delete_llm_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear the authenticated user's LLM configuration.
    
    Removes all custom LLM settings and reverts the user to system default configuration.
    This will clear:
    - Provider setting
    - Custom endpoint (IP:port)
    - Model name
    
    **Example Response:**
    ```json
    {
        "status": "success",
        "message": "LLM configuration cleared successfully"
    }
    ```
    """
    try:
        # Query the user fresh from the current session to avoid session conflicts
        user = db.query(User).filter(User.id == current_user.id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Clear user's LLM configuration
        user.llm_provider = None
        user.llm_endpoint = None
        user.llm_model = None
        
        db.commit()
        
        ote_logger.logger.info(f"LLM config cleared for user {user.id}")
        
        return {
            "status": "success",
            "message": "LLM configuration cleared successfully"
        }
    except Exception as e:
        db.rollback()
        ote_logger.logger.error(f"Error clearing LLM config: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing LLM configuration: {str(e)}"
        )
