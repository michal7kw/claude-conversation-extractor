#!/usr/bin/env python3
"""
Rename Claude conversation files from:
  claude-conversation-YYYY-MM-DD-{SUFFIX}.md
to:
  YYYY-MM-DD-HH_MM-{SUFFIX}.md

The time (HH:MM) is extracted from the Date: line inside each file's header.
"""

import argparse
import re
from pathlib import Path


def extract_datetime_from_file(filepath: Path) -> tuple[str, str, str] | None:
    """
    Read the first 10 lines of the file and extract date and time from Date: line.
    Returns (date, hour, minute) or None if not found.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                match = re.match(
                    r"Date:\s*(\d{4}-\d{2}-\d{2})\s+(\d{2}):(\d{2}):\d{2}", line
                )
                if match:
                    return match.group(1), match.group(2), match.group(3)
    except Exception as e:
        print(f"  Error reading {filepath}: {e}")
    return None


def extract_suffix_from_filename(filename: str) -> str | None:
    """
    Extract the suffix from claude-conversation-YYYY-MM-DD-{SUFFIX}.md
    Returns the suffix (e.g., 'agent-a0') or None if pattern doesn't match.
    """
    # Pattern: claude-conversation-YYYY-MM-DD-{SUFFIX}.md
    match = re.match(r"claude-conversation-\d{4}-\d{2}-\d{2}-(.+)\.md$", filename)
    if match:
        return match.group(1)
    return None


def rename_conversations(root_dir: Path, execute: bool = False) -> None:
    """
    Find and rename all claude-conversation-*.md files.
    """
    # Find all matching files
    pattern = "claude-conversation-*.md"
    files = list(root_dir.rglob(pattern))

    print(f"Found {len(files)} files matching '{pattern}'")
    print(f"Mode: {'EXECUTE' if execute else 'DRY-RUN (preview only)'}")
    print("-" * 60)

    success_count = 0
    skipped_count = 0
    error_count = 0

    for filepath in sorted(files):
        filename = filepath.name

        # Extract suffix from original filename
        suffix = extract_suffix_from_filename(filename)
        if suffix is None:
            print(f"SKIP: {filename} (doesn't match expected pattern)")
            skipped_count += 1
            continue

        # Extract datetime from file content
        datetime_info = extract_datetime_from_file(filepath)
        if datetime_info is None:
            print(f"SKIP: {filename} (no Date: line found in header)")
            skipped_count += 1
            continue

        date, hour, minute = datetime_info

        # Build new filename
        new_filename = f"{date}-{hour}_{minute}-{suffix}.md"
        new_filepath = filepath.parent / new_filename

        # Check if new file already exists
        if new_filepath.exists() and new_filepath != filepath:
            print(f"SKIP: {filename} -> {new_filename} (target already exists)")
            skipped_count += 1
            continue

        # Check if already renamed
        if new_filename == filename:
            print(f"SKIP: {filename} (already has correct name)")
            skipped_count += 1
            continue

        # Perform or preview rename
        if execute:
            try:
                filepath.rename(new_filepath)
                print(f"RENAMED: {filename} -> {new_filename}")
                success_count += 1
            except Exception as e:
                print(f"ERROR: {filename} -> {new_filename}: {e}")
                error_count += 1
        else:
            print(f"WOULD RENAME: {filename} -> {new_filename}")
            success_count += 1

    # Summary
    print("-" * 60)
    print("Summary:")
    print(f"  {'Renamed' if execute else 'Would rename'}: {success_count}")
    print(f"  Skipped: {skipped_count}")
    if error_count > 0:
        print(f"  Errors: {error_count}")

    if not execute and success_count > 0:
        print("\nTo apply changes, run with --execute flag")


def main():
    parser = argparse.ArgumentParser(
        description="Rename Claude conversation files to include timestamp from content"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform renames (default is dry-run)",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("."),
        help="Root directory to search (default: current directory)",
    )

    args = parser.parse_args()

    root_dir = args.dir.resolve()
    print(f"Searching in: {root_dir}")

    rename_conversations(root_dir, execute=args.execute)


if __name__ == "__main__":
    main()
