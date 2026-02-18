# Tmux Configuration Patterns

## Table of Contents
1. [Plugin Configuration](#plugin-configuration)
2. [Session Workflows](#session-workflows)
3. [Status Bar Customization](#status-bar-customization)
4. [Copy Mode & Clipboard](#copy-mode--clipboard)
5. [Terminal Integration](#terminal-integration)
6. [Performance Tuning](#performance-tuning)

## Plugin Configuration

### Resurrect + Continuum (Session Persistence)

```tmux
# Resurrect settings
set -g @resurrect-capture-pane-contents 'on'
set -g @resurrect-strategy-vim 'session'
set -g @resurrect-strategy-nvim 'session'
set -g @resurrect-processes 'vim nvim emacs htop "git log" "docker" claude'

# Continuum auto-save/restore
set -g @continuum-restore 'on'
set -g @continuum-save-interval '5'  # Minutes
set -g @continuum-boot 'on'
set -g @continuum-boot-options 'ghostty,wezterm,alacritty'
```

### Vim-Tmux Navigator

```tmux
# Smart pane switching with Vim awareness
bind-key -n C-h if -F "#{@pane-is-vim}" 'send-keys C-h' 'select-pane -L'
bind-key -n C-j if -F "#{@pane-is-vim}" 'send-keys C-j' 'select-pane -D'
bind-key -n C-k if -F "#{@pane-is-vim}" 'send-keys C-k' 'select-pane -U'
bind-key -n C-l if -F "#{@pane-is-vim}" 'send-keys C-l' 'select-pane -R'
```

### FZF Integration Plugins

```tmux
# fzf-url: Open URLs from terminal
set -g @fzf-url-bind 'u'

# fzf-pane-switch: Quick pane navigation
set -g @fzf-pane-switch-key 'p'

# tmux-thumbs: Quick text selection
set -g @thumbs-key F
set -g @thumbs-reverse enabled
set -g @thumbs-unique enabled
```

### Tilish (i3-like Layouts)

```tmux
set -g @tilish-navigate 'on'
set -g @tilish-default 'even-horizontal'
# Alt+Enter: New pane
# Alt+hjkl: Navigate
# Alt+Shift+hjkl: Move panes
```

### Custom Plugin from GitHub

```nix
# In Nix/Home Manager
{
  plugin = pkgs.tmuxPlugins.mkTmuxPlugin {
    pluginName = "tmux-fzf-pane-switch";
    version = "unstable-2024-01-01";
    src = pkgs.fetchFromGitHub {
      owner = "Kristijan";
      repo = "tmux-fzf-pane-switch";
      rev = "master";
      sha256 = "sha256-XXXX...";
    };
  };
}
```

## Session Workflows

### Project-Based Sessions

```tmux
# Keybindings for common projects
bind-key N new-session -A -s 'nix' -c '~/dotfiles/nix'
bind-key W new-session -A -s 'work' -c '~/repos/workspaces/'
bind-key P command-prompt -p "Project:" "new-session -A -s '%%' -c '#{pane_current_path}'"
```

### Session Chooser

```tmux
bind-key C-s choose-tree -s
bind-key S command-prompt -p "New Session:" "new-session -A -s '%%'"
bind-key K confirm-before -p "Kill session #S? (y/n)" kill-session
```

### Sesh Integration (External Session Manager)

```tmux
bind-key "T" run-shell "sesh connect \"\$(
  sesh list | fzf-tmux -p 55%,60% \
    --no-sort --prompt '> ' \
    --bind 'ctrl-a:change-prompt(all)+reload(sesh list)' \
    --bind 'ctrl-t:change-prompt(tmux)+reload(sesh list -t)' \
    --bind 'ctrl-x:change-prompt(zoxide)+reload(sesh list -z)'
)\""
```

## Status Bar Customization

### Minimal Status Bar

```tmux
set -g status-position top
set -g status-left " #S "
set -g status-right " %H:%M %b %d "
set -g status-left-length 30
set -g status-right-length 50
```

### Git-Aware Status Bar

```tmux
set -g status-right "#[fg=magenta]#(cd #{pane_current_path}; git branch --show-current 2>/dev/null | sed 's/^/ /') #[fg=cyan]%H:%M"
set -g status-right-length 100
set -g status-interval 5
```

### System Monitoring Status Bar

```tmux
# Using cpu plugin
set -g @cpu_low_fg_color "#[fg=green]"
set -g @cpu_medium_fg_color "#[fg=yellow]"
set -g @cpu_high_fg_color "#[fg=red]"

# Status line
set -g status-right "CPU:#{cpu_percentage} MEM:#{ram_percentage} | %H:%M"
```

### Window Status Format

```tmux
# Active window
set-window-option -g window-status-current-format "#[bold] #I:#W#{?window_zoomed_flag,Z,} "

# Inactive windows
set-window-option -g window-status-format " #I:#W "

# Auto-rename based on current path
set-window-option -g automatic-rename on
set-window-option -g automatic-rename-format '#{b:pane_current_path}'
```

## Copy Mode & Clipboard

### Vi-Style Copy Mode

```tmux
set-window-option -g mode-keys vi

# Selection and copy
bind-key -T copy-mode-vi v send-keys -X begin-selection
bind-key -T copy-mode-vi y send-keys -X copy-selection
bind-key -T copy-mode-vi r send-keys -X rectangle-toggle
bind-key -T copy-mode-vi Escape send-keys -X cancel
```

### macOS Clipboard Integration

```tmux
# Using yank plugin
set -g @yank_selection_mouse 'clipboard'
set -g @yank_with_mouse on

# Manual pbcopy integration
bind-key -T copy-mode-vi MouseDragEnd1Pane send-keys -X copy-pipe-and-cancel "pbcopy"
bind-key -T copy-mode-vi Enter send-keys -X copy-pipe-and-cancel "pbcopy"
```

### Linux Clipboard (xclip/xsel)

```tmux
bind-key -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "xclip -selection clipboard"
```

## Terminal Integration

### True Color Support

```tmux
set -g default-terminal "screen-256color"
set -sa terminal-overrides ',xterm-256color:RGB'
set -as terminal-overrides ',*:Tc'
```

### Undercurl and Italics

```tmux
# Undercurl support
set -as terminal-overrides ',*:Smulx=\E[4::%p1%dm'

# Underscore colors
set -as terminal-overrides ',*:Setulc=\E[58::2::%p1%{65536}%/%d::%p1%{256}%/%{255}%&%d::%p1%{255}%&%d%;m'

# Italics
set -as terminal-overrides ',xterm*:sitm=\E[3m'
```

### Focus Events (for Vim autoread)

```tmux
set -g focus-events on
```

## Performance Tuning

### History and Buffer

```tmux
set -g history-limit 50000
set -g display-time 4000
```

### Escape Time (Important for Vim)

```tmux
set -g escape-time 10  # Or even 0
```

### Status Update Interval

```tmux
set -g status-interval 5  # Seconds
```

### Aggressive Resize

```tmux
setw -g aggressive-resize on
```

## Theme Examples

### Gruvbox

```tmux
set -g @plugin 'egel/tmux-gruvbox'
set -g @tmux-gruvbox 'dark'  # or 'light'
```

### Catppuccin

```tmux
set -g @plugin 'catppuccin/tmux'
set -g @catppuccin_flavour 'mocha'
```

### Manual Minimal Theme

```tmux
set -g status-style "bg=default,fg=white"
set -g pane-border-style "fg=colour238"
set -g pane-active-border-style "fg=colour39"
set -g message-style "bg=colour0,fg=colour3"
```
