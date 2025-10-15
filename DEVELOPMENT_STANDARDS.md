# 🎯 Development Standards - Socializer Project

**Date:** 2025-10-15  
**Status:** Active Guidelines  

---

## 📋 Core Principles

This project follows three key development methodologies:

1. **TDD** - Test-Driven Development
2. **OOP** - Object-Oriented Programming
3. **O-T-E** - Observability, Traceability, Evaluation

---

## 🧪 Test-Driven Development (TDD)

### **The TDD Cycle**

```
1. RED    → Write failing test first
2. GREEN  → Write minimal code to pass
3. REFACTOR → Clean up code
4. REPEAT → Next feature
```

### **TDD Rules**

✅ **DO:**
- Write test BEFORE implementation
- One test per feature/behavior
- Test both positive and negative cases
- Keep tests isolated and independent
- Use descriptive test names

❌ **DON'T:**
- Write production code without test
- Test implementation details
- Create test dependencies
- Skip negative/edge cases

### **Test Structure**

```python
def test_feature_name_when_condition_then_result():
    """
    TEST: Brief description of what we're testing.
    
    OBSERVABILITY: Log all steps
    TRACEABILITY: Track relevant IDs
    EVALUATION: Clear assertions
    """
    # ARRANGE: Set up test data
    print("[STEP 1] Setting up test data")
    data = create_test_data()
    
    # ACT: Execute the behavior
    print("[STEP 2] Executing feature")
    result = feature_under_test(data)
    
    # ASSERT: Verify the outcome
    print("[STEP 3] Verifying result")
    assert result == expected, "[EVAL] Result should match expected"
    
    print("[SUCCESS] ✅ Test passed")
```

---

## 🏗️ Object-Oriented Programming (OOP)

### **SOLID Principles**

#### **S - Single Responsibility Principle**
- One class = One responsibility
- One file per class (max 2 if tightly coupled)
- Clear, focused purpose

```python
# ✅ GOOD: Single responsibility
class RoomManager:
    """Manages room lifecycle: create, update, delete."""
    def create_room(self): ...
    def update_room(self): ...
    def delete_room(self): ...

# ❌ BAD: Multiple responsibilities
class RoomAndUserAndMessageManager:
    def create_room(self): ...
    def create_user(self): ...
    def send_message(self): ...
```

#### **O - Open/Closed Principle**
- Open for extension, closed for modification
- Use inheritance/composition

```python
# ✅ GOOD: Extensible
class BaseTool:
    def execute(self): ...

class ConversationTool(BaseTool):
    def execute(self): ...  # Extends without modifying base
```

#### **L - Liskov Substitution Principle**
- Subclasses must be substitutable for base class
- Don't break contracts

#### **I - Interface Segregation**
- Many specific interfaces > One general interface
- Don't force unused methods

#### **D - Dependency Inversion**
- Depend on abstractions, not concretions
- Use dependency injection

```python
# ✅ GOOD: Dependency injection
class RoomService:
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager

# ❌ BAD: Hard dependency
class RoomService:
    def __init__(self):
        self.dm = DataManager()  # Hard-coded!
```

### **Class Documentation**

Every class must have:

```python
class MyClass:
    """
    Brief one-line description.
    
    Longer description explaining purpose, when to use,
    and any important considerations.
    
    Attributes:
        attr1 (Type): Description
        attr2 (Type): Description
    
    Example:
        >>> obj = MyClass(param1, param2)
        >>> result = obj.method()
        >>> print(result)
        expected_output
    
    Notes:
        - Implementation details
        - Performance considerations
        - Thread safety notes
    """
```

### **Method Documentation**

Every method must have:

```python
def method_name(self, param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief description of what this method does.
    
    Args:
        param1 (Type1): Description of param1
            - Valid values or constraints
        param2 (Type2): Description of param2
    
    Returns:
        ReturnType: Description of return value
            - Structure if dict/list
            - Possible values
    
    Raises:
        ExceptionType: When and why
    
    Example:
        >>> result = obj.method_name(arg1, arg2)
        >>> print(result)
        expected_output
    """
```

---

## 📊 Observability-Traceability-Evaluation (O-T-E)

### **Observability 🔍**

**What:** Every operation must be visible in logs.

**Log Levels:**
- `[TRACE]` - Normal operation flow
- `[EVAL]` - Validation/evaluation checks
- `[ERROR]` - Errors with full context

**Example:**
```python
def create_room(self, creator_id: int, name: str, password: str = None):
    """Create a new room."""
    # OBSERVABILITY: Log operation start
    print(f"[TRACE] create_room: creator_id={creator_id}, name={name}, protected={bool(password)}")
    
    try:
        room = Room(...)
        session.add(room)
        session.commit()
        
        # OBSERVABILITY: Log success
        print(f"[TRACE] create_room success: room_id={room.id}")
        return room
        
    except Exception as e:
        # OBSERVABILITY: Log error with context
        print(f"[ERROR] create_room failed: creator_id={creator_id}, error={e}")
        return None
```

**Observability Checklist:**
- [ ] Operation start logged with parameters
- [ ] Success logged with resulting IDs
- [ ] Errors logged with full context
- [ ] All branches have logs
- [ ] Sensitive data (passwords) NOT logged

---

### **Traceability 📋**

**What:** Track entities through their entire lifecycle.

**Required IDs:**
- `user_id` - Who performed the action
- `room_id` - Which room
- `message_id` - Which message
- `invite_id` - Which invite
- `session_id` - Which session (if applicable)

**Example:**
```python
def accept_invite(self, invite_id: int, user_id: int):
    """Accept room invite."""
    # TRACEABILITY: Log all relevant IDs
    print(f"[TRACE] accept_invite: invite_id={invite_id}, user_id={user_id}")
    
    invite = get_invite(invite_id)
    room_id = invite.room_id
    
    # TRACEABILITY: Track through operations
    print(f"[TRACE] Adding user {user_id} to room {room_id}")
    
    add_member(room_id, user_id)
    
    # TRACEABILITY: Log final state
    print(f"[TRACE] accept_invite success: user_id={user_id}, room_id={room_id}")
```

**Traceability Checklist:**
- [ ] All entity IDs logged
- [ ] State changes logged
- [ ] Can reconstruct operation flow from logs
- [ ] Timestamps included (automatically via logging)

---

### **Evaluation 📊**

**What:** Validate at every step, with clear success/failure criteria.

**Evaluation Points:**
1. **Input Validation** - Check parameters
2. **Authorization** - Verify permissions
3. **Business Logic** - Apply rules
4. **State Consistency** - Verify final state

**Example:**
```python
def accept_invite(self, invite_id: int, user_id: int):
    """Accept invite with full evaluation."""
    
    # EVALUATION: Check invite exists
    invite = get_invite(invite_id)
    if not invite:
        print(f"[EVAL] accept_invite failed: invite {invite_id} not found")
        return False
    
    # EVALUATION: Check user is invitee
    if invite.invitee_id != user_id:
        print(f"[EVAL] accept_invite failed: user {user_id} not invitee (expected {invite.invitee_id})")
        return False
    
    # EVALUATION: Check status
    if invite.status != 'pending':
        print(f"[EVAL] accept_invite failed: status '{invite.status}', expected 'pending'")
        return False
    
    # All checks passed
    print(f"[EVAL] All validations passed")
    return True
```

**Evaluation Checklist:**
- [ ] All inputs validated
- [ ] Authorization checked
- [ ] Business rules enforced
- [ ] State verified after operation
- [ ] Clear success/failure conditions

---

## 🔄 Development Workflow

### **Step-by-Step Process**

#### **Phase 1: Design**
1. Define the feature clearly
2. Identify inputs and outputs
3. Consider edge cases
4. Plan O-T-E points

#### **Phase 2: Write Test (TDD - RED)**
```python
def test_new_feature():
    """Test the feature we're about to build."""
    # Arrange
    setup_test_data()
    
    # Act
    result = new_feature(test_input)
    
    # Assert
    assert result == expected
```

#### **Phase 3: Run Test (Should FAIL)**
```bash
pytest tests/test_new_feature.py -v
# Expected: FAILED (feature not implemented yet)
```

#### **Phase 4: Implement (TDD - GREEN)**
```python
def new_feature(input_data):
    """
    Implement the feature.
    
    OBSERVABILITY: Log operations
    TRACEABILITY: Track IDs
    EVALUATION: Validate inputs
    """
    print(f"[TRACE] new_feature: input={input_data}")
    
    # EVALUATION: Validate input
    if not input_data:
        print(f"[EVAL] new_feature failed: invalid input")
        return None
    
    # Implementation
    result = process(input_data)
    
    print(f"[TRACE] new_feature success: result={result}")
    return result
```

#### **Phase 5: Run Test (Should PASS)**
```bash
pytest tests/test_new_feature.py -v
# Expected: PASSED
```

#### **Phase 6: Refactor (TDD - REFACTOR)**
- Clean up code
- Improve readability
- Ensure O-T-E standards
- Run tests again (should still pass)

#### **Phase 7: Document**
- Update docstrings
- Update README if needed
- Create summary markdown

---

## 📁 Project Structure

```
Socializer/
├── app/
│   ├── routers/           # API endpoints (one router per domain)
│   │   ├── auth.py        # Authentication routes
│   │   ├── rooms.py       # Room management routes
│   │   └── chat.py        # Chat routes
│   ├── services/          # Business logic (one service per domain)
│   │   ├── auth_service.py
│   │   ├── room_service.py
│   │   └── chat_service.py
│   └── main.py            # App initialization only
│
├── datamanager/           # Data access layer
│   ├── data_manager.py    # Database operations
│   ├── data_model.py      # SQLAlchemy models
│   └── migrations/        # Database migrations
│
├── chat_agent/            # AI agent (after refactoring)
│   ├── core/              # Core agent logic
│   │   ├── agent.py       # Main agent class
│   │   └── base_agent.py  # Base classes
│   ├── tools/             # AI tools (one file per tool)
│   │   ├── base.py
│   │   ├── conversation_recall_tool.py
│   │   ├── skill_evaluator_tool.py
│   │   └── ...
│   ├── graph/             # Graph components
│   │   ├── state.py
│   │   └── tool_node.py
│   └── models/            # Data models
│       └── user_data.py
│
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   │   ├── test_room_manager.py
│   │   └── ...
│   ├── integration/       # Integration tests
│   │   ├── test_room_flow.py
│   │   └── ...
│   └── conftest.py        # Pytest fixtures
│
├── static/                # Frontend files
│   ├── js/
│   │   ├── chat/          # Chat modules
│   │   │   ├── PrivateRooms.js
│   │   │   └── ...
│   │   └── auth/          # Auth modules
│   └── css/
│
└── docs/                  # Documentation
    ├── DEVELOPMENT_STANDARDS.md  # This file
    ├── API_DOCS.md
    └── ...
```

---

## ✅ Code Review Checklist

Before committing code, verify:

### **TDD:**
- [ ] Tests written first
- [ ] All tests pass
- [ ] Both positive and negative cases tested
- [ ] Edge cases covered

### **OOP:**
- [ ] Single responsibility per class
- [ ] One class per file
- [ ] SOLID principles followed
- [ ] Proper inheritance/composition

### **Observability:**
- [ ] All operations logged
- [ ] [TRACE] for normal flow
- [ ] [EVAL] for validations
- [ ] [ERROR] for errors with context

### **Traceability:**
- [ ] All entity IDs logged
- [ ] Can trace operation from logs
- [ ] State changes visible

### **Evaluation:**
- [ ] Input validation present
- [ ] Authorization checked
- [ ] Business rules enforced
- [ ] Success/failure clear

### **Documentation:**
- [ ] Class docstrings complete
- [ ] Method docstrings complete
- [ ] I/O clearly documented
- [ ] Examples provided

---

## 🎯 Quality Metrics

### **Test Coverage**
- **Target:** 80%+
- **Measure:** `pytest --cov=. tests/`

### **Code Complexity**
- **Max file size:** 500 lines
- **Max method size:** 50 lines
- **Max cyclomatic complexity:** 10

### **Documentation**
- **Every class:** Docstring with example
- **Every method:** Full I/O documentation
- **Every module:** Purpose explanation

---

## 🚀 Quick Reference

### **Starting a New Feature**

```bash
# 1. Create test file
touch tests/test_my_feature.py

# 2. Write failing test
# (Edit test file)

# 3. Run test (should FAIL)
pytest tests/test_my_feature.py -v

# 4. Implement feature with O-T-E
# (Edit implementation file)

# 5. Run test (should PASS)
pytest tests/test_my_feature.py -v

# 6. Refactor and verify
pytest tests/test_my_feature.py -v

# 7. Run all tests
pytest tests/ -v

# 8. Commit
git add .
git commit -m "feat: Add my_feature with TDD+O-T-E"
```

---

## 📚 Examples

See these files for reference implementations:
- `tests/test_invite_password_bypass.py` - TDD + O-T-E example
- `datamanager/data_manager.py` - O-T-E logging
- `app/routers/rooms.py` - API documentation

---

**Status:** Living document - update as standards evolve ✨
