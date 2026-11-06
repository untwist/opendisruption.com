#!/usr/bin/env python3
"""Weekly news-hour briefs: fetch links, draft rundown and headlines."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote_plus, urlparse, urlunparse

from bs4 import BeautifulSoup

from open_links_in_chrome import parse_category_line

GetBody = Callable[[str], str]

LOGIN_WALL_RE = re.compile(
    r"please log in|sign in to continue|log in to continue|subscribe to read",
    re.I,
)
MIN_READABLE_CHARS = 80


def strip_tracking_params(url: str) -> str:
    """Remove query string and fragment from a URL (X tracking params, etc.)."""
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def is_x_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in {"x.com", "www.x.com", "twitter.com", "www.twitter.com"}


def x_status_id(url: str) -> str | None:
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def fxtwitter_api_url(url: str) -> str:
    """Build api.fxtwitter.com URL for a cleaned X status URL."""
    clean = strip_tracking_params(url)
    parsed = urlparse(clean)
    # path like /openai/status/123
    return f"https://api.fxtwitter.com{parsed.path}"


@dataclass(frozen=True)
class BriefItem:
    """One ordered item from RAW_LINKS for briefing."""

    section: str | None
    url: str
    kind: str  # "url" | "search"
    note: str | None = None


@dataclass(frozen=True)
class SourcePack:
    """Fetched content for one brief item."""

    url: str
    section: str | None
    status: str  # "ok" | "unread" | "search" | "thin"
    text: str = ""
    author: str | None = None
    quoted_text: str | None = None
    note: str | None = None
    thin_media: bool = False
    title: str | None = None


def _unread_pack(item: BriefItem) -> SourcePack:
    return SourcePack(
        url=item.url,
        section=item.section,
        status="unread",
        text="",
        note=item.note,
    )


def _parse_fxtwitter_body(item: BriefItem, body: str) -> SourcePack:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return _unread_pack(item)

    tweet = data.get("tweet") or data
    text = (tweet.get("text") or "").strip()
    if not text:
        return _unread_pack(item)

    author_obj = tweet.get("author") or {}
    author = (author_obj.get("name") or author_obj.get("screen_name") or "").strip() or None

    quoted = tweet.get("quote") or tweet.get("quoted")
    quoted_text = None
    if isinstance(quoted, dict):
        quoted_text = (quoted.get("text") or "").strip() or None

    media = tweet.get("media") or {}
    photos = media.get("photos") or []
    videos = media.get("videos") or []
    thin_media = bool(photos or videos) and len(text) < 120

    status = "thin" if thin_media else "ok"
    return SourcePack(
        url=item.url,
        section=item.section,
        status=status,
        text=text,
        author=author,
        quoted_text=quoted_text,
        note=item.note,
        thin_media=thin_media,
    )


def _extract_article_text(html: str) -> tuple[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title = None
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title and soup.title.string:
        title = soup.title.string.strip()

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    parts: list[str] = []
    article = soup.find("article")
    root = article if article else soup.body or soup
    for node in root.find_all(["h1", "h2", "p"]):
        text = node.get_text(" ", strip=True)
        if text:
            parts.append(text)
    if not parts:
        parts.append(root.get_text(" ", strip=True))

    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        desc = og_desc["content"].strip()
        if desc and desc not in parts:
            parts.insert(1 if parts else 0, desc)

    joined = "\n".join(parts).strip()
    return joined, title


def _parse_article_body(item: BriefItem, body: str) -> SourcePack:
    if not body or not body.strip():
        return _unread_pack(item)

    text, title = _extract_article_text(body)
    if not text or len(text) < MIN_READABLE_CHARS or LOGIN_WALL_RE.search(text):
        return _unread_pack(item)

    return SourcePack(
        url=item.url,
        section=item.section,
        status="ok",
        text=text,
        note=item.note,
        title=title,
    )


@dataclass(frozen=True)
class BriefResult:
    """Spoken headline and script for one source pack."""

    url: str
    section: str | None
    status: str
    headline: str
    script: str
    note: str | None = None
    id: str = ""


ModelFn = Callable[[SourcePack], dict[str, str]]

THIN_REQUIRED_PHRASE = "not watched"


def _search_headline(url: str) -> str:
    query = parse_qs(urlparse(url).query).get("q", [""])[0]
    term = unquote_plus(query).strip() or "topic"
    return f"Search: {term}"


def _stable_item_id(url: str, index: int) -> str:
    status = x_status_id(url)
    if status:
        return f"x-{status}"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", urlparse(url).path.strip("/"))[:40].strip("-")
    return f"item-{index}-{slug or 'link'}"


def brief_from_pack(
    pack: SourcePack,
    *,
    model: ModelFn,
    index: int = 0,
) -> BriefResult:
    """
    Produce a headline and spoken script from a source pack.

    Unread and search packs never call the model. Thin packs require the
    script to say the clip was not watched.
    """
    item_id = _stable_item_id(pack.url, index)

    if pack.status == "unread":
        return BriefResult(
            url=pack.url,
            section=pack.section,
            status="unread",
            headline="",
            script="",
            note=pack.note,
            id=item_id,
        )

    if pack.status == "search":
        return BriefResult(
            url=pack.url,
            section=pack.section,
            status="search",
            headline=_search_headline(pack.url),
            script="",
            note=pack.note,
            id=item_id,
        )

    raw = model(pack)
    headline = (raw.get("headline") or "").strip()
    script = (raw.get("script") or "").strip()
    status = (raw.get("status") or pack.status).strip()

    if pack.thin_media or pack.status == "thin":
        status = "thin"
        if THIN_REQUIRED_PHRASE not in script.lower():
            script = (script + " The clip was not watched for this rundown.").strip()

    return BriefResult(
        url=pack.url,
        section=pack.section,
        status=status,
        headline=headline,
        script=script,
        note=pack.note,
        id=item_id,
    )


def fetch_source_pack(
    item: BriefItem,
    *,
    get_body: GetBody,
    cache: dict[str, SourcePack] | None = None,
) -> SourcePack:
    """
    Build a SourcePack for one item.

    get_body is the network boundary: tests pass fixtures; production passes HTTP.
    Search items never call get_body. Empty or blocked bodies become unread.
    When cache has a hit for this URL, the network is skipped.
    """
    if item.kind == "search":
        return SourcePack(
            url=item.url,
            section=item.section,
            status="search",
            text="",
            note=item.note,
        )

    if cache:
        hit = cache.get(item.url) or cache.get(strip_tracking_params(item.url))
        if hit is not None:
            return SourcePack(
                url=item.url,
                section=item.section,
                status=hit.status,
                text=hit.text,
                author=hit.author,
                quoted_text=hit.quoted_text,
                note=item.note if item.note is not None else hit.note,
                thin_media=hit.thin_media,
                title=hit.title,
            )

    try:
        if is_x_url(item.url):
            fetch_url = fxtwitter_api_url(item.url)
            body = get_body(fetch_url)
            return _parse_fxtwitter_body(item, body)
        body = get_body(strip_tracking_params(item.url))
        return _parse_article_body(item, body)
    except Exception:
        return _unread_pack(item)


def parse_brief_items(content: str) -> list[BriefItem]:
    """
    Parse RAW_LINKS into ordered brief items.

    Keeps curator notes and attaches a note before a URL to that URL.
    A note at the end of a section attaches to the previous URL.
    Duplicate URLs are kept once. Quoted lines are search items.
    """
    lines = content.splitlines()
    items: list[BriefItem] = []
    seen_urls: set[str] = set()
    current_section: str | None = None
    pending_note: str | None = None
    last_item_index: int | None = None

    def flush_pending_note_to_previous() -> None:
        nonlocal pending_note, last_item_index
        if pending_note is None or last_item_index is None:
            pending_note = None
            return
        prev = items[last_item_index]
        if prev.note is None:
            items[last_item_index] = BriefItem(
                section=prev.section,
                url=prev.url,
                kind=prev.kind,
                note=pending_note,
            )
        pending_note = None

    for line in lines:
        stripped = line.strip()

        category_name, is_closing = parse_category_line(stripped)
        if category_name is not None:
            if is_closing:
                if current_section is not None:
                    flush_pending_note_to_previous()
                    current_section = None
                    last_item_index = None
                continue
            flush_pending_note_to_previous()
            current_section = category_name
            last_item_index = None
            continue

        if not stripped or stripped.lower() in ("xx", "---"):
            continue

        if stripped.startswith('"') and stripped.endswith('"') and len(stripped) > 2:
            term = stripped[1:-1].strip()
            if term:
                url = f"https://www.google.com/search?q={quote(term)}"
                note = pending_note
                pending_note = None
                items.append(
                    BriefItem(
                        section=current_section,
                        url=url,
                        kind="search",
                        note=note,
                    )
                )
                last_item_index = len(items) - 1
            continue

        if stripped.startswith("http://") or stripped.startswith("https://"):
            url = stripped
            if url in seen_urls:
                pending_note = None
                continue
            seen_urls.add(url)
            note = pending_note
            pending_note = None
            items.append(
                BriefItem(
                    section=current_section,
                    url=url,
                    kind="url",
                    note=note,
                )
            )
            last_item_index = len(items) - 1
            continue

        # Curator note line
        pending_note = stripped

    flush_pending_note_to_previous()
    return items


@dataclass(frozen=True)
class RundownRecord:
    """One speaker-note record from a rundown markdown file."""

    id: str
    kind: str  # "section" | "link"
    section: str | None
    url: str
    headline: str
    script: str
    status: str


def urls_match_for_presenter(a: str, b: str) -> bool:
    """Match tab URL to rundown URL; X posts compare status ids."""
    if is_x_url(a) and is_x_url(b):
        id_a = x_status_id(a)
        id_b = x_status_id(b)
        return bool(id_a and id_b and id_a == id_b)
    return strip_tracking_params(a) == strip_tracking_params(b)


def render_rundown(briefs: list[BriefResult], *, date_str: str) -> str:
    """Render ordered briefs into presenter-loadable rundown markdown."""
    lines: list[str] = [
        "# Open Disruption — News Hour Rundown",
        f"**Date:** {date_str}",
        "",
        "*Speaker notes for office hours. Not published on the public weekly page.*",
        "",
    ]
    current_section: str | None = None
    for brief in briefs:
        section = brief.section or "OTHER"
        if section != current_section:
            section_id = f"section-{re.sub(r'[^a-zA-Z0-9]+', '-', section).strip('-').lower()}"
            lines.append(f"## [section] {section} {{#{section_id}}}")
            lines.append("")
            current_section = section

        lines.append(f"## [link] {brief.id}")
        lines.append(f"status: {brief.status}")
        lines.append(brief.url)
        lines.append("")
        headline = brief.headline or ("UNREAD" if brief.status == "unread" else brief.id)
        lines.append(f"**{headline}**")
        lines.append("")
        if brief.script:
            lines.append(brief.script)
            lines.append("")
        elif brief.status == "unread":
            lines.append("_UNREAD — no script until this link can be read._")
            lines.append("")
        elif brief.status == "search":
            lines.append("_Search topic — open the Google tab; no spoken script._")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_rundown(markdown: str) -> list[RundownRecord]:
    """Parse rundown markdown back into ordered speaker records."""
    records: list[RundownRecord] = []
    current_section: str | None = None
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        section_match = re.match(r"^## \[section\]\s+(.+?)(?:\s+\{\#[^}]+\})?\s*$", line)
        if section_match:
            name = section_match.group(1).strip()
            # Drop optional trailing {#id} already handled; name is clean
            name = re.sub(r"\s+\{\#[^}]+\}\s*$", "", name).strip()
            current_section = name
            section_id = f"section-{re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()}"
            records.append(
                RundownRecord(
                    id=section_id,
                    kind="section",
                    section=name,
                    url="",
                    headline="",
                    script="",
                    status="section",
                )
            )
            i += 1
            continue

        link_match = re.match(r"^## \[link\]\s+(\S+)\s*$", line)
        if link_match:
            item_id = link_match.group(1)
            status = "ok"
            url = ""
            headline = ""
            script_parts: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                row = lines[i]
                if row.startswith("status:"):
                    status = row.split(":", 1)[1].strip()
                elif row.startswith("http://") or row.startswith("https://"):
                    url = row.strip()
                elif row.startswith("**") and row.endswith("**") and len(row) > 4:
                    headline = row[2:-2].strip()
                elif row.startswith("_") and row.endswith("_"):
                    pass  # placeholder notes for unread/search
                elif row.strip():
                    script_parts.append(row.strip())
                i += 1
            records.append(
                RundownRecord(
                    id=item_id,
                    kind="link",
                    section=current_section,
                    url=url,
                    headline=headline,
                    script=" ".join(script_parts).strip()
                    if len(script_parts) == 1
                    else "\n".join(script_parts).strip(),
                    status=status,
                )
            )
            continue

        i += 1

    return records


def render_headlines_draft(briefs: list[BriefResult], *, date_str: str) -> str:
    """Render proposed one-sentence headlines for the public weekly page."""
    lines = [
        "# Open Disruption — Proposed Headlines",
        f"**Date:** {date_str}",
        "",
        "*Review, then apply with `brief_week.py --apply`. Does not change the live page until applied.*",
        "",
        "## Links from Office Hours",
        "",
    ]
    for brief in briefs:
        if brief.status == "search":
            continue
        label = brief.headline.strip() if brief.headline.strip() else brief.url
        lines.append(
            f'- <a href="{brief.url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        )
    lines.append("")
    return "\n".join(lines)


def write_drafts(
    briefs: list[BriefResult],
    *,
    weekly_dir: Path,
    date_str: str,
) -> tuple[Path, Path]:
    """Write rundown and headlines drafts. Does not touch the public weekly page."""
    weekly_dir.mkdir(parents=True, exist_ok=True)
    rundown_path = weekly_dir / f"{date_str}-rundown.md"
    headlines_path = weekly_dir / f"{date_str}-headlines.md"
    rundown_path.write_text(render_rundown(briefs, date_str=date_str), encoding="utf-8")
    headlines_path.write_text(
        render_headlines_draft(briefs, date_str=date_str), encoding="utf-8"
    )
    return rundown_path, headlines_path


ANCHOR_RE = re.compile(
    r'(<a\s+[^>]*href=")([^"]+)("[^>]*>)(.*?)(</a>)',
    re.I | re.DOTALL,
)
HEADLINE_ANCHOR_RE = re.compile(
    r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.I | re.DOTALL,
)


def parse_headlines_draft(markdown: str) -> dict[str, str]:
    """Map URL -> accepted headline label from a headlines draft file."""
    mapping: dict[str, str] = {}
    for match in HEADLINE_ANCHOR_RE.finditer(markdown):
        url = match.group(1)
        label = match.group(2).strip()
        if label and label != url:
            mapping[url] = label
    return mapping


def apply_headline_labels(weekly_markdown: str, labels: dict[str, str]) -> str:
    """Replace anchor text for matching hrefs; leave URLs unchanged."""

    def replacer(match: re.Match[str]) -> str:
        prefix, href, mid, _old_label, suffix = match.groups()
        new_label = None
        for url, label in labels.items():
            if urls_match_for_presenter(href, url):
                new_label = label
                break
        if new_label is None:
            return match.group(0)
        return f"{prefix}{href}{mid}{new_label}{suffix}"

    return ANCHOR_RE.sub(replacer, weekly_markdown)


def apply_headlines(
    *,
    weekly_dir: Path,
    date_str: str,
    regenerate_html: Callable[[Path], Path],
) -> Path:
    """
    Copy accepted headlines into the public weekly markdown and regenerate HTML.

    Only anchor text changes; href values stay the same.
    """
    weekly_md = weekly_dir / f"{date_str}-links.md"
    headlines_md = weekly_dir / f"{date_str}-headlines.md"
    if not weekly_md.exists():
        raise FileNotFoundError(f"Missing weekly page: {weekly_md}")
    if not headlines_md.exists():
        raise FileNotFoundError(f"Missing headlines draft: {headlines_md}")

    labels = parse_headlines_draft(headlines_md.read_text(encoding="utf-8"))
    updated = apply_headline_labels(weekly_md.read_text(encoding="utf-8"), labels)
    weekly_md.write_text(updated, encoding="utf-8")
    regenerate_html(weekly_md)
    return weekly_md


def rebrief_unread(
    packs: list[SourcePack],
    *,
    read_page: GetBody,
    model: ModelFn,
) -> tuple[list[SourcePack], list[BriefResult]]:
    """
    Browser fallback: re-fetch only unread packs, then brief those that become readable.

    Already-ok and search packs are left alone. Returns updated packs and only
    the new briefs produced for previously unread items.
    """
    updated: list[SourcePack] = []
    new_briefs: list[BriefResult] = []

    for index, pack in enumerate(packs):
        if pack.status != "unread":
            updated.append(pack)
            continue

        item = BriefItem(
            section=pack.section,
            url=pack.url,
            kind="url",
            note=pack.note,
        )
        try:
            body = read_page(pack.url)
        except Exception:
            updated.append(pack)
            continue

        refreshed = _parse_article_body(item, body)
        updated.append(refreshed)
        # Briefing happens in build_week_briefs after packs are finalized so
        # the brief cache can be consulted/invalidated once.

    return updated, new_briefs


def format_unread_browser_prompt(packs: list[SourcePack]) -> str:
    """Human-facing prompt listing unread URLs before an optional browser pass."""
    unread = [p for p in packs if p.status == "unread"]
    lines = [
        f"{len(unread)} unread item(s) after the fetch pass:",
        "",
    ]
    for pack in unread:
        section = pack.section or "OTHER"
        lines.append(f"  [{section}] {pack.url}")
    lines.append("")
    lines.append(
        f"{len(unread)} unread item(s). Process them with a browser? [y/N] "
    )
    return "\n".join(lines)


def decide_browser_pass(
    *,
    unread_count: int,
    force_browser: bool,
    interactive: bool,
    ask: Callable[[str], str],
    prompt_message: str | None = None,
) -> bool:
    """
    Decide whether to run the browser re-fetch for unread items.

    - No unread → False
    - force_browser (--browser) → True without prompting
    - Non-interactive (no TTY) → False unless force_browser
    - Interactive → ask; truthy answers are y/yes (case-insensitive)
    """
    if unread_count <= 0:
        return False
    if force_browser:
        return True
    if not interactive:
        return False
    message = prompt_message or (
        f"{unread_count} unread item(s). Process them with a browser? [y/N] "
    )
    answer = (ask(message) or "").strip().lower()
    return answer in {"y", "yes"}


def default_ask_browser(message: str) -> str:
    """Prompt on stdout/stdin (production CLI)."""
    return input(message)


def stdin_is_interactive() -> bool:
    """True when stdin is a TTY so prompting will not hang CI/pipes."""
    import sys

    return bool(getattr(sys.stdin, "isatty", lambda: False)())


def http_get_body(url: str, *, timeout: int = 20) -> str:
    """Fetch a URL body over HTTP (network boundary for production runs)."""
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response.text


DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _start_playwright():
    """Indirection so tests can stub Playwright without importing the real package."""
    from playwright.sync_api import sync_playwright

    return sync_playwright().start()


class PlaywrightSession:
    """Reusable headless Chromium session for unread / --browser re-fetches."""

    def __init__(self, *, headless: bool = True, timeout_ms: int = 45_000) -> None:
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._pw = None
        self._browser = None

    def open(self) -> None:
        if self._browser is not None:
            return
        self._pw = _start_playwright()
        self._browser = self._pw.chromium.launch(headless=self.headless)

    def get_body(self, url: str) -> str:
        """Navigate to url and return full page HTML for the article parser."""
        self.open()
        assert self._browser is not None
        context = self._browser.new_context(user_agent=DEFAULT_BROWSER_USER_AGENT)
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            # Give client-rendered / soft-paywall shells a moment to settle.
            page.wait_for_timeout(1_500)
            return page.content()
        finally:
            context.close()

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._pw is not None:
            self._pw.stop()
            self._pw = None

    def __enter__(self) -> "PlaywrightSession":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def browser_get_body(
    url: str,
    *,
    session: PlaywrightSession | None = None,
    timeout_ms: int = 45_000,
) -> str:
    """
    Fetch a URL body via Playwright Chromium (for pages that block plain HTTP).

    Pass a PlaywrightSession to reuse one browser across many unread URLs.
    Without a session, opens and closes Chromium for this single call.
    """
    if session is not None:
        return session.get_body(url)
    with PlaywrightSession(timeout_ms=timeout_ms) as owned:
        return owned.get_body(url)


def heuristic_model(pack: SourcePack) -> dict[str, str]:
    """
    Offline brief writer: headline and script drawn only from fetched text.

    Used when BRIEF_WEEK_MODEL=heuristic or --heuristic is passed.
    """
    words = pack.text.split()
    title = (pack.title or "").strip()
    author = (pack.author or "").strip()

    if title:
        headline = title if title.endswith((".", "!", "?")) else title
        if len(headline) > 120:
            headline = headline[:117].rsplit(" ", 1)[0] + "..."
    else:
        snippet = " ".join(words[:16])
        headline = snippet if snippet else pack.url

    lead = f"{author} " if author else ""
    body_bits = " ".join(words[:55]).strip()
    if pack.note:
        body_bits = f"{body_bits} Curator note: {pack.note}."
    script = (
        f"{lead}{body_bits} "
        "That is the concrete detail for this week's AI news hour."
    ).strip()
    if pack.thin_media or pack.status == "thin":
        if THIN_REQUIRED_PHRASE not in script.lower():
            script = f"{script} The clip was not watched for this rundown."

    # Pad or trim toward 45–70 words without inventing facts
    script_words = script.split()
    while len(script_words) < 45 and words:
        # Repeat a short factual close rather than invent claims
        script_words.extend("Worth covering in this week's office hours.".split())
        break
    if len(script_words) < 45:
        script_words.extend(
            ["Worth", "covering", "in", "this", "week's", "office", "hours."]
        )
    # Ensure we hit 45
    fillers = "This item belongs in today's rundown as curated.".split()
    while len(script_words) < 45:
        script_words.append(fillers[(len(script_words)) % len(fillers)])
    script = " ".join(script_words[:70])

    status = "thin" if (pack.thin_media or pack.status == "thin") else "ok"
    return {"status": status, "headline": headline, "script": script}


def _load_env_file() -> None:
    """Load repo-root .env into os.environ without overwriting existing vars."""
    import os

    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def resolve_model(
    *,
    heuristic: bool = False,
    usage: UsageTracker | None = None,
) -> ModelFn:
    """Return a model function, or exit with a clear message if no API key."""
    import os

    _load_env_file()

    if heuristic or os.environ.get("BRIEF_WEEK_MODEL", "").lower() == "heuristic":
        return heuristic_model

    api_key = (
        os.environ.get("BRIEF_WEEK_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
    )
    if not api_key:
        raise SystemExit(
            "Missing API key. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or "
            "BRIEF_WEEK_API_KEY, or pass --heuristic for offline drafts from fetched text."
        )

    if os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        return _make_anthropic_model(api_key, usage=usage)
    return _make_openai_model(api_key, usage=usage)


def _make_openai_model(
    api_key: str, *, usage: UsageTracker | None = None
) -> ModelFn:
    import os

    import requests

    model_name = os.environ.get("BRIEF_WEEK_OPENAI_MODEL", "gpt-4o-mini")
    if usage is not None and usage.model != model_name:
        usage.model = model_name

    def model(pack: SourcePack) -> dict[str, str]:
        prompt = _brief_prompt(pack)
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_name,
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You write spoken AI news-hour briefs. "
                            "Return JSON with keys status, headline, script. "
                            "Script must be 45-70 words. Use only facts in the source."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        if usage is not None:
            u = payload.get("usage") or {}
            usage.add(
                url=pack.url,
                input_tokens=int(u.get("prompt_tokens") or 0),
                output_tokens=int(u.get("completion_tokens") or 0),
                model=model_name,
            )
        content = payload["choices"][0]["message"]["content"]
        return json.loads(content)

    return model


def _make_anthropic_model(
    api_key: str, *, usage: UsageTracker | None = None
) -> ModelFn:
    import os

    import requests

    # Haiku is the default for weekly briefs: enough quality for 10–30s copy,
    # roughly 20× cheaper than Sonnet 5.5 on list pricing.
    model_name = os.environ.get("BRIEF_WEEK_ANTHROPIC_MODEL", "claude-haiku-5-5")
    if usage is not None:
        usage.model = model_name

    def model(pack: SourcePack) -> dict[str, str]:
        prompt = _brief_prompt(pack)
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=anthropic_messages_body(model_name=model_name, prompt=prompt),
            timeout=60,
        )
        if not response.ok:
            detail = (response.text or "").strip()[:500]
            raise RuntimeError(
                f"Anthropic API {response.status_code} for model {model_name!r}: {detail}"
            )
        payload = response.json()
        if usage is not None:
            in_tok, out_tok = extract_anthropic_usage(payload)
            usage.add(
                url=pack.url,
                input_tokens=in_tok,
                output_tokens=out_tok,
                model=model_name,
            )
        content = extract_anthropic_text(payload)
        if not content:
            raise RuntimeError(
                f"Anthropic API returned no text content for model {model_name!r}: "
                f"{json.dumps(payload)[:500]}"
            )
        # Allow fenced JSON
        fence = re.search(r"\{.*\}", content, re.S)
        return json.loads(fence.group(0) if fence else content)

    return model


def extract_anthropic_text(payload: dict) -> str:
    """Pull concatenated text blocks from an Anthropic messages response."""
    blocks = payload.get("content") or []
    text_parts = [
        block.get("text", "")
        for block in blocks
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    return "\n".join(part for part in text_parts if part).strip()


# List prices USD per million tokens (input, output). Under-100k Haiku tier.
MODEL_PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-sonnet-5": (2.0, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
}


def cost_usd_for_usage(
    *, model: str, input_tokens: int, output_tokens: int
) -> float:
    """Estimate USD cost from token counts using known list prices."""
    rates = MODEL_PRICES_PER_MTOK.get(model)
    if rates is None:
        # Unknown model: treat like Haiku so we still surface a number.
        rates = MODEL_PRICES_PER_MTOK["claude-haiku-5-5"]
    in_rate, out_rate = rates
    return input_tokens / 1_000_000 * in_rate + output_tokens / 1_000_000 * out_rate


def extract_anthropic_usage(payload: dict) -> tuple[int, int]:
    """Return (input_tokens, output_tokens) from an Anthropic messages payload."""
    usage = payload.get("usage") or {}
    return int(usage.get("input_tokens") or 0), int(usage.get("output_tokens") or 0)


@dataclass
class UsageTracker:
    """Accumulate per-call token usage and estimated cost for one brief run."""

    model: str
    calls: list[dict] = field(default_factory=list)

    def add(
        self,
        *,
        url: str,
        input_tokens: int,
        output_tokens: int,
        model: str | None = None,
    ) -> None:
        model_name = model or self.model
        self.calls.append(
            {
                "url": url,
                "model": model_name,
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens),
                "cost_usd": cost_usd_for_usage(
                    model=model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                ),
            }
        )

    def summary(self) -> dict:
        input_tokens = sum(c["input_tokens"] for c in self.calls)
        output_tokens = sum(c["output_tokens"] for c in self.calls)
        cost = sum(c["cost_usd"] for c in self.calls)
        return {
            "model": self.model,
            "calls": len(self.calls),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"summary": self.summary(), "calls": self.calls}
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def format_summary_line(self) -> str:
        s = self.summary()
        return (
            f"Usage: {s['calls']} calls, "
            f"{s['input_tokens']:,} in / {s['output_tokens']:,} out tokens, "
            f"est. ${s['cost_usd']:.4f} ({s['model']})"
        )


def usage_log_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / ".cache" / "brief_week" / f"{date_str}-usage.json"


def anthropic_messages_body(*, model_name: str, prompt: str) -> dict:
    """Build Messages API body. Thinking is disabled so max_tokens goes to the JSON brief."""
    return {
        "model": model_name,
        "max_tokens": 400,
        "thinking": {"type": "disabled"},
        "messages": [
            {
                "role": "user",
                "content": (
                    "Return only JSON with keys status, headline, script. "
                    "Script must be 45-70 words. Use only facts in the source.\n\n"
                    + prompt
                ),
            }
        ],
    }


def fetch_cache_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / ".cache" / "brief_week" / f"{date_str}-packs.json"


def brief_cache_path(repo_root: Path, date_str: str) -> Path:
    return repo_root / ".cache" / "brief_week" / f"{date_str}-briefs.json"


def save_fetch_cache(cache_file: Path, packs: list[SourcePack]) -> None:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "url": p.url,
            "section": p.section,
            "status": p.status,
            "text": p.text,
            "author": p.author,
            "quoted_text": p.quoted_text,
            "note": p.note,
            "thin_media": p.thin_media,
            "title": p.title,
        }
        for p in packs
    ]
    cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_fetch_cache(cache_file: Path) -> dict[str, SourcePack]:
    if not cache_file.is_file():
        return {}
    raw = json.loads(cache_file.read_text(encoding="utf-8"))
    out: dict[str, SourcePack] = {}
    for row in raw:
        pack = SourcePack(
            url=row["url"],
            section=row.get("section"),
            status=row["status"],
            text=row.get("text") or "",
            author=row.get("author"),
            quoted_text=row.get("quoted_text"),
            note=row.get("note"),
            thin_media=bool(row.get("thin_media")),
            title=row.get("title"),
        )
        out[strip_tracking_params(pack.url)] = pack
        out[pack.url] = pack
    return out


def _brief_to_cache_row(brief: BriefResult) -> dict:
    return {
        "id": brief.id,
        "url": brief.url,
        "section": brief.section,
        "status": brief.status,
        "headline": brief.headline,
        "script": brief.script,
        "note": brief.note,
    }


def save_brief_cache(cache_file: Path, briefs: list[BriefResult]) -> None:
    """Persist briefs, merging by URL so a partial run cannot wipe older entries."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    by_key: dict[str, dict] = {}
    if cache_file.is_file():
        try:
            existing = json.loads(cache_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = []
        if isinstance(existing, list):
            for row in existing:
                url = row.get("url") or ""
                if url:
                    by_key[strip_tracking_params(url)] = row
    for brief in briefs:
        by_key[strip_tracking_params(brief.url)] = _brief_to_cache_row(brief)
    payload = list(by_key.values())
    cache_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_brief_cache(cache_file: Path) -> dict[str, BriefResult]:
    if not cache_file.is_file():
        return {}
    raw = json.loads(cache_file.read_text(encoding="utf-8"))
    out: dict[str, BriefResult] = {}
    for row in raw:
        brief = BriefResult(
            id=row.get("id") or "",
            url=row["url"],
            section=row.get("section"),
            status=row.get("status") or "ok",
            headline=row.get("headline") or "",
            script=row.get("script") or "",
            note=row.get("note"),
        )
        out[strip_tracking_params(brief.url)] = brief
        out[brief.url] = brief
    return out


def briefs_from_rundown(markdown: str) -> list[BriefResult]:
    """Rebuild brief-cache entries from an existing rundown (recovery / seed)."""
    briefs: list[BriefResult] = []
    for record in parse_rundown(markdown):
        if record.kind != "link" or not record.url:
            continue
        briefs.append(
            BriefResult(
                id=record.id,
                url=record.url,
                section=record.section,
                status=record.status,
                headline=record.headline,
                script=record.script,
            )
        )
    return briefs


def lookup_brief_cache(
    cache: dict[str, BriefResult], url: str
) -> BriefResult | None:
    return cache.get(url) or cache.get(strip_tracking_params(url))


def _brief_prompt(pack: SourcePack) -> str:
    parts = [
        f"URL: {pack.url}",
        f"Section: {pack.section or 'OTHER'}",
        f"Fetch status: {pack.status}",
    ]
    if pack.author:
        parts.append(f"Author: {pack.author}")
    if pack.title:
        parts.append(f"Title: {pack.title}")
    if pack.note:
        parts.append(f"Curator note: {pack.note}")
    if pack.quoted_text:
        parts.append(f"Quoted text: {pack.quoted_text}")
    if pack.thin_media:
        parts.append(
            "This is a thin media post. Script must say the clip was not watched."
        )
    parts.append("Source text:")
    # Cap source length to keep weekly cost low; X posts are short anyway.
    parts.append(pack.text[:3000])
    return "\n".join(parts)


def build_week_briefs(
    raw_content: str,
    *,
    get_body: GetBody,
    model: ModelFn,
    browser: bool = False,
    read_page: GetBody | None = None,
    log: Callable[[str], None] | None = None,
    cache: dict[str, SourcePack] | None = None,
    cache_file: Path | None = None,
    brief_cache_file: Path | None = None,
    refresh_fetch: bool = False,
    refresh_briefs: bool = False,
    ask_browser: Callable[[str], str] | None = None,
    interactive: bool | None = None,
    seed_briefs: list[BriefResult] | None = None,
) -> tuple[list[SourcePack], list[BriefResult]]:
    """Parse RAW_LINKS, fetch, brief; optionally re-brief unread via browser reader."""
    emit = log or (lambda _msg: None)
    items = parse_brief_items(raw_content)
    total = len(items)
    emit(f"Parsed {total} items from RAW_LINKS")

    active_cache: dict[str, SourcePack] = {}
    if not refresh_fetch:
        if cache is not None:
            active_cache = cache
        elif cache_file is not None:
            active_cache = load_fetch_cache(cache_file)
            if active_cache:
                emit(f"Loaded fetch cache: {cache_file} ({len(active_cache)} keys)")

    packs: list[SourcePack] = []
    for index, item in enumerate(items, start=1):
        cached_hit = (
            not refresh_fetch
            and item.kind != "search"
            and (
                item.url in active_cache
                or strip_tracking_params(item.url) in active_cache
            )
        )
        label = "CACHE" if cached_hit else "FETCH"
        emit(f"[{index}/{total}] {label} {item.kind} {item.url}")
        pack = fetch_source_pack(
            item,
            get_body=get_body,
            cache=None if refresh_fetch else active_cache,
        )
        note = f" note={pack.note!r}" if pack.note else ""
        emit(f"[{index}/{total}] {label} → {pack.status}{note}")
        packs.append(pack)
        # Persist after each item so a mid-run failure still keeps completed fetches.
        if cache_file is not None:
            save_fetch_cache(cache_file, packs)

    if cache_file is not None:
        emit(f"Saved fetch cache: {cache_file}")

    unread_n = sum(1 for p in packs if p.status == "unread")
    is_interactive = (
        stdin_is_interactive() if interactive is None else interactive
    )
    ask = ask_browser or default_ask_browser
    prompt = format_unread_browser_prompt(packs) if unread_n else ""
    if decide_browser_pass(
        unread_count=unread_n,
        force_browser=browser,
        interactive=is_interactive,
        ask=ask,
        prompt_message=prompt,
    ):
        emit(f"Browser pass for {unread_n} unread item(s)")
        reader = read_page or get_body
        packs, _ = rebrief_unread(packs, read_page=reader, model=model)
        # Persist any rescued fetches for later runs.
        if cache_file is not None:
            save_fetch_cache(cache_file, packs)
        # rebrief_unread returns only new briefs; rebuild all from final packs

    brief_cache: dict[str, BriefResult] = {}
    if not refresh_briefs and brief_cache_file is not None:
        brief_cache = load_brief_cache(brief_cache_file)
        if brief_cache:
            emit(
                f"Loaded brief cache: {brief_cache_file} ({len(brief_cache)} keys)"
            )
        elif seed_briefs:
            for seeded in seed_briefs:
                brief_cache[strip_tracking_params(seeded.url)] = seeded
                brief_cache[seeded.url] = seeded
            save_brief_cache(brief_cache_file, seed_briefs)
            emit(
                f"Seeded brief cache from rundown: {brief_cache_file} "
                f"({len(seed_briefs)} entries)"
            )

    briefs: list[BriefResult] = []
    for index, pack in enumerate(packs):
        n = index + 1
        cached_brief = (
            None
            if refresh_briefs
            else lookup_brief_cache(brief_cache, pack.url)
        )
        # After a browser rescue, pack may be ok while cache still holds UNREAD.
        if (
            cached_brief is not None
            and cached_brief.status in {"unread", "search"}
            and pack.status in {"ok", "thin"}
        ):
            cached_brief = None
        if cached_brief is not None:
            emit(f"[{n}/{total}] BRIEF CACHE {pack.url}")
            brief = BriefResult(
                id=cached_brief.id or _stable_item_id(pack.url, index),
                url=pack.url,
                section=pack.section,
                status=cached_brief.status,
                headline=cached_brief.headline,
                script=cached_brief.script,
                note=pack.note if pack.note is not None else cached_brief.note,
            )
            emit(
                f"[{n}/{total}] BRIEF CACHE → {brief.status}: "
                f"{(brief.headline or brief.status)[:90]}"
            )
        else:
            if pack.status in {"unread", "search"}:
                emit(f"[{n}/{total}] BRIEF skip ({pack.status}) {pack.url}")
            else:
                emit(f"[{n}/{total}] BRIEF {pack.url}")
            brief = brief_from_pack(pack, model=model, index=index)
            if brief.headline:
                emit(f"[{n}/{total}] BRIEF → {brief.status}: {brief.headline[:90]}")
            else:
                emit(f"[{n}/{total}] BRIEF → {brief.status}")
        briefs.append(brief)
        if brief_cache_file is not None:
            save_brief_cache(brief_cache_file, briefs)

    if brief_cache_file is not None:
        emit(f"Saved brief cache: {brief_cache_file}")

    return packs, briefs


def default_regenerate_html(md_path: Path) -> Path:
    from markdown_to_html import convert_markdown_to_html

    return convert_markdown_to_html(md_path)


def main(argv: list[str] | None = None) -> int:
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser(
        description="Draft news-hour rundown and headline files from RAW_LINKS."
    )
    parser.add_argument("--date", help="YYYY-MM-DD (default: today)")
    parser.add_argument(
        "--input",
        type=Path,
        help="RAW_LINKS file (default: RAW_LINKS/<date>)",
    )
    parser.add_argument(
        "--weekly-dir",
        type=Path,
        default=None,
        help="weekly-links directory (default: repo weekly-links/)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply headlines draft to the public weekly page and regenerate HTML",
    )
    parser.add_argument(
        "--browser",
        action="store_true",
        help=(
            "Skip the unread prompt and re-fetch unread items with Playwright "
            "Chromium before briefing (default: ask interactively when unread)"
        ),
    )
    parser.add_argument(
        "--heuristic",
        action="store_true",
        help="Draft briefs from fetched text without an LLM API key",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N items (for smoke tests)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print per-item fetch and brief progress",
    )
    parser.add_argument(
        "--refresh-fetch",
        action="store_true",
        help="Ignore fetch cache and re-download every URL",
    )
    parser.add_argument(
        "--refresh-briefs",
        action="store_true",
        help="Ignore brief cache and re-call the model for every readable item",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    weekly_dir = args.weekly_dir or (repo_root / "weekly-links")
    date_str = args.date or date.today().strftime("%Y-%m-%d")
    log = print if args.verbose else None
    cache_file = fetch_cache_path(repo_root, date_str)
    briefs_cache_file = brief_cache_path(repo_root, date_str)
    usage_file = usage_log_path(repo_root, date_str)

    if args.apply:
        apply_headlines(
            weekly_dir=weekly_dir,
            date_str=date_str,
            regenerate_html=default_regenerate_html,
        )
        print(f"Applied headlines for {date_str}")
        return 0

    raw_path = args.input or (repo_root / "RAW_LINKS" / date_str)
    if not raw_path.exists():
        raise SystemExit(f"RAW_LINKS file not found: {raw_path}")

    import os

    _load_env_file()
    model_label = (
        "heuristic"
        if args.heuristic or os.environ.get("BRIEF_WEEK_MODEL", "").lower() == "heuristic"
        else os.environ.get("BRIEF_WEEK_ANTHROPIC_MODEL")
        or (
            "claude-haiku-5-5"
            if os.environ.get("ANTHROPIC_API_KEY")
            else os.environ.get("BRIEF_WEEK_OPENAI_MODEL", "gpt-4o-mini")
        )
    )
    usage = None if args.heuristic else UsageTracker(model=model_label)
    model = resolve_model(heuristic=args.heuristic, usage=usage)
    if args.verbose:
        print(f"Date: {date_str}")
        print(f"RAW_LINKS: {raw_path}")
        print(f"Model: {model_label}")

    raw_content = raw_path.read_text(encoding="utf-8")
    items = parse_brief_items(raw_content)
    seed_briefs: list[BriefResult] | None = None
    rundown_seed_path = weekly_dir / f"{date_str}-rundown.md"
    if not args.refresh_briefs and rundown_seed_path.is_file():
        from_rundown = briefs_from_rundown(
            rundown_seed_path.read_text(encoding="utf-8")
        )
        cached = load_brief_cache(briefs_cache_file)
        unique_cached = {strip_tracking_params(b.url) for b in cached.values()}
        if from_rundown and len(unique_cached) < len(from_rundown):
            # Empty or mid-run-wiped cache: restore from the existing rundown.
            save_brief_cache(briefs_cache_file, from_rundown)
            if args.verbose:
                print(
                    f"Seeded brief cache from {rundown_seed_path.name} "
                    f"({len(unique_cached)} → {len(from_rundown)} entries)"
                )

    if args.limit is not None:
        # Truncate by rewriting a minimal RAW_LINKS stream for the shared pipeline
        limited_lines: list[str] = []
        kept = 0
        current_section: str | None = None
        for item in items[: args.limit]:
            if item.section != current_section:
                limited_lines.append(f"<{item.section or 'OTHER'}>")
                current_section = item.section
            if item.note:
                limited_lines.append(item.note)
            if item.kind == "search":
                term = parse_qs(urlparse(item.url).query).get("q", [""])[0]
                limited_lines.append(f'"{unquote_plus(term)}"')
            else:
                limited_lines.append(item.url)
            kept += 1
        raw_for_build = "\n".join(limited_lines) + "\n"
        if args.verbose:
            print(f"Limit: processing first {kept} item(s)")
    else:
        raw_for_build = raw_content

    # Playwright is only used for the unread re-fetch pass (prompt or --browser).
    with PlaywrightSession() as browser_session:
        packs, briefs = build_week_briefs(
            raw_for_build,
            get_body=http_get_body,
            model=model,
            browser=args.browser,
            read_page=browser_session.get_body,
            log=log,
            cache_file=cache_file,
            brief_cache_file=briefs_cache_file,
            refresh_fetch=args.refresh_fetch,
            refresh_briefs=args.refresh_briefs,
            seed_briefs=seed_briefs,
        )

    rundown_path, headlines_path = write_drafts(
        briefs, weekly_dir=weekly_dir, date_str=date_str
    )
    unread = sum(1 for p in packs if p.status == "unread")
    ok = sum(1 for p in packs if p.status in {"ok", "thin"})
    print(f"Wrote {rundown_path}")
    print(f"Wrote {headlines_path}")
    print(f"Items: {len(packs)} (readable={ok}, unread={unread})")
    if usage is not None and usage.calls:
        usage.save(usage_file)
        print(usage.format_summary_line())
        print(f"Wrote usage log: {usage_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
