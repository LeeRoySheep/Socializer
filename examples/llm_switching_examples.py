"""
LLM Switching Examples
Demonstrates how to use different AI providers in your Socializer app
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from llm_manager import LLMManager, LLMProvider
from llm_config import LLMSettings, LLMPresets


def example_1_default_llm():
    """Example 1: Use default LLM from config"""
    print("\n" + "="*60)
    print("Example 1: Default LLM (from llm_config.py)")
    print("="*60)
    
    llm = LLMManager.get_llm(
        provider=LLMSettings.DEFAULT_PROVIDER,
        model=LLMSettings.DEFAULT_MODEL
    )
    
    print(f"✅ Using: {LLMSettings.DEFAULT_PROVIDER} - {LLMSettings.DEFAULT_MODEL}")
    
    # Test with a simple message
    response = llm.invoke("Say hello in 5 words or less")
    print(f"Response: {response.content}")


def example_2_switch_to_gemini():
    """Example 2: Switch to Google Gemini"""
    print("\n" + "="*60)
    print("Example 2: Switch to Google Gemini")
    print("="*60)
    
    try:
        llm = LLMManager.get_llm(
            provider="gemini",
            model="gemini-1.5-flash"
        )
        
        print("✅ Using: Gemini 1.5 Flash")
        
        response = llm.invoke("What's 2+2?")
        print(f"Response: {response.content}")
        
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("💡 Add GOOGLE_API_KEY to your .env file")


def example_3_local_lm_studio():
    """Example 3: Use LM Studio (local model)"""
    print("\n" + "="*60)
    print("Example 3: LM Studio (Local Model)")
    print("="*60)
    
    try:
        llm = LLMManager.get_llm(
            provider="lm_studio",
            model="local-model"
        )
        
        print("✅ Using: LM Studio (local)")
        print("💡 Make sure LM Studio server is running on http://localhost:1234")
        
        response = llm.invoke("Hello! Respond in 5 words.")
        print(f"Response: {response.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Start LM Studio server first")


def example_4_ollama():
    """Example 4: Use Ollama (local model)"""
    print("\n" + "="*60)
    print("Example 4: Ollama (Local Model)")
    print("="*60)
    
    try:
        llm = LLMManager.get_llm(
            provider="ollama",
            model="llama3.2"
        )
        
        print("✅ Using: Ollama - Llama 3.2")
        print("💡 Make sure Ollama is running: ollama serve")
        
        response = llm.invoke("Hi! Reply briefly.")
        print(f"Response: {response.content}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Install Ollama and run: ollama pull llama3.2")


def example_5_use_preset():
    """Example 5: Use configuration preset"""
    print("\n" + "="*60)
    print("Example 5: Using Configuration Presets")
    print("="*60)
    
    # Use FAST preset (cheap and quick)
    llm = LLMManager.get_llm(**LLMPresets.FAST)
    print(f"✅ Using FAST preset: {LLMPresets.FAST}")
    
    response = llm.invoke("Count to 3")
    print(f"Response: {response.content}")


def example_6_temperature_control():
    """Example 6: Control creativity with temperature"""
    print("\n" + "="*60)
    print("Example 6: Temperature Control")
    print("="*60)
    
    prompt = "Write a creative sentence about AI"
    
    # Low temperature (more deterministic)
    print("\n🧊 Low Temperature (0.2) - Precise:")
    llm_precise = LLMManager.get_llm(temperature=0.2)
    response = llm_precise.invoke(prompt)
    print(f"   {response.content}")
    
    # High temperature (more creative)
    print("\n🔥 High Temperature (0.9) - Creative:")
    llm_creative = LLMManager.get_llm(temperature=0.9)
    response = llm_creative.invoke(prompt)
    print(f"   {response.content}")


def example_7_compare_providers():
    """Example 7: Compare responses from different providers"""
    print("\n" + "="*60)
    print("Example 7: Compare Providers")
    print("="*60)
    
    prompt = "Explain AI in one sentence"
    
    providers = [
        ("openai", "gpt-4o-mini"),
        # ("gemini", "gemini-1.5-flash"),  # Uncomment if you have API key
        # ("lm_studio", "local-model"),     # Uncomment if LM Studio is running
    ]
    
    for provider, model in providers:
        try:
            print(f"\n🤖 {provider.upper()} ({model}):")
            llm = LLMManager.get_llm(provider=provider, model=model)
            response = llm.invoke(prompt)
            print(f"   {response.content}")
        except Exception as e:
            print(f"   ❌ Not available: {e}")


def example_8_list_models():
    """Example 8: List available models"""
    print("\n" + "="*60)
    print("Example 8: Available Models")
    print("="*60)
    
    providers = ["openai", "gemini", "claude", "ollama"]
    
    for provider in providers:
        print(f"\n📋 {provider.upper()} Models:")
        models = LLMManager.list_available_models(provider)
        for model_name, config in models.items():
            print(f"   - {model_name}")
            if isinstance(config, dict):
                for key, value in config.items():
                    print(f"     {key}: {value}")


def main():
    """Run all examples"""
    print("\n" + "🤖 LLM SWITCHING EXAMPLES ".center(60, "="))
    
    # Show current configuration
    LLMSettings.print_config()
    
    # Run examples
    examples = [
        example_1_default_llm,
        # example_2_switch_to_gemini,  # Uncomment if you have Gemini API key
        # example_3_local_lm_studio,    # Uncomment if LM Studio is running
        # example_4_ollama,             # Uncomment if Ollama is running
        example_5_use_preset,
        example_6_temperature_control,
        example_7_compare_providers,
        example_8_list_models,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Examples complete!")
    print("="*60)
    print("\n💡 Tips:")
    print("   - Edit llm_config.py to change default provider")
    print("   - Add API keys to .env file")
    print("   - Install providers: ./install_llm_providers.sh")
    print("   - Read: LLM_SWITCHING_GUIDE.md")


if __name__ == "__main__":
    main()
