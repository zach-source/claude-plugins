---
name: replay-buffer
description: "Experience replay for tool/test/build failures. Invoke IMMEDIATELY when any tool fails (non-zero exit, FAIL/error/panic in output). Looks up known fixes before debugging, records failures and fixes, promotes successful fixes. Triggers on: test failures, build errors, lint failures, compilation errors, any recurring error patterns."
---

# Replay Buffer

Local experience replay: lookup known fixes before debugging, record new fixes, promote on success.

## Mandatory Workflow

On ANY tool failure (non-zero exit or error output), execute in order:

### Step A: Lookup First

Before exploring fixes, call the `mcp__replay-memory__lookup_fix` tool:
```json
{
  "tool": "<tool name>",
  "args": ["<args>"],
  "stderr": "<stderr output>",
  "stdout": "<stdout if small>",
  "cwd": "<repo path>"
}
```

If `confidence >= 0.7`:
- Say: "Replay buffer hit: applying prior fix: <summary>"
- Apply the fix immediately (patch or described actions)
- Skip brainstorming

If no match: proceed with normal debugging.

### Step B: Record Failure

On failure, call the `mcp__replay-memory__record_failure` tool:
```json
{
  "tool": "<tool>",
  "args": ["<args>"],
  "exit_code": "<code>",
  "stderr": "<stderr>",
  "stdout": "<stdout>",
  "goal": "<what I was trying to do>"
}
```

Save returned `failure_id` for correlation.

### Step C: Record Fix

After applying code edits, call the `mcp__replay-memory__record_fix` tool:
```json
{
  "failure_id": "<failure_id>",
  "summary": "<1-sentence specific fix, e.g. 'Mock time.Now() in TestTokenRefresh setup'>",
  "patch": "<diff or file list>"
}
```

### Step D: Promote on Success

When the same tool/test now passes, call the `mcp__replay-memory__record_success` tool:
```json
{
  "failure_id": "<failure_id>"
}
```

If fix didn't work: do NOT promote. Try another fix.

## Data Management Tools

Optional tools for managing replay buffer data:

### List Failures

Browse recorded failures with filters:
```json
{
  "limit": 50,
  "offset": 0,
  "tool_filter": "go test",
  "has_fix": true
}
```

### Get Statistics

View overall success rate and top failing tools:
```json
{}
```

### Export Backup

Export all failures and fixes to JSON for backup:
```json
{}
```

### Clear Old Failures

Remove failures older than N days:
```json
{
  "days": 30
}
```

## Error Patterns to Watch

Invoke this skill when stderr/stdout contains:
- `FAIL` / `FAILED` / `error` / `panic` / `exception`
- `error:` / `fatal:` / `compilation terminated`
- Test framework failures
- Lint rule violations
- Build tool errors

## Features

- **Exact matching**: Normalizes line numbers, timestamps, file paths, UUIDs
- **Optional fuzzy search**: Requires `sentence-transformers` package for vector similarity
- **Secret redaction**: Automatically redacts API keys, tokens, passwords before storage
- **Confidence scoring**: Fixes promoted after 2 confirmed successes

## Guardrails

- **Redact secrets** before recording: API keys, tokens, passwords, credentials
- **Prefer minimal patches**: If diff is huge, store summary + key snippet only
- **Don't force replay** if codebase changed materially: treat as hint, not command
- **Check stats periodically**: Use `get_statistics` to see success rate and top issues
