---
name: promptcontext
description: "Context recommendation system for reducing action uncertainty. Use PROACTIVELY when user mentions keywords like 'use this kubeconfig', 'our goal is', 'debug this', 'in production', 'deploy to', or when uncertainty about environment, cluster, namespace, or AWS profile drops below 80%."
---

# Prompt Context Recommendation

This skill provides guidance for when and how to recommend setting operational context to reduce uncertainty in actions.

## Uncertainty Threshold

**Critical Rule**: When confidence in any of these is below 80%, PROACTIVELY recommend setting context:

| Context Type | Signs of Uncertainty | Recommendation |
|-------------|---------------------|----------------|
| Kubernetes | Unknown cluster, namespace, or kubeconfig | `/prompt:context set "k8s <cluster> namespace <ns>"` |
| AWS | Unknown profile or region | `/prompt:context set "aws profile <name> region <region>"` |
| Git | Wrong branch assumptions, repo confusion | `/prompt:context set "git <branch>"` |
| Project | Unclear which project or service | `/prompt:context set "note: working on <project>"` |
| Environment | Unknown dev/staging/prod | `/prompt:context set "env ENV=<value>"` |

## When to Trigger

### Keyword-Based Triggers (PROACTIVE)

When user message contains these keywords/patterns, **immediately** recommend setting context:

| Keyword Pattern | Recommended Action | Example Command |
|----------------|-------------------|-----------------|
| `use this kubeconfig` / `kubeconfig file:` / `~/.kube/` | Set k8s config | `/prompt:context set "k8s <cluster> --kubeconfig <path>"` |
| `our goal is` / `we're working on` / `the objective` | Set project note | `/prompt:context set "note: <captured goal>"` |
| `debug this` / `troubleshoot` / `investigate` | Set debug context | `/prompt:context set "note: debugging <component>"` |
| `in production` / `prod environment` | Set prod context | `/prompt:context set "env production; note: PROD - be careful"` |
| `staging` / `in staging` | Set staging context | `/prompt:context set "env staging"` |
| `deploy to` / `deploying` | Set deployment target | `/prompt:context set "note: deploying to <target>"` |
| `AWS account` / `aws profile` | Set AWS profile | `/prompt:context set "aws profile <name>"` |
| `this cluster` / `cluster named` | Set k8s cluster | `/prompt:context set "k8s <cluster-name>"` |
| `namespace` / `in ns` | Set k8s namespace | `/prompt:context set "k8s <cluster> namespace <ns>"` |
| `this repo` / `this project` / `codebase` | Set project note | `/prompt:context set "note: working on <project-name>"` |

**Keyword Trigger Examples:**

1. **User says**: "use this kubeconfig file: ~/.kube/nexus-dev"

   **Immediately recommend**:
   ```
   /prompt:context set "k8s nexus-dev --kubeconfig ~/.kube/nexus-dev"
   ```

2. **User says**: "our goal is to fix the authentication bug in the API gateway"

   **Immediately recommend**:
   ```
   /prompt:context set "note: fixing auth bug in API gateway"
   ```

3. **User says**: "debug this failing deployment"

   **Immediately recommend**:
   ```
   /prompt:context set "note: debugging failing deployment"
   ```
   Then ask: Which cluster and namespace?

4. **User says**: "we're working on the payment-service microservice"

   **Immediately recommend**:
   ```
   /prompt:context set "note: working on payment-service"
   ```

### Automatic Triggers (Uncertainty < 80%)

1. **Kubernetes operations** without known context:
   - "Apply this manifest" - Which cluster? Which namespace?
   - "Check pod status" - Which cluster?
   - "Scale deployment" - Where?

2. **AWS operations** without profile/region:
   - "Deploy to S3" - Which account? Which region?
   - "Create Lambda" - What profile?
   - "Update IAM" - Production or development?

3. **Multi-environment codebases**:
   - Operations that could affect dev, staging, or production
   - Database migrations, deployments, configuration changes

4. **Ambiguous commands**:
   - User says "deploy" without specifying where
   - "Run tests" in a multi-service repo
   - "Check logs" without service/namespace context

## Response Patterns

### Pattern 1: Keyword Detection (Immediate)

When keywords are detected, respond **immediately** with context suggestion:

```markdown
I noticed you mentioned [keyword]. Let me capture that context:

```
/prompt:context set "[captured context]"
```

[Continue with the task using this context]
```

**Examples:**

- **Keyword detected**: "use this kubeconfig file: ~/.kube/nexus-dev"
  > I'll set up the kubeconfig context:
  > ```
  > /prompt:context set "k8s nexus-dev --kubeconfig ~/.kube/nexus-dev"
  > ```
  > Now proceeding with your request using this cluster...

- **Keyword detected**: "our goal is to migrate the database"
  > Capturing your goal:
  > ```
  > /prompt:context set "note: goal - migrate the database"
  > ```
  > I'll keep this objective in mind. Which database and target environment?

### Pattern 2: Uncertainty Detection (Threshold)

When uncertainty is detected, respond with:

```markdown
**Context Recommendation**

I noticed uncertainty about the operational context. To ensure accurate actions, consider setting:

```
/prompt:context set "<suggested context>"
```

**Current uncertainty:**
- [List specific unknowns: cluster, namespace, profile, etc.]

**Why this matters:**
- [Brief explanation of potential risks without context]

Would you like to set the context, or should I proceed with assumptions?
```

## Quick Context Commands

```bash
# View current context
/prompt:context

# Set Kubernetes context
/prompt:context set "k8s prod-cluster namespace api"

# Set AWS context
/prompt:context set "aws profile production region us-west-2"

# Set project note
/prompt:context set "note: working on payment-service"

# Combined context
/prompt:context set "k8s dev-cluster; aws staging; note: testing feature X"

# Clear context
/prompt:context clear all
```

## Uncertainty Calculation

Estimate confidence based on:

| Factor | High Confidence (>80%) | Low Confidence (<80%) |
|--------|----------------------|----------------------|
| Cluster | Explicitly stated or single cluster | Multiple possible, none specified |
| Namespace | Stated or `default` known safe | Could be any of several |
| AWS Profile | Stated or obvious from task | Multiple accounts possible |
| Region | Stated or single-region setup | Multi-region, none specified |
| Environment | Clear dev/staging/prod | Could be any |

## Examples

### Example 1: Kubernetes Uncertainty

**User**: "Scale the api deployment to 5 replicas"

**Uncertainty**: Cluster and namespace unknown
**Confidence**: ~40%

**Response**:
> **Context Recommendation**
>
> I'm uncertain about the target cluster and namespace for scaling the `api` deployment.
>
> ```
> /prompt:context set "k8s <cluster-name> namespace <namespace>"
> ```
>
> Without context, I might scale the wrong deployment in the wrong environment. Would you like to set the context first?

### Example 2: AWS Uncertainty

**User**: "Upload this file to S3"

**Uncertainty**: AWS profile and bucket unknown
**Confidence**: ~50%

**Response**:
> **Context Recommendation**
>
> I need to know which AWS account and bucket to use.
>
> ```
> /prompt:context set "aws profile <profile-name> region <region>"
> ```
>
> Which S3 bucket should I upload to?

### Example 3: High Confidence (No Recommendation Needed)

**User**: "Scale the api deployment to 5 replicas in the prod-cluster api namespace"

**Confidence**: 95% - All context explicitly provided
**Action**: Proceed directly without context recommendation

## Integration with Other Skills

- **kubernetes-expert**: Use promptcontext before k8s operations
- **cloud-architect**: Set AWS context before infrastructure changes
- **deployment-engineer**: Set full context before deployments

## Best Practices

1. **Ask early**: Recommend context at start of ambiguous tasks
2. **Don't over-ask**: If context is clear, don't prompt
3. **Remember context**: Once set, context persists - don't re-ask
4. **Offer defaults**: Suggest common contexts as options
5. **Explain risks**: Help users understand why context matters
