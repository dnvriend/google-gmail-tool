---
description: Search Google Drive files and folders
argument-hint: name
---

Search for files and folders in Google Drive.

## Usage

```bash
google-gmail-tool drive search [--name "NAME"] [--type TYPE]
```

## Arguments

- `--name "NAME"`: Search by file/folder name
- `--type TYPE`: Filter by type (document, spreadsheet, folder, pdf)
- `--owner me|others|anyone`: Filter by owner
- `--shared`: Show only shared files
- `-n N`: Max results (default: 50)
- `--text`: Output in text format
- `-v/-vv/-vvv`: Verbosity (INFO/DEBUG/TRACE)

## Examples

```bash
# Search by name
google-gmail-tool drive search --name "report"

# Find PDFs I own
google-gmail-tool drive search --type pdf --owner me

# Find shared spreadsheets
google-gmail-tool drive search --type spreadsheet --shared
```

## Output

Returns JSON array with id, name, mimeType, size, modified, webViewLink.
