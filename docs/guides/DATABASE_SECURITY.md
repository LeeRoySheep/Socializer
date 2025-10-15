# Database Security Best Practices

**Socializer Project**  
**Last Updated:** 2025-10-15

---

## 🎯 **Overview**

This guide covers database security best practices for the Socializer application,
including connection security, data protection, access control, and audit logging.

---

## 🔒 **Current Security Status**

### **✅ What's Already Implemented**

1. **ORM Protection**
   - Using SQLAlchemy ORM prevents SQL injection
   - Parameterized queries throughout codebase
   - No raw SQL string concatenation

2. **Connection Management**
   - Database URL from environment variables
   - Connection pooling configured
   - Proper session lifecycle management

3. **Password Security**
   - Bcrypt hashing for all passwords
   - 12+ bcrypt rounds (configurable)
   - No plain-text passwords stored

4. **Access Control**
   - JWT token-based authentication
   - User authentication required for all sensitive operations
   - Role-based access in place

### **⚠️ Areas for Improvement**

1. Database encryption at rest
2. Connection pool size limits
3. Query timeout configuration
4. Audit logging for sensitive operations
5. Database backup automation
6. Rate limiting on database operations

---

## 🗄️ **Database Configuration**

### **Current Setup (SQLite - Development)**

```python
# app/config.py
DATABASE_PATH = db_dir / "socializer.db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
```

### **Recommended Production Setup (PostgreSQL)**

```python
# .env (Production)
DATABASE_URL=postgresql://username:password@localhost:5432/socializer_prod

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

### **Enhanced Database Configuration**

```python
# app/database.py - Enhanced version
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database settings from environment
DATABASE_URL = os.getenv("DATABASE_URL")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Create engine with enhanced security settings
engine_kwargs = {
    "pool_pre_ping": True,  # Check connection health before use
    "pool_recycle": DB_POOL_RECYCLE,  # Recycle connections after 1 hour
    "echo": False,  # Don't log all SQL (security risk)
}

# Add connection pooling for non-SQLite databases
if not DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "poolclass": QueuePool,
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "pool_timeout": DB_POOL_TIMEOUT,
    })
else:
    # SQLite-specific settings
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
        "timeout": 30,  # 30 second timeout for locks
    }

engine = create_engine(DATABASE_URL, **engine_kwargs)

# Enable query logging for debugging (disable in production)
if os.getenv("DEBUG") == "True":
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Session factory with security settings
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Prevent lazy-loading after commit
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency with automatic cleanup.
    
    OBSERVABILITY:
    - Logs session creation and closure
    - Tracks active session count
    
    TRACEABILITY:
    - Associates sessions with request IDs
    
    EVALUATION:
    - Ensures sessions are always closed
    - Rolls back on error
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Event listeners for security monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections."""
    logger.info("New database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkouts from pool."""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection returns to pool."""
    logger.debug("Connection returned to pool")
```

---

## 🔐 **SQL Injection Prevention**

### **✅ Always Use ORM**

```python
# ✅ SAFE: Using ORM with parameters
user = db.query(User).filter(User.username == username).first()

# ✅ SAFE: Using bound parameters
stmt = select(User).where(User.email == email)
user = db.execute(stmt).scalars().first()

# ❌ DANGEROUS: String concatenation
query = f"SELECT * FROM users WHERE username = '{username}'"  # SQL injection risk!
db.execute(query)

# ❌ DANGEROUS: String formatting
query = "SELECT * FROM users WHERE email = '%s'" % email  # SQL injection risk!
```

### **If Raw SQL is Absolutely Necessary**

```python
from sqlalchemy import text

# ✅ SAFE: Using text() with bound parameters
stmt = text("SELECT * FROM users WHERE username = :username")
user = db.execute(stmt, {"username": username}).first()

# ✅ SAFE: Using named parameters
stmt = text("SELECT * FROM orders WHERE user_id = :user_id AND status = :status")
orders = db.execute(stmt, {"user_id": user_id, "status": "active"}).fetchall()
```

---

## 🔑 **Access Control**

### **Row-Level Security**

```python
class DataManager:
    """
    Database operations with built-in access control.
    
    EVALUATION:
    - Verifies user owns resource before access
    - Checks user permissions for operations
    - Logs unauthorized access attempts
    """
    
    def get_user_messages(self, user_id: int, room_id: int) -> List[Message]:
        """
        Get messages for a user in a specific room.
        
        SECURITY:
        - Only returns messages from rooms user has access to
        - Filters out deleted/hidden messages
        - Respects privacy settings
        """
        # Check room membership
        membership = self.db.query(RoomMembership).filter(
            RoomMembership.user_id == user_id,
            RoomMembership.room_id == room_id
        ).first()
        
        if not membership:
            logger.warning(f"User {user_id} attempted to access room {room_id} without membership")
            raise PermissionError("Not a member of this room")
        
        # Get messages with security filter
        messages = self.db.query(Message).filter(
            Message.room_id == room_id,
            Message.deleted_at == None  # Exclude deleted messages
        ).order_by(Message.created_at.desc()).limit(100).all()
        
        logger.info(f"User {user_id} accessed {len(messages)} messages from room {room_id}")
        return messages
```

### **Permission Checking**

```python
def require_permission(permission: str):
    """
    Decorator to check user permissions before database operations.
    """
    def decorator(func):
        def wrapper(self, user_id: int, *args, **kwargs):
            if not self.user_has_permission(user_id, permission):
                logger.warning(f"User {user_id} denied access: missing {permission}")
                raise PermissionError(f"Missing permission: {permission}")
            return func(self, user_id, *args, **kwargs)
        return wrapper
    return decorator

class AdminDataManager(DataManager):
    @require_permission("admin.delete_user")
    def delete_user(self, admin_id: int, target_user_id: int):
        """Delete a user (admin only)."""
        # Implementation...
        logger.info(f"Admin {admin_id} deleted user {target_user_id}")
```

---

## 📊 **Audit Logging**

### **Sensitive Operations Logging**

```python
class AuditLog(Base):
    """
    Audit log for tracking sensitive database operations.
    
    TRACEABILITY:
    - Records who performed action
    - Timestamps all operations
    - Stores before/after state for updates
    - Maintains immutable log entries
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)  # CREATE, READ, UPDATE, DELETE
    table_name = Column(String, nullable=False)
    record_id = Column(Integer)
    old_values = Column(JSON)  # State before change
    new_values = Column(JSON)  # State after change
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def log_audit(db: Session, user_id: int, action: str, table: str, record_id: int, 
               old: dict = None, new: dict = None, request = None):
    """
    Log sensitive database operation.
    
    OBSERVABILITY:
    - Tracks all CREATE/UPDATE/DELETE operations
    - Records user and timestamp
    - Captures request metadata
    
    EVALUATION:
    - Validates required fields
    - Ensures immutability of logs
    """
    audit = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table,
        record_id=record_id,
        old_values=old,
        new_values=new,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit)
    db.commit()
    
    logger.info(f"Audit: User {user_id} performed {action} on {table}#{record_id}")
```

### **Usage Example**

```python
def update_user_profile(db: Session, user_id: int, updates: dict, request):
    """Update user profile with audit logging."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise ValueError("User not found")
    
    # Capture old state
    old_values = {
        "username": user.username,
        "email": user.email,
        "bio": user.bio
    }
    
    # Apply updates
    for key, value in updates.items():
        setattr(user, key, value)
    
    db.commit()
    
    # Log the change
    log_audit(
        db=db,
        user_id=user_id,
        action="UPDATE",
        table="users",
        record_id=user.id,
        old=old_values,
        new=updates,
        request=request
    )
```

---

## 💾 **Data Encryption**

### **Encrypting Sensitive Fields**

```python
from cryptography.fernet import Fernet
import base64

class EncryptedField:
    """
    Encrypted database field for sensitive data.
    
    SECURITY:
    - Uses Fernet symmetric encryption
    - Key stored in environment variable
    - Transparent encryption/decryption
    """
    
    def __init__(self, key: str):
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, value: str) -> str:
        """Encrypt a value."""
        if not value:
            return value
        encrypted = self.cipher.encrypt(value.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a value."""
        if not encrypted:
            return encrypted
        decoded = base64.b64decode(encrypted.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()

# Usage in models
ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")
encryptor = EncryptedField(ENCRYPTION_KEY)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email_encrypted = Column(String)  # Stored encrypted
    
    @property
    def email(self):
        """Decrypt email when accessed."""
        return encryptor.decrypt(self.email_encrypted)
    
    @email.setter
    def email(self, value):
        """Encrypt email when set."""
        self.email_encrypted = encryptor.encrypt(value)
```

---

## 🔄 **Backup & Recovery**

### **Automated Backup Script**

```bash
#!/bin/bash
# backup_database.sh

# Configuration
BACKUP_DIR="/var/backups/socializer"
DB_NAME="socializer_prod"
DB_USER="socializer"
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/socializer_${TIMESTAMP}.sql.gz"

# PostgreSQL backup
echo "Starting database backup..."
pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"

# Check if backup was successful
if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Remove backups older than retention period
    find "$BACKUP_DIR" -name "socializer_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Old backups cleaned up (retention: ${RETENTION_DAYS} days)"
else
    echo "Backup failed!"
    exit 1
fi
```

### **Backup Schedule (crontab)**

```bash
# Run daily backup at 2 AM
0 2 * * * /path/to/backup_database.sh >> /var/log/socializer_backup.log 2>&1

# Run weekly full backup on Sundays at 3 AM
0 3 * * 0 /path/to/full_backup.sh >> /var/log/socializer_backup.log 2>&1
```

---

## 🛡️ **Security Checklist**

### **Development**
- [x] Using ORM (SQLAlchemy) for all queries
- [x] Environment-based database credentials
- [x] Password hashing with bcrypt
- [x] Connection pooling configured
- [ ] Query timeout settings
- [ ] Database audit logging

### **Production**
- [ ] PostgreSQL with SSL/TLS enabled
- [ ] Database encryption at rest
- [ ] Regular automated backups
- [ ] Backup recovery tested
- [ ] Database firewall rules
- [ ] Connection from app server only
- [ ] Monitoring and alerting
- [ ] Rate limiting on database operations

### **Access Control**
- [x] JWT token authentication
- [x] Row-level permission checks
- [ ] Role-based access control (RBAC)
- [ ] API rate limiting
- [ ] Account lockout after failed attempts

---

## 🚨 **Security Incident Response**

### **Database Breach Response**

1. **Immediate Actions:**
   - Disconnect database from internet
   - Revoke all access credentials
   - Enable maintenance mode
   - Preserve logs for forensics

2. **Investigation:**
   - Review audit logs
   - Identify compromised data
   - Determine breach scope
   - Document timeline

3. **Recovery:**
   - Restore from clean backup
   - Reset all passwords
   - Rotate encryption keys
   - Update security measures

4. **Notification:**
   - Notify affected users
   - Report to authorities if required
   - Document incident for review

---

## 📚 **Additional Resources**

- [OWASP Database Security](https://owasp.org/www-community/vulnerabilities/)
- [PostgreSQL Security Best Practices](https://www.postgresql.org/docs/current/security.html)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/core/security.html)
- [PCI DSS Database Security](https://www.pcisecuritystandards.org/)

---

**Last Updated:** 2025-10-15  
**Review Schedule:** Quarterly  
**Next Review:** 2025-04-15
