# Nix/Home Manager Integration for Tmux & Zsh

## Table of Contents
1. [Home Manager Zsh Module](#home-manager-zsh-module)
2. [Home Manager Tmux Module](#home-manager-tmux-module)
3. [Custom Tmux Plugins](#custom-tmux-plugins)
4. [Init Order Management](#init-order-management)
5. [Cross-Platform Patterns](#cross-platform-patterns)
6. [Troubleshooting](#troubleshooting)

## Home Manager Zsh Module

### Basic Configuration

```nix
{ config, pkgs, lib, ... }:
{
  programs.zsh = {
    enable = true;
    autocd = true;
    enableCompletion = true;
    autosuggestion.enable = true;
    syntaxHighlighting.enable = true;

    history = {
      size = 10000;
      save = 10000;
      path = "$HOME/.zsh_history";
      expireDuplicatesFirst = true;
      ignoreDups = true;
      ignoreSpace = true;
    };

    shellAliases = {
      ll = "ls -la";
      ".." = "cd ..";
    };
  };
}
```

### Zplug Configuration

```nix
programs.zsh.zplug = {
  enable = true;
  plugins = [
    { name = "jeffreytse/zsh-vi-mode"; }
    { name = "mafredri/zsh-async"; }
    { name = "mattmc3/ez-compinit"; }
    { name = "akermu/emacs-libvterm"; }
    {
      name = "plugins/git";
      tags = [ "from:oh-my-zsh" ];
    }
  ];
};
```

### Init Content Ordering

```nix
programs.zsh.initContent = lib.mkMerge [
  # BEFORE plugins (mkBefore)
  (lib.mkBefore ''
    # FZF configuration
    export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border"

    # ZVM configuration BEFORE it loads
    ZVM_LAZY_KEYBINDINGS=false
    ZVM_INIT_MODE=sourcing

    function zvm_config() {
      ZVM_LINE_INIT_MODE=$ZVM_MODE_INSERT
      ZVM_VI_INSERT_ESCAPE_BINDKEY=jk
    }

    function zvm_after_init() {
      eval "$(starship init zsh)"
    }
  '')

  # MAIN configuration (default priority)
  ''
    setopt HIST_IGNORE_ALL_DUPS
    setopt SHARE_HISTORY
  ''

  # AFTER plugins (mkAfter)
  (lib.mkAfter ''
    # Post-plugin keybindings
    zvm_bindkey viins '^R' fzf-history-widget
  '')
];
```

### Environment Variables

```nix
programs.zsh.envExtra = ''
  # Loaded for ALL shell types (login, interactive, non-interactive)
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
'';

programs.zsh.sessionVariables = {
  EDITOR = "nvim";
  VISUAL = "nvim";
};
```

### Profile vs InitExtra vs EnvExtra

| Option | Loaded When | Use For |
|--------|-------------|---------|
| `envExtra` | All shells | PATH, brew init, env vars |
| `profileExtra` | Login shells | One-time setup |
| `initContent` | Interactive shells | Plugins, aliases, keybindings |
| `initExtraFirst` | First in init | Critical early config |

## Home Manager Tmux Module

### Basic Configuration

```nix
{ config, pkgs, lib, ... }:
{
  programs.tmux = {
    enable = true;
    mouse = true;
    escapeTime = 10;
    terminal = "screen-256color";
    shell = "${pkgs.zsh}/bin/zsh";
    newSession = true;
    keyMode = "vi";
    historyLimit = 50000;
    baseIndex = 1;

    plugins = with pkgs.tmuxPlugins; [
      sensible
      yank
      resurrect
      continuum
    ];

    extraConfig = ''
      # Additional raw tmux config
      set -g status-position top
    '';
  };
}
```

### Plugins with Extra Config

```nix
plugins = with pkgs.tmuxPlugins; [
  sensible
  yank
  {
    plugin = resurrect;
    extraConfig = ''
      set -g @resurrect-capture-pane-contents 'on'
      set -g @resurrect-strategy-nvim 'session'
    '';
  }
  {
    plugin = continuum;
    extraConfig = ''
      set -g @continuum-restore 'on'
      set -g @continuum-save-interval '5'
    '';
  }
  {
    plugin = vim-tmux-navigator;
    extraConfig = ''
      bind-key -n C-h if -F "#{@pane-is-vim}" 'send-keys C-h' 'select-pane -L'
      bind-key -n C-j if -F "#{@pane-is-vim}" 'send-keys C-j' 'select-pane -D'
      bind-key -n C-k if -F "#{@pane-is-vim}" 'send-keys C-k' 'select-pane -U'
      bind-key -n C-l if -F "#{@pane-is-vim}" 'send-keys C-l' 'select-pane -R'
    '';
  }
];
```

## Custom Tmux Plugins

### From GitHub (Not in Nixpkgs)

```nix
{
  plugin = pkgs.tmuxPlugins.mkTmuxPlugin {
    pluginName = "tmux-fzf-pane-switch";
    version = "unstable-2024-01-01";
    src = pkgs.fetchFromGitHub {
      owner = "Kristijan";
      repo = "tmux-fzf-pane-switch";
      rev = "master";
      sha256 = "sha256-XXXX...";  # Get with nix-prefetch-url
    };
  };
  extraConfig = ''
    set -g @fzf-pane-switch-key 'p'
  '';
}
```

### Custom rtpFilePath

```nix
{
  plugin = pkgs.tmuxPlugins.mkTmuxPlugin {
    pluginName = "tmux-which-key";
    version = "unstable-2024-01-01";
    src = pkgs.fetchFromGitHub {
      owner = "alexwforsythe";
      repo = "tmux-which-key";
      rev = "main";
      sha256 = "sha256-XXXX...";
    };
    # Some plugins don't follow standard naming
    rtpFilePath = "plugin.sh.tmux";
  };
}
```

### Getting SHA256

```bash
# For GitHub repos
nix-prefetch-url --unpack https://github.com/OWNER/REPO/archive/BRANCH.tar.gz

# Or use nix-prefetch-github
nix-prefetch-github OWNER REPO --rev BRANCH
```

## Init Order Management

### Zsh Loading Order

```
1. /etc/zshenv (system)
2. ~/.zshenv (envExtra)
3. /etc/zprofile (system, login shells)
4. ~/.zprofile (profileExtra, login shells)
5. /etc/zshrc (system, interactive)
6. ~/.zshrc (initContent, interactive)
7. /etc/zlogin (system, login shells)
8. ~/.zlogin (loginExtra, login shells)
```

### Using lib.mkOrder for Precise Control

```nix
initContent = lib.mkMerge [
  (lib.mkOrder 100 ''
    # Very early - before most things
  '')
  (lib.mkOrder 500 ''
    # Middle - default priority
  '')
  (lib.mkOrder 1000 ''
    # Late - after most things
  '')
];

# mkBefore = mkOrder 500
# mkAfter = mkOrder 1500
```

## Cross-Platform Patterns

### Darwin vs Linux Detection

```nix
{ config, pkgs, lib, ... }:
{
  programs.zsh.initContent = lib.mkMerge [
    ''
      # Common config
    ''

    (lib.mkIf pkgs.stdenv.isDarwin ''
      # macOS specific
      if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
      fi
    '')

    (lib.mkIf pkgs.stdenv.isLinux ''
      # Linux specific
      export XDG_RUNTIME_DIR="/run/user/$UID"
    '')
  ];
}
```

### Platform-Specific Clipboard

```nix
programs.tmux.extraConfig = lib.mkMerge [
  ''
    # Common config
  ''

  (lib.mkIf pkgs.stdenv.isDarwin ''
    bind-key -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "pbcopy"
  '')

  (lib.mkIf pkgs.stdenv.isLinux ''
    bind-key -T copy-mode-vi y send-keys -X copy-pipe-and-cancel "xclip -selection clipboard"
  '')
];
```

## Troubleshooting

### Common Issues

**Shell not changing:**
```nix
# Ensure shell is in /etc/shells
environment.shells = with pkgs; [ zsh ];
users.users.USERNAME.shell = pkgs.zsh;
```

**Tmux plugins not loading:**
```bash
# Check plugin directory
ls ~/.tmux/plugins/

# Reload tmux config
tmux source-file ~/.tmux.conf
```

**Zsh completions not working:**
```bash
# Rebuild completions
rm -f ~/.zcompdump*
compinit
```

**Plugin loading order issues:**
```nix
# Use lib.mkBefore/mkAfter for precise ordering
initContent = lib.mkMerge [
  (lib.mkBefore "# This runs first")
  "# This runs in the middle"
  (lib.mkAfter "# This runs last")
];
```

### Debugging Zsh

```bash
# Verbose startup
zsh -xv

# Profile startup time
zmodload zsh/zprof
# ... at end of .zshrc
zprof

# Check loaded options
setopt
```

### Debugging Tmux

```bash
# Check effective config
tmux show-options -g

# Check keybindings
tmux list-keys

# Check plugins loaded
tmux list-plugins  # If TPM installed

# Verbose tmux server
tmux -vvv new-session
```

### Rebuilding After Changes

```bash
# Home Manager standalone
home-manager switch

# With nix-darwin
darwin-rebuild switch --flake .

# With NixOS
nixos-rebuild switch --flake .

# Check generation
home-manager generations
```

## File Locations

| File | Purpose | Managed By |
|------|---------|-----------|
| `~/.zshrc` | Main zsh config | Home Manager |
| `~/.zshenv` | Environment vars | Home Manager |
| `~/.tmux.conf` | Tmux config | Home Manager |
| `~/.config/starship.toml` | Starship prompt | Manual or Home Manager |
| `~/.tmux/resurrect/` | Session saves | tmux-resurrect |
| `~/.local/share/zsh/` | Completion cache | zsh |
