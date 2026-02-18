---
name: granted
description: "AWS role assumption with Granted CLI. Use when assuming AWS profiles, switching accounts, opening AWS console, or authenticating to AWS. Triggers on: assume, granted, AWS profile, AWS role, AWS SSO, switch AWS account, AWS console, AWS authentication."
---

# Granted: AWS Role Assumption for Claude Code

Granted is a CLI tool that simplifies AWS role assumption and multi-account access. The `assume` command is the primary interface for assuming AWS profiles.

## Quick Reference

| Command | Purpose |
|---------|---------|
| `assume` | Interactive profile selector |
| `assume <profile>` | Assume specific profile |
| `assume <profile> -y --env` | Assume and export to .env file |
| `assume -c <profile>` | Open AWS console for profile |
| `assume -c -ar` | Open console for current role |
| `assume --exec "aws s3 ls"` | Run command with assumed role |
| `assume --unset` | Clear all Assume env vars |
| `granted sso-tokens list` | List cached SSO tokens |
| `granted sso-tokens clear` | Clear SSO token cache |

## Core Usage Patterns

### Assume a Profile

```bash
# Interactive profile selector
assume

# Assume specific profile
assume my-dev-profile

# Assume with custom duration (within role's max)
assume my-profile -d 4h
```

### Verify Authentication

After assuming a role, **always verify** with:

```bash
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AROAXXXXXXXXXX:session-name",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/RoleName/session-name"
}
```

### Open AWS Console

```bash
# Open console for profile
assume -c my-profile

# Open console for currently assumed role
assume -c -ar

# Open specific service
assume -c my-profile -s lambda

# Open specific region
assume -c my-profile -r us-west-2

# Get URL without opening browser
assume -c my-profile --url
```

### Region Shortcuts

| Shorthand | Region |
|-----------|--------|
| `ue1` | us-east-1 |
| `uw2` | us-west-2 |
| `eu1` | eu-west-1 |
| `ap1` | ap-southeast-1 |

```bash
assume -c my-profile -r ue1 -s ec2
```

## Claude Code Integration

### Pattern 1: Pre-Session Authentication

Before starting AWS work, ensure authentication:

```bash
# Check if already authenticated
aws sts get-caller-identity 2>/dev/null || assume my-profile
```

### Pattern 2: Profile Discovery

List available profiles:

```bash
# List all AWS profiles
grep -E '^\[profile ' ~/.aws/config | sed 's/\[profile //;s/\]//'

# Or use granted's interactive selector
assume
```

### Pattern 3: Multi-Account Operations

When working across accounts:

```bash
# First account
assume account-a-dev
aws s3 ls  # operations in account A

# Switch to second account (new terminal or re-assume)
assume account-b-prod
aws s3 ls  # operations in account B
```

### Pattern 4: SSO Token Management

```bash
# List cached SSO tokens
granted sso-tokens list

# Clear specific token
granted sso-tokens clear my-profile

# Clear all tokens (force re-auth)
granted sso-tokens clear
```

### Pattern 5: Export Credentials for Scripts

```bash
# Credentials are set as environment variables after assume
# For subprocesses that need explicit export:
eval $(assume my-profile --export)
```

### Pattern 6: Export to .env File

The `--env` flag writes credentials to a `.env` file. It prompts to create the file if it doesn't exist.

```bash
# Will prompt "Create .env file?" if not present - use -y to auto-accept
assume my-profile -y --env

# Or pipe yes to accept the prompt
yes | assume my-profile --env

# If .env already exists, it updates without prompting
touch .env && assume my-profile --env
```

**Note**: The `-y` flag auto-accepts creating the .env file. Without it, the command waits for interactive confirmation.

## Environment Variables After Assume

After running `assume`, these are set in your shell:

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | Temporary access key |
| `AWS_SECRET_ACCESS_KEY` | Temporary secret key |
| `AWS_SESSION_TOKEN` | Session token |
| `AWS_REGION` | Default region |
| `AWS_DEFAULT_REGION` | Default region (legacy) |
| `AWS_PROFILE` | Profile name |
| `GRANTED_SSO` | SSO indicator |

## AWS Profile Configuration

### SSO Profile (Identity Center)

```ini
# ~/.aws/config
[profile my-sso-profile]
sso_start_url = https://mycompany.awsapps.com/start
sso_region = us-east-1
sso_account_id = 123456789012
sso_role_name = DeveloperRole
region = us-east-1
```

### Cross-Account Role Assumption

```ini
[profile base-account]
region = us-east-1

[profile target-account]
source_profile = base-account
role_arn = arn:aws:iam::987654321098:role/CrossAccountRole
region = us-east-1
```

### Credential Process (External Auth)

```ini
[profile my-profile]
credential_process = /path/to/credential/helper
region = us-east-1
```

## Granted Configuration

Settings stored in `~/.granted/`:

```bash
# Set default browser
granted browser set

# Set SSO browser (separate from console browser)
granted browser set-sso

# Configure profile ordering (frecency or alphabetical)
granted settings profile-order set

# Enable shell completions
granted completion -s zsh >> ~/.zshrc
granted completion -s fish >> ~/.config/fish/completions/granted.fish
```

### Environment Variables

```bash
# Disable update checks
export GRANTED_DISABLE_UPDATE_CHECK=true

# Quiet mode (suppress output)
export GRANTED_QUIET=true
```

## Troubleshooting

### "No credentials found"

```bash
# Re-authenticate with SSO
granted sso-tokens clear my-profile
assume my-profile  # Will trigger browser auth
```

### "Token expired"

```bash
# Tokens typically last 1 hour, re-assume to refresh
assume my-profile
```

### "Profile not found"

```bash
# Verify profile exists in config
grep -A5 'my-profile' ~/.aws/config

# Check config file location
echo $AWS_CONFIG_FILE  # Should be empty or ~/.aws/config
```

### Verify Current Identity

```bash
# Always verify after assume
aws sts get-caller-identity

# Check which credentials are active
env | grep AWS_
```

## Best Practices for Claude Code Sessions

1. **Verify First**: Always run `aws sts get-caller-identity` before AWS operations
2. **Re-assume After Errors**: If operations fail with auth errors, re-assume the profile
3. **Check Profile Context**: Before destructive operations, verify you're in the correct account
4. **Use Specific Profiles**: Name profiles clearly (e.g., `prod-admin`, `dev-readonly`)
5. **Session Duration**: Use `-d` flag for longer sessions when doing extended work
6. **Terminal Scope**: Remember credentials are per-terminal; new terminals need new assume

## Command Reference

### assume

```
assume [options] [Profile]

Core Flags:
  -c, --console              Open AWS console in browser
  -t, --terminal             With -c, also export credentials to terminal
  -u, --url                  Get console URL without opening browser
  -s, --service <name>       Open console to specific AWS service
  -r, --region <region>      Region for console or credential export
  -d, --duration <time>      Session duration (e.g., 1h, 4h)
  -ar, --active-role         Use currently assumed role

Credential Export:
  -e, --env                  Export credentials to .env file (prompts to create)
  --ex, --export             Export credentials to ~/.aws/credentials
  --es, --export-sso-token   Export SSO token to ~/.aws/sso/cache
  -x, --export-all-env-vars  Export all credentials (for credential-process profiles)
  --un, --unset              Unset all Assume environment variables

SSO Direct Flags (use with --sso):
  --sso                      Assume using SSO flags instead of profile
  --sso-start-url <url>      SSO start URL
  --sso-region <region>      SSO region
  --account-id <id>          Target account ID
  --role-name <name>         Role name to assume
  --save-to <profile>        Save to AWS config as profile name

Prompts & Auth:
  -y, --confirm              Skip confirmation prompts (e.g., .env creation)
  --mfa-token <token>        Provide MFA token to skip prompt
  --wait                     Wait for Common Fate access approval
  --reason <text>            Provide reason for access request
  --attach <id>              Attach justification (e.g., --attach=JIRA-123)

Advanced:
  --exec <command>           Execute command after assuming role
  --chain <arn>              Assume role ARN using selected profile
  --cd, --console-destination <url>  Open console at specific destination
  --bp, --browser-profile <name>     Use specific browser profile
  --pt, --pass-through <args>        Pass args to proxy assumer
  --no-cache                 Force credential refresh, skip cache
  --verbose                  Enable debug logging
  -h, --help                 Show help
  -v, --version              Print version
```

### granted

```
granted [command]

Commands:
  browser        Configure browser settings
  completion     Generate shell completions
  settings       Configure granted settings
  sso-tokens     Manage SSO token cache
  version        Print version info
```

## Installation

### macOS (Homebrew)

```bash
brew tap common-fate/granted
brew install granted
```

### Linux (APT)

```bash
sudo apt update && sudo apt install gpg
wget -O- https://apt.releases.commonfate.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/common-fate-linux.gpg
echo "deb [signed-by=/usr/share/keyrings/common-fate-linux.gpg] https://apt.releases.commonfate.io stable main" | sudo tee /etc/apt/sources.list.d/common-fate.list
sudo apt update && sudo apt install granted
```

### Shell Alias Setup

Add to your shell profile (`.zshrc`, `.bashrc`):

```bash
# The assume command is typically aliased during installation
# If not, add:
alias assume="source assume"
```

## Sources

- [Granted Documentation](https://docs.commonfate.io/granted/getting-started)
- [Granted GitHub](https://github.com/common-fate/granted)
- [AWS SSO Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)
