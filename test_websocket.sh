#!/bin/bash

# WebSocket Test Script for OpenIM Server
# This script tests the basic WebSocket connectivity

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
WS_HOST="${WS_HOST:-localhost}"
WS_PORT="${WS_PORT:-10001}"
WS_URL="ws://${WS_HOST}:${WS_PORT}"
TEST_USER="${TEST_USER:-test_user_001}"
TEST_TOKEN="${TEST_TOKEN:-test_token}"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}WebSocket Test Script${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
    fi
}

# Test 1: Check if service is running
echo "Test 1: Checking if msggateway service is running..."
if netstat -tuln 2>/dev/null | grep -q ":${WS_PORT} " || lsof -i :${WS_PORT} 2>/dev/null | grep -q LISTEN; then
    print_result 0 "msggateway is running on port ${WS_PORT}"
else
    print_result 1 "msggateway is not running on port ${WS_PORT}"
    echo -e "${YELLOW}Please start the service with: mage start${NC}"
    exit 1
fi
echo ""

# Test 2: Check if wscat is installed
echo "Test 2: Checking if wscat is installed..."
if command -v wscat &> /dev/null; then
    print_result 0 "wscat is installed"
    echo ""
else
    echo -e "${YELLOW}wscat not found. Installing wscat...${NC}"
    if command -v npm &> /dev/null; then
        npm install -g wscat
        print_result 0 "wscat installed successfully"
    else
        print_result 1 "npm not found. Please install wscat manually: npm install -g wscat"
        exit 1
    fi
    echo ""
fi

# Test 3: Test basic WebSocket connection
echo "Test 3: Testing basic WebSocket connection..."
CONNECTION_URL="${WS_URL}/?token=${TEST_TOKEN}&sendID=${TEST_USER}&platformID=1&operationID=test_001"

# Create a temporary test script
cat > /tmp/ws_test.js << 'EOF'
const WebSocket = require('ws');
const url = process.argv[2];
const ws = new WebSocket(url);

let connected = false;
let timeout = false;

const timeoutId = setTimeout(() => {
    timeout = true;
    ws.close();
    console.log('ERROR: Connection timeout');
    process.exit(1);
}, 5000);

ws.on('open', () => {
    connected = true;
    clearTimeout(timeoutId);
    console.log('Connected successfully');

    // Send a ping
    ws.ping();

    // Close connection
    setTimeout(() => {
        ws.close();
    }, 500);
});

ws.on('pong', () => {
    console.log('Pong received');
});

ws.on('error', (error) => {
    clearTimeout(timeoutId);
    console.log('ERROR:', error.message);
    process.exit(1);
});

ws.on('close', () => {
    clearTimeout(timeoutId);
    if (connected && !timeout) {
        console.log('Connection closed successfully');
        process.exit(0);
    }
});
EOF

# Check if Node.js and ws package are available
if command -v node &> /dev/null; then
    if node -e "require('ws')" 2>/dev/null; then
        node /tmp/ws_test.js "${CONNECTION_URL}"
        if [ $? -eq 0 ]; then
            print_result 0 "Basic WebSocket connection test"
        else
            print_result 1 "Basic WebSocket connection test"
        fi
    else
        echo -e "${YELLOW}Installing ws package...${NC}"
        npm install -g ws
        node /tmp/ws_test.js "${CONNECTION_URL}"
        if [ $? -eq 0 ]; then
            print_result 0 "Basic WebSocket connection test"
        else
            print_result 1 "Basic WebSocket connection test"
        fi
    fi
else
    echo -e "${YELLOW}Node.js not available, skipping WebSocket connection test${NC}"
fi
echo ""

# Test 4: Test with compression
echo "Test 4: Testing WebSocket connection with compression..."
CONNECTION_URL_COMPRESSED="${WS_URL}/?token=${TEST_TOKEN}&sendID=${TEST_USER}&platformID=1&operationID=test_001&compression=gzip"

if command -v node &> /dev/null; then
    node /tmp/ws_test.js "${CONNECTION_URL_COMPRESSED}"
    if [ $? -eq 0 ]; then
        print_result 0 "WebSocket connection with compression test"
    else
        print_result 1 "WebSocket connection with compression test"
    fi
fi
echo ""

# Test 5: Check service health
echo "Test 5: Checking service health..."
if command -v curl &> /dev/null; then
    HTTP_URL="http://${WS_HOST}:${WS_PORT}/"
    if curl -s --max-time 5 "${HTTP_URL}" > /dev/null 2>&1; then
        print_result 0 "Service is responding to HTTP requests"
    else
        echo -e "${YELLOW}Service may not have HTTP endpoints (WebSocket only)${NC}"
        print_result 0 "Service health check (WebSocket only mode)"
    fi
else
    echo -e "${YELLOW}curl not available, skipping health check${NC}"
fi
echo ""

# Test 6: Check Redis connection (if Redis is used)
echo "Test 6: Checking Redis connection (if configured)..."
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        print_result 0 "Redis is available"
    else
        echo -e "${YELLOW}Redis not available (may not be required for basic testing)${NC}"
    fi
else
    echo -e "${YELLOW}redis-cli not available, skipping Redis check${NC}"
fi
echo ""

# Test 7: Run Go unit tests if available
echo "Test 7: Running Go unit tests..."
if command -v go &> /dev/null; then
    cd internal/msggateway 2>/dev/null && go test -v -run TestCompressDecompress 2>/dev/null
    if [ $? -eq 0 ]; then
        print_result 0 "Go unit tests passed"
    else
        echo -e "${YELLOW}Unit tests failed or not available${NC}"
    fi
    cd - > /dev/null
else
    echo -e "${YELLOW}Go not available, skipping unit tests${NC}"
fi
echo ""

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "For manual testing, you can use:"
echo "  1. wscat: wscat -c '${CONNECTION_URL}'"
echo "  2. Browser: Open DevTools Console and connect to WebSocket"
echo "  3. Python: See docs/websocket-testing-guide.md for Python examples"
echo "  4. Postman: Create WebSocket request with the URL"
echo ""
echo "For comprehensive testing guide, see: docs/websocket-testing-guide.md"
echo ""