#!/usr/bin/env python3
"""Remove YAML frontmatter from markdown files."""

import argparse
import re
from pathlib import Path


def remove_frontmatter(content: str) -> tuple[str, bool]:
    """Remove YAML frontmatter from content.

    Returns:
        Tuple of (new_content, was_modified)
    """
    # Pattern: starts with ---, captures everything until next ---
    # Must be at the very start of the file
    pattern = r"^---\s*\n.*?\n---\s*\n?"

    match = re.match(pattern, content, re.DOTALL)
    if match:
        new_content = content[match.end() :]
        return new_content, True
    return content, False


def main():
    parser = argparse.ArgumentParser(
        description="Remove YAML frontmatter from markdown files"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually modify files (default is dry-run)",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to process (default: current directory)",
    )
    args = parser.parse_args()

    root = Path(args.path).resolve()

    files_scanned = 0
    files_with_frontmatter = 0

    for md_file in root.rglob("*.md"):
        files_scanned += 1

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[ERROR] Could not read {md_file}: {e}")
            continue

        new_content, was_modified = remove_frontmatter(content)

        if was_modified:
            files_with_frontmatter += 1
            if args.apply:
                try:
                    md_file.write_text(new_content, encoding="utf-8")
                    print(f"[MODIFIED] {md_file}")
                except Exception as e:
                    print(f"[ERROR] Could not write {md_file}: {e}")
            else:
                print(f"[WOULD MODIFY] {md_file}")

    print()
    print("Summary:")
    print(f"  Files scanned: {files_scanned}")
    print(f"  Files with frontmatter: {files_with_frontmatter}")
    if not args.apply:
        print()
        print("This was a DRY RUN. Use --apply to actually modify files.")


if __name__ == "__main__":
    main()
