#!/usr/bin/env bash
set -euo pipefail

BASE=${BASE_URL:-http://127.0.0.1:8000}
PASSWORD="Test1234!"
EMAIL="ci_test_$(date +%s)@example.com"

echo "Using base $BASE"
echo "Creating user $EMAIL"

signup=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"firstname\":\"CI\",\"lastname\":\"Test\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"confirm_password\":\"$PASSWORD\"}" \
  "$BASE/signup_client")

echo "Signup response: $signup"

# attempt login
login=$(curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  "$BASE/login" || true)

echo "Login response: $login"

token=$(python3 - <<PY
import sys, json
try:
    j=json.loads(sys.stdin.read())
    print(j.get('access_token',''))
except Exception:
    print('')
PY
<<<"$login")

echo "Token: ${token:-<none>}"

echo "Deleting account $EMAIL"
del=$(curl -s -X POST -F "email=$EMAIL" "$BASE/delete_account" || true)
echo "Delete response: $del"

# verify deletion by attempting login again
echo "Verifying deletion by attempting login (expect 401 or error)"
login2=$(curl -s -o /dev/stdout -w "\n%{http_code}" -X POST -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  "$BASE/login" || true)
echo "Post-delete login attempt: $login2"

echo "Script finished"
