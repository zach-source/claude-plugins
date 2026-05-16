# Memory Storage Patterns

Detailed templates for the four proactive memory patterns. Load this reference when storing a non-trivial memory and you want the right structure.

## Failure → Success

When to use: after solving a problem that took multiple attempts, hit unexpected errors, or required a non-obvious fix. Store both the failure and the solution so future sessions skip the pain.

```python
add_memory({
  name: "Fix: [component] - [brief description]",
  episode_body: """
  FAILED APPROACH:
  - Tried: [what was attempted first]
  - Error: [exact error message or behavior]
  - Why it failed: [root cause of failure]

  WORKING SOLUTION:
  - Fix: [what actually worked]
  - Key insight: [the non-obvious thing that made it work]
  - Files changed: [list of files]

  PREVENTION:
  - Next time: [how to avoid this entirely]
  - Warning signs: [what to look for]
  """,
  source: "text",
  source_description: "failure-to-success learning",
  group_id: "[project-name]"
})
```

Examples of when to store:
- node2nix build failed → switched to npm global install via activation script
- Hook was catching false positives → refined regex pattern
- Package missing runtime dependency → added dependency to nix packages
- Config file had wrong keys for service → documented correct schema

## Infrastructure Context

When to use: when discovering or working with service deployments, cluster configurations, database connections, or any infrastructure topology that future sessions need to know.

```python
add_memory({
  name: "Infra: [service] on [cluster/environment]",
  episode_body: """
  SERVICE: [service name]
  ENVIRONMENT: [cluster/namespace/region]
  ENDPOINT: [URL or connection string - NO secrets]

  TOPOLOGY:
  - Runs on: [cluster name, namespace]
  - Depends on: [upstream services]
  - Consumed by: [downstream services]

  KNOWN ISSUES:
  - [issue 1 and workaround]
  - [issue 2 and workaround]

  CONFIG LOCATION:
  - Helm chart: [path]
  - K8s manifests: [path]
  - Environment vars: [where they're set]

  LAST VERIFIED: [date]
  """,
  source: "text",
  source_description: "infrastructure context",
  group_id: "[project-name]"
})
```

## Tool/Build Configuration

When to use: when discovering how a tool is configured, what flags it needs, or non-obvious build steps that aren't documented elsewhere.

```python
add_memory({
  name: "Tool: [tool name] configuration",
  episode_body: """
  TOOL: [name and version]
  PURPOSE: [what it does in this project]

  SETUP:
  - Install: [how to install]
  - Config file: [location]
  - Required env vars: [list - NO values for secrets]

  GOTCHAS:
  - [non-obvious thing 1]
  - [non-obvious thing 2]

  COMMON COMMANDS:
  - [command 1]: [what it does]
  - [command 2]: [what it does]
  """,
  source: "text",
  source_description: "tool configuration",
  group_id: "[project-name]"
})
```

## Cross-Session Context

When to use: when the user shares context that will be needed in future sessions — project relationships, team conventions, deployment schedules, or ongoing initiatives.

```python
add_memory({
  name: "Context: [brief description]",
  episode_body: """
  CONTEXT: [what needs to be remembered]
  RELEVANCE: [when this matters]
  SOURCE: [who/what provided this - user, docs, discovery]
  EXPIRES: [when this might become stale, or "indefinite"]
  """,
  source: "text",
  source_description: "cross-session context",
  group_id: "[project-name]"
})
```

## Structured (JSON) Episodes

For configs, mappings, or anything that should preserve structure for later retrieval:

```python
add_memory({
  name: "Config: [service name]",
  episode_body: '{"service": "api", "endpoints": [...], "auth": "oauth2"}',
  source: "json",
  source_description: "service configuration"
})
```

## Session Summary

Before ending a work session:

```python
add_memory({
  name: "Session Summary: [date] [project]",
  episode_body: """
  Accomplished:
  - [task 1]
  - [task 2]

  Key Decisions:
  - [decision and rationale]

  Open Questions:
  - [what remains unclear]

  Next Steps:
  - [what to do next session]
  """,
  source: "text",
  source_description: "session summary"
})
```
