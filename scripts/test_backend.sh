#!/bin/bash
# Backend test script
# Runs pytest with quiet output

set -e

echo "🧪 Running backend tests..."

cd backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pytest with quiet output
pytest -q --tb=short

echo "✅ Backend tests completed!"
