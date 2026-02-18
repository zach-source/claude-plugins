---
name: osgrep
description: "Semantic code search tool using natural language queries instead of regex patterns. Use when exploring codebases, finding implementations by concept, or answering 'where do we handle X?' questions."
---

# osgrep - Semantic Code Search

> Semantic search tool for exploring local files using natural language queries instead of regex patterns

## What is osgrep?

**osgrep** replaces traditional `grep` and `find` commands with AI-powered natural language queries. It understands code concepts rather than just matching strings, making it ideal for code discovery and conceptual exploration.

## Key Features

- **Semantic searching**: Ask questions in plain language rather than using regex patterns
- **Live indexing**: Background server automatically keeps search index current
- **Structured output**: The `--json` flag returns organized results with file paths, line numbers, relevance scores, and content snippets
- **Local & Private**: Uses `transformers.js` for 100% local embeddings with no remote API calls
- **Auto-Isolated Indexes**: Each repository automatically gets its own separate index
- **Adaptive Performance**: Throttles indexing based on system resources to prevent overheating

## When to Use This Skill

Use osgrep when you need to:
- Find code based on concepts rather than exact string matches
- Explore unfamiliar codebases quickly
- Locate implementation patterns across a large codebase
- Answer "where do we handle X?" type questions
- Discover similar code patterns or architectural approaches

## Example Queries

Natural language queries that work well with osgrep:

```bash
# Authentication and security
osgrep --json "How are user authentication tokens validated?"
osgrep --json "Where do we verify permissions?"

# Error handling
osgrep --json "Where do we handle retries or backoff?"
osgrep --json "How are errors logged and reported?"

# Data flow
osgrep --json "Where is user data persisted?"
osgrep --json "How do we cache API responses?"

# Architecture patterns
osgrep --json "dependency injection setup"
osgrep --json "middleware configuration"
```

## Essential Commands

### Basic Search
```bash
# Default search (returns up to 25 results)
osgrep --json "your question"

# Search within specific path
osgrep --json "your question" path/to/directory
```

### Controlling Results
```bash
# Limit total results
osgrep --json -m 10 "your question"

# Get more matches per file (default is 1)
osgrep --json --per-file 3 "your question"

# Combine both limits
osgrep --json -m 20 --per-file 2 "your question"
```

### Server Management
```bash
# Start the background server (auto-indexes and watches for changes)
osgrep serve

# Manual indexing
osgrep index

# Check indexed repositories
osgrep list

# Verify installation
osgrep doctor
```

## Output Format

When using `--json`, osgrep returns structured data:

```json
{
  "results": [
    {
      "file": "src/auth/validator.ts",
      "line": 42,
      "score": 0.89,
      "content": "function validateToken(token: string) { ... }"
    }
  ]
}
```

## Recommended Workflow

1. **Start with a natural language query** using `--json`
   ```bash
   osgrep --json "Where do we handle database migrations?"
   ```

2. **Review the JSON output** to determine if it answers your question
   - Check relevance scores (higher is better)
   - Look at file paths to understand context
   - Read snippets to verify relevance

3. **Only open full files** if you need additional context
   - Use the file paths from results
   - Increase `--per-file` if you need more context from specific files

4. **Refine queries** if initial findings lack clarity
   - Make queries more specific
   - Adjust result limits (`-m` and `--per-file`)
   - Try different phrasings

## Installation & Setup

```bash
# Install globally
npm install -g osgrep

# Download embedding models (~150MB, one-time setup)
osgrep setup

# Install Claude Code integration
osgrep install-claude-code
```

## Configuration

### Ignoring Files

Create `.osgrepignore` in your repository root to exclude paths:

```
# Example .osgrepignore
node_modules/
dist/
*.test.ts
coverage/
```

osgrep also respects `.gitignore` automatically.

### Environment Variables

- `MXBAI_STORE`: Override store names for manual index isolation

## Technical Details

- **Chunking**: Uses tree-sitter for smart code chunking by function/class boundaries
- **Search Algorithm**: Reciprocal Rank Fusion combining vector search with keyword matching
- **Performance**: Adaptive throttling monitors RAM and CPU to maintain system stability
- **Index Isolation**: Repositories automatically isolated based on Git remote URL or directory name

## Tips for Better Results

1. **Be specific**: "JWT token validation logic" works better than "auth stuff"
2. **Use domain terms**: "GraphQL resolver" is better than "API handler"
3. **Start broad, then narrow**: Begin with high-level concepts, then drill down
4. **Increase per-file limit**: When you find the right file but need more context
5. **Use the server**: `osgrep serve` keeps indexes fresh and searches fast (<50ms)

## Limitations

- Requires initial indexing (automatic on first search)
- Embedding models download is ~150MB (one-time)
- Best results on well-structured code with clear function/class boundaries
- Natural language queries work better than code snippets

## License

Apache License 2.0

## Source

Based on osgrep by Ryan D'Onofrio
- GitHub: https://github.com/Ryandonofrio3/osgrep
- Built upon concepts from mgrep by MixedBread
