# Postman WebSocket Testing Guide

This guide provides detailed instructions for testing the OpenIM WebSocket server using Postman.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Connection Test](#basic-connection-test)
- [Message Sending](#message-sending)
- [Advanced Testing](#advanced-testing)
- [Test Collections](#test-collections)
- [Environment Variables](#environment-variables)
- [Common Issues](#common-issues)

## Prerequisites

- Postman application (desktop or web)
  - Download: https://www.postman.com/downloads/
  - Minimum version: v8.0.0 (WebSocket support)
- OpenIM msggateway service running
  - Default port: 10001
  - Check status: `mage check`

## Installation

### 1. Download and Install Postman

**Windows:**
1. Download from https://www.postman.com/downloads/
2. Run the installer
3. Launch Postman

**Mac:**
```bash
# Using Homebrew
brew install --cask postman

# Or download from https://www.postman.com/downloads/
```

**Linux:**
```bash
# Download from https://www.postman.com/downloads/
# Extract and run the AppImage
wget https://dl.pstmn.io/download/latest/linux64
chmod +x linux64
./linux64
```

### 2. Verify WebSocket Support

Postman v8.0+ has built-in WebSocket support. You can verify by:
1. Open Postman
2. Click "New" button
3. Look for "WebSocket Request" option

## Basic Connection Test

### Step 1: Create WebSocket Request

1. Open Postman
2. Click **New** (top left)
3. Select **WebSocket Request**
4. Enter WebSocket URL with query parameters

### Step 2: Configure Connection

**URL Format:**
```
ws://localhost:10001/?token=YOUR_TOKEN&sendID=YOUR_USER_ID&platformID=1&operationID=YOUR_OPERATION_ID
```

**Example URL:**
```
ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=op001
```

**Query Parameters:**

| Parameter | Description | Example | Required |
|-----------|-------------|---------|----------|
| `token` | Authentication token | `test_token` | Yes |
| `sendID` | Sender user ID | `user001` | Yes |
| `platformID` | Platform identifier | `1` (Web), `2` (iOS), `3` (Android) | Yes |
| `operationID` | Operation ID for tracing | `op_001` | Yes |
| `compression` | Enable compression | `gzip` | No |
| `sdkType` | SDK type | `go` or `js` | No |
| `sdkVersion` | SDK version | `1.0.0` | No |
| `isBackground` | Background status | `true` or `false` | No |
| `isMsgResp` | Send response | `true` or `false` | No |

### Step 3: Connect to WebSocket

1. Click **Connect** button
2. Wait for connection to establish
3. Check connection status indicator:
   - 🟢 Green: Connected
   - 🔴 Red: Disconnected
   - 🟡 Yellow: Connecting

### Step 4: Verify Connection

After connecting, you should see:
- Connection status: "Connected"
- Connection timestamp
- WebSocket endpoint information

**Example Output:**
```
Connected to ws://localhost:10001
Connected at: 2024-03-05 10:30:45
```

## Message Sending

### Step 1: Prepare Message Format

OpenIM uses a JSON-based message format:

```json
{
  "reqIdentifier": 1003,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "msg_001",
  "data": "SGVsbG8gV29ybGQ="
}
```

**Field Descriptions:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `reqIdentifier` | number | Message type identifier | 1003 (Send Message) |
| `sendID` | string | Sender user ID | "user001" |
| `operationID` | string | Operation ID for tracing | "op001" |
| `msgIncr` | string | Message increment ID | "msg_001" |
| `data` | string | Base64 encoded message data | "SGVsbG8gV29ybGQ=" |
| `token` | string | Authentication token (optional) | "test_token" |

### Step 2: Base64 Encode Data

The `data` field must be Base64 encoded. Here are ways to encode:

**Online Tools:**
- https://www.base64encode.org/
- https://www.base64decode.org/

**Command Line:**
```bash
# Linux/Mac
echo -n "Hello World" | base64

# Windows (PowerShell)
[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("Hello World"))
```

**JavaScript (Browser Console):**
```javascript
btoa("Hello World")
```

**Python:**
```python
import base64
base64.b64encode(b"Hello World").decode()
```

### Step 3: Send Message in Postman

1. In the message input area (bottom panel), type your message
2. Click **Send** button (or press Enter)
3. View the response in the output panel

**Example Message:**
```json
{
  "reqIdentifier": 1003,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "msg_001",
  "data": "SGVsbG8gV29ybGQgZnJvbSBQb3N0bWFuIQ=="
}
```

**Expected Response:**
```json
{
  "reqIdentifier": 1003,
  "msgIncr": "msg_001",
  "operationID": "op001",
  "errCode": 0,
  "errMsg": "",
  "data": "..."
}
```

## Advanced Testing

### Test 1: Get Sequence Numbers

**Purpose:** Get latest message sequence numbers

**Message:**
```json
{
  "reqIdentifier": 1001,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "seq_001",
  "data": "e30="
}
```

**Note:** `e30=` is Base64 for `{}` (empty object)

### Test 2: Pull Messages by Sequence

**Purpose:** Pull messages by sequence list

**Message:**
```json
{
  "reqIdentifier": 1002,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "pull_001",
  "data": "eyJzZXExIjogMSwgInNlcTIiOiAyLCAic2VxMyI6IDN9"
}
```

**Note:** Data is Base64 encoded JSON: `{"seq1": 1, "seq2": 2, "seq3": 3}`

### Test 3: User Logout

**Purpose:** Logout user

**Message:**
```json
{
  "reqIdentifier": 2003,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "logout_001",
  "data": "e30="
}
```

### Test 4: Set Background Status

**Purpose:** Set app background status

**Message:**
```json
{
  "reqIdentifier": 2004,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "bg_001",
  "data": "eyJpc0JhY2tncm91bmQiOiB0cnVlfQ=="
}
```

**Note:** Data is Base64 encoded: `{"isBackground": true}`

### Test 5: Subscribe to User Online Status

**Purpose:** Subscribe to user online status changes

**Message:**
```json
{
  "reqIdentifier": 2005,
  "sendID": "user001",
  "operationID": "op001",
  "msgIncr": "sub_001",
  "data": "eyJ1c2VySUQiOiAidXNlcjAwMiJ9"
}
```

**Note:** Data is Base64 encoded: `{"userID": "user002"}`

## Test Collections

### Creating a Test Collection

1. Click **Collections** (left sidebar)
2. Click **+ Create New Collection**
3. Name: "OpenIM WebSocket Tests"
4. Add folders for organization:
   - Connection Tests
   - Message Tests
   - Compression Tests
   - Error Handling Tests

### Adding Requests to Collection

1. Create a WebSocket request
2. Click **Save** button
3. Select collection and folder
4. Name the request descriptively

**Example Collection Structure:**
```
OpenIM WebSocket Tests/
├── Connection Tests/
│   ├── Basic Connection
│   ├── Connection with Compression
│   └── Multiple Connections
├── Message Tests/
│   ├── Send Message
│   ├── Get Sequence Numbers
│   ├── Pull Messages
│   └── User Logout
└── Error Handling Tests/
    ├── Invalid Token
    ├── Missing Parameters
    └── Invalid Message Format
```

### Running Collection Tests

1. Select the collection
2. Click **Run** (three dots menu)
3. Configure run options:
   - Run sequentially or parallel
   - Delay between requests
   - Save results
4. Click **Run Collection**

### Example Collection Requests

**1. Basic Connection**
```
URL: ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=conn_001
Message: (empty - just connect)
```

**2. Send Hello Message**
```
URL: ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=msg_001
Message:
{
  "reqIdentifier": 1003,
  "sendID": "user001",
  "operationID": "msg_001",
  "msgIncr": "msg_001",
  "data": "SGVsbG8gV29ybGQh"
}
```

**3. Get Sequence**
```
URL: ws://localhost:10001/?token=test_token&sendID=user001&platformID=1&operationID=seq_001
Message:
{
  "reqIdentifier": 1001,
  "sendID": "user001",
  "operationID": "seq_001",
  "msgIncr": "seq_001",
  "data": "e30="
}
```

## Environment Variables

### Setting Up Environment Variables

1. Click **Environments** (top right gear icon)
2. Click **+ Create Environment**
3. Name: "OpenIM WebSocket"
4. Add variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `ws_host` | `localhost` | WebSocket host |
| `ws_port` | `10001` | WebSocket port |
| `user_id` | `user001` | Test user ID |
| `token` | `test_token` | Test token |
| `operation_id` | `test_op` | Operation ID |

### Using Variables in Requests

**URL:**
```
ws://{{ws_host}}:{{ws_port}}/?token={{token}}&sendID={{user_id}}&platformID=1&operationID={{operation_id}}
```

**Message:**
```json
{
  "reqIdentifier": 1003,
  "sendID": "{{user_id}}",
  "operationID": "{{operation_id}}",
  "msgIncr": "{{$timestamp}}",
  "data": "SGVsbG8gV29ybGQh"
}
```

### Dynamic Variables

Postman provides built-in dynamic variables:

- `{{$timestamp}}` - Current timestamp
- `{{$randomInt}}` - Random integer
- `{{$randomUUID}}` - Random UUID

**Example:**
```json
{
  "reqIdentifier": 1003,
  "sendID": "user001",
  "operationID": "op_{{$timestamp}}",
  "msgIncr": "msg_{{$randomInt}}",
  "data": "SGVsbG8gV29ybGQh"
}
```

## Advanced Features

### Pre-request Scripts

Add scripts to execute before sending requests:

1. Open request
2. Go to **Pre-request Script** tab
3. Add JavaScript code

**Example: Generate Base64 data**
```javascript
// Generate message
const message = "Hello from Postman!";
const base64Data = btoa(message);

// Set as environment variable
pm.environment.set("message_data", base64Data);
```

**Use in message:**
```json
{
  "reqIdentifier": 1003,
  "sendID": "user001",
  "operationID": "op_001",
  "msgIncr": "msg_001",
  "data": "{{message_data}}"
}
```

### Test Scripts

Add scripts to validate responses:

1. Open request
2. Go to **Tests** tab
3. Add JavaScript code

**Example: Validate response**
```javascript
// Parse response
const response = JSON.parse(pm.response.text());

// Validate errCode is 0 (success)
pm.test("Response has no errors", function() {
    pm.expect(response.errCode).to.eql(0);
});

// Validate reqIdentifier matches request
pm.test("Request identifier matches", function() {
    pm.expect(response.reqIdentifier).to.eql(1003);
});

// Validate data is present
pm.test("Response contains data", function() {
    pm.expect(response.data).to.exist;
});

// Log response details
console.log("Response:", response);
```

### Monitoring and History

**View Connection History:**
1. Click **History** (left sidebar)
2. Filter by WebSocket requests
3. Click on past requests to view details

**Save for Debugging:**
1. Click **Save** button
2. Add description
3. Organize in collections

## Test Scenarios

### Scenario 1: Basic Message Flow

**Steps:**
1. Connect to WebSocket
2. Send "Hello World" message
3. Verify response
4. Disconnect

**Expected:**
- Connection established
- Message sent successfully
- Response received
- No errors

### Scenario 2: Multiple Messages

**Steps:**
1. Connect to WebSocket
2. Send 5 messages sequentially
3. Verify each response
4. Check response order

**Expected:**
- All messages sent
- All responses received
- Responses in order

### Scenario 3: Compression Test

**Steps:**
1. Connect with `compression=gzip`
2. Send large message (>10KB)
3. Observe response size
4. Compare with uncompressed

**Expected:**
- Connection with compression
- Message sent
- Compressed response received
- Size reduction observed

### Scenario 4: Error Handling

**Steps:**
1. Connect without token
2. Send message without required fields
3. Send invalid message format
4. Observe error responses

**Expected:**
- Connection rejected without token
- Appropriate error messages
- Connection remains open (non-critical errors)

### Scenario 5: Heartbeat

**Steps:**
1. Connect to WebSocket
2. Wait for 30 seconds without sending
3. Observe server ping/pong

**Expected:**
- Server sends periodic pings
- Client responds with pongs
- Connection stays alive

## Message Identifiers Reference

| Identifier | Value | Description |
|------------|-------|-------------|
| `WSGetNewestSeq` | 1001 | Get latest sequence numbers |
| `WSPullMsgBySeqList` | 1002 | Pull messages by sequence list |
| `WSSendMsg` | 1003 | Send message |
| `WSSendSignalMsg` | 1004 | Send signaling message |
| `WSPullMsg` | 1005 | Pull messages |
| `WSGetConvMaxReadSeq` | 1006 | Get conversation max read sequence |
| `WsPullConvLastMessage` | 1007 | Pull last message |
| `WSPushMsg` | 2001 | Push message (server-initiated) |
| `WSKickOnlineMsg` | 2002 | Kick user offline (server-initiated) |
| `WsLogoutMsg` | 2003 | User logout |
| `WsSetBackgroundStatus` | 2004 | Set background status |
| `WsSubUserOnlineStatus` | 2005 | Subscribe to user online status |
| `WSDataError` | 3001 | Data error |

## Platform IDs

| Platform ID | Value | Description |
|-------------|-------|-------------|
| Web | 1 | Web browser |
| iOS | 2 | iOS app |
| Android | 3 | Android app |
| Windows | 4 | Windows desktop |
| macOS | 5 | macOS desktop |
| Linux | 6 | Linux desktop |
| Mini | 7 | Mini program |

## Common Issues

### Issue 1: Connection Refused

**Symptoms:**
- "Connection refused" error
- Status remains red

**Solutions:**
1. Verify msggateway is running: `mage check`
2. Check port is correct (default: 10001)
3. Check firewall settings
4. Verify URL format: `ws://localhost:10001`

### Issue 2: Authentication Failed

**Symptoms:**
- "Authentication failed" error
- Connection established but messages fail

**Solutions:**
1. Verify token is valid
2. Check token matches user ID
3. Ensure auth service is running
4. Verify token is URL-encoded

### Issue 3: Malformed JSON

**Symptoms:**
- "Invalid JSON format" error
- No response to message

**Solutions:**
1. Use JSON validator: https://jsonlint.com/
2. Verify all quotes are properly escaped
3. Check trailing commas
4. Validate message structure

### Issue 4: Base64 Decode Error

**Symptoms:**
- "Base64 decode error"
- Response has empty data field

**Solutions:**
1. Verify data is Base64 encoded
2. Use Base64 validator
3. Ensure data is not double-encoded
4. Check for URL encoding issues

### Issue 5: Connection Timeout

**Symptoms:**
- Connection takes too long
- Timeout error

**Solutions:**
1. Check network connectivity
2. Verify server load
3. Increase timeout settings
4. Check server logs for errors

## Tips and Best Practices

1. **Use Collections**: Organize related tests in collections
2. **Environment Variables**: Use variables for configurable values
3. **Pre-request Scripts**: Automate data generation
4. **Test Scripts**: Validate responses automatically
5. **Save Requests**: Save frequently used requests
6. **Documentation**: Add descriptions to requests
7. **Version Control**: Export collections for version control
8. **Monitoring**: Use history for debugging
9. **Bulk Testing**: Use collection runner for bulk tests
10. **Response Validation**: Always validate response structure

## Export and Import Collections

### Export Collection

1. Select collection
2. Click **...** (three dots)
3. Select **Export**
4. Choose format (Collection v2.1)
5. Save to file

### Import Collection

1. Click **Import** (top left)
2. Select file or drag and drop
3. Review imported collection
4. Organize in workspace

## Postman API (Optional)

For advanced users, Postman provides an API to automate testing programmatically:

```javascript
const postman = require('postman-collection');

// Create new collection
const collection = new postman.Collection({
  info: {
    name: "OpenIM WebSocket Tests"
  }
});

// Add WebSocket request
const wsRequest = new postman.Item({
  name: "Basic Connection",
  request: {
    url: "ws://localhost:10001",
    method: "GET"
  }
});

collection.items.add(wsRequest);

// Export
console.log(JSON.stringify(collection.toJSON(), null, 2));
```

## Additional Resources

- [Postman WebSocket Documentation](https://learning.postman.com/docs/sending-requests-requests/websocket/)
- [OpenIM Documentation](https://docs.openim.io/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [Base64 Encoding Guide](https://en.wikipedia.org/wiki/Base64)

---

**Document Version:** 1.0
**Last Updated:** 2026-03-05
**Postman Version Required:** v8.0+