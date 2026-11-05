#!/usr/bin/env python3
"""
One weekly command for the Open Disruption RAW_LINKS pipeline.

Copies a Google Keep note from the clipboard into RAW_LINKS/YYYY-MM-DD
(or reuses an existing file with --input), then runs:
  1. raw_links_to_weekly.py
  2. hybrid_workflow.py --smart-only
  3. open_links_in_chrome.py --delay 3 8

Usage:
    python scripts/week.py
    python scripts/week.py --date 2026-11-05
    python scripts/week.py --no-chrome
    python scripts/week.py --dry-run
    python scripts/week.py --force
    python scripts/week.py --input RAW_LINKS/2026-11-05
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from open_links_in_chrome import parse_raw_links_with_categories

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
RAW_LINKS_DIR = REPO_ROOT / "RAW_LINKS"
WEEKLY_DIR = REPO_ROOT / "weekly-links"
DATE_FMT = "%Y-%m-%d"
CHROME_DELAY = ["3", "8"]
YOUTUBE_PLACEHOLDER = "https://youtube.com/your-video-link"


@dataclass(frozen=True)
class WeekPaths:
    date_str: str
    raw_file: Path
    weekly_file: Path


def parse_date(value: str | None, today: date | None = None) -> date:
    """Resolve YYYY-MM-DD, or today's date when value is None."""
    if value is None:
        return today or date.today()
    try:
        return datetime.strptime(value, DATE_FMT).date()
    except ValueError as exc:
        raise ValueError(f"--date must be YYYY-MM-DD (e.g. 2026-11-05), got {value!r}") from exc


def paths_for_date(date_obj: date, repo_root: Path | None = None) -> WeekPaths:
    """Build RAW_LINKS and weekly-links paths for a date."""
    root = repo_root or REPO_ROOT
    date_str = date_obj.strftime(DATE_FMT)
    return WeekPaths(
        date_str=date_str,
        raw_file=root / "RAW_LINKS" / date_str,
        weekly_file=root / "weekly-links" / f"{date_str}-links.md",
    )


def count_urls_and_searches(content: str) -> tuple[int, int]:
    """Return (url_count, search_topic_count) using the shared RAW_LINKS parser."""
    items, search_topics = parse_raw_links_with_categories(content)
    url_count = sum(1 for _, typ in items if typ == "url")
    return url_count, len(search_topics)


def validate_raw_content(content: str) -> tuple[int, int]:
    """Require at least one URL. Returns (url_count, search_topic_count)."""
    url_count, search_count = count_urls_and_searches(content)
    if url_count == 0:
        raise ValueError("No URLs found in clipboard / RAW_LINKS content.")
    return url_count, search_count


def check_raw_file_writable(raw_file: Path, *, force: bool) -> None:
    """Refuse to overwrite an existing RAW_LINKS file unless force is True."""
    if raw_file.exists() and not force:
        raise FileExistsError(
            f"{raw_file} already exists. Re-run with --force to overwrite, "
            f"or use --input {raw_file}"
        )


def read_clipboard() -> str:
    """Read plain text from the macOS clipboard via pbpaste."""
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pbpaste not found. This command needs macOS clipboard access."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to read clipboard: {exc}") from exc
    return result.stdout


def has_youtube_placeholder(weekly_file: Path) -> bool:
    """True when the weekly markdown still has the default YouTube placeholder."""
    if not weekly_file.exists():
        return True
    text = weekly_file.read_text(encoding="utf-8")
    return YOUTUBE_PLACEHOLDER in text


def run_step(cmd: list[str], *, cwd: Path) -> int:
    """Run a child script; stream output. Return its exit code."""
    print(f"\n→ {' '.join(cmd)}")
    completed = subprocess.run(cmd, cwd=cwd)
    return completed.returncode


def resume_hint(raw_file: Path) -> str:
    rel = raw_file
    try:
        rel = raw_file.relative_to(REPO_ROOT)
    except ValueError:
        pass
    return f"python scripts/week.py --input {rel}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One weekly command: clipboard → RAW_LINKS → smart format → Chrome"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date in YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Existing RAW_LINKS file (skips clipboard)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing RAW_LINKS file when writing from clipboard",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview date, counts, and paths without writing or running steps",
    )
    parser.add_argument(
        "--no-chrome",
        action="store_true",
        help="Skip opening links in Chrome",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from_clipboard = args.input is None

    try:
        if args.input is not None:
            raw_path = args.input.expanduser()
            if not raw_path.is_absolute():
                raw_path = (Path.cwd() / raw_path).resolve()
            if not raw_path.exists():
                print(f"Error: File not found: {raw_path}", file=sys.stderr)
                return 1
            date_obj = parse_date(args.date or raw_path.name)
            paths = paths_for_date(date_obj)
            # Prefer the explicit input path (may differ from date-derived path)
            paths = WeekPaths(
                date_str=paths.date_str,
                raw_file=raw_path,
                weekly_file=paths.weekly_file,
            )
            content = raw_path.read_text(encoding="utf-8")
        else:
            date_obj = parse_date(args.date)
            paths = paths_for_date(date_obj)
            content = read_clipboard()
            if not content.strip():
                print("Error: Clipboard is empty.", file=sys.stderr)
                return 1

        url_count, search_count = validate_raw_content(content)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Date: {paths.date_str}")
    print(f"URLs: {url_count}")
    print(f"Search topics: {search_count}")
    print(f"RAW_LINKS: {paths.raw_file}")
    print(f"Weekly file: {paths.weekly_file}")

    if args.dry_run:
        print("\nDry run — no files written, no scripts run.")
        return 0

    if from_clipboard:
        try:
            check_raw_file_writable(paths.raw_file, force=args.force)
        except FileExistsError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        paths.raw_file.parent.mkdir(parents=True, exist_ok=True)
        paths.raw_file.write_text(content, encoding="utf-8")
        print(f"Wrote {paths.raw_file}")

    python = sys.executable
    steps: list[list[str]] = [
        [
            python,
            str(SCRIPT_DIR / "raw_links_to_weekly.py"),
            "--input",
            str(paths.raw_file),
            "--date",
            paths.date_str,
        ],
        [
            python,
            str(SCRIPT_DIR / "hybrid_workflow.py"),
            "--input",
            str(paths.weekly_file),
            "--smart-only",
        ],
    ]
    if not args.no_chrome:
        steps.append(
            [
                python,
                str(SCRIPT_DIR / "open_links_in_chrome.py"),
                str(paths.raw_file),
                "--delay",
                *CHROME_DELAY,
            ]
        )

    for cmd in steps:
        code = run_step(cmd, cwd=REPO_ROOT)
        if code != 0:
            print(
                f"\nStopped after failure (exit {code}). Resume with:\n  {resume_hint(paths.raw_file)}",
                file=sys.stderr,
            )
            return code

    if has_youtube_placeholder(paths.weekly_file):
        print(
            f"\nReminder: add the YouTube URL in {paths.weekly_file.name} "
            "(placeholder still present)."
        )

    print("\nWeekly pipeline finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
