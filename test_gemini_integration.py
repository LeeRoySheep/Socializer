"""
Test Gemini API Integration with SearchTool
============================================

Tests that SearchTool works correctly with Google's Gemini API.

This is the critical test that will verify:
1. Tool binding works with Gemini
2. Gemini can call the tool
3. Gemini processes tool results
4. No empty responses

Author: AI Assistant
Date: 2025-10-22
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from tools.gemini.search_tool import SearchTool
from tools.gemini import GeminiResponseHandler


def test_api_keys():
    """Test 1: Check that required API keys are present."""
    print("\n" + "="*70)
    print("TEST 1: API Keys")
    print("="*70)
    
    google_key = os.getenv('GOOGLE_API_KEY')
    tavily_key = os.getenv('TAVILY_API_KEY')
    
    print(f"GOOGLE_API_KEY: {'✅ Found' if google_key else '❌ Missing'}")
    print(f"TAVILY_API_KEY: {'✅ Found' if tavily_key else '❌ Missing'}")
    
    if not google_key:
        print("\n❌ GOOGLE_API_KEY is required for this test")
        print("   Add it to your .env file")
        return False
    
    if not tavily_key:
        print("\n⚠️  TAVILY_API_KEY is missing")
        print("   SearchTool will not work without it")
        return False
    
    print("\n✅ All required API keys present!")
    return True


def test_tool_binding():
    """Test 2: Test that SearchTool binds to Gemini without errors."""
    print("\n" + "="*70)
    print("TEST 2: Tool Binding")
    print("="*70)
    
    try:
        # Create Gemini LLM
        print("📝 Initializing Gemini model...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0
        )
        print("✅ Gemini model initialized")
        
        # Create SearchTool
        print("\n📝 Creating SearchTool...")
        search_tool = SearchTool()
        print("✅ SearchTool created")
        
        # Bind tool to LLM
        print("\n📝 Binding tool to Gemini...")
        llm_with_tools = llm.bind_tools([search_tool])
        print("✅ Tool binding successful!")
        
        # Check binding (simplified - just verify it exists)
        print(f"\n📊 LLM with tools ready: {llm_with_tools is not None}")
        
        return llm_with_tools, search_tool
        
    except Exception as e:
        print(f"\n❌ Tool binding failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_gemini_tool_call():
    """Test 3: Test that Gemini actually calls the tool."""
    print("\n" + "="*70)
    print("TEST 3: Gemini Tool Calling")
    print("="*70)
    
    # Get bound LLM
    llm_with_tools, search_tool = test_tool_binding()
    
    if not llm_with_tools:
        print("❌ Cannot test - tool binding failed")
        return False
    
    try:
        # Test prompt that should trigger search
        test_query = "What is the weather in London today?"
        print(f"\n📝 Test Query: '{test_query}'")
        print("   (This should trigger the search tool)")
        
        # Invoke Gemini
        print("\n🔍 Calling Gemini...")
        message = HumanMessage(content=test_query)
        response = llm_with_tools.invoke([message])
        
        print(f"\n📊 Response Type: {type(response).__name__}")
        print(f"   Content: {response.content[:100] if response.content else '(empty)'}...")
        
        # Check if tool was called
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"\n✅ Tool was called!")
            print(f"   Number of tool calls: {len(response.tool_calls)}")
            
            for i, tool_call in enumerate(response.tool_calls, 1):
                tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                tool_args = tool_call.get('args') if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
                print(f"\n   Tool Call {i}:")
                print(f"   - Name: {tool_name}")
                print(f"   - Args: {tool_args}")
            
            return True
        else:
            print("\n⚠️  Tool was NOT called")
            print("   Gemini responded directly without using the tool")
            print(f"   Response: {response.content}")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """Test 4: Test complete workflow with tool execution."""
    print("\n" + "="*70)
    print("TEST 4: Full Workflow (Call + Execute + Response)")
    print("="*70)
    
    try:
        # Setup
        print("📝 Setting up...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0
        )
        search_tool = SearchTool()
        llm_with_tools = llm.bind_tools([search_tool])
        handler = GeminiResponseHandler()
        
        print("✅ Setup complete")
        
        # First call - should generate tool call
        test_query = "What are the latest AI news?"
        print(f"\n📝 Query: '{test_query}'")
        
        print("\n🔍 Step 1: Initial LLM call...")
        message = HumanMessage(content=test_query)
        response1 = llm_with_tools.invoke([message])
        
        if not hasattr(response1, 'tool_calls') or not response1.tool_calls:
            print("⚠️  Gemini didn't call the tool")
            print(f"   Response: {response1.content}")
            return False
        
        print("✅ Gemini requested tool call")
        
        # Execute tool
        tool_call = response1.tool_calls[0]
        tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', '')
        tool_args = tool_call.get('args') if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
        
        print(f"\n🔧 Step 2: Executing tool '{tool_name}'...")
        print(f"   Args: {tool_args}")
        
        tool_result = search_tool._run(**tool_args)
        print(f"   Status: {tool_result['status']}")
        print(f"   Message: {tool_result['message']}")
        
        if tool_result['status'] != 'success':
            print(f"\n⚠️  Tool execution failed")
            return False
        
        print("✅ Tool executed successfully")
        
        # Create tool message
        from langchain_core.messages import ToolMessage
        tool_message = ToolMessage(
            content=str(tool_result),
            tool_call_id=tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', 'test_id')
        )
        
        # Second call - with tool results
        print(f"\n💬 Step 3: Sending tool results back to Gemini...")
        messages = [message, response1, tool_message]
        response2 = llm_with_tools.invoke(messages)
        
        print(f"\n📊 Final Response:")
        print(f"   Type: {type(response2).__name__}")
        print(f"   Content Length: {len(response2.content) if response2.content else 0} chars")
        
        # Check for empty response
        if handler.is_empty_response(response2):
            print("\n❌ Empty response detected!")
            print("   Gemini returned no content after tool execution")
            
            # Try to generate fallback
            print("\n🔧 Attempting fallback...")
            fallback = handler.create_response_with_fallback(response2, messages)
            print(f"   Fallback: {fallback.content[:200]}...")
            return False
        
        print(f"\n✅ Valid response received!")
        print(f"\nResponse Preview:")
        print(f"{response2.content[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Gemini integration tests."""
    print("\n" + "🧪" * 35)
    print("GEMINI INTEGRATION TEST SUITE")
    print("🧪" * 35)
    
    tests = [
        ("API Keys Check", test_api_keys),
        ("Tool Binding", lambda: test_tool_binding() != (None, None)),
        ("Tool Calling", test_gemini_tool_call),
        ("Full Workflow", test_full_workflow),
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
        print("\n✨ SearchTool works perfectly with Gemini!")
        print("📝 Ready for integration into ai_chatagent.py")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        print("   Please review the errors above")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
