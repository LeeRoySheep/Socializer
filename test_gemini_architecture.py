"""
Test Script for Gemini Tool Architecture
=========================================

This script tests the base architecture before implementing actual tools.

Tests:
1. GeminiSchemaValidator - validates schemas correctly
2. GeminiToolBase - base class works
3. GeminiResponseHandler - handles responses

Author: AI Assistant
Date: 2025-10-22
"""

import sys
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# Import our new architecture
from tools.gemini import GeminiToolBase, GeminiSchemaValidator, GeminiResponseHandler


# ============================================================================
# TEST 1: Schema Validation
# ============================================================================

def test_schema_validation():
    """Test the GeminiSchemaValidator."""
    print("\n" + "="*70)
    print("TEST 1: Schema Validation")
    print("="*70)
    
    # Test Case 1: Valid Schema
    print("\n📝 Test Case 1.1: Valid Schema")
    class ValidSchema(BaseModel):
        query: str = Field(description="Search query")
        limit: Optional[int] = Field(default=10, description="Max results")
    
    validator = GeminiSchemaValidator()
    is_valid, errors, warnings = validator.validate(ValidSchema)
    
    assert is_valid, "Valid schema should pass"
    assert len(errors) == 0, "Should have no errors"
    print("✅ Valid schema passed!")
    
    # Test Case 2: Missing Description
    print("\n📝 Test Case 1.2: Missing Description (should fail)")
    class InvalidSchema(BaseModel):
        query: str  # No description
    
    is_valid, errors, warnings = validator.validate(InvalidSchema)
    
    assert not is_valid, "Invalid schema should fail"
    assert len(errors) > 0, "Should have errors"
    assert "description" in errors[0].lower(), "Error should mention description"
    print(f"✅ Correctly caught error: {errors[0]}")
    
    # Test Case 3: Optional Without Default (warning)
    print("\n📝 Test Case 1.3: Optional Without Default (should warn)")
    class WarningSchema(BaseModel):
        query: str = Field(description="Query")
        limit: Optional[int] = Field(description="Limit")  # No default
    
    is_valid, errors, warnings = validator.validate(WarningSchema)
    
    assert is_valid, "Should be valid but with warnings"
    assert len(warnings) > 0, "Should have warnings"
    print(f"✅ Correctly generated warning: {warnings[0]}")
    
    print("\n" + "="*70)
    print("✅ TEST 1 PASSED: Schema Validation Works!")
    print("="*70)


# ============================================================================
# TEST 2: GeminiToolBase
# ============================================================================

def test_tool_base():
    """Test the GeminiToolBase class."""
    print("\n" + "="*70)
    print("TEST 2: GeminiToolBase")
    print("="*70)
    
    # Test Case 1: Create a Simple Tool
    print("\n📝 Test Case 2.1: Create Simple Tool")
    
    class SimpleToolInput(BaseModel):
        message: str = Field(description="A message to echo")
    
    class SimpleTool(GeminiToolBase):
        name: str = "simple_tool"
        description: str = "Echoes a message"
        args_schema = SimpleToolInput
        
        def _run(self, message: str) -> Dict[str, Any]:
            return {
                "status": "success",
                "message": f"Echo: {message}",
                "data": {"original": message}
            }
    
    tool = SimpleTool()
    
    # Test execution
    result = tool._run(message="Hello Gemini!")
    
    assert result["status"] == "success", "Tool should execute successfully"
    assert "Hello Gemini!" in result["message"], "Should echo the message"
    print(f"✅ Tool executed: {result['message']}")
    
    # Test schema info
    print("\n📝 Test Case 2.2: Get Schema Info")
    schema_info = tool.get_schema_info()
    
    assert schema_info["name"] == "simple_tool", "Should have correct name"
    assert "message" in schema_info["fields"], "Should have message field"
    print(f"✅ Schema info: {schema_info}")
    
    # Test Case 3: Tool with Invalid Schema (should fail on init)
    print("\n📝 Test Case 2.3: Tool with Invalid Schema (should fail)")
    
    class InvalidToolInput(BaseModel):
        message: str  # No description
    
    class InvalidTool(GeminiToolBase):
        name: str = "invalid_tool"
        description: str = "This should fail"
        args_schema = InvalidToolInput
        
        def _run(self, message: str):
            return {"status": "success"}
    
    try:
        invalid_tool = InvalidTool()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✅ Correctly caught error: {e}")
    
    print("\n" + "="*70)
    print("✅ TEST 2 PASSED: GeminiToolBase Works!")
    print("="*70)


# ============================================================================
# TEST 3: Response Handler
# ============================================================================

def test_response_handler():
    """Test the GeminiResponseHandler."""
    print("\n" + "="*70)
    print("TEST 3: GeminiResponseHandler")
    print("="*70)
    
    handler = GeminiResponseHandler()
    
    # Test Case 1: Detect Empty Response
    print("\n📝 Test Case 3.1: Detect Empty Response")
    
    from langchain_core.messages import AIMessage
    
    empty_message = AIMessage(content="")
    assert handler.is_empty_response(empty_message), "Should detect empty"
    print("✅ Empty response detected")
    
    empty_message2 = AIMessage(content="```")
    assert handler.is_empty_response(empty_message2), "Should detect code block only"
    print("✅ Code block only detected as empty")
    
    valid_message = AIMessage(content="Hello!")
    assert not handler.is_empty_response(valid_message), "Should not detect valid message"
    print("✅ Valid message not flagged as empty")
    
    # Test Case 2: Format Tool Result
    print("\n📝 Test Case 3.2: Format Tool Result")
    
    tool_result = {
        "status": "success",
        "data": {"temperature": "20°C", "condition": "Sunny"}
    }
    
    formatted = handler.format_tool_result(tool_result, "weather_tool")
    
    assert "weather_tool" in formatted, "Should include tool name"
    assert "temperature" in formatted or "20°C" in formatted, "Should include data"
    print(f"✅ Formatted result: {formatted[:100]}")
    
    # Test Case 3: Generate Fallback
    print("\n📝 Test Case 3.3: Generate Fallback")
    
    fallback = handler.generate_fallback(tool_result, "weather_tool")
    
    assert fallback.content, "Fallback should have content"
    assert "weather_tool" in fallback.content, "Should mention tool"
    print(f"✅ Fallback generated: {fallback.content[:100]}")
    
    print("\n" + "="*70)
    print("✅ TEST 3 PASSED: GeminiResponseHandler Works!")
    print("="*70)


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def run_all_tests():
    """Run all architecture tests."""
    print("\n" + "🧪" * 35)
    print("GEMINI ARCHITECTURE TEST SUITE")
    print("🧪" * 35)
    
    try:
        test_schema_validation()
        test_tool_base()
        test_response_handler()
        
        print("\n" + "🎉" * 35)
        print("✅ ALL TESTS PASSED!")
        print("🎉" * 35)
        print("\n✨ Gemini architecture is working correctly!")
        print("📝 Next step: Implement actual tools using this architecture")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
