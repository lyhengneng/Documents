# WebSocket Testing Quick Start Guide

This guide helps you quickly test the WebSocket functionality in the OpenIM server.

## Quick Start (5 Minutes)

### 1. Start the Server

```bash
# Start all services
mage start

# Or start just the msggateway
mage start openim-msggateway

# Check if services are running
mage check
```

### 2. Run Python Test Script

```bash
# Make sure Python 3 is installed
python3 --version

# Run the test script
python3 test_websocket.py
```

The Python script will automatically:
- Install required dependencies
- Test basic connection
- Test message sending
- Test compression
- Test multiple messages
- Test heartbeat/ping-pong

### 3. Run Shell Test Script

```bash
# Make script executable (Linux/Mac)
chmod +x test_websocket.sh

# Run the script
./test_websocket.sh
```

The shell script will check:
- Service status
- Connection to WebSocket
- Compression support
- Health checks

## Manual Testing Tools

### Option 1: wscat (Command Line)

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c "ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001"

# Send a message (after connecting)
{"reqIdentifier": 1003, "sendID": "user001", "operationID": "op001", "msgIncr": "msg001", "data": "SGVsbG8gV29ybGQ="}
```

### Option 2: Browser DevTools

1. Open browser (Chrome/Firefox)
2. Press F12 to open DevTools
3. Go to Console tab
4. Paste and run:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001');

ws.onopen = function(event) {
    console.log('Connected to WebSocket');

    // Send a message
    const message = {
        reqIdentifier: 1003,
        sendID: 'user001',
        operationID: 'op001',
        msgIncr: 'msg001',
        data: btoa('Hello World')
    };

    ws.send(JSON.stringify(message));
};

ws.onmessage = function(event) {
    console.log('Message received:', event.data);
};

ws.onerror = function(event) {
    console.error('WebSocket error:', event);
};
```

### Option 3: Postman (Recommended for GUI Testing)

#### Quick Start with Postman

**Import Ready-to-Use Collection:**

1. Download Postman: https://www.postman.com/downloads/
2. Open Postman and click **Import**
3. Import the collection file: `docs/postman_collection.json`
4. Import the environment file: `docs/postman_environment.json`
5. Select "OpenIM WebSocket Environment" from environment dropdown
6. Start the server: `mage start`
7. Run any test from the collection!

**Collection Includes:**
- ✅ Connection Tests
- ✅ Message Tests (Send, Get Seq, Pull, Logout)
- ✅ Compression Tests
- ✅ Error Handling Tests
- ✅ Background Status Tests

**For detailed guide:** See `docs/postman-testing-guide.md`

#### Manual Postman Setup

1. Click **New** → **WebSocket Request**
2. Enter URL:
   ```
   ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001
   ```
3. Click **Connect**
4. Send message:
   ```json
   {
     "reqIdentifier": 1003,
     "sendID": "user001",
     "operationID": "op001",
     "msgIncr": "msg001",
     "data": "SGVsbG8gV29ybGQ="
   }
   ```

### Option 4: Python

```python
import asyncio
import websockets
import json
import base64

async def test_websocket():
    uri = "ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001"

    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")

        # Send a message
        message = {
            "reqIdentifier": 1003,
            "sendID": "user001",
            "operationID": "op001",
            "msgIncr": "msg001",
            "data": base64.b64encode(b"Hello World").decode()
        }

        await websocket.send(json.dumps(message))
        print("Message sent")

        # Receive response
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(test_websocket())
```

## Test Scenarios

### Scenario 1: Basic Connection
✓ Connect with valid parameters
✓ Verify connection established
✓ Send ping/pong

### Scenario 2: Message Sending
✓ Connect to WebSocket
✓ Send message in correct format
✓ Receive response
✓ Verify message content

### Scenario 3: Compression
✓ Connect with compression=gzip
✓ Send message
✓ Verify compression applied

### Scenario 4: Multi-Terminal
✓ Connect user1 from platform 1
✓ Connect user1 from platform 2
✓ Verify multi-terminal handling

## Troubleshooting

### Connection Refused

```bash
# Check if service is running
ps aux | grep openim-msggateway

# Check port
netstat -tuln | grep 10001

# Start service
mage start
```

### Authentication Failed

- Verify token is valid
- Check auth service is running
- Verify token matches user ID

### Timeout Errors

- Increase timeout in configuration
- Check server load
- Verify network connectivity

## View Logs

```bash
# View msggateway logs
tail -f logs/openim-msggateway.log

# Search for errors
grep -i error logs/openim-msggateway.log
```

## Test Configuration

Edit test scripts to change configuration:

**Python (test_websocket.py):**
```python
WS_HOST = "localhost"
WS_PORT = 10001
TEST_USER = "test_user_001"
TEST_TOKEN = "test_token"
```

**Shell (test_websocket.sh):**
```bash
WS_HOST="${WS_HOST:-localhost}"
WS_PORT="${WS_PORT:-10001}"
TEST_USER="${TEST_USER:-test_user_001}"
TEST_TOKEN="${TEST_TOKEN:-test_token}"
```

## Expected Results

✅ All tests pass
✅ No errors in logs
✅ Messages sent and received correctly
✅ Compression works if enabled
✅ Multiple connections handled properly

## Next Steps

For comprehensive testing, see:
- `docs/postman-testing-guide.md` - Postman testing guide (recommended)
- `docs/websocket-testing-guide.md` - Complete testing guide
- `docs/websocket-workflow.md` - Understanding WebSocket workflow

## Test Checklist

- [ ] Service starts without errors
- [ ] WebSocket port accessible
- [ ] Basic connection works
- [ ] Ping/pong works
- [ ] Message sending works
- [ ] Compression works
- [ ] Multi-terminal handled
- [ ] Connection limits enforced
- [ ] No errors in logs

## Support

If you encounter issues:
1. Check service logs: `tail -f logs/openim-msggateway.log`
2. Verify dependencies are installed
3. Check service status: `mage check`
4. Review troubleshooting section in docs/websocket-testing-guide.md

---

**Last Updated:** 2026-03-05