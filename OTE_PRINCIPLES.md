# 🎯 OTE Principles for Socializer

**Date:** November 12, 2024  
**Purpose:** Maintain Observability, Traceability, and Evaluation throughout optimization

---

## 📊 **O**bservability

### **Principle:**
Every operation should be observable with timestamps and context.

### **Implementation:**

**1. Comprehensive Logging:**
```python
import logging
import time
from datetime import datetime
from functools import wraps

class OTELogger:
    """Logger with OTE principles: Observability, Traceability, Evaluation."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.metrics = {}
    
    def log_operation(self, operation: str, **kwargs):
        """
        Log operation with timestamp and context.
        
        Args:
            operation: Name of operation
            **kwargs: Additional context
        """
        timestamp = datetime.now().isoformat()
        self.logger.info(f"[{timestamp}] {operation}", extra=kwargs)
```

**2. Decorator for Timing:**
```python
def observe(operation_name: str):
    """
    Decorator to observe function execution with timing.
    
    Provides:
    - Entry/exit timestamps
    - Execution duration
    - Exception tracking
    - Return value logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_timestamp = datetime.now().isoformat()
            
            logger.info(f"⏱️  START [{start_timestamp}] {operation_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"✅ END [{datetime.now().isoformat()}] {operation_name} "
                    f"(Duration: {duration:.3f}s)"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"❌ FAILED [{datetime.now().isoformat()}] {operation_name} "
                    f"(Duration: {duration:.3f}s) Error: {str(e)}"
                )
                raise
        
        return wrapper
    return decorator
```

**3. Usage Example:**
```python
@observe("user_preference_save")
def save_preference(user_id: int, pref_type: str, value: str):
    """Save user preference with observable logging."""
    # Implementation
    pass
```

---

## 🔍 **T**raceability

### **Principle:**
Code should be easy to trace for debugging and changes.

### **Implementation:**

**1. Clear Module Structure:**
```python
"""
User Preference Tool Module

LOCATION: app/tools/user/preference_tool.py
PURPOSE: Manage user preferences with encryption
DEPENDENCIES: 
    - app.datamanager.DataManager
    - app.memory.UserMemoryEncryptor
    
TRACE POINTS:
    - Entry: UserPreferenceTool.__init__()
    - Save: UserPreferenceTool._save_preference()
    - Retrieve: UserPreferenceTool._get_preference()
    - Encryption: UserMemoryEncryptor.encrypt()
    
RELATED:
    - Data Model: datamanager/data_model.py (User.preferences)
    - Encryption: memory/user_memory_encryptor.py
    - API: app/routers/user.py
"""
```

**2. Traceable Error Messages:**
```python
def save_preference(user_id: int, pref_type: str, value: str):
    """
    Save user preference with traceability.
    
    Trace Path:
        1. Validate input
        2. Encrypt if sensitive
        3. Save to database
        4. Log operation
    """
    try:
        # TRACE POINT 1: Validation
        if not user_id:
            raise ValueError(
                "TRACE: save_preference -> validation_failed "
                "| user_id is required"
            )
        
        # TRACE POINT 2: Encryption
        if self._is_sensitive(pref_type):
            value = self.encryptor.encrypt(value)
            logger.debug(f"TRACE: save_preference -> encrypted {pref_type}")
        
        # TRACE POINT 3: Database save
        result = self.db.save(user_id, pref_type, value)
        logger.debug(f"TRACE: save_preference -> saved to DB")
        
        return result
        
    except Exception as e:
        logger.error(
            f"TRACE: save_preference -> FAILED at {e.__traceback__.tb_lineno} "
            f"| Error: {str(e)}"
        )
        raise
```

**3. Call Stack Documentation:**
```python
"""
Call Stack for User Message Processing:

1. WebSocket receives message
   → app/routers/websocket.py:handle_message()
   
2. Message routed to AI agent
   → app/agents/chatagent.py:process_message()
   
3. LLM invoked with tools
   → app/llm/manager.py:invoke()
   
4. Tool execution if needed
   → app/tools/base/executor.py:execute()
   
5. Response formatted
   → app/agents/response_handler.py:format()
   
6. Result sent to WebSocket
   → app/routers/websocket.py:send_response()

Each step logs with TRACE markers for debugging.
"""
```

---

## 📈 **E**valuation

### **Principle:**
Track metrics to evaluate performance and find optimization opportunities.

### **Implementation:**

**1. Performance Metrics:**
```python
class PerformanceMetrics:
    """
    Track performance metrics for evaluation.
    
    Metrics tracked:
    - Execution time per operation
    - Success/failure rates
    - Resource usage
    - API call counts
    - Token usage
    - Cost per operation
    """
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'successes': 0,
            'failures': 0,
            'avg_time': 0
        })
    
    def record(self, operation: str, duration: float, success: bool):
        """Record operation metrics for evaluation."""
        m = self.metrics[operation]
        m['count'] += 1
        m['total_time'] += duration
        m['successes'] += 1 if success else 0
        m['failures'] += 0 if success else 1
        m['avg_time'] = m['total_time'] / m['count']
    
    def report(self) -> Dict[str, Any]:
        """Generate evaluation report."""
        return {
            op: {
                'calls': m['count'],
                'avg_time': f"{m['avg_time']:.3f}s",
                'success_rate': f"{(m['successes']/m['count']*100):.1f}%",
                'total_time': f"{m['total_time']:.3f}s"
            }
            for op, m in self.metrics.items()
        }
```

**2. Comparison Framework:**
```python
class ComparisonFramework:
    """
    Compare different implementations for optimization.
    
    Example:
        Compare LLM providers (OpenAI vs Claude vs Gemini)
        Compare tool execution strategies
        Compare caching vs non-caching
    """
    
    def compare(self, implementations: List[Callable], test_cases: List[Any]):
        """
        Compare implementations across test cases.
        
        Returns:
            DataFrame with comparison metrics
        """
        results = []
        
        for impl in implementations:
            for test_case in test_cases:
                start = time.time()
                
                try:
                    result = impl(test_case)
                    duration = time.time() - start
                    
                    results.append({
                        'implementation': impl.__name__,
                        'test_case': str(test_case),
                        'duration': duration,
                        'success': True,
                        'result': result
                    })
                except Exception as e:
                    duration = time.time() - start
                    results.append({
                        'implementation': impl.__name__,
                        'test_case': str(test_case),
                        'duration': duration,
                        'success': False,
                        'error': str(e)
                    })
        
        return pd.DataFrame(results)
```

**3. Bug Detection:**
```python
class AnomalyDetector:
    """
    Detect anomalies in metrics for bug finding.
    
    Detects:
    - Sudden performance degradation
    - Increased error rates
    - Memory leaks
    - Unusual patterns
    """
    
    def detect_anomalies(self, metrics: PerformanceMetrics) -> List[str]:
        """
        Analyze metrics to find potential bugs.
        
        Returns:
            List of detected anomalies with descriptions
        """
        anomalies = []
        
        for operation, data in metrics.metrics.items():
            # Check error rate
            error_rate = data['failures'] / data['count']
            if error_rate > 0.1:  # >10% errors
                anomalies.append(
                    f"⚠️  HIGH ERROR RATE in {operation}: "
                    f"{error_rate*100:.1f}% (threshold: 10%)"
                )
            
            # Check slow operations
            if data['avg_time'] > 5.0:  # >5 seconds
                anomalies.append(
                    f"🐌 SLOW OPERATION {operation}: "
                    f"{data['avg_time']:.2f}s (threshold: 5s)"
                )
        
        return anomalies
```

---

## 🏗️ Integration into Code Structure

### **Every Module Will Have:**

**1. OTE Logger:**
```python
from app.utils.ote_logger import OTELogger

logger = OTELogger(__name__)
```

**2. Observable Methods:**
```python
@observe("operation_name")
def method(self, *args, **kwargs):
    """Method with OTE logging."""
    pass
```

**3. Traceable Errors:**
```python
try:
    # operation
except Exception as e:
    logger.error(f"TRACE: {self.__class__.__name__}.method -> {str(e)}")
    raise
```

**4. Performance Tracking:**
```python
from app.utils.metrics import metrics_tracker

metrics_tracker.record("operation", duration, success)
```

---

## 📊 Example: Complete OTE Implementation

```python
"""
User Preference Tool with Full OTE

LOCATION: app/tools/user/preference_tool.py
PURPOSE: Manage user preferences
TRACE: See call stack documentation below
"""

from typing import Dict, Any, Optional
from app.utils.ote_logger import OTELogger, observe
from app.utils.metrics import metrics_tracker
from datetime import datetime
import time

logger = OTELogger(__name__)

class UserPreferenceTool:
    """
    User preference management tool with OTE compliance.
    
    OTE Compliance:
    - O: All operations logged with timestamps
    - T: Clear trace paths in docstrings
    - E: Performance metrics tracked
    
    Attributes:
        dm (DataManager): Database access
        encryptor (UserMemoryEncryptor): Encryption handler
        metrics (PerformanceMetrics): Evaluation tracker
    """
    
    def __init__(self, data_manager):
        """
        Initialize preference tool.
        
        TRACE: Entry point for preference operations
        
        Args:
            data_manager: Database manager instance
        """
        logger.log_operation("preference_tool_init", timestamp=datetime.now())
        self.dm = data_manager
        self.encryptor = UserMemoryEncryptor()
    
    @observe("save_preference")
    def save(self, user_id: int, pref_type: str, value: str) -> Dict[str, Any]:
        """
        Save user preference with OTE logging.
        
        TRACE PATH:
            1. UserPreferenceTool.save()
            2. → _validate_input()
            3. → _encrypt_if_sensitive()
            4. → DataManager.save_preference()
            5. → metrics_tracker.record()
        
        Observability:
            - Entry/exit logged with timestamps
            - Duration tracked
            - Success/failure recorded
        
        Traceability:
            - Each step logged with TRACE marker
            - Errors include trace path
            - Call stack documented
        
        Evaluation:
            - Execution time recorded
            - Success rate tracked
            - Metrics available for comparison
        
        Args:
            user_id: User ID
            pref_type: Preference type
            value: Preference value
            
        Returns:
            Dict with status and result
            
        Raises:
            ValueError: If validation fails (TRACE logged)
            EncryptionError: If encryption fails (TRACE logged)
        """
        start_time = time.time()
        success = False
        
        try:
            # TRACE POINT 1: Validation
            logger.debug(f"TRACE: save → validate (user={user_id}, type={pref_type})")
            self._validate_input(user_id, pref_type, value)
            
            # TRACE POINT 2: Encryption check
            if self._is_sensitive(pref_type):
                logger.debug(f"TRACE: save → encrypt ({pref_type})")
                value = self.encryptor.encrypt(value)
            
            # TRACE POINT 3: Database save
            logger.debug(f"TRACE: save → database.save")
            result = self.dm.save_preference(user_id, pref_type, value)
            
            success = True
            
            return {
                "status": "success",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"TRACE: save → FAILED | "
                f"user={user_id} | type={pref_type} | "
                f"error={str(e)}"
            )
            raise
            
        finally:
            # EVALUATION: Record metrics
            duration = time.time() - start_time
            metrics_tracker.record("save_preference", duration, success)
            
            logger.debug(
                f"EVALUATION: save_preference | "
                f"duration={duration:.3f}s | "
                f"success={success}"
            )
```

---

## 🎯 OTE Checklist for Each Module

### **Observability:**
- [ ] All public methods have `@observe` decorator
- [ ] All operations log entry/exit with timestamps
- [ ] All errors log with context
- [ ] Performance data captured

### **Traceability:**
- [ ] Module docstring includes LOCATION
- [ ] Module docstring includes TRACE POINTS
- [ ] Module docstring includes DEPENDENCIES
- [ ] Methods document TRACE PATH
- [ ] Errors include trace information

### **Evaluation:**
- [ ] Metrics tracked for all operations
- [ ] Success/failure rates recorded
- [ ] Duration tracked
- [ ] Comparison data available
- [ ] Anomaly detection possible

---

## 📈 Benefits

### **Development:**
- Faster debugging (clear trace paths)
- Easy performance optimization (metrics)
- Quick issue identification (observability)

### **Production:**
- Monitor system health
- Identify bottlenecks
- Track improvements over time
- Compare different approaches

### **Maintenance:**
- Understand code flow quickly
- Find where to make changes
- Verify fixes work
- Prevent regressions

---

## 🚀 Next Steps

1. ✅ Create OTE utility modules
2. ✅ Apply to all refactored code
3. ✅ Add to testing framework
4. ✅ Create metrics dashboard
5. ✅ Document patterns

---

**All optimization work will follow these OTE principles!** 🎯

