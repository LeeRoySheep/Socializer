#!/bin/bash

# Test authentication API endpoints
echo "=== Testing Authentication API ==="
echo ""

# Test 1: Register a new user
echo "1. Testing POST /api/auth/register"
echo "-----------------------------------"
curl -X 'POST' \
  'http://localhost:8000/api/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "testuser_'$(date +%s)'",
  "email": "test'$(date +%s)'@example.com",
  "password": "securepass123"
}'
echo ""
echo ""

# Test 2: Login with the user
echo "2. Testing POST /api/auth/login"
echo "-----------------------------------"
curl -X 'POST' \
  'http://localhost:8000/api/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "testuser",
  "password": "securepass123"
}'
echo ""
echo ""

echo "=== Tests Complete ==="
