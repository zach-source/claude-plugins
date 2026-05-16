---
name: graphiti
description: "Temporal knowledge graph memory system. Use PROACTIVELY at session start to load context, when solving non-trivial problems to check for known solutions, and at session end to persist learnings. Auto-store failure→success learnings when debugging takes 3+ attempts. Auto-store infrastructure context when discovering services/clusters/topology. Triggers on: 'remember this', 'what do you know about', 'save for later', project context questions, approach pivots, or when debugging takes >15 min."
---

# Graphiti — Temporal Knowledge Graph Memory

Graphiti provides persistent AI memory through a temporal knowledge graph backed by Neo4j. Store and retrieve project context, solutions, user preferences, and architectural decisions across sessions.

## Decision Tree

```
Starting work?          → search_nodes for project context
Looking for patterns?   → search_memory_facts for relations
Solved hard problem?    → add_memory with the solution
Need recent context?    → get_episodes for session history
Session ending?         → add_memory with key learnings
User shares preference? → add_memory to remember it
```

## MCP Tools

| Tool | Purpose | When to use |
|------|---------|-------------|
| `add_memory` | Store episodes/insights | Capturing solutions, decisions, preferences |
| `search_nodes` | Search entity summaries | Finding project context, exploring knowledge |
| `search_memory_facts` | Find relationships between entities | Discovering patterns, connections |
| `get_episodes` | Retrieve recent episodes | Getting conversation/session history |
| `delete_episode` | Remove episode and related data | Cleanup incorrect entries |
| `delete_entity_edge` | Remove a relationship | Correct wrong connections |
| `get_entity_edge` | Get specific relationship | Inspect a known edge |
| `get_status` | Check server health | Debugging connectivity |
| `clear_graph` | Delete all data for group | Reset memory (dangerous!) |

## Core Workflows

### Session Start (ALWAYS)

```python
search_nodes({ query: "[project-name] context" })
search_memory_facts({ query: "[project-name] patterns decisions" })
get_episodes({ max_episodes: 5 })
```

### Problem Solving

```
1. search_memory_facts({ query: "[error message or problem]" })
2. If found → Apply known solution
3. If not → Debug normally
4. If solved after >15 min effort → add_memory with solution (see references/store-patterns.md)
```

### Storing Memories

For the four detailed templates (Failure→Success, Infrastructure Context, Tool Config, Cross-Session Context) including the session-summary template, see **[references/store-patterns.md](references/store-patterns.md)**.

Minimal pattern:

```python
add_memory({
  name: "Solution: [brief title]",
  episode_body: "Problem: ... Context: ... Solution: ... Why: ...",
  source: "text",
  source_description: "debugging session",
  group_id: "[project-name]"
})
```

## Auto-Store Triggers

Store automatically (without being asked) when ANY of these occur:

| Trigger | Pattern (in store-patterns.md) | Example |
|---------|-------------------------------|---------|
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
- Tool configurations with gotchas

**DON'T Add:**
- Generic knowledge (already in training data)
- Trivial fixes (typos, simple syntax errors)
- Sensitive data (credentials, API keys, PII, connection passwords)
- Temporary debugging info
- Content that changes frequently
- Exact secret values (store the 1Password path instead)

## Group IDs

Use `group_id` to scope memories per project or domain:

```python
add_memory({ name: "...", episode_body: "...", group_id: "nix-dotfiles" })
search_nodes({ query: "...", group_ids: ["nix-dotfiles"] })
```

## Entity Types

Graphiti auto-extracts: **Preference** (user choices), **Requirement** (features/constraints), **Procedure** (step-by-step processes), **Organization** (companies/teams), **Document** (files/references), **Topic** (knowledge domains).

## Search Tips

```python
# Find architecture context
search_nodes({ query: "nix-dotfiles architecture structure" })

# Find solutions to errors
search_memory_facts({ query: "error ENOENT file not found" })

# Find user preferences
search_nodes({ query: "user preference coding style" })

# Pagination
search_nodes({ query: "...", max_nodes: 20 })
```

## Server Setup

**Backend**: Neo4j (graph DB via launchd)
**MCP Server**: Graphiti MCP on `http://127.0.0.1:51847`

Both services run as macOS LaunchAgents (auto-start on login):

| Service | LaunchAgent label | Logs |
|---------|-------------------|------|
| Neo4j | `com.claude.neo4j` | `~/.graphiti/neo4j/logs/neo4j.log` |
| Graphiti MCP | `com.claude.graphiti` | `~/.graphiti/logs/graphiti.log` |

Check / restart:

```bash
launchctl list | grep claude
launchctl kickstart -k gui/$(id -u)/com.claude.neo4j
launchctl kickstart -k gui/$(id -u)/com.claude.graphiti
```

## Shell CLI (Without MCP)

For hooks, CI, and shell automation, use the bundled scripts in `scripts/`. See **[references/shell-cli.md](references/shell-cli.md)** for the full CLI reference, examples, and HTTP tool-name mapping.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | `launchctl list \| grep claude` |
| Neo4j not starting | `tail ~/.graphiti/neo4j/logs/neo4j.error.log` |
| Graphiti not starting | `tail ~/.graphiti/logs/graphiti.error.log` |
| Session expired (404) | Re-initialize: call `initialize` again |
| No results found | Broaden search terms, check `group_id` |
| Slow queries | Reduce `max_nodes`/`max_facts` |
| Duplicate entries | Use `delete_episode` to clean up |
| OpenAI key failure | Check 1Password: `op read "op://Private/..."` |
