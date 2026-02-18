---
name: graphiti
description: "Temporal knowledge graph memory system. Use PROACTIVELY at session start to load context, when solving non-trivial problems to check for known solutions, and at session end to persist learnings. Auto-store failure→success learnings when debugging takes 3+ attempts. Auto-store infrastructure context when discovering services/clusters/topology. Triggers on: 'remember this', 'what do you know about', 'save for later', project context questions, approach pivots, or when debugging takes >15 min."
---

# Graphiti - Temporal Knowledge Graph Memory

Graphiti provides persistent AI memory through a temporal knowledge graph backed by FalkorDB. Use it to store and retrieve project context, solutions to problems, user preferences, and architectural decisions.

## Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHEN TO USE GRAPHITI                         │
├─────────────────────────────────────────────────────────────────┤
│  Starting work?          → search_nodes for project context    │
│  Looking for patterns?   → search_memory_facts for relations   │
│  Solved hard problem?    → add_memory with the solution        │
│  Need recent context?    → get_episodes for session history    │
│  Session ending?         → add_memory with key learnings       │
│  User shares preference? → add_memory to remember it           │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Tools Reference

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `add_memory` | Store episodes/insights in graph | Capturing solutions, decisions, preferences |
| `search_nodes` | Search entity summaries | Finding project context, exploring knowledge |
| `search_memory_facts` | Find relationships between entities | Discovering patterns, connections |
| `get_episodes` | Retrieve recent episodes | Getting conversation/session history |
| `delete_episode` | Remove episode and related data | Cleanup incorrect entries |
| `delete_entity_edge` | Remove a relationship | Correct wrong connections |
| `get_entity_edge` | Get specific relationship | Inspect a known edge |
| `get_status` | Check server health | Debugging connectivity |
| `clear_graph` | Delete all data for group | Reset memory (dangerous!) |

## Workflows

### Session Start (ALWAYS DO THIS)

Before starting work on a project, load relevant context:

```
1. search_nodes({ query: "[project-name] context" })
2. search_memory_facts({ query: "[project-name] patterns decisions" })
3. get_episodes({ max_episodes: 5 })  # Recent session history
4. Begin work with context loaded
```

### Problem Solving

When debugging or solving a problem:

```
1. search_memory_facts({ query: "[error-message or problem]" })
2. If found → Apply the known solution
3. If not → Debug normally
4. If solved after >15 min effort → add_memory with solution
```

### Store Insights

When you've learned something worth remembering:

```python
add_memory({
  name: "Solution: [brief title]",
  episode_body: """
  Problem: [what was wrong]
  Context: [project, file, component]
  Solution: [what fixed it]
  Why: [root cause explanation]
  """,
  source: "text",
  source_description: "debugging session"
})
```

### Session End

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

### Store Structured Data

For structured information like configs or mappings:

```python
add_memory({
  name: "Config: [service name]",
  episode_body: '{"service": "api", "endpoints": [...], "auth": "oauth2"}',
  source: "json",
  source_description: "service configuration"
})
```

## Proactive Memory Patterns

### Failure → Success Learnings

**When to trigger:** After solving a problem that took multiple attempts, hit unexpected errors, or required a non-obvious fix. Store BOTH the failure and the solution so future sessions skip the pain.

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

**Examples of when to store:**
- node2nix build failed → switched to npm global install via activation script
- Hook was catching false positives → refined regex pattern
- Package missing runtime dependency → added dependency to nix packages
- Config file had wrong keys for service → documented correct schema

### Infrastructure Context

**When to trigger:** When discovering or working with service deployments, cluster configurations, database connections, or any infrastructure topology that future sessions need to know.

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

### Tool/Build Configuration

**When to trigger:** When discovering how a tool is configured, what flags it needs, or non-obvious build steps that aren't documented elsewhere.

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

### Cross-Session Context

**When to trigger:** When the user shares context that will be needed in future sessions - project relationships, team conventions, deployment schedules, or ongoing initiatives.

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

## Auto-Store Triggers

Store a memory automatically (without being asked) when ANY of these occur:

| Trigger | Memory Type | Example |
|---------|-------------|---------|
| Solved after 3+ attempts | Failure→Success | Debugging a build error |
| Discovered wrong config keys | Failure→Success | YAML had keys for wrong service |
| User says "remember this" | Cross-Session Context | Any explicit request |
| New service/cluster discovered | Infrastructure Context | kubectl reveals new topology |
| Tool required non-obvious setup | Tool Configuration | Package needed extra runtime deps |
| Approach pivot (plan A → plan B) | Failure→Success | node2nix → npm activation script |
| User shares team/project context | Cross-Session Context | "We deploy on Tuesdays" |
| Found undocumented behavior | Failure→Success | API behaves differently than docs |

## When to Add Memory

**DO Add:**
- Solutions to non-trivial problems (>15 min debugging)
- Failed approaches and what worked instead
- Infrastructure topology and service relationships
- User-explained project context or preferences
- Architectural or design decisions with rationale
- Discovered undocumented behavior or gotchas
- Session summaries with key learnings
- Recurring patterns or anti-patterns found
- Tool configurations with gotchas

**DON'T Add:**
- Generic knowledge (already in training data)
- Trivial fixes (typos, simple syntax errors)
- Sensitive data (credentials, API keys, PII, connection passwords)
- Temporary debugging info
- Content that changes frequently
- Exact secret values (store the 1Password path instead)

## Entity Types

Graphiti automatically extracts these entity types from your episodes:

| Entity Type | Description | Examples |
|------------|-------------|----------|
| **Preference** | User choices, opinions | "prefers tabs over spaces" |
| **Requirement** | Features, constraints | "needs OAuth2 support" |
| **Procedure** | Step-by-step processes | "deployment workflow" |
| **Organization** | Companies, teams | "Ripple", "Platform team" |
| **Document** | Files, references | "CLAUDE.md", "API docs" |
| **Topic** | Knowledge domains | "Kubernetes", "Nix flakes" |

## Group IDs

Use `group_id` to organize memories by project or domain:

```python
# Project-specific memory
add_memory({
  name: "...",
  episode_body: "...",
  group_id: "nix-dotfiles"
})

# Search within a project
search_nodes({
  query: "...",
  group_ids: ["nix-dotfiles"]
})
```

## Search Tips

### Effective Queries

```python
# Find architecture context
search_nodes({ query: "nix-dotfiles architecture structure" })

# Find solutions to errors
search_memory_facts({ query: "error ENOENT file not found" })

# Find user preferences
search_nodes({ query: "user preference coding style" })

# Find decisions
search_memory_facts({ query: "decision why chose" })
```

### Pagination

```python
# Get more results
search_nodes({ query: "...", max_nodes: 20 })
search_memory_facts({ query: "...", max_facts: 20 })
```

## Server Setup

**Backend**: Neo4j (graph database via launchd)
**MCP Server**: Graphiti MCP on `http://127.0.0.1:51847`

Both services run as macOS LaunchAgents (auto-start on login):

| Service | LaunchAgent Label | Logs |
|---------|------------------|------|
| Neo4j | `com.claude.neo4j` | `~/.graphiti/neo4j/logs/neo4j.log` |
| Graphiti MCP | `com.claude.graphiti` | `~/.graphiti/logs/graphiti.log` |

**Check services:**
```bash
# Via launchctl
launchctl list | grep claude

# Via MCP tool
get_status()
```

**Restart services:**
```bash
launchctl kickstart -k gui/$(id -u)/com.claude.neo4j
launchctl kickstart -k gui/$(id -u)/com.claude.graphiti
```

## Using Graphiti via Shell (without MCP)

Bundled Python scripts in `scripts/` provide direct HTTP access to Graphiti. They handle MCP-over-HTTP session management (JSON-RPC 2.0, session initialization, SSE parsing) automatically. Run with `uv run --script` - dependencies (`httpx`) are resolved on first use.

### Bundled Scripts

```
graphiti/
├── SKILL.md
└── scripts/
    ├── graphiti-cli.py      # Full CLI with all subcommands
    ├── graphiti-add.py      # Focused: store a memory (for hooks/automation)
    └── graphiti-search.py   # Focused: search nodes and facts
```

### graphiti-cli.py (Full CLI)

All-in-one tool with subcommands for every Graphiti operation.

```bash
SCRIPTS=~/.claude/skills/graphiti/scripts

# Check server health
uv run --script $SCRIPTS/graphiti-cli.py status

# Store a memory
uv run --script $SCRIPTS/graphiti-cli.py add \
  "Fix: node2nix sandbox failure" \
  "FAILED: ENOTCACHED for large npm packages. SOLUTION: npm global install via activation script." \
  --desc "failure-to-success learning"

# Search entity nodes
uv run --script $SCRIPTS/graphiti-cli.py search "kubernetes deployment issues"

# Search facts/relationships
uv run --script $SCRIPTS/graphiti-cli.py facts "nix build errors"

# Get recent episodes
uv run --script $SCRIPTS/graphiti-cli.py episodes --limit 10

# Delete an episode
uv run --script $SCRIPTS/graphiti-cli.py delete-episode <uuid>

# List all available server tools
uv run --script $SCRIPTS/graphiti-cli.py tools
```

### graphiti-add.py (Store Memories)

Lightweight script for hooks, CI, and automation. Supports stdin for piping.

```bash
SCRIPTS=~/.claude/skills/graphiti/scripts

# Positional args
uv run --script $SCRIPTS/graphiti-add.py "Fix: YAML parse error" "Wrong keys for service. Fixed by checking schema docs."

# With metadata
uv run --script $SCRIPTS/graphiti-add.py \
  --source json --desc "infra context" \
  "Infra: api-server on prod" \
  '{"cluster": "prod-cluster", "namespace": "api", "replicas": 3}'

# Pipe body from stdin
echo "Deployed api v2.1 to prod-cluster/default at $(date)" | \
  uv run --script $SCRIPTS/graphiti-add.py --stdin "Deploy: api v2.1"

# Quiet mode (no output on success)
uv run --script $SCRIPTS/graphiti-add.py -q "Session note" "Working on feature X"
```

### graphiti-search.py (Query Knowledge)

Search nodes, facts, or both in one call.

```bash
SCRIPTS=~/.claude/skills/graphiti/scripts

# Search entity nodes (default)
uv run --script $SCRIPTS/graphiti-search.py "nix-dotfiles architecture"

# Search facts/relationships only
uv run --script $SCRIPTS/graphiti-search.py --facts "deployment errors"

# Search both nodes AND facts
uv run --script $SCRIPTS/graphiti-search.py --both "api authentication"

# Filter by group
uv run --script $SCRIPTS/graphiti-search.py --group nix-dotfiles "common issues"

# Raw JSON output (for piping to jq)
uv run --script $SCRIPTS/graphiti-search.py --raw "build errors" | jq '.[] | .summary'
```

### Use in Build Scripts / CI

```bash
#!/usr/bin/env bash
# Example: post-deploy hook that records deployment context
SCRIPTS=~/.claude/skills/graphiti/scripts

SERVICE="$1" CLUSTER="$2" NS="$3" TAG="$4"

uv run --script $SCRIPTS/graphiti-add.py \
  --desc "deployment record" \
  "Deploy: $SERVICE to $CLUSTER/$NS" \
  "Service: $SERVICE | Cluster: $CLUSTER | Namespace: $NS | Image: $TAG | Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

### Protocol Details

The scripts communicate via MCP-over-HTTP (JSON-RPC 2.0) at `http://127.0.0.1:51847/mcp/`. Each script automatically handles:
- Session initialization (`initialize` handshake)
- `Mcp-Session-Id` header management
- SSE (Server-Sent Events) response parsing
- Connection error handling with service check hints

### Available HTTP Tools

| Tool Name | Arguments | Purpose |
|-----------|-----------|---------|
| `add_episode` | `name`, `episode_body`, `source` (`text`\|`json`\|`message`), `source_description` | Store data |
| `search_nodes` | `query`, `group_ids` (optional) | Search entities |
| `search_facts` | `query`, `group_ids` (optional) | Search relationships |
| `get_episodes` | `group_id`, `limit` (optional) | Get recent episodes |
| `get_entity_edge` | `edge_id` | Get specific relationship |
| `delete_entity_edge` | `edge_id` | Remove relationship |
| `delete_episode` | `episode_id` | Remove episode |
| `clear_graph` | (none) | Delete all data (dangerous!) |
| `get_status` | (none) | Server health |

**Note:** The HTTP tool names differ slightly from the MCP tool names used in Claude:
- MCP `add_memory` → HTTP `add_episode`
- MCP `search_memory_facts` → HTTP `search_facts`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check launchd: `launchctl list \| grep claude` |
| Neo4j not starting | Check logs: `tail ~/.graphiti/neo4j/logs/neo4j.error.log` |
| Graphiti not starting | Check logs: `tail ~/.graphiti/logs/graphiti.error.log` |
| Session expired (404) | Re-initialize: call `initialize` again |
| No results found | Broaden search terms, check group_id |
| Slow queries | Reduce max_nodes/max_facts |
| Duplicate entries | Use delete_episode to clean up |
| OpenAI key failure | Check 1Password: `op read "op://Private/..."` |

## Examples

### Store a Bug Fix Solution

```python
add_memory({
  name: "Fix: Fork bomb pattern matching Go wildcards",
  episode_body: """
  Problem: dangerous-command-blocker.sh was catching 'go build ./...' as a fork bomb

  Root Cause: Pattern '\\.\\/' matched './' in Go's recursive wildcard

  Solution: Changed pattern to only match standalone './.' at end of command or
  followed by space, not when followed by more dots (like './...')

  Files: home/ztaylor/features/tools/claude-hooks/bash-hooks/dangerous-command-blocker.sh
  """,
  source: "text",
  source_description: "bug fix"
})
```

### Store User Preference

```python
add_memory({
  name: "Preference: Commit message style",
  episode_body: """
  User prefers conventional commit format:
  - type(scope): description
  - Types: feat, fix, docs, style, refactor, test, chore
  - Scope: component or area affected
  - Keep under 72 chars for first line
  """,
  source: "text",
  source_description: "user preference"
})
```

### Search Before Debugging

```python
# Before spending time debugging, check if solution exists
search_memory_facts({
  query: "nix build error attribute missing"
})

# Check for patterns in this project
search_nodes({
  query: "nix-dotfiles common issues",
  group_ids: ["nix-dotfiles"]
})
```
