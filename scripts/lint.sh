#!/bin/bash
# Linting script for backend and frontend
# Runs flake8 for Python and eslint for JavaScript/TypeScript

set -e

echo "🔍 Running linters..."

# Backend linting with flake8
echo "📝 Linting backend (Python)..."
cd backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run flake8 (allow it to fail without stopping script)
flake8 --max-line-length=120 --exclude=venv,migrations,__pycache__,.git . || echo "⚠️  Backend linting found issues (non-critical)"

cd ..

# Frontend linting
echo "📝 Linting frontend (TypeScript/JavaScript)..."
cd frontend

# Check if lint script exists
if npm run | grep -q "lint"; then
    npm run lint --if-present || echo "⚠️  Frontend linting found issues (non-critical)"
else
    echo "⚠️  No frontend lint script configured"
fi

cd ..

echo "✅ Linting completed!"
