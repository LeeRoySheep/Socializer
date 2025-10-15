# 🖥️ Local AI Setup Guide

**Run AI Models Locally with LM Studio or Ollama**

---

## 🎯 **Why Local AI?**

### **Benefits:**
✅ **Privacy** - Your data never leaves your machine  
✅ **Cost** - Zero API costs after setup  
✅ **Speed** - No network latency (once loaded)  
✅ **Offline** - Works without internet  
✅ **Customization** - Fine-tune your own models  

### **Trade-offs:**
⚠️ **Hardware** - Needs 8GB+ RAM (16GB+ recommended)  
⚠️ **Load Time** - Initial model load takes 10-30 seconds  
⚠️ **Quality** - Smaller models may be less capable than GPT-4  

---

## 🚀 **Option 1: LM Studio (Recommended)**

### **What is LM Studio?**
- Beautiful desktop app for running local LLMs
- Supports hundreds of models (Llama, Mistral, Phi, etc.)
- Easy model download and management
- OpenAI-compatible API

### **Installation:**

1. **Download LM Studio**
   - Visit: https://lmstudio.ai/
   - Download for Mac/Windows/Linux
   - Install like any normal app

2. **Download a Model**
   - Open LM Studio
   - Click "Search" tab
   - Recommended models:
     - `TheBloke/Mistral-7B-Instruct-v0.2-GGUF` (7GB, balanced)
     - `TheBloke/Llama-2-13B-chat-GGUF` (8GB, better quality)
     - `microsoft/phi-2-GGUF` (3GB, fast but basic)
   - Click download on your chosen model

3. **Start Local Server**
   - Click "Local Server" tab
   - Select your downloaded model
   - Click "Start Server"
   - Default: `http://localhost:1234/v1`

4. **Use in Socializer**
   - In chat, select "LM Studio (Local)" from dropdown
   - Send a message - it will use your local model!

### **Configuration:**

```bash
# Optional: Change default port in .env
LM_STUDIO_BASE_URL=http://localhost:1234/v1
```

---

## 🦙 **Option 2: Ollama**

### **What is Ollama?**
- Command-line tool for running local LLMs
- Fast and lightweight
- Good for developers
- Supports Llama, Mistral, Code Llama, and more

### **Installation:**

**Mac/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
- Download from: https://ollama.com/download/windows

### **Download Models:**

```bash
# Recommended models:
ollama pull llama2          # 7B, general purpose
ollama pull mistral         # 7B, fast and capable
ollama pull codellama       # 7B, code-focused
ollama pull phi             # 3B, very fast
```

### **Start Ollama:**

```bash
# Ollama starts automatically after install
# Check status:
ollama list

# Test it:
ollama run llama2 "Hello!"
```

### **Use in Socializer:**

1. Make sure Ollama is running: `ollama list`
2. In chat, select "Ollama (Local)" from dropdown
3. Send a message!

### **Configuration:**

```bash
# Optional: Change default model in .env
OLLAMA_MODEL=mistral  # or llama2, codellama, etc.
OLLAMA_BASE_URL=http://localhost:11434
```

---

## ⚙️ **Configuration Options**

### **Environment Variables (.env):**

```bash
# ===== LM Studio Configuration =====
LM_STUDIO_BASE_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=local-model  # LM Studio auto-detects

# ===== Ollama Configuration =====
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2  # or mistral, codellama, phi

# ===== Performance Tuning =====
# Number of tokens to generate (affects speed vs quality)
LOCAL_MAX_TOKENS=2048

# Temperature (0-1, higher = more creative)
LOCAL_TEMPERATURE=0.7
```

---

## 📊 **Model Comparison**

### **Recommended Models:**

| Model | Size | RAM Needed | Speed | Quality | Best For |
|-------|------|------------|-------|---------|----------|
| **Phi-2** | 3GB | 8GB | ⚡⚡⚡ | ⭐⭐⭐ | Fast responses, basic chat |
| **Mistral 7B** | 7GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐ | Balanced, general purpose |
| **Llama 2 13B** | 8GB | 16GB | ⚡ | ⭐⭐⭐⭐⭐ | High quality, slower |
| **Code Llama** | 7GB | 16GB | ⚡⚡ | ⭐⭐⭐⭐ | Code generation |

### **Performance on Typical Hardware:**

**MacBook Pro M1/M2 (16GB RAM):**
- Mistral 7B: ~20 tokens/sec ✅
- Llama 2 13B: ~10 tokens/sec ✅
- Phi-2: ~40 tokens/sec ✅

**Windows Gaming PC (32GB RAM, RTX 4070):**
- Mistral 7B: ~50 tokens/sec ✅
- Llama 2 13B: ~25 tokens/sec ✅
- Phi-2: ~80 tokens/sec ✅

**Regular Laptop (8GB RAM):**
- Phi-2: ~10-15 tokens/sec ⚠️
- Mistral 7B: May be slow/crash ❌

---

## 🧪 **Testing Local Models**

### **1. Test LM Studio:**

```bash
# Test the API directly
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### **2. Test Ollama:**

```bash
# Test with CLI
ollama run llama2 "What is the capital of France?"

# Test the API
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Hello!",
    "stream": false
  }'
```

### **3. Test in Socializer:**

1. Start your local model server
2. Open Socializer chat
3. Select "LM Studio (Local)" or "Ollama (Local)"
4. Send: "Hello, are you running locally?"
5. Check server logs for connection

---

## 🐛 **Troubleshooting**

### **"Connection refused" error:**

**LM Studio:**
```bash
# Make sure server is running
# Check LM Studio -> Local Server tab
# Should show: ✅ Running on port 1234
```

**Ollama:**
```bash
# Check if Ollama is running
ollama list

# If not, start it
ollama serve
```

### **Slow responses:**

1. **Use a smaller model**
   - Phi-2 (3GB) instead of Llama 2 13B (8GB)

2. **Reduce max_tokens**
   ```bash
   # In .env
   LOCAL_MAX_TOKENS=512  # Instead of 2048
   ```

3. **Close other apps**
   - Free up RAM for the model

### **Model quality is poor:**

1. **Try a better model**
   - Mistral 7B > Phi-2
   - Llama 2 13B > Llama 2 7B

2. **Adjust temperature**
   ```bash
   # In .env
   LOCAL_TEMPERATURE=0.5  # More focused (0-1)
   ```

3. **Check model is fully loaded**
   - LM Studio: Wait for "Model loaded" message
   - Ollama: `ollama list` should show model

### **Port conflicts:**

**LM Studio using different port:**
```bash
# In .env
LM_STUDIO_BASE_URL=http://localhost:YOUR_PORT/v1
```

**Ollama using different port:**
```bash
# In .env
OLLAMA_BASE_URL=http://localhost:YOUR_PORT
```

---

## 💡 **Tips & Best Practices**

### **1. Model Selection:**
- **Chat:** Mistral 7B or Llama 2 13B
- **Code:** Code Llama
- **Speed:** Phi-2
- **Quality:** Llama 2 13B

### **2. Performance:**
- Load model once, keep server running
- Use GPU if available (LM Studio auto-detects)
- Close browser tabs to free RAM

### **3. Privacy:**
- Local models = zero data sent to cloud ✅
- Perfect for sensitive conversations
- No API keys needed

### **4. Hybrid Approach:**
- **Fast queries:** Use local model
- **Complex tasks:** Switch to GPT-4
- **Code:** Use Code Llama locally
- **Web search:** Use GPT with tools

---

## 📚 **Useful Links**

**LM Studio:**
- Website: https://lmstudio.ai/
- Models: https://huggingface.co/models?library=gguf
- Discord: https://discord.gg/lmstudio

**Ollama:**
- Website: https://ollama.com/
- Models: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama

**Model Libraries:**
- Hugging Face: https://huggingface.co/models
- TheBloke (GGUF): https://huggingface.co/TheBloke

---

## ✅ **Quick Start Checklist**

### **LM Studio:**
- [ ] Download LM Studio
- [ ] Install application
- [ ] Download a model (Mistral 7B recommended)
- [ ] Start local server (port 1234)
- [ ] Select "LM Studio (Local)" in Socializer
- [ ] Test with a message

### **Ollama:**
- [ ] Install Ollama (`curl https://ollama.com/install.sh | sh`)
- [ ] Download model (`ollama pull mistral`)
- [ ] Verify running (`ollama list`)
- [ ] Select "Ollama (Local)" in Socializer
- [ ] Test with a message

---

## 🎉 **Success!**

If you can send a message and get a response from your local model, you're all set!

**Benefits you now have:**
- ✅ Privacy-first AI
- ✅ Zero API costs
- ✅ Offline capability
- ✅ Full control

**Pro tip:** Keep both cloud and local models available. Switch based on your needs!

---

**Need help?** Check the troubleshooting section or open an issue on GitHub.
