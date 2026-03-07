#!/bin/bash
# ClawLoom API Test Runner

echo "🧪 ClawLoom API Test Runner"
echo "============================"

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server is not running!"
    echo "   Please start the server first: ./start_server.sh"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run tests
echo "🚀 Running API tests..."
echo ""
python api/test_api.py
