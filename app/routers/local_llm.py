"""
Local LLM API Router

PURPOSE: Handle all local LLM (LM Studio/Ollama) operations via backend
LOCATION: app/routers/local_llm.py

Architecture:
- Frontend → Backend API → Local LLM
- No direct browser-to-LLM connections
- All data flows through authenticated API routes

Endpoints:
- GET /api/local-llm/ping - Test backend ↔ LM Studio connection
- GET /api/local-llm/status - Get local LLM status and models
- POST /api/local-llm/chat - Send chat message to local LLM
- GET /api/local-llm/models - List available local models

Observability:
- Request tracing with unique IDs
- Latency metrics
- Connection status monitoring
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.utils import get_logger
from datamanager.data_model import User

logger = get_logger(__name__)

router = APIRouter(prefix="/api/local-llm", tags=["local-llm"])


# ============================================================================
# CONFIGURATION
# ============================================================================

class LocalLLMConfig:
    """Configuration for local LLM connections"""
    
    # Default endpoints
    LM_STUDIO_URL = "http://localhost:1234/v1"
    OLLAMA_URL = "http://localhost:11434/v1"
    
    # Timeouts
    PING_TIMEOUT = 5.0  # seconds
    CHAT_TIMEOUT = 120.0  # seconds
    
    # Default model
    DEFAULT_MODEL = "ibm/granite-4-h-tiny"


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class PingResponse(BaseModel):
    """Response for ping endpoint"""
    success: bool
    message: str
    trace_id: str
    timestamp: str
    latency_ms: float
    endpoint: str
    models_available: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "pong - LM Studio connected",
                "trace_id": "LLM-PING-abc123",
                "timestamp": "2025-12-11T19:00:00",
                "latency_ms": 45.2,
                "endpoint": "http://localhost:1234/v1",
                "models_available": 5
            }
        }


class LocalLLMStatusResponse(BaseModel):
    """Response for status endpoint"""
    available: bool
    endpoint: str
    provider: str
    models: List[str] = []
    current_model: Optional[str] = None
    trace_id: str
    checked_at: str


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class LocalChatRequest(BaseModel):
    """Request for local LLM chat"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello!"}
                ],
                "model": "ibm/granite-4-h-tiny",
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }


class LocalChatResponse(BaseModel):
    """Response for local LLM chat"""
    success: bool
    response: str
    model: str
    trace_id: str
    latency_ms: float
    tokens: Dict[str, int] = {}
    error: Optional[str] = None


class ModelsResponse(BaseModel):
    """Response for models list endpoint"""
    models: List[Dict[str, Any]]
    count: int
    trace_id: str
    endpoint: str


# ============================================================================
# LOCAL LLM CLIENT
# ============================================================================

class LocalLLMClient:
    """
    Backend client for local LLM communication.
    
    All LLM interactions go through this client.
    Provides observability, tracing, and error handling.
    """
    
    def __init__(self, base_url: str = LocalLLMConfig.LM_STUDIO_URL):
        self.base_url = base_url
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=LocalLLMConfig.CHAT_TIMEOUT
        )
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    def _generate_trace_id(self, prefix: str = "LLM") -> str:
        """Generate unique trace ID for observability"""
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
    
    async def ping(self) -> Dict[str, Any]:
        """
        Ping the local LLM server.
        
        Returns:
            Dict with success status, latency, and model count
        """
        trace_id = self._generate_trace_id("PING")
        logger.info(f"[{trace_id}] Pinging local LLM at {self.base_url}")
        
        start_time = time.time()
        try:
            response = await self._client.get(
                "/models",
                timeout=LocalLLMConfig.PING_TIMEOUT
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                
                logger.info(
                    f"[{trace_id}] OBSERVE:ping_success | "
                    f"latency_ms={latency_ms:.2f} | models={len(models)}"
                )
                
                return {
                    "success": True,
                    "message": "pong - LM Studio connected",
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "models_available": len(models)
                }
            else:
                logger.error(f"[{trace_id}] Ping failed: HTTP {response.status_code}")
                return {
                    "success": False,
                    "message": f"LM Studio returned HTTP {response.status_code}",
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "models_available": 0
                }
                
        except httpx.ConnectError as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"[{trace_id}] Connection failed: {e}")
            return {
                "success": False,
                "message": "Connection refused - Is LM Studio running?",
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "models_available": 0
            }
        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"[{trace_id}] Ping timeout after {latency_ms:.2f}ms")
            return {
                "success": False,
                "message": "Connection timeout",
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "models_available": 0
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"[{trace_id}] Unexpected error: {e}")
            return {
                "success": False,
                "message": str(e),
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "models_available": 0
            }
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from local LLM"""
        trace_id = self._generate_trace_id("MODELS")
        logger.info(f"[{trace_id}] Fetching models from {self.base_url}")
        
        try:
            response = await self._client.get("/models", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                logger.info(f"[{trace_id}] OBSERVE:models_fetched | count={len(models)}")
                return models
            return []
        except Exception as e:
            logger.error(f"[{trace_id}] Failed to fetch models: {e}")
            return []
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send chat request to local LLM.
        
        Args:
            messages: List of message dicts with role and content
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            user_id: ID of authenticated user (for logging)
        
        Returns:
            Dict with response, latency, tokens, etc.
        """
        trace_id = self._generate_trace_id("CHAT")
        model = model or LocalLLMConfig.DEFAULT_MODEL
        
        logger.info(
            f"[{trace_id}] Chat request | user_id={user_id} | "
            f"model={model} | messages={len(messages)}"
        )
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        start_time = time.time()
        try:
            response = await self._client.post(
                "/chat/completions",
                json=payload,
                timeout=LocalLLMConfig.CHAT_TIMEOUT
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                
                logger.info(
                    f"[{trace_id}] OBSERVE:chat_success | "
                    f"latency_ms={latency_ms:.2f} | "
                    f"tokens={usage.get('total_tokens', 0)} | "
                    f"response_length={len(content)}"
                )
                
                return {
                    "success": True,
                    "response": content,
                    "model": data.get("model", model),
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "tokens": {
                        "prompt": usage.get("prompt_tokens", 0),
                        "completion": usage.get("completion_tokens", 0),
                        "total": usage.get("total_tokens", 0)
                    },
                    "error": None
                }
            else:
                error_msg = f"LLM returned HTTP {response.status_code}"
                logger.error(f"[{trace_id}] {error_msg}")
                return {
                    "success": False,
                    "response": "",
                    "model": model,
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "tokens": {},
                    "error": error_msg
                }
                
        except httpx.ConnectError:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = "Connection refused - Is LM Studio running?"
            logger.error(f"[{trace_id}] {error_msg}")
            return {
                "success": False,
                "response": "",
                "model": model,
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "tokens": {},
                "error": error_msg
            }
        except httpx.TimeoutException:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Request timeout after {latency_ms:.0f}ms"
            logger.error(f"[{trace_id}] {error_msg}")
            return {
                "success": False,
                "response": "",
                "model": model,
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "tokens": {},
                "error": error_msg
            }
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"[{trace_id}] Unexpected error: {e}")
            return {
                "success": False,
                "response": "",
                "model": model,
                "trace_id": trace_id,
                "latency_ms": latency_ms,
                "tokens": {},
                "error": str(e)
            }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/ping", response_model=PingResponse)
async def ping_local_llm(
    current_user: User = Depends(get_current_user)
):
    """
    Ping the local LLM server to test connection.
    
    Returns:
        PingResponse with connection status and latency
    
    Example response:
        {
            "success": true,
            "message": "pong - LM Studio connected",
            "trace_id": "PING-abc123",
            "timestamp": "2025-12-11T19:00:00",
            "latency_ms": 45.2,
            "endpoint": "http://localhost:1234/v1",
            "models_available": 5
        }
    """
    logger.info(f"Ping request from user {current_user.id} ({current_user.username})")
    
    async with LocalLLMClient() as client:
        result = await client.ping()
        
        return PingResponse(
            success=result["success"],
            message=result["message"],
            trace_id=result["trace_id"],
            timestamp=datetime.now().isoformat(),
            latency_ms=result["latency_ms"],
            endpoint=LocalLLMConfig.LM_STUDIO_URL,
            models_available=result["models_available"]
        )


@router.get("/status", response_model=LocalLLMStatusResponse)
async def get_local_llm_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed status of local LLM connection.
    
    Returns:
        LocalLLMStatusResponse with availability and model list
    """
    trace_id = f"STATUS-{uuid.uuid4().hex[:8]}"
    logger.info(f"[{trace_id}] Status request from user {current_user.id}")
    
    async with LocalLLMClient() as client:
        ping_result = await client.ping()
        models = []
        
        if ping_result["success"]:
            models_data = await client.get_models()
            models = [m.get("id", "unknown") for m in models_data]
        
        return LocalLLMStatusResponse(
            available=ping_result["success"],
            endpoint=LocalLLMConfig.LM_STUDIO_URL,
            provider="lm_studio",
            models=models,
            current_model=LocalLLMConfig.DEFAULT_MODEL if models else None,
            trace_id=trace_id,
            checked_at=datetime.now().isoformat()
        )


@router.get("/models", response_model=ModelsResponse)
async def list_local_models(
    current_user: User = Depends(get_current_user)
):
    """
    List available models from local LLM server.
    
    Returns:
        ModelsResponse with list of available models
    """
    trace_id = f"MODELS-{uuid.uuid4().hex[:8]}"
    logger.info(f"[{trace_id}] Models request from user {current_user.id}")
    
    async with LocalLLMClient() as client:
        models = await client.get_models()
        
        return ModelsResponse(
            models=models,
            count=len(models),
            trace_id=trace_id,
            endpoint=LocalLLMConfig.LM_STUDIO_URL
        )


@router.post("/chat", response_model=LocalChatResponse)
async def chat_with_local_llm(
    request: LocalChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send chat message to local LLM.
    
    All chat requests are authenticated and traced.
    User data is isolated - each user only accesses their own context.
    
    Args:
        request: Chat request with messages, model, and parameters
    
    Returns:
        LocalChatResponse with LLM response and metrics
    """
    logger.info(
        f"Chat request from user {current_user.id} ({current_user.username}) | "
        f"model={request.model} | messages={len(request.messages)}"
    )
    
    # Convert messages to dict format
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    async with LocalLLMClient() as client:
        result = await client.chat(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            user_id=current_user.id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=result["error"]
            )
        
        return LocalChatResponse(
            success=result["success"],
            response=result["response"],
            model=result["model"],
            trace_id=result["trace_id"],
            latency_ms=result["latency_ms"],
            tokens=result["tokens"],
            error=result["error"]
        )


# ============================================================================
# HEALTH CHECK (No auth required for monitoring)
# ============================================================================

@router.get("/health")
async def local_llm_health():
    """
    Health check endpoint for monitoring.
    No authentication required - used by monitoring systems.
    
    Returns:
        Simple health status
    """
    async with LocalLLMClient() as client:
        result = await client.ping()
        
        return {
            "status": "healthy" if result["success"] else "unhealthy",
            "local_llm_connected": result["success"],
            "latency_ms": result["latency_ms"],
            "timestamp": datetime.now().isoformat()
        }
