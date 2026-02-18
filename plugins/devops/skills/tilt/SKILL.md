---
name: tilt
description: Local Kubernetes development with Tilt. Use when users need to create or modify Tiltfiles, debug multi-service applications, set up live updates, or work with the Tilt development workflow. Covers Tiltfile authoring, extensions, debugging, and integration with kubectl/Helm/Kustomize.
---

# Tilt Development Skill

## Overview

Tilt is a local Kubernetes development tool that provides:
- **Live updates**: Code changes sync instantly without full rebuilds
- **Multi-service orchestration**: Manage complex microservice environments
- **Visual dashboard**: Real-time status, logs, and debugging in browser UI
- **Extensible**: Plugin ecosystem for Helm, databases, and custom workflows

**Announce at start:** "I'm using the tilt skill to help with local Kubernetes development."

## When to Use This Skill

Use this skill when users need to:
- Create or modify Tiltfiles (Starlark configuration)
- Set up live update/hot-reload for Kubernetes development
- Debug multi-service applications locally
- Configure port forwards, resource dependencies, or build triggers
- Integrate Tilt with Helm, Kustomize, or custom build systems
- Troubleshoot Tilt errors or slow builds

## Quick Start

### Minimal Tiltfile

```python
# Tiltfile - Place in project root
docker_build('my-app', '.')
k8s_yaml('k8s/deployment.yaml')
k8s_resource('my-app', port_forwards='8080:8080')
```

### Core Commands

```bash
tilt up              # Start development session (opens UI at localhost:10350)
tilt down            # Stop all resources
tilt logs -f <name>  # Stream logs for a resource
tilt trigger <name>  # Force rebuild of a resource
tilt ci              # Run once and exit (for CI/CD)
```

## Tiltfile Authoring

Tiltfiles use Starlark (Python-like) syntax. Key functions:

### docker_build() - Build Container Images

```python
# Basic build
docker_build('my-app', '.')

# With live updates (hot reload)
docker_build('my-app', '.',
  live_update=[
    sync('.', '/app'),
    run('pip install -r requirements.txt', trigger='requirements.txt'),
  ])

# Custom Dockerfile
docker_build('my-app', '.', dockerfile='Dockerfile.dev')

# Build arguments
docker_build('my-app', '.', build_args={'NODE_ENV': 'development'})

# Ignore files (faster builds)
docker_build('my-app', '.', ignore=['node_modules', '*.md', 'tests/'])
```

### k8s_yaml() - Deploy Kubernetes Manifests

```python
# Single file
k8s_yaml('k8s/deployment.yaml')

# Multiple files
k8s_yaml(['k8s/deployment.yaml', 'k8s/service.yaml'])

# Glob patterns
k8s_yaml(glob('k8s/*.yaml'))

# Kustomize
k8s_yaml(kustomize('k8s/overlays/dev'))

# Helm
k8s_yaml(helm('charts/my-app', values=['values-dev.yaml']))
```

### k8s_resource() - Configure Resources

```python
# Port forwarding
k8s_resource('my-app', port_forwards='8080:8080')
k8s_resource('my-app', port_forwards=['8080:8080', '9090:9090'])

# Resource dependencies (start database before app)
k8s_resource('my-app', resource_deps=['postgres'])

# Custom labels for grouping in UI
k8s_resource('my-app', labels=['backend'])

# Trigger mode (manual vs auto rebuild)
k8s_resource('my-app', trigger_mode=TRIGGER_MODE_MANUAL)
```

### local_resource() - Non-Kubernetes Tasks

```python
# Run local commands
local_resource('npm-install',
  cmd='npm install',
  deps=['package.json'])

# Build frontend locally
local_resource('frontend-build',
  cmd='npm run build',
  deps=['src/'],
  resource_deps=['npm-install'])

# Serve local documentation
local_resource('docs',
  serve_cmd='mkdocs serve',
  deps=['docs/'])
```

### live_update - Hot Reloading

```python
docker_build('my-app', '.',
  live_update=[
    # Sync files from host to container
    sync('./src', '/app/src'),

    # Run command when specific files change
    run('pip install -r requirements.txt', trigger='requirements.txt'),
    run('npm install', trigger=['package.json', 'package-lock.json']),

    # Restart process in container (needs restart_process extension)
    restart_container(),
  ])
```

**Live update requirements:**
- Container must already be running
- Synced paths must exist in container
- For interpreted languages (Python, Node), often no restart needed
- For compiled languages, use `restart_container()` or rebuild

## Multi-Service Development

### Resource Dependencies

```python
# Database must start before app
k8s_yaml('k8s/postgres.yaml')
k8s_resource('postgres', port_forwards='5432:5432')

k8s_yaml('k8s/app.yaml')
k8s_resource('app',
  port_forwards='8080:8080',
  resource_deps=['postgres'])
```

### Environment Variables

```python
# Read from .env file
env = read_file('.env')

# Pass to build
docker_build('my-app', '.',
  build_args={'API_KEY': os.getenv('API_KEY')})

# Or use Kubernetes ConfigMaps/Secrets in your manifests
```

### Workload Groups

```python
# Group resources in UI
k8s_resource('api', labels=['backend'])
k8s_resource('worker', labels=['backend'])
k8s_resource('frontend', labels=['frontend'])
k8s_resource('postgres', labels=['data'])
k8s_resource('redis', labels=['data'])
```

## Debugging

### Tilt Commands

```bash
# View all resources and their status
tilt get

# Detailed resource info
tilt describe <resource-name>

# Stream logs
tilt logs -f <resource-name>

# Force rebuild
tilt trigger <resource-name>

# Open UI (if not already)
tilt up --web-mode=browser
```

### Common Issues

**Build context too large / slow builds:**
```python
# Add ignore patterns
docker_build('my-app', '.',
  ignore=['node_modules/', '.git/', '*.md', 'tests/', '__pycache__/'])

# Or use .dockerignore file
```

**Live update not syncing:**
```python
# Verify paths match container structure
live_update=[
  sync('./src', '/app/src'),  # Host path -> Container path
]

# Check container path exists
# Run: kubectl exec -it <pod> -- ls /app/
```

**Image pull backoff:**
```bash
# Check image name in k8s manifest matches docker_build
# Verify cluster can pull from your registry
kubectl describe pod <pod-name>
```

**Resource stuck in pending:**
```bash
# Check Kubernetes events
kubectl get events --sort-by='.lastTimestamp'
kubectl describe pod <pod-name>

# Common causes: resource limits, missing secrets, PVC issues
```

**Port forward not working:**
```python
# Ensure service selector matches pod labels
# Check port numbers match (host:container)
k8s_resource('app', port_forwards='8080:8080')
```

### Debug Mode

```bash
# Verbose logging
tilt up --debug

# Print Tiltfile evaluation
tilt up --print-config
```

## Extensions

Load extensions for additional functionality:

### helm_resource - Deploy Helm Charts

```python
load('ext://helm_resource', 'helm_resource', 'helm_repo')

# Add helm repository
helm_repo('bitnami', 'https://charts.bitnami.com/bitnami')

# Deploy chart
helm_resource('postgres', 'bitnami/postgresql',
  flags=['--set=auth.postgresPassword=devpass'])
```

### restart_process - In-Place Restart

```python
load('ext://restart_process', 'docker_build_with_restart')

# Automatically restart process on sync (for compiled languages)
docker_build_with_restart('my-go-app', '.',
  entrypoint='/app/server',
  live_update=[sync('./build', '/app')])
```

### namespace - Multi-Namespace Support

```python
load('ext://namespace', 'namespace_create', 'namespace_inject')

# Create namespace
namespace_create('my-dev')

# Inject namespace into all resources
namespace_inject('my-dev')
```

### configmap - ConfigMap from Files

```python
load('ext://configmap', 'configmap_create')

# Create ConfigMap from directory
configmap_create('app-config', from_file=glob('config/*'))
```

### secret - Secret from Files

```python
load('ext://secret', 'secret_create_generic')

# Create Secret
secret_create_generic('db-creds',
  from_literal={'username': 'admin', 'password': 'secret'})
```

See all extensions: https://github.com/tilt-dev/tilt-extensions

## Integration with Other Tools

### With kubectl
```bash
# Tilt manages deployments, kubectl for inspection
kubectl get pods -w        # Watch pod status
kubectl logs -f <pod>      # Alternative to tilt logs
kubectl exec -it <pod> sh  # Shell into container
```

### With Helm
```python
# Option 1: Generate manifests
k8s_yaml(helm('charts/my-app', values=['values-dev.yaml']))

# Option 2: Use helm_resource extension for full chart lifecycle
load('ext://helm_resource', 'helm_resource')
helm_resource('my-app', 'charts/my-app')
```

### With Kustomize
```python
k8s_yaml(kustomize('k8s/overlays/dev'))
```

### With kubernetes-expert Agent
Use the **kubernetes-expert** agent for:
- RBAC and security issues
- Network policy debugging
- Production deployment patterns
- Cluster-level troubleshooting

The Tilt skill focuses on local development workflows.

### With DevSpace
Both Tilt and DevSpace serve similar purposes:
- **Tilt**: Starlark config, visual UI, extension ecosystem
- **DevSpace**: YAML config, sync-focused, devcontainers

Choose based on team preference. Both integrate with the same Kubernetes clusters.

## Complete Example

```python
# Tiltfile for a Python Flask + PostgreSQL application

# Load extensions
load('ext://helm_resource', 'helm_resource', 'helm_repo')
load('ext://restart_process', 'docker_build_with_restart')

# Database (using Helm)
helm_repo('bitnami', 'https://charts.bitnami.com/bitnami')
helm_resource('postgres', 'bitnami/postgresql',
  flags=[
    '--set=auth.postgresPassword=devpass',
    '--set=auth.database=myapp',
  ],
  port_forwards='5432:5432',
  labels=['data'])

# Application with live updates
docker_build('myapp-api', './api',
  live_update=[
    sync('./api', '/app'),
    run('pip install -r requirements.txt', trigger='requirements.txt'),
  ])

k8s_yaml('k8s/api.yaml')
k8s_resource('api',
  port_forwards='8080:8080',
  resource_deps=['postgres'],
  labels=['backend'])

# Frontend (local development)
local_resource('frontend',
  serve_cmd='cd frontend && npm run dev',
  deps=['frontend/src'],
  labels=['frontend'])

# Custom resource grouping
config.define_string_list('to-run', args=True)
cfg = config.parse()
groups = {
  'backend': ['postgres', 'api'],
  'frontend': ['frontend'],
  'all': ['postgres', 'api', 'frontend'],
}
resources = cfg.get('to-run', ['all'])
for r in resources:
  if r in groups:
    config.set_enabled_resources(groups[r])
```

## API & Scripting

Tilt has a Kubernetes-style API server for programmatic access:

```bash
# List all API resources
tilt api-resources

# Get resource status as JSON
tilt get uiresources -o json

# Query specific resource
tilt get uiresource my-app -o jsonpath='{.status.runtimeStatus}'

# REST API (when Tilt is running)
curl http://localhost:10350/apis
```

Use for: CI health checks, metrics scraping, IDE integration, notifications.

See `references/api-scripting.md` for full scripting examples.

## Resources

- **Official Docs**: https://docs.tilt.dev/
- **Tiltfile API**: https://docs.tilt.dev/api.html
- **Server API**: https://api.tilt.dev/
- **Extensions**: https://github.com/tilt-dev/tilt-extensions
- **Examples**: https://github.com/tilt-dev/tilt-example-html

### Reference Files
- `references/tiltfile-api.md` - Condensed Tiltfile API reference
- `references/extensions.md` - Popular extensions guide
- `references/api-scripting.md` - API server & scripting examples
