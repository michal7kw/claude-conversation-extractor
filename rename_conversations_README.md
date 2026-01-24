# Rename Conversations Script

A Python script to rename Claude conversation markdown files by adding timestamps extracted from file content.

## What It Does

Renames files from:
```
claude-conversation-YYYY-MM-DD-{SUFFIX}.md
```
To:
```
YYYY-MM-DD-HH_MM-{SUFFIX}.md
```

The time (HH:MM) is extracted from the `Date:` line inside each file's header.

## Example

**Before:** `claude-conversation-2025-12-19-agent-a0.md`
**After:** `2025-12-19-07_39-agent-a0.md`

## Usage

Preview changes (dry-run):
```bash
python rename_conversations.py --dir "E:\Code\Claude_code"
```

Apply changes:
```bash
python rename_conversations.py --dir "E:\Code\Claude_code" --execute
```

## Results (2026-01-24)

- **1,256 files renamed**
- **8 files skipped** (missing `Date:` header line)

Skipped files were all from 2025-11-23 with `-title` suffix.
