# UserRegister API Processing Documentation

## Overview
The UserRegister API allows administrators to register new user accounts in the OpenIM system. This API supports registering multiple users in a single request and includes webhook callbacks for pre- and post-registration processing.

---

## Step-by-Step Processing Flow

### Step 1: HTTP Request Reception
**Location:** `internal/api/router.go:103`

```go
userRouterGroup.POST("/user_register", u.UserRegister)
```

- **Endpoint:** `POST /user/user_register`
- **Request Body:** Array of user information (via `pbuser.UserRegisterReq`)
- **Authentication:** **Admin token required** (processed by `GinParseToken` middleware)
  - API is **NOT** in the whitelist
  - Must include valid token in header: `operationID: <token>`

---

### Step 2: HTTP Handler - UserApi.UserRegister
**Location:** `internal/api/user.go:40-42`

```go
func (u *UserApi) UserRegister(c *gin.Context) {
    a2r.Call(c, user.UserClient.UserRegister, u.Client)
}
```

**What happens:**
- Receives the HTTP Gin context
- Delegates to `a2r.Call` which automatically handles:
  - JSON request binding to `pbuser.UserRegisterReq` protobuf struct
  - Context propagation (operation ID, user ID, platform)
  - gRPC client invocation
  - Response serialization

---

### Step 3: RPC Client Invocation
**Tool:** `github.com/openimsdk/tools/a2r`

The `a2r.Call` function:
1. Extracts user context from Gin middleware
2. Binds HTTP JSON body to `pbuser.UserRegisterReq` protobuf struct
3. Calls the gRPC client method `user.UserClient.UserRegister`
4. Serializes the `pbuser.UserRegisterResp` back to JSON

---

### Step 4: RPC Server Handler - UserRegister
**Location:** `internal/rpc/user/user.go:271-325`

```go
func (s *userServer) UserRegister(ctx context.Context, req *pbuser.UserRegisterReq) (resp *pbuser.UserRegisterResp, err error) {
    resp = &pbuser.UserRegisterResp{}

    // Step 4.1: Validate input
    if len(req.Users) == 0 {
        return nil, errs.ErrArgs.WrapMsg("users is empty")
    }

    // Step 4.2: Verify admin authorization
    if err = authverify.CheckAdmin(ctx, s.config.Share.IMAdminUserID); err != nil {
        return nil, err
    }

    // Step 4.3: Check for duplicate userIDs in request
    if datautil.DuplicateAny(req.Users, func(e *sdkws.UserInfo) string { return e.UserID }) {
        return nil, errs.ErrArgs.WrapMsg("userID repeated")
    }

    // Step 4.4: Validate each userID
    userIDs := make([]string, 0)
    for _, user := range req.Users {
        if user.UserID == "" {
            return nil, errs.ErrArgs.WrapMsg("userID is empty")
        }
        if strings.Contains(user.UserID, ":") {
            return nil, errs.ErrArgs.WrapMsg("userID contains ':' is invalid userID")
        }
        userIDs = append(userIDs, user.UserID)
    }

    // Step 4.5: Check if users already exist
    exist, err := s.db.IsExist(ctx, userIDs)
    if err != nil {
        return nil, err
    }
    if exist {
        return nil, servererrs.ErrRegisteredAlready.WrapMsg("userID registered already")
    }

    // Step 4.6: Execute before-registration webhook (synchronous)
    if err := s.webhookBeforeUserRegister(ctx, &s.config.WebhooksConfig.BeforeUserRegister, req); err != nil {
        return nil, err
    }

    // Step 4.7: Create user records in database
    now := time.Now()
    users := make([]*tablerelation.User, 0, len(req.Users))
    for _, user := range req.Users {
        users = append(users, &tablerelation.User{
            UserID:           user.UserID,
            Nickname:         user.Nickname,
            FaceURL:          user.FaceURL,
            Ex:               user.Ex,
            CreateTime:       now,
            AppMangerLevel:   user.AppMangerLevel,
            GlobalRecvMsgOpt: user.GlobalRecvMsgOpt,
        })
    }
    if err := s.db.Create(ctx, users); err != nil {
        return nil, err
    }

    // Step 4.8: Update metrics
    prommetrics.UserRegisterCounter.Add(float64(len(users)))

    // Step 4.9: Execute after-registration webhook (asynchronous)
    s.webhookAfterUserRegister(ctx, &s.config.WebhooksConfig.AfterUserRegister, req)

    return resp, nil
}
```

**What happens:**
1. Validates input (users array not empty)
2. Verifies admin authorization
3. Checks for duplicate userIDs in request
4. Validates each userID format (not empty, no colons)
5. Checks if users already exist in database
6. Calls before-registration webhook (synchronous - can modify user data)
7. Creates user records in database
8. Updates Prometheus metrics
9. Calls after-registration webhook (asynchronous - notification only)

---

### Step 5: Database Layer - User Creation
**Location:** `pkg/common/storage/controller/user.go` (via `s.db.Create()`)

The database layer:
- Accepts array of `*tablerelation.User` objects
- Inserts user records into MongoDB
- Handles transaction management if needed
- Returns error if insertion fails

---

### Step 6: Webhook Processing

#### Step 6a: Before-Registration Webhook (Synchronous)
**Location:** `internal/rpc/user/callback.go:88-106`

```go
func (s *userServer) webhookBeforeUserRegister(ctx context.Context, before *config.BeforeConfig, req *pbuser.UserRegisterReq) error {
    return webhook.WithCondition(ctx, before, func(ctx context.Context) error {
        cbReq := &cbapi.CallbackBeforeUserRegisterReq{
            CallbackCommand: cbapi.CallbackBeforeUserRegisterCommand,
            Users:           req.Users,
        }

        resp := &cbapi.CallbackBeforeUserRegisterResp{}

        if err := s.webhookClient.SyncPost(ctx, cbReq.GetCallbackCommand(), cbReq, resp, before); err != nil {
            return err
        }

        // Webhook can modify user data
        if len(resp.Users) != 0 {
            req.Users = resp.Users
        }
        return nil
    })
}
```

**Purpose:**
- Allows external systems to validate and/or modify user data before registration
- If webhook returns modified user data, it replaces the original data
- If webhook fails, registration is aborted
- Uses **synchronous** HTTP call to webhook URL

**Configuration:** `webhooks.beforeUserRegister` in config file

#### Step 6b: After-Registration Webhook (Asynchronous)
**Location:** `internal/rpc/user/callback.go:108-115`

```go
func (s *userServer) webhookAfterUserRegister(ctx context.Context, after *config.AfterConfig, req *pbuser.UserRegisterReq) {
    cbReq := &cbapi.CallbackAfterUserRegisterReq{
        CallbackCommand: cbapi.CallbackAfterUserRegisterCommand,
        Users:           req.Users,
    }

    s.webhookClient.AsyncPost(ctx, cbReq.GetCallbackCommand(), cbReq, &cbapi.CallbackAfterUserRegisterResp{}, after)
}
```

**Purpose:**
- Notifies external systems that user registration completed successfully
- Does not affect the registration process (errors are ignored)
- Uses **asynchronous** HTTP call to webhook URL

**Configuration:** `webhooks.afterUserRegister` in config file

---

### Step 7: Response Flow Back to Client

The response flows back through the same layers:

1. **RPC Server** → Returns `pbuser.UserRegisterResp{}` (empty response on success)
2. **gRPC Transport** → Sends response over network
3. **RPC Client** → Receives and deserializes
4. **a2r.Call** → Converts to JSON HTTP response
5. **HTTP Client** → Receives JSON response

---

## API Contract

### Request
```json
{
  "users": [
    {
      "userID": "user123",
      "nickname": "John Doe",
      "faceURL": "https://example.com/avatar.jpg",
      "ex": "{\"customField\":\"value\"}",
      "appMangerLevel": 1,
      "globalRecvMsgOpt": 0
    },
    {
      "userID": "user456",
      "nickname": "Jane Smith"
    }
  ]
}
```

### Response (Success)
```json
{}
```

### Response (Error)
```json
{
  "errCode": 1001,
  "errMsg": "userID registered already"
}
```

---

## Webhook Structures

### Before-Registration Webhook Request
**Endpoint:** Configured webhook URL with command `callbackBeforeUserRegisterCommand`

```json
{
  "callbackCommand": "callbackBeforeUserRegisterCommand",
  "users": [
    {
      "userID": "user123",
      "nickname": "John Doe",
      "faceURL": "https://example.com/avatar.jpg",
      "ex": "{\"customField\":\"value\"}",
      "appMangerLevel": 1,
      "globalRecvMsgOpt": 0
    }
  ]
}
```

### Before-Registration Webhook Response
```json
{
  "errCode": 0,
  "errMsg": "",
  "users": [
    {
      "userID": "user123",
      "nickname": "Modified Name",
      "faceURL": "https://example.com/new-avatar.jpg",
      "ex": "{\"customField\":\"newValue\"}",
      "appMangerLevel": 1,
      "globalRecvMsgOpt": 0
    }
  ]
}
```

### After-Registration Webhook Request
**Endpoint:** Configured webhook URL with command `callbackAfterUserRegisterCommand`

```json
{
  "callbackCommand": "callbackAfterUserRegisterCommand",
  "users": [
    {
      "userID": "user123",
      "nickname": "John Doe",
      "faceURL": "https://example.com/avatar.jpg",
      "ex": "{\"customField\":\"value\"}",
      "appMangerLevel": 1,
      "globalRecvMsgOpt": 0
    }
  ]
}
```

### After-Registration Webhook Response
```json
{
  "errCode": 0,
  "errMsg": ""
}
```

---

## Configuration

### Webhook Configuration
Located in `config/webhooks.yml` or main config file:

```yaml
webhooks:
  url: "https://your-webhook-url.com/callback"
  beforeUserRegister:
    enable: true
    timeout: 5
  afterUserRegister:
    enable: true
    timeout: 5
```

### Admin User Configuration
The API requires admin access. Admin users are configured in:
- `config.Share.IMAdminUserID` - Array of admin user IDs
- These users have `AppMangerLevel` set to `constant.AppNotificationAdmin`

---

## Related APIs

| API | Purpose |
|-----|---------|
| `/user/get_users_info` | Get user information by user IDs |
| `/user/account_check` | Check if user IDs are already registered |
| `/user/update_user_info` | Update existing user information |
| `/statistics/user/register` | Get user registration statistics |

---

## Error Handling

| Error Code | Error Message | Description |
|------------|---------------|-------------|
| 1001 | `users is empty` | No users provided in request |
| 1001 | `userID repeated` | Duplicate user IDs in request |
| 1001 | `userID is empty` | User ID field is empty |
| 1001 | `userID contains ':' is invalid userID` | Invalid user ID format |
| 1003 | `userID registered already` | User ID already exists in database |
| 1004 | `header must have token` | No authentication token provided |
| 1007 | `permission denied` | User is not an admin |

---

## Architecture Diagram

```
┌─────────────┐
│ HTTP Client │
└──────┬──────┘
       │ POST /user/user_register
       │ (Admin Token Required)
       ▼
┌─────────────────────────────────────┐
│ Step 1: router.go:103             │
│ userRouterGroup.POST(...)          │
└──────┬────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Step 2: user.go:40-42             │
│ UserApi.UserRegister()             │
│ a2r.Call()                        │
└──────┬────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Step 3: a2r (gRPC Client)         │
│ user.UserClient.UserRegister()     │
└──────┬────────────────────────────┘
       │ gRPC
       ▼
┌─────────────────────────────────────┐
│ Step 4: user.go:271-325          │
│ userServer.UserRegister()           │
│  - Validate input                  │
│  - Check admin auth               │
│  - Check duplicates               │
│  - Check if users exist          │
└──────┬────────────────────────────┘
       │
       ├──► ┌──────────────────────────────────┐
       │    │ Step 4.6: Before Webhook (Sync)│
       │    │ webhookBeforeUserRegister()      │
       │    │ callback.go:88-106             │
       │    └──────┬─────────────────────────┘
       │           │ (can modify user data)
       │           ▼
       │    ┌──────────────────────────────────┐
       │    │ Step 4.7: Create Users          │
       │    │ s.db.Create() → MongoDB        │
       │    └──────────────────────────────────┘
       │
       └──► ┌──────────────────────────────────┐
            │ Step 4.9: After Webhook (Async) │
            │ webhookAfterUserRegister()       │
            │ callback.go:108-115             │
            └──────────────────────────────────┘
                 │ (fire and forget)
                 ▼
┌─────────────────────────────────────┐
│ Response: JSON {} (empty on success)│
└─────────────────────────────────────┘
```

---

## File References

| File | Line(s) | Component |
|------|---------|-----------|
| `internal/api/router.go` | 103 | Route definition |
| `internal/api/user.go` | 40-42 | HTTP handler |
| `internal/rpc/user/user.go` | 271-325 | RPC server handler |
| `internal/rpc/user/callback.go` | 88-115 | Webhook callbacks |
| `pkg/callbackstruct/user.go` | 73-90 | Callback structures |
| `pkg/common/config/config.go` | 456-457 | Webhook config definitions |
| `pkg/common/prommetrics/grpc_user.go` | 6-7 | Metrics definition |

---

## Security Considerations

1. **Admin-Only Access:** This API requires admin privileges. Only users listed in `IMAdminUserID` configuration can access it.

2. **Input Validation:**
   - User IDs cannot contain colons (`:`)
   - User IDs must be unique across the system
   - Empty user IDs are rejected

3. **Webhook Security:**
   - Webhook URLs should be HTTPS with proper authentication
   - Use timeout configuration to prevent hanging requests
   - Webhook failures are handled appropriately (sync vs async)

4. **Rate Limiting:** Consider implementing rate limiting at the gateway level to prevent bulk registration abuse.

---

## Best Practices

1. **Batch Registration:** Use the array feature to register multiple users in a single request for better performance.

2. **Webhook Integration:**
   - Use the before-registration webhook for data validation and enrichment
   - Use the after-registration webhook for notifications to other systems (e.g., email systems, CRM)

3. **Error Handling:**
   - Check the response carefully for partial failures
   - Implement retry logic for webhook timeouts
   - Log registration attempts for audit purposes

4. **Metrics Monitoring:**
   - Monitor `user_register_total` Prometheus metric for registration volume
   - Track webhook success/failure rates