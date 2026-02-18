# Tilt Extensions Reference

Extensions add functionality to Tilt. Load them with `load('ext://name', ...)`.

Full catalog: https://github.com/tilt-dev/tilt-extensions

## Helm Extensions

### helm_resource
Deploy Helm charts as managed resources.

```python
load('ext://helm_resource', 'helm_resource', 'helm_repo')

# Add repository
helm_repo('bitnami', 'https://charts.bitnami.com/bitnami')

# Deploy chart
helm_resource('postgres', 'bitnami/postgresql',
  flags=[
    '--set=auth.postgresPassword=devpass',
    '--set=primary.persistence.enabled=false',
  ],
  port_forwards='5432:5432',
  labels=['data'])

# From local chart
helm_resource('my-app', 'charts/my-app',
  flags=['--values=values-dev.yaml'],
  image_deps=['my-app-image'],
  image_keys=['image.repository', 'image.tag'])
```

**Parameters:**
- `name`: Release name
- `chart`: Chart reference (repo/chart or local path)
- `flags`: Helm flags (--set, --values, etc.)
- `namespace`: Target namespace
- `port_forwards`: Port forward rules
- `resource_deps`: Dependencies
- `labels`: UI labels
- `image_deps`: Docker builds to depend on
- `image_keys`: Where to inject image refs

### helm_remote
Fetch remote Helm charts.

```python
load('ext://helm_remote', 'helm_remote')

helm_remote('ingress-nginx',
  repo_url='https://kubernetes.github.io/ingress-nginx',
  version='4.0.0')
```

## Container Management

### restart_process
Restart container process without full rebuild.

```python
load('ext://restart_process', 'docker_build_with_restart')

# For compiled languages (Go, Rust, etc.)
docker_build_with_restart('my-go-app', '.',
  entrypoint=['/app/server'],
  live_update=[
    sync('./build', '/app'),
  ])
```

**Use when:**
- Compiled binaries need restart after sync
- Process doesn't pick up file changes automatically

### container_restart
Alternative restart approach.

```python
load('ext://container_restart', 'container_restart')

docker_build('my-app', '.',
  live_update=[
    sync('.', '/app'),
    container_restart('my-app'),
  ])
```

## Namespace Management

### namespace
Create and manage namespaces.

```python
load('ext://namespace', 'namespace_create', 'namespace_inject')

# Create namespace if not exists
namespace_create('my-dev-ns')

# Inject namespace into all resources
namespace_inject('my-dev-ns')
```

### namespace (with labels)
```python
load('ext://namespace', 'namespace_create')

namespace_create('my-ns', labels={'team': 'backend'})
```

## ConfigMap and Secret

### configmap
Create ConfigMaps from files or literals.

```python
load('ext://configmap', 'configmap_create', 'configmap_from_dict')

# From files
configmap_create('app-config', from_file=glob('config/*.yaml'))

# From directory
configmap_create('app-config', from_dir='config/')

# From dict
configmap_from_dict('app-config', {'key': 'value'})

# Watch for changes
configmap_create('app-config',
  from_file='config/app.yaml',
  watch=True)  # Triggers dependent resources on change
```

### secret
Create Secrets.

```python
load('ext://secret', 'secret_create_generic', 'secret_from_dict')

# From literals
secret_create_generic('db-creds',
  from_literal={'username': 'admin', 'password': 'secret'})

# From files
secret_create_generic('tls-certs',
  from_file=['tls.crt', 'tls.key'])

# From env file
secret_create_generic('env-secret', from_env_file='.env.secret')

# From dict
secret_from_dict('my-secret', {'api_key': 'abc123'})
```

## Git Integration

### git_resource
Deploy from Git repositories.

```python
load('ext://git_resource', 'git_resource')

# Deploy from remote repo
git_resource('external-config',
  url='https://github.com/org/config-repo.git',
  paths=['k8s/'])

# With branch/tag
git_resource('config', 'git@github.com:org/repo.git',
  ref='main',
  paths=['manifests/'])
```

## Database & Storage

### uibutton
Add interactive buttons to Tilt UI.

```python
load('ext://uibutton', 'cmd_button', 'location')

# Button to run migrations
cmd_button('migrate',
  argv=['python', 'manage.py', 'migrate'],
  resource='api',
  icon_name='database',
  text='Run Migrations')

# Button with confirmation
cmd_button('seed-db',
  argv=['./scripts/seed.sh'],
  resource='postgres',
  text='Seed Database',
  requires_confirmation=True)
```

### podman
Build with Podman instead of Docker.

```python
load('ext://podman', 'podman_build')

podman_build('my-app', '.')
```

## Testing Extensions

### tests
Group test resources.

```python
load('ext://tests/golang', 'go_test')

go_test('unit-tests', './...', recursive=True)
```

### jest
Run Jest tests.

```python
load('ext://jest', 'jest')

jest('frontend-tests', 'frontend/', watch=True)
```

## Utility Extensions

### color
Add colored output to local commands.

```python
load('ext://color', 'color')

local_resource('status',
  cmd=color('green', 'echo "All systems go!"'))
```

### print_tiltfile_dir
Debug helper.

```python
load('ext://print_tiltfile_dir', 'print_tiltfile_dir')
print_tiltfile_dir()  # Prints Tiltfile directory
```

### min_tilt_version
Enforce minimum Tilt version.

```python
load('ext://min_tilt_version', 'min_tilt_version')
min_tilt_version('0.30.0')
```

### dotenv
Load environment from .env files.

```python
load('ext://dotenv', 'dotenv')

dotenv('.env')
dotenv('.env.local')  # Override with local values
```

## Loading Extensions

### From Official Repo (Recommended)
```python
load('ext://helm_resource', 'helm_resource')
```
Tilt auto-downloads from https://github.com/tilt-dev/tilt-extensions

### From Local Path
```python
load('./extensions/my_ext/Tiltfile', 'my_function')
```

### From Git URL
```python
load('ext://git_resource', 'git_resource')
# Then load from cloned repo
```

## Creating Custom Extensions

Create `Tiltfile` in your extension directory:

```python
# extensions/my_helpers/Tiltfile

def deploy_service(name, port):
    """Helper to deploy a standard service."""
    docker_build(name, './' + name)
    k8s_yaml('k8s/' + name + '.yaml')
    k8s_resource(name,
      port_forwards=str(port) + ':' + str(port),
      labels=['backend'])
```

**Use in main Tiltfile:**
```python
load('./extensions/my_helpers/Tiltfile', 'deploy_service')

deploy_service('api', 8080)
deploy_service('worker', 8081)
```

## Common Extension Patterns

### Database with Seeding
```python
load('ext://helm_resource', 'helm_resource', 'helm_repo')
load('ext://uibutton', 'cmd_button')

helm_repo('bitnami', 'https://charts.bitnami.com/bitnami')
helm_resource('postgres', 'bitnami/postgresql',
  flags=['--set=auth.postgresPassword=dev'],
  port_forwards='5432:5432')

cmd_button('seed',
  argv=['./scripts/seed-db.sh'],
  resource='postgres',
  text='Seed Data',
  icon_name='database')
```

### Multi-Environment Setup
```python
load('ext://dotenv', 'dotenv')
load('ext://namespace', 'namespace_create', 'namespace_inject')

# Load environment
dotenv()
env = os.environ.get('TILT_ENV', 'dev')

# Create namespace
namespace_create('myapp-' + env)
namespace_inject('myapp-' + env)

# Environment-specific values
if env == 'staging':
    helm_flags = ['--values=values-staging.yaml']
else:
    helm_flags = ['--values=values-dev.yaml']
```

### Service Mesh Integration
```python
load('ext://helm_resource', 'helm_resource', 'helm_repo')

# Install Istio (example)
helm_repo('istio', 'https://istio-release.storage.googleapis.com/charts')
helm_resource('istio-base', 'istio/base', namespace='istio-system')
helm_resource('istiod', 'istio/istiod',
  namespace='istio-system',
  resource_deps=['istio-base'])
```
