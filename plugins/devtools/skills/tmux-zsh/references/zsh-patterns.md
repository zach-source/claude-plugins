# Zsh Configuration Patterns

## Table of Contents
1. [Plugin Managers](#plugin-managers)
2. [Vi-Mode Configuration](#vi-mode-configuration)
3. [Completion System](#completion-system)
4. [Prompt Configuration](#prompt-configuration)
5. [History Configuration](#history-configuration)
6. [Keybindings](#keybindings)
7. [Performance Optimization](#performance-optimization)

## Plugin Managers

### zplug (Nix-Native)

```nix
# Home Manager configuration
programs.zsh.zplug = {
  enable = true;
  plugins = [
    { name = "jeffreytse/zsh-vi-mode"; }
    { name = "mafredri/zsh-async"; }
    { name = "plugins/git"; tags = [ "from:oh-my-zsh" ]; }
  ];
};
```

### zinit (Performance-Focused)

```zsh
# Basic setup
source "$HOME/.zinit/bin/zinit.zsh"

# Turbo mode (lazy loading)
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions

# With compile
zinit ice wait lucid atload'_zsh_autosuggest_start'
zinit light zsh-users/zsh-autosuggestions
```

### oh-my-zsh (Framework)

```zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git docker kubectl)
source $ZSH/oh-my-zsh.sh
```

### Essential Plugins

| Plugin | Purpose |
|--------|---------|
| `zsh-autosuggestions` | Fish-like suggestions |
| `zsh-syntax-highlighting` | Command highlighting |
| `zsh-vi-mode` | Better vi mode |
| `fzf` | Fuzzy finder integration |
| `z` or `zoxide` | Directory jumping |

## Vi-Mode Configuration

### zsh-vi-mode (jeffreytse)

```zsh
# Configuration before plugin loads
ZVM_LAZY_KEYBINDINGS=false
ZVM_INIT_MODE=sourcing

function zvm_config() {
  ZVM_LINE_INIT_MODE=$ZVM_MODE_INSERT
  ZVM_VI_INSERT_ESCAPE_BINDKEY=jk
  ZVM_VI_SURROUND_BINDKEY=s-prefix
}

# Initialize other tools after zvm
function zvm_after_init() {
  # FZF keybindings
  [ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

  # Starship prompt
  eval "$(starship init zsh)"
}
```

### Built-in Vi Mode

```zsh
bindkey -v
export KEYTIMEOUT=1

# Cursor shape changes
function zle-keymap-select {
  if [[ ${KEYMAP} == vicmd ]] || [[ $1 = 'block' ]]; then
    echo -ne '\e[1 q'  # Block cursor
  elif [[ ${KEYMAP} == main ]] || [[ ${KEYMAP} == viins ]]; then
    echo -ne '\e[5 q'  # Beam cursor
  fi
}
zle -N zle-keymap-select
```

### Text Objects in Vi Mode

```zsh
# With zsh-vi-mode plugin
# ci" - Change inside quotes
# da( - Delete around parentheses
# yiw - Yank inner word
# vaw - Visual select a word
```

## Completion System

### Basic Setup

```zsh
autoload -Uz compinit
compinit

# Case-insensitive completion
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'

# Menu selection
zstyle ':completion:*' menu select

# Group completions
zstyle ':completion:*' group-name ''
zstyle ':completion:*:descriptions' format '%B%d%b'
```

### Performance-Optimized Compinit

```zsh
# Only regenerate completions once a day
autoload -Uz compinit
if [[ -n ${ZDOTDIR}/.zcompdump(#qN.mh+24) ]]; then
  compinit
else
  compinit -C
fi
```

### Custom Completions

```zsh
# Add completion directory
fpath+=~/.zsh/completions

# Generate completion for a command
compdef _gnu_generic mycommand
```

## Prompt Configuration

### Starship Integration

```zsh
# In zshrc (after zvm_after_init if using zsh-vi-mode)
eval "$(starship init zsh)"
```

```toml
# ~/.config/starship.toml
[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"
vicmd_symbol = "[<](bold blue)"

[directory]
truncation_length = 3

[git_branch]
symbol = " "
```

### Powerlevel10k

```zsh
# In zshrc
source /path/to/powerlevel10k/powerlevel10k.zsh-theme

# Run configuration wizard
p10k configure
```

### Minimal Custom Prompt

```zsh
# Simple prompt with git info
autoload -Uz vcs_info
precmd() { vcs_info }
zstyle ':vcs_info:git:*' formats '%b '
setopt PROMPT_SUBST
PROMPT='%F{blue}%~%f %F{yellow}${vcs_info_msg_0_}%f> '
```

## History Configuration

### Basic Settings

```zsh
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000

setopt EXTENDED_HISTORY       # Write timestamp to history
setopt HIST_EXPIRE_DUPS_FIRST # Expire duplicates first
setopt HIST_IGNORE_DUPS       # Ignore consecutive duplicates
setopt HIST_IGNORE_ALL_DUPS   # Remove older duplicate
setopt HIST_IGNORE_SPACE      # Ignore commands starting with space
setopt HIST_FIND_NO_DUPS      # No duplicates in search
setopt HIST_REDUCE_BLANKS     # Remove blank lines
setopt SHARE_HISTORY          # Share between sessions
```

### FZF History Search

```zsh
# Default FZF options
export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border"
export FZF_CTRL_R_OPTS="--preview 'echo {}' --preview-window down:3:hidden:wrap"

# Source FZF
source <(fzf --zsh)
# Or for older versions:
# source /usr/share/fzf/key-bindings.zsh
```

### Atuin (Advanced History)

```zsh
eval "$(atuin init zsh)"

# Configuration
# ~/.config/atuin/config.toml
# keymap_mode = "vim-normal"
# enter_accept = false
```

## Keybindings

### Binding Reference

```zsh
# List all bindings
bindkey -l  # List keymaps
bindkey     # Current keymap bindings
bindkey -M vicmd  # Vi command mode

# Common keymaps
# emacs - Default emacs mode
# viins - Vi insert mode
# vicmd - Vi command mode
```

### Common Bindings

```zsh
# History navigation
bindkey "^[[A" history-search-backward
bindkey "^[[B" history-search-forward

# Edit command in editor
autoload -U edit-command-line
zle -N edit-command-line
bindkey -M vicmd 'v' edit-command-line

# Quick directory up
bindkey -s '^U' 'cd ..\n'
```

### FZF Integration Bindings

```zsh
# In vi insert mode
zvm_bindkey viins '^R' fzf-history-widget
zvm_bindkey viins '^T' fzf-file-widget
zvm_bindkey viins '^[c' fzf-cd-widget
```

## Performance Optimization

### Startup Profiling

```zsh
# Add at top of .zshrc
zmodload zsh/zprof

# Run and check
zsh -i -c exit
zprof | head -20
```

### Lazy Loading

```zsh
# Lazy load nvm
nvm() {
  unfunction nvm
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"
  nvm "$@"
}

# Lazy load kubectl completion
kubectl() {
  unfunction kubectl
  source <(command kubectl completion zsh)
  command kubectl "$@"
}
```

### Defer Plugin Loading

```zsh
# Using zsh-defer plugin
zsh-defer source ~/.zsh/plugins/slow-plugin.zsh
```

### Compile Zsh Files

```zsh
# Compile zshrc for faster loading
zcompile ~/.zshrc

# Auto-compile on changes
if [[ ! -f ~/.zshrc.zwc ]] || [[ ~/.zshrc -nt ~/.zshrc.zwc ]]; then
  zcompile ~/.zshrc
fi
```

## Environment Variables

### PATH Management

```zsh
# In .zshenv (loaded for all shells)
typeset -U path  # Unique entries only
path=(
  $HOME/.local/bin
  $HOME/go/bin
  /opt/homebrew/bin
  $path
)
export PATH
```

### Shell Integration

```zsh
# Homebrew
eval "$(/opt/homebrew/bin/brew shellenv)"

# Cargo (Rust)
source "$HOME/.cargo/env"

# pyenv
eval "$(pyenv init -)"
```
