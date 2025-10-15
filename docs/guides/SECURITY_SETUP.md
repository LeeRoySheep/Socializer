# Security Setup Guide

This guide explains how to properly configure security settings for the Socializer application.

## 🔒 **Environment Variables Configuration**

### **Step 1: Copy the Example File**

```bash
cp .env.example .env
```

### **Step 2: Generate a Secure SECRET_KEY**

**Option A: Using Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option B: Using OpenSSL**
```bash
openssl rand -base64 32
```

Copy the generated key and paste it into your `.env` file:
```
SECRET_KEY=your-generated-secure-key-here
```

### **Step 3: Configure Database URL**

**For Development (SQLite):**
```
DATABASE_URL=sqlite:///./data/socializer.db
```

**For Production (PostgreSQL):**
```
DATABASE_URL=postgresql://username:password@localhost:5432/socializer_db
```

**Security Note:** Never commit database credentials to git!

### **Step 4: Add API Keys**

#### **OpenAI API Key (for AI features)**
1. Go to https://platform.openai.com/
2. Create an account or log in
3. Navigate to API Keys section
4. Create a new API key
5. Add to `.env`:
   ```
   OPENAI_API_KEY=sk-...your-key-here
   ```

#### **Tavily API Key (for web search)**
1. Go to https://tavily.com/
2. Sign up for an account
3. Get your API key
4. Add to `.env`:
   ```
   TAVILY_API_KEY=tvly-...your-key-here
   ```

### **Step 5: Configure CORS**

Set allowed origins for your frontend:
```
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## 🛡️ **Security Best Practices**

### **1. Environment Variables**

✅ **DO:**
- Use `.env` file for all secrets
- Keep `.env` in `.gitignore`
- Use `.env.example` as a template (no real secrets)
- Rotate keys regularly (every 90 days recommended)
- Use different keys for dev/staging/production

❌ **DON'T:**
- Commit `.env` to git
- Share your `.env` file
- Hardcode secrets in code
- Use default/example keys in production

### **2. JWT Tokens**

**Current Configuration:**
- Algorithm: HS256 (HMAC with SHA-256)
- Expiration: 30 minutes
- Token blacklist: Enabled for logout

**Security Measures:**
```python
# Token includes:
- exp: Expiration timestamp
- sub: Username (subject)
- iat: Issued at timestamp

# Validation includes:
- Signature verification
- Expiration check
- Blacklist check
- User existence check
```

**Recommendations:**
- Keep expiration short (30 minutes is good)
- Implement refresh tokens for longer sessions
- Clear token blacklist periodically (older than max token age)
- Consider Redis for distributed token blacklist

### **3. Password Security**

**Current Implementation:**
- Algorithm: bcrypt
- Log rounds: 12 (configurable in `.env`)
- Automatic salt generation

**Best Practices:**
✅ Current implementation follows OWASP guidelines
- Never store plain-text passwords
- Use bcrypt with 12+ rounds
- Validate password complexity on registration
- Implement account lockout after failed attempts

**Recommended Password Policy:**
```python
# Minimum requirements:
- Length: 8+ characters
- Uppercase: 1+ letters
- Lowercase: 1+ letters
- Numbers: 1+ digits
- Special characters: 1+ symbols
```

### **4. Database Security**

**Current Configuration:**
- ORM: SQLAlchemy (prevents SQL injection)
- Connection: Environment-based URL
- Thread safety: Enabled for SQLite

**Security Checklist:**
- [x] Using ORM (SQL injection protection)
- [x] Environment-based credentials
- [x] Connection pooling configured
- [ ] Database encryption at rest (recommended for production)
- [ ] Regular backups automated
- [ ] Audit logging for sensitive operations

**Recommendations:**
```python
# Add to production config:
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True  # Check connection before use
)
```

### **5. API Security**

**Implemented:**
- [x] JWT authentication
- [x] CORS configuration
- [x] Password hashing
- [x] Token expiration

**Recommended (Future):**
- [ ] Rate limiting per IP
- [ ] Rate limiting per user
- [ ] Request size limits
- [ ] Security headers middleware
- [ ] API versioning
- [ ] Request validation

**Example Rate Limiting (to implement):**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request):
    ...
```

### **6. WebSocket Security**

**Implemented:**
- [x] Token-based authentication
- [x] User validation on connect
- [x] Room authorization

**Recommended (Future):**
- [ ] Message size limits
- [ ] Connection rate limiting
- [ ] Message rate limiting per user
- [ ] Disconnect on auth failure

### **7. HTTPS/TLS**

**For Production:**
```python
# Use a reverse proxy (nginx/caddy) with TLS
# Or configure uvicorn with SSL:

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile=/path/to/key.pem \
    --ssl-certfile=/path/to/cert.pem
```

**Security Headers (nginx example):**
```nginx
# Add to nginx config
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
```

---

## 🔍 **Security Checklist**

### **Before Deployment:**

#### **Environment:**
- [ ] `.env` file created with secure values
- [ ] SECRET_KEY is unique and random (32+ characters)
- [ ] Database credentials are secure
- [ ] API keys are valid and active
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has no real secrets

#### **Application:**
- [ ] DEBUG mode is False in production
- [ ] HTTPS/TLS enabled
- [ ] CORS configured for your domain only
- [ ] Security headers enabled
- [ ] Rate limiting enabled
- [ ] Error messages don't leak sensitive info

#### **Database:**
- [ ] Database backups automated
- [ ] Connection pooling configured
- [ ] Credentials rotated regularly
- [ ] Audit logging enabled
- [ ] Access restricted by firewall

#### **Monitoring:**
- [ ] Failed login attempts logged
- [ ] API errors monitored
- [ ] Unusual activity alerts set up
- [ ] Security logs reviewed regularly

---

## 🚨 **Incident Response**

### **If API Key is Compromised:**
1. Immediately revoke the key from provider
2. Generate new key
3. Update `.env` file
4. Restart application
5. Review logs for suspicious activity
6. Rotate all other keys as precaution

### **If Database is Compromised:**
1. Disconnect database from internet
2. Change all database credentials
3. Audit all database access logs
4. Reset all user passwords
5. Notify affected users
6. Review and patch security vulnerability

### **If SECRET_KEY is Compromised:**
1. Generate new SECRET_KEY immediately
2. Update `.env` and restart app
3. All existing JWT tokens become invalid
4. Users will need to log in again
5. Review code for any key leakage
6. Check git history for exposed keys

---

## 📋 **Security Audit Log**

| Date | Action | Details |
|------|--------|---------|
| 2025-10-15 | Security audit | Fixed hardcoded SECRET_KEY in auth.py |
| 2025-10-15 | Configuration | Created .env.example template |
| 2025-10-15 | Documentation | Created security setup guide |

---

## 📚 **Additional Resources**

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/core/security.html)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated:** 2025-10-15  
**Maintained By:** Security Team  
**Review Schedule:** Quarterly
