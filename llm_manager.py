"""
LLM Manager - Flexible Language Model Switching
Supports: OpenAI, Gemini, Claude, LM Studio (local), and more
"""

import os
from typing import Optional, Dict, Any, Literal
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama

load_dotenv()


class LLMProvider:
    """Enum-like class for LLM providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"


class LLMConfig:
    """Configuration for different LLM providers"""
    
    # OpenAI Models
    OPENAI_MODELS = {
        "gpt-4o": {"max_tokens": 4096, "supports_tools": True},
        "gpt-4o-mini": {"max_tokens": 16384, "supports_tools": True},
        "gpt-4-turbo": {"max_tokens": 4096, "supports_tools": True},
        "gpt-3.5-turbo": {"max_tokens": 4096, "supports_tools": True},
    }
    
    # Gemini Models
    GEMINI_MODELS = {
        "gemini-2.0-flash-exp": {"max_tokens": 8192, "supports_tools": True},
        "gemini-1.5-pro": {"max_tokens": 8192, "supports_tools": True},
        "gemini-1.5-flash": {"max_tokens": 8192, "supports_tools": True},
    }
    
    # Claude Models
    CLAUDE_MODELS = {
        "claude-3-5-sonnet-20241022": {"max_tokens": 8192, "supports_tools": True},
        "claude-3-opus-20240229": {"max_tokens": 4096, "supports_tools": True},
        "claude-3-sonnet-20240229": {"max_tokens": 4096, "supports_tools": True},
    }
    
    # LM Studio / Local Models (default endpoint)
    LM_STUDIO_ENDPOINT = "http://localhost:1234/v1"
    
    # Ollama Models (runs locally)
    OLLAMA_MODELS = {
        "llama3.2": {"supports_tools": True},
        "llama3.1": {"supports_tools": True},
        "mistral": {"supports_tools": True},
        "mixtral": {"supports_tools": True},
    }


class LLMManager:
    """
    Manages LLM initialization and switching between providers.
    
    Usage:
        # Use OpenAI (default)
        llm = LLMManager.get_llm()
        
        # Use Gemini
        llm = LLMManager.get_llm(provider="gemini", model="gemini-1.5-pro")
        
        # Use LM Studio (local)
        llm = LLMManager.get_llm(provider="lm_studio", model="local-model")
        
        # Use Ollama (local)
        llm = LLMManager.get_llm(provider="ollama", model="llama3.2")
    """
    
    @staticmethod
    def get_llm(
        provider: str = LLMProvider.OPENAI,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Get an LLM instance based on provider and configuration.
        
        Args:
            provider: LLM provider (openai, gemini, claude, lm_studio, ollama)
            model: Model name (provider-specific)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            api_key: API key (if not in environment)
            base_url: Custom base URL (for local models)
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Configured LLM instance
        """
        
        if provider == LLMProvider.OPENAI:
            return LLMManager._get_openai_llm(model, temperature, max_tokens, api_key, **kwargs)
        
        elif provider == LLMProvider.GEMINI:
            return LLMManager._get_gemini_llm(model, temperature, max_tokens, api_key, **kwargs)
        
        elif provider == LLMProvider.CLAUDE:
            return LLMManager._get_claude_llm(model, temperature, max_tokens, api_key, **kwargs)
        
        elif provider == LLMProvider.LM_STUDIO:
            return LLMManager._get_lm_studio_llm(model, temperature, max_tokens, base_url, **kwargs)
        
        elif provider == LLMProvider.OLLAMA:
            return LLMManager._get_ollama_llm(model, temperature, base_url, **kwargs)
        
        else:
            raise ValueError(f"Unknown provider: {provider}. Use one of: {list(vars(LLMProvider).values())}")
    
    @staticmethod
    def _get_openai_llm(
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Get OpenAI LLM instance"""
        model = model or "gpt-4o-mini"
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment or arguments")
        
        config = LLMConfig.OPENAI_MODELS.get(model, {})
        max_tokens = max_tokens or config.get("max_tokens", 4096)
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _get_gemini_llm(
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Get Gemini LLM instance"""
        model = model or "gemini-1.5-flash"
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment or arguments")
        
        config = LLMConfig.GEMINI_MODELS.get(model, {})
        max_tokens = max_tokens or config.get("max_tokens", 8192)
        
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _get_claude_llm(
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """Get Claude LLM instance"""
        model = model or "claude-3-5-sonnet-20241022"
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or arguments")
        
        config = LLMConfig.CLAUDE_MODELS.get(model, {})
        max_tokens = max_tokens or config.get("max_tokens", 8192)
        
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
            **kwargs
        )
    
    @staticmethod
    def _get_lm_studio_llm(
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Get LM Studio LLM instance (local model).
        
        LM Studio runs a local OpenAI-compatible API server.
        Default endpoint: http://localhost:1234/v1
        
        Setup:
        1. Download LM Studio: https://lmstudio.ai/
        2. Download a model (e.g., Llama 3.2, Mistral)
        3. Start the local server in LM Studio
        4. Use this method to connect
        """
        model = model or "local-model"  # LM Studio uses the loaded model
        base_url = base_url or LLMConfig.LM_STUDIO_ENDPOINT
        max_tokens = max_tokens or 4096
        
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            base_url=base_url,
            api_key="lm-studio",  # LM Studio doesn't require a real API key
            **kwargs
        )
    
    @staticmethod
    def _get_ollama_llm(
        model: Optional[str] = None,
        temperature: float = 0.7,
        base_url: Optional[str] = None,
        **kwargs
    ):
        """
        Get Ollama LLM instance (local model).
        
        Ollama runs models locally without API keys.
        Default endpoint: http://localhost:11434
        
        Setup:
        1. Install Ollama: https://ollama.ai/
        2. Pull a model: ollama pull llama3.2
        3. Use this method to connect
        """
        model = model or "llama3.2"
        base_url = base_url or "http://localhost:11434"
        
        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=base_url,
            **kwargs
        )
    
    @staticmethod
    def list_available_models(provider: str) -> Dict[str, Any]:
        """List available models for a provider"""
        if provider == LLMProvider.OPENAI:
            return LLMConfig.OPENAI_MODELS
        elif provider == LLMProvider.GEMINI:
            return LLMConfig.GEMINI_MODELS
        elif provider == LLMProvider.CLAUDE:
            return LLMConfig.CLAUDE_MODELS
        elif provider == LLMProvider.OLLAMA:
            return LLMConfig.OLLAMA_MODELS
        else:
            return {}
    
    @staticmethod
    def validate_provider(provider: str) -> bool:
        """Check if provider is supported"""
        return provider in [
            LLMProvider.OPENAI,
            LLMProvider.GEMINI,
            LLMProvider.CLAUDE,
            LLMProvider.LM_STUDIO,
            LLMProvider.OLLAMA,
        ]


# Convenience function for quick LLM initialization
def get_llm(provider: str = "openai", model: Optional[str] = None, **kwargs):
    """
    Quick LLM initialization.
    
    Examples:
        # OpenAI (default)
        llm = get_llm()
        
        # Gemini
        llm = get_llm("gemini", "gemini-1.5-pro")
        
        # LM Studio (local)
        llm = get_llm("lm_studio")
        
        # Ollama (local)
        llm = get_llm("ollama", "llama3.2")
    """
    return LLMManager.get_llm(provider=provider, model=model, **kwargs)


if __name__ == "__main__":
    # Example usage and testing
    print("🤖 LLM Manager - Available Providers\n")
    
    print("1. OpenAI Models:")
    for model, config in LLMConfig.OPENAI_MODELS.items():
        print(f"   - {model}: {config}")
    
    print("\n2. Gemini Models:")
    for model, config in LLMConfig.GEMINI_MODELS.items():
        print(f"   - {model}: {config}")
    
    print("\n3. Claude Models:")
    for model, config in LLMConfig.CLAUDE_MODELS.items():
        print(f"   - {model}: {config}")
    
    print("\n4. Local Models:")
    print(f"   - LM Studio: {LLMConfig.LM_STUDIO_ENDPOINT}")
    print(f"   - Ollama: http://localhost:11434")
    
    print("\n✅ LLM Manager ready!")
