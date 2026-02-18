---
name: deploy
description: |
  Infrastructure deployment verification workflow. Use when: (1) Pushing infrastructure/config changes,
  (2) Deploying to Kubernetes, (3) User says "deploy", "rollout", "verify deployment",
  (4) After committing Helm/K8s/Hydra/Kratos YAML changes, (5) Need to check deployment status.
---

# Deploy Verification Workflow

## Pre-Deploy Checklist

1. **Validate configs** before committing:
   - YAML syntax: `python3 -c "import yaml; yaml.safe_load(open('FILE'))"`
   - K8s manifests: `kubectl apply --dry-run=client -f <file>`
   - Helm: `helm template <chart> | kubectl apply --dry-run=client -f -`
   - Cross-check service-specific keys (don't mix Hydra/Kratos/other service configs)

2. **Build verification** (if applicable):
   - `go build ./...` or `make build`
   - `go vet ./...`
   - Run tests: `make test` or `go test ./...`

## Deploy Steps

1. Stage and commit changes with conventional commit format
2. Push to current branch
3. Verify deployment:

```bash
# Check rollout status with timeout
kubectl rollout status deployment/<name> -n <namespace> --timeout=120s

# If flaky connectivity, retry with backoff
for i in 1 2 3; do
  kubectl rollout status deployment/<name> -n <namespace> --timeout=60s && break
  echo "Retry $i/3... waiting 15s"
  sleep 15
done
```

## Post-Deploy Verification

```bash
# Check pods are healthy
kubectl get pods -n <namespace> -l app=<name>

# Check recent logs for errors
kubectl logs -n <namespace> deployment/<name> --tail=50 --since=2m

# Smoke test (if endpoint available)
curl -sf https://<endpoint>/health
```

## Connectivity Failure Protocol

If kubectl is unreachable after 3 retries:
1. Document in commit/PR: "UNVERIFIED: kubectl connectivity failed at $(date)"
2. Create a verification script the user can run later:
   ```bash
   kubectl rollout status deployment/<name> -n <namespace>
   kubectl get pods -n <namespace> -l app=<name>
   ```
3. Inform the user clearly that manual verification is needed

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Wrong config keys | Copied from wrong service | Validate top-level keys match target service |
| ImagePullBackOff | Wrong image tag/registry | Check image exists: `docker manifest inspect <image>` |
| CrashLoopBackOff | Config or code error | Check logs: `kubectl logs <pod> --previous` |
| Pending pods | Resource constraints | Check events: `kubectl describe pod <pod>` |
