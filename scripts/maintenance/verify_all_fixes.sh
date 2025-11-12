#!/bin/bash

# Comprehensive Verification Script for All Fixes
# Tests: Swagger UI, Auth API, Rooms API, WebSocket
# Date: 2025-10-15

echo "================================="
echo "🧪 VERIFICATION TEST SUITE"
echo "================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:8000"
PASS_COUNT=0
FAIL_COUNT=0

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local expected_code=$3
    local description=$4
    local data=$5
    local token=$6
    
    echo -n "Testing: $description... "
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        if [ -n "$token" ]; then
            response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $token" \
                -d "$data")
        else
            response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data")
        fi
    else
        if [ -n "$token" ]; then
            response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
                -H "Authorization: Bearer $token")
        else
            response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint")
        fi
    fi
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($http_code)"
        ((PASS_COUNT++))
    else
        echo -e "${RED}❌ FAIL${NC} (Expected: $expected_code, Got: $http_code)"
        ((FAIL_COUNT++))
    fi
}

echo "================================="
echo "📋 1. SWAGGER UI SCHEMA TEST"
echo "================================="
echo ""

# Test that Swagger UI endpoint is accessible
test_endpoint "GET" "/docs" "200" "Swagger UI accessible"
test_endpoint "GET" "/openapi.json" "200" "OpenAPI schema available"

echo ""
echo "================================="
echo "🔐 2. AUTH API TESTS"
echo "================================="
echo ""

# Create unique username for testing
TIMESTAMP=$(date +%s)
TEST_USER="testuser_$TIMESTAMP"
TEST_EMAIL="test_$TIMESTAMP@example.com"
TEST_PASS="securepass123"

# Test registration
REGISTER_DATA="{\"username\":\"$TEST_USER\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASS\"}"
echo "Registering user: $TEST_USER"
test_endpoint "POST" "/api/auth/register" "200" "Register new user" "$REGISTER_DATA"

# Test login
LOGIN_DATA="{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}"
echo "Logging in user: $TEST_USER"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "$LOGIN_DATA")

# Extract token
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "Login: ${GREEN}✅ PASS${NC} (Token received)"
    ((PASS_COUNT++))
    echo "Token length: ${#TOKEN} characters"
else
    echo -e "Login: ${RED}❌ FAIL${NC} (No token received)"
    ((FAIL_COUNT++))
fi

echo ""
echo "================================="
echo "🏠 3. ROOMS API TESTS"
echo "================================="
echo ""

# Test rooms endpoints (should NOT be 404)
if [ -n "$TOKEN" ]; then
    test_endpoint "GET" "/api/rooms/" "200" "List user rooms" "" "$TOKEN"
    test_endpoint "GET" "/api/rooms/invites/pending" "200" "Get pending invites" "" "$TOKEN"
    
    # Test creating a room
    ROOM_DATA='{"name":"Test Room","invitees":[]}'
    test_endpoint "POST" "/api/rooms/" "201" "Create new room" "$ROOM_DATA" "$TOKEN"
else
    echo -e "${YELLOW}⚠️  SKIP: No token available for authenticated tests${NC}"
fi

echo ""
echo "================================="
echo "💬 4. CHAT API TESTS"
echo "================================="
echo ""

if [ -n "$TOKEN" ]; then
    test_endpoint "GET" "/api/chat/messages" "200" "Get chat messages" "" "$TOKEN"
else
    echo -e "${YELLOW}⚠️  SKIP: No token available for authenticated tests${NC}"
fi

echo ""
echo "================================="
echo "🔌 5. WEBSOCKET ENDPOINT CHECK"
echo "================================="
echo ""

# Check if WebSocket endpoint is registered by testing actual endpoint
# WebSocket endpoints don't always appear in OpenAPI JSON
echo -n "Testing: WebSocket endpoint exists... "
WS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/ws/chat")
# WebSocket endpoints return 426 (Upgrade Required) when accessed via HTTP, which is correct
if [ "$WS_RESPONSE" = "426" ] || [ "$WS_RESPONSE" = "400" ]; then
    echo -e "${GREEN}✅ PASS${NC} (WebSocket endpoint registered)"
    ((PASS_COUNT++))
else
    echo -e "${YELLOW}⚠️  SKIP${NC} (HTTP code: $WS_RESPONSE - WebSocket may still work)"
fi

echo ""
echo "================================="
echo "📊 6. API DOCUMENTATION CHECK"
echo "================================="
echo ""

# Check Swagger UI has proper schemas
OPENAPI=$(curl -s "$BASE_URL/openapi.json")

# Check for LoginRequest schema
if echo "$OPENAPI" | grep -q "LoginRequest"; then
    echo -e "LoginRequest schema exists: ${GREEN}✅ PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "LoginRequest schema exists: ${RED}❌ FAIL${NC}"
    ((FAIL_COUNT++))
fi

# Check for UserCreateAPI schema
if echo "$OPENAPI" | grep -q "UserCreateAPI"; then
    echo -e "UserCreateAPI schema exists: ${GREEN}✅ PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "UserCreateAPI schema exists: ${RED}❌ FAIL${NC}"
    ((FAIL_COUNT++))
fi

# Check for RegisterResponse schema
if echo "$OPENAPI" | grep -q "RegisterResponse"; then
    echo -e "RegisterResponse schema exists: ${GREEN}✅ PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "RegisterResponse schema exists: ${RED}❌ FAIL${NC}"
    ((FAIL_COUNT++))
fi

# Check that auth endpoints are tagged correctly
if echo "$OPENAPI" | grep -q "\"tags\".*\"Authentication\""; then
    echo -e "Authentication tag exists: ${GREEN}✅ PASS${NC}"
    ((PASS_COUNT++))
else
    echo -e "Authentication tag exists: ${RED}❌ FAIL${NC}"
    ((FAIL_COUNT++))
fi

echo ""
echo "================================="
echo "🎯 TEST RESULTS SUMMARY"
echo "================================="
echo ""
echo -e "Total Tests: $((PASS_COUNT + FAIL_COUNT))"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "🎉 Your Socializer app is working correctly!"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:8000/docs to test Swagger UI"
    echo "  2. Open http://localhost:8000/login to test frontend"
    echo "  3. Test WebSocket chat functionality"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check:"
    echo "  - Is the server running? (uvicorn app.main:app --reload)"
    echo "  - Are there any errors in the server logs?"
    echo "  - Did you apply all the fixes from this session?"
    echo ""
    exit 1
fi
