# Admin RPC Development Guide

## Overview

This guide explains how to implement Admin RPC methods following the OpenIM Server gRPC pattern, where admin functionality is implemented in OpenIM Server and messenger-admin-service connects via gRPC.

## Architecture

```
┌─────────────────────┐      REST      ┌─────────────────────┐      gRPC      ┌─────────────────────┐
│  Admin-API        │ ─────────────> │  Admin-API         │ ─────────────> │  OpenIM Server    │
│  (REST Handler)  │              │  (gRPC Client)      │              │  (Admin/User/Group) │
└─────────────────────┘              └─────────────────────┘              └─────────────────────┘
        │                                   │                                        │
        │                                   │                                        │
        └───────────────────────────────────────┴────────────────────────────────────────┘
                           Shared Protocol Repository
                  (D:\nenglyheng\messenger\protocol\)
```

### Project Structure

```
messenger/
├── protocol/                              # Shared Protocol Repository
│   ├── openmeeting/
│   │   └── admin/
│   │       ├── admin.proto                 # Admin RPC definitions
│   │       ├── admin.pb.go                # Generated message definitions
│   │       └── admin_grpc.pb.go         # Generated gRPC client/server
│   ├── user/
│   │   ├── user.proto
│   │   ├── user.pb.go
│   │   └── user_grpc.pb.go
│   ├── group/
│   │   ├── group.proto
│   │   └── ...
│   └── ... (other services)
│
├── messenger-admin-service/                 # Admin REST API
│   ├── internal/
│   │   ├── api/admin/                   # REST API handlers (thin layer)
│   │   └── rpc/admin/                  # Deprecated: Remove or keep as wrapper
│   └── pkg/
│       └── rpclient/admin/               # Admin RPC client wrapper
│
└── open-im-server/                      # OpenIM Server (gRPC Service)
    ├── internal/rpc/user/               # User RPC implementation (existing)
    ├── internal/rpc/group/              # Group RPC implementation (existing)
    ├── internal/rpc/openmeeting/
    │   └── admin/                   # Admin RPC implementation (NEW)
    └── ... (other services)
```

## Migration from Old to New Architecture

### Current State (Old Architecture)
- Admin RPC logic is implemented in `messenger-admin-service/internal/rpc/admin/`
- Direct database access from messenger-admin-service
- Business logic mixed with RPC handling

### Target State (New Architecture)
- Admin RPC implementation moved to `open-im-server/internal/rpc/openmeeting/admin/`
- Messenger-admin-service becomes thin REST API layer
- Connects to OpenIM Server via gRPC (like user RPC pattern)

### Benefits of New Architecture
1. **Consistent gRPC Pattern:** All RPC services follow the same pattern
2. **Centralized Business Logic:** All RPC implementations in OpenIM Server
3. **Better Separation:** API layer (messenger-admin-service) is just HTTP/gRPC adapter
4. **Easier Maintenance:** Single place for all RPC implementations
5. **Service Discovery:** Uses same discovery mechanism as other RPC services
6. **Database Consistency:** All database operations through OpenIM Server's data layer

## Step-by-Step Guide

### Step 1: Add Admin RPC Service to OpenIM Server

**Location:** `open-im-server/internal/rpc/openmeeting/admin/`

Create new directory structure:

```
open-im-server/internal/rpc/openmeeting/admin/
├── admin.go                    # Main implementation
├── start.go                    # Server initialization
├── config.go                   # Configuration
└── admin_test.go               # (Optional) Tests
```

### Step 2: Implement Admin RPC Server

**File:** `open-im-server/internal/rpc/openmeeting/admin/start.go`

```go
package admin

import (
    "context"
    "crypto/md5"
    "encoding/hex"
    "math/rand"
    "time"

    "github.com/openimsdk/open-im-server/v3/internal/rpc/user"
    "github.com/openimsdk/open-im-server/v3/pkg/common/config"
    "github.com/openimsdk/open-im-server/v3/pkg/common/servererrs"
    "github.com/openimsdk/open-im-server/v3/pkg/common/storage/cache"
    "github.com/openimsdk/open-im-server/v3/pkg/common/storage/cache/redis"
    "github.com/openimsdk/open-im-server/v3/pkg/common/storage/controller"
    "github.com/openimsdk/open-im-server/v3/pkg/common/storage/database/mgo"
    adminmodel "github.com/openimsdk/open-im-server/v3/pkg/common/storage/model"
    adminpb "github.com/openimsdk/protocol/openmeeting/admin"
    "github.com/openimsdk/tools/db/mongoutil"
    "github.com/openimsdk/tools/db/redisutil"
    "github.com/openimsdk/tools/discovery"
    "github.com/openimsdk/tools/errs"
    "google.golang.org/grpc"
)

type Config struct {
    RpcConfig          config.Admin
    RedisConfig        config.Redis
    MongodbConfig      config.Mongo
    Discovery          config.Discovery
    Share              config.Share
}

type adminServer struct {
    adminpb.UnimplementedAdminServer
    db        controller.AdminDatabase
    userRPC   *user.Client
    config    *Config
}

func Start(ctx context.Context, config *Config, client discovery.SvcDiscoveryRegistry, server grpc.ServiceRegistrar) error {
    rand.Seed(time.Now().UnixNano())

    // Initialize database connections
    rdb, err := redisutil.NewRedisClient(ctx, config.RedisConfig.Build())
    if err != nil {
        return err
    }
    mgocli, err := mongoutil.NewMongoDB(ctx, config.MongodbConfig.Build())
    if err != nil {
        return err
    }

    var srv adminServer
    srv.db, err = controller.NewAdminDatabase(mgocli, rdb)
    if err != nil {
        return err
    }

    // Connect to user RPC for user operations
    userConn, err := client.GetConn(ctx, config.Discovery.RpcService.User, grpc.WithTransportCredentials(insecure.NewCredentials()))
    if err != nil {
        return err
    }
    srv.userRPC = user.NewUserClient(userConn)

    // Initialize admin accounts
    if err := srv.initAdmin(ctx, config.Share.ChatAdmin, config.Share.OpenIM.AdminUserID); err != nil {
        return err
    }

    // Register admin service
    adminpb.RegisterAdminServer(server, &srv)
    return nil
}

func (o *adminServer) initAdmin(ctx context.Context, admins []string, imUserID string) error {
    for _, account := range admins {
        if _, err := o.db.GetAdmin(ctx, account); err == nil {
            continue
        } else if !dbutil.IsDBNotFound(err) {
            return err
        }
        sum := md5.Sum([]byte(account))
        a := adminmodel.Admin{
            Account:    account,
            UserID:     imUserID,
            Password:   hex.EncodeToString(sum[:]),
            CreateTime: time.Now(),
        }
        if err := o.db.Create(ctx, []*adminmodel.Admin{&a}); err != nil {
            return err
        }
    }
    return nil
}
```

### Step 3: Implement Admin RPC Methods

**File:** `open-im-server/internal/rpc/openmeeting/admin/admin.go`

```go
package admin

import (
    "context"

    "github.com/openimsdk/open-im-server/v3/pkg/common/mctx"
    "github.com/openimsdk/open-im-server/v3/pkg/eerrs"
    adminpb "github.com/openimsdk/protocol/openmeeting/admin"
)

func (o *adminServer) GetAdminInfo(ctx context.Context, req *adminpb.GetAdminInfoReq) (*adminpb.GetAdminInfoResp, error) {
    // Check admin authentication
    userID, err := mctx.CheckAdmin(ctx)
    if err != nil {
        return nil, err
    }

    // Get admin info from database
    a, err := o.db.GetAdminUserID(ctx, userID)
    if err != nil {
        return nil, err
    }

    return &adminpb.GetAdminInfoResp{
        Account:    a.Account,
        Password:   a.Password,
        FaceURL:    a.FaceURL,
        Nickname:   a.Nickname,
        UserID:     a.UserID,
        Level:      a.Level,
        CreateTime: a.CreateTime.UnixMilli(),
    }, nil
}

func (o *adminServer) ChangeAdminPassword(ctx context.Context, req *adminpb.ChangeAdminPasswordReq) (*adminpb.ChangeAdminPasswordResp, error) {
    user, err := o.db.GetAdminUserID(ctx, req.UserID)
    if err != nil {
        return nil, err
    }

    if user.Password != req.CurrentPassword {
        return nil, servererrs.ErrPasswordIncorrect
    }

    if err := o.db.ChangePassword(ctx, req.UserID, req.NewPassword); err != nil {
        return nil, err
    }
    return &adminpb.ChangeAdminPasswordResp{}, nil
}

func (o *adminServer) AddAdminAccount(ctx context.Context, req *adminpb.AddAdminAccountReq) (*adminpb.AddAdminAccountResp, error) {
    if err := o.CheckSuperAdmin(ctx); err != nil {
        return nil, err
    }

    _, err := o.db.GetAdmin(ctx, req.Account)
    if err == nil {
        return nil, servererrs.ErrDuplicateAdmin
    }

    // Generate user ID
    userID := o.genUserID()

    adm := &adminmodel.Admin{
        Account:    req.Account,
        Password:   req.Password,
        FaceURL:    req.FaceURL,
        Nickname:   req.Nickname,
        UserID:     userID,
        Level:      80,
        CreateTime: time.Now(),
    }
    if err = o.db.Create(ctx, []*adminmodel.Admin{adm}); err != nil {
        return nil, err
    }
    return &adminpb.AddAdminAccountResp{}, nil
}

func (o *adminServer) genUserID() string {
    const l = 10
    data := make([]byte, l)
    rand.Read(data)
    chars := []byte("0123456789")
    for i := 0; i < len(data); i++ {
        if i == 0 {
            data[i] = chars[1:][data[i]%9]
        } else {
            data[i] = chars[data[i]%10]
        }
    }
    return string(data)
}
```

### Step 4: Add RPC Client to Messenger-Admin-Service

**Location:** `messenger-admin-service/pkg/rpclient/admin/admin.go`

```go
package admin

import (
    "context"

    adminpb "github.com/openimsdk/protocol/openmeeting/admin"
)

func NewAdminClient(conn *grpc.ClientConn) *AdminClient {
    return &AdminClient{
        client: adminpb.NewAdminClient(conn),
    }
}

type AdminClient struct {
    client adminpb.AdminClient
}

func (c *AdminClient) GetAdminInfo(ctx context.Context, req *adminpb.GetAdminInfoReq) (*adminpb.GetAdminInfoResp, error) {
    return c.client.GetAdminInfo(ctx, req)
}

func (c *AdminClient) ChangeAdminPassword(ctx context.Context, req *adminpb.ChangeAdminPasswordReq) (*adminpb.ChangeAdminPasswordResp, error) {
    return c.client.ChangeAdminPassword(ctx, req)
}

// Add other client methods as needed...
```

### Step 5: Update REST API Handlers

**Location:** `messenger-admin-service/internal/api/admin/admin.go`

Update to use gRPC client:

```go
package admin

import (
    "github.com/gin-gonic/gin"
    openmeetingadmin "github.com/openimsdk/protocol/openmeeting/admin"
    "github.com/openimsdk/chat/pkg/rpclient/admin"
    "github.com/openimsdk/tools/a2r"
)

func (o *Api) GetAdminInfo(c *gin.Context) {
    a2r.Call(openmeetingadmin.AdminClient.GetAdminInfo, o.adminClient, c)
}

func (o *Api) ChangeAdminPassword(c *gin.Context) {
    a2r.Call(openmeetingadmin.AdminClient.ChangeAdminPassword, o.adminClient, c)
}

func (o *Api) AddAdminAccount(c *gin.Context) {
    a2r.Call(openmeetingadmin.AdminClient.AddAdminAccount, o.adminClient, c)
}
```

### Step 6: Update Service Discovery

**Location:** `open-im-server/cmd/openim-rpc/main.go` (or similar)

Add admin RPC service to discovery:

```go
// Add to discovery configuration
discoveryConfig.RpcService.OpenMeetingAdmin = "openim-admin-rpc"

// Register admin service
conn, err := client.GetConn(ctx, config.Discovery.RpcService.OpenMeetingAdmin)
if err != nil {
    return err
}
```

**Location:** `messenger-admin-service/cmd/api/main.go`

Update to connect to admin RPC:

```go
// Connect to admin RPC
adminConn, err := client.GetConn(ctx, config.Discovery.RpcService.OpenMeetingAdmin)
if err != nil {
    return err
}
adminClient := adminClient.NewAdminClient(adminConn)
```

### Step 7: Generate Protobuf Files

```bash
cd D:\nenglyheng\messenger\protocol
./gen.sh
```

This generates:
- `openmeeting/admin/admin.pb.go` - Message definitions
- `openmeeting/admin/admin_grpc.pb.go` - gRPC client/server

After generation, update go.mod in both projects:

```bash
cd messenger-admin-service
go mod tidy

cd ../open-im-server
go mod tidy
```

### Step 8: Add Check() Method for Request Validation

**Location:** `D:\nenglyheng\messenger\protocol\openmeeting\admin\admin.go`

```go
func (x *GetAdminInfoReq) Check() error {
    return nil // No validation needed
}

func (x *ChangeAdminPasswordReq) Check() error {
    if x.UserID == "" {
        return errs.ErrArgs.WrapMsg("userID is required")
    }
    if x.CurrentPassword == "" {
        return errs.ErrArgs.WrapMsg("currentPassword is required")
    }
    if x.NewPassword == "" {
        return errs.ErrArgs.WrapMsg("newPassword is required")
    }
    return nil
}

func (x *AddAdminAccountReq) Check() error {
    if x.Account == "" {
        return errs.ErrArgs.WrapMsg("account is required")
    }
    if x.Password == "" {
        return errs.ErrArgs.WrapMsg("password is required")
    }
    return nil
}
```

## Complete Example

Here's a complete example for adding a "GetUserStatistics" admin RPC method:

### 1. Protocol Definition (`D:\nenglyheng\messenger\protocol\openmeeting\admin\admin.proto`)

```protobuf
message GetUserStatisticsReq {
  repeated string userIDs = 1;
}

message UserStatistics {
  string userID = 1;
  int32 messageCount = 2;
  int32 friendCount = 3;
  int32 groupCount = 4;
}

message GetUserStatisticsResp {
  repeated UserStatistics statistics = 1;
  uint32 total = 2;
}

service admin {
  rpc GetUserStatistics(GetUserStatisticsReq) returns (GetUserStatisticsResp);
}
```

### 2. Request Validation (`D:\nenglyheng\messenger\protocol\openmeeting\admin\admin.go`)

```go
func (x *GetUserStatisticsReq) Check() error {
    if len(x.UserIDs) == 0 {
        return errs.ErrArgs.WrapMsg("userIDs cannot be empty")
    }
    return nil
}
```

### 3. Server Implementation (`open-im-server/internal/rpc/openmeeting/admin/admin.go`)

```go
func (o *adminServer) GetUserStatistics(ctx context.Context, req *adminpb.GetUserStatisticsReq) (*adminpb.GetUserStatisticsResp, error) {
    userID, err := mctx.CheckAdmin(ctx)
    if err != nil {
        return nil, err
    }

    if err := req.Check(); err != nil {
        return nil, err
    }

    // Get user info from OpenIM Server's user RPC
    users, err := o.userRPC.GetDesignateUsers(ctx, &userpb.GetDesignateUsersReq{
        UserIDs: req.UserIDs,
    })
    if err != nil {
        return nil, err
    }

    statistics := make([]*adminpb.UserStatistics, 0, len(users.UsersInfo))
    for _, user := range users.UsersInfo {
        stats := &adminpb.UserStatistics{
            UserID: user.UserID,
            // Add your custom statistics here
            MessageCount: 0,
            FriendCount:  0,
            GroupCount:   0,
        }
        statistics = append(statistics, stats)
    }

    return &adminpb.GetUserStatisticsResp{
        Statistics: statistics,
        Total:      uint32(len(statistics)),
    }, nil
}
```

### 4. Client Wrapper (`messenger-admin-service/pkg/rpclient/admin/admin.go`)

```go
func (c *AdminClient) GetUserStatistics(ctx context.Context, req *adminpb.GetUserStatisticsReq) (*adminpb.GetUserStatisticsResp, error) {
    return c.client.GetUserStatistics(ctx, req)
}
```

### 5. REST API Handler (`messenger-admin-service/internal/api/admin/admin.go`)

```go
func (o *Api) GetUserStatistics(c *gin.Context) {
    a2r.Call(openmeetingadmin.AdminClient.GetUserStatistics, o.adminClient, c)
}
```

### 6. Route Definition (`messenger-admin-service/internal/api/admin/start.go`)

```go
func SetAdminRoute(router gin.IRouter, admin *Api, mw *chatmw.MW, cfg *Config, client discovery.SvcDiscoveryRegistry) {
    // ... existing routes ...

    statisticRouter := router.Group("/statistic", mw.CheckAdmin)
    statisticRouter.POST("/user", admin.GetUserStatistics)
}
```

## Configuration

Ensure your discovery configuration includes OpenIM Server services:

**Location:** `messenger-admin-service/config/config.yaml` (or similar)

```yaml
discovery:
  enable: etcd
  etcd:
    addrs: ["localhost:2379"]
  rpc_service:
    admin: openim-admin-rpc      # New: Admin RPC in OpenIM Server
    chat: openim-chat-rpc
    user: openim-user-rpc
    group: openim-group-rpc
    msg: openim-msg-rpc
    # ... other services
```

## Testing

1. **Generate protobuf files:**
   ```bash
   cd D:\nenglyheng\messenger\protocol
   ./gen.sh
   ```

2. **Update go.mod files:**
   ```bash
   cd messenger-admin-service
   go mod tidy

   cd ../open-im-server
   go mod tidy
   ```

3. **Build admin-service:**
   ```bash
   cd messenger-admin-service
   make build
   ```

4. **Start OpenIM Server:**
   ```bash
   cd open-im-server
   make start
   ```

5. **Start admin-service:**
   ```bash
   cd messenger-admin-service
   make start
   ```

6. **Test the REST API:**
   ```bash
   curl -X POST http://localhost:10002/statistic/user \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your-admin-token>" \
     -d '{"userIDs": ["user1", "user2"]}'
   ```

## Key Files Reference

| File | Purpose |
|------|---------|
| `D:\nenglyheng\messenger\protocol\openmeeting\admin\admin.proto` | Admin RPC method definitions |
| `D:\nenglyheng\messenger\protocol\openmeeting\admin\admin.go` | Request validation |
| `D:\nenglyheng\messenger\protocol\openmeeting\admin\admin.pb.go` | Generated message definitions |
| `D:\nenglyheng\messenger\protocol\openmeeting\admin\admin_grpc.pb.go` | Generated gRPC client/server |
| `D:\nenglyheng\messenger\protocol\user\user.proto` | OpenIM Server User RPC definitions |
| `D:\nenglyheng\messenger\protocol\group\group.proto` | OpenIM Server Group RPC definitions |
| `open-im-server/internal/rpc/openmeeting/admin/start.go` | Admin RPC server initialization |
| `open-im-server/internal/rpc/openmeeting/admin/*.go` | Admin RPC method implementations |
| `messenger-admin-service/pkg/rpclient/admin/admin.go` | Admin RPC client wrapper |
| `messenger-admin-service/internal/api/admin/start.go` | REST API routes |
| `messenger-admin-service/internal/api/admin/admin.go` | REST API handlers |

## Best Practices

1. **Follow User RPC Pattern:** Use the same patterns as existing RPC services in OpenIM Server
2. **Always validate requests** using `Check()` method
3. **Use `mctx.CheckAdmin()`** to ensure caller is authenticated
4. **Follow naming conventions** - use descriptive names for methods and messages
5. **Handle errors properly** using servererrs package for server-specific errors
6. **Use middleware** for authentication and authorization (`mw.CheckAdmin`)
7. **Keep business logic** in OpenIM Server, not in API layer
8. **Document your methods** with clear comments
9. **Test thoroughly** with various scenarios
10. **Use dependency injection** for other RPC services (user, group, etc.)

## Common OpenIM Server RPC Methods

### User RPC
- `GetDesignateUsers` - Get user information by user IDs
- `UserRegister` - Register new users
- `UpdateUserInfo` - Update user information
- `GetPaginationUsers` - Get paginated user list

### Group RPC
- `GetGroupsInfo` - Get group information
- `CreateGroup` - Create a new group
- `GetGroupMembersInfo` - Get group members information

### Message RPC
- `SendMsg` - Send message
- `GetMaxSeq` - Get maximum sequence number

### Relation RPC
- `GetFriendIDs` - Get friend IDs
- `AddFriend` - Add friend
- `DeleteFriend` - Delete friend

## Troubleshooting

### Issue: RPC method not found
**Solution:** Make sure you've regenerated protobuf files after modifying `.proto` file and updated go.mod in both projects.

### Issue: Connection refused to OpenIM Server
**Solution:** Check your discovery configuration and ensure OpenIM Server services are running.

### Issue: Admin RPC not registered
**Solution:** Make sure you've added the admin RPC service to OpenIM Server's service discovery.

### Issue: Authentication errors
**Solution:** Ensure that admin token is valid and user has sufficient permissions in OpenIM Server.

### Issue: Database connection errors
**Solution:** Check that OpenIM Server's database configuration matches messenger-admin-service's database settings if needed.

### Issue: Request validation fails
**Solution:** Check your `Check()` method implementation and ensure all required fields are provided.

## Additional Resources

- [OpenIM Server Documentation](https://docs.openim.io/)
- [gRPC Go Documentation](https://grpc.io/docs/languages/go/)
- [Protocol Buffers Guide](https://developers.google.com/protocol-buffers)
