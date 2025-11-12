"""
LLM Provider Manager - Smart Multi-Provider Management with Automatic Fallback
===============================================================================

This module provides a robust, production-ready system for managing multiple
LLM providers with automatic failover, quota management, and error handling.

Features:
---------
1. **Multi-Provider Support**: OpenAI, Gemini, Claude, Local models
2. **Automatic Fallback**: Switch providers on quota/error
3. **Rate Limiting**: Prevent quota exhaustion
4. **Usage Tracking**: Monitor costs and requests
5. **OOP Design**: Clean, testable, maintainable code

Author: Socializer Development Team
Date: 2024-11-12
"""

import os
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ProviderType(Enum):
    """
    Enumeration of supported LLM providers.
    
    Using Enum ensures type safety and prevents typos.
    """
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"


@dataclass
class ProviderConfig:
    """
    Configuration for a specific LLM provider.
    
    Attributes:
        name: Provider name (openai, gemini, etc.)
        model: Model identifier
        api_key: API key (None for local models)
        endpoint: API endpoint URL (for local/custom endpoints)
        max_requests_per_minute: Rate limit
        max_tokens: Maximum output tokens
        temperature: Sampling temperature (0-1)
        is_available: Whether provider is currently available
        priority: Priority order (lower = higher priority)
    """
    name: str
    model: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    max_requests_per_minute: int = 60
    max_tokens: int = 4096
    temperature: float = 0.7
    is_available: bool = True
    priority: int = 0
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_requests_per_minute <= 0:
            raise ValueError("max_requests_per_minute must be positive")
        if not 0 <= self.temperature <= 1:
            raise ValueError("temperature must be between 0 and 1")


@dataclass
class UsageStats:
    """
    Track usage statistics for a provider.
    
    Attributes:
        total_requests: Total API requests made
        successful_requests: Successful requests
        failed_requests: Failed requests
        total_tokens: Total tokens consumed
        total_cost: Estimated total cost in USD
        last_request_time: Timestamp of last request
        error_count: Count of consecutive errors
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_request_time: Optional[datetime] = None
    error_count: int = 0
    
    def record_success(self, tokens: int, cost: float):
        """Record a successful request."""
        self.total_requests += 1
        self.successful_requests += 1
        self.total_tokens += tokens
        self.total_cost += cost
        self.last_request_time = datetime.now()
        self.error_count = 0  # Reset error count on success
    
    def record_failure(self):
        """Record a failed request."""
        self.total_requests += 1
        self.failed_requests += 1
        self.error_count += 1
        self.last_request_time = datetime.now()
    
    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100


class RateLimiter:
    """
    Token-bucket rate limiter for API calls.
    
    Prevents quota exhaustion by enforcing request rate limits.
    Thread-safe and efficient.
    
    Attributes:
        max_requests: Maximum requests per time window
        time_window: Time window in seconds
        requests: Queue of recent request timestamps
    """
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 60s = 1 minute)
        
        Raises:
            ValueError: If max_requests or time_window are invalid
        """
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if time_window <= 0:
            raise ValueError("time_window must be positive")
        
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
    
    def wait_if_needed(self) -> float:
        """
        Block if necessary to respect rate limits.
        
        Returns:
            float: Seconds waited (0 if no wait needed)
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Remove requests outside the time window
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        
        # Check if we need to wait
        if len(self.requests) >= self.max_requests:
            oldest_request = self.requests[0]
            wait_until = oldest_request + timedelta(seconds=self.time_window)
            wait_time = (wait_until - now).total_seconds()
            
            if wait_time > 0:
                print(f"⏱️  Rate limit: waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                # Clean up again after waiting
                now = datetime.now()
                cutoff = now - timedelta(seconds=self.time_window)
                while self.requests and self.requests[0] < cutoff:
                    self.requests.popleft()
                
                self.requests.append(now)
                return wait_time
        
        # Record this request
        self.requests.append(now)
        return 0.0
    
    def can_proceed(self) -> bool:
        """
        Check if a request can proceed without waiting.
        
        Returns:
            bool: True if request can proceed immediately
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Count requests in window
        active_requests = sum(1 for req_time in self.requests if req_time > cutoff)
        return active_requests < self.max_requests
    
    def reset(self):
        """Clear all request history."""
        self.requests.clear()


class LLMProviderManager:
    """
    Intelligent multi-provider LLM manager with automatic fallback.
    
    This class manages multiple LLM providers, handles automatic failover,
    implements rate limiting, tracks usage, and provides a unified interface.
    
    Design Pattern: Strategy Pattern with Fallback Chain
    
    Example:
        ```python
        manager = LLMProviderManager()
        
        # Add providers in priority order
        manager.add_provider("openai", "gpt-4o-mini", priority=1)
        manager.add_provider("gemini", "gemini-2.0-flash-exp", priority=2)
        
        # Get LLM with automatic fallback
        llm = manager.get_llm()
        response = llm.invoke("Hello!")
        ```
    
    Attributes:
        providers: Dictionary of configured providers
        rate_limiters: Rate limiters for each provider
        usage_stats: Usage statistics for each provider
        current_provider: Currently active provider name
        fallback_enabled: Whether automatic fallback is enabled
    """
    
    def __init__(self, fallback_enabled: bool = True):
        """
        Initialize the provider manager.
        
        Args:
            fallback_enabled: Enable automatic fallback on errors
        """
        self.providers: Dict[str, ProviderConfig] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.usage_stats: Dict[str, UsageStats] = {}
        self.current_provider: Optional[str] = None
        self.fallback_enabled = fallback_enabled
        
        # Load default configuration
        self._load_default_providers()
    
    def _load_default_providers(self):
        """Load providers from environment variables and config."""
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.add_provider(
                name=ProviderType.OPENAI.value,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=openai_key,
                max_requests_per_minute=60,
                priority=1
            )
        
        # Gemini
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            self.add_provider(
                name=ProviderType.GEMINI.value,
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
                api_key=gemini_key,
                max_requests_per_minute=15,  # Free tier limit
                priority=2
            )
        
        # Claude
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key:
            self.add_provider(
                name=ProviderType.CLAUDE.value,
                model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                api_key=claude_key,
                max_requests_per_minute=50,
                priority=3
            )
    
    def add_provider(
        self,
        name: str,
        model: str,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        max_requests_per_minute: int = 60,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        priority: int = 0
    ) -> None:
        """
        Add a new provider to the manager.
        
        Args:
            name: Provider name (openai, gemini, etc.)
            model: Model identifier
            api_key: API key (optional for local models)
            endpoint: Custom endpoint URL (optional)
            max_requests_per_minute: Rate limit
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            priority: Priority order (lower = higher priority)
        
        Raises:
            ValueError: If provider configuration is invalid
        """
        config = ProviderConfig(
            name=name,
            model=model,
            api_key=api_key,
            endpoint=endpoint,
            max_requests_per_minute=max_requests_per_minute,
            max_tokens=max_tokens,
            temperature=temperature,
            priority=priority,
            is_available=bool(api_key) if api_key else True
        )
        
        self.providers[name] = config
        self.rate_limiters[name] = RateLimiter(
            max_requests=max_requests_per_minute,
            time_window=60
        )
        self.usage_stats[name] = UsageStats()
        
        print(f"✅ Added provider: {name} (model: {model}, priority: {priority})")
    
    def get_llm(
        self,
        provider_name: Optional[str] = None,
        **kwargs
    ):
        """
        Get an LLM instance with automatic fallback.
        
        Args:
            provider_name: Specific provider to use (None = auto-select)
            **kwargs: Additional arguments to pass to the LLM
        
        Returns:
            LLM instance ready for use
        
        Raises:
            RuntimeError: If no providers are available
        """
        # Get providers in priority order
        sorted_providers = self._get_providers_by_priority()
        
        if not sorted_providers:
            raise RuntimeError("No LLM providers configured")
        
        # Try specific provider if requested
        if provider_name and provider_name in self.providers:
            sorted_providers = [self.providers[provider_name]] + [
                p for p in sorted_providers if p.name != provider_name
            ]
        
        # Try each provider
        last_error = None
        for provider in sorted_providers:
            if not provider.is_available:
                continue
            
            try:
                # Apply rate limiting
                rate_limiter = self.rate_limiters[provider.name]
                rate_limiter.wait_if_needed()
                
                # Create LLM instance
                llm = self._create_llm_instance(provider, **kwargs)
                self.current_provider = provider.name
                
                return llm
                
            except Exception as e:
                last_error = e
                self.usage_stats[provider.name].record_failure()
                
                # Mark as unavailable if too many errors
                if self.usage_stats[provider.name].error_count >= 3:
                    provider.is_available = False
                    print(f"⚠️  Provider {provider.name} marked unavailable after 3 errors")
                
                if not self.fallback_enabled:
                    raise
                
                print(f"⚠️  Provider {provider.name} failed: {e}")
                print(f"🔄 Trying next provider...")
                continue
        
        # All providers failed
        raise RuntimeError(
            f"All LLM providers failed. Last error: {last_error}"
        )
    
    def _create_llm_instance(self, provider: ProviderConfig, **kwargs):
        """
        Create an LLM instance for the given provider.
        
        Args:
            provider: Provider configuration
            **kwargs: Additional LLM arguments
        
        Returns:
            LLM instance
        
        Raises:
            ImportError: If required package not installed
            ValueError: If provider type not supported
        """
        # Merge kwargs with provider defaults
        llm_kwargs = {
            "temperature": provider.temperature,
            "max_tokens": provider.max_tokens,
            **kwargs
        }
        
        if provider.name == ProviderType.OPENAI.value:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=provider.model,
                api_key=provider.api_key,
                **llm_kwargs
            )
        
        elif provider.name == ProviderType.GEMINI.value:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=provider.model,
                google_api_key=provider.api_key,
                **llm_kwargs
            )
        
        elif provider.name == ProviderType.CLAUDE.value:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=provider.model,
                anthropic_api_key=provider.api_key,
                **llm_kwargs
            )
        
        elif provider.name == ProviderType.LM_STUDIO.value:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=provider.model,
                base_url=provider.endpoint or "http://localhost:1234/v1",
                api_key="not-needed",
                **llm_kwargs
            )
        
        elif provider.name == ProviderType.OLLAMA.value:
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(
                model=provider.model,
                base_url=provider.endpoint or "http://localhost:11434",
                **llm_kwargs
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider.name}")
    
    def _get_providers_by_priority(self) -> List[ProviderConfig]:
        """
        Get list of providers sorted by priority.
        
        Returns:
            List of ProviderConfig sorted by priority (ascending)
        """
        return sorted(
            self.providers.values(),
            key=lambda p: p.priority
        )
    
    def get_usage_report(self) -> str:
        """
        Generate a usage report for all providers.
        
        Returns:
            Formatted string with usage statistics
        """
        report = ["📊 LLM Provider Usage Report", "=" * 70, ""]
        
        for name, stats in self.usage_stats.items():
            provider = self.providers.get(name)
            if not provider:
                continue
            
            status = "✅" if provider.is_available else "❌"
            report.append(f"{status} {name.upper()} ({provider.model})")
            report.append(f"   Requests: {stats.total_requests} "
                         f"(✅ {stats.successful_requests} / ❌ {stats.failed_requests})")
            report.append(f"   Success Rate: {stats.get_success_rate():.1f}%")
            report.append(f"   Tokens: {stats.total_tokens:,}")
            report.append(f"   Est. Cost: ${stats.total_cost:.4f}")
            
            if stats.last_request_time:
                report.append(f"   Last Used: {stats.last_request_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            report.append("")
        
        return "\n".join(report)
    
    def reset_provider(self, provider_name: str):
        """
        Reset a provider's status and error count.
        
        Args:
            provider_name: Name of provider to reset
        """
        if provider_name in self.providers:
            self.providers[provider_name].is_available = True
            self.usage_stats[provider_name].error_count = 0
            self.rate_limiters[provider_name].reset()
            print(f"✅ Reset provider: {provider_name}")
    
    def disable_provider(self, provider_name: str):
        """
        Manually disable a provider.
        
        Args:
            provider_name: Name of provider to disable
        """
        if provider_name in self.providers:
            self.providers[provider_name].is_available = False
            print(f"❌ Disabled provider: {provider_name}")
    
    def enable_provider(self, provider_name: str):
        """
        Manually enable a provider.
        
        Args:
            provider_name: Name of provider to enable
        """
        if provider_name in self.providers:
            self.providers[provider_name].is_available = True
            self.usage_stats[provider_name].error_count = 0
            print(f"✅ Enabled provider: {provider_name}")


# Singleton instance
_provider_manager = None


def get_provider_manager() -> LLMProviderManager:
    """
    Get the global provider manager instance.
    
    Returns:
        LLMProviderManager singleton instance
    """
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = LLMProviderManager()
    return _provider_manager


def get_llm(**kwargs):
    """
    Convenience function to get an LLM with automatic provider management.
    
    Args:
        **kwargs: Arguments to pass to get_llm()
    
    Returns:
        LLM instance
    """
    manager = get_provider_manager()
    return manager.get_llm(**kwargs)


if __name__ == "__main__":
    # Demo
    print("🤖 LLM Provider Manager Demo\n")
    
    manager = LLMProviderManager()
    
    print("\n" + manager.get_usage_report())
    
    print("\n💡 To use:")
    print("   from llm_provider_manager import get_llm")
    print("   llm = get_llm()")
    print("   response = llm.invoke('Hello!')")
