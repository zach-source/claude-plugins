# Tiltfile API Reference

Quick reference for commonly used Tiltfile functions. Full docs: https://docs.tilt.dev/api.html

## Build Functions

### docker_build()
Build a Docker image from source.

```python
docker_build(
  ref,                    # Image name (string, required)
  context,                # Build context path (string, required)
  dockerfile='Dockerfile', # Dockerfile path
  build_args={},          # Build arguments dict
  live_update=[],         # Live update rules
  ignore=[],              # Files to ignore
  only=[],                # Only include these files
  target='',              # Multi-stage build target
  network='',             # Docker build network
  ssh='',                 # SSH agent socket
  secret=[],              # Build secrets
  extra_tag=[],           # Additional tags
  entrypoint=[],          # Override entrypoint (for live_update)
  container_args=[],      # Override CMD
  cache_from=[],          # Cache sources
)
```

**Examples:**
```python
# Basic
docker_build('my-app', '.')

# With live updates
docker_build('my-app', '.',
  live_update=[
    sync('.', '/app'),
    run('pip install -r requirements.txt', trigger='requirements.txt'),
  ],
  ignore=['tests/', '*.md', '.git/'])

# Multi-stage build
docker_build('my-app', '.', target='development')

# Build args
docker_build('my-app', '.', build_args={'NODE_ENV': 'development'})
```

### custom_build()
Build images with custom commands (for non-Docker builders).

```python
custom_build(
  ref,                    # Image name
  command,                # Build command
  deps,                   # Files that trigger rebuild
  tag='',                 # Tag to apply
  disable_push=False,     # Don't push to registry
  skips_local_docker=False, # Image not in local Docker
  live_update=[],
  ignore=[],
)
```

**Example (Buildpack):**
```python
custom_build('my-app',
  command='pack build $EXPECTED_REF --builder paketobuildpacks/builder:base',
  deps=['src/', 'package.json'])
```

## Kubernetes Functions

### k8s_yaml()
Load Kubernetes manifests.

```python
k8s_yaml(
  yaml,                   # File path, list, or blob (required)
  allow_duplicates=False, # Allow duplicate resources
)
```

**Examples:**
```python
# Single file
k8s_yaml('k8s/deployment.yaml')

# Multiple files
k8s_yaml(['k8s/deployment.yaml', 'k8s/service.yaml'])

# Glob
k8s_yaml(glob('k8s/*.yaml'))

# Inline YAML
k8s_yaml(blob("""
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  key: value
"""))

# Kustomize
k8s_yaml(kustomize('k8s/overlays/dev'))

# Helm
k8s_yaml(helm('charts/my-app', values=['values-dev.yaml']))
```

### k8s_resource()
Configure a Kubernetes resource.

```python
k8s_resource(
  workload,               # Resource name (required)
  new_name='',            # Rename in UI
  port_forwards=[],       # Port forward rules
  extra_pod_selectors=[], # Additional pod selectors
  trigger_mode=TRIGGER_MODE_AUTO, # TRIGGER_MODE_MANUAL for manual only
  resource_deps=[],       # Resources that must be ready first
  objects=[],             # Associated non-workload objects
  labels=[],              # UI grouping labels
  links=[],               # Clickable links in UI
  auto_init=True,         # Auto-start on tilt up
)
```

**Examples:**
```python
# Port forward
k8s_resource('my-app', port_forwards='8080:8080')
k8s_resource('my-app', port_forwards=['8080:8080', '9090:9090'])

# Dependencies
k8s_resource('api', resource_deps=['postgres', 'redis'])

# Manual trigger
k8s_resource('migration', trigger_mode=TRIGGER_MODE_MANUAL)

# Labels for UI grouping
k8s_resource('api', labels=['backend'])
k8s_resource('worker', labels=['backend'])

# Links in UI
k8s_resource('api', links=[
  link('http://localhost:8080', 'API'),
  link('http://localhost:8080/docs', 'Swagger'),
])
```

### k8s_kind()
Register custom Kubernetes resource kinds.

```python
k8s_kind(
  kind,                   # Resource kind (required)
  api_version='',         # API version
  image_json_path=[],     # JSONPath to image field
)
```

## Local Functions

### local_resource()
Run local commands as Tilt resources.

```python
local_resource(
  name,                   # Resource name (required)
  cmd='',                 # Command to run (one-shot)
  serve_cmd='',           # Long-running server command
  deps=[],                # Files that trigger re-run
  resource_deps=[],       # Resources that must be ready first
  trigger_mode=TRIGGER_MODE_AUTO,
  auto_init=True,
  labels=[],
  links=[],
  allow_parallel=False,   # Allow parallel execution
  readiness_probe=None,   # Custom readiness check
)
```

**Examples:**
```python
# One-shot command
local_resource('install', cmd='npm install', deps=['package.json'])

# Long-running server
local_resource('frontend', serve_cmd='npm run dev', deps=['src/'])

# With dependencies
local_resource('build',
  cmd='npm run build',
  deps=['src/'],
  resource_deps=['install'])

# Database migration
local_resource('migrate',
  cmd='python manage.py migrate',
  resource_deps=['postgres'],
  trigger_mode=TRIGGER_MODE_MANUAL)
```

### local()
Run a local command during Tiltfile evaluation (not as resource).

```python
result = local(
  command,                # Command string or list
  quiet=False,            # Suppress output
  echo_off=False,         # Don't echo command
)
```

**Example:**
```python
version = local('git describe --tags', quiet=True)
```

## Live Update Rules

Used in `docker_build(..., live_update=[...])`.

### sync()
Copy files from host to container.

```python
sync(local_path, container_path)
```

### run()
Run command in container.

```python
run(
  cmd,                    # Command to run
  trigger=[],             # Only run when these files change
)
```

### restart_container()
Restart the container process.

```python
restart_container()       # Requires restart_process extension
```

### fall_back_on()
Fall back to full rebuild for certain files.

```python
fall_back_on(paths)       # List of file patterns
```

**Example:**
```python
docker_build('app', '.',
  live_update=[
    fall_back_on(['requirements.txt', 'Dockerfile']),
    sync('.', '/app'),
    run('pip install -r requirements.txt', trigger='requirements.txt'),
  ])
```

## Helper Functions

### glob()
Match files with glob patterns.
```python
glob('k8s/*.yaml')
glob('src/**/*.py')
```

### kustomize()
Run kustomize and return manifests.
```python
kustomize(path, flags=[], kustomize_bin='')
```

### helm()
Render Helm chart to manifests.
```python
helm(
  chart,                  # Chart path or name
  name='',                # Release name
  namespace='',           # Namespace
  values=[],              # Values files
  set=[],                 # --set flags
  flags=[],               # Additional flags
)
```

### read_file()
Read file contents.
```python
content = read_file('config.yaml')
```

### read_json() / read_yaml()
Read and parse file.
```python
config = read_json('config.json')
config = read_yaml('config.yaml')
```

### blob()
Create inline YAML/text blob.
```python
k8s_yaml(blob(yaml_string))
```

### encode_json() / encode_yaml()
Encode dict to string.
```python
yaml_str = encode_yaml({'key': 'value'})
```

## Configuration

### config.define_*()
Define config variables.

```python
config.define_bool('debug')
config.define_string('env')
config.define_string_list('services')

cfg = config.parse()

if cfg.get('debug'):
    # ...

env = cfg.get('env', 'development')
services = cfg.get('services', ['all'])
```

### config.set_enabled_resources()
Enable specific resources.

```python
config.define_string_list('to-run', args=True)
cfg = config.parse()
if cfg.get('to-run'):
    config.set_enabled_resources(cfg.get('to-run'))
```

**Usage:**
```bash
tilt up api worker    # Only run api and worker
tilt args -- api      # Same thing
```

## Built-in Variables

```python
os.environ              # Environment variables dict
os.getcwd()             # Current working directory
os.name                 # 'posix' or 'nt'
```

## Trigger Modes

```python
TRIGGER_MODE_AUTO       # Rebuild on file changes (default)
TRIGGER_MODE_MANUAL     # Only rebuild when manually triggered
```

## Starlark Syntax Notes

Starlark is Python-like but with differences:
- No `class` keyword
- No `import` (use `load()` instead)
- No recursion
- No `while` loops (only `for`)
- No `try`/`except`
- Strings are immutable
- Dicts preserve insertion order

**Loading extensions:**
```python
load('ext://helm_resource', 'helm_resource', 'helm_repo')
load('ext://restart_process', 'docker_build_with_restart')
```

**Functions:**
```python
def my_helper(name, port=8080):
    k8s_resource(name, port_forwards=str(port))
    return name
```

**Conditionals:**
```python
if os.environ.get('CI'):
    # CI-specific config
else:
    # Local dev config
```

**Loops:**
```python
services = ['api', 'worker', 'scheduler']
for svc in services:
    docker_build(svc, './' + svc)
    k8s_yaml('k8s/' + svc + '.yaml')
```
