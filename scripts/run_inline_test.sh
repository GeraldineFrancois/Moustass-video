#!/usr/bin/env bash
set -euo pipefail

BASE=http://localhost:8001
EMAIL="test$(date +%s)@example.com"
PASSWORD="Str0ngPass!23"

echo "Using $EMAIL"

echo "SIGNUP..."
SIGNUP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/signup_client" -H "Content-Type: application/json" -d "{\"firstname\":\"Test\",\"lastname\":\"User\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"confirm_password\":\"$PASSWORD\"}")
SIGNUP_BODY=$(printf "%s" "$SIGNUP" | sed '$d')
SIGNUP_STATUS=$(printf "%s" "$SIGNUP" | tail -n1)
echo "SIGNUP status:$SIGNUP_STATUS body:$SIGNUP_BODY"

TOKEN=$(python3 -c "import sys,json; s=sys.stdin.read(); j=json.loads(s or '{}'); print(j.get('access_token',''))" <<< "$SIGNUP_BODY")
echo "token:$TOKEN"

echo "LOGIN..."
LOGIN=$(curl -s -w "\n%{http_code}" -X POST "$BASE/login" -H "Content-Type: application/json" -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
LOGIN_BODY=$(printf "%s" "$LOGIN" | sed '$d')
LOGIN_STATUS=$(printf "%s" "$LOGIN" | tail -n1)
echo "LOGIN status:$LOGIN_STATUS body:$LOGIN_BODY"

TOKEN2=$(python3 -c "import sys,json; s=sys.stdin.read(); j=json.loads(s or '{}'); print(j.get('access_token',''))" <<< "$LOGIN_BODY")
echo "token2:$TOKEN2"

echo "DELETE..."
DELETE=$(curl -s -w "\n%{http_code}" -X POST "$BASE/delete_account" -d "email=$EMAIL")
DELETE_BODY=$(printf "%s" "$DELETE" | sed '$d')
DELETE_STATUS=$(printf "%s" "$DELETE" | tail -n1)
echo "DELETE status:$DELETE_STATUS body:$DELETE_BODY"

echo "VERIFY /me with previous token (should be 404)..."
ME=$(curl -s -w "\n%{http_code}" -X GET "$BASE/me" -H "Authorization: Bearer $TOKEN")
ME_BODY=$(printf "%s" "$ME" | sed '$d')
ME_STATUS=$(printf "%s" "$ME" | tail -n1)
echo "/me status:$ME_STATUS body:$ME_BODY"
