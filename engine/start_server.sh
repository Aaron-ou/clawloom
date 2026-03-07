#!/bin/bash
# ClawLoom Server Startup Script

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 ClawLoom Server Launcher${NC}"
echo "=============================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📥 Installing dependencies...${NC}"
pip install -q -r requirements.txt

# Check environment variables
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  DATABASE_URL not set, using default${NC}"
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/clawloom"
fi

if [ -z "$OPENCLAW_URL" ]; then
    echo -e "${YELLOW}⚠️  OPENCLAW_URL not set, using default${NC}"
    export OPENCLAW_URL="http://localhost:8080"
fi

# Start server
echo -e "${GREEN}✅ Starting ClawLoom API Server...${NC}"
echo ""
echo "📡 Server will be available at:"
echo "   - API: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo "=============================="

# Run server
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
