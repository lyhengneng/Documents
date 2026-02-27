# Prometheus - Complete Guide

## Table of Contents
- [What is Prometheus?](#what-is-prometheus)
- [Core Concepts](#core-concepts)
- [Prometheus Architecture](#prometheus-architecture)
- [Metric Types](#metric-types)
- [PromQL (Prometheus Query Language)](promql-prometheus-query-language)
- [Instrumentation](#instrumentation)
- [Practical Examples](#practical-examples)
- [Best Practices](#best-practices)
- [Alerting](#alerting)
- [Grafana Integration](#grafana-integration)

---

## What is Prometheus?

**Prometheus** is an open-source monitoring and alerting toolkit originally built at SoundCloud in 2012. It is now a graduated project of the Cloud Native Computing Foundation (CNCF) and is the standard for monitoring Kubernetes and cloud-native applications.

### What is Monitoring?

**Monitoring** is the practice of collecting, processing, aggregating, and displaying real-time quantitative data about systems to help understand their behavior, troubleshoot issues, and improve performance.

### Key Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                 PROMETHEUS CHARACTERISTICS                      │
├─────────────────────────────────────────────────────────────────┤
│  📊 Time Series DB    ──►  Stores metrics over time             │
│  🎯 Pull-Based        ──►  Scrapes targets at intervals         │
│  🏷️ Multi-dimensional ──►  Key-value labels for flexibility     │
│  🔍 Powerful Query    ──►  PromQL for complex analytics         │
│  🚨 Alerting          ──►  Built-in alert management            │
│  📈 Service Discovery ──►  Automatic target discovery           │
│  💾 Local Storage     ──►  Efficient time-series storage        │
└─────────────────────────────────────────────────────────────────┘
```

### Why Prometheus?

```
Traditional Monitoring (Push-based):
┌─────────────┐         push metrics          ┌──────────────┐
│ Application │ ────────────────────────────► │ Monitoring   │
│             │                               │ System       │
└─────────────┘                               └──────────────┘
     ↓ Problems:
     - Can't detect if app is down (can't push)
     - Hard to manage many targets
     - No control over scrape rate

Prometheus (Pull-based):
┌─────────────┐         scrape metrics       ┌──────────────┐
│   Prometheus │ ◄────────────────────────── │ Application  │
│              │                              │  (exposes    │
│              │ ────────────────────────────►   /metrics)  │
└─────────────┘         pull when ready       └──────────────┘
     ↓ Benefits:
     - Knows if target is down (scrape fails)
     - Centralized control
     - Service discovery integration
     - Easy to add new targets
```

---

## Core Concepts

### 1. Metrics

A **metric** is a numeric measurement of some aspect of a system.

```
Example Metrics:
├── http_requests_total         - How many requests?
├── http_request_duration       - How long do requests take?
├── memory_usage_bytes          - How much memory is used?
├── active_connections          - How many connections are open?
└── error_rate                  - What percentage of requests fail?
```

### 2. Time Series

A **time series** is a stream of timestamped values belonging to the same metric.

```
Metric: http_requests_total
Labels: {method="GET", path="/api/users", status="200"}

Time Series Data:
┌─────────────────────┬───────┐
│ Timestamp           │ Value │
├─────────────────────┼───────┤
│ 2025-02-25 10:00:00 │ 1234  │
│ 2025-02-25 10:01:00 │ 1245  │
│ 2025-02-25 10:02:00 │ 1258  │
│ 2025-02-25 10:03:00 │ 1272  │
│ 2025-02-25 10:04:00 │ 1291  │
└─────────────────────┴───────┘

Each line = one data point (timestamp + value)
```

### 3. Labels

**Labels** are key-value pairs that add dimensions to metrics.

```
Without labels (limited):
http_requests_total → 1500

With labels (powerful):
http_requests_total{method="GET",path="/api/users",status="200"}     → 1200
http_requests_total{method="GET",path="/api/users",status="404"}     → 50
http_requests_total{method="POST",path="/api/users",status="201"}    → 200
http_requests_total{method="DELETE",path="/api/users",status="200"}  → 50

Benefits:
✅ Filter: Show only 404 errors
✅ Aggregate: Sum all status codes
✅ Compare: GET vs POST performance
✅ Group: By path, method, or status
```

### 4. Instances and Jobs

```
Job:  Logical group of instances (same purpose)
Instance:  Individual target (host:port)

Example:
┌─────────────────────────────────────────────────┐
│ Job: api-servers                                │
├─────────────────────────────────────────────────┤
│ Instance 1: api-server-1:8080                   │
│ Instance 2: api-server-2:8080                   │
│ Instance 3: api-server-3:8080                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Job: databases                                  │
├─────────────────────────────────────────────────┤
│ Instance 1: postgres-primary:5432               │
│ Instance 2: postgres-replica-1:5432             │
│ Instance 3: postgres-replica-2:5432             │
└─────────────────────────────────────────────────┘

Labels added automatically:
job="api-servers"
instance="api-server-1:8080"
```

### 5. Scraping

**Scraping** is the process of Prometheus pulling metrics from targets.

```
Scrape Loop (every 15 seconds by default):

┌─────────────┐
│ Prometheus  │
│             │  ┌─────────────────────────────────┐
└──────┬──────┘  │ 1. HTTP GET /metrics            │
       │         └─────────────────────────────────┘
       │                      │
       │                      ▼
       │         ┌─────────────────────────────────┐
       │         │ Target: http://app:8080/metrics │
       │         │                                 │
       │         │ http_requests_total 1234        │
       │         │ http_duration_seconds 0.045     │
       │         │ memory_bytes 104857600          │
       │         └─────────────────────────────────┘
       │                      │
       │                      ▼
       │         ┌─────────────────────────────────┐
       │         │ 2. Parse and store metrics      │
       │         └─────────────────────────────────┘
       │                      │
       ▼
┌─────────────────────────────────┐
│ 3. Store in time-series database │
└─────────────────────────────────┘
```

---

## Prometheus Architecture

### Complete Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          PROMETHEUS ECOSYSTEM                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────┐                                                          │
│  │  Service     │  ┌──────────────┐                                       │
│  │  Discovery   │──│  Prometheus  │                                       │
│  │  (Kubernetes │  │   Server     │                                       │
│  │   Consul)    │  │              │                                       │
│  └──────────────┘  │  ┌────────┐  │                                       │
│                   │  │ Storage │  │                                       │
│  ┌──────────────┐  │  └────────┘  │                                       │
│  │   Targets    │  │              │    HTTP pull (every 15s)              │
│  │              │  │              │◄────────────────────────┐              │
│  │ ┌──────────┐ │  │              │                         │              │
│  │ │API Server│ │  └──────┬───────┘                         │              │
│  │ └──────────┘ │         │                                 │              │
│  │ ┌──────────┐ │         │                                 │              │
│  │ │Database  │ │         │ HTTP push (for short-lived)     │              │
│  │ └──────────┘ │         │                                 │              │
│  │ ┌──────────┐ │         │                                 │              │
│  │ │  Redis   │ │         │                                 │              │
│  │ └──────────┘ │         │                                 │              │
│  └──────────────┘         │                                 │              │
│                           │                                 │              │
│  ┌──────────────┐         │                                 │              │
│  │  Pushgateway │─────────┘                                 │              │
│  └──────────────┘                                           │              │
│                                                             │              │
│  ┌──────────────┐         ┌─────────────────────────────────┘              │
│  │ Alertmanager │◄────────┤                                                  │
│  └──────────────┘         │                                                  │
│         │                 │                                                  │
│         │                 │                                                  │
│         ▼                 ▼                                                  │
│  ┌──────────────┐   ┌──────────┐                                            │
│  │  Notifications│  │   Query  │                                            │
│  │  (Email/Slack│  │   API    │                                            │
│  │   PagerDuty) │  └──────────┘                                            │
│  └──────────────┘         │                                                  │
│                           │                                                  │
│                           ▼                                                  │
│                   ┌──────────────┐                                          │
│                   │   Grafana    │                                          │
│                   │  (Visualize) │                                          │
│                   └──────────────┘                                          │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Purpose |
|-----------|---------|
| **Prometheus Server** | Core component that scrapes and stores metrics |
| **Service Discovery** | Automatically finds targets to monitor (Kubernetes, Consul, etc.) |
| **Targets** | Applications exposing metrics on `/metrics` endpoint |
| **Pushgateway** | Receive metrics from short-lived jobs (batch jobs) |
| **Alertmanager** | Handle alert routing, grouping, and notifications |
| **Grafana** | Visualization and dashboards |

---

## Metric Types

Prometheus has four primary metric types:

### 1. Counter

**Counter** is a cumulative metric that only increases and never decreases.

```
Use cases:
├── Number of requests served
├── Number of errors
├── Number of tasks completed
└── Number of bytes received

Example:
http_requests_total{
    method="POST",
    path="/api/users",
    status="201"
} → 15234

Key points:
✅ Only goes UP (never reset)
✅ Can calculate rate of change
✅ Use _rate() or _increase() functions
❌ Don't use for things that can decrease
```

**Example Counter Metrics:**
```
# Total HTTP requests
http_requests_total{method="GET",path="/api/users",status="200"} 1234

# Total bytes received
network_received_bytes_total{interface="eth0"} 1048576000

# Total errors
error_count_total{type="database"} 42

# Tasks processed
jobs_processed_total{queue="email"} 5000
```

### 2. Gauge

**Gauge** is a metric that can go up or down.

```
Use cases:
├── Current memory usage
├── Current temperature
├── Number of concurrent requests
├── Queue size
└── Disk usage

Example:
memory_usage_bytes{
    type="heap"
} → 1073741824

Key points:
✅ Can go UP and DOWN
✅ Shows current state
✅ Direct value observation
❌ Don't use for accumulating counts
```

**Example Gauge Metrics:**
```
# Current memory usage
memory_usage_bytes{type="heap"} 1073741824

# Active connections
active_connections{server="api-1"} 245

# Queue size
queue_size{queue="email"} 150

# CPU usage percentage
cpu_usage_percent{core="0"} 45.2

# Temperature in Celsius
temperature_celsius{sensor="cpu-0"} 67.5
```

### 3. Histogram

**Histogram** samples observations and counts them in configurable buckets.

```
Use cases:
├── Request latency
├── Response size
└── Processing time

Example:
http_request_duration_seconds_bucket{
    le="0.1"      // ≤ 100ms
} → 8234

http_request_duration_seconds_bucket{
    le="0.5"      // ≤ 500ms
} → 9456

http_request_duration_seconds_bucket{
    le="+Inf"     // All requests
} → 9876

Calculated metrics:
├── _bucket: Count in each bucket
├── _sum: Total sum of all values
└── _count: Total count of observations
```

**Histogram Example:**
```
# Request duration buckets
http_request_duration_seconds_bucket{le="0.005"} 5000     # ≤ 5ms
http_request_duration_seconds_bucket{le="0.01"}  8000     # ≤ 10ms
http_request_duration_seconds_bucket{le="0.025"} 9500     # ≤ 25ms
http_request_duration_seconds_bucket{le="0.05"}  9800     # ≤ 50ms
http_request_duration_seconds_bucket{le="0.1"}   9900     # ≤ 100ms
http_request_duration_seconds_bucket{le="0.25"}  9950     # ≤ 250ms
http_request_duration_seconds_bucket{le="0.5"}   9980     # ≤ 500ms
http_request_duration_seconds_bucket{le="1"}     9990     # ≤ 1s
http_request_duration_seconds_bucket{le="+Inf"}  10000    # Total

# Sum of all request durations
http_request_duration_seconds_sum 250.5

# Count of all requests
http_request_duration_seconds_count 10000

# Calculate: Average = sum / count = 250.5 / 10000 = 0.025s
```

### 4. Summary

**Summary** is similar to histogram but calculated on the client side.

```
Use cases:
├── Request latency (pre-calculated quantiles)
├── Response size (pre-calculated quantiles)

Example:
http_request_duration_seconds{
    quantile="0.5"   // 50th percentile (median)
} → 0.023

http_request_duration_seconds{
    quantile="0.9"   // 90th percentile
} → 0.045

http_request_duration_seconds{
    quantile="0.99"  // 99th percentile
} → 0.123

Key differences from Histogram:
├── Calculated on client side
├── Pre-defined quantiles
├── Less flexible for aggregations
└── Use Histogram for most cases
```

**Metric Type Comparison:**

| Type | Direction | Use When | Examples |
|------|-----------|----------|----------|
| **Counter** | Only up | Counting events | Requests, errors, bytes |
| **Gauge** | Up/down | Current state | Memory, connections, temp |
| **Histogram** | N/A | Distributions (server) | Latency, size, duration |
| **Summary** | N/A | Distributions (client) | Pre-calculated quantiles |

---

## PromQL (Prometheus Query Language)

PromQL is a powerful query language for selecting and aggregating time series data.

### Basic Selectors

```promql
# Select all time series for a metric
http_requests_total

# Select by label value
http_requests_total{method="GET"}

# Select by multiple labels
http_requests_total{method="GET",status="200"}

# Select by label match (regex)
http_requests_total{method=~"GET|POST"}           # GET or POST
http_requests_total{method!~"DELETE|PUT"}        # Not DELETE or PUT
http_requests_total{path=~"/api/.*"}             # Paths starting with /api/

# Select by label not equal
http_requests_total{status!="200"}
```

### Range Selectors

```promql
# Instant vector (current value)
http_requests_total

# Range vector (last 5 minutes)
http_requests_total[5m]

# Common ranges:
[5m]    # Last 5 minutes
[1h]    # Last 1 hour
[1d]    # Last 1 day
[7d]    # Last 7 days
```

### Operators

```promql
# Arithmetic operators
http_requests_total * 2          # Multiply
http_requests_total + 100        # Add
memory_bytes / 1024 / 1024       # Convert to MB

# Comparison operators
http_requests_total > 1000       # Greater than
memory_bytes < 1000000000        # Less than
cpu_usage >= 80                  # Greater or equal

# Logical operators
http_requests_total > 1000 and method="GET"
http_requests_total < 100 or status="500"
method!~"DELETE"                 # Not equal regex
```

### Aggregation Operators

```promql
# Sum - Add all values
sum(http_requests_total)                    # Total requests
sum(http_requests_total) by (method)        # Sum per method
sum(http_requests_total) by (job, instance) # Sum per job and instance

# Avg - Average
avg(memory_usage_bytes)                     # Average memory
avg(cpu_usage) by (instance)                # Average CPU per instance

# Min/Max
max(response_size_bytes)                    # Largest response
min(temperature_celsius) by (sensor)        # Min temperature

# Count - Count series
count(up)                                   # How many targets are up?
count(http_requests_total) by (status)      # Count per status

# Stddev/Stdvar
stddev(duration_seconds)                    # Standard deviation
stdvar(memory_bytes)                        # Variance

# Topk/Bottomk - Top or bottom N
topk(5, http_requests_total)                # Top 5 by request count
bottomk(3, error_rate)                      # Bottom 3 error rates
```

### Functions

```promql
# Rate - Per-second rate of increase (for counters)
rate(http_requests_total[5m])               # Requests per second
rate(errors_total[1h])                      # Errors per second

# Irate - Instant rate (last two points only)
irate(http_requests_total[5m])              # More responsive

# Increase - Total increase over time
increase(http_requests_total[1h])           # Total requests in 1 hour

# Delta - Difference over time
delta(memory_usage_bytes[1h])               # Memory change in 1 hour

# Aggregation over time
avg_over_time(cpu_usage[5m])                # Average CPU over 5m
max_over_time(memory_bytes[1h])             # Max memory in 1h
min_over_time(response_time[5m])            # Min response in 5m

# Time-based
offset 1h                                   # Data from 1 hour ago
http_requests_total offset 1h               # Request count 1h ago

# Prediction
predict_linear(memory_usage[1h], 3600)      # Predict memory in 1h
```

### Real Query Examples

```promql
# 1. Requests per second per endpoint
rate(http_requests_total{job="api"}[5m])

# 2. 95th percentile of response time
histogram_quantile(0.95,
    rate(http_request_duration_seconds_bucket[5m])
)

# 3. Error rate (percentage)
(
    sum(rate(http_requests_total{status=~"5.."}[5m]))
    /
    sum(rate(http_requests_total[5m]))
) * 100

# 4. CPU usage percentage
(1 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) by (instance)) * 100

# 5. Memory usage percentage
(1 -
    (node_memory_MemAvailable_bytes /
    node_memory_MemTotal_bytes)
) * 100

# 6. Disk usage percentage
(1 -
    (node_filesystem_avail_bytes{mountpoint="/"}
    / node_filesystem_size_bytes{mountpoint="/"})
) * 100

# 7. Requests in the last hour
increase(http_requests_total[1h])

# 8. Average response time by endpoint
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])

# 9. Service availability (up = 1, down = 0)
avg(up)

# 10. Alert: High error rate
rate(http_requests_total{status="500"}[5m]) > 10
```

---

## Instrumentation

Instrumentation is the process of adding metrics to your application.

### Exposition Format

The `/metrics` endpoint returns metrics in a simple text format:

```text
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",path="/api/users",status="201"} 1234
http_requests_total{method="GET",path="/api/users",status="200"} 5678
http_requests_total{method="GET",path="/api/users",status="404"} 89

# HELP http_request_duration_seconds Request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 8234
http_request_duration_seconds_bucket{le="0.5"} 9456
http_request_duration_seconds_bucket{le="+Inf"} 9876
http_request_duration_seconds_sum 250.5
http_request_duration_seconds_count 9876

# HELP memory_usage_bytes Current memory usage
# TYPE memory_usage_bytes gauge
memory_usage_bytes{type="heap"} 1073741824
memory_usage_bytes{type="stack"} 524288000

# HELP active_connections Current number of connections
# TYPE active_connections gauge
active_connections 245
```

### Go Client Library Examples

#### Basic Setup

```go
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    // Define a counter
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},
    )

    // Define a histogram
    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request latency",
            Buckets: prometheus.DefBuckets, // Default buckets
        },
        []string{"method", "path"},
    )

    // Define a gauge
    activeConnections = prometheus.NewGauge(
        prometheus.GaugeOpts{
            Name: "active_connections",
            Help: "Current number of active connections",
        },
    )
)

func init() {
    // Register metrics with Prometheus
    prometheus.MustRegister(httpRequestsTotal)
    prometheus.MustRegister(httpRequestDuration)
    prometheus.MustRegister(activeConnections)
}

func main() {
    // Expose the /metrics endpoint
    http.Handle("/metrics", promhttp.Handler())

    // Your application handlers
    http.HandleFunc("/api/users", handleUsers)

    http.ListenAndServe(":8080", nil)
}
```

#### Middleware for HTTP Metrics

```go
package main

import (
    "net/http"
    "strconv"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    // Auto-create metrics (no manual registration needed)
    httpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},
    )

    httpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request latency",
            Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5},
        },
        []string{"method", "path"},
    )

    requestsInFlight = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "http_requests_in_flight",
            Help: "Current number of requests being processed",
        },
    )
}

// MetricsMiddleware wraps an http.Handler with metrics
func MetricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Track in-flight requests
        requestsInFlight.Inc()
        defer requestsInFlight.Dec()

        // Start timer
        start := time.Now()

        // Wrap ResponseWriter to capture status code
        wrapped := &responseWriter{ResponseWriter: w, status: 200}

        // Call the actual handler
        next.ServeHTTP(wrapped, r)

        // Calculate duration
        duration := time.Since(start).Seconds()

        // Record metrics
        httpRequestsTotal.WithLabelValues(
            r.Method,
            r.URL.Path,
            strconv.Itoa(wrapped.status),
        ).Inc()

        httpRequestDuration.WithLabelValues(
            r.Method,
            r.URL.Path,
        ).Observe(duration)
    })
}

// responseWriter wraps http.ResponseWriter to capture status code
type responseWriter struct {
    http.ResponseWriter
    status int
}

func (rw *responseWriter) WriteHeader(status int) {
    rw.status = status
    rw.ResponseWriter.WriteHeader(status)
}

func main() {
    // Create mux
    mux := http.NewServeMux()

    // Register handlers
    mux.HandleFunc("/api/users", handleUsers)
    mux.HandleFunc("/api/products", handleProducts)

    // Wrap with metrics middleware
    handler := MetricsMiddleware(mux)

    // Expose metrics endpoint
    handler = promhttp.InstrumentHandlerInFlight(
        requestsInFlight,
        handler,
    )

    http.Handle("/metrics", promhttp.Handler())
    http.Handle("/", handler)

    http.ListenAndServe(":8080", nil)
}

func handleUsers(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"users": ["alice", "bob"]}`))
}

func handleProducts(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte(`{"products": ["laptop", "phone"]}`))
}
```

#### Database Metrics

```go
package main

import (
    "database/sql"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    dbQueriesTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "db_queries_total",
            Help: "Total number of database queries",
        },
        []string{"query_type", "status"}, // select, insert, update, delete
    )

    dbQueryDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "db_query_duration_seconds",
            Help:    "Database query duration",
            Buckets: prometheus.ExponentialBuckets(0.001, 2, 10), // 1ms to 1s
        },
        []string{"query_type"},
    )

    dbConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "db_connections_active",
            Help: "Current number of active database connections",
        },
    )
)

// InstrumentedDB wraps sql.DB with metrics
type InstrumentedDB struct {
    *sql.DB
}

func (idb *InstrumentedDB) Query(query string, args ...interface{}) (*sql.Rows, error) {
    start := time.Now()
    queryType := getQueryType(query)

    rows, err := idb.DB.Query(query, args...)
    duration := time.Since(start).Seconds()

    dbQueryDuration.WithLabelValues(queryType).Observe(duration)
    dbConnections.Set(getActiveConnections(idb.DB))

    if err != nil {
        dbQueriesTotal.WithLabelValues(queryType, "error").Inc()
    } else {
        dbQueriesTotal.WithLabelValues(queryType, "success").Inc()
    }

    return rows, err
}

func (idb *InstrumentedDB) Exec(query string, args ...interface{}) (sql.Result, error) {
    start := time.Now()
    queryType := getQueryType(query)

    result, err := idb.DB.Exec(query, args...)
    duration := time.Since(start).Seconds()

    dbQueryDuration.WithLabelValues(queryType).Observe(duration)

    if err != nil {
        dbQueriesTotal.WithLabelValues(queryType, "error").Inc()
    } else {
        dbQueriesTotal.WithLabelValues(queryType, "success").Inc()
    }

    return result, err
}

func getQueryType(query string) string {
    switch {
    case strings.HasPrefix(strings.ToUpper(query), "SELECT"):
        return "select"
    case strings.HasPrefix(strings.ToUpper(query), "INSERT"):
        return "insert"
    case strings.HasPrefix(strings.ToUpper(query), "UPDATE"):
        return "update"
    case strings.HasPrefix(strings.ToUpper(query), "DELETE"):
        return "delete"
    default:
        return "other"
    }
}
```

#### Custom Business Metrics

```go
package main

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // Business metrics
    ordersProcessed = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "orders_processed_total",
            Help: "Total number of orders processed",
        },
        []string{"status", "payment_method"},
    )

    orderValue = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "order_value_usd",
            Help:    "Order value in USD",
            Buckets: []float64{10, 50, 100, 200, 500, 1000, 5000},
        },
        []string{"country"},
    )

    activeUsers = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "active_users",
            Help: "Current number of active users",
        },
        []string{"plan_type"}, // free, premium, enterprise
    )

    queueSize = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "email_queue_size",
            Help: "Current size of email queue",
        },
        []string{"priority"}, // high, normal, low
    )
)

// ProcessOrder with metrics
func ProcessOrder(order Order) error {
    start := time.Now()

    // Track active users
    activeUsers.WithLabelValues(order.User.PlanType).Inc()
    defer activeUsers.WithLabelValues(order.User.PlanType).Dec()

    // Process order
    err := processPayment(order)
    if err != nil {
        ordersProcessed.WithLabelValues("failed", order.PaymentMethod).Inc()
        return err
    }

    // Record order value
    orderValue.WithLabelValues(order.Country).Observe(order.Amount)

    // Mark as processed
    ordersProcessed.WithLabelValues("success", order.PaymentMethod).Inc()

    return nil
}
```

---

## Practical Examples

### Example 1: Simple Web Server with Metrics

```go
package main

import (
    "fmt"
    "math/rand"
    "net/http"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    requestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "app_requests_total",
            Help: "Total number of requests",
        },
        []string{"endpoint", "status"},
    )

    requestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "app_request_duration_seconds",
            Help:    "Request duration",
            Buckets: prometheus.DefBuckets,
        },
        []string{"endpoint"},
    )

    activeUsers = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "app_active_users",
            Help: "Active users",
        },
        []string{"role"},
    )
)

func main() {
    // Initialize metrics
    activeUsers.WithLabelValues("admin").Set(3)
    activeUsers.WithLabelValues("user").Set(150)

    // Setup routes
    http.HandleFunc("/", handleHome)
    http.HandleFunc("/api/data", handleData)
    http.Handle("/metrics", promhttp.Handler())

    fmt.Println("Server starting on :8080")
    fmt.Println("Metrics available at http://localhost:8080/metrics")
    http.ListenAndServe(":8080", nil)
}

func handleHome(w http.ResponseWriter, r *http.Request) {
    start := time.Now()

    // Simulate some work
    time.Sleep(time.Duration(rand.Intn(100)) * time.Millisecond)

    w.WriteHeader(http.StatusOK)
    fmt.Fprintf(w, "Welcome to the home page!")

    // Record metrics
    duration := time.Since(start).Seconds()
    requestDuration.WithLabelValues("/").Observe(duration)
    requestsTotal.WithLabelValues("/", "200").Inc()
}

func handleData(w http.ResponseWriter, r *http.Request) {
    start := time.Now()

    // Simulate API call
    time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)

    // Randomly return errors
    if rand.Float32() < 0.1 { // 10% error rate
        w.WriteHeader(http.StatusInternalServerError)
        fmt.Fprintf(w, `{"error": "internal server error"}`)
        requestsTotal.WithLabelValues("/api/data", "500").Inc()
    } else {
        w.WriteHeader(http.StatusOK)
        fmt.Fprintf(w, `{"data": [1, 2, 3, 4, 5]}`)
        requestsTotal.WithLabelValues("/api/data", "200").Inc()
    }

    duration := time.Since(start).Seconds()
    requestDuration.WithLabelValues("/api/data").Observe(duration)
}
```

### Example 2: Prometheus Configuration

```yaml
# prometheus.yml

global:
  # Scrape interval (how often to scrape targets)
  scrape_interval: 15s
  # Evaluation interval for rules
  evaluation_interval: 15s
  # External labels
  external_labels:
    cluster: 'production'
    environment: 'us-west-2'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

# Rule files
rule_files:
  - "alerts.yml"
  - "recording_rules.yml"

# Scrape configurations
scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          instance: 'prometheus-server'

  # API servers
  - job_name: 'api-servers'
    scrape_interval: 10s
    scrape_timeout: 5s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['api-server-1:8080', 'api-server-2:8080', 'api-server-3:8080']
        labels:
          cluster: 'production'
          datacenter: 'us-west-2'

  # Database servers
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
        labels:
          db_type: 'postgresql'

  # Kubernetes service discovery
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      # Keep only pods with specific annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      # Use pod name as instance label
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: instance
      # Use pod namespace
      - source_labels: [__meta_kubernetes_pod_namespace]
        target_label: namespace

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Redis exporter
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### Example 3: Alert Rules

```yaml
# alerts.yml

groups:
  - name: api_alerts
    interval: 30s
    rules:
      # High error rate alert
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for the last 5 minutes"

      # High latency alert
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
          ) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is {{ $value }}s"

      # Service down alert
      - alert: ServiceDown
        expr: up{job="api-servers"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "{{ $labels.instance }} has been down for more than 1 minute"

  - name: infrastructure_alerts
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% on {{ $labels.instance }}"

      # Disk space low
      - alert: DiskSpaceLow
        expr: |
          (1 - node_filesystem_avail_bytes{fstype!~"tmpfs|fuse.*"}
          / node_filesystem_size_bytes) * 100 > 85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disk space running low"
          description: "Disk usage is {{ $value }}% on {{ $labels.device }}"

  - name: business_alerts
    rules:
      # Low order rate
      - alert: LowOrderRate
        expr: rate(orders_processed_total[1h]) < 10
        for: 15m
        labels:
          severity: warning
          team: sales
        annotations:
          summary: "Order rate is unusually low"
          description: "Only {{ $value }} orders/minute in the last hour"

      # Payment failures
      - alert: HighPaymentFailures
        expr: |
          sum(rate(payment_attempts_total{status="failed"}[5m])) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High payment failure rate"
          description: "{{ $value }} failed payment attempts per second"
```

### Example 4: Recording Rules

```yaml
# recording_rules.yml

groups:
  - name: api_rate_rules
    interval: 30s
    rules:
      # Calculate request rate per endpoint
      - record: job:http_requests_per_second:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job, path)

      # Calculate error rate
      - record: job:http_error_rate:rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
          /
          sum(rate(http_requests_total[5m])) by (job)

      # Calculate 95th percentile latency
      - record: job:http_latency:p95:5m
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, job)
          )

  - name: infrastructure_rules
    rules:
      # CPU usage percentage
      - record: instance:cpu_usage:percent
        expr: |
          (100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))
          by (instance)

      # Memory usage percentage
      - record: instance:memory_usage:percent
        expr: |
          (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

      # Disk usage percentage
      - record: instance:disk_usage:percent
        expr: |
          (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100

  - name: business_rules
    rules:
      # Orders per minute
      - record: business:orders_per_minute
        expr: sum(rate(orders_processed_total[1m])) * 60

      # Revenue per hour
      - record: business:revenue_per_hour
        expr: sum(increase(order_value_usd[1h]))
```

### Example 5: Multi-Target Monitoring

```go
package main

import (
    "net/http"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

// Monitor multiple services
type ServiceMonitor struct {
    serviceName string
    url         string
    up          prometheus.Gauge
    latency     prometheus.Histogram
}

func NewServiceMonitor(name, url string) *ServiceMonitor {
    return &ServiceMonitor{
        serviceName: name,
        url:         url,
        up: promauto.NewGauge(prometheus.GaugeOpts{
            Name: "service_up",
            Help: "Service availability",
            ConstLabels: prometheus.Labels{
                "service": name,
            },
        }),
        latency: promauto.NewHistogram(prometheus.HistogramOpts{
            Name:    "service_latency_seconds",
            Help:    "Service response latency",
            Buckets: prometheus.DefBuckets,
            ConstLabels: prometheus.Labels{
                "service": name,
            },
        }),
    }
}

func (sm *ServiceMonitor) Check() {
    start := time.Now()
    resp, err := http.Get(sm.url)
    duration := time.Since(start).Seconds()

    if err != nil || resp.StatusCode >= 500 {
        sm.up.Set(0)
    } else {
        sm.up.Set(1)
    }

    if resp != nil {
        resp.Body.Close()
    }

    sm.latency.Observe(duration)
}

func main() {
    // Monitor multiple services
    services := []*ServiceMonitor{
        NewServiceMonitor("api", "http://api:8080/health"),
        NewServiceMonitor("auth", "http://auth:8081/health"),
        NewServiceMonitor("payment", "http://payment:8082/health"),
    }

    // Check services every 30 seconds
    go func() {
        ticker := time.NewTicker(30 * time.Second)
        for range ticker.C {
            for _, svc := range services {
                svc.Check()
            }
        }
    }()

    // Expose metrics
    http.Handle("/metrics", promhttp.Handler())
    http.ListenAndServe(":9090", nil)
}
```

---

## Best Practices

### 1. Metric Naming

```
✅ Good naming:
http_requests_total          # Clear, descriptive
http_request_duration_seconds # Unit included
memory_usage_bytes           # Unit included
active_connections           # Current state

❌ Bad naming:
metrics_1                    # Meaningless
http                         # Too vague
count                        # Doesn't say what
reqs                         # Abbreviated

Naming conventions:
├── Use snake_case
├── Include unit suffix (_total, _seconds, _bytes)
├── Be descriptive
├── Use prefixes to group related metrics
└── Counter metrics: _total suffix
```

### 2. Label Best Practices

```go
✅ Good labels:
{
    "method": "GET",
    "path": "/api/users",
    "status": "200"
}

❌ Bad labels:
{
    "method_GET_path_api_users_status_200": "true"  // Should be in metric name
    "timestamp": "2025-02-25T10:00:00Z"              # Too many values
    "user_id": "12345"                               # High cardinality
}

Label guidelines:
✅ Use low cardinality labels (1-100 values)
✅ Use consistent label names
✅ Use labels for grouping and filtering
❌ Avoid high cardinality (user_id, request_id)
❌ Don't encode everything in labels
❌ Don't use more than ~20 labels per metric
```

### 3. Bucket Selection for Histograms

```go
// Customized buckets based on your needs
requestDuration := promauto.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request latency",
        // Choose buckets based on expected latency range
        Buckets: []float64{
            0.001,  // 1ms    - Fast responses
            0.005,  // 5ms
            0.01,   // 10ms
            0.025,  // 25ms
            0.05,   // 50ms
            0.1,    // 100ms
            0.25,   // 250ms
            0.5,    // 500ms
            1.0,    // 1s     - Slow but acceptable
            2.5,    // 2.5s
            5.0,    // 5s     - Very slow
            10.0,   // 10s    - Error threshold
        },
    },
    []string{"endpoint"},
)

// Use predefined bucket sets
prometheus.DefBuckets           // Default: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
prometheus.LinearBuckets(0, 10, 20)           // 20 buckets from 0 to 10
prometheus.ExponentialBuckets(0.001, 2, 10)   // 10 exponential buckets from 1ms
```

### 4. Cardinality Management

```go
❌ High cardinality (AVOID):
user_requests_total{user_id="12345"}  # Millions of users
request_duration{request_id="abc123"} # Unique per request

✅ Low cardinality (USE):
http_requests_total{method="GET", status="200"}  # Limited combinations
error_count{error_type="timeout"}                 # Categorized

// If you need high cardinality:
// 1. Use sampling instead of full tracking
// 2. Aggregate before storing
// 3. Use separate system (e.g., logging/tracing)
```

### 5. Performance Considerations

```go
// Bad: Creating metrics on the fly
func handleRequest(userID string) {
    metric := prometheus.NewCounter(...)  // Don't do this!
    metric.Inc()
}

// Good: Pre-defined metrics with labels
var userRequests = promauto.NewCounterVec(
    prometheus.CounterOpts{
        Name: "user_requests_total",
    },
    []string{"user_type"},  // Low cardinality label
)

func handleRequest(userType string) {
    userRequests.WithLabelValues(userType).Inc()
}
```

---

## Alerting

### Alertmanager Configuration

```yaml
# alertmanager.yml

global:
  # Global SMTP settings
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'password'

# Route alerts to receivers
route:
  # Default receiver
  receiver: 'default'

  # Group alerts
  group_by: ['alertname', 'cluster']

  # Wait time before sending notification
  group_wait: 10s

  # Wait time before sending new notification for same group
  group_interval: 5m

  # Wait time before re-sending notification
  repeat_interval: 12h

  # Child routes
  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      group_wait: 10s
      repeat_interval: 5m

    # Business alerts go to Slack
    - match:
        team: sales
      receiver: 'sales-team'
      repeat_interval: 1h

    # Infrastructure alerts
    - match:
        alertname: 'HighCPUUsage|HighMemoryUsage'
      receiver: 'infra-team'

# Receivers define where to send alerts
receivers:
  - name: 'default'
    email_configs:
      - to: 'oncall@example.com'
        headers:
          Subject: '[Prometheus] {{ .GroupLabels.alertname }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

  - name: 'sales-team'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#sales-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'infra-team'
    webhook_configs:
      - url: 'http://internal-alert-handler/alerts'
```

### Alert Lifecycle

```
1. Rule Evaluation
   Prometheus evaluates alert rules every 30s

2. Pending State
   Condition met but not yet reached 'for' duration
   └─> Wait for 'for' period (5 minutes)

3. Firing State
   Condition still met after 'for' period
   └─> Send to Alertmanager

4. Alertmanager Processing
   ├─> Group alerts
   ├─> Deduplicate
   ├─> Route to receivers
   └─> Send notifications

5. Notification
   ├─> Email
   ├─> Slack
   ├─> PagerDuty
   └─> Webhook

6. Resolution
   When condition no longer met
   └─> Send resolved notification
```

---

## Grafana Integration

### Dashboard JSON Example

```json
{
  "dashboard": {
    "title": "API Service Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (status)",
            "legendFormat": "{{ status }}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
          }
        ]
      },
      {
        "title": "Latency (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"
          }
        ]
      }
    ]
  }
}
```

### Important Grafana Queries

```promql
# 1. Request rate over time
rate(http_requests_total[5m])

# 2. Error percentage
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# 3. P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 4. CPU by instance
100 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100

# 5. Memory usage
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 6. Request rate heatmap
rate(http_requests_total[5m])

# 7. Top 5 endpoints by requests
topk(5, sum(rate(http_requests_total[5m])) by (path))

# 8. Service availability
avg(up) * 100
```

---

## Summary

### Key Takeaways

1. **Prometheus is pull-based** - It scrapes metrics from targets
2. **Metrics are time series** - Timestamped values with labels
3. **Four metric types** - Counter (up), Gauge (up/down), Histogram (distribution), Summary (pre-calculated)
4. **PromQL is powerful** - Flexible querying and aggregation
5. **Labels are key** - Enable dimensional data and flexible querying
6. **Instrument early** - Add metrics from the start
7. **Alert on symptoms** - Alert on what affects users
8. **Use Grafana** - Visualize metrics effectively

### Monitoring Checklist

```
Application Metrics:
✅ Request rate (counter)
✅ Error rate (counter)
✅ Latency (histogram)
✅ Active connections (gauge)
✅ Queue size (gauge)

Infrastructure Metrics:
✅ CPU usage (gauge)
✅ Memory usage (gauge)
✅ Disk usage (gauge)
✅ Network traffic (counter)
✅ Service availability (gauge)

Business Metrics:
✅ Orders/second (counter)
✅ Revenue (counter/gauge)
✅ Active users (gauge)
✅ Conversion rate (gauge)
```

### Learning Path

1. **Start with basics**: Install Prometheus, scrape a target
2. **Learn PromQL**: Query and visualize data
3. **Instrument your app**: Add custom metrics
4. **Create dashboards**: Use Grafana for visualization
5. **Set up alerts**: Configure Alertmanager
6. **Advanced topics**: Recording rules, federation, thanos

---

## Resources

### Official Resources
- [Prometheus Documentation](https://prometheus.io/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Best Practices](https://prometheus.io/docs/practices/)
- [Client Libraries](https://prometheus.io/docs/instrumenting/clientlibs/)

### Go Libraries
- [prometheus/client_golang](https://github.com/prometheus/client_golang) - Official Go client
- [prometheus/client_golang/api](https://github.com/prometheus/client_golang) - Go API client

### Tools
- [Grafana](https://grafana.com/) - Visualization
- [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/) - Alert routing
- [Pushgateway](https://prometheus.io/docs/practices/pushing/) - For short-lived jobs

### Books
- "Prometheus: Up & Running" - James Turnbull
- "Monitoring with Prometheus" - Various authors

---

**Document Version:** 1.0
**Last Updated:** 2025-02-25
**Author:** Claude Code
