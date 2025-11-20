---
description: Send email via Gmail API
argument-hint: to subject body
---

Send an email message via Gmail.

## Usage

```bash
google-gmail-tool mail send --to "EMAIL" --subject "SUBJECT" --body "BODY"
```

## Arguments

- `--to EMAIL`: Recipient email (required)
- `--subject TEXT`: Email subject (required)
- `--body TEXT`: Email body (required)
- `--cc EMAIL`: CC recipients (optional)
- `--bcc EMAIL`: BCC recipients (optional)
- `--html`: Send as HTML instead of plain text
- `--dry-run`: Preview without sending
- `-v/-vv/-vvv`: Verbosity (INFO/DEBUG/TRACE)

## Examples

```bash
# Send plain text email
google-gmail-tool mail send \
    --to "user@example.com" \
    --subject "Meeting Notes" \
    --body "Here are the notes..."

# Send HTML email with CC
google-gmail-tool mail send \
    --to "user@example.com" \
    --cc "team@example.com" \
    --subject "Report" \
    --body "<h1>Report</h1>" \
    --html
```

## Output

Returns success confirmation with message ID.
