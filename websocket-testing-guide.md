# WebSocket Testing Guide - OpenIM Server

This guide provides comprehensive instructions for testing the WebSocket workflow in the OpenIM server.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Manual Testing](#manual-testing)
- [Test Scenarios](#test-scenarios)
- [Performance Testing](#performance-testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

1. **Go** (1.21+)
   ```bash
   go version
   ```

2. **Redis** (for online cache)
   ```bash
   # Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **PostgreSQL/MySQL** (for data storage - optional for basic testing)

4. **WebSocket Client Tools**:
   - [wscat](https://github.com/websockets/wscat) - Command-line WebSocket client
   - [Postman](https://www.postman.com/) - GUI testing
   - Browser DevTools - Built-in WebSocket testing
   - Python: `pip install websocket-client`

### Build the Project

```bash
# Build all services
mage build

# Or build specific service
mage build openim-msggateway
```

### Start Services

```bash
# Start all services
mage start

# Or start specific service
mage start openim-msggateway
```

### Check Service Status

```bash
# Check if services are running
mage check
```

## Quick Start

### 1. Verify WebSocket Server is Running

```bash
# Check if msggateway is running
ps aux | grep openim-msggateway

# Or check the port (default: 10001)
netstat -tuln | grep 10001
# or
lsof -i :10001
```

### 2. Test Basic Connection

```bash
# Using wscat
wscat -c "ws://localhost:10001/?token=YOUR_TOKEN&sendID=test_user&platformID=1&operationID=test_001"
```

## Unit Testing

### Run Existing Tests

```bash
# Run all tests in msggateway package
cd internal/msggateway
go test -v

# Run specific test
go test -v -run TestCompressDecompress

# Run with coverage
go test -v -cover -coverprofile=coverage.out
go tool cover -html=coverage.out
```

### Create Additional Unit Tests

Create file: `internal/msggateway/client_test.go`

```go
package msggateway

import (
	"testing"
	"github.com/stretchr/testify/assert"
)

func TestClientReset(t *testing.T) {
	ctx := newContext(nil, &http.Request{URL: &url.URL{}})
	conn := NewWebSocketClientConn(nil, maxMessageSize, pongWait, pingInterval)
	server := &WsServer{}

	client := new(Client)
	client.ResetClient(ctx, conn, server)

	assert.NotNil(t, client.w)
	assert.NotNil(t, client.conn)
	assert.Equal(t, 0, client.PlatformID)
	assert.False(t, client.IsCompress)
	assert.False(t, client.IsBackground)
	assert.False(t, client.closed.Load())
}

func TestMessageEncoding(t *testing.T) {
	req := &Req{
		ReqIdentifier: WSSendMsg,
		SendID:        "test_user",
		OperationID:   "test_001",
		MsgIncr:       "msg_001",
	}

	encoder := NewJsonEncoder()
	data, err := encoder.Encode(req)
	assert.NoError(t, err)
	assert.NotNil(t, data)

	var decoded Req
	err = encoder.Decode(data, &decoded)
	assert.NoError(t, err)
	assert.Equal(t, req.ReqIdentifier, decoded.ReqIdentifier)
	assert.Equal(t, req.SendID, decoded.SendID)
}
```

### Run Benchmarks

```bash
# Run compression benchmarks
go test -bench=. -benchmem

# Run specific benchmark
go test -bench=BenchmarkCompress -benchmem
```

## Integration Testing

### Integration Test Script

Create file: `tests/integration/websocket_test.go`

```go
package integration

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"github.com/stretchr/testify/assert"
)

const (
	wsURL       = "ws://localhost:10001"
	testUserID  = "test_user_001"
	testToken   = "test_token"
	testOpID    = "test_operation_001"
	platformID  = 1 // Web platform
)

func TestWebSocketConnection(t *testing.T) {
	// Create WebSocket URL with query parameters
	u, err := url.Parse(wsURL)
	assert.NoError(t, err)

	q := u.Query()
	q.Set("token", testToken)
	q.Set("sendID", testUserID)
	q.Set("platformID", fmt.Sprintf("%d", platformID))
	q.Set("operationID", testOpID)
	u.RawQuery = q.Encode()

	// Connect to WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	assert.NoError(t, err)
	defer conn.Close()

	// Wait for connection to establish
	time.Sleep(100 * time.Millisecond)

	// Test connection is still alive
	err = conn.WriteMessage(websocket.PingMessage, []byte{})
	assert.NoError(t, err)

	t.Log("WebSocket connection successful")
}

func TestSendMessage(t *testing.T) {
	u, err := url.Parse(wsURL)
	assert.NoError(t, err)

	q := u.Query()
	q.Set("token", testToken)
	q.Set("sendID", testUserID)
	q.Set("platformID", fmt.Sprintf("%d", platformID))
	q.Set("operationID", testOpID)
	u.RawQuery = u.RawQuery

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	assert.NoError(t, err)
	defer conn.Close()

	// Wait for connection
	time.Sleep(100 * time.Millisecond)

	// Send a message
	req := map[string]interface{}{
		"reqIdentifier": 1003, // WSSendMsg
		"sendID":        testUserID,
		"operationID":   testOpID,
		"msgIncr":       "msg_001",
		"data":          []byte("test message"),
	}

	reqBytes, _ := json.Marshal(req)
	err = conn.WriteMessage(websocket.BinaryMessage, reqBytes)
	assert.NoError(t, err)

	// Read response
	_, resp, err := conn.ReadMessage()
	assert.NoError(t, err)
	assert.NotEmpty(t, resp)

	t.Log("Message sent and received response")
}

func TestCompression(t *testing.T) {
	u, err := url.Parse(wsURL)
	assert.NoError(t, err)

	q := u.Query()
	q.Set("token", testToken)
	q.Set("sendID", testUserID)
	q.Set("platformID", fmt.Sprintf("%d", platformID))
	q.Set("operationID", testOpID)
	q.Set("compression", "gzip")
	u.RawQuery = q.Encode()

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	assert.NoError(t, err)
	defer conn.Close()

	time.Sleep(100 * time.Millisecond)

	// Send message
	req := map[string]interface{}{
		"reqIdentifier": 1003,
		"sendID":        testUserID,
		"operationID":   testOpID,
		"msgIncr":       "msg_001",
		"data":          []byte("test message"),
	}

	reqBytes, _ := json.Marshal(req)
	err = conn.WriteMessage(websocket.BinaryMessage, reqBytes)
	assert.NoError(t, err)

	t.Log("Compression test passed")
}

func TestMultipleConnections(t *testing.T) {
	connections := make([]*websocket.Conn, 5)

	// Create multiple connections
	for i := 0; i < 5; i++ {
		u, err := url.Parse(wsURL)
		assert.NoError(t, err)

		userID := fmt.Sprintf("%s_%d", testUserID, i)
		q := u.Query()
		q.Set("token", testToken)
		q.Set("sendID", userID)
		q.Set("platformID", fmt.Sprintf("%d", platformID))
		q.Set("operationID", testOpID)
		u.RawQuery = q.Encode()

		conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
		assert.NoError(t, err)
		connections[i] = conn
	}
	defer func() {
		for _, conn := range connections {
			conn.Close()
		}
	}()

	// Wait for all connections to establish
	time.Sleep(500 * time.Millisecond)

	// Test each connection
	for i, conn := range connections {
		err := conn.WriteMessage(websocket.PingMessage, []byte{})
		assert.NoError(t, err, "Connection %d failed", i)
	}

	t.Log("Multiple connections test passed")
}
```

### Run Integration Tests

```bash
# Run all integration tests
go test -v ./tests/integration/

# Run specific test
go test -v ./tests/integration/ -run TestWebSocketConnection

# Run with timeout
go test -v -timeout 30s ./tests/integration/
```

## Manual Testing

### 1. Using wscat (Command Line)

#### Install wscat
```bash
npm install -g wscat
```

#### Basic Connection Test
```bash
wscat -c "ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001"
```

#### Send Message
After connecting, type a message in JSON format:
```json
{
  "reqIdentifier": 1003,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "msg001",
  "data": "SGVsbG8gV29ybGQ="
}
```

Note: `data` should be base64 encoded

#### With Compression
```bash
wscat -c "ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001&compression=gzip"
```

### 2. Using Browser DevTools

#### JavaScript Console Test
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001');

// Connection open
ws.onopen = function(event) {
    console.log('Connected to WebSocket');

    // Send a message
    const message = {
        reqIdentifier: 1003, // WSSendMsg
        sendID: 'user001',
        operationID: 'op001',
        msgIncr: 'msg001',
        data: btoa('Hello World') // base64 encode
    };

    ws.send(JSON.stringify(message));
};

// Message received
ws.onmessage = function(event) {
    console.log('Message received:', event.data);
};

// Connection closed
ws.onclose = function(event) {
    console.log('WebSocket closed');
};

// Error occurred
ws.onerror = function(event) {
    console.error('WebSocket error:', event);
};
```

### 3. Using Python

Create file: `test_websocket.py`

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
            "reqIdentifier": 1003,  # WSSendMsg
            "sendID": "user001",
            "operationID": "op001",
            "msgIncr": "msg001",
            "data": base64.b64encode(b"Hello World").decode()
        }

        await websocket.send(json.dumps(message))
        print(f"Sent message: {message}")

        # Receive response
        response = await websocket.recv()
        print(f"Received response: {response}")

# Run the test
asyncio.run(test_websocket())
```

Install dependencies and run:
```bash
pip install websockets
python test_websocket.py
```

### 4. Using Postman

1. Open Postman
2. Create new WebSocket request: `ws://localhost:10001`
3. Add query parameters:
   - `token`: `test_token`
   - `sendID`: `user001`
   - `platformID`: `1`
   - `operationID`: `op001`
4. Click Connect
5. Send message in JSON format

### 5. Using Go Test Client

Create file: `test_client.go`

```go
package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log"
	"net/url"

	"github.com/gorilla/websocket"
)

func main() {
	// Build WebSocket URL
	u, err := url.Parse("ws://localhost:10001")
	if err != nil {
		log.Fatal(err)
	}

	q := u.Query()
	q.Set("token", "test_token")
	q.Set("sendID", "user001")
	q.Set("platformID", "1")
	q.Set("operationID", "op001")
	u.RawQuery = q.Encode()

	// Connect to WebSocket
	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Fatal("Dial error:", err)
	}
	defer conn.Close()

	fmt.Println("Connected to WebSocket")

	// Send a message
	req := map[string]interface{}{
		"reqIdentifier": 1003, // WSSendMsg
		"sendID":        "user001",
		"operationID":   "op001",
		"msgIncr":       "msg001",
		"data":          base64.StdEncoding.EncodeToString([]byte("Hello World")),
	}

	reqBytes, err := json.Marshal(req)
	if err != nil {
		log.Fatal("Marshal error:", err)
	}

	err = conn.WriteMessage(websocket.BinaryMessage, reqBytes)
	if err != nil {
		log.Fatal("Write error:", err)
	}

	fmt.Println("Message sent")

	// Read response
	_, resp, err := conn.ReadMessage()
	if err != nil {
		log.Fatal("Read error:", err)
	}

	fmt.Printf("Response: %s\n", resp)
}
```

Run:
```bash
go run test_client.go
```

## Test Scenarios

### Scenario 1: Basic Connection Flow

**Test Steps:**
1. Start the msggateway service
2. Connect with valid token
3. Verify connection is established
4. Send ping message
5. Receive pong response
6. Close connection gracefully

**Expected Result:**
- Connection succeeds
- Ping/pong works
- No errors in logs

### Scenario 2: Authentication

**Test Steps:**
1. Connect without token
2. Connect with invalid token
3. Connect with valid token

**Expected Result:**
- Without token: Connection rejected (401 or error)
- Invalid token: Connection rejected
- Valid token: Connection succeeds

### Scenario 3: Multi-Terminal Login

**Test Steps:**
1. Connect user1 from platform 1 (web)
2. Connect user1 from platform 2 (mobile)
3. Connect user1 from same platform again

**Expected Result:**
- First two connections succeed
- Third connection kicks first or succeeds based on policy

### Scenario 4: Message Sending

**Test Steps:**
1. Connect two users (user1, user2)
2. Send message from user1 to user2
3. Verify user2 receives the message

**Expected Result:**
- Message sent successfully
- Message received by target user
- No errors in logs

### Scenario 5: Compression

**Test Steps:**
1. Connect with compression=gzip
2. Send a large message (>10KB)
3. Verify compression is applied
4. Decompress and verify data integrity

**Expected Result:**
- Compression applied successfully
- Data integrity maintained
- Performance improvement on large messages

### Scenario 6: Connection Limits

**Test Steps:**
1. Configure max connections to small number (e.g., 10)
2. Attempt to create 15 connections
3. Verify limit is enforced

**Expected Result:**
- First 10 connections succeed
- Remaining 5 connections rejected
- Appropriate error message

### Scenario 7: Heartbeat

**Test Steps:**
1. Connect to WebSocket
2. Don't send any messages for 30+ seconds
3. Verify connection stays alive (server ping)
4. Verify pong response

**Expected Result:**
- Server sends periodic pings
- Client responds with pongs
- Connection remains active

### Scenario 8: Error Handling

**Test Steps:**
1. Send invalid message format
2. Send message with invalid reqIdentifier
3. Send message without required fields

**Expected Result:**
- Server returns appropriate error
- Connection not terminated (unless critical error)
- Error logged

### Scenario 9: Reconnection

**Test Steps:**
1. Connect user1
2. Close connection abruptly
3. Reconnect immediately with same token
4. Verify connection succeeds

**Expected Result:**
- Reconnection succeeds
- Old connection cleaned up
- No duplicate connections

### Scenario 10: Background Status

**Test Steps:**
1. Connect user1
2. Set background status to true
3. Send message to user1
4. Verify behavior (especially for iOS)

**Expected Result:**
- Background status updated
- Appropriate handling for background messages

## Performance Testing

### Load Test with Go

Create file: `load_test.go`

```go
package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log"
	"net/url"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	wsURL      = "ws://localhost:10001"
	numClients = 100
	msgPerConn = 10
)

func main() {
	var wg sync.WaitGroup
	startTime := time.Now()

	// Create multiple connections
	for i := 0; i < numClients; i++ {
		wg.Add(1)
		go func(clientID int) {
			defer wg.Done()
			clientTest(clientID)
		}(i)
	}

	wg.Wait()
	duration := time.Since(startTime)

	fmt.Printf("Load test completed:\n")
	fmt.Printf("- Clients: %d\n", numClients)
	fmt.Printf("- Messages per client: %d\n", msgPerConn)
	fmt.Printf("- Total messages: %d\n", numClients*msgPerConn)
	fmt.Printf("- Duration: %v\n", duration)
	fmt.Printf("- Messages/sec: %.2f\n", float64(numClients*msgPerConn)/duration.Seconds())
}

func clientTest(clientID int) {
	userID := fmt.Sprintf("user_%04d", clientID)

	u, err := url.Parse(wsURL)
	if err != nil {
		log.Printf("Client %d: URL parse error: %v", clientID, err)
		return
	}

	q := u.Query()
	q.Set("token", "test_token")
	q.Set("sendID", userID)
	q.Set("platformID", "1")
	q.Set("operationID", fmt.Sprintf("op_%d", clientID))
	u.RawQuery = q.Encode()

	conn, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		log.Printf("Client %d: Connection error: %v", clientID, err)
		return
	}
	defer conn.Close()

	// Send messages
	for i := 0; i < msgPerConn; i++ {
		req := map[string]interface{}{
			"reqIdentifier": 1003,
			"sendID":        userID,
			"operationID":   fmt.Sprintf("op_%d", clientID),
			"msgIncr":       fmt.Sprintf("msg_%d_%d", clientID, i),
			"data":          base64.StdEncoding.EncodeToString([]byte(fmt.Sprintf("Message %d from %s", i, userID))),
		}

		reqBytes, err := json.Marshal(req)
		if err != nil {
			log.Printf("Client %d: Marshal error: %v", clientID, err)
			continue
		}

		if err := conn.WriteMessage(websocket.BinaryMessage, reqBytes); err != nil {
			log.Printf("Client %d: Write error: %v", clientID, err)
			return
		}

		// Read response
		_, resp, err := conn.ReadMessage()
		if err != nil {
			log.Printf("Client %d: Read error: %v", clientID, err)
			return
		}

		if i%5 == 0 {
			log.Printf("Client %d: Sent %d messages, last response: %s", clientID, i+1, string(resp))
		}
	}

	log.Printf("Client %d: Completed %d messages", clientID, msgPerConn)
}
```

Run load test:
```bash
go run load_test.go
```

### Benchmark with Apache Benchmark (ab)

For HTTP endpoints:
```bash
ab -n 10000 -c 100 http://localhost:10001/
```

### Monitor Resources

```bash
# CPU and Memory usage
top -p $(pgrep openim-msggateway)

# Network connections
netstat -an | grep :10001 | wc -l

# Open file descriptors
lsof -p $(pgrep openim-msggateway) | wc -l
```

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Symptom:** Cannot connect to WebSocket server

**Solutions:**
- Check if service is running: `mage check`
- Check port is listening: `netstat -tuln | grep 10001`
- Check firewall settings
- Verify service logs: `tail -f logs/openim-msggateway.log`

#### 2. Authentication Failed

**Symptom:** Connection rejected with auth error

**Solutions:**
- Verify token is valid
- Check auth service is running
- Verify token matches user ID
- Check auth service logs

#### 3. Connection Timeout

**Symptom:** Connection takes too long or times out

**Solutions:**
- Increase timeout in configuration
- Check network latency
- Verify server load
- Check if max connections reached

#### 4. Message Not Received

**Symptom:** Message sent but not received by other party

**Solutions:**
- Verify both users are connected
- Check message routing in logs
- Verify user IDs match
- Check if receiver is in correct channel/group

#### 5. Compression Errors

**Symptom:** Errors when using compression

**Solutions:**
- Verify compression parameter is set correctly
- Check message size limits
- Verify compression protocol (gzip)
- Check decompression logic

### Debug Mode

Enable debug logging:

```bash
# Modify config to set log level to debug
# config.yaml
log:
  level: debug

# Restart service
mage stop
mage start
```

### Check Logs

```bash
# View msggateway logs
tail -f logs/openim-msggateway.log

# Search for errors
grep -i error logs/openim-msggateway.log

# Search for specific user
grep "user001" logs/openim-msggateway.log
```

### Verify Dependencies

```bash
# Check Redis connection
redis-cli ping

# Check database connection
psql -h localhost -U openim -d openim

# Check auth service
curl http://localhost:10001/health
```

## Test Checklist

- [ ] Service starts without errors
- [ ] WebSocket port is accessible
- [ ] Connection with valid token succeeds
- [ ] Connection with invalid token fails
- [ ] Basic ping/pong works
- [ ] Message sending works
- [ ] Message receiving works
- [ ] Compression works correctly
- [ ] Multi-terminal login handled correctly
- [ ] Connection limits enforced
- [ ] Heartbeat keeps connection alive
- [ ] Reconnection works
- [ ] Background status updates work
- [ ] Error messages are appropriate
- [ ] Logs show expected information
- [ ] Performance meets requirements
- [ ] Resource usage is acceptable
- [ ] Graceful shutdown works

## Additional Resources

- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [Gorilla WebSocket Documentation](https://github.com/gorilla/websocket)
- [OpenIM Documentation](https://docs.openim.io/)
- [OpenIM GitHub](https://github.com/openimsdk/open-im-server)

---

**Document Version:** 1.0
**Last Updated:** 2026-03-05