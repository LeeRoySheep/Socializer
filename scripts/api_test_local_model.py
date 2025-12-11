#!/usr/bin/env python3
"""
API Test Script for Local Model Integration

Tests the AI chat endpoint with a local LLM (LM Studio/Ollama) 
to verify proper JSON parsing and response formatting.

Usage:
    python scripts/api_test_local_model.py
    
    # With custom server
    python scripts/api_test_local_model.py --host localhost --port 8000
    
    # With auth token
    python scripts/api_test_local_model.py --token YOUR_TOKEN
"""

import argparse
import requests
import json
import sys
from typing import Optional


def register_user(base_url: str, username: str, password: str, email: str = None) -> bool:
    """Register a new user via API."""
    if not email:
        email = f"{username.lower()}@test.com"
    
    try:
        # Try JSON API first
        response = requests.post(
            f"{base_url}/api/auth/register",
            json={"username": username, "password": password, "email": email},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   Registration response: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Registered user: {username}")
            return True
        elif response.status_code == 400 and "already" in response.text.lower():
            print(f"   ℹ️  User {username} already exists")
            return True
        elif response.status_code == 404:
            # Try without /api prefix
            response = requests.post(
                f"{base_url}/auth/register",
                json={"username": username, "password": password, "email": email},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                print(f"   ✅ Registered user: {username}")
                return True
            print(f"   ⚠️  Registration endpoint not found")
        else:
            print(f"   ⚠️  Registration failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️  Registration error: {e}")
    return False


def get_auth_token(base_url: str, username: str = "testuser", password: str = "testpass") -> Optional[str]:
    """Get auth token by logging in via /api/auth/login endpoint."""
    try:
        url = f"{base_url}/api/auth/login"
        payload = {"username": username, "password": password}
        
        # Try JSON login endpoint first (main.py defines this)
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json().get("access_token")
        
        # If 404, try OAuth2 token endpoint
        if response.status_code == 404:
            url2 = f"{base_url}/auth/token"
            response = requests.post(
                url2,
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if response.status_code == 200:
                return response.json().get("access_token")
        
        print(f"   Auth response for {username}: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"⚠️  Auth failed for {username}: {e}")
    return None


def test_chat(base_url: str, token: str, message: str, model: str = "lm-studio") -> dict:
    """Send a chat message and get response."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "message": message,
        "model": model,
        "conversation_id": "test_local_model"
    }
    
    print(f"\n📤 Sending: {message}")
    print(f"   Model: {model}")
    
    response = requests.post(
        f"{base_url}/api/ai/chat",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Response:")
        print(f"   {data.get('response', 'No response')[:500]}")
        
        # Check for raw JSON in response
        resp_text = data.get('response', '')
        if resp_text.startswith('[{') or resp_text.startswith('{"'):
            print("\n⚠️  WARNING: Response appears to be raw JSON!")
            return {"status": "error", "reason": "raw_json", "data": data}
        
        # Check for tool usage
        tools = data.get('tools_used', [])
        if tools:
            print(f"\n🔧 Tools used: {tools}")
        
        return {"status": "ok", "data": data}
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")
        return {"status": "error", "code": response.status_code}


def run_test_suite(base_url: str, token: str, model: str):
    """Run a suite of tests."""
    print("=" * 60)
    print("🧪 LOCAL MODEL INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        # Test 1: Simple greeting (no tools needed)
        {
            "name": "Simple Greeting",
            "message": "Hallo!",
            "expect_tools": False
        },
        # Test 2: Weather query (should use web_search)
        {
            "name": "Weather Query",
            "message": "Wie ist das Wetter in Berlin?",
            "expect_tools": True,
            "expect_tool": "web_search"
        },
        # Test 3: Memory recall (should use recall_last_conversation)
        {
            "name": "Memory Recall",
            "message": "Weißt du noch wer ich bin?",
            "expect_tools": True,
            "expect_tool": "recall_last_conversation"
        },
        # Test 4: Clarification (should use clarify_communication)
        {
            "name": "Clarification",
            "message": "Was bedeutet 'Empathie' genau?",
            "expect_tools": False  # Model might answer directly
        }
    ]
    
    results = []
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*60}")
        
        result = test_chat(base_url, token, test['message'], model)
        
        # Evaluate result - check for meaningful response
        passed = result['status'] == 'ok'
        
        if passed:
            response_text = result.get('data', {}).get('response', '')
            
            # Check for error messages (these are failures)
            error_indicators = [
                'error', 'fehler', 'encountered an error', 
                'couldn\'t process', 'try again', 'erneut versuchen'
            ]
            has_error = any(ind in response_text.lower() for ind in error_indicators)
            
            # Check for raw JSON (this is a failure)
            is_raw_json = response_text.strip().startswith('[{') or response_text.strip().startswith('{"')
            
            # Check for meaningful content (more than 20 chars, not an error)
            has_content = len(response_text) > 20 and not has_error and not is_raw_json
            
            passed = has_content
            
            if has_error:
                print(f"   ⚠️  Response contains error message")
            if is_raw_json:
                print(f"   ⚠️  Response is raw JSON (not formatted)")
        
        results.append({
            "test": test['name'],
            "passed": passed,
            "result": result
        })
        
        print(f"\n{'✅ PASSED' if passed else '❌ FAILED'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed_count = sum(1 for r in results if r['passed'])
    print(f"Passed: {passed_count}/{len(results)}")
    
    for r in results:
        status = "✅" if r['passed'] else "❌"
        print(f"  {status} {r['test']}")
    
    return results


def test_language_detection(base_url: str, model: str):
    """Test language detection with English and German users."""
    print("\n" + "=" * 60)
    print("🌐 LANGUAGE DETECTION TEST")
    print("=" * 60)
    
    # Test users
    users = [
        {"username": "human2", "password": "FuckShit123.", "expected_lang": "German", "test_msg": "Hallo, wie geht es dir?"},
        {"username": "English", "password": "FuckShit123.", "expected_lang": "English", "test_msg": "Hello, how are you?"},
    ]
    
    # Step 1: Register English user if not exists
    print("\n📝 Ensuring test users exist...")
    register_user(base_url, "English", "FuckShit123.", "english@test.com")
    
    # Step 2: Get ALL tokens upfront before running any tests
    print("\n🔑 Authenticating all users...")
    tokens = {}
    for user in users:
        print(f"   Authenticating {user['username']}...")
        token = get_auth_token(base_url, user['username'], user['password'])
        if token:
            tokens[user['username']] = token
            print(f"   ✅ {user['username']} authenticated")
        else:
            print(f"   ❌ {user['username']} auth failed")
    
    # Step 3: Run tests with pre-fetched tokens
    results = []
    for user in users:
        print(f"\n{'='*40}")
        print(f"Testing: {user['username']} (expected: {user['expected_lang']})")
        print(f"{'='*40}")
        
        token = tokens.get(user['username'])
        if not token:
            print(f"   ⚠️  Could not authenticate {user['username']}")
            results.append({"user": user['username'], "passed": False, "reason": "auth_failed"})
            continue
        
        result = test_chat(base_url, token, user['test_msg'], model)
        
        if result['status'] == 'ok':
            response = result.get('data', {}).get('response', '')
            
            # Check if response is in expected language
            if user['expected_lang'] == 'German':
                # German indicators
                german_words = ['ich', 'dir', 'du', 'wie', 'und', 'ist', 'ein', 'das']
                is_german = any(word in response.lower() for word in german_words)
                passed = is_german
            else:
                # English indicators
                english_words = ['i', 'you', 'how', 'are', 'the', 'is', 'can', 'help']
                is_english = any(word in response.lower().split() for word in english_words)
                passed = is_english
            
            print(f"   Language check: {'✅ Correct' if passed else '❌ Wrong'}")
            results.append({"user": user['username'], "passed": passed, "response": response[:100]})
        else:
            results.append({"user": user['username'], "passed": False, "reason": "request_failed"})
    
    # Summary
    print(f"\n{'='*60}")
    print("LANGUAGE DETECTION SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "✅" if r['passed'] else "❌"
        print(f"  {status} {r['user']}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test Local Model Integration")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", default=8000, type=int, help="Server port")
    parser.add_argument("--token", help="Auth token (optional)")
    parser.add_argument("--username", default="testuser", help="Username for auth")
    parser.add_argument("--password", default="testpass", help="Password for auth")
    parser.add_argument("--model", default="lm-studio", help="Model to test")
    parser.add_argument("--message", help="Single message to test (skip test suite)")
    parser.add_argument("--lang-test", action="store_true", help="Run language detection test")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    print(f"🔗 Server: {base_url}")
    
    # Language detection test (doesn't need auth)
    if args.lang_test:
        test_language_detection(base_url, args.model)
        return
    
    # Get token
    token = args.token
    if not token:
        print(f"🔑 Authenticating as {args.username}...")
        token = get_auth_token(base_url, args.username, args.password)
        if not token:
            print("❌ Could not authenticate. Use --token to provide a token.")
            sys.exit(1)
        print("✅ Authenticated")
    
    # Run tests
    if args.message:
        # Single message test
        test_chat(base_url, token, args.message, args.model)
    else:
        # Full test suite
        run_test_suite(base_url, token, args.model)


if __name__ == "__main__":
    main()
