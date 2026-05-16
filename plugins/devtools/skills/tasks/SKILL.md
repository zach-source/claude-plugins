---
name: tasks
description: Claude Code task framework for reusable workflows. Use when user asks about "/task:run", "/task:list", "/task:new", "create a task", "global tasks", "local tasks", or needs to run structured multi-step workflows. Triggers on task-related questions or when creating reusable automation.
context: fork
---

# Task Framework

The task framework provides reusable, structured workflows that can be invoked with `/task:run <name>`.

## Core Concepts

### Task Types

| Type | Location | Scope |
|------|----------|-------|
| **Local** | `.claude/tasks/<name>.md` | Project-specific |
| **Global** | `~/.claude/tasks/<name>.md` | Available everywhere |

**Precedence**: Local tasks override global tasks with the same name.

### Complex Tasks (Directories)

For multi-file tasks:
```
.claude/tasks/<name>/
├── prompt.md       # Main task instructions
├── template.md     # Template files
└── config.json     # Task configuration
```

## Task Commands

### `/task:run <name> [args]`

Execute a task by name with optional arguments.

```bash
# Run a global task
/task:run github-pr

# Run with arguments
/task:run gitflow-release-start 1.2.0

# Local task (if exists) takes precedence
/task:run custom-deploy
```

### `/task:list`

List all available tasks (both local and global).

### `/task:new <name>`

Create a new local task from template.

### `/task:install <source>`

Install a task from URL or path.

## Task File Format

```markdown
---
description: Short description of what this task does
allowed-tools: ["Bash", "Read", "Write", "Glob", "Grep"]
requires:
  - Prerequisite 1
  - Prerequisite 2
---

# Task Title

[Task description and context]

## Arguments

- `$1` - First argument description
- `$2` - Second argument (optional)
- `--flag` - Flag description

## Steps

### 1. Step Name

[Step description]

```bash
# Commands to execute
VARIABLE="$1"
echo "Processing $VARIABLE"
```

### 2. Next Step

[Continue with workflow...]

## Notes

[Important considerations, gotchas, tips]

## Examples

```bash
/task:run task-name arg1 arg2
/task:run task-name --flag
```
```

## Advanced Frontmatter Options

### Agent Execution (`agent`)

Execute the task using a specialized sub-agent:

```yaml
---
description: Deep security audit
allowed-tools: ["Read", "Grep", "Glob"]
agent: security-auditor
---
```

**When to use**: Tasks requiring specialized domain expertise (code review, debugging, architecture analysis).

**Available agents**: `code-reviewer`, `debugger`, `typescript-pro`, `architect-reviewer`, `security-auditor`, `golang-pro`, `python-pro`, etc.

### Forked Context (`context: fork`)

Run the task in an isolated sub-agent context:

```yaml
---
description: Comprehensive codebase analysis
allowed-tools: ["Read", "Grep", "Glob", "Task"]
context: fork
---
```

**When to use**: Long-running, multi-step tasks that benefit from isolation. The forked agent has full conversation history but operates independently.

### Combined Example

```yaml
---
description: Architecture review with isolation
allowed-tools: ["Read", "Grep", "Glob", "Task"]
agent: architect-reviewer
context: fork
---
```

Runs in a forked context using the architect-reviewer agent - ideal for complex, autonomous analysis tasks.

## Built-in Global Tasks

### Git Workflows

| Task | Purpose |
|------|---------|
| `github-pr` | Create GitHub PR with structured description |
| `gitlab-mr` | Create GitLab MR with structured description |
| `git-worktree` | Create isolated git worktree |

### GitFlow Tasks

| Task | Purpose |
|------|---------|
| `gitflow-init` | Initialize GitFlow branch structure |
| `gitflow-feature-start` | Start feature branch from develop |
| `gitflow-feature-finish` | Complete feature (merge to develop) |
| `gitflow-release-start` | Start release branch, bump version |
| `gitflow-release-finish` | Complete release (merge to main AND develop) |
| `gitflow-hotfix-start` | Start emergency fix from main |
| `gitflow-hotfix-finish` | Complete hotfix (merge to main AND develop) |
| `gitflow-status` | Show current GitFlow state |

### CI/CD Tasks

| Task | Purpose |
|------|---------|
| `github-release-workflow` | Add GitHub Actions release automation |
| `gitlab-release-pipeline` | Add GitLab CI release pipeline |

### Jujutsu Tasks

| Task | Purpose |
|------|---------|
| `jj-workspace` | Create new jj workspace |

## Creating Custom Tasks

### Local Task Example

Create `.claude/tasks/deploy-staging.md`:

```markdown
---
description: Deploy to staging environment
allowed-tools: ["Bash", "Read"]
requires:
  - kubectl configured
  - Staging namespace exists
---

# Deploy to Staging

Deploy the current build to the staging environment.

## Steps

### 1. Build Application

```bash
make build
```

### 2. Run Tests

```bash
make test
```

### 3. Deploy

```bash
kubectl apply -k deploy/staging/
```

### 4. Verify

```bash
kubectl rollout status deployment/app -n staging
```
```

Then invoke with: `/task:run deploy-staging`

### Task Best Practices

1. **Clear Description**: Frontmatter description appears in `/task:list`
2. **Minimal Tools**: Only request tools you actually need
3. **Prerequisites**: List what must exist before running
4. **Error Handling**: Include checks and graceful failures
5. **Idempotent**: Safe to run multiple times
6. **Arguments**: Document all parameters clearly

## Task Discovery

```bash
# List all tasks
/task:list

# View task contents
Read ~/.claude/tasks/<name>.md

# Find tasks by pattern
ls ~/.claude/tasks/ | grep deploy
```

## Task Arguments

Arguments are passed positionally:

```bash
/task:run my-task arg1 arg2 arg3
```

In the task, reference as `$1`, `$2`, `$3`, etc.

Flags like `--flag` are parsed by the task implementation.

## Task Variables

Tasks can access:
- `$1`, `$2`, etc. - Positional arguments
- Standard environment variables
- Git context (branch, remote, etc.)

## Relationship to Skills

| Feature | Tasks | Skills |
|---------|-------|--------|
| Invocation | `/task:run <name>` | Automatic/contextual |
| Purpose | Execute workflow | Provide knowledge |
| Output | Actions & changes | Guidance & patterns |
| Structure | Step-by-step | Reference material |

**Use Tasks for**: Repeatable workflows with concrete steps
**Use Skills for**: Knowledge domains and best practices

## Troubleshooting

### Task Not Found

```bash
# Check if task exists
ls ~/.claude/tasks/
ls .claude/tasks/

# Verify file extension
# Must be .md or directory with prompt.md
```

### Permissions Error

```bash
# Check allowed-tools in frontmatter
# Task can only use tools listed there
```

### Arguments Not Working

```bash
# Ensure arguments are passed after task name
/task:run task-name "arg with spaces" arg2
```
