---
name: dbos-python
description: "DBOS durable execution framework for Python. Use when implementing resilient, failure-recoverable applications with durable workflows, steps, transactions, queues, and workflow communication patterns. Triggers on DBOS Python, durable execution Python, resilient workflows Python, saga pattern Python, or when building fault-tolerant Python applications."
---

# DBOS for Python

DBOS provides durable execution so you can write programs that are resilient to any failure. When interrupted, workflows automatically resume from their last completed step. Uses PostgreSQL or SQLite as its system database.

## Core Decorators

| Decorator | Purpose |
|-----------|---------|
| `@DBOS.workflow()` | Marks durable, recoverable execution units |
| `@DBOS.step()` | Annotates helper functions for non-deterministic operations |
| `@DBOS.transaction()` | Database-optimized steps executing as single transactions |
| `@DBOS.scheduled()` | Runs workflows on cron schedules |

## Essential Patterns

### Basic Application Structure

```python
import os
from dbos import DBOS, DBOSConfig

config: DBOSConfig = {
    "name": "my-app",
    "system_database_url": os.environ.get("DBOS_SYSTEM_DATABASE_URL"),
}
DBOS(config=config)

@DBOS.step()
def call_external_api(data: str) -> dict:
    response = requests.post("https://api.example.com", json={"data": data})
    return response.json()

@DBOS.step()
def process_result(result: dict) -> str:
    return result.get("status", "unknown")

@DBOS.workflow()
def my_workflow(input_data: str) -> str:
    api_result = call_external_api(input_data)
    status = process_result(api_result)
    return status

if __name__ == "__main__":
    DBOS.launch()
    result = my_workflow("hello")
```

### Steps with Retry Configuration

```python
@DBOS.step(retries_allowed=True, max_attempts=10)
def unreliable_api_call(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text
```

### Database Transactions

```python
from sqlalchemy import Table, Column, String, MetaData

metadata = MetaData()
users = Table("users", metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
)

@DBOS.transaction()
def create_user(user_id: str, name: str) -> None:
    DBOS.sql_session.execute(
        users.insert().values(id=user_id, name=name)
    )

@DBOS.transaction()
def get_user(user_id: str) -> dict:
    result = DBOS.sql_session.execute(
        users.select().where(users.c.id == user_id)
    ).fetchone()
    return dict(result) if result else None

@DBOS.workflow()
def user_workflow(user_id: str, name: str) -> dict:
    create_user(user_id, name)
    return get_user(user_id)
```

### Background Workflows

```python
from dbos import WorkflowHandle

@DBOS.workflow()
def background_workflow(data: str) -> str:
    return long_running_task(data)

# Start without blocking
handle: WorkflowHandle = DBOS.start_workflow(background_workflow, "input")
print(f"Workflow ID: {handle.workflow_id}")

# Later, retrieve result
result = handle.get_result()
```

### Queue-Based Processing

```python
from dbos import Queue

queue = Queue("task_queue", worker_concurrency=5)

# Or with rate limiting
rate_limited_queue = Queue(
    "api_queue",
    limiter={"limit": 100, "period": 60}  # 100 requests per minute
)

@DBOS.workflow()
def process_task(task_id: int) -> str:
    return f"Completed task {task_id}"

# Enqueue work
handle = queue.enqueue(process_task, 123)
result = handle.get_result()
```

### Queue with Partitioning

```python
queue = Queue("user_queue", worker_concurrency=10)

@DBOS.workflow()
def process_user_action(user_id: str, action: dict) -> str:
    return f"Processed {action} for {user_id}"

# Actions for same user_id processed in order
queue.enqueue(process_user_action, "user_123", {"type": "update"},
              partition_key="user_123")
```

### Workflow Communication - Messages

```python
@DBOS.workflow()
def checkout_workflow(order_id: str) -> str:
    # Wait up to 5 minutes for payment confirmation
    payment_result = DBOS.recv(topic="payment", timeout_seconds=300)

    if payment_result is None:
        return "payment_timeout"
    if payment_result["status"] == "completed":
        return "order_completed"
    return "payment_failed"

def payment_webhook(workflow_id: str, status: str):
    DBOS.send(workflow_id, {"status": status}, topic="payment")
```

### Workflow Communication - Events

```python
@DBOS.workflow()
def checkout_workflow(order: dict) -> str:
    payment_url = generate_payment_url(order)
    DBOS.set_event("payment_url", payment_url)
    return "completed"

def checkout_handler(order: dict):
    handle = DBOS.start_workflow(checkout_workflow, order)
    url = DBOS.get_event(handle.workflow_id, "payment_url", timeout_seconds=30)
    return {"redirect_url": url}
```

### Durable Sleep

```python
@DBOS.workflow()
def scheduled_task_workflow(delay_seconds: int, task: str) -> str:
    DBOS.sleep(delay_seconds)
    return execute_task(task)
```

### Scheduled Workflows (Cron)

```python
@DBOS.scheduled("0 2 * * *")  # Daily at 2:00 AM
@DBOS.workflow()
def daily_backup(scheduled_time, actual_time):
    perform_backup()
    return "backup_completed"

@DBOS.scheduled("*/15 * * * *")  # Every 15 minutes
@DBOS.workflow()
def health_check(scheduled_time, actual_time):
    return check_system_health()

if __name__ == "__main__":
    DBOS.launch()  # Schedules start automatically
```

### Idempotent Workflows

```python
from dbos import SetWorkflowID

@DBOS.workflow()
def process_payment(payment_id: str, amount: float) -> str:
    return "processed"

def handle_payment(payment_id: str, amount: float):
    # Same workflow ID = same execution (prevents duplicates)
    with SetWorkflowID(f"payment-{payment_id}"):
        result = process_payment(payment_id, amount)
    return result
```

### Workflow Timeout

```python
from dbos import SetWorkflowTimeout

@DBOS.workflow()
def long_workflow(data: str) -> str:
    return "completed"

# Workflow times out after 1 hour
with SetWorkflowTimeout(3600):
    result = long_workflow("input")
```

### Debouncing

```python
from dbos import Debouncer

@DBOS.workflow()
def process_user_input(user_id: str, final_input: str) -> str:
    return f"Processing: {final_input}"

debouncer = Debouncer.create(process_user_input)

def on_user_keystroke(user_id: str, current_input: str):
    debouncer.debounce(user_id, 60, current_input)
```

### Async Workflows

```python
import aiohttp

@DBOS.step()
async def async_fetch(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()

@DBOS.workflow()
async def async_workflow(urls: list[str]) -> list[str]:
    await DBOS.sleep_async(1)
    results = []
    for url in urls:
        result = await async_fetch(url)
        results.append(result)
    return results
```

### FastAPI Integration

```python
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@DBOS.step()
def process_order(order_id: str) -> dict:
    return {"order_id": order_id, "status": "processed"}

@app.post("/orders/{order_id}")
@DBOS.workflow()
def create_order(order_id: str) -> dict:
    return process_order(order_id)

@app.get("/orders/{order_id}/status")
def get_order_status(order_id: str):
    workflows = DBOS.list_workflows(workflow_id=order_id)
    return workflows[0] if workflows else None

if __name__ == "__main__":
    DBOS.launch()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Class-Based Workflows

```python
from dbos import DBOSConfiguredInstance

@DBOS.dbos_class()
class DataProcessor(DBOSConfiguredInstance):
    def __init__(self, source_url: str):
        self.source_url = source_url
        super().__init__(config_name=source_url)

    @DBOS.step()
    def fetch_data(self) -> dict:
        return requests.get(self.source_url).json()

    @DBOS.workflow()
    def process(self) -> dict:
        data = self.fetch_data()
        return {"transformed": data}

# Instantiate before DBOS.launch()
processor = DataProcessor("https://api.example.com/data")

if __name__ == "__main__":
    DBOS.launch()
    result = processor.process()
```

### Workflow Introspection

```python
# List workflows by status
pending = DBOS.list_workflows(status="PENDING", limit=10)
completed = DBOS.list_workflows(status="SUCCESS", sort_desc=True)

# Get workflow steps
steps = DBOS.list_workflow_steps(workflow_id)

# Control operations
DBOS.cancel_workflow(workflow_id)
DBOS.resume_workflow(workflow_id)
DBOS.fork_workflow(workflow_id, start_step=3)
```

### Testing

```python
import pytest
from dbos import DBOS, DBOSConfig

@pytest.fixture()
def dbos_test():
    DBOS.destroy()
    config: DBOSConfig = {"name": "test-app"}
    DBOS(config=config)
    DBOS.reset_system_database()
    DBOS.launch()
    yield
    DBOS.destroy()

def test_workflow(dbos_test):
    result = my_workflow("test_input")
    assert result == "expected_output"
```

## Critical Rules

### Determinism Requirements
1. **No direct randomness** - Wrap in steps
2. **No direct time access** - Use `DBOS.sleep()` or wrap in steps
3. **No direct I/O** - All API calls, file access must be steps
4. **No threads in workflows** - Use queues or child workflows

### Step Requirements
- Inputs and outputs must be serializable (JSON-compatible)
- Should be idempotent when possible
- Use `retries_allowed=True` for transient failures

### Workflow Requirements
- Must be decorated with `@DBOS.workflow()`
- Input parameters must be serializable
- Return value must be serializable
- Call `DBOS.launch()` before executing workflows

### Transaction Requirements
- Only use `@DBOS.transaction()` for database operations
- Works with PostgreSQL via SQLAlchemy
- Access database via `DBOS.sql_session`

## Configuration Options

```python
config: DBOSConfig = {
    "name": "my-app",
    "system_database_url": "postgresql://...",
    "application_database_url": "postgresql://...",
    "log_level": "INFO",
    "application_version": "1.0.0",
}
```
