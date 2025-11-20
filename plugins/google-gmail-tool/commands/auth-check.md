---
description: Verify OAuth credentials and API access
argument-hint:
---

Verify Google OAuth credentials and API access.

## Usage

```bash
google-gmail-tool auth check [-v|-vv|-vvv]
```

## Environment Variables

- `GOOGLE_GMAIL_TOOL_CREDENTIALS_JSON`: Full OAuth2 credentials as JSON
- `GOOGLE_GMAIL_TOOL_CREDENTIALS`: Path to credentials JSON file

## Examples

```bash
# Check authentication status
google-gmail-tool auth check

# Check with verbose output
google-gmail-tool auth check -vv
```

## Output

Returns status for Gmail, Calendar, Tasks, and Drive API access.
