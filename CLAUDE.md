# google-gmail-tool - Project Specification

## Goal

A professional CLI that provides access to Google services: Gmail, Calendar (Events), Tasks, and Drive.

## What is google-gmail-tool?

`google-gmail-tool` is a command-line utility built with modern Python tooling and best practices. It provides both human and AI-agent friendly interfaces to Google APIs with OAuth2 authentication.

## Key Features

- **Multi-Service Support**: Gmail, Google Calendar (events), Google Tasks, Google Drive
- **Agent-Friendly Design**: JSON output to stdout, logs to stderr, self-documenting help
- **Smart Integrations**: Export to Obsidian with smart merge (preserves checked items)
- **Type-Safe**: Strict mypy checking throughout
- **Production Ready**: Comprehensive error handling and validation

## Technical Requirements

### Runtime

- Python 3.14+
- Installable globally with mise
- Cross-platform (macOS, Linux, Windows)

### Dependencies

- `click>=8.1.7` - CLI framework
- `google-api-python-client>=2.147.0` - Google API client
- `google-auth>=2.35.0` - OAuth2 authentication
- `google-auth-oauthlib>=1.2.0` - OAuth2 flows
- `google-auth-httplib2>=0.2.0` - HTTP transport
- `html2text>=2024.2.26` - HTML to markdown conversion
- `python-slugify>=8.0.0` - Slug generation for filenames
- `python-dateutil>=2.8.2` - Date parsing utilities

### Development Dependencies

- `ruff>=0.8.0` - Linting and formatting
- `mypy>=1.7.0` - Type checking
- `pytest>=7.4.0` - Testing framework
- `types-requests>=2.31.0` - Type stubs
- `types-python-dateutil>=2.8.19` - Type stubs

## CLI Command Structure

```bash
google-gmail-tool <command-group> <command> [OPTIONS]
```

### Command Groups

1. **completion** - Shell completion (top-level command)
   - `bash` - Generate bash completion script
   - `zsh` - Generate zsh completion script
   - `fish` - Generate fish completion script

2. **auth** - Authentication verification
   - `check` - Verify OAuth credentials and API access
   - `login` - Complete OAuth flow to generate credentials

3. **mail** - Gmail operations
   - `list` - List threads/messages with filtering
   - `get` - Get specific message/thread details
   - `send` - Send email
   - `export-obsidian` - Export threads to Obsidian vault

4. **calendar** - Google Calendar operations (Events API)
   - `list` - List events with time range and query filtering
   - `get` - Get event details by ID
   - `create` - Create new events
   - `update` - Update existing events
   - `delete` - Delete events
   - `export-obsidian` - Export events to Obsidian daily notes

5. **task** - Google Tasks operations (Tasks API)
   - `list` - List tasks with status/due date filtering
   - `get` - Get task details by ID
   - `create` - Create new tasks
   - `update` - Update existing tasks
   - `complete` - Mark tasks as completed
   - `uncomplete` - Mark tasks as incomplete
   - `delete` - Delete tasks
   - `export-obsidian` - Export tasks to Obsidian daily notes

6. **drive** - Google Drive operations (read-only)
   - `list` - List files with filtering and sorting
   - `get` - Get file metadata
   - `download` - Download files
   - `search` - Search for files with common filters

### Global Options

- `--help` / `-h` - Show help message
- `--version` - Show version
- `-v` / `--verbose` - Increase verbosity (can be repeated: -v INFO, -vv DEBUG)

## Project Structure

```
google-gmail-tool/
├── google_gmail_tool/
│   ├── __init__.py
│   ├── cli.py                        # Click CLI entry point with command groups
│   ├── logging_config.py             # Logging setup (multi-level verbosity)
│   ├── core/                         # Core library (CLI-independent, importable)
│   │   ├── __init__.py
│   │   ├── auth.py                   # OAuth2 authentication & credential management
│   │   ├── gmail_client.py           # Gmail API client (threads, messages, send)
│   │   ├── calendar_client.py        # Calendar API client (events CRUD)
│   │   ├── task_client.py            # Tasks API client (tasks CRUD)
│   │   ├── drive_client.py           # Drive API client (list, search, download)
│   │   ├── obsidian_mail_exporter.py # Mail to Obsidian export with smart merge
│   │   ├── obsidian_calendar_exporter.py  # Calendar to Obsidian export
│   │   └── obsidian_task_exporter.py # Tasks to Obsidian export with smart merge
│   └── commands/                     # CLI command implementations
│       ├── __init__.py
│       ├── auth_commands.py          # auth check, login
│       ├── completion_commands.py    # completion bash, zsh, fish
│       ├── mail_commands.py          # mail list, get, send, export-obsidian
│       ├── calendar_commands.py      # calendar list, get, export-obsidian
│       ├── calendar_create_update_delete.py  # calendar create, update, delete
│       ├── task_commands.py          # task list, get, export-obsidian
│       ├── task_create_update_delete.py  # task create, update, delete, complete, uncomplete
│       └── drive_commands.py         # drive list, get, download, search
├── tests/
│   ├── __init__.py
│   └── test_utils.py
├── pyproject.toml       # Project configuration
├── README.md            # User documentation
├── CLAUDE.md            # This file (development spec)
├── Makefile             # Development commands
├── LICENSE              # MIT License
├── .mise.toml           # mise configuration
└── .gitignore
```

## Code Style & Standards

- **Type Safety**: Type hints for all functions, strict mypy checking
- **Documentation**: Code-RAG friendly module docstrings with:
  - Module purpose and key responsibilities
  - API integration details
  - Design patterns used
  - Usage examples
  - AI-generated code acknowledgment
- **Code Quality**: Follow PEP 8 via ruff, 100 character line length
- **Error Handling**: Exception-based in core, CLI handles formatting
- **Output Design**: JSON to stdout, logs to stderr (agent-friendly)
- **CLI Design**: Self-documenting help with inline examples (Agent-Friendly CLI Help pattern)

## Architecture Principles

### Core vs CLI Separation

- **core/**: CLI-independent, importable library
  - Pure API clients (no click dependencies)
  - Return structured data (dicts, lists)
  - Raise exceptions for errors
  - Logging for observability

- **commands/**: CLI layer
  - Thin wrappers around core clients
  - Handle click decorators and options
  - Format output (JSON or text)
  - Exit codes and error messages
  - User interaction (prompts, confirmations)

### Agent-Friendly Design

- **Self-Documenting Help**: Comprehensive `--help` with inline examples
- **Progressive Complexity**: Examples progress from simple to advanced
- **Output Structure**: Predictable JSON schemas, documented in help
- **Error Messages**: Actionable guidance on how to fix issues
- **Exit Codes**: Consistent across commands (0=success, 1=error, 2=not found/cancelled)

## Development Workflow

```bash
# Install dependencies
make install

# Run linting
make lint

# Format code
make format

# Type check
make typecheck

# Run tests
make test

# Run all checks
make check

# Full pipeline
make pipeline
```

## Installation Methods

### Global installation with mise

```bash
cd /path/to/google-gmail-tool
mise use -g python@3.14
uv sync
uv tool install .
```

After installation, `google-gmail-tool` command is available globally.

### Local development

```bash
uv sync
uv run google-gmail-tool [args]
```
