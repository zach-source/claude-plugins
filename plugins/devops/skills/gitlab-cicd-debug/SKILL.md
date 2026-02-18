---
name: gitlab-cicd-debug
description: |
  Debug GitLab CI/CD pipeline failures including vault auth, docker builds, K8s deployments, and job errors.
  Use when: (1) Pipeline jobs fail, (2) Vault JWT auth issues, (3) Docker build/push errors, (4) K8s deployment failures,
  (5) "permission denied" or "unauthorized" errors, (6) rkeychain/devenv issues, (7) User asks to check pipeline status,
  (8) ECR push failures, (9) Runner or executor problems.
---

# GitLab CI/CD Pipeline Debugging

## Quick Diagnosis

1. **Get pipeline status**: Check GitLab UI or use API
2. **Get failed job logs**: Fetch job trace via API
3. **Identify error category** from patterns below

## Error Categories & Solutions

### Vault JWT Auth Failures

**Symptoms**: "permission denied", "invalid role", "no matching bound claims"

```bash
# Check vault role exists and bindings
vault read auth/jwt-gitlab-com/role/<ROLE_NAME>

# Verify bound_claims matches project path
# - namespace_path: "ripple/ai" matches ripple/ai/*
# - project_path: "ripple/ai/code-reviewer" matches exact project

# Check token_policies have required access
vault policy read <POLICY_NAME>
```

**Fixes**:
- Role doesn't exist: Create with `vault write auth/jwt-gitlab-com/role/<name> ...`
- Wrong namespace: Update `bound_claims` to match project path
- Missing policy: Add required paths

### AWS/ECR Auth Failures

**Symptoms**: "not authorized to perform: ecr:*", "no credentials"

```bash
# Check AWS role in vault
vault list aws/roles | grep <role-name>
vault read aws/roles/<role-name>
```

**Required policy paths**:
```hcl
path "aws/roles" { capabilities = ["list"] }
path "aws/sts/<role-name>" { capabilities = ["read"] }
path "aws/roles/<role-name>" { capabilities = ["read"] }
```

### Docker Build Failures

- **Platform mismatch**: Use `--platform linux/amd64` for EKS
- **Build context**: Dockerfile paths relative to context
- **Layer cache**: Try `--no-cache`

### K8s Deployment Failures

```bash
kubectl get pods -n <namespace> -l app=<app>
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

- **ImagePullBackOff**: Check ECR auth, image tag
- **CrashLoopBackOff**: Check logs, entrypoint
- **exec format error**: Wrong arch (arm64 vs amd64)

## Devenv + rkeychain Pattern

```yaml
.login: &login_before_script
  - |
    devenv shell -i bash <<'EOF'
    rkeychain config init
    rkeychain config set-vault-context nexus
    rkeychain login vault-token -t $(vault write -field=token auth/jwt-gitlab-com/login role=$GITLAB_ROLE jwt=$VAULT_ID_TOKEN)
    rkeychain aws update-aws-config
    rkeychain aws update-kubeconfig --region us-west-2 --profile <profile> --cluster <cluster>
    EOF
```

**Required variables**:
```yaml
variables:
  VAULT_ADDR: "https://vault.usw2.nexus.ripplenet.dev:8200"
  GITLAB_ROLE: <your-role-name>

.job_template:
  id_tokens:
    VAULT_ID_TOKEN:
      aud: https://vault.usw2.nexus.ripplenet.dev:8200
```

## GitLab API Commands

```bash
# Get recent pipelines
curl -s -H "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipelines?per_page=5"

# Get jobs for pipeline
curl -s -H "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/pipelines/$PIPELINE_ID/jobs"

# Get job trace/log
curl -s -H "PRIVATE-TOKEN: $TOKEN" \
  "https://gitlab.com/api/v4/projects/$PROJECT_ID/jobs/$JOB_ID/trace"
```

## Creating Vault Roles (Least Privilege)

```bash
# Create minimal policy
vault policy write <name> - <<'EOF'
path "aws/roles" { capabilities = ["list"] }
path "aws/sts/<aws-role>" { capabilities = ["read"] }
path "aws/roles/<aws-role>" { capabilities = ["read"] }
EOF

# Create JWT role bound to specific project
vault write auth/jwt-gitlab-com/role/<role-name> - <<'EOF'
{
  "role_type": "jwt",
  "user_claim": "user_email",
  "bound_audiences": ["https://vault.usw2.nexus.ripplenet.dev", "https://vault.usw2.nexus.ripplenet.dev:8200"],
  "bound_claims_type": "glob",
  "bound_claims": { "project_path": "<namespace>/<project>" },
  "token_policies": ["<policy-name>", "default"]
}
EOF
```
