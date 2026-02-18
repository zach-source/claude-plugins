# zach-source/claude-plugins

A Claude plugin marketplace — 44 skills organized into 8 plugins.

## Install

```bash
claude plugin add github:zach-source/claude-plugins
```

Or install individual plugins:

```bash
claude plugin add github:zach-source/claude-plugins/plugins/git-tools
claude plugin add github:zach-source/claude-plugins/plugins/testing
```

## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| **git-tools** | git, gitflow, git-worktrees, jj, changelog-generator | Git workflow skills |
| **devops** | deploy, ci-polling, tilt, gitlab-cicd-debug, granted | DevOps and infrastructure |
| **cloud-and-observability** | aws-skills, otel-go, otel-python, dbos-go, dbos-python | Cloud, tracing, durable execution |
| **ai-memory** | graphiti, context7, replay-buffer, promptcontext | AI memory and context management |
| **documents** | docx, d3js, tapestry, file-organizer | Document creation and organization |
| **testing** | tdd, pypict, webapp-testing, playwright | Testing workflows and automation |
| **devtools** | ast-grep, osgrep, tmux-zsh, terminal-title, tasks, mcp-builder | Developer tools |
| **plugin-dev** | agent-development, command-development, hook-development, mcp-integration, plugin-settings, plugin-structure, skill-development, skill-creator, writing-rules, frontend-design, example-skill | Claude plugin development |

## Nix Flake Usage

Add as a flake input for declarative deployment:

```nix
# flake.nix
inputs.claude-plugins = {
  url = "github:zach-source/claude-plugins";
  flake = false;
};
```

## License

MIT
