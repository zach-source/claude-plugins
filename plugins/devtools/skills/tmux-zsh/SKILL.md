---
name: tmux-zsh
description: Expert guidance for tmux terminal multiplexer and zsh shell configuration, design, and troubleshooting. Use when users need to configure tmux sessions, panes, keybindings, or plugins; set up zsh with vi-mode, plugins (zplug/zinit/oh-my-zsh), completions, or prompts (starship/powerlevel10k); integrate tmux and zsh with Nix/Home Manager; debug shell startup issues, keybinding conflicts, or plugin problems; or design productive terminal workflows.
---

# Tmux & Zsh Configuration Skill

## Overview

Expert knowledge for configuring tmux (terminal multiplexer) and zsh (Z shell) for productive terminal workflows.

**Announce at start:** "I'm using the tmux-zsh skill to help with terminal configuration."

## Quick Diagnostics

### Common Issues & Fixes

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Slow shell startup | Plugin overhead | Profile with `zsh -xv` or `zprof` |
| Vi-mode breaks prompt | Starship/zvm conflict | Configure `ZVM_INIT_MODE=sourcing` |
| Keybindings not working | Wrong binding mode | Check `bindkey -l` and mode (viins/vicmd) |
| Tmux colors wrong | TERM not set | Use `TERM=screen-256color` or `tmux-256color` |
| Copy/paste broken | Clipboard integration | Configure `set -g @yank_selection_mouse 'clipboard'` |
| Resurrect not restoring | Save path issues | Check `~/.tmux/resurrect/` permissions |

## Zsh Configuration

### Plugin Managers

| Manager | Config Style | Best For |
|---------|-------------|----------|
| **zplug** | Nix-native | Home Manager integration |
| **zinit** | Turbo mode | Performance-focused |
| **oh-my-zsh** | Framework | Beginners, comprehensive themes |
| **antigen** | Bundle-based | Simple setup |

### Vi-Mode Integration

**Critical pattern for starship + zsh-vi-mode:**

```zsh
# In initContent (before plugins)
ZVM_LAZY_KEYBINDINGS=false
ZVM_INIT_MODE=sourcing

function zvm_config() {
  ZVM_LINE_INIT_MODE=$ZVM_MODE_INSERT
  ZVM_VI_INSERT_ESCAPE_BINDKEY=jk
}

function zvm_after_init() {
  eval "$(starship init zsh)"
}

export FUNCNEST=500  # Prevent recursion errors
```

### Essential Options

```zsh
setopt HIST_IGNORE_ALL_DUPS  # No duplicate history entries
setopt SHARE_HISTORY         # Share history between sessions
setopt AUTO_CD               # cd into directories by typing name
setopt EXTENDED_GLOB         # Extended pattern matching
setopt NO_BEEP               # Silence terminal bell
```

### Keybinding Modes

```zsh
# Check current keymaps
bindkey -l

# Common modes:
# viins - vi insert mode (default for vi-mode)
# vicmd - vi command mode
# emacs - emacs mode

# Bind in specific mode
bindkey -M viins '^R' fzf-history-widget
bindkey -M vicmd 'v' edit-command-line
```

## Tmux Configuration

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Session** | Top-level container, persists detached |
| **Window** | Tab within session |
| **Pane** | Split within window |
| **Prefix** | Key combo to trigger tmux commands (default: `C-b`) |

### Essential Plugins (nixpkgs)

```nix
plugins = with pkgs.tmuxPlugins; [
  sensible        # Sane defaults
  yank            # Clipboard integration
  resurrect       # Session persistence
  continuum       # Auto-save/restore
  vim-tmux-navigator  # Seamless vim/tmux navigation
];
```

### Keybinding Patterns

```tmux
# Pane splits preserving path
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Vi-style pane resizing
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Vi copy mode
bind-key -T copy-mode-vi v send-keys -X begin-selection
bind-key -T copy-mode-vi y send-keys -X copy-selection
```

### Session Management

```bash
# Create named session
tmux new-session -s work -c ~/projects

# Attach or create
tmux new-session -A -s main

# List sessions
tmux list-sessions

# Switch sessions
tmux switch-client -t <session>
```

## Reference Files

- **Tmux patterns**: See [references/tmux-patterns.md](references/tmux-patterns.md) for advanced configuration patterns, plugin setup, and status bar customization
- **Zsh patterns**: See [references/zsh-patterns.md](references/zsh-patterns.md) for plugin ecosystems, completion systems, and prompt configuration
- **Nix integration**: See [references/nix-integration.md](references/nix-integration.md) for Home Manager module patterns and best practices

## Debugging

### Zsh Startup Profiling

```bash
# Add to ~/.zshrc
zmodload zsh/zprof

# Then run
zsh -i -c exit
zprof
```

### Tmux Debug

```bash
# Show all keybindings
tmux list-keys

# Show all options
tmux show-options -g

# Reload config
tmux source-file ~/.tmux.conf

# Check plugin loading
ls ~/.tmux/plugins/
```

### Common Conflicts

| Tool A | Tool B | Issue | Resolution |
|--------|--------|-------|------------|
| zsh-vi-mode | starship | Infinite recursion | Use `zvm_after_init` hook |
| fzf | atuin | Ctrl-R conflict | Choose one or rebind |
| tilish | vim-tmux-navigator | C-hjkl conflict | Configure `@tilish-navigate` |
| tmux | ghostty | Terminal capabilities | Set proper TERM |

## Resources

- **Tmux Manual**: `man tmux` or https://man.openbsd.org/tmux
- **Zsh Manual**: `man zshall` or https://zsh.sourceforge.io/Doc/
- **Home Manager Options**: https://nix-community.github.io/home-manager/options.html
