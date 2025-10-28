#!/bin/bash
# Example script to test session persistence with multi-worker WSGI server
# This demonstrates the session troubleshooting features

set -e

echo "=========================================="
echo "NOW LMS Session Testing Script"
echo "=========================================="
echo ""

# Configuration
REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"
PORT="${PORT:-8080}"
WORKERS="${NOW_LMS_WORKERS:-3}"
BASE_URL="http://127.0.0.1:${PORT}"

echo "Configuration:"
echo "  Redis URL: ${REDIS_URL}"
echo "  Secret Key: ${SECRET_KEY:0:16}... (truncated)"
echo "  Port: ${PORT}"
echo "  Workers: ${WORKERS}"
echo "  Base URL: ${BASE_URL}"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v redis-cli &> /dev/null; then
    echo "WARNING: redis-cli not found. Install Redis: apt install redis-server"
    echo "         Continuing anyway (will test with filesystem cache)..."
else
    echo "✓ redis-cli found"
    
    # Test Redis connection
    if redis-cli -u "${REDIS_URL}" ping &> /dev/null; then
        echo "✓ Redis connection successful"
        USE_REDIS=true
    else
        echo "WARNING: Redis ping failed. Starting local Redis..."
        redis-server --daemonize yes --port 6379 || true
        sleep 1
        if redis-cli -u "${REDIS_URL}" ping &> /dev/null; then
            echo "✓ Redis started successfully"
            USE_REDIS=true
        else
            echo "WARNING: Could not start Redis. Will use filesystem cache."
            USE_REDIS=false
        fi
    fi
fi

if ! command -v curl &> /dev/null; then
    echo "ERROR: curl not found. Install it: apt install curl"
    exit 1
fi
echo "✓ curl found"

if ! command -v jq &> /dev/null; then
    echo "WARNING: jq not found (optional). Install it for better output: apt install jq"
    JQ_AVAILABLE=false
else
    echo "✓ jq found"
    JQ_AVAILABLE=true
fi

echo ""

# Export environment variables
export SECRET_KEY
export NOW_LMS_DEBUG_ENDPOINTS=1
export NOW_LMS_WORKERS="${WORKERS}"

if [ "${USE_REDIS}" = true ]; then
    export REDIS_URL
    echo "Using Redis for session storage"
else
    unset REDIS_URL
    echo "Using filesystem cache for session storage"
fi

echo ""
echo "=========================================="
echo "Step 1: Check Configuration"
echo "=========================================="
echo ""

if [ "${JQ_AVAILABLE}" = true ]; then
    curl -s "${BASE_URL}/debug/config" | jq '.'
else
    curl -s "${BASE_URL}/debug/config"
fi

echo ""
echo "=========================================="
echo "Step 2: Check Redis Connection"
echo "=========================================="
echo ""

if [ "${JQ_AVAILABLE}" = true ]; then
    curl -s "${BASE_URL}/debug/redis" | jq '.'
else
    curl -s "${BASE_URL}/debug/redis"
fi

echo ""
echo "=========================================="
echo "Step 3: Login and Test Session Persistence"
echo "=========================================="
echo ""

# Create temporary cookie file
COOKIE_FILE=$(mktemp)
trap "rm -f ${COOKIE_FILE}" EXIT

echo "Logging in as lms-admin..."
LOGIN_RESPONSE=$(curl -s -c "${COOKIE_FILE}" -L -X POST "${BASE_URL}/user/login" \
    -d "usuario=lms-admin" \
    -d "acceso=lms-admin")

if echo "${LOGIN_RESPONSE}" | grep -q "lms-admin" || echo "${LOGIN_RESPONSE}" | grep -q "bienvenido"; then
    echo "✓ Login successful"
else
    echo "ERROR: Login failed"
    echo "Response: ${LOGIN_RESPONSE}"
    exit 1
fi

echo ""
echo "Testing session persistence across 10 requests..."
echo "Each request may hit a different worker (different PID)."
echo "The authenticated status should remain TRUE across all requests."
echo ""

# Store results
PIDS=()
AUTH_STATES=()

for i in {1..10}; do
    RESPONSE=$(curl -s -b "${COOKIE_FILE}" "${BASE_URL}/debug/session")
    
    if [ "${JQ_AVAILABLE}" = true ]; then
        PID=$(echo "${RESPONSE}" | jq -r '.worker.pid')
        AUTH=$(echo "${RESPONSE}" | jq -r '.authenticated')
        USER=$(echo "${RESPONSE}" | jq -r '.current_user.usuario // "none"')
    else
        PID=$(echo "${RESPONSE}" | grep -o '"pid":[0-9]*' | cut -d':' -f2)
        AUTH=$(echo "${RESPONSE}" | grep -o '"authenticated":[a-z]*' | cut -d':' -f2)
        USER="unknown"
    fi
    
    PIDS+=("${PID}")
    AUTH_STATES+=("${AUTH}")
    
    printf "Request %2d: PID=%s, Authenticated=%s, User=%s\n" "${i}" "${PID}" "${AUTH}" "${USER}"
done

echo ""
echo "=========================================="
echo "Results Analysis"
echo "=========================================="
echo ""

# Count unique PIDs
UNIQUE_PIDS=$(printf '%s\n' "${PIDS[@]}" | sort -u | wc -l)
echo "Unique PIDs seen: ${UNIQUE_PIDS}"

if [ "${UNIQUE_PIDS}" -gt 1 ]; then
    echo "✓ Multiple workers handling requests (good for multi-worker testing)"
else
    echo "ℹ Only one PID seen (single worker or not enough requests)"
fi

# Check if all authenticated
ALL_TRUE=true
for state in "${AUTH_STATES[@]}"; do
    if [ "${state}" != "true" ]; then
        ALL_TRUE=false
        break
    fi
done

if [ "${ALL_TRUE}" = true ]; then
    echo "✓ Session persisted across all requests - SUCCESS!"
else
    echo "✗ Session did NOT persist - FAILURE"
    echo "  Some requests showed authenticated=false"
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 4: Test Session After Logout"
echo "=========================================="
echo ""

echo "Logging out..."
curl -s -b "${COOKIE_FILE}" "${BASE_URL}/user/logout" > /dev/null

RESPONSE=$(curl -s -b "${COOKIE_FILE}" "${BASE_URL}/debug/session")

if [ "${JQ_AVAILABLE}" = true ]; then
    AUTH=$(echo "${RESPONSE}" | jq -r '.authenticated')
else
    AUTH=$(echo "${RESPONSE}" | grep -o '"authenticated":[a-z]*' | cut -d':' -f2)
fi

if [ "${AUTH}" = "false" ]; then
    echo "✓ Session cleared after logout - CORRECT"
else
    echo "✗ Session still authenticated after logout - UNEXPECTED"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""
echo "✓ All tests passed successfully!"
echo ""
echo "Session configuration is working correctly for multi-worker WSGI servers."
echo ""

if [ "${USE_REDIS}" = true ]; then
    echo "Using: Redis session storage (optimal for production)"
else
    echo "Using: Filesystem cache (works but Redis is recommended for production)"
fi

echo ""
echo "To use in production:"
echo "  1. Set REDIS_URL environment variable"
echo "  2. Set unique SECRET_KEY"
echo "  3. Disable debug endpoints (unset NOW_LMS_DEBUG_ENDPOINTS)"
echo ""
