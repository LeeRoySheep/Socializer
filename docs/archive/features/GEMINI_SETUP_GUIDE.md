# 🤖 Gemini API Setup & Troubleshooting Guide

**Date:** November 12, 2024  
**Status:** 🔴 Quota Exhausted - Solutions Provided

---

## 📊 Current Diagnosis

### ✅ What's Working:
- ✅ API key properly configured in `.env`
- ✅ Key format is valid (AIza...Wy04)
- ✅ Environment variables loaded
- ✅ Required packages installed
- ✅ System has both OpenAI and Gemini keys

### ❌ The Issue:
```
429 Quota Exceeded: generate_content_free_tier_requests, limit: 0
```

**Translation:** Your free tier quota has been completely used up.

---

## 🎯 Solution Options

### **Option 1: Get a New API Key (Recommended)**

Google allows multiple API keys per account. Create a fresh one:

1. **Go to:** https://makersuite.google.com/app/apikey
2. **Click:** "Create API key"
3. **Copy** the new key
4. **Update** `.env` file:
   ```env
   GOOGLE_API_KEY=your_new_key_here
   ```
5. **Restart** your server

**Why this works:** New key = New quota allocation

---

### **Option 2: Wait for Quota Reset**

Free tier quotas reset based on:
- **Per Minute:** 15 requests/min (resets every minute)
- **Per Day:** May have daily limits (resets at midnight UTC)

**Check your usage:** https://ai.dev/usage?tab=rate-limit

**Wait time:** Could be minutes to 24 hours depending on quota type

---

### **Option 3: Use OpenAI Instead (Current Setup)**

Your system is already configured to use OpenAI:
```python
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"
```

**Benefits:**
- ✅ Already working
- ✅ API key valid
- ✅ No quota issues
- ✅ Good performance

**To continue with OpenAI:** Do nothing! It's already set up.

---

### **Option 4: Upgrade to Gemini Paid Tier**

If you need higher quota:

1. **Go to:** https://console.cloud.google.com/
2. **Enable billing** for your project
3. **Upgrade** to paid tier
4. **Much higher quotas:** 1000+ requests/min

**Cost:** Pay-as-you-go (very affordable for personal projects)

---

## 🔄 Switching Between Providers

### **To Use Gemini** (when quota available):

Edit `llm_config.py`:
```python
DEFAULT_PROVIDER = "gemini"
DEFAULT_MODEL = "gemini-2.0-flash-exp"  # Free tier
```

Or set environment variables in `.env`:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash-exp
```

### **To Use OpenAI** (current):

Edit `llm_config.py`:
```python
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"  # Fast & cost-effective
```

Or in `.env`:
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
```

---

## 📋 Gemini Free Tier Limits

### **Rate Limits:**
- **15 requests per minute**
- **1500 requests per day**
- **1 million tokens per day**

### **If You Exceed:**
- ❌ 429 error (quota exceeded)
- ⏱️ Must wait for reset
- 💡 Get new API key or upgrade

### **Tips to Avoid:**
1. **Implement caching** for repeated queries
2. **Add rate limiting** in your code
3. **Monitor usage** at https://ai.dev/usage
4. **Use shorter prompts** to save tokens

---

## 🔐 Best Practices

### **API Key Management:**

```python
# ✅ Good - Use environment variables
api_key = os.getenv("GOOGLE_API_KEY")

# ❌ Bad - Never hardcode keys
api_key = "AIzaSyCbPeR72V_UNxZ..."  # NEVER DO THIS!
```

### **Error Handling:**

```python
from langchain_google_genai import ChatGoogleGenerativeAI

try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7
    )
    response = llm.invoke(prompt)
    
except Exception as e:
    if "429" in str(e) or "quota" in str(e).lower():
        # Quota exceeded - fallback to OpenAI
        print("Gemini quota exceeded, using OpenAI")
        llm = ChatOpenAI(model="gpt-4o-mini")
        response = llm.invoke(prompt)
    else:
        raise
```

### **Rate Limiting Implementation:**

```python
import time
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """
    Simple rate limiter for API calls.
    
    Ensures you don't exceed Gemini's 15 requests/minute limit.
    """
    
    def __init__(self, max_requests: int = 15, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 60s = 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def wait_if_needed(self) -> float:
        """
        Wait if necessary to respect rate limits.
        
        Returns:
            float: Seconds waited (0 if no wait needed)
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.time_window)
        
        # Remove old requests outside time window
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
        
        # If at limit, wait
        if len(self.requests) >= self.max_requests:
            wait_time = (self.requests[0] - cutoff).total_seconds()
            if wait_time > 0:
                print(f"Rate limit: waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                return wait_time
        
        # Record this request
        self.requests.append(now)
        return 0.0

# Usage:
rate_limiter = RateLimiter(max_requests=15, time_window=60)

def call_gemini_api(prompt: str):
    """Make rate-limited API call to Gemini."""
    rate_limiter.wait_if_needed()
    # Make your API call here
    return llm.invoke(prompt)
```

---

## 🧪 Testing Your Setup

Run the diagnostic tool anytime:
```bash
.venv/bin/python diagnose_gemini_api.py
```

**What it checks:**
1. ✅ .env file configuration
2. ✅ API key loading
3. ✅ Key format validation
4. ✅ API connectivity
5. ✅ Free tier model access
6. ✅ System configuration

---

## 📊 Comparing Providers

| Feature | OpenAI (gpt-4o-mini) | Gemini (2.0-flash-exp) |
|---------|---------------------|------------------------|
| **Cost** | ~$0.15/1M tokens | Free (with limits) |
| **Speed** | Very fast | Very fast |
| **Context** | 128K tokens | 1M tokens |
| **Tools** | ✅ Excellent | ✅ Good |
| **Reliability** | ✅ Very high | ⚠️ Quota limits |
| **Best for** | Production | Testing/Development |

---

## 🎯 Recommended Setup

### **For Development:**
```python
# Use OpenAI (more reliable, no quota issues)
DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4o-mini"
```

### **For Production:**
```python
# Use OpenAI with fallback
PRIMARY_PROVIDER = "openai"
FALLBACK_PROVIDER = "gemini"
```

### **For Cost Optimization:**
```python
# Use Gemini with OpenAI fallback
PRIMARY_PROVIDER = "gemini"  # Free tier
FALLBACK_PROVIDER = "openai"  # When quota exceeded
```

---

## 🔧 Quick Fixes

### **Problem: 429 Quota Exceeded**
```bash
# Solution 1: Get new API key
# Go to: https://makersuite.google.com/app/apikey

# Solution 2: Switch to OpenAI
# Edit llm_config.py:
DEFAULT_PROVIDER = "openai"
```

### **Problem: Invalid API Key**
```bash
# Check .env file
cat .env | grep GOOGLE_API_KEY

# Verify key format (should be 39 chars, start with AIza)
# Get new key if needed
```

### **Problem: Gemini Not Available**
```bash
# Check provider status
.venv/bin/python llm_config.py

# Install required package if missing
pip install langchain-google-genai
```

---

## 📚 Additional Resources

- **Get API Keys:** https://makersuite.google.com/app/apikey
- **Check Usage:** https://ai.dev/usage?tab=rate-limit
- **Gemini Docs:** https://ai.google.dev/
- **Rate Limits:** https://ai.google.dev/gemini-api/docs/rate-limits
- **Pricing:** https://ai.google.dev/pricing
- **Google Cloud Console:** https://console.cloud.google.com/

---

## ✅ Next Steps

### **Immediate Action:**

**Option A - Get New Gemini Key:**
1. Visit: https://makersuite.google.com/app/apikey
2. Create new API key
3. Update `.env`: `GOOGLE_API_KEY=new_key_here`
4. Update `llm_config.py`: `DEFAULT_PROVIDER = "gemini"`
5. Restart server

**Option B - Use OpenAI (Already Working):**
1. Keep current configuration (already set to OpenAI)
2. No changes needed
3. Everything works!

### **Long-term:**

1. **Implement rate limiting** to avoid quota issues
2. **Add error handling** with provider fallback
3. **Monitor usage** regularly
4. **Consider paid tier** if needed

---

## 💡 Pro Tips

1. **Keep Both Keys:** Having both OpenAI and Gemini allows fallback
2. **Monitor Costs:** Check usage dashboards regularly
3. **Use Caching:** Cache responses for repeated queries
4. **Implement Retries:** Handle temporary errors gracefully
5. **Test Thoroughly:** Use diagnostic tool before deployment

---

**Your API key is valid - you just need to manage quotas better!** 🎯
