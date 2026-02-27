# RPC Services - Complete Guide

## Table of Contents
- [What is RPC?](#what-is-rpc)
- [How RPC Works](#how-rpc-works)
- [Common RPC Frameworks](#common-rpc-frameworks)
- [RPC vs REST](#rpc-vs-rest)
- [When to Use RPC](#when-to-use-rpc)
- [Practical Examples](#practical-examples)
- [Best Practices](#best-practices)

---

## What is RPC?

**RPC (Remote Procedure Call)** is a protocol that allows a program to execute a procedure or function on another computer or server without the developer needing to explicitly code the details of the network interaction.

### The Core Concept

RPC makes calling a function on a remote server **feel exactly like calling a local function** in your own code. It abstracts away the complexity of network communication, serialization, and transport protocols.

### Code Comparison

**Without RPC (Manual HTTP Requests):**
```go
// Client must handle all the details
url := "http://server.com/api/user/123"
response, err := http.Get(url)
if err != nil {
    return err
}
defer response.Body.Close()

var user User
err = json.NewDecoder(response.Body).Decode(&user)
if err != nil {
    return err
}

return user
```

**With RPC (Feels Local):**
```go
// Looks like a local function call
user, err := userService.GetUser(123)
// All networking, serialization, error handling is handled automatically
```

---

## How RPC Works

### The Request-Response Flow

```
┌─────────┐       1. Call Function        ┌──────────┐
│ Client  │ ──────────────────────────► │   Stub    │
└─────────┘                             └──────────┘
     ▲                                          │
     │                                          │ 2. Serialize
     │                                          ▼
     │                                   ┌──────────┐
     │                                   │ Transport │
     │                                   └──────────┘
     │                                          │
     │                    3. Send over Network  │
     │                                          ▼
     │◄─────────────────────────────────────────────────────►
     │                    ┌─────────────────────────────────┐
     │                    │         Network                 │
     │                    └─────────────────────────────────┘
     │                                          │
     │                                          ▼
     │                                   ┌──────────┐
     │                                   │  Server  │
     │                                   └──────────┘
     │                                          │
     │                                   4. Deserialize
     │                                          │
     │                                          ▼
     │                                   ┌──────────┐
     │                                   │ Function │
     │                                   └──────────┘
     │                                          │
     │                    5. Execute            │
     │                                          │
     │                                          ▼
     │                                   ┌──────────┐
     │                                   │  Server  │
     │                                   └──────────┘
     │                                          │
     │                    6. Serialize Response  │
     │                                          │
     │                                          ▼
     │                    ┌─────────────────────────────────┐
     └─────────────────── │         Network                 │
                          └─────────────────────────────────┘
                                            │
                                            │ 7. Send Response
                                            ▼
                                   ┌──────────┐
                                   │  Client  │
                                   └──────────┘
                                            │
                                     8. Deserialize
                                            │
                                            ▼
                                   ┌──────────┐
                                   │  Return  │
                                   └──────────┘
```

### Step-by-Step Breakdown

1. **Client Call**: Client application calls a remote function (looks like a local call)
2. **Stub/Client Proxy**: Packs the request parameters (serialization)
3. **Transport Layer**: Sends the serialized data over the network
4. **Server Receives**: Server unpacks and deserializes the request
5. **Function Execution**: Server executes the actual function with the provided parameters
6. **Response Packing**: Server packs the return value (serialization)
7. **Transport Return**: Sends the response back over the network
8. **Client Return**: Client receives, deserializes, and returns the result

---

## Common RPC Frameworks

### gRPC (Google Remote Procedure Call)

**Language Support:** Go, Java, Python, C++, C#, Ruby, Node.js, and more

**Protocol:** HTTP/2 + Protocol Buffers (binary)

**Best For:**
- High-performance microservices
- Low-latency systems
- Strongly typed interfaces
- Real-time streaming

**Key Features:**
- Binary serialization (Protobuf) - faster and smaller than JSON
- Built on HTTP/2 - supports streaming and multiplexing
- Automatic code generation from .proto files
- Bi-directional streaming
- Built-in authentication and load balancing

### JSON-RPC

**Language Support:** Language-agnostic

**Protocol:** JSON over HTTP or WebSocket

**Best For:**
- Simple client-server communication
- Web applications
- Quick prototyping
- REST-like behavior but structured

**Key Features:**
- Human-readable format (JSON)
- Lightweight and simple
- Easy to debug
- No code generation required

**Example Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "getUser",
  "params": { "id": 123 },
  "id": 1
}
```

**Example Response:**
```json
{
  "jsonrpc": "2.0",
  "result": { "id": 123, "name": "John" },
  "id": 1
}
```

### XML-RPC

**Language Support:** Multi-language

**Protocol:** XML over HTTP

**Best For:**
- Legacy systems
- Cross-platform integration
- Systems requiring XML format

**Key Features:**
- Uses XML format
- Very simple specification
- Widely supported in older systems

### Apache Thrift

**Language Support:** C++, Java, Python, PHP, Ruby, Go, and more

**Protocol:** Binary (custom)

**Best For:**
- Large-scale distributed systems
- High-performance requirements
- Polyglot environments

**Key Features:**
- Multiple serialization formats
- Asynchronous processing
- Lightweight
- Facebook-created, battle-tested

### Dubbo

**Language Support:** Primarily Java

**Protocol:** Multiple (Hessian, HTTP, REST, etc.)

**Best For:**
- Large-scale Java microservices
- Enterprise applications
- High-traffic systems (Alibaba-scale)

**Key Features:**
- Service registry and discovery
- Load balancing
- Failover mechanisms
- Multiple protocol support

### Framework Comparison

| Framework | Performance | Complexity | Type Safety | Learning Curve | Ecosystem |
|-----------|-------------|------------|-------------|----------------|-----------|
| gRPC | ⭐⭐⭐⭐⭐ | Medium | High | Medium | Excellent |
| JSON-RPC | ⭐⭐⭐ | Low | Low | Easy | Good |
| XML-RPC | ⭐⭐ | Low | Low | Easy | Mature |
| Thrift | ⭐⭐⭐⭐⭐ | High | High | Hard | Good |
| Dubbo | ⭐⭐⭐⭐ | High | High | Hard | Java-focused |

---

## RPC vs REST

### Conceptual Differences

| Aspect | RPC | REST |
|--------|-----|------|
| **Focus** | Actions (verbs) | Resources (nouns) |
| **Philosophy** | "Do this" | "Get this resource" |
| **URL Structure** | `/rpc/getUser` | `/users/123` |
| **HTTP Methods** | Usually POST only | GET, POST, PUT, DELETE |
| **State** | Can be stateful | Stateless |
| **Interface** | Explicit contract | Hypermedia-driven |

### Example Comparison

**RPC Style:**
```
POST /rpc
{
  "method": "createUser",
  "params": { "name": "John", "email": "john@example.com" }
}

POST /rpc
{
  "method": "updateUser",
  "params": { "id": 123, "name": "John Doe" }
}

POST /rpc
{
  "method": "deleteUser",
  "params": { "id": 123 }
}
```

**REST Style:**
```
POST /users
{
  "name": "John",
  "email": "john@example.com"
}

PUT /users/123
{
  "name": "John Doe"
}

DELETE /users/123
```

### When to Choose RPC

✅ **Choose RPC when:**
- Building internal microservices
- Performance is critical
- Strong typing is required
- Real-time bidirectional communication needed
- Complex business operations (not simple CRUD)
- Team prefers explicit contracts

### When to Choose REST

✅ **Choose REST when:**
- Building public APIs
- Simple CRUD operations
- Caching is important
- Wide variety of clients (web, mobile, third-party)
- Stateless operations preferred
- leveraging existing HTTP infrastructure

---

## When to Use RPC

### Ideal Use Cases

#### 1. Microservices Architecture
```
┌─────────────┐     RPC      ┌──────────────┐
│   Gateway   │◄────────────►│  Auth Service│
└─────────────┘              └──────────────┘
      │                              │
      │ RPC                          │ RPC
      ▼                              ▼
┌─────────────┐              ┌──────────────┐
│  Msg Service│◄────────────►│  Push Service│
└─────────────┘              └──────────────┘
```

**Why RPC?**
- Low latency between services
- Type-safe interfaces prevent bugs
- Efficient binary serialization
- Service discovery and load balancing

#### 2. High-Performance Systems
- Real-time trading platforms
- Gaming backends
- Streaming services
- Analytics systems

#### 3. Internal APIs
- Backend-to-backend communication
- Service mesh implementations
- Distributed databases

#### 4. Real-Time Streaming
```go
// gRPC streaming example
stream ChatMessages(ChatRequest) returns (stream ChatMessage)
```

### Anti-Patterns (When NOT to Use RPC)

❌ **Avoid RPC when:**
- Building public-facing APIs
- Simple CRUD operations
- Diverse, unknown clients
- Bandwidth is not a concern
- Team lacks RPC experience
- Debugging/visibility is priority

---

## Practical Examples

### gRPC Complete Example

#### 1. Define the Service (user.proto)

```protobuf
syntax = "proto3";

package user;

// The user service definition
service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(DeleteUserRequest) returns (DeleteUserResponse);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
}

// Request messages
message GetUserRequest {
  int32 id = 1;
}

message CreateUserRequest {
  string name = 1;
  string email = 2;
  string password = 3;
}

message UpdateUserRequest {
  int32 id = 1;
  string name = 2;
  string email = 3;
}

message DeleteUserRequest {
  int32 id = 1;
}

message ListUsersRequest {
  int32 page = 1;
  int32 limit = 2;
}

// Response messages
message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
  int64 created_at = 4;
  int64 updated_at = 5;
}

message DeleteUserResponse {
  bool success = 1;
  string message = 2;
}

message ListUsersResponse {
  repeated User users = 1;
  int32 total = 2;
}
```

#### 2. Generate Code

```bash
# Generate Go code
protoc --go_out=. --go_opt=paths=source_relative \
       --go-grpc_out=. --go-grpc_opt=paths=source_relative \
       user.proto

# Output: user.pb.go and user_grpc.pb.go
```

#### 3. Implement the Server (Go)

```go
package main

import (
    "context"
    "log"
    "net"
    "time"

    "google.golang.org/grpc"
    pb "path/to/protobuf"
)

// Server implements the UserService
type Server struct {
    pb.UnimplementedUserServiceServer
}

// GetUser retrieves a user by ID
func (s *Server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    // In real implementation, query database here
    log.Printf("Received: GetUser with id=%d", req.Id)

    return &pb.User{
        Id:        req.Id,
        Name:      "John Doe",
        Email:     "john@example.com",
        CreatedAt: time.Now().Unix(),
        UpdatedAt: time.Now().Unix(),
    }, nil
}

// CreateUser creates a new user
func (s *Server) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.User, error) {
    log.Printf("Received: CreateUser name=%s email=%s", req.Name, req.Email)

    // Simulate database insertion
    newUserId := 123 // In reality, this would be generated by the database

    return &pb.User{
        Id:        newUserId,
        Name:      req.Name,
        Email:     req.Email,
        CreatedAt: time.Now().Unix(),
        UpdatedAt: time.Now().Unix(),
    }, nil
}

// UpdateUser updates an existing user
func (s *Server) UpdateUser(ctx context.Context, req *pb.UpdateUserRequest) (*pb.User, error) {
    log.Printf("Received: UpdateUser id=%d", req.Id)

    // Simulate database update
    return &pb.User{
        Id:        req.Id,
        Name:      req.Name,
        Email:     req.Email,
        CreatedAt: time.Now().Add(-24 * time.Hour).Unix(),
        UpdatedAt: time.Now().Unix(),
    }, nil
}

// DeleteUser deletes a user
func (s *Server) DeleteUser(ctx context.Context, req *pb.DeleteUserRequest) (*pb.DeleteUserResponse, error) {
    log.Printf("Received: DeleteUser id=%d", req.Id)

    // Simulate database deletion
    return &pb.DeleteUserResponse{
        Success: true,
        Message: "User deleted successfully",
    }, nil
}

// ListUsers returns a paginated list of users
func (s *Server) ListUsers(ctx context.Context, req *pb.ListUsersRequest) (*pb.ListUsersResponse, error) {
    log.Printf("Received: ListUsers page=%d limit=%d", req.Page, req.Limit)

    // Simulate database query
    users := []*pb.User{
        {
            Id:        1,
            Name:      "Alice",
            Email:     "alice@example.com",
            CreatedAt: time.Now().Unix(),
            UpdatedAt: time.Now().Unix(),
        },
        {
            Id:        2,
            Name:      "Bob",
            Email:     "bob@example.com",
            CreatedAt: time.Now().Unix(),
            UpdatedAt: time.Now().Unix(),
        },
    }

    return &pb.ListUsersResponse{
        Users: users,
        Total: 2,
    }, nil
}

func main() {
    // Create a listener on TCP port 50051
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("Failed to listen: %v", err)
    }

    // Create a gRPC server
    s := grpc.NewServer()

    // Register the UserService server
    pb.RegisterUserServiceServer(s, &Server{})

    log.Printf("Server listening at %v", lis.Addr())

    // Start serving
    if err := s.Serve(lis); err != nil {
        log.Fatalf("Failed to serve: %v", err)
    }
}
```

#### 4. Implement the Client (Go)

```go
package main

import (
    "context"
    "log"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    pb "path/to/protobuf"
)

func main() {
    // Establish connection to server
    conn, err := grpc.Dial("localhost:50051",
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithBlock(),
    )
    if err != nil {
        log.Fatalf("Failed to connect: %v", err)
    }
    defer conn.Close()

    // Create client
    client := pb.NewUserServiceClient(conn)

    // Set timeout
    ctx, cancel := context.WithTimeout(context.Background(), time.Second*5)
    defer cancel()

    // Call GetUser
    log.Println("=== Calling GetUser ===")
    user, err := client.GetUser(ctx, &pb.GetUserRequest{Id: 1})
    if err != nil {
        log.Fatalf("GetUser failed: %v", err)
    }
    log.Printf("User: ID=%d, Name=%s, Email=%s\n", user.Id, user.Name, user.Email)

    // Call CreateUser
    log.Println("\n=== Calling CreateUser ===")
    newUser, err := client.CreateUser(ctx, &pb.CreateUserRequest{
        Name:     "Jane Doe",
        Email:    "jane@example.com",
        Password: "secret123",
    })
    if err != nil {
        log.Fatalf("CreateUser failed: %v", err)
    }
    log.Printf("Created user: ID=%d, Name=%s\n", newUser.Id, newUser.Name)

    // Call UpdateUser
    log.Println("\n=== Calling UpdateUser ===")
    updatedUser, err := client.UpdateUser(ctx, &pb.UpdateUserRequest{
        Id:    1,
        Name:  "Alice Updated",
        Email: "alice.updated@example.com",
    })
    if err != nil {
        log.Fatalf("UpdateUser failed: %v", err)
    }
    log.Printf("Updated user: Name=%s, Email=%s\n", updatedUser.Name, updatedUser.Email)

    // Call ListUsers
    log.Println("\n=== Calling ListUsers ===")
    list, err := client.ListUsers(ctx, &pb.ListUsersRequest{
        Page:  1,
        Limit: 10,
    })
    if err != nil {
        log.Fatalf("ListUsers failed: %v", err)
    }
    log.Printf("Total users: %d\n", list.Total)
    for _, u := range list.Users {
        log.Printf("  - %s (%s)\n", u.Name, u.Email)
    }

    // Call DeleteUser
    log.Println("\n=== Calling DeleteUser ===")
    delResp, err := client.DeleteUser(ctx, &pb.DeleteUserRequest{Id: 999})
    if err != nil {
        log.Fatalf("DeleteUser failed: %v", err)
    }
    log.Printf("Delete success: %v, Message: %s\n", delResp.Success, delResp.Message)
}
```

### JSON-RPC Example

#### Server (Node.js)

```javascript
const jsonrpc = require('json-rpc-2.0');

const server = new jsonrpc.JSONRPCServer();

// Register methods
server.addMethod('getUser', async ({ id }) => {
    return {
        id,
        name: 'John Doe',
        email: 'john@example.com'
    };
});

server.addMethod('createUser', async ({ name, email, password }) => {
    // Simulate database insert
    const newUser = {
        id: Math.floor(Math.random() * 1000),
        name,
        email
    };
    return newUser;
});

// Express server setup
const express = require('express');
const app = express();

app.use(express.json());

app.post('/rpc', (req, res) => {
    const request = req.body;

    server.receive(request).then(response => {
        res.json(response);
    });
});

app.listen(3000, () => {
    console.log('JSON-RPC server running on port 3000');
});
```

#### Client (JavaScript)

```javascript
async function callJSONRPC(method, params) {
    const response = await fetch('http://localhost:3000/rpc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: Date.now()
        })
    });

    return response.json();
}

// Usage
(async () => {
    // Get user
    const user = await callJSONRPC('getUser', { id: 123 });
    console.log('User:', user.result);

    // Create user
    const newUser = await callJSONRPC('createUser', {
        name: 'Jane Doe',
        email: 'jane@example.com',
        password: 'secret'
    });
    console.log('New user:', newUser.result);
})();
```

---

## Best Practices

### 1. Service Design

#### Do's ✅
```protobuf
// Good: Clear, descriptive names
service UserService {
  rpc GetUserById(GetUserRequest) returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
}

// Good: Use nouns for resources
message User {
  int32 id = 1;
  string name = 2;
}
```

#### Don'ts ❌
```protobuf
// Bad: Vague naming
service Service {
  rpc Get(Request) returns (Response);
  rpc Do(Args) returns (Result);
}

// Bad: Abbreviations
message Usr {
  int32 uid = 1;
  string nm = 2;
}
```

### 2. Error Handling

```go
// Use proper status codes
import "google.golang.org/grpc/codes"
import "google.golang.org/grpc/status"

func (s *Server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    if req.Id <= 0 {
        return nil, status.Error(codes.InvalidArgument, "Invalid user ID")
    }

    user, err := s.db.GetUser(req.Id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return nil, status.Error(codes.NotFound, "User not found")
        }
        return nil, status.Error(codes.Internal, "Internal error")
    }

    return user, nil
}
```

### 3. Versioning

```protobuf
// Version your services
package user.v1;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
}

// Future version
package user.v2;

service UserService {
  rpc GetUser(GetUserRequest) returns (User);
  rpc GetUserWithEmail(GetUserByEmailRequest) returns (User);
}
```

### 4. Timeout Management

```go
// Always use timeouts with context
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

response, err := client.SomeMethod(ctx, request)
```

### 5. Interceptors (Middleware)

```go
// Logging interceptor
func loggingInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    start := time.Now()
    log.Printf("Method: %s, Request: %v", info.FullMethod, req)

    resp, err := handler(ctx, req)

    log.Printf("Method: %s, Duration: %v, Error: %v",
        info.FullMethod, time.Since(start), err)

    return resp, err
}

// Register interceptor
s := grpc.NewServer(
    grpc.UnaryInterceptor(loggingInterceptor),
)
```

### 6. Testing

```go
// Table-driven tests
tests := []struct {
    name    string
    request *pb.GetUserRequest
    want    *pb.User
    wantErr bool
}{
    {
        name: "valid user",
        request: &pb.GetUserRequest{Id: 1},
        want: &pb.User{Id: 1, Name: "Alice"},
        wantErr: false,
    },
    {
        name: "invalid id",
        request: &pb.GetUserRequest{Id: -1},
        wantErr: true,
    },
}

for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        got, err := server.GetUser(context.Background(), tt.request)
        if (err != nil) != tt.wantErr {
            t.Errorf("error = %v, wantErr %v", err, tt.wantErr)
            return
        }
        if !reflect.DeepEqual(got, tt.want) {
            t.Errorf("got = %v, want %v", got, tt.want)
        }
    })
}
```

---

## Performance Considerations

### Serialization Comparison

| Format | Size | Speed | Human Readable |
|--------|------|-------|----------------|
| JSON | Large | Medium | Yes |
| XML | Very Large | Slow | Yes |
| Protobuf | Small | Fast | No |
| MessagePack | Small | Fast | No |

### When Performance Matters

```go
// Protobuf is ~3-5x faster than JSON
// Protobuf payloads are ~50-70% smaller than JSON

// For high-throughput systems:
// JSON: ~50K requests/sec
// gRPC/Protobuf: ~200K+ requests/sec
```

---

## Monitoring & Debugging

### gRPC Reflection

```go
// Enable reflection for debugging
import "google.golang.org/grpc/reflection"

reflection.Register(s)

// Use grpcurl to inspect services
// grpcurl -plaintext localhost:50051 list
// grpcurl -plaintext localhost:50051 describe UserService
```

### Logging Structured Data

```go
log.WithFields(log.Fields{
    "method": "GetUser",
    "user_id": req.Id,
    "duration_ms": duration.Milliseconds(),
    "success": err == nil,
}).Info("RPC call completed")
```

---

## Security Best Practices

### 1. TLS Encryption

```go
// Always use TLS in production
creds, err := credentials.NewServerTLSFromFile("server.crt", "server.key")
s := grpc.NewServer(grpc.Creds(creds))
```

### 2. Authentication

```go
// Per-RPC authentication
type contextKey string

func (s *Server) authenticate(ctx context.Context) (string, error) {
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return "", status.Error(codes.Unauthenticated, "missing metadata")
    }

    token := md["authorization"]
    if len(token) == 0 {
        return "", status.Error(codes.Unauthenticated, "missing token")
    }

    // Validate token
    userID, err := validateToken(token[0])
    if err != nil {
        return "", status.Error(codes.Unauthenticated, "invalid token")
    }

    return userID, nil
}
```

### 3. Input Validation

```go
func validateRequest(req *pb.CreateUserRequest) error {
    if req.Name == "" {
        return status.Error(codes.InvalidArgument, "name is required")
    }
    if !isValidEmail(req.Email) {
        return status.Error(codes.InvalidArgument, "invalid email format")
    }
    return nil
}
```

---

## Common Pitfalls

### 1. Blocking Calls
```go
// Bad: Blocking in streaming
func (s *Server) StreamData(req *pb.Request, stream pb.Service_StreamDataServer) error {
    for {
        data := <-s.dataChannel  // Can block forever
        stream.Send(&pb.Response{Data: data})
    }
}

// Good: Use select with context
func (s *Server) StreamData(req *pb.Request, stream pb.Service_StreamDataServer) error {
    for {
        select {
        case data := <-s.dataChannel:
            if err := stream.Send(&pb.Response{Data: data}); err != nil {
                return err
            }
        case <-stream.Context().Done():
            return stream.Context().Err()
        }
    }
}
```

### 2. Not Handling Context Cancellation
```go
// Bad: Ignores context
func (s *Server) LongOperation(ctx context.Context, req *pb.Request) (*pb.Response, error) {
    // Takes 10 seconds but doesn't check for cancellation
    time.Sleep(10 * time.Second)
    return &pb.Response{}, nil
}

// Good: Respects context
func (s *Server) LongOperation(ctx context.Context, req *pb.Request) (*pb.Response, error) {
    done := make(chan struct{})
    go func() {
        // Do work
        time.Sleep(10 * time.Second)
        close(done)
    }()

    select {
    case <-done:
        return &pb.Response{}, nil
    case <-ctx.Done():
        return nil, ctx.Err() // Returns when client cancels
    }
}
```

### 3. Overusing Streaming
```go
// Don't use streaming when simple RPC suffices
// Only use streaming for:
// - Large datasets that don't fit in memory
// - Real-time updates
// - Long-running operations
```

---

## Tools & Ecosystem

### Development Tools

1. **protoc**: Protocol Buffer compiler
   ```bash
   protoc --go_out=. --go-grpc_out=. service.proto
   ```

2. **grpcurl**: CLI for interacting with gRPC servers
   ```bash
   grpcurl -plaintext localhost:50051 list
   grpcurl -plaintext localhost:50051 UserService/GetUser
   ```

3. **BloomRPC**: GUI for gRPC API testing
   - Similar to Postman but for gRPC

4. **Postman**: Now supports gRPC testing
   - Test both gRPC and REST APIs in one place

### Monitoring Tools

1. **Prometheus + Grafana**: Metrics collection and visualization
2. **Jaeger**: Distributed tracing
3. **OpenTelemetry**: Standardized observability

---

## Summary

### Key Takeaways

1. **RPC abstracts network complexity** - making remote calls feel local
2. **gRPC is the modern choice** - combining performance with strong typing
3. **Use RPC for internal microservices** - use REST for public APIs
4. **Always implement proper error handling** - use appropriate status codes
5. **Security is critical** - use TLS and implement authentication
6. **Monitor and log everything** - essential for distributed systems
7. **Respect contexts and timeouts** - prevent resource leaks
8. **Design your services carefully** - good interfaces prevent future pain

### When in Doubt

- **Performance matters?** → gRPC
- **Public API?** → REST
- **Simple prototype?** → JSON-RPC
- **Java microservices?** → Dubbo
- **Legacy integration?** → XML-RPC

---

## Further Reading

- [gRPC Official Documentation](https://grpc.io/docs/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- [Microservices Patterns](https://microservices.io/patterns/)
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices/9781491950340/)

---

**Document Version:** 1.0
**Last Updated:** 2025-02-25
**Author:** Claude Code
