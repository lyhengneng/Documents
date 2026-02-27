# Message Sending Flow - Quick Reference

## 📨 The 10-Step Flow

```
1. Client → API Gateway
2. API → Message RPC
3. Validation & Processing
4. Send to Kafka
5. MsgTransfer → Redis (cache)
6. MsgTransfer → MongoDB (storage)
7. Push Service checks online status
8. Online users → WebSocket push
9. Offline users → FCM/APNs push
10. Client receives message
```

## 🔑 Key Files

| Purpose | File Location |
|---------|---------------|
| API Entry | `internal/api/msg.go` |
| Message RPC | `internal/rpc/msg/send.go` |
| Verification | `internal/rpc/msg/verify.go` |
| Kafka Producer | `pkg/common/storage/controller/msg.go` |
| Redis Consumer | `internal/msgtransfer/online_history_msg_handler.go` |
| Mongo Consumer | `internal/msgtransfer/online_msg_to_mongo_handler.go` |
| Push Service | `internal/push/push_handler.go` |
| WebSocket | `internal/msggateway/` |

## 📊 Message Structure

```go
MsgData {
    SendID:      "user123"        // Sender
    RecvID:      "user456"        // Receiver
    Content:     "Hello!"         // Message content
    ContentType: 101              // Text
    SessionType: 1                // SingleChat
    ServerMsgID: "uuid-server"    // Generated
    ClientMsgID: "uuid-client"    // Client provided
    SendTime:    1234567890       // Timestamp
    Seq:         1                // Sequence number
}
```

## ⏱️ Performance

| Metric | Time |
|--------|------|
| API Response | 10-35ms |
| Online Delivery | 20-60ms |
| Offline Delivery | 200-600ms |

## 🐛 Debug Commands

```bash
# View API logs
grep "SendMsg" ./_output/logs/openim-service-log.$(date +%Y-%m-%d)

# View push logs
grep "push" ./_output/logs/openim-service-log.$(date +%Y-%m-%d)

# View errors
grep -i "error" ./_output/logs/openim-service-log.$(date +%Y-%m-%d)
```

## 📝 Message Types

| Type | Value | Description |
|------|-------|-------------|
| Text | 101 | Plain text |
| Picture | 102 | Image |
| Video | 104 | Video |
| File | 105 | File |
| Custom | 107 | Custom |

## 🔧 Session Types

| Type | Value | Description |
|------|-------|-------------|
| SingleChat | 1 | 1-on-1 chat |
| GroupChat | 2 | Group chat |
| Notification | 3 | System notification |

## 💡 Key Points

✅ **Async Processing** - API returns fast, delivery in background
✅ **Kafka Queue** - No message loss
✅ **Redis Cache** - Fast access
✅ **MongoDB** - Permanent storage
✅ **WebSocket** - Real-time online push
✅ **FCM/APNs** - Offline push

## 🚨 Troubleshooting

**Message not delivered?**
1. Check API logs - did it reach server?
2. Check Kafka - is it queued?
3. Check Redis/MongoDB - is it stored?
4. Check Push logs - was push attempted?
5. Check online status - is user online?

---

**Full Documentation:** See `MESSAGE_SENDING_FLOW.md`
