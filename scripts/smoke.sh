#!/bin/bash
# Smoke tests - basic health checks for services
# Tests that all critical endpoints are responding

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "🔥 Running smoke tests..."
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    echo -n "Testing $name... "
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 || echo "000")
    
    if [ "$http_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $http_code)"
        return 0
    else
        echo -e "${RED}✗${NC} (HTTP $http_code, expected $expected_code)"
        return 1
    fi
}

# Track failures
FAILURES=0

# Backend health check
echo "🏥 Backend Health Checks:"
check_endpoint "$BACKEND_URL/health/" "Health endpoint" || ((FAILURES++))
check_endpoint "$BACKEND_URL/admin/" "Admin panel" || ((FAILURES++))

# API endpoints (should return 401 for unauthenticated requests)
echo ""
echo "🔌 API Endpoints:"
check_endpoint "$BACKEND_URL/api/auth/me/" "Auth endpoint" 401 || ((FAILURES++))
check_endpoint "$BACKEND_URL/api/contents/" "Contents API" 401 || ((FAILURES++))
check_endpoint "$BACKEND_URL/api/ai/usage/summary/" "AI Usage API" 401 || ((FAILURES++))

# Frontend check
echo ""
echo "🎨 Frontend Check:"
check_endpoint "$FRONTEND_URL/" "Frontend root" || ((FAILURES++))

echo ""
echo "================================"

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILURES test(s) failed${NC}"
    exit 1
fi
