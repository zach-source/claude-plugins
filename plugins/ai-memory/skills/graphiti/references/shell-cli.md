# Graphiti Shell CLI

Use these bundled Python scripts to interact with Graphiti without the MCP tool surface (hooks, CI, shell pipelines). They handle MCP-over-HTTP session management (JSON-RPC 2.0, session init, SSE parsing) automatically. Run with `uv run --script` — `httpx` is resolved on first use.

## Scripts

```
graphiti/scripts/
├── graphiti-cli.py     # Full CLI with all subcommands
├── graphiti-add.py     # Focused: store a memory (for hooks/automation)
└── graphiti-search.py  # Focused: search nodes and facts
```

## graphiti-cli.py — Full CLI

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

## graphiti-add.py — Store Memories

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

## graphiti-search.py — Query Knowledge

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

## Use in Build Scripts / CI

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

## Protocol Details

Scripts communicate via MCP-over-HTTP (JSON-RPC 2.0) at `http://127.0.0.1:51847/mcp/`. Each script handles:
- Session initialization (`initialize` handshake)
- `Mcp-Session-Id` header management
- SSE (Server-Sent Events) response parsing
- Connection error handling with service check hints

## HTTP Tool Names

HTTP tool names differ from the MCP tool names used inside Claude:

| HTTP name | MCP equivalent | Arguments | Purpose |
|-----------|---------------|-----------|---------|
| `add_episode` | `add_memory` | `name`, `episode_body`, `source` (`text`\|`json`\|`message`), `source_description` | Store data |
| `search_nodes` | `search_nodes` | `query`, `group_ids` (optional) | Search entities |
| `search_facts` | `search_memory_facts` | `query`, `group_ids` (optional) | Search relationships |
| `get_episodes` | `get_episodes` | `group_id`, `limit` (optional) | Get recent episodes |
| `get_entity_edge` | `get_entity_edge` | `edge_id` | Get specific relationship |
| `delete_entity_edge` | `delete_entity_edge` | `edge_id` | Remove relationship |
| `delete_episode` | `delete_episode` | `episode_id` | Remove episode |
| `clear_graph` | `clear_graph` | (none) | Delete all data (dangerous!) |
| `get_status` | `get_status` | (none) | Server health |
