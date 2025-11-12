"""
O-T-E Logger: Observability, Traceability, Evaluation for AI System

Provides comprehensive logging and metrics for production AI applications.
Follows industry best practices for LLM observability.
"""
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, asdict
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


@dataclass
class AIMetrics:
    """Metrics for AI interaction evaluation."""
    request_id: str
    user_id: int
    timestamp: str
    duration_ms: float
    
    # LLM Metrics
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimate: float
    
    # Tool Metrics
    tools_called: List[str]
    tool_count: int
    duplicate_blocks: int
    
    # Quality Metrics
    success: bool
    error: Optional[str]
    response_length: int
    
    # Traceability
    conversation_id: str
    session_id: str


class OTELogger:
    """
    Observability-Traceability-Evaluation Logger for AI System.
    
    Capabilities:
    - Structured logging with correlation IDs
    - Performance metrics tracking
    - Token usage and cost estimation
    - Tool usage analytics
    - Error tracking and debugging
    - Request tracing across distributed components
    """
    
    def __init__(self, service_name: str = "AI-ChatAgent"):
        """
        Initialize OTE Logger.
        
        Args:
            service_name: Name of the service for identification
        """
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.metrics_buffer: List[AIMetrics] = []
        
        # Cost per 1k tokens (approximate for GPT-4o-mini)
        self.cost_per_1k_prompt = 0.00015  # $0.15 per 1M tokens
        self.cost_per_1k_completion = 0.0006  # $0.60 per 1M tokens
    
    def generate_request_id(self) -> str:
        """Generate unique request ID for tracing."""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    @contextmanager
    def trace_request(self, 
                      request_id: str,
                      user_id: int,
                      operation: str,
                      **metadata):
        """
        Context manager for tracing a request with automatic timing.
        
        Usage:
            with logger.trace_request(req_id, user_id, "chat_completion"):
                # Your code here
                pass
        
        Args:
            request_id: Unique identifier for request
            user_id: User making the request
            operation: Operation being performed
            **metadata: Additional context
        """
        start_time = time.time()
        
        self.logger.info(
            f"🚀 START | {operation}",
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'operation': operation,
                **metadata
            }
        )
        
        try:
            yield
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.info(
                f"✅ SUCCESS | {operation} | {duration_ms:.2f}ms",
                extra={
                    'request_id': request_id,
                    'duration_ms': duration_ms,
                    'success': True
                }
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            self.logger.error(
                f"❌ ERROR | {operation} | {duration_ms:.2f}ms | {str(e)}",
                extra={
                    'request_id': request_id,
                    'duration_ms': duration_ms,
                    'error': str(e),
                    'success': False
                },
                exc_info=True
            )
            raise
    
    def log_llm_call(self,
                     request_id: str,
                     model: str,
                     prompt_tokens: int,
                     completion_tokens: int,
                     duration_ms: float,
                     **metadata):
        """
        Log LLM API call with token usage and cost.
        
        Args:
            request_id: Request identifier
            model: LLM model name
            prompt_tokens: Input tokens
            completion_tokens: Output tokens
            duration_ms: Call duration in milliseconds
            **metadata: Additional context
        """
        total_tokens = prompt_tokens + completion_tokens
        cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
        
        self.logger.info(
            f"🤖 LLM CALL | {model} | "
            f"Tokens: {total_tokens} ({prompt_tokens}→{completion_tokens}) | "
            f"Cost: ${cost:.6f} | {duration_ms:.2f}ms",
            extra={
                'request_id': request_id,
                'event_type': 'llm_call',
                'model': model,
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost,
                'duration_ms': duration_ms,
                **metadata
            }
        )
    
    def log_tool_call(self,
                      request_id: str,
                      tool_name: str,
                      tool_args: Dict[str, Any],
                      duration_ms: float,
                      success: bool,
                      result_preview: str = ""):
        """
        Log tool execution.
        
        Args:
            request_id: Request identifier
            tool_name: Name of tool called
            tool_args: Tool arguments
            duration_ms: Execution duration
            success: Whether tool succeeded
            result_preview: Preview of result (first 100 chars)
        """
        status = "✅" if success else "❌"
        
        self.logger.info(
            f"{status} TOOL | {tool_name} | {duration_ms:.2f}ms",
            extra={
                'request_id': request_id,
                'event_type': 'tool_call',
                'tool_name': tool_name,
                'tool_args': json.dumps(tool_args),
                'duration_ms': duration_ms,
                'success': success,
                'result_preview': result_preview[:100]
            }
        )
    
    def log_duplicate_block(self,
                           request_id: str,
                           tool_name: str,
                           tool_args: Dict[str, Any]):
        """
        Log when a duplicate tool call is blocked.
        
        Args:
            request_id: Request identifier
            tool_name: Tool that was blocked
            tool_args: Arguments that matched
        """
        self.logger.warning(
            f"🛑 DUPLICATE BLOCKED | {tool_name}",
            extra={
                'request_id': request_id,
                'event_type': 'duplicate_block',
                'tool_name': tool_name,
                'tool_args': json.dumps(tool_args)
            }
        )
    
    def log_metrics(self, metrics: AIMetrics):
        """
        Log complete metrics for request.
        
        Args:
            metrics: AIMetrics dataclass with all metrics
        """
        self.metrics_buffer.append(metrics)
        
        self.logger.info(
            f"📊 METRICS | User:{metrics.user_id} | "
            f"{metrics.duration_ms:.2f}ms | "
            f"{metrics.total_tokens} tokens | "
            f"${metrics.cost_estimate:.6f} | "
            f"Tools:{metrics.tool_count}",
            extra={
                'event_type': 'metrics',
                **asdict(metrics)
            }
        )
    
    def log_evaluation(self,
                      request_id: str,
                      user_id: int,
                      quality_score: float,
                      relevance_score: float,
                      empathy_score: float,
                      **metrics):
        """
        Log quality evaluation scores.
        
        Args:
            request_id: Request identifier
            user_id: User ID
            quality_score: Overall quality (0-1)
            relevance_score: Response relevance (0-1)
            empathy_score: Empathy level (0-1)
            **metrics: Additional evaluation metrics
        """
        self.logger.info(
            f"⭐ EVALUATION | Quality:{quality_score:.2f} | "
            f"Relevance:{relevance_score:.2f} | "
            f"Empathy:{empathy_score:.2f}",
            extra={
                'request_id': request_id,
                'user_id': user_id,
                'event_type': 'evaluation',
                'quality_score': quality_score,
                'relevance_score': relevance_score,
                'empathy_score': empathy_score,
                **metrics
            }
        )
    
    def get_metrics_summary(self, last_n: int = 100) -> Dict[str, Any]:
        """
        Get summary statistics for last N requests.
        
        Args:
            last_n: Number of recent requests to analyze
            
        Returns:
            dict: Summary statistics
        """
        if not self.metrics_buffer:
            return {"error": "No metrics available"}
        
        recent = self.metrics_buffer[-last_n:]
        
        return {
            "total_requests": len(recent),
            "success_rate": sum(1 for m in recent if m.success) / len(recent),
            "avg_duration_ms": sum(m.duration_ms for m in recent) / len(recent),
            "total_tokens": sum(m.total_tokens for m in recent),
            "total_cost_usd": sum(m.cost_estimate for m in recent),
            "avg_tokens_per_request": sum(m.total_tokens for m in recent) / len(recent),
            "most_used_tools": self._get_top_tools(recent),
            "duplicate_blocks": sum(m.duplicate_blocks for m in recent),
        }
    
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate estimated cost for token usage based on model.
        
        Args:
            model: Model name (e.g., 'gpt-4o-mini', 'gemini-2.0-flash-exp')
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            
        Returns:
            float: Estimated cost in USD
        """
        # Model-specific pricing (per 1k tokens)
        pricing = {
            # OpenAI models
            'gpt-4o': {'prompt': 0.0025, 'completion': 0.010},
            'gpt-4o-mini': {'prompt': 0.00015, 'completion': 0.0006},
            'gpt-4-turbo': {'prompt': 0.010, 'completion': 0.030},
            'gpt-3.5-turbo': {'prompt': 0.0005, 'completion': 0.0015},
            
            # Gemini models (free tier = $0)
            'gemini-2.0-flash-exp': {'prompt': 0.0, 'completion': 0.0},
            'gemini-1.5-pro': {'prompt': 0.00125, 'completion': 0.005},
            'gemini-1.5-flash': {'prompt': 0.000075, 'completion': 0.0003},
            
            # Claude models
            'claude-3-5-sonnet-20241022': {'prompt': 0.003, 'completion': 0.015},
            'claude-3-opus-20240229': {'prompt': 0.015, 'completion': 0.075},
            'claude-3-sonnet-20240229': {'prompt': 0.003, 'completion': 0.015},
        }
        
        # Get pricing for model (default to gpt-4o-mini if unknown)
        model_pricing = pricing.get(model, pricing['gpt-4o-mini'])
        
        prompt_cost = (prompt_tokens / 1000) * model_pricing['prompt']
        completion_cost = (completion_tokens / 1000) * model_pricing['completion']
        
        return prompt_cost + completion_cost
    
    def _get_top_tools(self, metrics: List[AIMetrics], top_n: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently used tools."""
        tool_counts = {}
        for m in metrics:
            for tool in m.tools_called:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"tool": tool, "count": count} for tool, count in sorted_tools[:top_n]]


# Global logger instance
ote_logger = OTELogger()


# Convenience functions
def get_logger() -> OTELogger:
    """Get global OTE logger instance."""
    return ote_logger


def create_metrics(
    request_id: str,
    user_id: int,
    duration_ms: float,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    tools_called: List[str],
    duplicate_blocks: int = 0,
    success: bool = True,
    error: Optional[str] = None,
    response_length: int = 0,
    conversation_id: str = "",
    session_id: str = ""
) -> AIMetrics:
    """
    Factory function to create AIMetrics.
    
    Returns:
        AIMetrics: Complete metrics object
    """
    total_tokens = prompt_tokens + completion_tokens
    cost = ote_logger._calculate_cost(prompt_tokens, completion_tokens)
    
    return AIMetrics(
        request_id=request_id,
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        duration_ms=duration_ms,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost_estimate=cost,
        tools_called=tools_called,
        tool_count=len(tools_called),
        duplicate_blocks=duplicate_blocks,
        success=success,
        error=error,
        response_length=response_length,
        conversation_id=conversation_id,
        session_id=session_id
    )
