# WebSocket Workflow - OpenIM Server

This document describes the complete WebSocket workflow in the OpenIM server project's msggateway module.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Detailed Workflow](#detailed-workflow)
- [Key Components](#key-components)
- [Connection Flow](#connection-flow)
- [Message Types](#message-types)
- [Multi-Terminal Support](#multi-terminal-support)

## Overview

The WebSocket gateway in OpenIM server handles real-time communication between clients and the backend services. It uses the Gorilla WebSocket library to manage WebSocket connections with features like:

- Authentication and authorization
- Message compression
- Multi-terminal login support
- Online status management
- Graceful connection handling
- Heartbeat/ping-pong mechanism

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Server (Port)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   wsHandler (Upgrade)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      WsServer                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         WebSocket Upgrader + Validator               │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Client Manager (UserMap)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Register/Unregister Channels               │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Client                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         WebSocketClientConn (Connection Wrapper)      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Message Handler (readMessage loop)           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Encoder (JSON/Gob) + Compressor              │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              GrpcHandler (Message Processing)                │
│  - GetSeq                                                   │
│  - SendMessage                                               │
│  - PullMessageBySeqList                                     │
│  - UserLogout                                                │
│  - etc.                                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              Backend gRPC Services
```

## Detailed Workflow

### 1. Server Initialization

**File:** `internal/msggateway/init.go` (lines 42-78)

```go
func Start(ctx context.Context, conf *Config, client discovery.SvcDiscoveryRegistry, server grpc.ServiceRegistrar) error
```

**Process:**
1. Load WebSocket server configuration (port, max connections, timeout, message size)
2. Create Redis connection for online user cache
3. Create WebSocket server with options:
   - Port (from config index)
   - Max connection count
   - Handshake timeout
   - Max message length
4. Create HubServer with the WebSocket server
5. Initialize online cache for tracking user online status
6. Start the server with `Run()`

### 2. HTTP Server Setup

**File:** `internal/msggateway/ws_server.go` (lines 171-217)

The `Run()` method:
- Creates an HTTP server listening on configured port
- Registers WebSocket handler: `http.HandleFunc("/", ws.wsHandler)`
- Starts background goroutine for graceful shutdown (15-second timeout)
- Waits for context cancellation to stop

### 3. WebSocket Connection Handler

**File:** `internal/msggateway/ws_server.go` (lines 491-549)

The `wsHandler(w http.ResponseWriter, r *http.Request)` function processes incoming connections:

#### Step-by-Step Process:

```
Client HTTP Request
    ↓
1. Connection Limit Check
    ↓
2. Parse Essential Args (userID, token, platformID)
    ↓
3. Authenticate Token (authClient.ParseToken)
    ↓
4. Validate Response (token matches userID & platformID)
    ↓
5. WebSocket Upgrade (websocket.Upgrader.Upgrade)
    ↓
6. Send Success Response (if required)
    ↓
7. Create Client (new(Client) + ResetClient)
    ↓
8. Register Client (registerChan ← client)
    ↓
9. Start Message Reading (go client.readMessage())
```

#### Key Operations:

**1. Connection Limit Check** (line 496)
```go
if ws.onlineUserConnNum.Load() >= ws.wsMaxConnNum {
    ws.handlerError(connContext, w, r, servererrs.ErrConnOverMaxNumLimit)
    return
}
```

**2. Parse Essential Args** (line 503)
Extracts userID, token, platformID from request query parameters

**3. Authentication** (line 511)
```go
resp, err := ws.authClient.ParseToken(connContext, connContext.GetToken())
```

**4. WebSocket Upgrade** (line 524)
```go
conn, err := ws.websocket.Upgrade(w, r, nil)
```

**5. Create Client** (line 544)
```go
client := new(Client)
client.ResetClient(connContext, NewWebSocketClientConn(conn, maxMessageSize, pongWait, pingInterval), ws)
```

### 4. WebSocket Client Connection Wrapper

**File:** `internal/msggateway/client_conn.go` (lines 29-47)

The `NewWebSocketClientConn()` creates a wrapper with:

- **Async Write Buffer**: Channel-based with 256 message capacity
- **Ping/Pong Handlers**: Automatic WebSocket ping/pong handling
- **Goroutines**:
  - `loopSend()`: Asynchronous message writer (line 95)
  - `doPing()`: Periodic ping sender (line 215)

#### Message Types Handled:

| Message Type | Handler | Description |
|--------------|---------|-------------|
| `BinaryMessage` | - | Application data (protobuf) |
| `TextMessage` | `onReadTextMessage()` | JSON ping/pong messages |
| `PingMessage` | `pingHandler()` | Responds with pong |
| `PongMessage` | `pongHandler()` | Acknowledges pong |
| `CloseMessage` | - | Connection closed by peer |

### 5. Client Registration

**File:** `internal/msggateway/ws_server.go` (lines 263-314)

The `registerClient(client *Client)` function:

1. **Check existing connections**: Determines if user already exists on same platform
2. **Multi-terminal login handling**: Kicks old connections based on policy (see below)
3. **Update metrics**: Increments online user and connection counters
4. **Notify other nodes**: Sends user online info to other gateway instances (if not K8s)

#### Multi-Terminal Login Policies:

| Policy | Behavior |
|--------|----------|
| `DefalutNotKick` | Allow all connections |
| `PCAndOther` | Don't kick PC, kick mobile |
| `AllLoginButSameTermKick` | Kick same platform, different token |
| `AllLoginButSameClassKick` | Kick same class (mobile/desktop) |

### 6. Message Reading Loop

**File:** `internal/msggateway/client.go` (lines 114-144)

```go
func (c *Client) readMessage() {
    defer func() {
        if r := recover(); r != nil {
            c.closedErr = ErrPanic
            log.ZPanic(c.ctx, "socket have panic err:", errs.ErrPanic(r))
        }
        c.close()
    }()

    for {
        message, returnErr := c.conn.ReadMessage()
        if returnErr != nil {
            log.ZWarn(c.ctx, "readMessage", returnErr)
            c.closedErr = returnErr
            return
        }

        if c.closed.Load() {
            c.closedErr = ErrConnClosed
            return
        }

        parseDataErr := c.handleMessage(message)
        if parseDataErr != nil {
            c.closedErr = parseDataErr
            return
        }
    }
}
```

### 7. Message Processing

**File:** `internal/msggateway/client.go` (lines 147-214)

The `handleMessage()` function processes each incoming message:

```
Raw Message
    ↓
1. Decompression (if IsCompress)
    ↓
2. Decoding (JSON/Gob Encoder)
    ↓
3. Validation (validator)
    ↓
4. Route by ReqIdentifier
    ↓
5. Call Handler (GrpcHandler)
    ↓
6. Marshal Response
    ↓
7. Encode & Send (with compression if needed)
```

#### Message Handlers:

| ReqIdentifier | Handler | Description |
|---------------|---------|-------------|
| `WSGetNewestSeq` | `GetSeq()` | Get latest message sequence numbers |
| `WSSendMsg` | `SendMessage()` | Send new message |
| `WSSendSignalMsg` | `SendSignalMessage()` | Send signaling message |
| `WSPullMsgBySeqList` | `PullMessageBySeqList()` | Pull messages by sequence list |
| `WSPullMsg` | `GetSeqMessage()` | Get messages by sequence |
| `WSGetConvMaxReadSeq` | `GetConversationsHasReadAndMaxSeq()` | Get conversation read/max seq |
| `WsPullConvLastMessage` | `GetLastMessage()` | Get last message in conversation |
| `WsLogoutMsg` | `UserLogout()` | User logout |
| `WsSetBackgroundStatus` | `setAppBackgroundStatus()` | Set app background status |
| `WsSubUserOnlineStatus` | `SubUserOnlineStatus()` | Subscribe to user online status |

### 8. Message Handlers (gRPC Backend)

**File:** `internal/msggateway/message_handler.go`

Each handler:

1. **Unmarshal**: Parse protobuf data from request
2. **Validate**: Use validator to check data integrity
3. **gRPC Call**: Call backend service (MsgClient or PushMsgServiceClient)
4. **Marshal**: Encode response back to protobuf
5. **Return**: Send to client

Example (SendMessage):
```go
func (g *GrpcHandler) SendMessage(ctx context.Context, data *Req) ([]byte, error) {
    var msgData sdkws.MsgData
    if err := proto.Unmarshal(data.Data, &msgData); err != nil {
        return nil, errs.WrapMsg(err, "SendMessage: error unmarshaling message data")
    }

    if err := g.validate.Struct(&msgData); err != nil {
        return nil, errs.WrapMsg(err, "SendMessage: message data validation failed")
    }

    req := msg.SendMsgReq{MsgData: &msgData}
    resp, err := g.msgClient.MsgClient.SendMsg(ctx, &req)
    if err != nil {
        return nil, err
    }

    c, err := proto.Marshal(resp)
    if err != nil {
        return nil, errs.WrapMsg(err, "SendMessage: error marshaling response")
    }

    return c, nil
}
```

### 9. Push Messages

**File:** `internal/msggateway/hub_server.go` (lines 135-169)

The `pushToUser()` function handles server-initiated pushes:

```go
func (s *Server) pushToUser(ctx context.Context, userID string, msgData *sdkws.MsgData) *msggateway.SingleMsgToUserResults {
    clients, ok := s.LongConnServer.GetUserAllCons(userID)
    if !ok {
        return &msggateway.SingleMsgToUserResults{UserID: userID}
    }

    result := &msggateway.SingleMsgToUserResults{
        UserID: userID,
        Resp:   make([]*msggateway.SingleMsgToUserPlatform, 0, len(clients)),
    }

    for _, client := range clients {
        userPlatform := &msggateway.SingleMsgToUserPlatform{
            RecvPlatFormID: int32(client.PlatformID),
        }

        // Check if iOS and background
        if client.IsBackground && client.PlatformID == constant.IOSPlatformID {
            userPlatform.ResultCode = int64(servererrs.ErrIOSBackgroundPushErr.Code())
            result.Resp = append(result.Resp, userPlatform)
            continue
        }

        // Push message to client
        if err := client.PushMessage(ctx, msgData); err != nil {
            log.ZWarn(ctx, "online push msg failed", err)
            userPlatform.ResultCode = int64(servererrs.ErrPushMsgErr.Code())
        } else if _, ok := s.pushTerminal[client.PlatformID]; ok {
            result.OnlinePush = true
        }

        result.Resp = append(result.Resp, userPlatform)
    }

    return result
}
```

**Batch Push** (lines 171-220):
- Uses memory queue for concurrent processing
- Processes up to 512 concurrent pushes
- Collects results in channel
- Handles context cancellation

### 10. Client Unregistration

**File:** `internal/msggateway/ws_server.go` (lines 439-453)

```go
func (ws *WsServer) unregisterClient(client *Client) {
    defer ws.clientPool.Put(client)
    isDeleteUser := ws.clients.DeleteClients(client.UserID, []*Client{client})
    if isDeleteUser {
        ws.onlineUserNum.Add(-1)
        prommetrics.OnlineUserGauge.Dec()
    }
    ws.onlineUserConnNum.Add(-1)
    ws.subscription.DelClient(client)
    log.ZDebug(client.ctx, "user offline", "close reason", client.closedErr)
}
```

### 11. Connection Lifecycle Management

#### Ping/Pong Heartbeat

**File:** `internal/msggateway/client_conn.go` (lines 198-229)

- **Server-side ping**: Periodic ping messages (if configured)
- **Ping handler**: Responds to client pings with pong
- **Pong handler**: Acknowledges received pongs
- **Read timeout**: Configurable timeout for connection health

#### Read/Write Flow

**Reading:**
- Continuous loop in `readMessage()`
- Sets read deadline before each read
- Handles different message types
- On error: closes connection and unregisters

**Writing:**
- Asynchronous via buffered channel (256 messages)
- Separate goroutine `loopSend()` handles actual writes
- If buffer full: closes connection with error
- Supports compression before sending

#### Graceful Shutdown

1. Context cancellation triggers shutdown
2. HTTP server shutdown initiated
3. 15-second timeout for graceful stop
4. All connections properly closed

## Key Components

| File | Lines | Description |
|------|-------|-------------|
| `init.go` | 42-78 | Server startup and initialization |
| `ws_server.go` | 137-169 | WebSocket server configuration |
| `ws_server.go` | 171-217 | HTTP server and graceful shutdown |
| `ws_server.go` | 491-549 | WebSocket connection handler |
| `ws_server.go` | 263-314 | Client registration logic |
| `client_conn.go` | 29-47 | WebSocket connection wrapper |
| `client_conn.go` | 95-133 | Async message writer |
| `client_conn.go` | 140-196 | Message reader with type handling |
| `client_conn.go` | 198-229 | Ping/Pong handlers |
| `client.go` | 85-111 | Client initialization |
| `client.go` | 114-144 | Message reading loop |
| `client.go` | 147-214 | Message processing and routing |
| `client.go` | 227-237 | Client cleanup |
| `client.go` | 263-283 | Server-initiated message push |
| `client.go` | 285-293 | Kick client message |
| `message_handler.go` | 130-281 | gRPC message handlers |

## Connection Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Request                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP GET /ws?token=xxx&userID=xxx
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              wsHandler (ws_server.go:491)                   │
│  1. Check connection limit                                  │
│  2. Parse userID, token, platformID                        │
│  3. Authenticate token via authClient                       │
│  4. Validate response                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              WebSocket Upgrade (line 524)                   │
│         websocket.Upgrader.Upgrade(w, r, nil)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Create Client + WebSocketClientConn (line 544)      │
│  - ResetClient() with context and connection                │
│  - Set encoder (JSON/Gob) based on SDK type                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Register Client (line 547)                     │
│         ws.registerChan ← client                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│          registerClient (ws_server.go:263)                  │
│  1. Check existing connections                               │
│  2. Handle multi-terminal login (kick old if needed)        │
│  3. Update online metrics                                    │
│  4. Notify other gateway nodes                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         Start readMessage() goroutine (line 548)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        Message Loop (client.go:114-144)                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  for {                                                │   │
│  │    message ← conn.ReadMessage()                      │   │
│  │    handleMessage(message)                            │   │
│  │  }                                                    │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│        handleMessage (client.go:147-214)                    │
│  1. Decompress (if needed)                                  │
│  2. Decode (JSON/Gob)                                       │
│  3. Validate request                                        │
│  4. Route by ReqIdentifier                                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│          GrpcHandler (message_handler.go)                    │
│  1. Unmarshal protobuf data                                 │
│  2. Validate with validator                                 │
│  3. Call backend gRPC service                               │
│  4. Marshal response                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              replyMessage (client.go:239)                    │
│  1. Encode response (JSON/Gob)                              │
│  2. Compress (if needed)                                   │
│  3. Write to connection                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Connection Loop                                │
│        Continue until error or client close                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼ On Error
┌─────────────────────────────────────────────────────────────┐
│              Client Cleanup                                 │
│  1. close() - close connection                             │
│  2. UnRegister - remove from map                           │
│  3. Update metrics                                          │
│  4. Return client to pool                                   │
└─────────────────────────────────────────────────────────────┘
```

## Message Types

### Request Structure

```go
type Req struct {
    ReqIdentifier int32  `json:"reqIdentifier"`  // Message type
    Token         string `json:"token"`          // Auth token
    SendID        string `json:"sendID"`         // Sender user ID
    OperationID   string `json:"operationID"`    // Operation ID for tracing
    MsgIncr       string `json:"msgIncr"`       // Message increment ID
    Data          []byte `json:"data"`          // Protobuf encoded data
}
```

### Response Structure

```go
type Resp struct {
    ReqIdentifier int32  `json:"reqIdentifier"`  // Message type (matches request)
    MsgIncr       string `json:"msgIncr"`        // Message increment ID
    OperationID   string `json:"operationID"`    // Operation ID for tracing
    ErrCode       int    `json:"errCode"`        // Error code
    ErrMsg        string `json:"errMsg"`         // Error message
    Data          []byte `json:"data"`          // Protobuf encoded response data
}
```

### Request Identifiers

| Value | Constant | Description |
|-------|----------|-------------|
| 1 | `WSGetNewestSeq` | Get latest sequence number |
| 2 | `WSSendMsg` | Send message |
| 3 | `WSSendSignalMsg` | Send signaling message |
| 4 | `WSPullMsgBySeqList` | Pull messages by sequence list |
| 5 | `WSPullMsg` | Pull messages |
| 6 | `WSGetConvMaxReadSeq` | Get conversation max read sequence |
| 7 | `WsPullConvLastMessage` | Pull last message |
| 8 | `WsLogoutMsg` | Logout |
| 9 | `WsSetBackgroundStatus` | Set background status |
| 10 | `WsSubUserOnlineStatus` | Subscribe to user online status |
| 1001 | `WSPushMsg` | Push message to client (server-initiated) |
| 1002 | `WSKickOnlineMsg` | Kick user offline (server-initiated) |
| 1003 | `WsSubUserOnlineStatus` | User online status push |

## Multi-Terminal Support

The gateway supports multiple login policies defined in `ws.msgGatewayConfig.Share.MultiLogin.Policy`:

### 1. Default: No Kick (`DefalutNotKick`)
- Allow all connections from any platform
- No existing connections are kicked

### 2. PC Protected (`PCAndOther`)
- Don't kick PC (desktop) connections
- Kick mobile/web connections from same user

### 3. Same Terminal Kick (`AllLoginButSameTermKick`)
- Kick connections on same platform (e.g., mobile)
- Only if token is different (reconnects allowed)
- Invalidate old tokens via auth service

### 4. Same Class Kick (`AllLoginButSameClassKick`)
- Kick connections in same class (mobile or desktop)
- Only if token is different

### Reconnection Handling

When a user reconnects (e.g., from instance A to instance B):
1. Check if token matches existing connection
2. If same token: don't kick (handle reconnection)
3. If different token: kick old connection based on policy

```go
func (ws *WsServer) checkSameTokenFunc(oldClients []*Client) []*Client {
    var clientsNeedToKick []*Client

    for _, c := range oldClients {
        if c.token == newClient.token {
            log.ZDebug(newClient.ctx, "token is same, not kick")
            continue
        }
        clientsNeedToKick = append(clientsNeedToKick, c)
    }

    return clientsNeedToKick
}
```

## Configuration

### WebSocket Server Configuration

```go
type Config struct {
    MsgGateway     config.MsgGateway
    Share          config.Share
    RedisConfig    config.Redis
    WebhooksConfig config.Webhooks
    Discovery      config.Discovery
    Index          config.Index
}
```

### Key Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `LongConnSvr.Ports` | WebSocket port(s) | Configured per instance |
| `LongConnSvr.WebsocketMaxConnNum` | Max concurrent connections | Configured in config |
| `LongConnSvr.WebsocketTimeout` | Handshake timeout (seconds) | Configured in config |
| `LongConnSvr.WebsocketMaxMsgLen` | Max message size | Configured in config |

### Ping/Pong Configuration

- `maxMessageSize`: Maximum message size (1MB)
- `pongWait`: Read timeout for waiting for pong
- `pingPeriod`: Ping interval (web platform only)
- `pingInterval`: Server-initiated ping interval (if configured)

## Error Handling

### Connection Errors

| Error | Cause | Action |
|-------|-------|--------|
| `ErrConnOverMaxNumLimit` | Connection limit exceeded | Return HTTP error |
| `ErrTokenInvalid` | Token validation failed | Return HTTP error |
| Connection limit | Buffer full | Close connection |
| Read timeout | No data received | Close connection |

### Message Errors

| Error | Cause | Action |
|-------|-------|--------|
| `ErrConnClosed` | Connection already closed | Stop processing |
| `ErrNotSupportMessageProtocol` | Unknown protocol | Stop processing |
| `ErrClientClosed` | Client closed connection | Stop processing |
| Panic errors | Runtime panic | Log and close |

## Metrics

The gateway tracks and reports metrics:

- `OnlineUserGauge`: Number of unique online users
- `onlineUserNum`: Internal counter for online users
- `onlineUserConnNum`: Internal counter for connections

Metrics are updated during:
- Client registration (increment)
- Client unregistration (decrement)

## Security Features

1. **Token Authentication**: Every connection must provide valid token
2. **Origin Validation**: Configurable `CheckOrigin` function
3. **Rate Limiting**: Connection limit prevents resource exhaustion
4. **Message Size Limit**: Prevents large message attacks
5. **Read Timeout**: Prevents hung connections
6. **Token Invalidation**: Old tokens invalidated on kick

## Best Practices

1. **Use async writes**: The `loopSend()` goroutine prevents blocking
2. **Pool reuse**: Client objects are reused via `sync.Pool`
3. **Graceful shutdown**: 15-second timeout for cleanup
4. **Context propagation**: OperationID traces requests through system
5. **Compression**: Enable compression for large payloads
6. **Error logging**: All errors logged with context

## Performance Considerations

1. **Buffer sizes**: Write buffer (256 messages) can be tuned
2. **Connection pooling**: Clients returned to pool for reuse
3. **Concurrent processing**: Memory queue for batch pushes (512 workers)
4. **Memory pools**: Request objects pooled to reduce GC pressure
5. **Async operations**: Registration, notification, and other async tasks

## Dependencies

- `github.com/gorilla/websocket`: WebSocket library
- `google.golang.org/protobuf`: Protocol buffers
- `github.com/go-playground/validator/v10`: Request validation
- `github.com/openimsdk/tools`: Common utilities

---

**Document Version:** 1.0
**Last Updated:** 2026-03-05
**OpenIM Server Version:** v3
