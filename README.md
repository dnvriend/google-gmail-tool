<div align="center">
  <img src=".github/assets/logo.png" alt="google-gmail-tool logo" width="200"/>
  <h1>google-gmail-tool</h1>

  [![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
  [![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://github.com/python/mypy)
  [![AI Generated](https://img.shields.io/badge/AI-Generated-blueviolet.svg)](https://www.anthropic.com/claude)
  [![Built with Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-5A67D8.svg)](https://www.anthropic.com/claude/code)

  <p>A professional CLI for access to Gmail, Calendar, Tasks, and Drive APIs with OAuth2 authentication</p>
</div>

## Table of Contents

- [About](#about)
- [Use Cases](#use-cases)
- [Features](#features)
- [Installation](#installation)
- [Shell Completion](#shell-completion)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Authentication](#authentication)
- [Development](#development)
- [Resources](#resources)
- [License](#license)

## About

### What is google-gmail-tool?

`google-gmail-tool` provides programmatic access to Google services through an agent-friendly CLI. Built with modern Python tooling (uv, mise, click) and designed for both human operators and AI agents.

**Official Documentation:**
- [Gmail API](https://developers.google.com/gmail/api)
- [Google Calendar API](https://developers.google.com/calendar)
- [Google Drive API](https://developers.google.com/drive)

### Why a CLI-First Tool?

This tool emphasizes:

- **🤖 Agent-Friendly Design**: Structured commands and self-documenting help enable AI agents (like Claude Code) to discover features and self-correct when commands fail (ReAct loops)
- **🔧 Composable Architecture**: JSON output to stdout, logs to stderr for easy piping and integration with automation workflows
- **🧩 Reusable Building Blocks**: Commands serve as building blocks for MCP servers, Claude Code skills, shell scripts, or custom automation pipelines
- **📦 Dual-Mode Operation**: Use as a CLI tool or import as a Python library for programmatic access
- **✅ Production Quality**: Type-safe (mypy strict), comprehensive error handling, tested, and documented

## Use Cases

- 📚 **Knowledge Base Management**: Export Gmail threads and Calendar events to markdown for Obsidian vaults
- 💻 **Source Code Intelligence**: Archive project communications and documentation to version control
- 🔍 **Semantic Search**: Build RAG systems with email and calendar data
- 🎯 **Automation**: Create workflows for email processing, calendar sync, and file management
- 🤖 **AI Agent Integration**: Provide Google API access to AI assistants and automation agents

## Features

- ✅ **OAuth2 Authentication**: Secure credential management via environment variables
- ✅ **API Access Verification**: Test Gmail, Calendar, and Drive permissions with visual feedback (✓/✗)
- ✅ **Agent-Friendly CLI**: Self-documenting help with inline examples for discovery and self-correction
- ✅ **Type-Safe**: Strict mypy checking for reliability
- ✅ **Production Ready**: Comprehensive error handling with actionable messages
- ✅ **Modern Tooling**: Built with uv, mise, and click

## Installation

### Prerequisites

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Google Cloud Project with OAuth 2.0 credentials

### Install from source

```bash
# Clone the repository
git clone https://github.com/dnvriend/google-gmail-tool.git
cd google-gmail-tool

# Install globally with uv
uv tool install .
```

### Install with mise (recommended for development)

```bash
cd google-gmail-tool
mise trust
mise install
uv sync
uv tool install .
```

### Verify installation

```bash
google-gmail-tool --version
google-gmail-tool --help
```

## Shell Completion

Enable tab completion for all commands, options, and arguments in your shell.

### Supported Shells

- Bash (≥4.4)
- Zsh
- Fish

### Installation

**Bash** (add to `~/.bashrc` or `~/.bash_profile`):
```bash
eval "$(google-gmail-tool completion bash)"
```

**Zsh** (add to `~/.zshrc`):
```bash
eval "$(google-gmail-tool completion zsh)"
```

**Fish** (save to completions directory):
```bash
google-gmail-tool completion fish > ~/.config/fish/completions/google-gmail-tool.fish
```

### Performance Optimization

For better shell startup performance, generate completion scripts once and source them:

```bash
# Bash
google-gmail-tool completion bash > ~/.google-gmail-tool-complete.bash
echo 'source ~/.google-gmail-tool-complete.bash' >> ~/.bashrc

# Zsh
google-gmail-tool completion zsh > ~/.google-gmail-tool-complete.zsh
echo 'source ~/.google-gmail-tool-complete.zsh' >> ~/.zshrc
```

After installation, restart your shell or source your configuration:
```bash
source ~/.bashrc    # Bash
source ~/.zshrc     # Zsh
# Fish loads automatically
```

For detailed help:
```bash
google-gmail-tool completion --help
```

## Configuration

### Setting Up OAuth2 Credentials

1. **Create OAuth 2.0 Credentials**
   - Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new project or select existing
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Desktop application" as application type
   - Download the JSON credentials file

2. **Enable Required APIs**
   - [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
   - [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)
   - [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)

3. **Configure OAuth Scopes** (when generating tokens)
   ```
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/calendar
   https://www.googleapis.com/auth/tasks
   https://www.googleapis.com/auth/drive.readonly
   ```

   **Note**: Calendar requires full access (not readonly) for create/update/delete operations. Tasks requires full access for all task operations.

### Environment Variables

Set one of the following:

```bash
# Option 1: Path to credentials file (recommended)
export GOOGLE_GMAIL_TOOL_CREDENTIALS=~/.config/google-gmail-tool/credentials.json

# Option 2: Credentials as JSON string
export GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON='{"type":"authorized_user","client_id":"...","client_secret":"...","refresh_token":"..."}'
```

### Credential Format

The credentials file should contain:

```json
{
  "type": "authorized_user",
  "client_id": "your-client-id.apps.googleusercontent.com",
  "client_secret": "your-client-secret",
  "refresh_token": "your-refresh-token"
}
```

**Note**: You'll need to complete an OAuth flow once to obtain the `refresh_token`. Use tools like [Google OAuth Playground](https://developers.google.com/oauthplayground/) or implement a simple OAuth flow.

## Usage

### Authentication

#### Generate OAuth Credentials (First Time Setup)

```bash
# Using client secret JSON file (easiest)
google-gmail-tool auth login --json-file ~/Downloads/client_secret.json

# Using client ID and secret directly
google-gmail-tool auth login \
  --client-id "YOUR_CLIENT_ID.apps.googleusercontent.com" \
  --client-secret "YOUR_CLIENT_SECRET"
```

This will:
1. Open your browser for OAuth authorization
2. Request all required scopes (gmail, calendar, tasks, drive)
3. Save credentials to `~/.config/google-gmail-tool/credentials.json`
4. Set `GOOGLE_GMAIL_TOOL_CREDENTIALS` environment variable

**See [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed OAuth setup instructions.**

#### Verify OAuth Credentials and API Access

```bash
# Basic authentication check
google-gmail-tool auth check

# Check with detailed error messages
google-gmail-tool auth check --verbose
```

**Output Example:**
```
🔐 Checking Google OAuth credentials...

✓ Credentials loaded successfully
  Token valid: True
  Has refresh token: True

🔍 Verifying API access...

✓ GMAIL: Gmail API access granted
✓ CALENDAR: Calendar API access granted
✓ DRIVE: Drive API access granted

✅ All API checks passed! You're ready to use google-gmail-tool.
```

**Exit Codes:**
- `0` - All checks passed
- `1` - Authentication failed or API access denied

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Credentials not found | Set `GOOGLE_GMAIL_TOOL_CREDENTIALS` or `GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON` |
| API access denied | Ensure OAuth scopes include: `gmail.readonly`, `calendar` (full), `tasks` (full), `drive.readonly` |
| Token expired | Credentials will auto-refresh using `refresh_token` |
| Invalid format | Check credential JSON matches required format |
| Insufficient permissions (403) | Regenerate OAuth token with all required scopes listed above |

### Mail Commands

#### List Gmail Messages

```bash
# List recent threads (default: 10)
google-gmail-tool mail list

# List with custom limit
google-gmail-tool mail list -n 50

# Search by query
google-gmail-tool mail list -q "from:noreply@github.com"

# List with labels
google-gmail-tool mail list --label INBOX --label UNREAD
```

#### Get Message Details

```bash
# Get specific message or thread
google-gmail-tool mail get <message-id>

# Get with text format
google-gmail-tool mail get <message-id> --format text
```

#### Send Email

```bash
# Send email
google-gmail-tool mail send \
  --to "user@example.com" \
  --subject "Meeting Notes" \
  --body "Here are the notes from today's meeting..."
```

#### Export to Obsidian

```bash
# Export recent threads to Obsidian vault
google-gmail-tool mail export-obsidian -n 20

# With query filter
google-gmail-tool mail export-obsidian -q "project-alpha" -n 10
```

### Calendar Commands

#### List Events

```bash
# List this week's events (default)
google-gmail-tool calendar list

# List today's events
google-gmail-tool calendar list --today

# List next 7 days
google-gmail-tool calendar list --days 7

# Search events
google-gmail-tool calendar list --this-week --query "standup"

# Custom date range
google-gmail-tool calendar list \
  --range-start "2025-11-20" \
  --range-end "2025-11-30"

# Human-readable output
google-gmail-tool calendar list --today --text
```

#### Get Event Details

```bash
# Get event by ID
google-gmail-tool calendar get <event-id>

# Text format
google-gmail-tool calendar get <event-id> --format text
```

#### Create Events

```bash
# Basic event
google-gmail-tool calendar create \
  --title "Team Standup" \
  --start "2025-11-20 09:00" \
  --end "2025-11-20 09:30"

# With location and attendees
google-gmail-tool calendar create \
  --title "Client Meeting" \
  --start "2025-11-20 14:00" \
  --end "2025-11-20 15:00" \
  --location "Conference Room A" \
  --attendees "john@example.com,jane@example.com"

# All-day event
google-gmail-tool calendar create \
  --title "Holiday" \
  --date "2025-12-25" \
  --all-day

# With Google Meet
google-gmail-tool calendar create \
  --title "Remote Standup" \
  --start "2025-11-20 09:00" \
  --end "2025-11-20 09:30" \
  --add-meet
```

#### Update Events

```bash
# Update event title
google-gmail-tool calendar update <event-id> \
  --title "Updated Meeting Title"

# Update time
google-gmail-tool calendar update <event-id> \
  --start "2025-11-20 15:00" \
  --end "2025-11-20 16:00"
```

#### Delete Events

```bash
# Delete with confirmation
google-gmail-tool calendar delete <event-id>

# Force delete (skip confirmation)
google-gmail-tool calendar delete <event-id> --force
```

#### Export to Obsidian

```bash
# Export today's events
google-gmail-tool calendar export-obsidian --today

# Export this week (7 daily notes)
google-gmail-tool calendar export-obsidian --this-week

# Export custom range
google-gmail-tool calendar export-obsidian \
  --range-start "2025-11-20" \
  --range-end "2025-11-25"

# Filter by query
google-gmail-tool calendar export-obsidian --today --query "standup"
```

**Smart Merge**: Preserves checked-off items while updating schedule

### Task Commands

#### List Tasks

```bash
# List incomplete tasks (default)
google-gmail-tool task list

# List completed tasks
google-gmail-tool task list --completed

# List all tasks
google-gmail-tool task list --all

# Filter by due date
google-gmail-tool task list --today
google-gmail-tool task list --overdue
google-gmail-tool task list --this-week

# Search tasks
google-gmail-tool task list --query "project"

# Combine filters
google-gmail-tool task list --incomplete --this-week --query "meeting"

# Human-readable output
google-gmail-tool task list --text
```

#### Get Task Details

```bash
# Get task by ID
google-gmail-tool task get <task-id>

# Text format
google-gmail-tool task get <task-id> --format text
```

#### Create Tasks

```bash
# Minimal task (only title required)
google-gmail-tool task create --title "Review PR #123"

# With due date
google-gmail-tool task create \
  --title "Review PR #123" \
  --due "2025-11-20"

# With notes and due date
google-gmail-tool task create \
  --title "Review PR #123" \
  --notes "Check code quality and tests" \
  --due "2025-11-20"
```

#### Update Tasks

```bash
# Update title
google-gmail-tool task update <task-id> --title "New Title"

# Update due date
google-gmail-tool task update <task-id> --due "2025-11-21"

# Update multiple fields
google-gmail-tool task update <task-id> \
  --title "Updated Task" \
  --notes "New notes" \
  --due "2025-11-21"
```

#### Complete/Uncomplete Tasks

```bash
# Complete single task
google-gmail-tool task complete <task-id>

# Complete multiple tasks
google-gmail-tool task complete <task-id-1> <task-id-2> <task-id-3>

# Uncomplete task
google-gmail-tool task uncomplete <task-id>
```

#### Delete Tasks

```bash
# Delete with confirmation
google-gmail-tool task delete <task-id>

# Force delete (skip confirmation)
google-gmail-tool task delete <task-id> --force
```

#### Export to Obsidian

```bash
# Export tasks to today's note
google-gmail-tool task export-obsidian --today

# Export to this week's notes (7 files)
google-gmail-tool task export-obsidian --this-week

# Export for specific date
google-gmail-tool task export-obsidian --date 2025-11-20

# Export custom range
google-gmail-tool task export-obsidian \
  --range-start "2025-11-20" \
  --range-end "2025-11-25"

# Filter by keyword
google-gmail-tool task export-obsidian --today --query "project"

# Include completed tasks
google-gmail-tool task export-obsidian --today --completed
```

**Smart Merge**: Preserves checked-off items while updating task details

**Output Format**: Tasks organized by sections (Overdue, Today, Tomorrow, This Week, No Due Date)

### Drive Commands (Coming Soon)

- `drive list` - List Drive files
- `drive get` - Download Drive files

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/dnvriend/google-gmail-tool.git
cd google-gmail-tool

# Install dependencies
make install

# Show available commands
make help
```

### Available Make Commands

```bash
make install          # Install dependencies
make format           # Format code with ruff
make lint             # Run linting with ruff
make typecheck        # Run type checking with mypy
make test             # Run tests with pytest
make check            # Run all checks (lint, typecheck, test)
make pipeline         # Run full pipeline (format, check, build, install-global)
make build            # Build package
make run ARGS="..."   # Run google-gmail-tool locally
make clean            # Remove build artifacts
```

### Project Structure

```
google-gmail-tool/
├── google_gmail_tool/          # Main package
│   ├── __init__.py            # Public API exports
│   ├── cli.py                 # CLI entry point with groups
│   ├── core/                  # Core library (importable, CLI-independent)
│   │   ├── __init__.py
│   │   └── auth.py           # Authentication & credential management
│   ├── commands/              # CLI command implementations
│   │   ├── __init__.py
│   │   └── auth_commands.py  # auth check command
│   └── utils.py               # Shared utilities
├── tests/                     # Test suite
│   ├── __init__.py
│   └── test_utils.py
├── pyproject.toml             # Project configuration
├── Makefile                   # Development commands
├── README.md                  # This file
├── LICENSE                    # MIT License
└── CLAUDE.md                  # Development documentation
```

### Code Standards

- Python 3.14+ with modern syntax (dict/list over Dict/List)
- Type hints required for all functions (mypy strict mode)
- Module-level docstrings acknowledging AI-generated code
- Line length: 100 characters
- Exception-based error handling in core, CLI handles formatting
- Composable output: JSON to stdout, logs to stderr

## Resources

### Official Documentation

- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [Google Auth Python Library](https://github.com/googleapis/google-auth-library-python)
- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
- [Calendar API Reference](https://developers.google.com/calendar/api/v3/reference)
- [Drive API Reference](https://developers.google.com/drive/api/v3/reference)

### Related Tools

- [click](https://click.palletsprojects.com/) - CLI framework
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- [mise](https://mise.jdx.dev/) - Development environment manager

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Dennis Vriend**

- GitHub: [@dnvriend](https://github.com/dnvriend)
- Email: dvriend@ilionx.com

---

**Generated with AI**

This project was generated using [Claude Code](https://www.anthropic.com/claude/code), an AI-powered development tool by [Anthropic](https://www.anthropic.com/). The implementation follows a "Code-RAG first" documentation model with comprehensive inline documentation for semantic code understanding.

Made with ❤️ using Python 3.14
