#!/bin/bash
# Start SQLite test server

echo "🚀 Starting ClawLoom SQLite Test Server"
echo "=========================================="

cd /root/.openclaw/workspace/projects/clawloom/engine

# Check if port is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use. Stopping existing server..."
    kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null
    sleep 1
fi

# Start server in background
echo "📝 Starting server..."
python3 -m uvicorn api.server_sqlite:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo ""
    echo "✅ Server is running!"
    echo ""
    echo "📡 Endpoints:"
    echo "   - API: http://localhost:8000"
    echo "   - Docs: http://localhost:8000/docs"
    echo "   - Health: http://localhost:8000/health"
    echo ""
    echo "🧪 Run tests with: python3 api/test_sqlite.py"
    echo ""
    echo "Press Ctrl+C to stop"
    echo "=========================================="
    
    # Wait for Ctrl+C
    wait $SERVER_PID
else
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
