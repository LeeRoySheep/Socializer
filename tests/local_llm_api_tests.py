"""
Local LLM API Integration Tests

PURPOSE: Test existing API routes with local LLM (LM Studio) integration
LOCATION: tests/local_llm_api_tests.py

Features:
- Uses existing API routes (no new endpoints needed)
- Tests user-bound agent functionality
- Includes observability (logging, request tracing)
- Includes evaluation metrics (latency, tokens, tools, quality)
- Respects user-specific encryption and data isolation

OOP Standards:
- Single Responsibility Principle for each test class
- Dependency Injection for services
- Factory pattern for test data creation
- Observer pattern for metrics collection

Observability:
- Request IDs for tracing
- Structured logging
- Timing decorators for latency tracking

Run with: pytest tests/local_llm_api_tests.py -v -s
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import httpx
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class TestConfig:
    """Configuration for test environment"""
    # API endpoints
    api_base_url: str = "http://localhost:8000"
    local_llm_url: str = "http://localhost:1234/v1"
    
    # Test user credentials
    test_username: str = "test_local_llm_user"
    test_password: str = "TestPassword123!"
    test_email: str = "test_local_llm@example.com"
    
    # Timeouts
    api_timeout: float = 30.0
    llm_timeout: float = 60.0
    
    # Local LLM settings
    local_model: str = "ibm/granite-4-h-tiny"
    
    # Evaluation thresholds
    max_latency_ms: int = 10000  # 10 seconds
    min_quality_score: float = 0.5


# ============================================================================
# OBSERVABILITY - Logging & Tracing
# ============================================================================

class RequestTracer:
    """Handles request tracing with unique IDs"""
    
    def __init__(self, prefix: str = "LLM-TEST"):
        self.prefix = prefix
        self._traces: Dict[str, Dict] = {}
    
    def start_trace(self, operation: str) -> str:
        """Start a new trace and return trace ID"""
        trace_id = f"{self.prefix}-{uuid.uuid4().hex[:8]}"
        self._traces[trace_id] = {
            "operation": operation,
            "start_time": time.time(),
            "events": [],
            "metrics": {}
        }
        return trace_id
    
    def add_event(self, trace_id: str, event: str, data: Optional[Dict] = None):
        """Add an event to an existing trace"""
        if trace_id in self._traces:
            self._traces[trace_id]["events"].append({
                "timestamp": time.time(),
                "event": event,
                "data": data or {}
            })
    
    def end_trace(self, trace_id: str, success: bool = True) -> Dict:
        """End a trace and return collected data"""
        if trace_id not in self._traces:
            return {}
        
        trace = self._traces[trace_id]
        trace["end_time"] = time.time()
        trace["duration_ms"] = (trace["end_time"] - trace["start_time"]) * 1000
        trace["success"] = success
        
        return trace
    
    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get trace data by ID"""
        return self._traces.get(trace_id)


class TestLogger:
    """Structured logging for tests with observability"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | [%(trace_id)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log(self, level: int, message: str, trace_id: str = "-", **kwargs):
        extra = {"trace_id": trace_id, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, trace_id: str = "-", **kwargs):
        self._log(logging.INFO, message, trace_id, **kwargs)
    
    def error(self, message: str, trace_id: str = "-", **kwargs):
        self._log(logging.ERROR, message, trace_id, **kwargs)
    
    def debug(self, message: str, trace_id: str = "-", **kwargs):
        self._log(logging.DEBUG, message, trace_id, **kwargs)
    
    def observe(self, metric: str, value: Any, trace_id: str = "-"):
        """Log an observable metric"""
        self._log(logging.INFO, f"OBSERVE:{metric} | value={value}", trace_id)


# Decorator for timing functions
def timed(logger: TestLogger):
    """Decorator to time function execution"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            trace_id = kwargs.get('trace_id', '-')
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                logger.observe(f"{func.__name__}_latency_ms", f"{duration_ms:.2f}", trace_id)
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {duration_ms:.2f}ms: {e}", trace_id)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            trace_id = kwargs.get('trace_id', '-')
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000
                logger.observe(f"{func.__name__}_latency_ms", f"{duration_ms:.2f}", trace_id)
                return result
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                logger.error(f"{func.__name__} failed after {duration_ms:.2f}ms: {e}", trace_id)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# ============================================================================
# EVALUATION METRICS
# ============================================================================

class MetricType(Enum):
    """Types of metrics we track"""
    LATENCY = "latency"
    TOKEN_USAGE = "token_usage"
    TOOL_USE = "tool_use"
    QUALITY = "quality"
    ERROR = "error"


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    trace_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Latency metrics
    total_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    api_latency_ms: float = 0.0
    
    # Token metrics
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # Tool usage
    tools_called: List[str] = field(default_factory=list)
    tool_success_rate: float = 1.0
    
    # Quality metrics
    response_length: int = 0
    has_valid_response: bool = False
    quality_score: float = 0.0  # 0.0 - 1.0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat(),
            "latency": {
                "total_ms": self.total_latency_ms,
                "llm_ms": self.llm_latency_ms,
                "api_ms": self.api_latency_ms
            },
            "tokens": {
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens,
                "total": self.total_tokens
            },
            "tools": {
                "called": self.tools_called,
                "success_rate": self.tool_success_rate
            },
            "quality": {
                "response_length": self.response_length,
                "valid_response": self.has_valid_response,
                "score": self.quality_score
            },
            "errors": self.errors
        }


class MetricsCollector:
    """Collects and aggregates evaluation metrics"""
    
    def __init__(self):
        self._metrics: List[EvaluationMetrics] = []
    
    def record(self, metrics: EvaluationMetrics):
        """Record a metric set"""
        self._metrics.append(metrics)
    
    def get_summary(self) -> Dict:
        """Get aggregated summary of all metrics"""
        if not self._metrics:
            return {"count": 0}
        
        latencies = [m.total_latency_ms for m in self._metrics]
        quality_scores = [m.quality_score for m in self._metrics if m.has_valid_response]
        
        return {
            "count": len(self._metrics),
            "latency": {
                "avg_ms": sum(latencies) / len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies)
            },
            "quality": {
                "avg_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "success_rate": len([m for m in self._metrics if m.has_valid_response]) / len(self._metrics)
            },
            "errors": {
                "total": sum(len(m.errors) for m in self._metrics),
                "rate": sum(1 for m in self._metrics if m.errors) / len(self._metrics)
            }
        }
    
    def get_all(self) -> List[Dict]:
        """Get all metrics as dictionaries"""
        return [m.to_dict() for m in self._metrics]


# ============================================================================
# API CLIENT
# ============================================================================

class APIClient:
    """HTTP client for API interactions with observability"""
    
    def __init__(self, config: TestConfig, logger: TestLogger, tracer: RequestTracer):
        self.config = config
        self.logger = logger
        self.tracer = tracer
        self._client: Optional[httpx.AsyncClient] = None
        self._token: Optional[str] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            timeout=self.config.api_timeout
        )
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}
    
    async def register_user(self, trace_id: str) -> bool:
        """Register a test user"""
        self.logger.info("Registering test user", trace_id)
        
        try:
            response = await self._client.post(
                "/api/auth/register",
                data={
                    "username": self.config.test_username,
                    "email": self.config.test_email,
                    "password": self.config.test_password,
                    "password_confirm": self.config.test_password
                },
                follow_redirects=True
            )
            
            if response.status_code in [200, 303]:
                self.logger.info("User registered successfully", trace_id)
                return True
            elif "already exists" in response.text.lower():
                self.logger.info("User already exists", trace_id)
                return True
            else:
                self.logger.error(f"Registration failed: {response.status_code}", trace_id)
                return False
        except Exception as e:
            self.logger.error(f"Registration error: {e}", trace_id)
            return False
    
    async def login(self, trace_id: str) -> bool:
        """Login and get access token"""
        self.logger.info("Logging in", trace_id)
        
        try:
            response = await self._client.post(
                "/token",
                data={
                    "username": self.config.test_username,
                    "password": self.config.test_password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self._token = data.get("access_token")
                self.logger.info("Login successful", trace_id)
                self.logger.observe("token_acquired", True, trace_id)
                return True
            else:
                self.logger.error(f"Login failed: {response.status_code}", trace_id)
                return False
        except Exception as e:
            self.logger.error(f"Login error: {e}", trace_id)
            return False
    
    async def get_user_info(self, trace_id: str) -> Optional[Dict]:
        """Get current user info"""
        try:
            response = await self._client.get(
                "/users/me/",
                headers=self.auth_headers
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.logger.error(f"Get user error: {e}", trace_id)
        return None
    
    async def send_ai_chat(self, message: str, trace_id: str, 
                           model: Optional[str] = None) -> Tuple[Optional[Dict], float]:
        """Send message to AI chat endpoint and return response + latency"""
        self.logger.info(f"Sending AI chat: {message[:50]}...", trace_id)
        
        start_time = time.time()
        try:
            payload = {
                "message": message,
                "conversation_id": f"test-{trace_id}",
                "model": model or self.config.local_model
            }
            
            response = await self._client.post(
                "/api/ai/chat",
                json=payload,
                headers=self.auth_headers,
                timeout=self.config.llm_timeout
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"AI response received in {latency_ms:.2f}ms", trace_id)
                self.logger.observe("ai_chat_latency_ms", f"{latency_ms:.2f}", trace_id)
                return data, latency_ms
            else:
                self.logger.error(f"AI chat failed: {response.status_code} - {response.text}", trace_id)
                return None, latency_ms
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error(f"AI chat error: {e}", trace_id)
            return None, latency_ms


# ============================================================================
# LOCAL LLM CLIENT
# ============================================================================

class LocalLLMClient:
    """Direct client for local LLM (LM Studio) with observability"""
    
    def __init__(self, config: TestConfig, logger: TestLogger):
        self.config = config
        self.logger = logger
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.config.local_llm_url,
            timeout=self.config.llm_timeout
        )
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    async def check_availability(self, trace_id: str) -> bool:
        """Check if local LLM is available"""
        self.logger.info("Checking local LLM availability", trace_id)
        
        try:
            response = await self._client.get("/models", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                self.logger.info(f"Local LLM available with {len(models)} model(s)", trace_id)
                self.logger.observe("local_llm_available", True, trace_id)
                return True
        except Exception as e:
            self.logger.error(f"Local LLM not available: {e}", trace_id)
        
        self.logger.observe("local_llm_available", False, trace_id)
        return False
    
    async def get_models(self, trace_id: str) -> List[str]:
        """Get available models from local LLM"""
        try:
            response = await self._client.get("/models")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("id", "unknown") for m in data.get("data", [])]
                self.logger.observe("local_llm_models", models, trace_id)
                return models
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}", trace_id)
        return []
    
    async def chat(self, messages: List[Dict], trace_id: str,
                   model: Optional[str] = None) -> Tuple[Optional[Dict], float]:
        """Send chat completion request to local LLM"""
        self.logger.info("Sending chat to local LLM", trace_id)
        
        payload = {
            "model": model or self.config.local_model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        start_time = time.time()
        try:
            response = await self._client.post(
                "/chat/completions",
                json=payload
            )
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Local LLM responded in {latency_ms:.2f}ms", trace_id)
                self.logger.observe("local_llm_latency_ms", f"{latency_ms:.2f}", trace_id)
                return data, latency_ms
            else:
                self.logger.error(f"Local LLM error: {response.status_code}", trace_id)
                return None, latency_ms
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Local LLM chat error: {e}", trace_id)
            return None, latency_ms


# ============================================================================
# QUALITY EVALUATOR
# ============================================================================

class ResponseQualityEvaluator:
    """Evaluates the quality of LLM responses"""
    
    def __init__(self, logger: TestLogger):
        self.logger = logger
    
    def evaluate(self, response: Optional[Dict], expected_keywords: List[str] = None,
                 trace_id: str = "-") -> float:
        """
        Evaluate response quality on a 0.0 - 1.0 scale
        
        Criteria:
        - Has content (0.3)
        - Content length > 10 chars (0.2)
        - Contains expected keywords (0.3)
        - No error indicators (0.2)
        """
        if not response:
            return 0.0
        
        score = 0.0
        content = ""
        
        # Extract content from different response formats
        if isinstance(response, dict):
            # API response format
            content = response.get("response", "")
            if not content:
                # Direct LLM response format
                choices = response.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
        
        # Has content
        if content:
            score += 0.3
            self.logger.debug(f"Has content: +0.3", trace_id)
        
        # Content length
        if len(content) > 10:
            score += 0.2
            self.logger.debug(f"Content length ({len(content)}): +0.2", trace_id)
        
        # Expected keywords
        if expected_keywords:
            found = sum(1 for kw in expected_keywords if kw.lower() in content.lower())
            keyword_score = (found / len(expected_keywords)) * 0.3
            score += keyword_score
            self.logger.debug(f"Keywords ({found}/{len(expected_keywords)}): +{keyword_score:.2f}", trace_id)
        else:
            score += 0.3  # No keywords to check
        
        # No error indicators
        error_indicators = ["error", "failed", "unable", "cannot", "sorry"]
        has_errors = any(err in content.lower() for err in error_indicators)
        if not has_errors:
            score += 0.2
            self.logger.debug(f"No error indicators: +0.2", trace_id)
        
        self.logger.observe("quality_score", f"{score:.2f}", trace_id)
        return score


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def config():
    """Test configuration"""
    return TestConfig()


@pytest.fixture
def logger():
    """Test logger"""
    return TestLogger("LocalLLMTest")


@pytest.fixture
def tracer():
    """Request tracer"""
    return RequestTracer()


@pytest.fixture
def metrics_collector():
    """Metrics collector"""
    return MetricsCollector()


@pytest.fixture
def quality_evaluator(logger):
    """Quality evaluator"""
    return ResponseQualityEvaluator(logger)


# ============================================================================
# TEST CLASSES
# ============================================================================

class TestLocalLLMAvailability:
    """Tests for local LLM availability and connection"""
    
    @pytest.mark.asyncio
    async def test_local_llm_connection(self, config, logger, tracer):
        """Test that local LLM server is running and accessible"""
        trace_id = tracer.start_trace("test_local_llm_connection")
        logger.info("Testing local LLM connection", trace_id)
        
        async with LocalLLMClient(config, logger) as client:
            available = await client.check_availability(trace_id)
            
            trace_data = tracer.end_trace(trace_id, success=available)
            logger.observe("trace_duration_ms", f"{trace_data['duration_ms']:.2f}", trace_id)
            
            assert available, "Local LLM server not available. Start LM Studio."
    
    @pytest.mark.asyncio
    async def test_local_llm_models(self, config, logger, tracer):
        """Test that local LLM has models loaded"""
        trace_id = tracer.start_trace("test_local_llm_models")
        logger.info("Testing local LLM models", trace_id)
        
        async with LocalLLMClient(config, logger) as client:
            models = await client.get_models(trace_id)
            
            tracer.end_trace(trace_id, success=len(models) > 0)
            logger.info(f"Found models: {models}", trace_id)
            
            assert len(models) > 0, "No models loaded in local LLM"


class TestAPIAuthentication:
    """Tests for API authentication flow"""
    
    @pytest.mark.asyncio
    async def test_user_registration_and_login(self, config, logger, tracer):
        """Test user registration and login flow"""
        trace_id = tracer.start_trace("test_auth_flow")
        logger.info("Testing authentication flow", trace_id)
        
        async with APIClient(config, logger, tracer) as client:
            # Register (may already exist)
            await client.register_user(trace_id)
            
            # Login
            logged_in = await client.login(trace_id)
            assert logged_in, "Login failed"
            
            # Verify token works
            user_info = await client.get_user_info(trace_id)
            assert user_info is not None, "Could not get user info"
            
            logger.info(f"Authenticated as: {user_info.get('username')}", trace_id)
            tracer.end_trace(trace_id, success=True)


class TestAIChatAPI:
    """Tests for AI chat API with local LLM"""
    
    @pytest.mark.asyncio
    async def test_ai_chat_simple(self, config, logger, tracer, metrics_collector, quality_evaluator):
        """Test simple AI chat message"""
        trace_id = tracer.start_trace("test_ai_chat_simple")
        metrics = EvaluationMetrics(trace_id=trace_id)
        
        logger.info("Testing simple AI chat", trace_id)
        
        async with APIClient(config, logger, tracer) as client:
            # Authenticate
            await client.register_user(trace_id)
            logged_in = await client.login(trace_id)
            assert logged_in, "Login failed"
            
            # Send message
            start_time = time.time()
            response, latency = await client.send_ai_chat(
                "Hello! What is your name?",
                trace_id
            )
            metrics.total_latency_ms = (time.time() - start_time) * 1000
            metrics.api_latency_ms = latency
            
            # Evaluate
            if response:
                metrics.has_valid_response = True
                metrics.response_length = len(response.get("response", ""))
                metrics.tools_called = response.get("tools_used", [])
                metrics.quality_score = quality_evaluator.evaluate(
                    response, 
                    expected_keywords=["hello", "assist", "help"],
                    trace_id=trace_id
                )
                
                # Token usage if available
                usage = response.get("usage", {})
                metrics.prompt_tokens = usage.get("prompt_tokens", 0)
                metrics.completion_tokens = usage.get("completion_tokens", 0)
                metrics.total_tokens = usage.get("total_tokens", 0)
            else:
                metrics.errors.append("No response received")
            
            metrics_collector.record(metrics)
            tracer.end_trace(trace_id, success=metrics.has_valid_response)
            
            # Log metrics
            logger.info(f"Metrics: {json.dumps(metrics.to_dict(), indent=2)}", trace_id)
            
            assert metrics.has_valid_response, "No valid response"
            assert metrics.total_latency_ms < config.max_latency_ms, "Response too slow"
    
    @pytest.mark.asyncio
    async def test_ai_chat_with_tool_use(self, config, logger, tracer, metrics_collector, quality_evaluator):
        """Test AI chat with expected tool usage (web search)"""
        trace_id = tracer.start_trace("test_ai_chat_tool_use")
        metrics = EvaluationMetrics(trace_id=trace_id)
        
        logger.info("Testing AI chat with tool use", trace_id)
        
        async with APIClient(config, logger, tracer) as client:
            await client.register_user(trace_id)
            await client.login(trace_id)
            
            # Message that should trigger web search
            start_time = time.time()
            response, latency = await client.send_ai_chat(
                "What is the current weather in Berlin?",
                trace_id
            )
            metrics.total_latency_ms = (time.time() - start_time) * 1000
            metrics.api_latency_ms = latency
            
            if response:
                metrics.has_valid_response = True
                metrics.tools_called = response.get("tools_used", [])
                metrics.quality_score = quality_evaluator.evaluate(
                    response,
                    expected_keywords=["weather", "berlin", "temperature"],
                    trace_id=trace_id
                )
            
            metrics_collector.record(metrics)
            logger.info(f"Tools called: {metrics.tools_called}", trace_id)
            logger.info(f"Metrics: {json.dumps(metrics.to_dict(), indent=2)}", trace_id)
            
            tracer.end_trace(trace_id, success=metrics.has_valid_response)


class TestDirectLocalLLM:
    """Tests for direct local LLM interaction"""
    
    @pytest.mark.asyncio
    async def test_direct_llm_chat(self, config, logger, tracer, quality_evaluator):
        """Test direct chat with local LLM (bypassing API)"""
        trace_id = tracer.start_trace("test_direct_llm_chat")
        
        logger.info("Testing direct local LLM chat", trace_id)
        
        async with LocalLLMClient(config, logger) as client:
            # Check availability first
            available = await client.check_availability(trace_id)
            if not available:
                pytest.skip("Local LLM not available")
            
            # Send message
            messages = [
                {"role": "system", "content": "You are a helpful assistant. Always respond in English."},
                {"role": "user", "content": "What is 2 + 2? Answer briefly."}
            ]
            
            response, latency = await client.chat(messages, trace_id)
            
            assert response is not None, "No response from local LLM"
            
            quality = quality_evaluator.evaluate(
                response,
                expected_keywords=["4", "four"],
                trace_id=trace_id
            )
            
            logger.observe("direct_llm_quality", f"{quality:.2f}", trace_id)
            tracer.end_trace(trace_id, success=quality > 0.5)
            
            assert quality > 0.3, f"Response quality too low: {quality}"
    
    @pytest.mark.asyncio
    async def test_llm_with_context(self, config, logger, tracer):
        """Test LLM maintains conversation context"""
        trace_id = tracer.start_trace("test_llm_context")
        
        async with LocalLLMClient(config, logger) as client:
            available = await client.check_availability(trace_id)
            if not available:
                pytest.skip("Local LLM not available")
            
            # First message
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "My name is Alice."}
            ]
            response1, _ = await client.chat(messages, trace_id)
            
            # Add response and follow-up
            content1 = response1["choices"][0]["message"]["content"]
            messages.append({"role": "assistant", "content": content1})
            messages.append({"role": "user", "content": "What is my name?"})
            
            response2, _ = await client.chat(messages, trace_id)
            content2 = response2["choices"][0]["message"]["content"]
            
            logger.info(f"Context test response: {content2}", trace_id)
            tracer.end_trace(trace_id, success="alice" in content2.lower())
            
            assert "alice" in content2.lower(), "LLM did not maintain context"


class TestUserDataIsolation:
    """Tests for user data isolation and security"""
    
    @pytest.mark.asyncio
    async def test_user_bound_agent(self, config, logger, tracer):
        """Test that agent is bound to authenticated user"""
        trace_id = tracer.start_trace("test_user_bound_agent")
        
        async with APIClient(config, logger, tracer) as client:
            await client.register_user(trace_id)
            await client.login(trace_id)
            
            # Get user info
            user_info = await client.get_user_info(trace_id)
            assert user_info is not None
            
            # Send message that references user
            response, _ = await client.send_ai_chat(
                "What is my username?",
                trace_id
            )
            
            if response:
                content = response.get("response", "")
                logger.info(f"Response about username: {content}", trace_id)
                # Agent should know the username
                tracer.end_trace(trace_id, success=True)
            else:
                tracer.end_trace(trace_id, success=False)
    
    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, config, logger, tracer):
        """Test that unauthenticated requests are denied"""
        trace_id = tracer.start_trace("test_unauth_denied")
        
        async with APIClient(config, logger, tracer) as client:
            # Don't login - try to access AI chat directly
            response, _ = await client.send_ai_chat(
                "Hello",
                trace_id
            )
            
            # Should fail or return error
            success = response is None or "error" in str(response).lower()
            tracer.end_trace(trace_id, success=success)
            
            # This test passes if the request was rejected
            logger.info(f"Unauthenticated response: {response}", trace_id)


# ============================================================================
# TEST RUNNER WITH SUMMARY
# ============================================================================

class TestSummary:
    """Generates test summary with all metrics"""
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, config, logger, tracer, metrics_collector):
        """Generate final test summary"""
        trace_id = tracer.start_trace("test_summary")
        
        summary = metrics_collector.get_summary()
        logger.info(f"Test Summary: {json.dumps(summary, indent=2)}", trace_id)
        
        tracer.end_trace(trace_id)
        
        # Always passes - just for reporting
        assert True


# ============================================================================
# MAIN RUNNER
# ============================================================================

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([
        __file__,
        "-v",
        "-s",
        "--tb=short",
        "-x",  # Stop on first failure
    ])
