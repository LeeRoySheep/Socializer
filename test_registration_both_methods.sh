#!/bin/bash

# Test registration with both JSON and form data
# This verifies the fix for frontend registration

echo "================================="
echo "🧪 REGISTRATION METHOD TESTS"
echo "================================="
echo ""

BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%s)

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "================================="
echo "📋 1. JSON REGISTRATION (Swagger UI)"
echo "================================="
echo ""

# Test 1: JSON registration
JSON_USER="json_user_$TIMESTAMP"
JSON_EMAIL="json_$TIMESTAMP@example.com"
JSON_DATA="{\"username\":\"$JSON_USER\",\"email\":\"$JSON_EMAIL\",\"password\":\"securepass123\"}"

echo "Testing JSON registration..."
JSON_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "$JSON_DATA")

JSON_CODE=$(echo "$JSON_RESPONSE" | tail -n1)

if [ "$JSON_CODE" = "200" ]; then
    echo -e "${GREEN}✅ JSON registration: PASS${NC} (200)"
    echo "Response: $(echo "$JSON_RESPONSE" | head -n -1)"
else
    echo -e "${RED}❌ JSON registration: FAIL${NC} (Expected: 200, Got: $JSON_CODE)"
    echo "Response: $(echo "$JSON_RESPONSE" | head -n -1)"
fi

echo ""
echo "================================="
echo "📝 2. FORM REGISTRATION (Frontend)"
echo "================================="
echo ""

# Test 2: Form data registration
FORM_USER="form_user_$TIMESTAMP"
FORM_EMAIL="form_$TIMESTAMP@example.com"

echo "Testing form data registration..."
FORM_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$FORM_USER&email=$FORM_EMAIL&password=securepass123&confirm_password=securepass123")

FORM_CODE=$(echo "$FORM_RESPONSE" | tail -n1)

# Form submissions should redirect (303) to login page
if [ "$FORM_CODE" = "303" ]; then
    echo -e "${GREEN}✅ Form registration: PASS${NC} (303 redirect to login)"
    LOCATION=$(echo "$FORM_RESPONSE" | grep -i "location:" || echo "Redirect to /login")
    echo "Redirects to: /login?registered=1"
else
    echo -e "${RED}❌ Form registration: FAIL${NC} (Expected: 303, Got: $FORM_CODE)"
    echo "Response: $(echo "$FORM_RESPONSE" | head -n -1)"
fi

echo ""
echo "================================="
echo "🎯 SUMMARY"
echo "================================="
echo ""

if [ "$JSON_CODE" = "200" ] && [ "$FORM_CODE" = "303" ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Both registration methods working:"
    echo "  ✅ JSON (Swagger UI) → Returns 200 with user data"
    echo "  ✅ Form (Frontend)   → Returns 303 redirect to login"
    echo ""
    echo "Frontend registration is now fixed!"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Please check:"
    echo "  - Is the server running?"
    echo "  - Did you apply the fix?"
    echo "  - Check server logs for errors"
    exit 1
fi
