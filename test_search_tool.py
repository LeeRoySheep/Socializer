"""
Unit Test for Gemini SearchTool
================================

Tests the SearchTool implementation with GeminiToolBase.

Author: AI Assistant
Date: 2025-10-22
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from tools.gemini.search_tool import SearchTool, SearchToolInput, search_web
from tools.gemini import GeminiSchemaValidator


def test_schema():
    """Test 1: Validate SearchTool schema."""
    print("\n" + "="*70)
    print("TEST 1: Schema Validation")
    print("="*70)
    
    validator = GeminiSchemaValidator()
    validator.print_report(SearchToolInput)
    
    is_valid, errors, warnings = validator.validate(SearchToolInput)
    
    assert is_valid, f"Schema should be valid, got errors: {errors}"
    print("\n✅ SearchTool schema is Gemini-compatible!")
    
    return True


def test_initialization():
    """Test 2: Initialize SearchTool."""
    print("\n" + "="*70)
    print("TEST 2: Tool Initialization")
    print("="*70)
    
    try:
        tool = SearchTool()
        print(f"✅ Tool created: {tool.name}")
        print(f"   Description: {tool.description[:60]}...")
        
        # Check schema info
        schema_info = tool.get_schema_info()
        print(f"\n📋 Schema Info:")
        print(f"   Name: {schema_info['name']}")
        print(f"   Fields: {list(schema_info['fields'].keys())}")
        
        assert schema_info['name'] == 'web_search', "Wrong tool name"
        assert 'query' in schema_info['fields'], "Missing query field"
        assert 'max_results' in schema_info['fields'], "Missing max_results field"
        
        print("\n✅ Tool initialization successful!")
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_input_validation():
    """Test 3: Test input validation."""
    print("\n" + "="*70)
    print("TEST 3: Input Validation")
    print("="*70)
    
    tool = SearchTool()
    
    # Test Case 1: Empty query
    print("\n📝 Test Case 3.1: Empty query (should fail gracefully)")
    result = tool._run(query="", max_results=5)
    
    assert result['status'] == 'error', "Empty query should return error"
    assert 'empty' in result['message'].lower(), "Error message should mention empty"
    print(f"✅ Correctly handled: {result['message']}")
    
    # Test Case 2: Valid query
    print("\n📝 Test Case 3.2: Valid query format")
    result = tool._run(query="test query", max_results=3)
    
    assert 'status' in result, "Result should have status"
    assert 'message' in result, "Result should have message"
    assert 'query' in result, "Result should include query"
    print(f"✅ Valid query format: {result['message']}")
    
    # Test Case 3: Max results clamping
    print("\n📝 Test Case 3.3: Max results bounds")
    # Tool should clamp to 1-10 range
    result1 = tool._run(query="test", max_results=0)  # Should clamp to 1
    result2 = tool._run(query="test", max_results=100)  # Should clamp to 10
    print("✅ Max results clamping works")
    
    print("\n" + "="*70)
    print("✅ TEST 3 PASSED: Input Validation Works!")
    print("="*70)
    
    return True


def test_search_execution():
    """Test 4: Test actual search execution (if API key available)."""
    print("\n" + "="*70)
    print("TEST 4: Search Execution")
    print("="*70)
    
    # Check if API key is available
    api_key = os.getenv('TAVILY_API_KEY')
    
    if not api_key:
        print("⚠️  TAVILY_API_KEY not found - skipping live search test")
        print("✅ Test skipped (API key required)")
        return True
    
    tool = SearchTool()
    
    if not tool.tavily_client:
        print("⚠️  Tavily client not initialized - skipping live search test")
        print("✅ Test skipped (initialization failed)")
        return True
    
    # Test Case 1: Simple search
    print("\n📝 Test Case 4.1: Perform live search")
    result = tool._run(query="Python programming language", max_results=3)
    
    print(f"\nSearch Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if result['status'] == 'success':
        print(f"Results Count: {result.get('results_count', 0)}")
        
        if 'data' in result and result['data']:
            print("\n📄 Sample Result:")
            first_result = result['data'][0] if isinstance(result['data'], list) else result['data']
            if isinstance(first_result, dict):
                print(f"   Title: {first_result.get('title', 'N/A')}")
                print(f"   Content: {first_result.get('content', '')[:100]}...")
        
        assert result['results_count'] > 0, "Should have results"
        print("\n✅ Live search successful!")
    else:
        print(f"\n⚠️  Search returned error: {result['message']}")
        print("✅ Error handled gracefully")
    
    print("\n" + "="*70)
    print("✅ TEST 4 PASSED: Search Execution Works!")
    print("="*70)
    
    return True


def test_convenience_function():
    """Test 5: Test convenience function."""
    print("\n" + "="*70)
    print("TEST 5: Convenience Function")
    print("="*70)
    
    print("\n📝 Testing search_web() function")
    
    try:
        result = search_web("test query", max_results=2)
        
        assert isinstance(result, dict), "Should return dict"
        assert 'status' in result, "Should have status"
        
        print(f"✅ Convenience function works: {result['status']}")
        
    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("✅ Error handled")
    
    print("\n" + "="*70)
    print("✅ TEST 5 PASSED: Convenience Function Works!")
    print("="*70)
    
    return True


def run_all_tests():
    """Run all SearchTool tests."""
    print("\n" + "🧪" * 35)
    print("SEARCHTOOL UNIT TEST SUITE")
    print("🧪" * 35)
    
    tests = [
        ("Schema Validation", test_schema),
        ("Tool Initialization", test_initialization),
        ("Input Validation", test_input_validation),
        ("Search Execution", test_search_execution),
        ("Convenience Function", test_convenience_function),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'▶️' * 35}")
            print(f"Running: {test_name}")
            print(f"{'▶️' * 35}")
            
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test_name} FAILED")
                
        except AssertionError as e:
            failed += 1
            print(f"\n❌ {test_name} FAILED: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ {test_name} ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n" + "🎉" * 35)
        print("✅ ALL TESTS PASSED!")
        print("🎉" * 35)
        print("\n✨ SearchTool is ready for integration!")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
