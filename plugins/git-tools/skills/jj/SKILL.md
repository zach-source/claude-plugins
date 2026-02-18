---
name: jj
description: Jujutsu (jj) version control system. Use when working with jj repositories, creating changes, rebasing, managing bookmarks, resolving conflicts, or syncing with Git remotes. Triggers on "jj", "jujutsu", "jj rebase", "jj bookmark", "jj squash", or when user mentions working with jj instead of git.
context: fork
---

# Jujutsu (jj) Version Control

Jujutsu is a Git-compatible VCS with automatic rebasing, first-class conflicts, and an operation log that makes mistakes reversible.

## Key Differences from Git

| Git | jj | Notes |
|-----|-----|-------|
| Staging area | No staging | Working copy IS a commit |
| `git checkout -b` | `jj bookmark create` | Bookmarks are optional |
| `git commit` | `jj new` | Finishes current, starts new |
| `git commit --amend` | Just edit files | Auto-amends working copy |
| `git stash` | `jj new` + `jj edit @-` | Switch without losing work |
| `git rebase -i` | `jj squash`, `jj split` | No interactive mode needed |
| Conflicts block operations | Conflicts are first-class | Rebase always succeeds |
| `git reflog` | `jj op log` | Full operation history |

## Setup

```bash
# Install
brew install jj

# Configure identity
jj config set --user user.name "Your Name"
jj config set --user user.email "your@email.com"

# Initialize in existing Git repo (recommended)
jj git init --colocate

# Clone with colocated Git
jj git clone --colocate https://github.com/user/repo
```

## Core Concepts

### Working Copy is a Commit

In jj, there's no staging area. Your working directory IS a commit that's automatically updated as you edit files.

```bash
# Edit files... they're automatically part of @
jj status    # See what's changed in @
jj diff      # See the diff of @
```

### Change ID vs Commit ID

- **Change ID** (`k`, `m`, etc.): Stable across rewrites, use for references
- **Commit ID**: Changes when commit content changes

```bash
jj log
# @  kpqxywon user@email.com 2025-01-15 14:30
# │  (empty) (no description set)
# ○  mzvwutvl user@email.com 2025-01-15 14:25
# │  Add new feature
```

Use the short change ID (e.g., `k` or `kpq`) to reference commits.

## Essential Commands

### Status & Viewing

```bash
jj status              # Working copy status (alias: jj st)
jj diff                # Diff of current change
jj diff -r @-          # Diff of parent change
jj show                # Show current change details
jj show -r xyz         # Show specific change
jj log                 # Commit graph
jj log -r 'trunk()..@' # Commits between trunk and @
```

### Creating Changes

```bash
jj new                 # Finish current, start new empty change
jj new -m "message"    # New change with description
jj commit -m "msg"     # Describe + new (Git-like shortcut)
jj describe -m "msg"   # Set description for current change
```

### Navigating

```bash
jj edit <change-id>    # Switch to a different change
jj edit @-             # Edit parent
jj prev                # Move @ to parent (like edit @-)
jj next                # Move @ to child
jj new <change-id>     # Start new change on top of specified one
```

### History Editing

```bash
jj squash              # Squash @ into parent
jj squash --into xyz   # Squash @ into specific change
jj squash -i           # Interactive squash (select hunks)

jj split               # Split current change interactively
jj split -r xyz        # Split a specific change

jj abandon             # Discard current change (keeps descendants)
jj abandon xyz         # Discard specific change
```

### Rebasing

```bash
jj rebase -d main      # Rebase @ onto main
jj rebase -b @ -d main # Rebase @ and ancestors onto main
jj rebase -s xyz -d main # Rebase xyz and descendants onto main

# Move a change to a different parent
jj rebase -r xyz -d abc
```

**Key insight**: Rebase ALWAYS succeeds. Conflicts become part of the commit and can be resolved later.

## Bookmarks (Branches)

Bookmarks are jj's version of Git branches - named pointers to commits.

```bash
jj bookmark list                    # List all bookmarks
jj bookmark create feature          # Create at @ (fails if exists)
jj bookmark set feature             # Create or update at @
jj bookmark set feature -r xyz      # Point to specific change
jj bookmark delete feature          # Delete bookmark
jj bookmark rename old new          # Rename bookmark
jj bookmark track main@origin       # Track remote bookmark
```

## Remote Operations

```bash
# Fetch from remote
jj git fetch
jj git fetch --remote origin

# Push bookmark to remote
jj git push --bookmark feature
jj git push --bookmark feature --allow-new  # First push

# Push all bookmarks
jj git push --all

# Import/export with colocated Git
jj git import    # Import Git refs
jj git export    # Export to Git refs
```

## Conflict Resolution

Conflicts in jj are first-class citizens - they don't block operations.

```bash
jj log                 # Conflicted changes show "conflict" marker
jj status              # Shows conflicted files

# Resolve interactively
jj resolve
jj resolve <file>

# Resolve with strategy
jj resolve --tool=:ours <file>
jj resolve --tool=:theirs <file>

# List conflicts
jj resolve --list
```

**Workflow**: Just edit the conflicted files directly - jj auto-detects resolution.

## Revsets (Selecting Commits)

| Revset | Meaning |
|--------|---------|
| `@` | Current working copy |
| `@-` | Parent of @ |
| `@--` | Grandparent of @ |
| `xyz` | Change with ID starting with xyz |
| `main` | Bookmark named main |
| `main@origin` | Remote bookmark |
| `trunk()` | Main development branches |
| `heads(all())` | All branch heads |
| `root()` | Root commit |
| `x..y` | Commits between x and y |
| `x::y` | x and all ancestors of y that are descendants of x |
| `x \| y` | Union of x and y |
| `x & y` | Intersection |
| `~x` | All commits except x |

```bash
# Examples
jj log -r 'trunk()..@'     # Your changes since trunk
jj log -r 'heads(all())'   # All branch heads
jj rebase -d 'trunk()'     # Rebase onto main/master
```

## Undo & Recovery

```bash
jj undo                # Undo last operation
jj redo                # Redo after undo

jj op log              # View operation history
jj op show <op-id>     # Show operation details
jj op restore <op-id>  # Restore to previous state

jj evolog              # Evolution log of current change
jj evolog -r xyz       # Evolution of specific change
```

## Common Workflows

### Start New Work

```bash
jj new main -m "Add new feature"
# Edit files...
jj status
jj diff
```

### Amend Current Change

```bash
# Just edit files - @ auto-updates
# Or explicitly describe:
jj describe -m "Better description"
```

### Squash Workflow

```bash
# Make changes in small increments
jj new -m "Part 1"
# work...
jj new -m "Part 2"
# work...
jj new -m "Part 3"

# Squash all into one
jj squash --into @--
jj squash --into @-
# Now @ contains all work
```

### Edit Workflow (Insert Change)

```bash
jj log
# @  z - Current work
# ○  y - Previous change
# ○  x - Earlier change

jj new x              # Insert after x, before y
# Edit files...
# jj automatically rebases y and z on top
```

### Stacked PRs

```bash
jj new main
# Work on part 1...
jj new
# Work on part 2...
jj new
# Work on part 3...

# Create bookmarks
jj bookmark set part1 -r @--
jj bookmark set part2 -r @-
jj bookmark set part3 -r @

# Push each
jj git push --bookmark part1 --allow-new
jj git push --bookmark part2 --allow-new
jj git push --bookmark part3 --allow-new
```

### Update from Upstream

```bash
jj git fetch
jj rebase -d main@origin
```

### Fix Specific Commit

```bash
jj edit xyz           # Switch to that commit
# Make fixes...
jj new                # Return to tip (auto-rebases descendants)
```

## Pro Tips

```bash
# Absorb: auto-distribute changes to appropriate commits
jj absorb

# Fix: run formatters/linters on changed files
jj fix

# Compare iterations of a change
jj interdiff --from @- --to @

# Duplicate a change
jj duplicate xyz

# Show file at specific revision
jj file show -r xyz path/to/file

# Blame/annotate
jj file annotate path/to/file
```

## Configuration

```bash
# View config
jj config list

# Set user config
jj config set --user user.name "Name"
jj config set --user user.email "email"

# Set repo config
jj config set --repo some.setting value

# Edit config file directly
jj config edit --user
```

### Useful Config Options

```toml
# ~/.config/jj/config.toml

[ui]
default-command = "log"
diff-editor = "meld"
merge-editor = "meld"

[git]
auto-local-bookmark = true

[aliases]
l = ["log", "-r", "trunk()..@"]
```

## With Git Colocated

When using `--colocate`, both `.jj` and `.git` exist:

- Git tools still work (`git log`, `git status`)
- Changes sync automatically
- Push/pull through jj OR git
- Best of both worlds

```bash
# In colocated repo
git status        # Works!
jj git import     # Import Git changes into jj
jj git export     # Export jj changes to Git refs
```
