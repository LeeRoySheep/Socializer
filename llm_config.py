"""
LLM Configuration - Easy switching between AI providers
Edit this file to change your default LLM provider and model
"""

from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class LLMSettings:
    """
    Central configuration for LLM selection.
    
    Change these values to switch between providers:
    - "openai" - OpenAI GPT models (API key required)
    - "gemini" - Google Gemini models (API key required)
    - "claude" - Anthropic Claude models (API key required)
    - "lm_studio" - Local models via LM Studio (no API key)
    - "ollama" - Local models via Ollama (no API key)
    """
    
    # ============================================
    # 🎯 MAIN CONFIGURATION - EDIT HERE
    # ============================================
    
    # Choose your provider
    DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # Change to: gemini, claude, lm_studio, ollama
    
    # Choose your model (provider-specific)
    DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")  # See options below
    
    # Model temperature (0.0 = deterministic, 1.0 = creative)
    DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # Maximum tokens in response
    DEFAULT_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
    
    # ============================================
    # 📋 AVAILABLE MODELS BY PROVIDER
    # ============================================
    
    # OpenAI Models
    OPENAI_OPTIONS = {
        "gpt-4o": "Most capable, best for complex tasks",
        "gpt-4o-mini": "Fast and cost-effective, great for most tasks",
        "gpt-4-turbo": "Powerful, good balance",
        "gpt-3.5-turbo": "Fast and cheap, basic tasks",
    }
    
    # Gemini Models
    GEMINI_OPTIONS = {
        "gemini-2.0-flash-exp": "Experimental, very fast",
        "gemini-1.5-pro": "Most capable Gemini model",
        "gemini-1.5-flash": "Fast and efficient",
    }
    
    # Claude Models
    CLAUDE_OPTIONS = {
        "claude-3-5-sonnet-20241022": "Most capable Claude model",
        "claude-3-opus-20240229": "Powerful reasoning",
        "claude-3-sonnet-20240229": "Balanced performance",
    }
    
    # Local Models (LM Studio)
    LM_STUDIO_OPTIONS = {
        "local-model": "Whatever model you loaded in LM Studio",
        "llama-3.2": "Meta's Llama 3.2 (if loaded)",
        "mistral": "Mistral model (if loaded)",
    }
    
    # Local Models (Ollama)
    OLLAMA_OPTIONS = {
        "llama3.2": "Meta's Llama 3.2",
        "llama3.1": "Meta's Llama 3.1",
        "mistral": "Mistral 7B",
        "mixtral": "Mixtral 8x7B",
    }
    
    # ============================================
    # 🔑 API KEYS (from .env file)
    # ============================================
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # ============================================
    # 🌐 LOCAL SERVER ENDPOINTS
    # ============================================
    
    LM_STUDIO_ENDPOINT = os.getenv("LM_STUDIO_ENDPOINT", "http://localhost:1234/v1")
    OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
    
    # ============================================
    # 📊 PROVIDER STATUS
    # ============================================
    
    @classmethod
    def get_provider_status(cls) -> dict:
        """Check which providers are available"""
        return {
            "openai": bool(cls.OPENAI_API_KEY),
            "gemini": bool(cls.GOOGLE_API_KEY),
            "claude": bool(cls.ANTHROPIC_API_KEY),
            "lm_studio": True,  # Always available if server is running
            "ollama": True,  # Always available if server is running
        }
    
    @classmethod
    def get_current_config(cls) -> dict:
        """Get current LLM configuration"""
        return {
            "provider": cls.DEFAULT_PROVIDER,
            "model": cls.DEFAULT_MODEL,
            "temperature": cls.DEFAULT_TEMPERATURE,
            "max_tokens": cls.DEFAULT_MAX_TOKENS,
        }
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("🤖 Current LLM Configuration")
        print("=" * 50)
        print(f"Provider:    {cls.DEFAULT_PROVIDER}")
        print(f"Model:       {cls.DEFAULT_MODEL}")
        print(f"Temperature: {cls.DEFAULT_TEMPERATURE}")
        print(f"Max Tokens:  {cls.DEFAULT_MAX_TOKENS}")
        print("=" * 50)
        
        print("\n🔑 Provider Status:")
        status = cls.get_provider_status()
        for provider, available in status.items():
            icon = "✅" if available else "❌"
            print(f"{icon} {provider.upper()}: {'Available' if available else 'API key missing'}")


# ============================================
# 🎯 QUICK SWITCH PRESETS
# ============================================

class LLMPresets:
    """Pre-configured LLM settings for common use cases"""
    
    # Fast and cheap (for testing)
    FAST = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    
    # Most capable (for production)
    BEST = {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    
    # Creative (for content generation)
    CREATIVE = {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.9,
        "max_tokens": 4096,
    }
    
    # Precise (for analysis)
    PRECISE = {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 4096,
    }
    
    # Local (no API costs)
    LOCAL_LM_STUDIO = {
        "provider": "lm_studio",
        "model": "local-model",
        "temperature": 0.7,
        "max_tokens": 4096,
    }
    
    # Local (Ollama)
    LOCAL_OLLAMA = {
        "provider": "ollama",
        "model": "llama3.2",
        "temperature": 0.7,
    }
    
    # Gemini (Google)
    GEMINI_FAST = {
        "provider": "gemini",
        "model": "gemini-1.5-flash",
        "temperature": 0.7,
        "max_tokens": 8192,
    }
    
    # Claude (Anthropic)
    CLAUDE_BEST = {
        "provider": "claude",
        "model": "claude-3-5-sonnet-20241022",
        "temperature": 0.7,
        "max_tokens": 8192,
    }


if __name__ == "__main__":
    # Print current configuration
    LLMSettings.print_config()
    
    print("\n📋 Available Presets:")
    print("=" * 50)
    for preset_name in dir(LLMPresets):
        if not preset_name.startswith("_"):
            preset = getattr(LLMPresets, preset_name)
            if isinstance(preset, dict):
                print(f"\n{preset_name}:")
                for key, value in preset.items():
                    print(f"  {key}: {value}")
