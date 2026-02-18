---
name: gitflow
description: Vincent Driessen's GitFlow branching model. Use when working with feature/release/hotfix branches, merging to develop or main, creating releases, or managing GitFlow workflows. Triggers on "gitflow", "feature branch", "release branch", "hotfix", "develop branch", "--no-ff", or questions about branch strategy.
context: fork
---

# GitFlow Branching Model

GitFlow is a structured branching model by Vincent Driessen for managing releases with parallel development.

**Reference**: https://nvie.com/posts/a-successful-git-branching-model/

## Branch Structure

```
main ─────●─────────────●─────────────●───── (production, tagged releases)
          │             ↑             ↑
          │      ┌──────┘      ┌──────┘
          │      │             │
release ──┼──────●─────────────●───────────── (release prep)
          │      ↑             ↑
          │      │             │
develop ──●──────●─────●───────●─────●─────── (integration)
          │            ↑       ↑     ↑
          │            │       │     │
feature ──┴────────────●───────●─────●─────── (new features)

hotfix ───────────────────────────────●────── (emergency fixes)
```

## Branch Types

| Branch | From | Merge To | Purpose |
|--------|------|----------|---------|
| `main` | - | - | Production releases (tagged) |
| `develop` | main | - | Integration branch |
| `feature/*` | develop | develop | New features |
| `release/*` | develop | main AND develop | Release preparation |
| `hotfix/*` | main | main AND develop | Emergency fixes |

## Key Rules

### 1. Always Use `--no-ff` Merges

```bash
# Preserves feature branch history
git merge --no-ff feature/my-feature -m "Merge feature/my-feature"
```

**Why?** Creates explicit merge commits showing when features were integrated.

### 2. Release/Hotfix Merge to BOTH Branches

**CRITICAL**: Releases and hotfixes must merge to:
- `main` (production deployment)
- `develop` (bring fixes forward)

```bash
# Release finish
git checkout main && git merge --no-ff release/1.0.0
git checkout develop && git merge --no-ff release/1.0.0

# Hotfix finish
git checkout main && git merge --no-ff hotfix/1.0.1
git checkout develop && git merge --no-ff hotfix/1.0.1
```

### 3. Tag Releases on Main

```bash
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin --tags
```

## Workflow Quick Reference

### Feature Development

```bash
# Start feature
git checkout develop
git checkout -b feature/user-auth

# Work on feature...
git add . && git commit -m "feat: add login form"

# Finish feature
git checkout develop
git merge --no-ff feature/user-auth
git branch -d feature/user-auth
git push origin develop
```

### Release Preparation

```bash
# Start release
git checkout develop
git checkout -b release/1.2.0
# Bump version in package.json, etc.
git commit -m "chore(release): bump version to 1.2.0"

# Release-critical fixes only...

# Finish release
git checkout main
git merge --no-ff release/1.2.0
git tag -a v1.2.0 -m "Release 1.2.0"
git checkout develop
git merge --no-ff release/1.2.0
git branch -d release/1.2.0
git push origin main develop --tags
```

### Emergency Hotfix

```bash
# Start hotfix (from main!)
git checkout main
git checkout -b hotfix/1.2.1
# Bump patch version
git commit -m "chore(hotfix): bump version to 1.2.1"

# Fix the bug...
git commit -m "fix(critical): resolve payment processing failure"

# Finish hotfix
git checkout main
git merge --no-ff hotfix/1.2.1
git tag -a v1.2.1 -m "Hotfix 1.2.1"
git checkout develop
git merge --no-ff hotfix/1.2.1
git branch -d hotfix/1.2.1
git push origin main develop --tags
```

## Task Framework Integration

Use the GitFlow tasks for automated workflows:

```bash
# Initialize GitFlow
/task:run gitflow-init

# Feature workflow
/task:run gitflow-feature-start user-authentication
/task:run gitflow-feature-finish

# Release workflow
/task:run gitflow-release-start 1.2.0
/task:run gitflow-release-finish

# Hotfix workflow
/task:run gitflow-hotfix-start
/task:run gitflow-hotfix-finish

# Check current state
/task:run gitflow-status
```

## When to Use GitFlow

**Good For:**
- ✅ Scheduled release cycles
- ✅ Multiple versions in production
- ✅ Explicit versioning (semver)
- ✅ Teams needing structure
- ✅ Software packages/libraries

**Consider Alternatives For:**
- ❌ Continuous deployment (use GitHub Flow)
- ❌ Single production version (use trunk-based)
- ❌ Small teams with rapid iteration

## Common Mistakes

### 1. Forgetting Dual Merge

```bash
# ❌ WRONG: Only merging release to main
git checkout main && git merge release/1.0.0
# Bug fixes in release are lost from develop!

# ✅ CORRECT: Merge to BOTH
git checkout main && git merge --no-ff release/1.0.0
git checkout develop && git merge --no-ff release/1.0.0
```

### 2. Using Fast-Forward Merges

```bash
# ❌ WRONG: Loses branch history
git checkout develop && git merge feature/x

# ✅ CORRECT: Preserves history
git checkout develop && git merge --no-ff feature/x
```

### 3. Hotfixing from Develop

```bash
# ❌ WRONG: Hotfix from develop includes unreleased features
git checkout develop
git checkout -b hotfix/1.0.1

# ✅ CORRECT: Hotfix from main (production code)
git checkout main
git checkout -b hotfix/1.0.1
```

### 4. Long-Running Release Branches

Release branches should be **short-lived** (days, not weeks).

If release takes too long:
- develop diverges significantly
- Merge conflicts grow
- Features pile up

### 5. Features on Release Branch

```bash
# ❌ WRONG: Adding features during release
git checkout release/1.0.0
git commit -m "feat: add cool new thing"

# ✅ CORRECT: Only release-critical fixes
git commit -m "fix(release): correct validation edge case"
git commit -m "docs(release): update changelog"
```

## Hotfix During Active Release

Special case: If a hotfix is needed while a release branch exists:

```bash
# Merge hotfix to RELEASE branch (not develop)
git checkout release/1.2.0
git merge --no-ff hotfix/1.1.1

# The release will carry the fix to develop when finished
```

## Version Bumping

| Event | Version Change | Example |
|-------|----------------|---------|
| Release start | Minor or major | 1.1.0 → 1.2.0 |
| Hotfix start | Patch | 1.2.0 → 1.2.1 |
| Pre-release | Suffix | 1.2.0-rc.1 |

Bump version at branch **creation**, not finish.

## Naming Conventions

| Type | Pattern | Examples |
|------|---------|----------|
| Feature | `feature/<name>` | `feature/user-auth`, `feature/JIRA-123` |
| Release | `release/<version>` | `release/1.2.0`, `release/2.0.0-beta` |
| Hotfix | `hotfix/<version>` | `hotfix/1.2.1`, `hotfix/critical-fix` |

## Commit Message Conventions

```bash
# Features
feat(auth): add OAuth2 login support
feat(api): implement rate limiting

# Fixes
fix(cart): resolve race condition in checkout
fix(ui): correct button alignment on mobile

# Release/Hotfix
chore(release): bump version to 1.2.0
fix(critical): patch SQL injection vulnerability
docs(release): update CHANGELOG for 1.2.0
```

## GitFlow vs Other Models

| Model | Main Branch | Integration | Best For |
|-------|-------------|-------------|----------|
| **GitFlow** | main + develop | develop | Scheduled releases |
| **GitHub Flow** | main only | main | Continuous deployment |
| **GitLab Flow** | main + environment | main | Multiple environments |
| **Trunk-Based** | main only | main | Small teams, rapid iteration |

## Reference

- Original article: https://nvie.com/posts/a-successful-git-branching-model/
- Git-flow CLI: https://github.com/nvie/gitflow
- Cheat sheet: https://danielkummer.github.io/git-flow-cheatsheet/
