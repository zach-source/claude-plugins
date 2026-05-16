---
name: git
description: Git version control essentials and best practices. Use when working with git repositories, commits, branches, merges, rebases, remotes, or resolving conflicts. Triggers on git commands, branch operations, merge/rebase questions, or version control workflows.
context: fork
---

# Git Version Control

Essential Git knowledge for effective version control.

## Daily Workflow

### Status & Changes

```bash
git status              # Current state
git status -sb          # Short format with branch
git diff                # Unstaged changes
git diff --staged       # Staged changes
git diff HEAD~3         # Last 3 commits
```

### Staging & Committing

```bash
# Stage changes
git add file.txt        # Specific file
git add .               # All changes
git add -p              # Interactive (patch mode)

# Commit
git commit -m "message" # With message
git commit              # Opens editor
git commit -am "msg"    # Add tracked + commit

# Amend last commit (before push)
git commit --amend      # Edit last commit
git commit --amend --no-edit  # Keep message
```

### Viewing History

```bash
git log                 # Full log
git log --oneline       # Compact
git log --oneline -10   # Last 10
git log --graph         # With branch graph
git log -p file.txt     # File history with diffs
git log --author="name" # By author
git log --since="1 week" # Time-based

# Show specific commit
git show abc123
git show HEAD~2
```

## Branching

### Create & Switch

```bash
# Create branch
git branch feature      # Create
git checkout -b feature # Create + switch
git switch -c feature   # Modern create + switch

# Switch branches
git checkout main       # Classic
git switch main         # Modern

# List branches
git branch              # Local
git branch -r           # Remote
git branch -a           # All
git branch -v           # With last commit
```

### Delete Branches

```bash
git branch -d feature   # Safe delete (merged only)
git branch -D feature   # Force delete
git push origin --delete feature  # Remote
```

## Merging

### Basic Merge

```bash
git checkout main
git merge feature       # Fast-forward if possible
git merge --no-ff feature  # Always create merge commit
```

### Merge Conflicts

```bash
# After conflict
git status              # See conflicted files
# Edit files, resolve markers (<<<<, ====, >>>>)
git add resolved-file.txt
git commit              # Complete merge

# Abort merge
git merge --abort
```

### Merge Strategies

```bash
git merge -X theirs feature  # Prefer theirs on conflict
git merge -X ours feature    # Prefer ours on conflict
```

## Rebasing

### Basic Rebase

```bash
git checkout feature
git rebase main         # Reapply feature on top of main

# Interactive rebase (edit history)
git rebase -i HEAD~3    # Last 3 commits
git rebase -i main      # All since main
```

### Interactive Rebase Commands

| Command | Purpose |
|---------|---------|
| `pick` | Keep commit |
| `reword` | Keep, change message |
| `edit` | Stop to amend |
| `squash` | Combine with previous |
| `fixup` | Combine, discard message |
| `drop` | Remove commit |

### Rebase Conflicts

```bash
# Resolve conflict, then:
git add resolved-file.txt
git rebase --continue

# Abort rebase
git rebase --abort

# Skip problematic commit
git rebase --skip
```

## Remote Operations

### Remotes

```bash
git remote -v           # List remotes
git remote add origin URL
git remote remove origin
git remote set-url origin NEW_URL
```

### Fetch & Pull

```bash
git fetch               # Download without merge
git fetch --all         # All remotes
git fetch --prune       # Remove deleted remote branches

git pull                # Fetch + merge
git pull --rebase       # Fetch + rebase (cleaner history)
git pull origin main    # Specific branch
```

### Push

```bash
git push                # Current branch
git push origin main    # Specific branch
git push -u origin feature  # Set upstream
git push --force-with-lease # Safe force push
git push --tags         # Push tags
```

## Undoing Changes

### Working Directory

```bash
git checkout -- file.txt    # Discard changes (old)
git restore file.txt        # Discard changes (modern)
git restore .               # Discard all

git clean -fd              # Remove untracked files/dirs
git clean -n               # Dry run
```

### Staging Area

```bash
git reset file.txt         # Unstage (keep changes)
git restore --staged file.txt  # Modern unstage
git reset                  # Unstage all
```

### Commits

```bash
# Undo last commit (keep changes staged)
git reset --soft HEAD~1

# Undo last commit (keep changes unstaged)
git reset HEAD~1
git reset --mixed HEAD~1   # Same as above

# Undo last commit (discard changes) ⚠️
git reset --hard HEAD~1

# Revert (creates new commit undoing changes)
git revert abc123          # Safe for shared history
```

## Stashing

```bash
git stash                  # Stash changes
git stash -m "message"     # With message
git stash -u               # Include untracked

git stash list             # List stashes
git stash show             # Show latest stash diff
git stash show -p stash@{0}  # Show specific stash

git stash pop              # Apply + remove
git stash apply            # Apply, keep in list
git stash drop             # Remove from list
git stash clear            # Remove all
```

## Tags

```bash
# Create tags
git tag v1.0.0             # Lightweight
git tag -a v1.0.0 -m "Release 1.0.0"  # Annotated (recommended)
git tag -a v1.0.0 abc123   # Tag specific commit

# List & show
git tag                    # List all
git tag -l "v1.*"          # Filter
git show v1.0.0            # Show tag details

# Push tags
git push origin v1.0.0     # Single tag
git push origin --tags     # All tags

# Delete tags
git tag -d v1.0.0          # Local
git push origin --delete v1.0.0  # Remote
```

## Cherry-Pick

```bash
git cherry-pick abc123     # Apply specific commit
git cherry-pick abc123..def456  # Range
git cherry-pick -n abc123  # Don't commit (stage only)

# Conflict resolution
git cherry-pick --continue
git cherry-pick --abort
```

## Bisect (Finding Bugs)

```bash
git bisect start
git bisect bad             # Current is broken
git bisect good v1.0.0     # This version worked

# Git checks out commits, you test:
git bisect good            # Works
git bisect bad             # Broken
# Repeat until found

git bisect reset           # Done, return to original
```

## Worktrees

```bash
# Create worktree
git worktree add ../feature-worktree feature-branch
git worktree add -b new-branch ../new-worktree

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../feature-worktree
```

## Configuration

```bash
# User identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Editor
git config --global core.editor "vim"

# Default branch
git config --global init.defaultBranch main

# Aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st status
git config --global alias.lg "log --oneline --graph"

# View config
git config --list
git config --global --list
```

## Best Practices

### Commit Messages

```
type(scope): subject

[optional body]

[optional footer]
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Examples**:
```
feat(auth): add OAuth2 login
fix(api): handle null response from payment service
docs(readme): update installation instructions
refactor(utils): extract date formatting to helper
```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<name>` | `feature/user-auth` |
| Bug fix | `fix/<name>` | `fix/login-redirect` |
| Hotfix | `hotfix/<version>` | `hotfix/1.2.1` |
| Release | `release/<version>` | `release/2.0.0` |

### Golden Rules

1. **Never rebase shared branches** (main, develop)
2. **Pull before push** to avoid conflicts
3. **Commit often**, push when ready
4. **Write meaningful commit messages**
5. **Use branches** for features
6. **Keep commits atomic** (one logical change)
7. **Review before committing** (`git diff --staged`)

## Troubleshooting

### Recover Deleted Branch

```bash
git reflog                 # Find commit hash
git checkout -b recovered abc123
```

### Undo Pushed Commit

```bash
# Safe way (new commit that undoes)
git revert abc123
git push

# Force way (rewrites history) ⚠️
git reset --hard HEAD~1
git push --force-with-lease
```

### Fix Wrong Branch Commit

```bash
# Move commit to correct branch
git checkout correct-branch
git cherry-pick abc123
git checkout wrong-branch
git reset --hard HEAD~1
```

### Large File Committed

```bash
# Remove from history
git filter-branch --tree-filter 'rm -f large-file.zip' HEAD
# Or use BFG Repo-Cleaner (faster)
```

## Useful Aliases

```bash
# Add to ~/.gitconfig
[alias]
    st = status -sb
    co = checkout
    br = branch
    ci = commit
    lg = log --oneline --graph --decorate
    last = log -1 HEAD
    unstage = reset HEAD --
    amend = commit --amend --no-edit
    undo = reset --soft HEAD~1
    wip = commit -am "WIP"
```

## GitHub/GitLab CLI Integration

```bash
# GitHub
gh pr create              # Create PR
gh pr list                # List PRs
gh pr checkout 123        # Checkout PR

# GitLab
glab mr create            # Create MR
glab mr list              # List MRs
glab mr checkout 123      # Checkout MR
```

## Related Skills & Tasks

- **git-worktrees skill**: Detailed worktree management
- **gitflow skill**: GitFlow branching model
- **jj skill**: Jujutsu (Git-compatible alternative)
- `/task:run github-pr`: Create GitHub PR
- `/task:run gitlab-mr`: Create GitLab MR
- `/task:run gitflow-*`: GitFlow workflows
