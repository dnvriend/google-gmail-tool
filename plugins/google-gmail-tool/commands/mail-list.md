---
description: List Gmail messages with filtering options
argument-hint: query
---

List Gmail messages or threads with optional filtering.

## Usage

```bash
google-gmail-tool mail list [--query "QUERY"] [--today] [-n N] [--text]
```

## Arguments

- `--query "QUERY"`: Gmail search query (optional)
- `--today`: Filter emails from today only
- `-n N`: Max results (default: 50, max: 500)
- `--text`: Output in text format
- `-v/-vv/-vvv`: Verbosity (INFO/DEBUG/TRACE)

## Examples

```bash
# List 50 most recent threads
google-gmail-tool mail list

# Find unread emails from today
google-gmail-tool mail list --today --query "is:unread"

# List with JSON output
google-gmail-tool mail list --query "from:team@company.com" -n 10
```

## Output

Returns JSON array with id, threadId, snippet, from, to, subject, date.
