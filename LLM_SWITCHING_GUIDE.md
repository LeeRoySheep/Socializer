# 🤖 LLM Switching Guide

Complete guide to switching between AI providers in your Socializer app.

---

## 🎯 Quick Start

### **Option 1: Edit Configuration File** (Recommended)

Edit `llm_config.py`:

```python
# Change these values:
DEFAULT_PROVIDER = "openai"  # or "gemini", "claude", "lm_studio", "ollama"
DEFAULT_MODEL = "gpt-4o-mini"  # See model options below
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 4096
```

### **Option 2: Use Environment Variables**

Add to your `.env` file:

```bash
# Choose your provider
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# API Keys (as needed)
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=...
```

---

## 📋 Available Providers

### **1. OpenAI (Default)** ✅

**Models:**
- `gpt-4o` - Most capable, best for complex tasks
- `gpt-4o-mini` - Fast and cost-effective (recommended)
- `gpt-4-turbo` - Powerful, good balance
- `gpt-3.5-turbo` - Fast and cheap

**Setup:**
```bash
# Add to .env
OPENAI_API_KEY=sk-your-key-here
```

**Configuration:**
```python
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"
```

---

### **2. Google Gemini** 🌟

**Models:**
- `gemini-2.0-flash-exp` - Experimental, very fast
- `gemini-1.5-pro` - Most capable Gemini model
- `gemini-1.5-flash` - Fast and efficient (recommended)

**Setup:**
```bash
# Get API key from: https://makersuite.google.com/app/apikey
# Add to .env
GOOGLE_API_KEY=your-key-here
```

**Configuration:**
```python
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-1.5-flash"
```

**Install dependencies:**
```bash
pip install langchain-google-genai
```

---

### **3. Anthropic Claude** 🧠

**Models:**
- `claude-3-5-sonnet-20241022` - Most capable (recommended)
- `claude-3-opus-20240229` - Powerful reasoning
- `claude-3-sonnet-20240229` - Balanced performance

**Setup:**
```bash
# Get API key from: https://console.anthropic.com/
# Add to .env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Configuration:**
```python
DEFAULT_PROVIDER = "claude"
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
```

**Install dependencies:**
```bash
pip install langchain-anthropic
```

---

### **4. LM Studio (Local)** 💻

Run AI models **locally** on your computer - **NO API COSTS!**

**Setup:**

1. **Download LM Studio:**
   - Visit: https://lmstudio.ai/
   - Download and install for your OS

2. **Download a Model:**
   - Open LM Studio
   - Go to "Discover" tab
   - Search for models (recommended: Llama 3.2, Mistral)
   - Click download

3. **Start Local Server:**
   - Go to "Local Server" tab
   - Click "Start Server"
   - Default endpoint: `http://localhost:1234/v1`

4. **Configure Socializer:**
   ```python
   DEFAULT_PROVIDER = "lm_studio"
   DEFAULT_MODEL = "local-model"  # Uses whatever you loaded
   ```

**Recommended Models:**
- `llama-3.2-3b` - Fast, good quality
- `mistral-7b` - Excellent performance
- `phi-3-mini` - Very fast, smaller

**Advantages:**
- ✅ No API costs
- ✅ Complete privacy
- ✅ Works offline
- ✅ No rate limits

**Requirements:**
- 8GB+ RAM (16GB recommended)
- Modern CPU/GPU

---

### **5. Ollama (Local)** 🦙

Another local option - **completely free and open source!**

**Setup:**

1. **Install Ollama:**
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Or download from: https://ollama.ai/
   ```

2. **Pull a Model:**
   ```bash
   # Llama 3.2 (recommended)
   ollama pull llama3.2
   
   # Other options:
   ollama pull llama3.1
   ollama pull mistral
   ollama pull mixtral
   ```

3. **Start Ollama:**
   ```bash
   ollama serve
   # Runs on http://localhost:11434
   ```

4. **Configure Socializer:**
   ```python
   DEFAULT_PROVIDER = "ollama"
   DEFAULT_MODEL = "llama3.2"
   ```

**Advantages:**
- ✅ Completely free
- ✅ Open source
- ✅ Easy to use
- ✅ No API keys needed

**Install dependencies:**
```bash
pip install langchain-community
```

---

## 🚀 Usage Examples

### **Switch to Gemini:**

```python
# In llm_config.py
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-1.5-flash"
```

Restart server:
```bash
uvicorn app.main:app --reload
```

### **Switch to Local (LM Studio):**

1. Start LM Studio server
2. Load a model
3. Update config:
   ```python
   DEFAULT_PROVIDER = "lm_studio"
   DEFAULT_MODEL = "local-model"
   ```
4. Restart server

### **Programmatic Switching:**

```python
from llm_manager import LLMManager

# Use Gemini
llm = LLMManager.get_llm(provider="gemini", model="gemini-1.5-flash")

# Use local model
llm = LLMManager.get_llm(provider="lm_studio")

# Use Ollama
llm = LLMManager.get_llm(provider="ollama", model="llama3.2")
```

---

## 🎛️ Configuration Presets

Use pre-configured settings from `llm_config.py`:

```python
from llm_config import LLMPresets
from llm_manager import LLMManager

# Fast and cheap (testing)
llm = LLMManager.get_llm(**LLMPresets.FAST)

# Most capable (production)
llm = LLMManager.get_llm(**LLMPresets.BEST)

# Creative (content generation)
llm = LLMManager.get_llm(**LLMPresets.CREATIVE)

# Local (no costs)
llm = LLMManager.get_llm(**LLMPresets.LOCAL_LM_STUDIO)
```

---

## 📊 Model Comparison

| Provider | Speed | Cost | Quality | Local | Tools Support |
|----------|-------|------|---------|-------|---------------|
| **GPT-4o-mini** | ⚡⚡⚡ | 💰 | ⭐⭐⭐⭐ | ❌ | ✅ |
| **GPT-4o** | ⚡⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ | ❌ | ✅ |
| **Gemini Flash** | ⚡⚡⚡⚡ | 💰 | ⭐⭐⭐⭐ | ❌ | ✅ |
| **Claude Sonnet** | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐⭐ | ❌ | ✅ |
| **LM Studio** | ⚡⚡ | FREE | ⭐⭐⭐ | ✅ | ⚠️ |
| **Ollama** | ⚡⚡ | FREE | ⭐⭐⭐ | ✅ | ⚠️ |

---

## 🔧 Troubleshooting

### **"API key not found" error**

Add the required API key to `.env`:
```bash
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```

### **LM Studio connection error**

1. Make sure LM Studio server is running
2. Check endpoint: `http://localhost:1234/v1`
3. Verify a model is loaded

### **Ollama not found**

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama3.2`
3. Start server: `ollama serve`

### **Module not found errors**

Install missing dependencies:
```bash
# For Gemini
pip install langchain-google-genai

# For Claude
pip install langchain-anthropic

# For Ollama
pip install langchain-community
```

---

## 💡 Best Practices

### **For Development:**
```python
# Use fast, cheap models
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"
```

### **For Production:**
```python
# Use most capable models
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o"
```

### **For Testing (No Costs):**
```python
# Use local models
DEFAULT_PROVIDER = "lm_studio"
DEFAULT_MODEL = "local-model"
```

### **For Privacy:**
```python
# All data stays local
DEFAULT_PROVIDER = "ollama"
DEFAULT_MODEL = "llama3.2"
```

---

## 📝 Check Current Configuration

Run this to see your current setup:

```bash
python llm_config.py
```

Output:
```
🤖 Current LLM Configuration
==================================================
Provider:    openai
Model:       gpt-4o-mini
Temperature: 0.7
Max Tokens:  4096
==================================================

🔑 Provider Status:
✅ OPENAI: Available
❌ GEMINI: API key missing
❌ CLAUDE: API key missing
✅ LM_STUDIO: Available
✅ OLLAMA: Available
```

---

## 🎉 Summary

**You can now:**
- ✅ Switch between 5 different AI providers
- ✅ Use API-based models (OpenAI, Gemini, Claude)
- ✅ Run models locally (LM Studio, Ollama)
- ✅ Save costs with local models
- ✅ Easy configuration via `llm_config.py`
- ✅ Environment variable support

**Just edit `llm_config.py` and restart your server!** 🚀
