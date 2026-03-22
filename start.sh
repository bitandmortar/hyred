#!/bin/bash
# Local Resume Builder - Startup Script
# Zero-Data-Leak Resume Tailoring on M2 Mac

set -e

echo "🚀 Local Resume Builder - Starting Up"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCUMENTS_DIR="$APP_DIR/my_documents"
LANCEDB_DIR="$APP_DIR/lancedb_data"
PORT="${PORT:-8501}"
HOST="${HOST:-0.0.0.0}"

# Check if running on M2 Mac
if [[ "$(uname -m)" != "arm64" ]]; then
    echo -e "${YELLOW}⚠️  Warning: This app is optimized for M2 Mac (Apple Silicon)${NC}"
    echo "   Some features may not work as expected on Intel Macs."
    echo ""
fi

# Step 1: Create directories
echo -e "${BLUE}📁 Setting up directories...${NC}"
mkdir -p "$DOCUMENTS_DIR"
mkdir -p "$LANCEDB_DIR"
echo -e "${GREEN}   ✓ Documents: $DOCUMENTS_DIR${NC}"
echo -e "${GREEN}   ✓ LanceDB: $LANCEDB_DIR${NC}"
echo ""

# Step 2: Check Ollama
echo -e "${BLUE}🤖 Checking Ollama...${NC}"
if command -v ollama &> /dev/null; then
    if ollama list | grep -q "llama3.2"; then
        echo -e "${GREEN}   ✓ Ollama installed with llama3.2${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Ollama installed but llama3.2 not found${NC}"
        echo -e "${YELLOW}      Run: ollama pull llama3.2${NC}"
    fi
else
    echo -e "${RED}   ✗ Ollama not installed${NC}"
    echo -e "${YELLOW}      Install with: brew install ollama${NC}"
    echo ""
    echo "   Starting app anyway (LLM features will be disabled)..."
fi
echo ""

# Step 3: Check Playwright
echo -e "${BLUE}🎭 Checking Playwright...${NC}"
if command -v playwright-cli &> /dev/null; then
    echo -e "${GREEN}   ✓ Playwright installed${NC}"
else
    echo -e "${YELLOW}   ⚠️  Playwright not installed${NC}"
    echo -e "${YELLOW}      Install with: brew install playwright-cli${NC}"
    echo ""
    echo "   Job scraping will be disabled. You can paste job descriptions manually."
fi
echo ""

# Step 4: Check Python dependencies
echo -e "${BLUE}🐍 Checking Python dependencies...${NC}"
if python3 -c "import streamlit" &> /dev/null; then
    echo -e "${GREEN}   ✓ Streamlit installed${NC}"
else
    echo -e "${YELLOW}   ⚠️  Installing Python dependencies...${NC}"
    pip3 install -r "$APP_DIR/requirements.txt"
fi
echo ""

# Step 5: Start Ollama if not running
echo -e "${BLUE}🚀 Starting Ollama server...${NC}"
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 3
    echo -e "${GREEN}   ✓ Ollama server started${NC}"
else
    echo -e "${GREEN}   ✓ Ollama server already running${NC}"
fi
echo ""

# Step 6: Start Streamlit app
echo -e "${BLUE}📄 Starting Streamlit app...${NC}"
echo -e "${GREEN}   Access at: http://localhost:$PORT${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  🔒 Privacy Notice:${NC}"
echo -e "${YELLOW}     All processing happens locally.${NC}"
echo -e "${YELLOW}     No data leaves your network.${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$APP_DIR"
streamlit run main_ui.py \
    --server.port="$PORT" \
    --server.address="$HOST" \
    --server.headless=false \
    --browser.gatherUsageStats=false \
    --server.enableXsrfProtection=true \
    --server.enableCORS=false

# Script will continue running Streamlit in foreground
# Press Ctrl+C to stop
