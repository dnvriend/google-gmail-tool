---
description: List Google Tasks with filtering
argument-hint: filter
---

List Google Tasks with status and date filtering.

## Usage

```bash
google-gmail-tool task list [--completed] [--incomplete] [--today]
```

## Arguments

- `--completed`: Show only completed tasks
- `--incomplete`: Show only incomplete tasks
- `--today`: Tasks due today
- `--overdue`: Tasks past due date
- `-n N`: Max results (default: 100)
- `--text`: Output in text format
- `-v/-vv/-vvv`: Verbosity (INFO/DEBUG/TRACE)

## Examples

```bash
# List all tasks
google-gmail-tool task list

# Show incomplete tasks due today
google-gmail-tool task list --incomplete --today

# Show overdue tasks
google-gmail-tool task list --overdue
```

## Output

Returns JSON array with id, title, notes, due, status, updated.
