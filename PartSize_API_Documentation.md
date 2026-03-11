# PartSize API Processing Documentation

## Overview
The PartSize API calculates the optimal chunk size for multipart file uploads based on the total file size and S3 configuration limits.

---

## Step-by-Step Processing Flow

### Step 1: HTTP Request Reception
**Location:** `internal/api/router.go:217`

```go
objectGroup.POST("/part_size", t.PartSize)
```

- **Endpoint:** `POST /third/object/part_size`
- **Request Body:** Contains file size in bytes (via `third.PartSizeReq`)
- **Authentication:** Requires valid token (processed by `GinParseToken` middleware)

---

### Step 2: HTTP Handler - ThirdApi.PartSize
**Location:** `internal/api/third.go:85-87`

```go
func (o *ThirdApi) PartSize(c *gin.Context) {
    a2r.Call(c, third.ThirdClient.PartSize, o.Client)
}
```

**What happens:**
- Receives the HTTP Gin context
- Delegates to `a2r.Call` which automatically handles:
  - JSON request binding to `third.PartSizeReq`
  - Context propagation
  - gRPC client invocation
  - Response serialization

---

### Step 3: RPC Client Invocation
**Tool:** `github.com/openimsdk/tools/a2r`

The `a2r.Call` function:
1. Extracts user context from Gin middleware (operation ID, user ID, platform)
2. Binds HTTP JSON body to `third.PartSizeReq` protobuf struct
3. Calls the gRPC client method `third.ThirdClient.PartSize`
4. Serializes the `third.PartSizeResp` back to JSON

---

### Step 4: RPC Server Handler
**Location:** `internal/rpc/third/s3.go:52-58`

```go
func (t *thirdServer) PartSize(ctx context.Context, req *third.PartSizeReq) (*third.PartSizeResp, error) {
    size, err := t.s3dataBase.PartSize(ctx, req.Size)
    if err != nil {
        return nil, err
    }
    return &third.PartSizeResp{Size: size}, nil
}
```

**What happens:**
- Extracts file size from request (`req.Size`)
- Delegates to S3 database layer for calculation
- Returns calculated part size in response

---

### Step 5: Database Controller Layer
**Location:** `pkg/common/storage/controller/s3.go:64-66`

```go
func (s *s3Database) PartSize(ctx context.Context, size int64) (int64, error) {
    return s.s3.PartSize(ctx, size)
}
```

**What happens:**
- Acts as an interface adapter
- Forwards to the S3 controller implementation
- The `s.s3` is of type `*cont.Controller` from external S3 library

---

### Step 6: S3 Controller (External Library)
**Library:** `github.com/openimsdk/tools/s3/cont`

The actual calculation logic resides in the external `s3/cont` package:
- Takes the total file size as input
- Uses S3 part limits (MinPartSize, MaxPartSize, MaxNumSize)
- Calculates optimal part size using algorithm:
  - Ensures part count doesn't exceed MaxNumSize
  - Ensures each part is within MinPartSize and MaxPartSize limits
  - Returns calculated part size in bytes

---

### Step 7: Response Flow Back to Client

The response flows back through the same layers:

1. **S3 Controller** → Returns calculated part size (int64)
2. **Database Controller** → Passes through (s3.go:64-66)
3. **RPC Server** → Wraps in `third.PartSizeResp{Size: size}`
4. **gRPC Transport** → Sends response over network
5. **RPC Client** → Receives and deserializes
6. **a2r.Call** → Converts to JSON HTTP response
7. **HTTP Client** → Receives JSON response with part size

---

## API Contract

### Request
```json
{
  "size": 104857600  // Total file size in bytes (e.g., 100MB)
}
```

### Response
```json
{
  "size": 5242880  // Recommended part size in bytes (e.g., 5MB)
}
```

---

## Related APIs

| API | Purpose |
|-----|---------|
| `/third/object/part_limit` | Returns S3 part size limits (MinPartSize, MaxPartSize, MaxNumSize) |
| `/third/object/initiate_multipart_upload` | Initiates multipart upload using the calculated part size |
| `/third/object/auth_sign` | Generates authentication signatures for uploading parts |

---

## Configuration

Part size limits are configured in the S3 backend (MinIO, AWS S3, etc.) and are typically:

| Parameter | Typical Value | Description |
|-----------|---------------|-------------|
| **MinPartSize** | 5MB (5,242,880 bytes) | Minimum allowed part size |
| **MaxPartSize** | 5GB | Maximum allowed part size |
| **MaxNumSize** | 10,000 | Maximum number of parts per upload |

These limits are retrieved via the `PartLimit` API and used by the `PartSize` calculation algorithm.

---

## Architecture Diagram

```
┌─────────────┐
│ HTTP Client │
└──────┬──────┘
       │ POST /third/object/part_size
       ▼
┌─────────────────────────────────────┐
│ Step 1: router.go:217                │
│ objectGroup.POST("/part_size", ...)  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Step 2: third.go:85-87               │
│ ThirdApi.PartSize()                  │
│ a2r.Call()                           │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Step 3: a2r (gRPC Client)           │
│ third.ThirdClient.PartSize()        │
└──────┬──────────────────────────────┘
       │ gRPC
       ▼
┌─────────────────────────────────────┐
│ Step 4: s3.go:52-58 (RPC Server)    │
│ thirdServer.PartSize()              │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Step 5: s3.go:64-66 (Controller)    │
│ s3Database.PartSize()               │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Step 6: s3/cont (External Library)  │
│ Calculate optimal part size         │
└──────┬──────────────────────────────┘
       │ Return part size
       ▼
┌─────────────────────────────────────┐
│ Response: JSON { "size": 5242880 }  │
└─────────────────────────────────────┘
```

---

## File References

| File | Line(s) | Component |
|------|---------|-----------|
| `internal/api/router.go` | 217 | Route definition |
| `internal/api/third.go` | 85-87 | HTTP handler |
| `internal/rpc/third/s3.go` | 52-58 | RPC server handler |
| `pkg/common/storage/controller/s3.go` | 64-66 | Database controller |
| `github.com/openimsdk/tools/s3/cont` | - | S3 controller (external) |

---

## Error Handling

The API returns appropriate errors for:
- Invalid file size (negative or zero)
- File size exceeding maximum upload limits
- S3 backend connection errors
- Configuration errors

Errors are wrapped and returned through the gRPC stack and converted to HTTP error responses by `a2r.Call`.
