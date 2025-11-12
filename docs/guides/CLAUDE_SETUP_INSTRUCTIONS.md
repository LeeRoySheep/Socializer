# 🤖 Claude AI Setup Instructions

**Date:** November 12, 2024  
**Status:** Ready to Configure

---

## 🎯 Quick Setup

### **Step 1: Get Your Claude API Key**

1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-ant-api...`)

---

### **Step 2: Add API Key to .env**

Open `/Users/leeroystevenson/PycharmProjects/Socializer/.env` and replace line 22:

```bash
# BEFORE (line 22):
ANTHROPIC_API_KEY=your-claude-api-key-here

# AFTER (use your actual key):
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

**Important:** Keep your API key secret! Never commit it to git.

---

### **Step 3: Test Claude Integration**

Run the test script:

```bash
cd /Users/leeroystevenson/PycharmProjects/Socializer
.venv/bin/python test_claude_integration.py
```

**Expected output:**
```
🤖 CLAUDE AI INTEGRATION TESTS
✅ PASS: API Key
✅ PASS: Initialization
✅ PASS: Basic API Call
✅ PASS: Language Detection
✅ PASS: Tool Binding
✅ PASS: Chat Agent Integration

🎉 ALL TESTS PASSED (6/6)
```

---

## 📊 Claude Models Available

### **Recommended: Claude 3.5 Sonnet** ⭐
```python
llm = LLMManager.get_llm(
    provider="claude",
    model="claude-3-5-sonnet-20241022"
)
```
- **Best balance** of intelligence, speed, and cost
- Excellent for language detection
- Great tool calling support
- **Default model**

### **Most Capable: Claude 3 Opus**
```python
llm = LLMManager.get_llm(
    provider="claude",
    model="claude-3-opus-20240229"
)
```
- Most intelligent model
- Best for complex tasks
- Higher cost
- Slower responses

### **Balanced: Claude 3 Sonnet**
```python
llm = LLMManager.get_llm(
    provider="claude",
    model="claude-3-sonnet-20240229"
)
```
- Good balance
- Faster than Opus
- Lower cost than Opus

---

## 🔧 Configuration in AI Agent

### **Option 1: Environment Variable (Recommended)**

Set in `.env`:
```bash
DEFAULT_LLM_PROVIDER=claude
DEFAULT_LLM_MODEL=claude-3-5-sonnet-20241022
```

### **Option 2: Code Configuration**

In `ai_manager.py` or wherever you create the agent:

```python
from llm_manager import LLMManager
from ai_chatagent import AiChatagent

# Create Claude LLM
llm = LLMManager.get_llm(
    provider="claude",
    model="claude-3-5-sonnet-20241022",
    temperature=0.7
)

# Create agent with Claude
agent = AiChatagent(user=user, llm=llm)
```

---

## ✅ What Works with Claude

### **✅ Language Detection**
```python
from services.ai_language_detector import AILanguageDetector

detector = AILanguageDetector(claude_llm)
result = detector.detect("Hallo! Wie geht es dir?")
# → German (high confidence)
```

### **✅ Tool Calling**
Claude supports all tools:
- `set_language_preference`
- `recall_last_conversation`
- `user_preference`
- `skill_evaluator`
- `tavily_search`
- All other tools

### **✅ Multi-Language Support**
Claude is excellent with:
- English, German, Spanish, French, Italian
- Portuguese, Dutch, Russian, Polish
- Japanese, Chinese, Korean
- And 100+ other languages

### **✅ Chat Agent Integration**
Full compatibility with `AiChatagent`:
- Tool binding works
- Memory system works
- Language detection works
- All features supported

---

## 🎨 Using Claude in Frontend

### **Switching Users to Claude**

The AI manager can be configured to use Claude for specific users or globally.

**Global switch (all users):**
```python
# In ai_manager.py or config
DEFAULT_PROVIDER = "claude"
```

**Per-user switch:**
```python
# In user preferences
user_preferences = {
    "llm_provider": "claude",
    "llm_model": "claude-3-5-sonnet-20241022"
}
```

---

## 💰 Cost Comparison

### **OpenAI GPT-4o-mini:**
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

### **Claude 3.5 Sonnet:**
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens

### **Claude 3 Opus:**
- Input: $15.00 / 1M tokens
- Output: $75.00 / 1M tokens

**Note:** Claude is more expensive but often more accurate and capable.

---

## 🐛 Troubleshooting

### **Error: "ANTHROPIC_API_KEY not found"**
**Fix:** Add your API key to `.env` file (line 22)

### **Error: "Invalid API key"**
**Fix:** Check that your API key is correct and active at https://console.anthropic.com/

### **Error: "Rate limit exceeded"**
**Fix:** Claude has rate limits. Wait a few minutes or upgrade your plan.

### **Error: "Model not found"**
**Fix:** Check model name spelling. Use one of:
- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`

### **Tool binding warnings**
**Fix:** This is normal. Claude's tool binding works differently but is handled automatically by the chat agent.

---

## 📊 Performance Comparison

| Feature | OpenAI | Gemini | Claude |
|---------|--------|--------|--------|
| Speed | ⚡⚡⚡ Fast | ⚡⚡⚡ Fast | ⚡⚡ Moderate |
| Cost | 💰 Cheap | 💰 Cheap | 💰💰💰 Expensive |
| Language Detection | ✅ Good | ✅ Very Good | ✅ Excellent |
| Tool Calling | ✅ Excellent | ✅ Good | ✅ Excellent |
| Context Understanding | ✅ Very Good | ✅ Very Good | ✅ Excellent |
| Long Conversations | ✅ Good | ✅ Good | ✅ Excellent |

---

## 🎯 When to Use Claude

### **✅ Use Claude for:**
- Complex reasoning tasks
- Nuanced language understanding
- Long context conversations
- High-stakes interactions
- Multi-language support
- Creative writing

### **⚠️ Use OpenAI/Gemini for:**
- High-volume simple tasks
- Cost-sensitive applications
- Quick responses needed
- Basic language detection

---

## 🚀 Testing Checklist

After adding your API key, verify these work:

- [ ] API key configured in .env
- [ ] Run `test_claude_integration.py` - all tests pass
- [ ] Claude LLM initializes without errors
- [ ] Language detection works with Claude
- [ ] Chat agent works with Claude
- [ ] Tools bind correctly to Claude
- [ ] Frontend can use Claude (if configured)

---

## 📝 Quick Test Commands

```bash
# Test 1: Check API key
grep ANTHROPIC .env

# Test 2: Test basic call
.venv/bin/python -c "
from llm_manager import LLMManager
llm = LLMManager.get_llm('claude')
print(llm.invoke('Say hello!').content)
"

# Test 3: Run full test suite
.venv/bin/python test_claude_integration.py

# Test 4: Test with chat agent
.venv/bin/python -c "
from datamanager.data_manager import DataManager
from llm_manager import LLMManager
from ai_chatagent import AiChatagent

dm = DataManager('data.sqlite.db')
user = dm.get_user(1)
llm = LLMManager.get_llm('claude')
agent = AiChatagent(user=user, llm=llm)
print('✅ Claude chat agent ready!')
"
```

---

## ✅ Success Criteria

You'll know Claude is working when:

1. ✅ Test script shows all tests passing
2. ✅ No API key errors
3. ✅ Language detection works accurately
4. ✅ Chat responses are intelligent and context-aware
5. ✅ Tools work correctly
6. ✅ Multi-language support verified

---

## 🎉 Next Steps After Setup

1. **Test in frontend** - Try Claude with real conversations
2. **Compare models** - Test different Claude versions
3. **Monitor costs** - Track API usage
4. **Optimize** - Fine-tune temperature and prompts
5. **Evaluate** - Compare Claude vs OpenAI vs Gemini

---

## 📚 Resources

- **Anthropic Console:** https://console.anthropic.com/
- **Claude Documentation:** https://docs.anthropic.com/
- **API Reference:** https://docs.anthropic.com/claude/reference
- **Pricing:** https://www.anthropic.com/pricing
- **Model Comparison:** https://www.anthropic.com/claude

---

**Ready to configure? Add your API key to `.env` and run the test!** 🚀

