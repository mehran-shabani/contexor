#!/bin/bash
# Frontend test script
# Runs npm test if available

set -e

echo "🧪 Running frontend tests..."

cd frontend

# Check if test script exists in package.json
if npm run | grep -q "test"; then
    npm test --if-present
    echo "✅ Frontend tests completed!"
else
    echo "⚠️  No frontend tests configured"
    exit 0
fi
