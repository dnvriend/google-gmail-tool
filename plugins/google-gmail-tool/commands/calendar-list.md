---
description: List calendar events with time filtering
argument-hint: timerange
---

List calendar events with optional filtering.

## Usage

```bash
google-gmail-tool calendar list [--today] [--this-week] [--query "TEXT"]
```

## Arguments

- `--today`: Events for today
- `--tomorrow`: Events for tomorrow
- `--this-week`: Events this week (Monday-Sunday)
- `--days N`: Events for next N days
- `--query "TEXT"`: Search query (title, description, location)
- `-n N`: Max results (default: 100)
- `--text`: Output in text format
- `-v/-vv/-vvv`: Verbosity (INFO/DEBUG/TRACE)

## Examples

```bash
# List this week's events
google-gmail-tool calendar list --this-week

# Find meetings about project
google-gmail-tool calendar list --query "project meeting"

# Today's events in text format
google-gmail-tool calendar list --today --text
```

## Output

Returns JSON array with id, summary, start, end, location, attendees.
