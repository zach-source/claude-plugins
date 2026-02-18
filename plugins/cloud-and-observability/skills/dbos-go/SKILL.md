---
name: dbos-go
description: "DBOS durable execution framework for Go. Use when implementing resilient, failure-recoverable applications with durable workflows, steps, queues, and workflow communication patterns. Triggers on DBOS Go, durable execution Go, resilient workflows Go, saga pattern Go, or when building fault-tolerant Go applications."
---

# DBOS for Go

DBOS provides durable execution so you can write programs that are resilient to any failure. When interrupted, workflows automatically resume from their last completed step. Requires PostgreSQL as its system database.

## Core Concepts

### Workflows
- Must be **deterministic** - calling with identical inputs should invoke same steps in same order
- Accept `dbos.DBOSContext` plus one serializable input
- Return one serializable output and an error
- Cannot spawn goroutines or use `select`
- Cannot modify global state (read-only access allowed)

### Steps
- Regular Go functions called via `dbos.RunAsStep()`
- Must accept `context.Context` and return serializable value + error
- Used for non-deterministic operations (API calls, random, time, file I/O)
- Automatically skipped on recovery if previously completed

### Queues
- Manage concurrent workflow execution with controlled flow
- Support rate limiting, priority, and deduplication
- Created with `dbos.NewWorkflowQueue()`

## Essential Patterns

### Basic Application Structure

```go
package main

import (
    "context"
    "fmt"
    "os"
    "time"

    "github.com/dbos-inc/dbos-transact-golang/dbos"
)

func main() {
    dbosContext, err := dbos.NewDBOSContext(context.Background(), dbos.Config{
        AppName:     "my-app",
        DatabaseURL: os.Getenv("DBOS_SYSTEM_DATABASE_URL"),
    })
    if err != nil {
        panic(fmt.Sprintf("Initializing DBOS failed: %v", err))
    }

    // Register workflows BEFORE Launch
    dbos.RegisterWorkflow(dbosContext, myWorkflow)

    err = dbos.Launch(dbosContext)
    if err != nil {
        panic(fmt.Sprintf("Launching DBOS failed: %v", err))
    }
    defer dbos.Shutdown(dbosContext, 5*time.Second)

    // Application logic (HTTP server, etc.)
}
```

### Workflow with Steps

```go
func myWorkflow(ctx dbos.DBOSContext, input string) (string, error) {
    result1, err := dbos.RunAsStep(ctx, func(stepCtx context.Context) (string, error) {
        return callExternalAPI(stepCtx, input)
    }, dbos.WithStepName("callAPI"))
    if err != nil {
        return "", err
    }

    result2, err := dbos.RunAsStep(ctx, func(stepCtx context.Context) (string, error) {
        return processData(stepCtx, result1)
    }, dbos.WithStepName("processData"))
    if err != nil {
        return "", err
    }

    return result2, nil
}
```

### Step with Retry Configuration

```go
func fetchWithRetry(ctx dbos.DBOSContext, url string) (string, error) {
    return dbos.RunAsStep(
        ctx,
        func(stepCtx context.Context) (string, error) {
            resp, err := http.Get(url)
            if err != nil {
                return "", err
            }
            defer resp.Body.Close()
            body, _ := io.ReadAll(resp.Body)
            return string(body), nil
        },
        dbos.WithStepName("fetchURL"),
        dbos.WithStepMaxRetries(10),
        dbos.WithMaxInterval(30*time.Second),
        dbos.WithBackoffFactor(2.0),
        dbos.WithBaseInterval(500*time.Millisecond),
    )
}
```

### Queue-Based Processing

```go
func main() {
    dbosContext := initDBOS()

    queue := dbos.NewWorkflowQueue(dbosContext, "task_queue",
        dbos.WithWorkerConcurrency(5))

    // Or with rate limiting
    rateLimitedQueue := dbos.NewWorkflowQueue(dbosContext, "api_queue",
        dbos.WithRateLimiter(&dbos.RateLimiter{
            Limit:  100,
            Period: 60.0, // 100 requests per minute
        }))

    dbos.RegisterWorkflow(dbosContext, taskWorkflow)
    dbos.Launch(dbosContext)
}

func enqueueTask(ctx dbos.DBOSContext, queue dbos.WorkflowQueue, taskID int) error {
    handle, err := dbos.RunWorkflow(ctx, taskWorkflow, taskID,
        dbos.WithQueue(queue.Name))
    if err != nil {
        return err
    }
    _, err = handle.GetResult()
    return err
}
```

### Workflow Communication - Messages

```go
const PaymentTopic = "payment_status"

func checkoutWorkflow(ctx dbos.DBOSContext, orderID string) (string, error) {
    // Wait up to 5 minutes for payment confirmation
    notification, err := dbos.Recv(ctx, PaymentTopic, 300)
    if err != nil {
        return "", fmt.Errorf("payment timeout: %w", err)
    }

    if notification.Status == "completed" {
        return "order_completed", nil
    }
    return "payment_failed", nil
}

func paymentWebhook(dbosContext dbos.DBOSContext, workflowID string, status string) error {
    return dbos.Send(dbosContext, workflowID, PaymentNotification{Status: status}, PaymentTopic)
}
```

### Workflow Communication - Events

```go
const PaymentURLKey = "payment_url"

func checkoutWorkflow(ctx dbos.DBOSContext, order Order) (string, error) {
    url := generatePaymentURL(order)
    err := dbos.SetEvent(ctx, PaymentURLKey, url)
    if err != nil {
        return "", err
    }
    // Continue processing...
}

func checkoutHandler(dbosContext dbos.DBOSContext, w http.ResponseWriter, r *http.Request) {
    handle, _ := dbos.RunWorkflow(dbosContext, checkoutWorkflow, order)
    url, err := dbos.GetEvent[string](dbosContext, handle.GetWorkflowID(), PaymentURLKey, 30*time.Second)
    if err != nil {
        http.Error(w, "Timeout", http.StatusGatewayTimeout)
        return
    }
    http.Redirect(w, r, url, http.StatusSeeOther)
}
```

### Durable Sleep

```go
func scheduledTaskWorkflow(ctx dbos.DBOSContext, delay time.Duration) (string, error) {
    _, err := dbos.Sleep(ctx, delay)
    if err != nil {
        return "", err
    }
    return dbos.RunAsStep(ctx, func(stepCtx context.Context) (string, error) {
        return executeTask(stepCtx)
    })
}
```

### Scheduled Workflows (Cron)

```go
func main() {
    dbosContext := initDBOS()

    // Run daily at 2:00 AM
    dbos.RegisterWorkflow(dbosContext, dailyBackup,
        dbos.WithSchedule("0 0 2 * * *"))

    // Run every 15 minutes
    dbos.RegisterWorkflow(dbosContext, healthCheck,
        dbos.WithSchedule("0 */15 * * * *"))

    dbos.Launch(dbosContext)
}
```

### Idempotent Workflows

```go
func handlePayment(dbosContext dbos.DBOSContext, payment Payment) error {
    // Same workflow ID = same execution (prevents duplicates)
    handle, err := dbos.RunWorkflow(dbosContext, processPayment, payment,
        dbos.WithWorkflowID(payment.ID))
    if err != nil {
        return err
    }
    _, err = handle.GetResult()
    return err
}
```

### Priority Queues

```go
queue := dbos.NewWorkflowQueue(dbosContext, "priority_queue",
    dbos.WithPriorityEnabled())

// Lower number = higher priority
dbos.RunWorkflow(ctx, urgentTask, data,
    dbos.WithQueue(queue.Name),
    dbos.WithPriority(1))  // High priority
```

### Child Workflows

```go
func parentWorkflow(ctx dbos.DBOSContext, items []Item) ([]Result, error) {
    var results []Result
    for _, item := range items {
        handle, err := dbos.RunWorkflow(ctx, processItemWorkflow, item)
        if err != nil {
            return nil, err
        }
        result, err := handle.GetResult()
        if err != nil {
            return nil, err
        }
        results = append(results, result)
    }
    return results, nil
}
```

### HTTP Integration with Gin

```go
func main() {
    dbosContext := initDBOS()
    dbos.RegisterWorkflow(dbosContext, orderWorkflow)
    dbos.Launch(dbosContext)
    defer dbos.Shutdown(dbosContext, 5*time.Second)

    r := gin.Default()
    r.POST("/orders", func(c *gin.Context) {
        var order Order
        if err := c.ShouldBindJSON(&order); err != nil {
            c.JSON(400, gin.H{"error": err.Error()})
            return
        }
        handle, err := dbos.RunWorkflow(dbosContext, orderWorkflow, order)
        if err != nil {
            c.JSON(500, gin.H{"error": err.Error()})
            return
        }
        c.JSON(202, gin.H{"workflow_id": handle.GetWorkflowID(), "status": "processing"})
    })
    r.Run(":8080")
}
```

## Critical Rules

### Determinism Requirements
1. **No direct randomness** - Wrap in steps
2. **No direct time access** - Use `dbos.Sleep()` or wrap `time.Now()` in steps
3. **No direct I/O** - All API calls, file access, DB queries must be steps
4. **No goroutines** - Use queues or child workflows for parallelism
5. **No global state mutation** - Read-only access to globals

### Step Requirements
- Must accept `context.Context` as first parameter
- Must return `(T, error)` where T is serializable
- Use `dbos.WithStepName()` for clarity in logs/debugging

### Workflow Requirements
- Must accept `dbos.DBOSContext` as first parameter
- Must accept exactly one serializable input parameter
- Must return exactly one serializable output and error
- Must be registered before `dbos.Launch()`
