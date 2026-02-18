# Tilt API & Scripting Reference

Tilt includes a Kubernetes-style API server for programmatic access to all resources.

## CLI Commands (kubectl-style)

### Discovery

```bash
# List all available API resource types
tilt api-resources

# Get documentation for a resource type
tilt explain uiresource
tilt explain cmd
tilt explain portforward
```

### Querying Resources

```bash
# List all resources of a type
tilt get uiresources
tilt get cmds
tilt get filewatches
tilt get portforwards

# Get specific resource
tilt get uiresource my-app

# Output formats
tilt get uiresource my-app -o json
tilt get uiresource my-app -o yaml
tilt get uiresources -o wide

# JSONPath queries
tilt get uiresource my-app -o jsonpath='{.status.runtimeStatus}'
tilt get uiresources -o jsonpath='{.items[*].metadata.name}'

# Human-readable details
tilt describe uiresource my-app
```

## API Resource Types

### Core Resources

| Resource | Description |
|----------|-------------|
| `Session` | Current Tilt session state |
| `Tiltfile` | Tiltfile evaluation status |
| `Cmd` | Local commands (from local_resource) |
| `FileWatch` | File watch configurations |
| `ConfigMap` | Configuration data |
| `Extension` | Loaded extensions |

### Kubernetes Resources

| Resource | Description |
|----------|-------------|
| `Cluster` | Connected K8s cluster info |
| `KubernetesApply` | Applied K8s manifests |
| `KubernetesDiscovery` | Discovered K8s objects |
| `PodLogStream` | Pod log streaming config |
| `PortForward` | Active port forwards |

### UI Resources

| Resource | Description |
|----------|-------------|
| `UISession` | UI session state |
| `UIResource` | Resource as shown in UI (build status, logs, etc.) |
| `UIButton` | Custom UI buttons |
| `ToggleButton` | Toggle buttons in UI |

### Container Resources

| Resource | Description |
|----------|-------------|
| `DockerImage` | Docker image builds |
| `CmdImage` | Custom build images |
| `LiveUpdate` | Live update configurations |
| `ImageMap` | Image name mappings |
| `DockerComposeService` | Docker Compose services |

## Scripting Examples

### Check Resource Status

```bash
#!/bin/bash
# check-tilt-status.sh - Check if all resources are healthy

# Get all resources with errors
errors=$(tilt get uiresources -o json | jq -r '
  .items[] |
  select(.status.runtimeStatus == "error" or .status.updateStatus == "error") |
  .metadata.name
')

if [ -n "$errors" ]; then
  echo "Resources with errors:"
  echo "$errors"
  exit 1
else
  echo "All resources healthy"
  exit 0
fi
```

### Get Build Times

```bash
#!/bin/bash
# build-times.sh - Get build times for all resources

tilt get uiresources -o json | jq -r '
  .items[] |
  select(.status.buildHistory != null) |
  .status.buildHistory[0] as $build |
  "\(.metadata.name): \($build.startTime) - \($build.finishTime // "in progress")"
'
```

### Monitor Port Forwards

```bash
#!/bin/bash
# list-ports.sh - List all active port forwards

tilt get portforwards -o json | jq -r '
  .items[] |
  "\(.metadata.name): localhost:\(.spec.forwards[0].localPort) -> \(.spec.forwards[0].containerPort)"
'
```

### Wait for Resource Ready

```bash
#!/bin/bash
# wait-for-ready.sh - Wait for a resource to be ready

RESOURCE=$1
TIMEOUT=${2:-300}

echo "Waiting for $RESOURCE to be ready..."

start_time=$(date +%s)
while true; do
  status=$(tilt get uiresource "$RESOURCE" -o jsonpath='{.status.runtimeStatus}' 2>/dev/null)

  if [ "$status" = "ok" ]; then
    echo "$RESOURCE is ready"
    exit 0
  fi

  current_time=$(date +%s)
  elapsed=$((current_time - start_time))

  if [ $elapsed -ge $TIMEOUT ]; then
    echo "Timeout waiting for $RESOURCE"
    exit 1
  fi

  sleep 2
done
```

### Export Resource Definitions

```bash
#!/bin/bash
# export-resources.sh - Export all resource definitions

mkdir -p tilt-export

for resource in $(tilt api-resources -o name); do
  tilt get "$resource" -o yaml > "tilt-export/${resource}.yaml" 2>/dev/null
done

echo "Exported to tilt-export/"
```

### CI Health Check

```bash
#!/bin/bash
# ci-health-check.sh - Health check for CI pipelines

# Run with: tilt ci -- ./ci-health-check.sh

max_wait=300
interval=10
elapsed=0

while [ $elapsed -lt $max_wait ]; do
  # Count resources by status
  total=$(tilt get uiresources -o json | jq '.items | length')
  ok=$(tilt get uiresources -o json | jq '[.items[] | select(.status.runtimeStatus == "ok")] | length')
  errors=$(tilt get uiresources -o json | jq '[.items[] | select(.status.runtimeStatus == "error")] | length')

  echo "Status: $ok/$total ready, $errors errors"

  if [ "$errors" -gt 0 ]; then
    echo "Build failed - errors detected"
    tilt get uiresources -o json | jq -r '.items[] | select(.status.runtimeStatus == "error") | .metadata.name'
    exit 1
  fi

  if [ "$ok" -eq "$total" ]; then
    echo "All resources ready"
    exit 0
  fi

  sleep $interval
  elapsed=$((elapsed + interval))
done

echo "Timeout waiting for resources"
exit 1
```

## REST API Access

The Tilt API server listens on `localhost:10350` by default.

### Direct HTTP Access

```bash
# List API groups
curl -s http://localhost:10350/apis | jq

# Get specific resource
curl -s http://localhost:10350/apis/tilt.dev/v1alpha1/uiresources | jq

# OpenAPI spec
curl -s http://localhost:10350/openapi/v2 > tilt-openapi.json
```

### Python Client Example

```python
#!/usr/bin/env python3
"""tilt_client.py - Simple Tilt API client"""

import requests
import json

TILT_API = "http://localhost:10350"

def get_resources(resource_type):
    """Get all resources of a type."""
    url = f"{TILT_API}/apis/tilt.dev/v1alpha1/{resource_type}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def get_resource(resource_type, name):
    """Get a specific resource."""
    url = f"{TILT_API}/apis/tilt.dev/v1alpha1/{resource_type}/{name}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def list_unhealthy():
    """List resources with errors."""
    resources = get_resources("uiresources")
    unhealthy = []
    for item in resources.get("items", []):
        status = item.get("status", {})
        if status.get("runtimeStatus") == "error":
            unhealthy.append(item["metadata"]["name"])
    return unhealthy

if __name__ == "__main__":
    unhealthy = list_unhealthy()
    if unhealthy:
        print(f"Unhealthy resources: {unhealthy}")
    else:
        print("All resources healthy")
```

### Go Client

Tilt provides Go types in `github.com/tilt-dev/tilt/pkg/apis`:

```go
package main

import (
    "context"
    "fmt"

    "github.com/tilt-dev/tilt/pkg/apis/core/v1alpha1"
    "k8s.io/client-go/rest"
)

func main() {
    config := &rest.Config{
        Host: "http://localhost:10350",
    }

    // Use Kubernetes client-go patterns
    // ...
}
```

## Tiltfile Integration

### Expose Custom Data via ConfigMap

```python
# Tiltfile - expose build info for scripts

# Create ConfigMap with build metadata
k8s_yaml(blob("""
apiVersion: v1
kind: ConfigMap
metadata:
  name: build-info
data:
  version: "{version}"
  commit: "{commit}"
""".format(
  version=local('git describe --tags', quiet=True),
  commit=local('git rev-parse HEAD', quiet=True)[:8]
)))
```

### Trigger from External Script

```bash
#!/bin/bash
# trigger-rebuild.sh - Trigger rebuild of a resource

RESOURCE=$1

# Use tilt trigger command
tilt trigger "$RESOURCE"

# Or touch a watched file to trigger rebuild
# touch src/main.go
```

## Metrics & Monitoring

### Prometheus Metrics

Tilt exposes Prometheus metrics at `localhost:10350/metrics`:

```bash
# Scrape metrics
curl -s http://localhost:10350/metrics | grep tilt_

# Example metrics:
# tilt_build_duration_seconds
# tilt_resource_count
# tilt_apiserver_request_total
```

### Grafana Dashboard

```bash
# Export metrics for Grafana
curl -s http://localhost:10350/metrics > tilt-metrics.txt
```

## Common Patterns

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit - Check Tilt status before commit

if pgrep -x "tilt" > /dev/null; then
  errors=$(tilt get uiresources -o json 2>/dev/null | jq '[.items[] | select(.status.runtimeStatus == "error")] | length')
  if [ "$errors" -gt 0 ]; then
    echo "Warning: Tilt has $errors resources with errors"
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
fi
```

### IDE Integration

```bash
#!/bin/bash
# tilt-status.sh - For IDE status bar integration

if ! pgrep -x "tilt" > /dev/null; then
  echo "TILT:OFF"
  exit 0
fi

status=$(tilt get uiresources -o json 2>/dev/null | jq -r '
  .items |
  if all(.status.runtimeStatus == "ok") then "OK"
  elif any(.status.runtimeStatus == "error") then "ERR"
  else "..."
  end
')

echo "TILT:$status"
```

### Slack/Discord Notification

```bash
#!/bin/bash
# notify-on-error.sh - Send notification when Tilt has errors

WEBHOOK_URL="$SLACK_WEBHOOK_URL"

check_status() {
  tilt get uiresources -o json 2>/dev/null | jq -r '
    .items[] |
    select(.status.runtimeStatus == "error") |
    "- \(.metadata.name): \(.status.lastDeployTime // "unknown")"
  '
}

errors=$(check_status)

if [ -n "$errors" ]; then
  curl -X POST "$WEBHOOK_URL" \
    -H 'Content-type: application/json' \
    -d "{\"text\": \"Tilt errors detected:\n$errors\"}"
fi
```

## References

- [Tilt API Server Docs](https://api.tilt.dev/)
- [tilt-apiserver GitHub](https://github.com/tilt-dev/tilt-apiserver)
- [Tilt Go Packages](https://pkg.go.dev/github.com/tilt-dev/tilt)
