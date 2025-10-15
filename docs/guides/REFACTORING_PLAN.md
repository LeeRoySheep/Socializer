# 🔧 Refactoring Plan - Socializer Project

**Date:** 2025-10-14  
**Status:** Ready to Execute  
**Approach:** Test-Driven Development (TDD)

---

## 📋 Summary of Findings

### **Obsolete Files Identified:**
1. ✅ `chatbot.py` (419 lines) - NOT imported anywhere → **DELETE**
2. ⚠️ `app.py` (514 lines) - Compatibility shim, some tests use it → **KEEP for now, update tests later**

### **Files Needing Refactoring:**
1. 🔴 **CRITICAL:** `ai_chatagent.py` (1,767 lines, 14 classes)
2. 🟡 **HIGH:** `app/main.py` (1,446 lines)
3. 🟢 **MEDIUM:** `datamanager/data_manager.py` (613 lines)

---

## 🎯 Phase 1: Remove Obsolete Code & Verify Tests

**Goal:** Clean up codebase and ensure all tests pass

### **Step 1.1: Verify Current Test Status**
```bash
# Run all tests to establish baseline
pytest tests/ -v

# Run specific test suites
pytest tests/test_connection_leaks.py -v
pytest tests/test_ai_chatagent.py -v
```

**Expected:** All tests should pass before we make changes

---

### **Step 1.2: Delete Obsolete chatbot.py**

**Action:**
```bash
# Verify it's not used (should show no results)
grep -r "from chatbot import\|import chatbot" --include="*.py" .

# Delete the file
rm chatbot.py
```

**Verification:**
- File deleted
- No import errors
- All tests still pass

---

### **Step 1.3: Document app.py Status**

**Action:** Add clear comment to `app.py` explaining its purpose

**Note:** Will be removed later when tests are updated to use `app.main` directly

---

## 🎯 Phase 2: Extract AI Agent Tools (PRIORITY 1)

**Goal:** Separate 14 classes in `ai_chatagent.py` into individual files

### **Directory Structure to Create:**
```
tools/
├── __init__.py                    # Tool registry
├── base_tool.py                   # Base classes if needed
├── conversation_recall_tool.py    # ConversationRecallTool + Input
├── user_preference_tool.py        # UserPreferenceTool
├── skill_evaluator_tool.py        # SkillEvaluator
├── tavily_search_tool.py          # TavilySearchTool
├── life_event_tool.py             # LifeEventTool + Input
└── clarify_communication_tool.py  # ClarifyCommunicationTool + Input

graph/
├── __init__.py
├── state.py                       # State TypedDict
└── tool_node.py                   # BasicToolNode

models/
├── __init__.py
└── user_data.py                   # UserData class

sessions/
├── __init__.py
└── chat_session.py                # ChatSession class

agents/
├── __init__.py
└── ai_chatagent.py                # Main AiChatagent class (refactored)
```

---

### **Step 2.1: Create Base Structure**

**TDD Approach:**
1. Create empty directories and `__init__.py` files
2. Create test files FIRST
3. Implement classes to make tests pass

**Actions:**
```bash
# Create directory structure
mkdir -p tools graph models sessions agents
touch tools/__init__.py graph/__init__.py models/__init__.py sessions/__init__.py agents/__init__.py
```

---

### **Step 2.2: Extract First Tool (TDD Example)**

**Tool to extract:** `ConversationRecallTool`

#### **A. Write Test First**
```python
# tests/tools/test_conversation_recall_tool.py
import pytest
from tools.conversation_recall_tool import ConversationRecallTool, ConversationRecallInput

class TestConversationRecallTool:
    """Test ConversationRecallTool in isolation."""
    
    def test_tool_initialization(self):
        """Test: Tool can be initialized with DataManager."""
        tool = ConversationRecallTool(dm=mock_data_manager)
        assert tool.name == "recall_last_conversation"
        assert tool.dm is not None
    
    def test_tool_invoke_success(self):
        """Test: Tool returns conversation history for valid user."""
        tool = ConversationRecallTool(dm=mock_data_manager)
        result = tool.invoke({"user_id": 1})
        assert "status" in result
        assert result["status"] == "success"
    
    def test_tool_invoke_invalid_user(self):
        """Test: Tool handles invalid user_id gracefully."""
        tool = ConversationRecallTool(dm=mock_data_manager)
        result = tool.invoke({"user_id": 999})
        assert "error" in result or "status" in result
```

#### **B. Extract Code**

1. Copy `ConversationRecallInput` and `ConversationRecallTool` from `ai_chatagent.py`
2. Create `tools/conversation_recall_tool.py`
3. Add proper imports
4. Add comprehensive docstrings

**Template:**
```python
"""
Conversation Recall Tool
Retrieves conversation history from memory for a specific user.
"""

from typing import Optional, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from datamanager.data_manager import DataManager


class ConversationRecallInput(BaseModel):
    """
    Input schema for conversation recall operation.
    
    Attributes:
        user_id (int): The unique identifier for the user
    """
    user_id: int = Field(
        ..., 
        description="The ID of the user whose conversation to retrieve",
        gt=0
    )


class ConversationRecallTool(BaseTool):
    """
    Tool to recall the last conversation from memory.
    
    This tool retrieves conversation history for a specific user,
    formatted as a structured response.
    
    Attributes:
        name (str): Tool identifier - "recall_last_conversation"
        description (str): Human-readable tool description
        args_schema (Type[BaseModel]): Input validation schema
        dm (DataManager): Database manager instance
    
    Example:
        >>> tool = ConversationRecallTool(dm=data_manager)
        >>> result = tool.invoke({"user_id": 1})
        >>> print(result["status"])
        'success'
    """
    
    name: str = "recall_last_conversation"
    description: str = (
        "Use this tool to recall the last conversation from memory. "
        "Use this when the user asks about previous conversations or context. "
        "Input should be a user_id."
    )
    args_schema: type[BaseModel] = ConversationRecallInput
    dm: Optional[DataManager] = None
    
    def _run(self, user_id: int) -> Dict[str, Any]:
        """
        Retrieve conversation history for a user.
        
        Args:
            user_id (int): The unique identifier for the user
            
        Returns:
            Dict[str, Any]: Response containing:
                - status (str): "success" or "error"
                - data (dict): Conversation history
                - message (str): Status message
                
        Raises:
            ValueError: If user_id is invalid
        """
        # Implementation here
        pass
```

#### **C. Run Tests**
```bash
pytest tests/tools/test_conversation_recall_tool.py -v
```

#### **D. Update Original File**

1. Import from new location in `ai_chatagent.py`:
```python
from tools.conversation_recall_tool import ConversationRecallTool
```

2. Remove old class definition

3. Run ALL tests to ensure nothing broke:
```bash
pytest tests/ -v
```

---

### **Step 2.3: Repeat for All Tools**

**Order of extraction (from simplest to most complex):**

1. ✅ `ConversationRecallTool` (example above)
2. ⬜ `UserPreferenceTool`
3. ⬜ `TavilySearchTool`
4. ⬜ `ClarifyCommunicationTool`
5. ⬜ `LifeEventTool`
6. ⬜ `SkillEvaluator` (most complex)

**For each tool:**
- [ ] Write tests first
- [ ] Extract class to new file
- [ ] Add comprehensive docstrings
- [ ] Run tests
- [ ] Update imports in `ai_chatagent.py`
- [ ] Run ALL tests

---

### **Step 2.4: Extract Supporting Classes**

**Order:**
1. `State` → `graph/state.py`
2. `BasicToolNode` → `graph/tool_node.py`
3. `UserData` → `models/user_data.py`
4. `ChatSession` → `sessions/chat_session.py`

**Same TDD process:**
- Write tests first
- Extract
- Document
- Verify

---

### **Step 2.5: Refactor Main Agent Class**

After all extractions, `ai_chatagent.py` should only contain:
- Main `AiChatagent` class
- Graph building logic
- Tool orchestration

**Move to:** `agents/ai_chatagent.py`

**Update all imports throughout codebase**

---

## 🎯 Phase 3: Add Missing Documentation

**Goal:** Every function has clear I/O documentation

### **Step 3.1: Documentation Template**

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """
    Brief one-line description.
    
    Longer description if needed. Explain what the function does,
    when to use it, and any important considerations.
    
    Args:
        param1 (Type1): Description of param1
            - Additional details if needed
            - Valid values or constraints
        param2 (Type2): Description of param2
    
    Returns:
        ReturnType: Description of return value
            - Structure if returning dict/list
            - Possible values
    
    Raises:
        ExceptionType: When and why this exception is raised
    
    Example:
        >>> result = function_name(arg1, arg2)
        >>> print(result)
        expected_output
    
    Notes:
        - Any important implementation details
        - Performance considerations
        - Thread safety notes
    """
    pass
```

### **Step 3.2: Document All Extracted Classes**

**Priority order:**
1. Tool classes (public API)
2. Model classes
3. Graph components
4. Main agent class
5. Helper functions

---

## 🎯 Phase 4: Improve Test Coverage

**Goal:** 80%+ test coverage, following TDD

### **Step 4.1: Test Organization**

```
tests/
├── tools/                      # Tool tests
│   ├── test_conversation_recall_tool.py
│   ├── test_user_preference_tool.py
│   ├── test_skill_evaluator_tool.py
│   └── ...
├── graph/                      # Graph component tests
│   ├── test_state.py
│   └── test_tool_node.py
├── models/                     # Model tests
│   └── test_user_data.py
├── agents/                     # Agent tests
│   └── test_ai_chatagent.py
├── integration/                # Integration tests
│   ├── test_chat_flow.py
│   ├── test_websocket_flow.py
│   └── test_ai_chat_integration.py
└── performance/                # Performance tests
    └── test_concurrent_users.py
```

### **Step 4.2: Test Checklist**

For each class:
- [ ] Unit tests for all public methods
- [ ] Edge case tests
- [ ] Error handling tests
- [ ] Mock external dependencies
- [ ] Integration tests for workflows

---

## 🎯 Phase 5: Refactor API Routes (Optional)

**Goal:** Split large `app/main.py` into smaller modules

### **Structure:**
```
app/
├── routers/
│   ├── __init__.py
│   ├── auth_router.py         # Authentication endpoints
│   ├── chat_router.py         # Chat endpoints
│   ├── user_router.py         # User management
│   └── ai_router.py           # AI endpoints
├── services/
│   ├── __init__.py
│   ├── auth_service.py        # Business logic
│   ├── chat_service.py
│   └── user_service.py
└── main.py                     # App initialization only
```

**Note:** This is Phase 5 (lower priority) - focus on AI agent refactoring first

---

## ✅ Testing Checklist

### **After Each Change:**
- [ ] Run specific test file
- [ ] Run all tests: `pytest tests/ -v`
- [ ] Check test coverage: `pytest --cov=. tests/`
- [ ] Fix any failures before proceeding

### **After Each Phase:**
- [ ] Run full test suite
- [ ] Manual testing: Start server and test key features
- [ ] Check for any import errors
- [ ] Verify API documentation at `/docs`

---

## 📊 Success Metrics

### **Code Quality:**
- ✅ ai_chatagent.py < 500 lines (currently 1,767)
- ✅ All classes in separate files
- ✅ All functions documented with I/O
- ✅ No obsolete code

### **Testing:**
- ✅ Test coverage > 80%
- ✅ All tests passing
- ✅ Tests run in < 30 seconds

### **Maintainability:**
- ✅ Easy to find classes
- ✅ Easy to add new tools
- ✅ Clear imports
- ✅ Consistent structure

---

## 🚀 Execution Order

### **Week 1: Cleanup & First Tool**
- Day 1: Delete obsolete code, verify tests
- Day 2-3: Extract first tool (ConversationRecallTool) using TDD
- Day 4-5: Extract 2 more tools

### **Week 2: Complete Tool Extraction**
- Day 1-3: Extract remaining tools
- Day 4-5: Extract supporting classes (State, ToolNode, etc.)

### **Week 3: Documentation & Testing**
- Day 1-2: Add comprehensive documentation
- Day 3-5: Improve test coverage

### **Week 4: Main Agent Refactoring**
- Day 1-3: Refactor main AiChatagent class
- Day 4-5: Final testing and optimization

---

## 📝 User Actions Required

**For each step, you will:**
1. Review the proposed changes
2. Run the tests: `pytest tests/ -v`
3. Start the server: `uvicorn app.main:app --reload`
4. Test key features manually
5. Confirm before proceeding to next step

**I will:**
1. Create all code changes
2. Write tests following TDD
3. Document all changes
4. Ensure no breaking changes
5. Wait for your confirmation before proceeding

---

## 🎯 Ready to Start?

**Proposed First Step:**
1. Delete `chatbot.py` (obsolete file)
2. Run tests to verify nothing breaks
3. Commit the change

**Shall I proceed with Step 1?**
