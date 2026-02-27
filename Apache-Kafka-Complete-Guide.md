# Apache Kafka - Complete Guide

## Table of Contents
- [What is Apache Kafka?](#what-is-apache-kafka)
- [Core Concepts](#core-concepts)
- [Kafka Architecture](#kafka-architecture)
- [How Kafka Works](#how-kafka-works)
- [Kafka vs Other Messaging Systems](#kafka-vs-other-messaging-systems)
- [When to Use Kafka](#when-to-use-kafka)
- [Practical Examples](#practical-examples)
- [Best Practices](#best-practices)
- [Operations & Monitoring](#operations--monitoring)

---

## What is Apache Kafka?

**Apache Kafka** is a distributed event streaming platform capable of handling trillions of events per day. Initially conceived at LinkedIn and open-sourced in 2011, it has become the de facto standard for building real-time data pipelines and streaming applications.

### What is Event Streaming?

**Event streaming** is the practice of capturing data in real-time from event sources like databases, sensors, mobile devices, cloud services, and software applications in the form of streams of events; storing these event streams durably for later retrieval; manipulating, processing, and reacting to the event streams in real-time as well as retrospectively; and routing the event streams to different destination technologies.

### Key Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                    KAFKA CHARACTERISTICS                        │
├─────────────────────────────────────────────────────────────────┤
│  ⚡ High Throughput   ──►  Millions of messages per second      │
│  📈 Scalable          ──►  Horizontal scaling with partitions   │
│  💾 Durable           ──►  Messages persisted to disk           │
│  🔄 Distributed       ──►  Replicated across multiple nodes     │
│  ⏱️ Real-time         ──►  Millisecond latency                  │
│  🎯 Fault Tolerant    ──►  Automatic leader election            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Topics

A **Topic** is a specific stream of data. It's like a category or feed name to which records are published.

```
Topic: "user-events"
├── Partition 0
│   ├── [Message 1] Offset 0
│   ├── [Message 2] Offset 1
│   └── [Message 3] Offset 2
├── Partition 1
│   ├── [Message 1] Offset 0
│   └── [Message 2] Offset 1
└── Partition 2
    └── [Message 1] Offset 0
```

**Key Points:**
- Topics are partitioned (split into multiple parts)
- Each partition is an ordered, immutable sequence of messages
- Messages in a partition are assigned a sequential ID called an **offset**
- Once written, data cannot be modified (append-only)

### 2. Producers

A **Producer** is an application that sends (publishes) records to a Kafka topic.

```
┌─────────────┐
│  Producer   │
│  (Sender)   │
└──────┬──────┘
       │
       │ 1. Send message
       ▼
┌─────────────┐
│ Kafka Topic │
└─────────────┘
```

**Producer Responsibilities:**
- Decide which topic to send to
- Decide which partition (can use load balancing)
- Compress messages
- Handle acknowledgments from brokers

### 3. Consumers

A **Consumer** is an application that reads (subscribes to) records from Kafka topics.

```
┌─────────────┐
│ Kafka Topic │
└──────┬──────┘
       │
       │ 2. Read messages
       ▼
┌─────────────┐
│  Consumer   │
│  (Reader)   │
└─────────────┘
```

**Consumer Responsibilities:**
- Subscribe to one or more topics
- Process messages
- Track which messages have been consumed (offsets)
- Handle failures and retries

### 4. Consumer Groups

A **Consumer Group** is a set of consumers that cooperate to consume a topic.

```
Topic: "orders" (3 partitions)
├── Partition 0 ─────┐
├── Partition 1 ─────┼──► Consumer Group A (3 consumers)
└── Partition 2 ─────┘
                        │
                        │ Each consumer reads from 1+ partitions
                        │
                        ▼
        ┌───────────────┴───────────────┐
        │  Consumer 1 │ Consumer 2 │ Consumer 3 │
        └───────────────────────────────────────┘
```

**Key Rules:**
- Each partition is consumed by exactly one consumer in a group
- If a consumer fails, its partitions are reassigned
- Enables parallel processing and scalability

### 5. Brokers

A **Broker** is a Kafka server. A Kafka cluster consists of multiple brokers.

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Broker 1 │  │ Broker 2 │  │ Broker 3 │
│  (Node)  │  │  (Node)  │  │  (Node)  │
└──────────┘  └──────────┘  └──────────┘
     │             │              │
     └─────────────┴──────────────┘
                   │
            Kafka Cluster
```

### 6. Partitions

**Partitions** allow a topic to be split across multiple brokers for scalability.

```
Topic: "user-clicks" (3 partitions, 3 brokers)

Broker 1          Broker 2          Broker 3
│                  │                  │
├─ Partition 0     ├─ Partition 1     ├─ Partition 2
│  Msg 1           │  Msg 1           │  Msg 1
│  Msg 2           │  Msg 2           │  Msg 2
│  Msg 3           │  Msg 3           │  Msg 3
```

**Benefits of Partitioning:**
- **Parallelism**: Multiple consumers can read in parallel
- **Scalability**: Distribute load across multiple servers
- **Performance**: Faster reads and writes

### 7. Replication

**Replication** copies partitions across multiple brokers for fault tolerance.

```
Replication Factor: 3

Partition 0
├── Leader (Broker 1) ────────┐
├── Replica (Broker 2) ───────┤
└── Replica (Broker 3) ───────┘
                              │
                    If Broker 1 fails,
                    Broker 2 or 3 becomes leader
```

---

## Kafka Architecture

### Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        KAFKA CLUSTER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │
│  │  Broker 1   │    │  Broker 2   │    │  Broker 3   │                │
│  │             │    │             │    │             │                │
│  │ Topic A:    │    │ Topic A:    │    │ Topic B:    │                │
│  │ - P0 (L)    │    │ - P0 (R)    │    │ - P2 (L)    │                │
│  │ - P1 (L)    │    │ - P2 (R)    │    │ - P3 (L)    │                │
│  │ Topic B:    │    │ Topic B:    │    │ Topic A:    │                │
│  │ - P2 (R)    │    │ - P3 (R)    │    │ - P0 (R)    │                │
│  │ - P3 (R)    │    │ Topic A:    │    │ - P1 (R)    │                │
│  └─────────────┘    │ - P1 (R)    │    └─────────────┘                │
│                     └─────────────┘                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ▲           │
                              │           │
┌─────────────────────────────┘           └─────────────────────────────┐
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐      ┌─────────────┐  ┌─────────────┐│
│  │  Producer 1 │  │  Producer 2 │      │ Consumer 1  │  │ Consumer 2  ││
│  │  (Web App)  │  │  (Mobile)   │      │  (Analytics)│  │ (Database)  ││
│  └─────────────┘  └─────────────┘      └─────────────┘  └─────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Legend: L = Leader, R = Replica
```

### Message Flow

```
1. PRODUCER SENDS MESSAGE
   Producer → Broker → Partition (Leader)

2. REPLICATION
   Partition (Leader) → Partition (Replica 1)
   Partition (Leader) → Partition (Replica 2)

3. ACKNOWLEDGMENT
   Partition (Replica) → Broker → Producer

4. CONSUMER READS MESSAGE
   Consumer → Broker → Partition (Leader)
```

---

## How Kafka Works

### Publishing Messages

```go
// Producer sends a message
message := {
    topic: "user-events",
    key: "user123",           // Optional: determines partition
    value: {
        "user_id": "user123",
        "action": "click",
        "timestamp": 1709251200
    },
    headers: {
        "content-type": "application/json"
    }
}

// Kafka calculates partition:
// - If key exists: hash(key) % num_partitions
// - If no key: round-robin or sticky partitioner

// Result: Message sent to Partition 1
```

### Consuming Messages

```go
// Consumer joins a consumer group
consumer = Consumer(group_id: "analytics-group")

consumer.subscribe(["user-events"])

// Kafka assigns partitions to consumers
// Partition 0 → Consumer 1
// Partition 1 → Consumer 2
// Partition 2 → Consumer 3

// Poll loop
while true {
    messages = consumer.poll(timeout=100ms)

    for message in messages {
        process(message)
        consumer.commit(message.offset)
    }
}
```

### Offset Management

**Offset**: The position of a consumer in a partition

```
Partition 0:
Offset 0: Message A
Offset 1: Message B
Offset 2: Message C
Offset 3: Message D
Offset 4: Message E
            ↑
            Current offset (consumed up to here)

Next poll will start from Offset 4
```

**Offset Storage Options:**

1. **Kafka Managed (Default)**
   - Offsets stored in a special Kafka topic: `__consumer_offsets`
   - Automatic periodic commits

2. **Custom Storage**
   - Store offsets in your own database
   - Exactly-once processing semantics
   - More control, more responsibility

---

## Kafka vs Other Messaging Systems

### Comparison Table

| Feature | Kafka | RabbitMQ | Redis Pub/Sub | AWS SQS |
|---------|-------|----------|---------------|---------|
| **Messaging Model** | Streaming | Queue/Topic | Pub/Sub | Queue |
| **Throughput** | Very High | Medium | High | Medium |
| **Latency** | Milliseconds | Microseconds | Microseconds | Tens of ms |
| **Durability** | Disk-based | Disk/Memory | Memory (optional) | Disk |
| **Scalability** | Horizontal | Vertical | Horizontal | Horizontal |
| **Consumer Model** | Pull | Push | Push | Pull |
| **Message Replay** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Ordering** | Per partition | Per queue | No | Best effort |
| **Learning Curve** | Medium | Easy | Easy | Easy |
| **Use Case** | Event streaming | Work queues | Real-time | Decoupling |

### When to Choose What?

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISION TREE                            │
└─────────────────────────────────────────────────────────────┘

Need to replay messages?
├── Yes → Kafka
└── No
    ├── Need complex routing?
    │   ├── Yes → RabbitMQ
    │   └── No
    │       ├── Simple pub/sub?
    │       │   ├── Yes → Redis
    │       │   └── No → SQS
    │       └── High throughput required?
    │           └── Yes → Kafka

Need guaranteed delivery?
├── Yes → RabbitMQ or SQS
└── No → Kafka or Redis

Need stream processing?
├── Yes → Kafka + Kafka Streams
└── No → Any
```

---

## When to Use Kafka

### Perfect Use Cases ✅

#### 1. Event Sourcing
```
User Service        →  Kafka (user-events topic)  →  Read Model
                      │
                      ├─► Email Service
                      ├─► Analytics Service
                      └─► Notification Service
```

**Why Kafka?**
- All services get the same events
- Can replay events to rebuild state
- Immutable audit log

#### 2. Log Aggregation
```
Application Servers → Kafka (logs topic) → Log Processor → Elasticsearch
                                                       → S3 (archive)
                                                       → Monitoring
```

**Why Kafka?**
- High throughput for massive log volumes
- Durable storage
- Multiple consumers

#### 3. Real-Time Analytics
```
IoT Devices → Kafka (sensor-data) → Stream Processing → Dashboard
                                                    → Alerts
                                                    → ML Models
```

**Why Kafka?**
- Real-time processing with Kafka Streams
- Windowed aggregations
- Joins and transformations

#### 4. Microservices Communication
```
┌─────────────┐     Kafka     ┌─────────────┐
│   Service A │ ─────────────►│   Service B │
└─────────────┘               └─────────────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │   Service C │
                            └─────────────┘
```

**Why Kafka?**
- Decouples services
- Asynchronous communication
- Backpressure handling

#### 5. Data Pipeline
```
Database CDC → Kafka → Transform → Data Warehouse
                              → Cache Invalidation
                              → Search Index
```

**Why Kafka?**
- Connects disparate systems
- Reliable data transport
- Supports multiple consumers

### Bad Use Cases ❌

#### 1. Simple Work Queue
```
❌ Don't use Kafka for:
   - Simple task processing
   - Request/response pattern
   - Low-volume messaging

✅ Use instead:
   - RabbitMQ
   - Redis
   - Sidekiq/Bull Queue
```

#### 2. Long-Term Storage
```
❌ Don't use Kafka for:
   - Storing data forever
   - Database replacement
   - Document archive

✅ Use instead:
   - S3
   - Database
   - Dedicated storage
```

#### 3. Small-Scale Projects
```
❌ Don't use Kafka for:
   - Personal projects
   - Low traffic (<1000 msg/sec)
   - Simple pub/sub

✅ Use instead:
   - Redis
   - Postgres LISTEN/NOTIFY
   - Cloud Pub/Sub
```

---

## Practical Examples

### Example 1: Producer in Go

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "time"

    "github.com/segmentio/kafka-go"
)

// UserEvent represents a user action event
type UserEvent struct {
    UserID    string    `json:"user_id"`
    Action    string    `json:"action"`
    Timestamp time.Time `json:"timestamp"`
    Metadata  map[string]string `json:"metadata,omitempty"`
}

func main() {
    // Create a Kafka writer
    writer := kafka.NewWriter(kafka.WriterConfig{
        Brokers:  []string{"localhost:9092"},
        Topic:    "user-events",
        Balancer: &kafka.LeastBytes{}, // Distribute messages by size
        // Async:    true, // Enable async writes for better performance
    })

    defer writer.Close()

    // Produce messages
    events := []UserEvent{
        {
            UserID:    "user123",
            Action:    "page_view",
            Timestamp: time.Now(),
            Metadata:  map[string]string{"page": "/home"},
        },
        {
            UserID:    "user456",
            Action:    "click",
            Timestamp: time.Now(),
            Metadata:  map[string]string{"element": "button"},
        },
        {
            UserID:    "user123",
            Action:    "purchase",
            Timestamp: time.Now(),
            Metadata:  map[string]string{"amount": "99.99"},
        },
    }

    for _, event := range events {
        // Marshal event to JSON
        value, err := json.Marshal(event)
        if err != nil {
            log.Printf("Failed to marshal event: %v", err)
            continue
        }

        // Create message with key for ordering per user
        message := kafka.Message{
            Key:   []byte(event.UserID), // Ensures same user goes to same partition
            Value: value,
            Time:  time.Now(),
        }

        // Send message
        ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
        err = writer.WriteMessages(ctx, message)
        cancel()

        if err != nil {
            log.Printf("Failed to write message: %v", err)
        } else {
            log.Printf("✓ Sent event: %s - %s", event.UserID, event.Action)
        }
    }
}
```

### Example 2: Consumer in Go

```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "time"

    "github.com/segmentio/kafka-go"
)

type UserEvent struct {
    UserID    string                 `json:"user_id"`
    Action    string                 `json:"action"`
    Timestamp time.Time              `json:"timestamp"`
    Metadata  map[string]string      `json:"metadata,omitempty"`
}

func main() {
    // Create a Kafka reader (consumer)
    reader := kafka.NewReader(kafka.ReaderConfig{
        Brokers:  []string{"localhost:9092"},
        GroupID:  "analytics-consumer-group", // Consumer group for scalability
        Topic:    "user-events",
        MinBytes: 10e3, // 10KB
        MaxBytes: 10e6, // 10MB
        // StartOffset: kafka.FirstOffset, // Read from beginning
        // StartOffset: kafka.LastOffset,  // Read only new messages
    })

    defer reader.Close()

    log.Println("🚀 Consumer started. Waiting for messages...")

    for {
        // Read message with timeout
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        message, err := reader.ReadMessage(ctx)
        cancel()

        if err != nil {
            // Check if it's just a timeout
            if err.Error() == "context deadline exceeded" {
                continue
            }
            log.Printf("Error reading message: %v", err)
            break
        }

        // Parse the message
        var event UserEvent
        if err := json.Unmarshal(message.Value, &event); err != nil {
            log.Printf("Failed to unmarshal message: %v", err)
            continue
        }

        // Process the event
        processEvent(event, message)

        // Commit offset (auto-commit is enabled by default)
        // reader.CommitMessage(message) // Manual commit if needed
    }
}

func processEvent(event UserEvent, message kafka.Message) {
    // Increment metrics
    incrementCounter(event.Action)

    // Log the event
    log.Printf("📊 Partition: %d | Offset: %d | User: %s | Action: %s",
        message.Partition, message.Offset, event.UserID, event.Action)

    // Process different actions
    switch event.Action {
    case "page_view":
        trackPageView(event)
    case "click":
        trackClick(event)
    case "purchase":
        trackPurchase(event)
    default:
        log.Printf("Unknown action: %s", event.Action)
    }
}

func incrementCounter(action string) {
    // In real implementation, send to Prometheus/DataDog
}

func trackPageView(event UserEvent) {
    log.Printf("  → Page view tracked: %s", event.Metadata["page"])
}

func trackClick(event UserEvent) {
    log.Printf("  → Click tracked: %s", event.Metadata["element"])
}

func trackPurchase(event UserEvent) {
    log.Printf("  → 💰 Purchase tracked: %s", event.Metadata["amount"])
}
```

### Example 3: Advanced Producer with Configuration

```go
package main

import (
    "context"
    "crypto/tls"
    "log"
    "time"

    "github.com/segmentio/kafka-go"
    "github.com/segmentio/kafka-go/sasl"
    "github.com/segmentio/kafka-go/sasl/scram"
)

type Producer struct {
    writer *kafka.Writer
}

func NewProducer(brokers []string, topic string, tlsConfig *tls.Config) *Producer {
    config := kafka.WriterConfig{
        Brokers: brokers,
        Topic:   topic,
        // Performance tuning
        BatchSize:        100,           // Batch messages together
        BatchTimeout:     10 * time.Millisecond,
        Compression:      kafka.Snappy,  // Compress batches
        Balancer:         &kafka.Murmur2Balancer{}, // Consistent hashing
        // Delivery guarantees
        RequiredAcks:     kafka.RequireAll, // Wait for all replicas
        MaxAttempts:      5,                // Retry failed sends
        // Async writes
        Async:            false, // Set to true for fire-and-forget
    }

    // Add SASL authentication if provided
    if tlsConfig != nil {
        config.Transport = &kafka.Transport{
            TLS: tlsConfig,
            SASL: saslMechanism(),
        }
    }

    return &Producer{
        writer: kafka.NewWriter(config),
    }
}

func saslMechanism() sasl.Mechanism {
    // SASL/SCRAM authentication (common in cloud Kafka)
    mechanism, err := scram.Mechanism(scram.SHA512, "username", "password")
    if err != nil {
        log.Fatal(err)
    }
    return mechanism
}

func (p *Producer) ProduceMessage(key, value []byte) error {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    return p.writer.WriteMessages(ctx, kafka.Message{
        Key:   key,
        Value: value,
        Headers: []kafka.Header{
            {Key: "producer", Value: []byte("my-service")},
            {Key: "version", Value: []byte("1.0.0")},
        },
    })
}

func (p *Producer) Close() error {
    return p.writer.Close()
}
```

### Example 4: Consumer Group with Manual Commit

```go
package main

import (
    "context"
    "log"
    "time"

    "github.com/segmentio/kafka-go"
)

func main() {
    reader := kafka.NewReader(kafka.ReaderConfig{
        Brokers:  []string{"localhost:9092"},
        GroupID:  "payment-processor",
        Topic:    "payment-events",
        // Manual commit control
        CommitInterval: 0, // Disable auto-commit
    })
    defer reader.Close()

    for {
        message, err := reader.ReadMessage(context.Background())
        if err != nil {
            log.Printf("Read error: %v", err)
            break
        }

        // Process the message
        if err := processPayment(message.Value); err != nil {
            // Handle processing error
            log.Printf("Processing failed: %v", err)
            // Don't commit - will retry
            continue
        }

        // Manually commit only after successful processing
        if err := reader.CommitMessages(context.Background(), message); err != nil {
            log.Printf("Commit error: %v", err)
        }
    }
}

func processPayment(data []byte) error {
    // Simulate payment processing
    log.Printf("Processing payment: %s", string(data))
    time.Sleep(100 * time.Millisecond)
    return nil
}
```

### Example 5: Kafka Streams (Go with ksqlDB-like functionality)

```go
package main

import (
    "context"
    "encoding/json"
    "log"
    "time"

    "github.com/segmentio/kafka-go"
)

// StreamProcessor processes messages and produces to output topic
type StreamProcessor struct {
    reader *kafka.Reader
    writer *kafka.Writer
}

type OrderEvent struct {
    OrderID   string  `json:"order_id"`
    UserID    string  `json:"user_id"`
    Amount    float64 `json:"amount"`
    Status    string  `json:"status"`
    Timestamp int64   `json:"timestamp"`
}

type OrderSummary struct {
    UserID       string  `json:"user_id"`
    TotalOrders  int     `json:"total_orders"`
    TotalAmount  float64 `json:"total_amount"`
    LastOrderAt  int64   `json:"last_order_at"`
}

func main() {
    processor := StreamProcessor{
        reader: kafka.NewReader(kafka.ReaderConfig{
            Brokers: []string{"localhost:9092"},
            Topic:   "orders",
            GroupID: "order-aggregator",
        }),
        writer: kafka.NewWriter(kafka.WriterConfig{
            Brokers: []string{"localhost:9092"},
            Topic:   "order-summaries",
        }),
    }
    defer processor.reader.Close()
    defer processor.writer.Close()

    processor.ProcessStream()
}

func (sp *StreamProcessor) ProcessStream() {
    userState := make(map[string]*OrderSummary)

    for {
        message, err := sp.reader.ReadMessage(context.Background())
        if err != nil {
            log.Printf("Read error: %v", err)
            continue
        }

        var order OrderEvent
        if err := json.Unmarshal(message.Value, &order); err != nil {
            log.Printf("Unmarshal error: %v", err)
            continue
        }

        // Aggregate data per user
        summary, exists := userState[order.UserID]
        if !exists {
            summary = &OrderSummary{
                UserID: order.UserID,
            }
        }

        summary.TotalOrders++
        summary.TotalAmount += order.Amount
        summary.LastOrderAt = order.Timestamp
        userState[order.UserID] = summary

        // Emit updated summary
        sp.emitSummary(summary)

        log.Printf("✓ Processed order %s for user %s",
            order.OrderID, order.UserID)
    }
}

func (sp *StreamProcessor) emitSummary(summary *OrderSummary) {
    value, _ := json.Marshal(summary)

    sp.writer.WriteMessages(context.Background(), kafka.Message{
        Key:   []byte(summary.UserID),
        Value: value,
    })
}
```

### Example 6: Multi-Topic Consumer

```go
package main

import (
    "context"
    "log"

    "github.com/segmentio/kafka-go"
)

// Consume from multiple topics
func main() {
    reader := kafka.NewReader(kafka.ReaderConfig{
        Brokers:  []string{"localhost:9092"},
        GroupID:  "multi-topic-consumer",
        // Read from multiple topics
        Topic:    "", // Don't set topic
        // Will use ReadPartitions to dynamically fetch
    })
    defer reader.Close()

    topics := []string{"user-events", "order-events", "payment-events"}

    // Connect to all topics
    for _, topic := range topics {
        if err := reader.ChangeTopic(topic); err != nil {
            log.Printf("Failed to connect to topic %s: %v", topic, err)
        }
    }

    // Process messages from all topics
    for {
        message, err := reader.ReadMessage(context.Background())
        if err != nil {
            log.Printf("Error: %v", err)
            continue
        }

        log.Printf("Topic: %s | Partition: %d | Message: %s",
            message.Topic, message.Partition, string(message.Value))

        // Route to appropriate handler
        switch message.Topic {
        case "user-events":
            handleUserEvent(message)
        case "order-events":
            handleOrderEvent(message)
        case "payment-events":
            handlePaymentEvent(message)
        }
    }
}

func handleUserEvent(msg kafka.Message) {
    log.Printf("Handling user event...")
}

func handleOrderEvent(msg kafka.Message) {
    log.Printf("Handling order event...")
}

func handlePaymentEvent(msg kafka.Message) {
    log.Printf("Handling payment event...")
}
```

---

## Best Practices

### 1. Topic Naming

✅ **Good Names:**
```
user-events
order.created
payment.processed
clickstream.raw
metrics.service-name
```

❌ **Bad Names:**
```
data1
events
myTopic
user_events_v2_final_real
```

**Guidelines:**
- Use lowercase with hyphens or dots
- Be descriptive and specific
- Use a consistent naming convention
- Include environment: `prod.user-events`, `dev.user-events`

### 2. Partitioning Strategy

```go
// Key-based partitioning (preserves order per key)
message := kafka.Message{
    Key: []byte(userID), // Same user always goes to same partition
    Value: data,
}

// Round-robin (better distribution, no ordering)
message := kafka.Message{
    Value: data, // No key = round-robin
}

// Custom partitioner
type CustomPartitioner struct{}

func (p *CustomPartitioner) Partition(msg *kafka.Message) int {
    // Custom logic
    return hash(msg.Key) % numPartitions
}
```

**Choosing Partition Count:**
```
Throughput per partition: ~10-100 MB/s
Calculate based on desired throughput:

Desired throughput: 1 GB/s
Per partition:      100 MB/s
────────────────────────────
Partitions needed:  10

Rule of thumb: Start with 3-6 partitions per topic,
scale based on consumer count
```

### 3. Message Size

```
Ideal message size: 1 KB - 1 MB

Too small (< 1 KB):
├── Overhead from headers
├── Network inefficiency
└── Too many requests

Too large (> 10 MB):
├── Memory pressure
├── GC issues
├── Slow recovery
└── Consumer buffer bloat

Solution: Batch or chunk large messages
```

### 4. Consumer Configuration

```go
reader := kafka.NewReader(kafka.ReaderConfig{
    Brokers:  []string{"localhost:9092"},
    Topic:    "events",
    GroupID:  "my-group",

    // Important settings
    MinBytes:  1e3,  // 1 KB - minimum fetch size
    MaxBytes:  10e6, // 10 MB - maximum fetch size

    // Fetch more data per poll
    MinWait:   100 * time.Millisecond, // Wait for batch

    // Balance latency vs throughput
    CommitInterval: time.Second, // How often to commit

    // Where to start reading
    StartOffset: kafka.LastOffset, // or kafka.FirstOffset

    // Keep partition assignment
    WatchPartitionChanges: false,
})
```

### 5. Error Handling

```go
func safeConsume(reader *kafka.Reader) {
    for {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        message, err := reader.ReadMessage(ctx)
        cancel()

        if err != nil {
            // Handle different error types
            switch {
            case errors.Is(err, context.DeadlineExceeded):
                // Timeout - normal, continue
                continue
            case errors.Is(err, kafka.ErrGenerationEnded):
                // Generation ended - rebalancing
                log.Println("Rebalancing...")
                time.Sleep(time.Second)
            default:
                log.Printf("Fatal error: %v", err)
                return
            }
            continue
        }

        // Process with retry
        if err := processWithRetry(message, 3); err != nil {
            log.Printf("Failed after retries: %v", err)
            // Send to DLQ (Dead Letter Queue)
            sendToDLQ(message)
        }
    }
}

func processWithRetry(msg kafka.Message, maxRetries int) error {
    var err error
    for i := 0; i < maxRetries; i++ {
        if err = processMessage(msg); err == nil {
            return nil
        }
        time.Sleep(time.Duration(i) * time.Second)
    }
    return err
}
```

### 6. Monitoring

```go
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    messagesConsumed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "kafka_messages_consumed_total",
            Help: "Total messages consumed",
        },
        []string{"topic", "partition"},
    )

    consumeErrors = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "kafka_consumer_errors_total",
            Help: "Total consumer errors",
        },
        []string{"topic"},
    )

    consumeLatency = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "kafka_consume_latency_seconds",
            Help:    "Time to process messages",
            Buckets: prometheus.DefBuckets,
        },
        []string{"topic"},
    )
)

func trackConsumption(topic string, partition int) {
    messagesConsumed.WithLabelValues(topic, fmt.Sprint(partition)).Inc()
}

func trackError(topic string) {
    consumeErrors.WithLabelValues(topic).Inc()
}

func trackLatency(topic string, duration time.Duration) {
    consumeLatency.WithLabelValues(topic).Observe(duration.Seconds())
}
```

### 7. Dead Letter Queue (DLQ)

```go
type DLQHandler struct {
    writer *kafka.Writer
}

func NewDLQHandler(brokers []string) *DLQHandler {
    return &DLQHandler{
        writer: kafka.NewWriter(kafka.WriterConfig{
            Brokers: brokers,
            Topic:   "dead-letter-queue",
        }),
    }
}

func (dlq *DLQHandler) SendToDLQ(originalMsg kafka.Message, err error) {
    dlqRecord := struct {
        OriginalTopic string        `json:"original_topic"`
        OriginalValue []byte        `json:"original_value"`
        Error         string        `json:"error"`
        Timestamp     time.Time     `json:"timestamp"`
    }{
        OriginalTopic: originalMsg.Topic,
        OriginalValue: originalMsg.Value,
        Error:         err.Error(),
        Timestamp:     time.Now(),
    }

    value, _ := json.Marshal(dlqRecord)

    dlq.writer.WriteMessages(context.Background(), kafka.Message{
        Value: value,
    })
}
```

---

## Operations & Monitoring

### 1. Kafka CLI Commands

```bash
# List topics
kafka-topics.sh --list --bootstrap-server localhost:9092

# Create topic
kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --topic user-events \
  --partitions 3 \
  --replication-factor 2

# Describe topic
kafka-topics.sh --describe \
  --bootstrap-server localhost:9092 \
  --topic user-events

# Delete topic
kafka-topics.sh --delete \
  --bootstrap-server localhost:9092 \
  --topic user-events

# Produce messages
kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic user-events

# Consume messages
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic user-events \
  --from-beginning

# List consumer groups
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --list

# Describe consumer group
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group my-group \
  --describe

# Get consumer group lag
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group my-group \
  --describe
```

### 2. Important Metrics to Monitor

```
Consumer Metrics:
├── consumer-lag (most important!)
├── consumer-rate
├── consumer-latency
└── consumer-errors

Producer Metrics:
├── producer-rate
├── producer-latency
├── producer-errors
└── producer-retries

Broker Metrics:
├── Under-replicated partitions
├── Offline partitions
├── Active controllers
├── Request handler idle ratio
└── Network throughput
```

### 3. Consumer Lag

```
Consumer Lag = Latest Offset - Consumer Offset

                    Latest Offset (1000)
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    │  Processed         │  Not Processed     │
    │  (Safe)            │  (Lag)             │
    │                    │                    │
    └────────────────────┼────────────────────┘
                         │
                   Consumer Offset (800)

Lag = 200 messages

Why it matters:
├── Lag growing → Consumer too slow
├── High lag → Delayed processing
├── Lag = 0 → Consumer caught up
└── Negative lag → Consumer issue
```

### 4. Health Checks

```go
func checkKafkaHealth(brokers []string) error {
    conn, err := kafka.Dial("tcp", brokers[0])
    if err != nil {
        return fmt.Errorf("failed to connect: %w", err)
    }
    defer conn.Close()

    // Check controller
    controller, err := conn.Controller()
    if err != nil {
        return fmt.Errorf("failed to get controller: %w", err)
    }

    // Check broker availability
    if controller == nil {
        return fmt.Errorf("no controller available")
    }

    return nil
}
```

---

## Kafka in Open-IM Context

### Typical Open-IM Architecture with Kafka

```
┌─────────────┐
│  Client App │
└──────┬──────┘
       │ WebSocket
       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Open-IM Gateway                          │
└─────────────────────────────────────────────────────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  ┌─────────┐         ┌─────────┐         ┌─────────┐
  │  Push   │         │ Message │         │  Auth   │
  │ Service │         │ Service │         │ Service │
  └────┬────┘         └────┬────┘         └────┬────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │        KAFKA           │
              ├───────────────────────┤
              │ topic: msg-gateway    │
              │ topic: push-msg       │
              │ topic: offline-msg    │
              │ topic: notification   │
              └───────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
        ┌─────────┐              ┌─────────┐
        │ Storage │              │  Sync   │
        │ Service │              │ Service │
        └─────────┘              └─────────┘
```

### Message Flow Example

```
1. User sends message
   Client → Gateway

2. Gateway publishes to Kafka
   Gateway → Kafka (msg-gateway topic)

3. Message Service processes
   Kafka → Message Service
   ├─ Save to MongoDB
   ├─ Ack to user
   └─ Publish to push-msg topic

4. Push Service handles delivery
   Kafka → Push Service
   ├─ User online? → Push via WebSocket
   └─ User offline? → Send push notification
```

---

## Security Best Practices

### 1. Authentication (SASL)

```go
mechanism, _ := scram.Mechanism(
    scram.SHA512,
    "username",
    "password",
)

dialer := &kafka.Dialer{
    Timeout:   10 * time.Second,
    DualStack: true,
    SASL:      mechanism,
}
```

### 2. Encryption (TLS)

```go
dialer := &kafka.Dialer{
    TLS: &tls.Config{
        InsecureSkipVerify: false, // Always verify in production
    },
}
```

### 3. Authorization (ACLs)

```bash
# Create ACL
kafka-acls.sh --bootstrap-server localhost:9092 \
  --add \
  --allow-principal User:producer-app \
  --operation Write \
  --topic user-events

# Remove ACL
kafka-acls.sh --bootstrap-server localhost:9092 \
  --remove \
  --allow-principal User:producer-app \
  --operation Write \
  --topic user-events
```

---

## Common Pitfalls and Solutions

### 1. Consumer Not Reading

```go
// Problem: Context with timeout too short
ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
message, err := reader.ReadMessage(ctx)
// Always times out!

// Solution: Use longer timeout or no timeout
message, err := reader.ReadMessage(context.Background())
```

### 2. Offset Commit Issues

```go
// Problem: Auto-commit before processing completes
// Consumer crashes after commit but before processing
// Data lost!

// Solution: Manual commit after processing
message, _ := reader.ReadMessage(ctx)
processMessage(message)
reader.CommitMessages(ctx, message) // Commit only after success
```

### 3. Producer Blocking

```go
// Problem: Synchronous writes block
writer.WriteMessages(ctx, message) // Blocks until ack

// Solution: Async writes or separate goroutines
writer := kafka.NewWriter(kafka.WriterConfig{
    Async: true, // Fire and forget
})

// Or use goroutine with channels
go func() {
    writer.WriteMessages(ctx, message)
}()
```

### 4. Memory Issues

```go
// Problem: Reading too many messages at once
reader := kafka.NewReader(kafka.ReaderConfig{
    MinBytes: 100 * 1024 * 1024, // 100 MB per fetch!
})

// Solution: Reasonable batch sizes
reader := kafka.NewReader(kafka.ReaderConfig{
    MinBytes: 10 * 1024,   // 10 KB
    MaxBytes: 10 * 1024 * 1024, // 10 MB max
})
```

---

## Performance Tuning

### Producer Tuning

```go
config := kafka.WriterConfig{
    // Batch more messages
    BatchSize:    1000,           // Messages per batch
    BatchTimeout: 10 * time.Millisecond,

    // Compression
    Compression: kafka.Snappy,    // or gzip, lz4, zstd

    // Acknowledgment
    RequiredAcks: kafka.RequireOne,  // 1 = leader only
                                        // all = all replicas
                                        // 0 = no ack (fastest, least safe)

    // Network
    ReadTimeout:  10 * time.Second,
    WriteTimeout: 10 * time.Second,
}
```

### Consumer Tuning

```go
config := kafka.ReaderConfig{
    // Fetch more data per poll
    MinBytes: 1e3,        // 1 KB minimum
    MaxBytes: 10e6,       // 10 MB maximum
    MaxWait:  500 * time.Millisecond,

    // Prefetch
    CommitInterval: time.Second,

    // Start position
    StartOffset: kafka.LastOffset,
}
```

### Broker Tuning

```properties
# server.properties

# Thread tuning
num.network.threads=8
num.io.threads=16

# Socket buffers
socket.send.buffer.bytes=102400
socket.receive.buffer.bytes=102400
socket.request.max.bytes=104857600

# Log flush
log.flush.interval.messages=10000
log.flush.interval.ms=1000

# Replication
num.replica.fetchers=4
replica.fetch.max.bytes=1048576
```

---

## Summary

### Key Takeaways

1. **Kafka is for streaming** - Think of it as a distributed commit log
2. **Topics are like categories** - Partition them for parallel processing
3. **Producers write, consumers read** - They don't know about each other
4. **Consumer groups enable scalability** - Each partition consumed by one consumer
5. **Offsets track position** - Enable replay and at-least-once semantics
6. **Replication provides durability** - Survive broker failures
7. **Monitor consumer lag** - Most important metric
8. **Design for failure** - Use DLQ, retries, and idempotent consumers

### When to Use Kafka Checklist

✅ Use Kafka when you need:
- High throughput (>10K messages/sec)
- Multiple consumers for same data
- Message replay capability
- Stream processing
- Event sourcing
- Log aggregation

❌ Don't use Kafka when:
- Simple work queue needed
- Low message volume
- Request/response pattern
- Need complex routing per message
- Team lacks Kafka expertise
- Simple pub/sub suffices

### Learning Path

1. **Start with basics**: Understand topics, partitions, producers, consumers
2. **Run locally**: Use Docker Compose for development
3. **Build simple producer/consumer**: Get comfortable with APIs
4. **Learn consumer groups**: Understand load balancing and failover
5. **Explore stream processing**: Kafka Streams, ksqlDB
6. **Master operations**: Monitoring, tuning, security

---

## Resources

### Official Documentation
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Kafka API Documentation](https://kafka.apache.org/35/javadoc/)
- [Confluent Documentation](https://docs.confluent.io/)

### Go Libraries
- [segmentio/kafka-go](https://github.com/segmentio/kafka-go) - Recommended
- [IBM/sarama](https://github.com/IBM/sarama) - Popular alternative
- [confluent-kafka-go](https://github.com/confluentinc/confluent-kafka-go) - C library wrapper

### Tools
- [kcat (kafkacat)](https://github.com/edenhill/kcat) - CLI producer/consumer
- [Kafka UI](https://github.com/provectus/kafka-ui) - Web UI
- [Kafka Explorer](https://www.kafkatool.com/) - Desktop GUI
- [Burrow](https://github.com/linkedin/Burrow) - Consumer lag monitoring

### Books
- "Kafka: The Definitive Guide" - Neha Narkhede et al.
- "Kafka Streams in Action" - Bill Bejeck
- "Designing Event-Driven Systems" - Ben Stopford

---

**Document Version:** 1.0
**Last Updated:** 2025-02-25
**Author:** Claude Code
