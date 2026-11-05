#!/usr/bin/env python3
"""Unit tests for scripts/week.py pure helpers (no clipboard, network, or Chrome)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from week import (
    check_raw_file_writable,
    parse_date,
    paths_for_date,
    validate_raw_content,
)


SAMPLE_RAW = """
<HEADLINES>
https://example.com/one
https://example.com/two
"search topic"
"""


def test_parse_date_defaults_to_today():
    today = date(2026, 11, 5)
    assert parse_date(None, today=today) == today


def test_parse_date_parses_iso():
    assert parse_date("2026-11-05") == date(2026, 11, 5)


def test_parse_date_rejects_bad_format():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_date("11-05-2026")


def test_paths_for_date(tmp_path: Path):
    paths = paths_for_date(date(2026, 11, 5), repo_root=tmp_path)
    assert paths.date_str == "2026-11-05"
    assert paths.raw_file == tmp_path / "RAW_LINKS" / "2026-11-05"
    assert paths.weekly_file == tmp_path / "weekly-links" / "2026-11-05-links.md"


def test_validate_raw_content_counts_urls_and_searches():
    url_count, search_count = validate_raw_content(SAMPLE_RAW)
    assert url_count == 2
    assert search_count == 1


def test_validate_raw_content_refuses_empty():
    with pytest.raises(ValueError, match="No URLs"):
        validate_raw_content("just some notes\n\"topic only\"\n")


def test_check_raw_file_writable_refuses_existing(tmp_path: Path):
    raw = tmp_path / "2026-11-05"
    raw.write_text(SAMPLE_RAW, encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        check_raw_file_writable(raw, force=False)


def test_check_raw_file_writable_allows_force(tmp_path: Path):
    raw = tmp_path / "2026-11-05"
    raw.write_text(SAMPLE_RAW, encoding="utf-8")
    check_raw_file_writable(raw, force=True)


def test_check_raw_file_writable_allows_missing(tmp_path: Path):
    check_raw_file_writable(tmp_path / "missing", force=False)
