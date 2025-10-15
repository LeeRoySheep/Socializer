#!/bin/bash
# Install optional LLM providers

echo "🤖 LLM Provider Installation Script"
echo "===================================="
echo ""

# Check if venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

echo "Select providers to install:"
echo ""
echo "1) Google Gemini"
echo "2) Anthropic Claude"
echo "3) Ollama (local models)"
echo "4) All providers"
echo "5) Exit"
echo ""

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo "📦 Installing Google Gemini support..."
        pip install langchain-google-genai
        echo "✅ Gemini installed!"
        echo "Add GOOGLE_API_KEY to your .env file"
        ;;
    2)
        echo "📦 Installing Anthropic Claude support..."
        pip install langchain-anthropic
        echo "✅ Claude installed!"
        echo "Add ANTHROPIC_API_KEY to your .env file"
        ;;
    3)
        echo "📦 Installing Ollama support..."
        pip install langchain-community
        echo "✅ Ollama support installed!"
        echo ""
        echo "Next steps:"
        echo "1. Install Ollama: https://ollama.ai/"
        echo "2. Pull a model: ollama pull llama3.2"
        echo "3. Start server: ollama serve"
        ;;
    4)
        echo "📦 Installing all providers..."
        pip install langchain-google-genai langchain-anthropic langchain-community
        echo "✅ All providers installed!"
        echo ""
        echo "Add these to your .env file:"
        echo "- GOOGLE_API_KEY=..."
        echo "- ANTHROPIC_API_KEY=..."
        ;;
    5)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit llm_config.py to set your provider"
echo "2. Add API keys to .env file"
echo "3. Restart your server"
