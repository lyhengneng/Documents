# OpenIM Server Learning Guide

> A step-by-step guide to understand and explore the OpenIM Server codebase

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Learning Path](#4-learning-path)
5. [Key Concepts](#5-key-concepts)
6. [Practical Exercises](#6-practical-exercises)
7. [Resources](#7-resources)
8. [Progress Tracker](#8-progress-tracker)

---

## 1. Project Overview

### What is OpenIM?

OpenIM is an **open-source instant messaging server** designed for developers to integrate IM functionality into their applications.

**Key Characteristics:**
- 🏗️ **Microservices Architecture** - Scalable and maintainable
- 📡 **Real-time Communication** - WebSocket support
- 🔐 **Authentication & Authorization** - Secure user management
- 💬 **Messaging** - Individual and group messaging
- 🌐 **REST API** - Easy integration with client applications

**Main Components:**
- **OpenIM Server** (this project) - Backend services
- **OpenIM SDK** - Client-side SDKs for integration

---

## 2. Technology Stack

### Core Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| **Go** | Programming Language | 1.22.7 |
| **gRPC** | Service Communication | - |
| **Gin** | HTTP Web Framework | 1.9.1 |
| **MongoDB** | Primary Database | - |
| **Redis** | Cache & Session Management | - |
| **Kafka** | Message Queue | - |
| **WebSocket** | Real-time Communication | - |
| **Docker** | Containerization | - |
| **Prometheus** | Monitoring | - |

### Key Dependencies

```
github.com/openimsdk/protocol       - Protocol buffers
github.com/openimsdk/tools          - Common utilities
github.com/gin-gonic/gin            - HTTP framework
go.mongodb.org/mongo-driver         - MongoDB driver
github.com/redis/go-redis/v9        - Redis driver
github.com/IBM/sarama               - Kafka client
google.golang.org/grpc              - gRPC framework
```

---

## 3. Project Structure

### High-Level Directory Structure

```
open-im-server-3.8.3-patch.12/
├── cmd/                    # Entry points for all services
├── internal/               # Private application code
├── pkg/                    # Public library code
├── config/                 # Configuration files
├── deployments/            # Deployment configurations
├── docs/                   # Documentation
├── scripts/                # Build and utility scripts
├── test/                   # Test files
├── tools/                  # Development tools
└── build/                  # Build artifacts
```

### Service Entry Points (`cmd/`)

```
cmd/
├── openim-api/                    # HTTP API Gateway
│   └── main.go
├── openim-msggateway/             # WebSocket Gateway
│   └── main.go
├── openim-msgtransfer/            # Message Transfer Service
│   └── main.go
├── openim-push/                   # Push Notification Service
│   └── main.go
├── openim-crontask/               # Scheduled Tasks
│   └── main.go
└── openim-rpc/                    # RPC Services
    ├── openim-rpc-auth/           # Authentication Service
    ├── openim-rpc-user/           # User Management
    ├── openim-rpc-friend/         # Friend Management
    ├── openim-rpc-group/          # Group Management
    ├── openim-rpc-msg/            # Message Service
    ├── openim-rpc-conversation/   # Conversation Management
    └── openim-rpc-third/          # Third-party Services
```

### Internal Code (`internal/`)

```
internal/
├── api/                    # HTTP API handlers
├── rpc/                    # RPC server implementations
├── msggateway/             # WebSocket gateway logic
├── msgtransfer/            # Message transfer logic
└── push/                   # Push notification logic
```

### Shared Packages (`pkg/`)

```
pkg/
├── common/                 # Common utilities
│   └── cmd/                # Command-line interface code
├── apistruct/              # API structures
├── authverify/             # Authentication verification
├── localcache/             # Local cache implementation
├── msgprocessor/           # Message processing
├── notification/           # Notification handling
└── util/                   # Utility functions
```

---

## 4. Learning Path

### Phase 1: Foundation (Days 1-2)

#### ☐ Step 1: Read Project Documentation
**Files to read:**
- [ ] `README.md` - Project overview
- [ ] `CONTRIBUTING.md` - Contribution guidelines
- [ ] `docs/contrib/development.md` - Development setup

**Key learnings:**
- [ ] What OpenIM is and what it does
- [ ] How to set up development environment
- [ ] Coding standards and conventions

---

#### ☐ Step 2: Understand Configuration
**Files to examine:**
- [ ] `.env` - Environment variables
- [ ] `config/` - Configuration files
- [ ] `docker-compose.yml` - Service dependencies

**Key learnings:**
- [ ] What services are required (MongoDB, Redis, Kafka, etc.)
- [ ] Configuration structure
- [ ] How services connect to each other

---

### Phase 2: Entry Points (Days 3-4)

#### ☐ Step 3: Study API Gateway
**Files to read in order:**
1. [ ] `cmd/openim-api/main.go` - Entry point
2. [ ] `pkg/common/cmd/api.go` - Command setup
3. [ ] `internal/api/` - API handlers

**Code walkthrough:**
```go
// cmd/openim-api/main.go
func main() {
    if err := cmd.NewApiCmd().Exec(); err != nil {
        program.ExitWithError(err)
    }
}
```

**Key learnings:**
- [ ] How the API service starts
- [ ] How HTTP requests are routed
- [ ] How it connects to RPC services

---

#### ☐ Step 4: Study One RPC Service
**Choose one service to understand deeply:**

**Option A: User Service** (Recommended for beginners)
1. [ ] `cmd/openim-rpc/openim-rpc-user/main.go`
2. [ ] `internal/rpc/user/`

**Option B: Message Service**
1. [ ] `cmd/openim-rpc/openim-rpc-msg/main.go`
2. [ ] `internal/rpc/msg/`

**Key learnings:**
- [ ] How RPC services are structured
- [ ] How they handle requests
- [ ] How they interact with the database

---

### Phase 3: Message Flow (Days 5-6)

#### ☐ Step 5: Understand WebSocket Gateway
**Files to study:**
- [ ] `cmd/openim-msggateway/main.go`
- [ ] `internal/msggateway/`

**Key learnings:**
- [ ] How clients connect via WebSocket
- [ ] How connections are managed
- [ ] How real-time messages are delivered

---

#### ☐ Step 6: Study Message Transfer
**Files to study:**
- [ ] `cmd/openim-msgtransfer/main.go`
- [ ] `internal/msgtransfer/`

**Key learnings:**
- [ ] How messages are processed
- [ ] How Kafka is used for message queuing
- [ ] How messages are stored and retrieved

---

### Phase 4: Core Features (Days 7-10)

#### ☐ Step 7: Authentication Flow
**Files to study:**
- [ ] `internal/rpc/auth/`
- [ ] `pkg/authverify/`

**Trace the flow:**
1. Client sends login request
2. API receives request
3. RPC validates credentials
4. Token is generated
5. Response returned to client

---

#### ☐ Step 8: User Management
**Files to study:**
- [ ] `internal/rpc/user/`
- [ ] User registration
- [ ] User profile management
- [ ] User search

---

#### ☐ Step 9: Group Management
**Files to study:**
- [ ] `internal/rpc/group/`
- [ ] Group creation
- [ ] Member management
- [ ] Group messaging

---

#### ☐ Step 10: Message Sending Flow
**End-to-end flow:**
1. Client sends message via WebSocket
2. MsgGateway receives message
3. MsgTransfer processes message
4. Message stored in MongoDB
5. Message sent to Kafka
6. Recipients notified via Push service

**Files to trace:**
- [ ] `internal/msggateway/`
- [ ] `internal/msgtransfer/`
- [ ] `internal/push/`

---

## 5. Key Concepts

### 5.1 Microservices Architecture

**Services communicate via:**
- **gRPC** - Service-to-service communication
- **Kafka** - Asynchronous messaging
- **HTTP/REST** - Client-to-server communication

**Benefits:**
- Scalability
- Independent deployment
- Technology diversity
- Fault isolation

---

### 5.2 Request Flow

```
Client Request
    ↓
API Gateway (HTTP)
    ↓
RPC Service (gRPC)
    ↓
Database (MongoDB/Redis)
    ↓
Response
```

---

### 5.3 Message Flow

```
Sender ──WebSocket──> MsgGateway
                         ↓
                    MsgTransfer
                         ↓
                    Kafka Queue
                         ↓
                    MsgTransfer
                         ↓
              Recipient (WebSocket)
```

---

### 5.4 Data Storage

**MongoDB:**
- User data
- Messages
- Groups
- Conversations

**Redis:**
- Session management
- Cache
- Online status
- Rate limiting

---

## 6. Practical Exercises

### Exercise 1: Setup Environment

☐ **Install dependencies:**
```bash
# Go
go version  # Should be 1.22.7+

# Docker
docker --version

# Build the project
mage build
```

☐ **Run services:**
```bash
docker-compose up -d
```

---

### Exercise 2: Trace a Simple Request

**Goal:** Understand how a user login request works

**Steps:**
1. Find login API endpoint in `internal/api/`
2. Trace to RPC call
3. Find database query
4. Identify response generation

**Files to examine:**
- `internal/api/user.go` (or similar)
- `internal/rpc/user/`
- Database models

---

### Exercise 3: Add a Simple Log

**Goal:** Understand execution flow

**Steps:**
1. Add a log statement in `internal/api/`
2. Rebuild and run
3. Make a request
4. Observe the log output

```go
log.ZDebug(ctx, "My first debug log", "function", "myFunction")
```

---

### Exercise 4: Draw Architecture Diagram

**Create a diagram showing:**
1. All services
2. How they connect
3. Data flow between them

**Tools:**
- Draw.io
- Mermaid
- Paper and pencil

---

### Exercise 5: Read Configuration

**Analyze:**
- What ports does each service use?
- What are the MongoDB connection settings?
- What Kafka topics are used?

---

## 7. Resources

### Documentation

- **Official Docs:** https://docs.openim.io/
- **API Reference:** Check `docs/contrib/api.md`
- **Contributing Guide:** `CONTRIBUTING.md`

### Key Documentation Files

| File | Purpose |
|------|---------|
| `docs/contrib/development.md` | Development setup |
| `docs/contrib/api.md` | API documentation |
| `docs/contrib/code-conventions.md` | Coding standards |
| `docs/contrib/logging.md` | Logging conventions |
| `docs/contrib/init-config.md` | Configuration guide |

### External Resources

- **Go Documentation:** https://golang.org/doc/
- **gRPC Guide:** https://grpc.io/docs/languages/go/
- **MongoDB Go Driver:** https://www.mongodb.com/docs/drivers/go/
- **Gin Framework:** https://gin-gonic.com/docs/

---

## 8. Progress Tracker

### Week 1 Checklist

**Days 1-2: Foundation**
- [ ] Read README.md
- [ ] Read CONTRIBUTING.md
- [ ] Study project structure
- [ ] Understand configuration files

**Days 3-4: Entry Points**
- [ ] Study API Gateway (`cmd/openim-api/`)
- [ ] Study one RPC service (User or Message)
- [ ] Understand service initialization

**Days 5-6: Message Flow**
- [ ] Study MsgGateway
- [ ] Study MsgTransfer
- [ ] Understand WebSocket connections

**Days 7-10: Core Features**
- [ ] Authentication flow
- [ ] User management
- [ ] Group management
- [ ] Message sending flow

---

### Learning Goals

**Week 1 Goals:**
- [ ] Understand overall architecture
- [ ] Can explain the request flow
- [ ] Know where each service is located
- [ ] Can navigate the codebase

**Week 2 Goals:**
- [ ] Can trace a feature end-to-end
- [ ] Understand database schema
- [ ] Know how to add a simple feature
- [ ] Can run the project locally

**Week 3 Goals:**
- [ ] Can make a small contribution
- [ ] Understand testing approach
- [ ] Know how to debug issues
- [ ] Can help others navigate the code

---

## 9. Quick Reference

### Common File Locations

| What you want to find | Where to look |
|----------------------|---------------|
| API endpoints | `internal/api/` |
| RPC services | `internal/rpc/` |
| Database models | `internal/rpc/*/model.go` |
| Configuration | `config/` and `.env` |
| Utility functions | `pkg/util/` |
| Common structures | `pkg/apistruct/` |
| Protocol definitions | `github.com/openimsdk/protocol` |

### Common Commands

```bash
# Build all services
mage build

# Run all services
mage start

# Run tests
mage test

# Check code style
mage lint

# Generate code
mage generate
```

### IDE Tips

1. **Use "Go to Definition"** (F12) to navigate
2. **Use "Find References"** (Shift+F12) to see usage
3. **Use "Go to Symbol"** (Ctrl+Shift+O) to find functions
4. **Set breakpoints** to understand execution flow
5. **Use debugger** to inspect variables

---

## 10. Next Steps

After completing this guide:

1. **Pick a Feature** - Choose a feature that interests you
2. **Read the Code** - Study its implementation
3. **Make Changes** - Try to modify it
4. **Test** - Verify your changes work
5. **Contribute** - Submit a pull request

### Suggested First Contributions

- Fix a typo in documentation
- Add logging to a function
- Improve error messages
- Add unit tests
- Fix a simple bug

---

## Notes Section

Use this section to write down your observations:

```
Key learnings:
1.


2.


3.


Questions:
1.


2.


3.


Important files:
-


-


Concepts to revisit:
-


-
```

---

**Remember:** Learning a large codebase takes time. Be patient, ask questions, and celebrate small wins!

**Need help?**
- Check the `docs/` directory
- Read existing issues on GitHub
- Ask questions in the community

**Happy Learning!** 🚀
