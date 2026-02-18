---
name: otel-go
description: "OpenTelemetry instrumentation for Go. Use when adding observability with distributed tracing, metrics, logging, context propagation, and exporters (OTLP, Jaeger, Prometheus). Triggers on OpenTelemetry Go, OTel Go, tracing Go, instrumentation Go, observability Go, or when debugging distributed Go systems."
---

# OpenTelemetry for Go

OpenTelemetry (OTel) is the observability framework for generating and collecting traces, metrics, and logs from distributed systems.

## Signal Status

| Signal | Status |
|--------|--------|
| Traces | **Stable** |
| Metrics | **Stable** |
| Logs | Beta |

## Core Packages

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
    "go.opentelemetry.io/otel/metric"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"

    // SDK
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    sdkmetric "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/sdk/resource"

    // Semantic conventions
    semconv "go.opentelemetry.io/otel/semconv/v1.37.0"
)
```

## Complete SDK Setup

```go
func setupOTelSDK(ctx context.Context) (shutdown func(context.Context) error, err error) {
    var shutdownFuncs []func(context.Context) error

    shutdown = func(ctx context.Context) error {
        var err error
        for _, fn := range shutdownFuncs {
            err = errors.Join(err, fn(ctx))
        }
        return err
    }

    // Create resource with service info
    res, err := resource.Merge(
        resource.Default(),
        resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName("my-service"),
            semconv.ServiceVersion("1.0.0"),
            semconv.DeploymentEnvironmentName("production"),
        ),
    )
    if err != nil {
        return nil, err
    }

    // Set up propagator
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    // Set up trace provider
    traceExporter, err := otlptracegrpc.New(ctx)
    if err != nil {
        return nil, err
    }

    tracerProvider := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(traceExporter),
        sdktrace.WithResource(res),
        sdktrace.WithSampler(sdktrace.AlwaysSample()),
    )
    shutdownFuncs = append(shutdownFuncs, tracerProvider.Shutdown)
    otel.SetTracerProvider(tracerProvider)

    // Set up meter provider
    metricExporter, err := otlpmetricgrpc.New(ctx)
    if err != nil {
        return nil, err
    }

    meterProvider := metric.NewMeterProvider(
        metric.WithResource(res),
        metric.WithReader(metric.NewPeriodicReader(metricExporter,
            metric.WithInterval(30*time.Second))),
    )
    shutdownFuncs = append(shutdownFuncs, meterProvider.Shutdown)
    otel.SetMeterProvider(meterProvider)

    return shutdown, nil
}

func main() {
    ctx := context.Background()
    shutdown, err := setupOTelSDK(ctx)
    if err != nil {
        panic(err)
    }
    defer shutdown(ctx)
    // Application code...
}
```

## Tracing

### Creating Spans

```go
var tracer = otel.Tracer("example.io/myapp")

func handleRequest(ctx context.Context) error {
    ctx, span := tracer.Start(ctx, "handleRequest")
    defer span.End()

    result, err := processData(ctx)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return err
    }

    span.SetStatus(codes.Ok, "success")
    return nil
}
```

### Nested Spans (Parent-Child)

```go
func parentFunction(ctx context.Context) {
    ctx, parentSpan := tracer.Start(ctx, "parent-operation")
    defer parentSpan.End()
    childFunction(ctx)  // Child inherits parent context
}

func childFunction(ctx context.Context) {
    ctx, childSpan := tracer.Start(ctx, "child-operation")
    defer childSpan.End()
}
```

### Span Attributes

```go
ctx, span := tracer.Start(ctx, "operation",
    trace.WithAttributes(
        attribute.String("user.id", userID),
        attribute.Int("request.size", len(body)),
    ))
defer span.End()

// Add attributes later
span.SetAttributes(
    attribute.Bool("cache.hit", cacheHit),
    semconv.HTTPRequestMethodGet,
    semconv.HTTPResponseStatusCode(200),
)
```

### Span Events

```go
span.AddEvent("Acquiring lock")
span.AddEvent("Processing started", trace.WithAttributes(
    attribute.Int("items.count", len(items)),
))
```

### Error Handling

```go
result, err := riskyOperation()
if err != nil {
    span.RecordError(err)
    span.SetStatus(codes.Error, "operation failed")
    return err
}
span.SetStatus(codes.Ok, "completed successfully")
```

### Getting Current Span

```go
func someFunction(ctx context.Context) {
    span := trace.SpanFromContext(ctx)
    span.AddEvent("Something happened")
}
```

## Metrics

### Acquiring a Meter

```go
var meter = otel.Meter("example.io/myapp")
```

### Counter

```go
requestCounter, _ := meter.Int64Counter(
    "http.requests.total",
    metric.WithDescription("Total HTTP requests"),
    metric.WithUnit("{request}"),
)

requestCounter.Add(ctx, 1,
    metric.WithAttributes(
        semconv.HTTPRequestMethodGet,
        semconv.HTTPResponseStatusCode(200),
    ))
```

### UpDown Counter

```go
activeConnections, _ := meter.Int64UpDownCounter(
    "connections.active",
    metric.WithDescription("Currently active connections"),
)

activeConnections.Add(ctx, 1)   // Connection opened
activeConnections.Add(ctx, -1)  // Connection closed
```

### Histogram

```go
requestDuration, _ := meter.Float64Histogram(
    "http.request.duration",
    metric.WithDescription("HTTP request duration"),
    metric.WithUnit("s"),
)

start := time.Now()
// ... handle request ...
requestDuration.Record(ctx, time.Since(start).Seconds(),
    metric.WithAttributes(attribute.String("http.route", "/api/users")))
```

### Observable Gauge (Async)

```go
memoryGauge, _ := meter.Int64ObservableGauge(
    "process.memory.heap",
    metric.WithDescription("Heap memory usage"),
    metric.WithInt64Callback(func(_ context.Context, o metric.Int64Observer) error {
        var m runtime.MemStats
        runtime.ReadMemStats(&m)
        o.Observe(int64(m.HeapAlloc))
        return nil
    }),
)
```

## Context Propagation

### HTTP Client (Outgoing)

```go
import "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

client := &http.Client{
    Transport: otelhttp.NewTransport(http.DefaultTransport),
}
req, _ := http.NewRequestWithContext(ctx, "GET", "https://api.example.com", nil)
resp, err := client.Do(req)
```

### HTTP Server (Incoming)

```go
handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    span := trace.SpanFromContext(ctx)
    span.AddEvent("Processing request")
})

wrappedHandler := otelhttp.NewHandler(handler, "my-server")
http.ListenAndServe(":8080", wrappedHandler)
```

### gRPC

```go
import "go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"

// Server
server := grpc.NewServer(grpc.StatsHandler(otelgrpc.NewServerHandler()))

// Client
conn, _ := grpc.Dial(target, grpc.WithStatsHandler(otelgrpc.NewClientHandler()))
```

## Exporters

### OTLP (Production)

```go
// gRPC
traceExporter, _ := otlptracegrpc.New(ctx,
    otlptracegrpc.WithEndpoint("localhost:4317"),
    otlptracegrpc.WithInsecure(),
)

// HTTP
traceExporter, _ := otlptracehttp.New(ctx,
    otlptracehttp.WithEndpoint("localhost:4318"),
    otlptracehttp.WithInsecure(),
)
```

### Console (Development)

```go
traceExporter, _ := stdouttrace.New(stdouttrace.WithPrettyPrint())
```

### Prometheus (Metrics)

```go
promExporter, _ := prometheus.New()
meterProvider := metric.NewMeterProvider(metric.WithReader(promExporter))
http.Handle("/metrics", promhttp.Handler())
```

## Sampling

```go
tracerProvider := sdktrace.NewTracerProvider(
    sdktrace.WithSampler(sdktrace.AlwaysSample()),        // Dev
    sdktrace.WithSampler(sdktrace.TraceIDRatioBased(0.1)), // 10%
    sdktrace.WithSampler(sdktrace.ParentBased(             // Parent-based
        sdktrace.TraceIDRatioBased(0.1),
    )),
)
```

## Environment Variables

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="service.version=1.0.0,deployment.environment=production"
export OTEL_TRACES_SAMPLER="parentbased_traceidratio"
export OTEL_TRACES_SAMPLER_ARG="0.1"
```

## Best Practices

1. **Always defer span.End()** - Ensures spans are closed even on panic
2. **Pass context everywhere** - Required for trace propagation
3. **Use semantic conventions** - `semconv` package for standard attribute names
4. **Set span status on errors** - `RecordError()` doesn't set status automatically
5. **Use batch exporters** - `WithBatcher()` for production performance
6. **Implement graceful shutdown** - Call `Shutdown()` on providers
7. **Use appropriate sampling** - 100% sampling is expensive in production
8. **Instrument at boundaries** - HTTP handlers, gRPC methods, DB calls
9. **Keep cardinality low** - Avoid high-cardinality attributes on metrics
