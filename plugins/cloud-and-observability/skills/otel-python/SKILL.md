---
name: otel-python
description: "OpenTelemetry instrumentation for Python. Use when adding observability with distributed tracing, metrics, logging, automatic instrumentation, context propagation, and exporters (OTLP, Jaeger, Prometheus). Triggers on OpenTelemetry Python, OTel Python, tracing Python, instrumentation Python, observability Python, or when debugging distributed Python systems."
---

# OpenTelemetry for Python

OpenTelemetry (OTel) is the observability framework for generating and collecting traces, metrics, and logs from distributed systems.

## Signal Status

| Signal | Status |
|--------|--------|
| Traces | **Stable** |
| Metrics | **Stable** |
| Logs | **Stable** |

## Installation

```bash
# Core packages
pip install opentelemetry-api opentelemetry-sdk

# Automatic instrumentation
pip install opentelemetry-distro
opentelemetry-bootstrap -a install

# OTLP exporters
pip install opentelemetry-exporter-otlp-proto-grpc
```

## Complete SDK Setup

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

def setup_otel():
    resource = Resource.create({
        SERVICE_NAME: "my-service",
        SERVICE_VERSION: "1.0.0",
        "deployment.environment": "production",
    })

    set_global_textmap(CompositePropagator([
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator(),
    ]))

    # TracerProvider
    trace_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    # MeterProvider
    metric_exporter = OTLPMetricExporter(endpoint="localhost:4317", insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=30000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    return trace_provider, meter_provider

def shutdown_otel(trace_provider, meter_provider):
    trace_provider.shutdown()
    meter_provider.shutdown()
```

## Automatic Instrumentation

```bash
opentelemetry-instrument \
    --traces_exporter otlp \
    --metrics_exporter otlp \
    --logs_exporter otlp \
    --service_name my-service \
    python app.py

# Console export (development)
opentelemetry-instrument \
    --traces_exporter console \
    --service_name my-service \
    flask run -p 8080
```

## Tracing

### Creating Spans

```python
from opentelemetry import trace

tracer = trace.get_tracer("my.app.tracer")

# Context manager
def process_request(request):
    with tracer.start_as_current_span("process-request") as span:
        span.set_attribute("request.id", request.id)
        return do_work(request)

# Decorator
@tracer.start_as_current_span("do_work")
def do_work(request):
    return "result"
```

### Nested Spans

```python
def parent_operation():
    with tracer.start_as_current_span("parent") as parent_span:
        child_operation()  # Automatically linked to parent

def child_operation():
    with tracer.start_as_current_span("child") as child_span:
        pass
```

### Span Attributes

```python
from opentelemetry.semconv.trace import SpanAttributes

span = trace.get_current_span()

# Custom attributes
span.set_attribute("user.id", "12345")
span.set_attribute("order.total", 99.99)

# Semantic conventions
span.set_attribute(SpanAttributes.HTTP_METHOD, "GET")
span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 200)
span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
```

### Span Events

```python
span = trace.get_current_span()
span.add_event("Cache lookup started")
span.add_event("Cache miss", {"cache.key": "user:123", "cache.type": "redis"})
```

### Error Handling

```python
from opentelemetry.trace import Status, StatusCode

span = trace.get_current_span()

try:
    result = risky_operation()
except Exception as ex:
    span.record_exception(ex)
    span.set_status(Status(StatusCode.ERROR, str(ex)))
    raise

span.set_status(Status(StatusCode.OK))
```

### Manual Context Propagation

```python
from opentelemetry.propagate import inject, extract

# Inject into headers (outgoing)
headers = {}
inject(headers)

# Extract from headers (incoming)
ctx = extract(headers)
with tracer.start_as_current_span("child", context=ctx) as span:
    pass
```

## Metrics

### Acquiring a Meter

```python
from opentelemetry import metrics
meter = metrics.get_meter("my.app.meter")
```

### Counter

```python
request_counter = meter.create_counter(
    name="http.requests.total",
    description="Total HTTP requests",
    unit="1",
)

request_counter.add(1, {"http.method": "GET", "http.status_code": 200})
```

### UpDown Counter

```python
active_connections = meter.create_up_down_counter("connections.active")
active_connections.add(1)   # Connection opened
active_connections.add(-1)  # Connection closed
```

### Histogram

```python
request_duration = meter.create_histogram(
    name="http.request.duration",
    unit="s",
)

start = time.time()
# ... process ...
request_duration.record(time.time() - start, {"http.route": "/api/users"})
```

### Observable Gauge (Async)

```python
from opentelemetry.metrics import CallbackOptions, Observation

def get_memory_usage(options: CallbackOptions):
    import psutil
    mem = psutil.virtual_memory()
    yield Observation(mem.used, {"memory.type": "used"})

meter.create_observable_gauge(
    name="system.memory.usage",
    callbacks=[get_memory_usage],
    unit="By",
)
```

## Framework Integration

### Flask

```python
from flask import Flask
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/")
def index():
    return "Hello!"  # Automatic span created
```

### FastAPI

```python
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def index():
    return {"message": "Hello!"}
```

### Requests

```python
from opentelemetry.instrumentation.requests import RequestsInstrumentor
RequestsInstrumentor().instrument()
# All requests.* calls now create spans
```

### SQLAlchemy

```python
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
engine = create_engine("postgresql://...")
SQLAlchemyInstrumentor().instrument(engine=engine)
```

## Exporters

### OTLP

```python
# gRPC
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
trace_exporter = OTLPSpanExporter(endpoint="localhost:4317", insecure=True)

# HTTP
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
trace_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
```

### Console

```python
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
trace_exporter = ConsoleSpanExporter()
```

### Prometheus

```python
from prometheus_client import start_http_server
from opentelemetry.exporter.prometheus import PrometheusMetricReader

start_http_server(port=8000)
reader = PrometheusMetricReader()
meter_provider = MeterProvider(metric_readers=[reader])
```

## Environment Variables

```bash
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="service.version=1.0.0"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_TRACES_EXPORTER="otlp"
export OTEL_METRICS_EXPORTER="otlp"
export OTEL_LOGS_EXPORTER="otlp"
export OTEL_TRACES_SAMPLER="parentbased_traceidratio"
export OTEL_TRACES_SAMPLER_ARG="0.1"
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
```

## Complete Flask Example

```python
from flask import Flask, request
from opentelemetry import trace, metrics
from opentelemetry.instrumentation.flask import FlaskInstrumentor
import random
import time

tracer = trace.get_tracer("dice-roller")
meter = metrics.get_meter("dice-roller")

roll_counter = meter.create_counter("dice.rolls")
roll_histogram = meter.create_histogram("dice.roll.duration", unit="s")

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

@app.route("/roll")
def roll_dice():
    player = request.args.get("player", "anonymous")

    with tracer.start_as_current_span("roll") as span:
        start = time.time()
        result = random.randint(1, 6)

        span.set_attribute("player.name", player)
        span.set_attribute("dice.result", result)

        roll_counter.add(1, {"player": player, "result": result})
        roll_histogram.record(time.time() - start, {"player": player})

        return {"player": player, "result": result}

if __name__ == "__main__":
    app.run(port=8080)
```

## Best Practices

1. **Use automatic instrumentation** - Start with `opentelemetry-instrument`
2. **Add manual spans** - Enhance auto-instrumentation with business logic spans
3. **Use semantic conventions** - Import from `opentelemetry.semconv`
4. **Batch exports** - Use `BatchSpanProcessor` for production
5. **Set service name** - Always identify your service via resource attributes
6. **Handle shutdown** - Call `shutdown()` on providers for clean exit
7. **Use context managers** - Prefer `with tracer.start_as_current_span()`
8. **Record exceptions** - Use `record_exception()` AND `set_status(ERROR)`
9. **Keep cardinality low** - Avoid high-cardinality attribute values on metrics
