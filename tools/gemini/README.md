# Gemini Tool Integration Framework

## 📖 Overview

This package provides OOP classes for creating Google Gemini-compatible tools with LangChain.

**Problem Solved:** Gemini has stricter requirements than OpenAI for tool schemas. This framework ensures all tools work properly with Gemini's API.

## 🏗️ Architecture

```
tools/gemini/
├── __init__.py              # Package exports
├── base.py                  # GeminiToolBase - base class for all tools
├── validator.py             # GeminiSchemaValidator - validates schemas
├── response_handler.py      # GeminiResponseHandler - handles responses
└── README.md               # This file
```

## 🎯 Key Components

### 1. GeminiToolBase

Base class for all Gemini-compatible tools.

**Features:**
- Automatic schema validation
- Type safety
- Clear error messages
- Consistent interface

**Usage:**
```python
from tools.gemini import GeminiToolBase
from pydantic import BaseModel, Field
from typing import Optional

class MyToolInput(BaseModel):
    """Input schema for MyTool."""
    query: str = Field(description="The search query")
    limit: Optional[int] = Field(default=10, description="Max results")

class MyTool(GeminiToolBase):
    name: str = "my_tool"
    description: str = "My tool does X, Y, and Z"
    args_schema: Type[BaseModel] = MyToolInput
    
    def _run(self, query: str, limit: int = 10) -> Dict[str, Any]:
        # Implementation
        return {
            "status": "success",
            "message": "Operation completed",
            "data": {...}
        }
```

### 2. GeminiSchemaValidator

Validates Pydantic schemas for Gemini compatibility.

**Checks:**
- All fields have descriptions ✅
- No unsupported Union types ✅
- Lists have item types defined ✅
- Optional fields have defaults ✅
- No complex nested structures ✅

**Usage:**
```python
from tools.gemini import GeminiSchemaValidator

validator = GeminiSchemaValidator()
is_valid, errors, warnings = validator.validate(MyToolInput)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

### 3. GeminiResponseHandler

Handles tool responses and prevents empty responses.

**Features:**
- Detects empty responses
- Formats tool results
- Generates fallbacks
- Extracts tool results from message history

**Usage:**
```python
from tools.gemini import GeminiResponseHandler

handler = GeminiResponseHandler()

# Check if response is empty
if handler.is_empty_response(ai_message):
    # Generate fallback from tool results
    fallback = handler.generate_fallback(tool_result, tool_name)
```

## ✅ Gemini Requirements

### Schema Requirements

| Requirement | ❌ Wrong | ✅ Correct |
|-------------|----------|-----------|
| **Field descriptions** | `query: str` | `query: str = Field(description="...")` |
| **Optional defaults** | `limit: Optional[int]` | `limit: Optional[int] = Field(default=10)` |
| **List types** | `tags: List` | `tags: List[str]` |
| **Union types** | `Union[str, int]` | Use separate fields |
| **Dict types** | `metadata: dict` | `metadata: Dict[str, Any]` |

### Supported Types

✅ **Fully Supported:**
- `str`
- `int`
- `float`
- `bool`
- `Optional[T]` (where T is supported)
- `List[T]` (where T is simple type)
- `Dict[str, Any]`

⚠️ **Use with Caution:**
- Nested Pydantic models
- `List[Dict]`
- Complex nested structures

❌ **Not Supported:**
- `Union[A, B]` (except Optional)
- Recursive schemas
- `Any` without context

## 🧪 Testing

### Step 1: Validate Schema

```python
from tools.gemini import GeminiSchemaValidator

validator = GeminiSchemaValidator()
validator.print_report(MyToolInput)
```

### Step 2: Test Tool Independently

```python
tool = MyTool()

# Test the run method
result = tool._run(query="test")
print(result)

# Check schema info
print(tool.get_schema_info())
```

### Step 3: Test with Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")
llm_with_tools = llm.bind_tools([tool])

# Test
response = llm_with_tools.invoke("test query")
```

## 📚 Examples

### Example 1: Simple Search Tool

```python
from tools.gemini import GeminiToolBase
from pydantic import BaseModel, Field
from typing import Optional

class SearchInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: Optional[int] = Field(default=10, description="Max results")

class SearchTool(GeminiToolBase):
    name: str = "web_search"
    description: str = "Search the web for information"
    args_schema = SearchInput
    
    def _run(self, query: str, max_results: int = 10):
        # Implement search
        return {"status": "success", "data": [...]}
```

### Example 2: User Preference Tool

```python
class PreferenceInput(BaseModel):
    user_id: int = Field(description="User ID")
    action: str = Field(description="Action: get, set, or delete")
    key: Optional[str] = Field(default=None, description="Preference key")
    value: Optional[str] = Field(default=None, description="Preference value")

class PreferenceTool(GeminiToolBase):
    name: str = "user_preference"
    description: str = "Manage user preferences"
    args_schema = PreferenceInput
    
    def _run(self, user_id: int, action: str, key: str = None, value: str = None):
        # Implement preferences
        return {"status": "success", "message": "Preference updated"}
```

## 🔍 Debugging

### Common Issues

**Issue 1: Empty Responses**
```python
# Use response handler
from tools.gemini import GeminiResponseHandler

handler = GeminiResponseHandler()
response = handler.create_response_with_fallback(ai_response, messages)
```

**Issue 2: Schema Validation Errors**
```python
# Check schema before using
validator = GeminiSchemaValidator()
is_valid, errors, warnings = validator.validate(MyToolInput)

if not is_valid:
    print("Schema errors:", errors)
```

**Issue 3: Tool Not Called**
```python
# Check tool binding
print(f"Tools bound: {len(llm_with_tools.bound.kwargs.get('tools', []))}")

# Check tool schema
tool = MyTool()
print(tool.get_schema_info())
```

## 📝 Best Practices

1. **Always validate schemas** before deploying
2. **Keep schemas simple** - avoid nested complexity
3. **Provide clear descriptions** for all fields
4. **Use default values** for optional fields
5. **Test independently** before integration
6. **Handle empty responses** with fallbacks
7. **Document your tools** thoroughly

## 🚀 Migration Guide

### Migrating Existing Tools

**Before:**
```python
class OldTool(BaseTool):
    name = "old_tool"
    description = "Does something"
    
    def _run(self, query):
        return query
```

**After:**
```python
class OldToolInput(BaseModel):
    query: str = Field(description="The query string")

class NewTool(GeminiToolBase):
    name: str = "old_tool"
    description: str = "Does something"
    args_schema = OldToolInput
    
    def _run(self, query: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "data": query
        }
```

## 📊 Version History

- **v1.0.0** (2025-10-22): Initial release
  - GeminiToolBase
  - GeminiSchemaValidator
  - GeminiResponseHandler
  - Complete documentation

## 🤝 Contributing

When adding new features:
1. Update this README
2. Add unit tests
3. Validate with Gemini API
4. Document any gotchas

## 📄 License

Part of the Socializer project.
