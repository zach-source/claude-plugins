---
name: ci-polling
description: CI/CD pipeline monitoring and polling. Use PROACTIVELY when user pushes code, creates PR/MR, mentions "wait for CI", "check the build", "monitor pipeline", "watch workflow", or asks about build status. Launches background polling tasks that report back on completion.
context: fork
---

# CI/CD Pipeline Polling

This skill coordinates background monitoring of CI/CD pipelines. When triggered, launch polling tasks that run independently and report back when builds complete.

## When to Use

**Trigger Keywords:**
| Keyword | Action |
|---------|--------|
| `wait for CI` / `wait for build` | Start polling immediately |
| `check the build` / `check pipeline` | Poll once, then offer to monitor |
| `monitor the workflow` | Start continuous polling |
| `watch the pipeline` | Start continuous polling |
| `is the build done?` | Check status, offer to poll if running |
| `push and wait` | After git push, start polling |

**Automatic Triggers (PROACTIVE):**
1. After `git push` to a branch with open PR/MR
2. After creating PR with `/task:run github-pr`
3. After creating MR with `/task:run gitlab-mr`
4. When user mentions they're waiting for CI

## Available Tasks

### GitHub Actions
```bash
/task:run github-poll-workflow [run-id]
```
- Polls GitHub Actions workflow runs
- Reports job-by-job status on completion
- Shows failed job logs automatically

### GitLab CI/CD
```bash
/task:run gitlab-poll-pipeline [pipeline-id]
```
- Polls GitLab CI/CD pipelines
- Reports stage-by-stage job status
- Shows failed job traces automatically

## Usage Patterns

### Pattern 1: After Push
When user pushes code:
```
User: "push this to the feature branch"
[After git push completes]
Claude: "Pushed to feature-branch. I'll monitor the CI workflow."
[Launch polling task in background]
```

### Pattern 2: Explicit Request
```
User: "wait for the build to finish"
Claude: "I'll monitor the pipeline and report back when it completes."
[Launch polling task]
```

### Pattern 3: Status Check
```
User: "is the build passing?"
[Check current status]
Claude: "Pipeline #12345 is running (3/5 jobs complete). Want me to monitor until it finishes?"
User: "yes"
[Launch polling task]
```

### Pattern 4: After PR Creation
```
User: "/task:run github-pr"
[After PR is created]
Claude: "PR #42 created. Monitoring CI checks..."
[Launch polling task automatically]
```

## Response Templates

### Starting Polling
```markdown
**Monitoring CI/CD**

I'm watching [GitHub workflow / GitLab pipeline] #[ID] for branch `[branch]`.

- **Polling interval**: 30 seconds
- **Timeout**: 60 minutes
- **Current status**: [pending/running]

I'll report back when it completes.
```

### Success Report
```markdown
**CI/CD Complete: SUCCESS**

[GitHub workflow / GitLab pipeline] #[ID] passed.

**Branch**: `[branch]`
**Duration**: [X minutes]
**Jobs**: [N/N passed]

The build is green. Ready to merge.
```

### Failure Report
```markdown
**CI/CD Complete: FAILED**

[GitHub workflow / GitLab pipeline] #[ID] failed.

**Branch**: `[branch]`
**Failed Jobs**:
- [job-name]: [brief error]

**Last 50 lines of failed job:**
```
[error log excerpt]
```

Would you like me to:
1. Investigate the failure
2. Show full job logs
3. Retry the pipeline
```

## Platform Detection

Detect platform automatically:
```bash
# Check remote URL
REMOTE=$(git remote get-url origin 2>/dev/null)

if echo "$REMOTE" | grep -q "github"; then
  # Use GitHub polling
  /task:run github-poll-workflow
elif echo "$REMOTE" | grep -q "gitlab"; then
  # Use GitLab polling
  /task:run gitlab-poll-pipeline
else
  echo "Unknown CI platform. Please specify:"
  echo "- /task:run github-poll-workflow [id]"
  echo "- /task:run gitlab-poll-pipeline [id]"
fi
```

## Configuration

### Environment Variables
| Variable | Purpose | Default |
|----------|---------|---------|
| `INTERVAL` | Polling interval (seconds) | 30 |
| `TIMEOUT` | Max wait time (minutes) | 60 |
| `GITLAB_API` | GitLab API URL | https://gitlab.com/api/v4 |
| `GITLAB_TOKEN` | GitLab API token | (from 1Password) |

### Adjusting Polling
```bash
# Fast polling (for quick builds)
INTERVAL=10 /task:run github-poll-workflow

# Long timeout (for slow builds)
TIMEOUT=120 /task:run gitlab-poll-pipeline
```

## Integration with Other Skills

- **git**: After push operations, offer to monitor CI
- **gitflow**: After finishing features/releases, monitor CI
- **tasks**: After PR/MR creation, monitor CI
- **promptcontext**: Set CI context for repeated monitoring

## Best Practices

1. **Don't poll too fast**: 30s interval avoids rate limits
2. **Set reasonable timeouts**: Most builds finish in <30 min
3. **Report failures clearly**: Show actionable error info
4. **Offer next steps**: After failure, suggest investigation
5. **Run in background**: Use `context: fork` for non-blocking monitoring
