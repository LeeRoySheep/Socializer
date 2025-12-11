# 🔒 Security Notice

## ⚠️ Test Data - Not Real Personal Information

**IMPORTANT:** All email addresses and user data in this repository are **TEST DATA ONLY**.

### Test Data Disclaimer

❌ **NO REAL EMAILS** are stored in this codebase  
❌ **NO REAL USER DATA** is committed to git  
✅ All emails in code/tests are **fake examples** for testing only  
✅ All user data is **encrypted** in production database  

### Examples of Test Data (NOT REAL):

```python
# These are TEST emails only - not real addresses
test_emails = [
    "test@example.com",
    "user@socializer.test", 
    "human2@socializer.com",  # Fake testing email
    "demo@example.org"
]
```

### What is Protected in Production:

1. **Emails**: Hashed with bcrypt (60-char hash, irreversible)
2. **Passwords**: Hashed with bcrypt (never stored in plain text)
3. **Conversation Memory**: Encrypted with Fernet (per-user keys)
4. **User Names**: Not stored (hashed_name field empty)

### Database Files Excluded:

All database files are in `.gitignore`:
- `*.db`
- `*.sqlite`
- `*.sqlite3`
- `data.sqlite.db`

**No production data is ever committed to version control.**

---

## 🔐 Security Standards

This application follows modern security best practices:

✅ **Authentication**: JWT tokens with expiration  
✅ **Password Hashing**: bcrypt with salt (industry standard)  
✅ **Data Encryption**: Fernet symmetric encryption  
✅ **No Plain Text Storage**: All PII encrypted or hashed  
✅ **HTTPS Required**: Production deployment requires TLS  
✅ **Rate Limiting**: Implemented on authentication endpoints  
✅ **Input Validation**: Pydantic models validate all inputs  
✅ **SQL Injection Protection**: SQLAlchemy ORM parameterized queries  

---

## 📧 For Developers

If you see email addresses in:
- Test files (`tests/`)
- Documentation (`docs/`)
- Code examples
- Demo scripts

**These are ALL fake/test emails.**

Real user emails are:
1. Never stored in plain text
2. Hashed before database storage
3. Not accessible even to developers
4. Protected by encryption at rest

---

**Last Updated**: December 1, 2025  
**Security Audit**: See SECURITY_AUDIT.md (to be created)
