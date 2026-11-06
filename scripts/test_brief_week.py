#!/usr/bin/env python3
"""Red-green tests for weekly news-hour briefs (no live network or model)."""

from __future__ import annotations

import json
from pathlib import Path

from brief_week import (
    BriefItem,
    BriefResult,
    SourcePack,
    apply_headlines,
    brief_from_pack,
    fetch_source_pack,
    parse_brief_items,
    parse_rundown,
    rebrief_unread,
    render_headlines_draft,
    render_rundown,
    strip_tracking_params,
    urls_match_for_presenter,
    write_drafts,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "brief_week"


def test_parse_keeps_section_order_and_attaches_note_before_url():
    content = """
<HEADLINES>
https://example.com/one

Dory looping model
https://example.com/dory

<GRAPHICS>
https://example.com/art
"""
    items = parse_brief_items(content)
    assert [item.url for item in items] == [
        "https://example.com/one",
        "https://example.com/dory",
        "https://example.com/art",
    ]
    assert [item.section for item in items] == ["HEADLINES", "HEADLINES", "GRAPHICS"]
    assert items[0].note is None
    assert items[1].note == "Dory looping model"
    assert items[1].kind == "url"
    assert items[2].note is None


def test_parse_attaches_trailing_section_note_to_previous_url():
    content = """
<HEADLINES>
https://example.com/one
follow up thought
</HEADLINES>
"""
    items = parse_brief_items(content)
    assert len(items) == 1
    assert items[0].url == "https://example.com/one"
    assert items[0].note == "follow up thought"


def test_parse_quoted_line_is_search_item():
    content = """
<LLMs>
"Qwen3 max thinking"
https://example.com/model
"""
    items = parse_brief_items(content)
    assert items[0].kind == "search"
    assert "Qwen3" in items[0].url
    assert items[1].kind == "url"
    assert items[1].url == "https://example.com/model"


def test_parse_keeps_duplicate_url_once():
    content = """
<HEADLINES>
https://example.com/one
https://example.com/one
https://example.com/two
"""
    items = parse_brief_items(content)
    assert [item.url for item in items] == [
        "https://example.com/one",
        "https://example.com/two",
    ]


def test_strip_tracking_params_from_x_url():
    dirty = (
        "https://x.com/openai/status/2118390190246879554"
        "?a=5jW9Ry9s2aJaMFOKxJ4&s=46"
    )
    assert strip_tracking_params(dirty) == (
        "https://x.com/openai/status/2118390190246879554"
    )


def test_fetch_source_pack_from_fxtwitter_json():
    body = (FIXTURES / "fxtwitter_sample.json").read_text(encoding="utf-8")
    item = BriefItem(
        section="HEADLINES",
        url="https://x.com/openai/status/2118390190246879554?s=20",
        kind="url",
        note=None,
    )

    def get_body(url: str) -> str:
        assert "2118390190246879554" in url
        assert "?" not in url.split("status/")[-1] or url.endswith(
            "2118390190246879554"
        )
        return body

    pack = fetch_source_pack(item, get_body=get_body)
    assert pack.status == "ok"
    assert pack.author == "OpenAI"
    assert "GPT-6 Cyber" in pack.text
    assert "Earlier work on Cyber" in (pack.quoted_text or "")
    assert pack.thin_media is False


def test_fetch_source_pack_from_article_html():
    body = (FIXTURES / "article_sample.html").read_text(encoding="utf-8")
    item = BriefItem(
        section="HEADLINES",
        url="https://fortune.com/2026/11/05/tech-stocks-selloff/",
        kind="url",
    )

    pack = fetch_source_pack(item, get_body=lambda url: body)
    assert pack.status == "ok"
    assert "biggest selloff" in pack.text.lower()
    assert "datacenter" in pack.text.lower()


def test_fetch_empty_or_blocked_body_is_unread():
    body = (FIXTURES / "empty_body.html").read_text(encoding="utf-8")
    item = BriefItem(
        section="HEADLINES",
        url="https://example.com/paywall",
        kind="url",
    )
    pack = fetch_source_pack(item, get_body=lambda url: body)
    assert pack.status == "unread"
    assert pack.text == ""


def test_fetch_search_item_is_search_without_get_body():
    calls: list[str] = []
    item = BriefItem(
        section="LLMs",
        url="https://www.google.com/search?q=Qwen3",
        kind="search",
    )

    def get_body(url: str) -> str:
        calls.append(url)
        return "should not be called"

    pack = fetch_source_pack(item, get_body=get_body)
    assert pack.status == "search"
    assert calls == []


SAMPLE_SCRIPT = (
    "Fortune reports tech stocks are seeing their biggest selloff since Covid, "
    "as investors question returns on AI datacenter buildouts. Chipmakers and "
    "cloud providers led the decline after earnings raised doubts about "
    "infrastructure spend across the sector. This is the market story shaping "
    "this week's AI news hour for the office."
)


def test_brief_from_readable_pack_uses_model_output():
    pack = SourcePack(
        url="https://fortune.com/example",
        section="HEADLINES",
        status="ok",
        text="Investors see premature end to AI datacenter boom.",
        title="Tech stocks suffer biggest selloff since Covid",
    )
    calls: list[SourcePack] = []

    def model(source: SourcePack) -> dict[str, str]:
        calls.append(source)
        return {
            "status": "ok",
            "headline": "Tech stocks suffer biggest selloff since Covid on AI datacenter doubts",
            "script": SAMPLE_SCRIPT,
        }

    brief = brief_from_pack(pack, model=model)
    assert len(calls) == 1
    assert brief.status == "ok"
    assert (
        brief.headline
        == "Tech stocks suffer biggest selloff since Covid on AI datacenter doubts"
    )
    word_count = len(brief.script.split())
    assert 45 <= word_count <= 70
    assert "Fortune" in brief.script


def test_brief_unread_never_calls_model_even_if_stub_would_invent():
    pack = SourcePack(
        url="https://example.com/paywall",
        section="HEADLINES",
        status="unread",
        text="",
    )
    calls: list[SourcePack] = []

    def model(source: SourcePack) -> dict[str, str]:
        calls.append(source)
        return {
            "status": "ok",
            "headline": "Invented headline",
            "script": SAMPLE_SCRIPT,
        }

    brief = brief_from_pack(pack, model=model)
    assert calls == []
    assert brief.status == "unread"
    assert brief.script == ""
    assert brief.headline == ""


def test_brief_search_never_calls_model():
    pack = SourcePack(
        url="https://www.google.com/search?q=Qwen3",
        section="LLMs",
        status="search",
    )
    calls: list[SourcePack] = []

    def model(source: SourcePack) -> dict[str, str]:
        calls.append(source)
        return {"status": "ok", "headline": "Nope", "script": SAMPLE_SCRIPT}

    brief = brief_from_pack(pack, model=model)
    assert calls == []
    assert brief.status == "search"
    assert brief.script == ""
    assert brief.headline == "Search: Qwen3"


def test_brief_thin_media_requires_clip_not_watched_phrase():
    pack = SourcePack(
        url="https://x.com/user/status/1",
        section="GRAPHICS",
        status="thin",
        text="One car. Five realities.",
        author="@user",
        thin_media=True,
    )

    def model(source: SourcePack) -> dict[str, str]:
        return {
            "status": "thin",
            "headline": "A video post claims one car across five realities",
            "script": (
                "A creator posted a clip claiming one car moves across five "
                "realities with no visible cuts. The caption is short and the "
                "clip itself was not watched for this rundown, so we are "
                "reporting only what the post says on screen. Still worth a "
                "look in the Graphics section of this week's hour."
            ),
        }

    brief = brief_from_pack(pack, model=model)
    assert brief.status == "thin"
    assert "not watched" in brief.script.lower()


def _sample_briefs() -> list[BriefResult]:
    return [
        BriefResult(
            id="x-111",
            url="https://x.com/openai/status/111?s=20",
            section="HEADLINES",
            status="ok",
            headline="OpenAI announces GPT-6 Cyber for security research",
            script=SAMPLE_SCRIPT,
        ),
        BriefResult(
            id="item-1-fortune",
            url="https://fortune.com/selloff",
            section="HEADLINES",
            status="unread",
            headline="",
            script="",
        ),
        BriefResult(
            id="item-2-art",
            url="https://example.com/art",
            section="GRAPHICS",
            status="ok",
            headline="A new generative video model ships today",
            script=SAMPLE_SCRIPT,
        ),
    ]


def test_render_and_parse_rundown_round_trips_speaker_fields():
    briefs = _sample_briefs()
    markdown = render_rundown(briefs, date_str="2026-11-05")
    records = parse_rundown(markdown)

    kinds = [r.kind for r in records]
    assert kinds[0] == "section"
    assert records[0].section == "HEADLINES"
    assert records[1].kind == "link"
    assert records[1].id == "x-111"
    assert records[1].url == "https://x.com/openai/status/111?s=20"
    assert records[1].headline == "OpenAI announces GPT-6 Cyber for security research"
    assert records[1].script == SAMPLE_SCRIPT
    assert records[1].status == "ok"

    unread = next(r for r in records if r.id == "item-1-fortune")
    assert unread.status == "unread"
    assert unread.script == ""

    # Section cue before GRAPHICS
    graphics_cue = next(
        r for r in records if r.kind == "section" and r.section == "GRAPHICS"
    )
    assert graphics_cue is not None


def test_parse_rundown_keeps_hand_edited_script():
    briefs = _sample_briefs()[:1]
    markdown = render_rundown(briefs, date_str="2026-11-05")
    edited = markdown.replace(SAMPLE_SCRIPT, "Hand edited speaker note for air.")
    records = parse_rundown(edited)
    link = next(r for r in records if r.kind == "link")
    assert link.script == "Hand edited speaker note for air."


def test_x_urls_match_on_status_id_ignoring_tracking():
    assert urls_match_for_presenter(
        "https://x.com/openai/status/111?s=20",
        "https://x.com/openai/status/111?a=abc",
    )
    assert not urls_match_for_presenter(
        "https://x.com/openai/status/111",
        "https://x.com/openai/status/222",
    )


def test_write_drafts_leaves_public_weekly_page_untouched(tmp_path: Path):
    weekly_dir = tmp_path / "weekly-links"
    weekly_dir.mkdir()
    public = weekly_dir / "2026-11-05-links.md"
    public.write_text("# public unchanged\n", encoding="utf-8")
    public_html = weekly_dir / "2026-11-05-links.html"
    public_html.write_text("<html>unchanged</html>", encoding="utf-8")
    before_md = public.read_text(encoding="utf-8")
    before_html = public_html.read_text(encoding="utf-8")

    briefs = _sample_briefs()
    write_drafts(briefs, weekly_dir=weekly_dir, date_str="2026-11-05")

    assert (weekly_dir / "2026-11-05-rundown.md").exists()
    headlines = (weekly_dir / "2026-11-05-headlines.md").read_text(encoding="utf-8")
    assert "OpenAI announces GPT-6 Cyber" in headlines
    assert public.read_text(encoding="utf-8") == before_md
    assert public_html.read_text(encoding="utf-8") == before_html


def test_render_headlines_draft_uses_one_sentence_anchors():
    briefs = _sample_briefs()
    text = render_headlines_draft(briefs, date_str="2026-11-05")
    assert "OpenAI announces GPT-6 Cyber for security research" in text
    assert "https://x.com/openai/status/111?s=20" in text
    # unread keeps empty or placeholder — still listed with URL
    assert "https://fortune.com/selloff" in text


def test_apply_headlines_replaces_only_anchor_text_and_regenerates_html(tmp_path: Path):
    weekly_dir = tmp_path / "weekly-links"
    weekly_dir.mkdir()
    date_str = "2026-11-05"
    weekly_md = weekly_dir / f"{date_str}-links.md"
    weekly_md.write_text(
        """# Weekly

## Links from Office Hours

- <a href="https://x.com/openai/status/111?s=20" target="_blank" rel="noopener noreferrer">@openai — Introducing GPT...</a>
- <a href="https://fortune.com/selloff" target="_blank" rel="noopener noreferrer">Fortune: Old Title</a>
""",
        encoding="utf-8",
    )
    headlines = weekly_dir / f"{date_str}-headlines.md"
    headlines.write_text(
        render_headlines_draft(
            [
                BriefResult(
                    id="x-111",
                    url="https://x.com/openai/status/111?s=20",
                    section="HEADLINES",
                    status="ok",
                    headline="OpenAI announces GPT-6 Cyber for security research",
                    script=SAMPLE_SCRIPT,
                ),
                BriefResult(
                    id="item-fortune",
                    url="https://fortune.com/selloff",
                    section="HEADLINES",
                    status="ok",
                    headline="Tech stocks suffer biggest selloff since Covid",
                    script=SAMPLE_SCRIPT,
                ),
            ],
            date_str=date_str,
        ),
        encoding="utf-8",
    )

    html_calls: list[Path] = []

    def regenerate(md_path: Path) -> Path:
        html_calls.append(md_path)
        out = md_path.with_suffix(".html")
        out.write_text("<html>regenerated</html>", encoding="utf-8")
        return out

    apply_headlines(
        weekly_dir=weekly_dir,
        date_str=date_str,
        regenerate_html=regenerate,
    )

    updated = weekly_md.read_text(encoding="utf-8")
    assert 'href="https://x.com/openai/status/111?s=20"' in updated
    assert 'href="https://fortune.com/selloff"' in updated
    assert "OpenAI announces GPT-6 Cyber for security research" in updated
    assert "Tech stocks suffer biggest selloff since Covid" in updated
    assert "@openai — Introducing GPT..." not in updated
    assert "Fortune: Old Title" not in updated
    assert html_calls == [weekly_md]
    assert (weekly_dir / f"{date_str}-links.html").read_text(encoding="utf-8") == (
        "<html>regenerated</html>"
    )


def test_heuristic_model_builds_script_from_fetched_text_only():
    from brief_week import heuristic_model

    pack = SourcePack(
        url="https://fortune.com/selloff",
        section="HEADLINES",
        status="ok",
        text=(
            "Tech stocks suffer biggest selloff since Covid. "
            "Investors see premature end to AI datacenter boom. "
            "Chipmakers led the decline after earnings."
        ),
        title="Tech stocks suffer biggest selloff since Covid",
        author=None,
    )
    result = heuristic_model(pack)
    assert "selloff" in result["headline"].lower()
    assert "datacenter" in result["script"].lower()
    assert 45 <= len(result["script"].split()) <= 70


def test_missing_api_key_raises_clear_error(monkeypatch):
    import brief_week
    from brief_week import resolve_model

    monkeypatch.setattr(brief_week, "_load_env_file", lambda: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("BRIEF_WEEK_API_KEY", raising=False)
    monkeypatch.delenv("BRIEF_WEEK_MODEL", raising=False)
    try:
        resolve_model(heuristic=False)
        raised = False
    except SystemExit as exc:
        raised = True
        assert "API key" in str(exc) or "api key" in str(exc).lower()
    assert raised


def test_extract_anthropic_text_joins_text_blocks_only():
    from brief_week import extract_anthropic_text

    payload = {
        "content": [
            {"type": "thinking", "thinking": "plan..."},
            {"type": "text", "text": '{"status":"ok","headline":"Hi","script":"One two."}'},
        ]
    }
    assert '"headline":"Hi"' in extract_anthropic_text(payload)


def test_anthropic_request_body_disables_thinking():
    from brief_week import anthropic_messages_body

    body = anthropic_messages_body(
        model_name="claude-haiku-5-5",
        prompt="Write a brief.",
    )
    assert body["thinking"] == {"type": "disabled"}
    assert "temperature" not in body
    assert body["model"] == "claude-haiku-5-5"


def test_haiku_cost_from_token_counts():
    from brief_week import cost_usd_for_usage

    # Haiku 5.5: $0.10 / MTok in, $0.50 / MTok out
    cost = cost_usd_for_usage(
        model="claude-haiku-5-5",
        input_tokens=26_752,
        output_tokens=10_054,
    )
    assert abs(cost - (26_752 / 1e6 * 0.10 + 10_054 / 1e6 * 0.50)) < 1e-9


def test_usage_tracker_records_and_summarizes(tmp_path: Path):
    from brief_week import UsageTracker

    tracker = UsageTracker(model="claude-haiku-5-5")
    tracker.add(
        url="https://example.com/one",
        input_tokens=400,
        output_tokens=150,
    )
    tracker.add(
        url="https://example.com/two",
        input_tokens=300,
        output_tokens=120,
    )
    summary = tracker.summary()
    assert summary["calls"] == 2
    assert summary["input_tokens"] == 700
    assert summary["output_tokens"] == 270
    assert summary["cost_usd"] > 0

    path = tmp_path / "usage.json"
    tracker.save(path)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["summary"]["calls"] == 2
    assert len(loaded["calls"]) == 2


def test_extract_usage_from_anthropic_payload():
    from brief_week import extract_anthropic_usage

    payload = {
        "usage": {
            "input_tokens": 412,
            "output_tokens": 138,
        }
    }
    assert extract_anthropic_usage(payload) == (412, 138)


def test_fetch_cache_skips_network_on_hit(tmp_path: Path):
    from brief_week import BriefItem, SourcePack, fetch_source_pack, load_fetch_cache, save_fetch_cache

    cache_file = tmp_path / "packs.json"
    item = BriefItem(
        section="HEADLINES",
        url="https://example.com/one",
        kind="url",
    )
    cached = SourcePack(
        url=item.url,
        section="HEADLINES",
        status="ok",
        text="Cached article body about AI datacenter spend and markets.",
        title="Cached title",
    )
    save_fetch_cache(cache_file, [cached])
    cache = load_fetch_cache(cache_file)
    calls: list[str] = []

    def get_body(url: str) -> str:
        calls.append(url)
        return "<html><body><p>should not fetch</p></body></html>"

    pack = fetch_source_pack(item, get_body=get_body, cache=cache)
    assert calls == []
    assert pack.text.startswith("Cached article")
    assert pack.status == "ok"


def test_save_brief_cache_merges_instead_of_wiping(tmp_path: Path):
    from brief_week import BriefResult, load_brief_cache, save_brief_cache

    cache = tmp_path / "briefs.json"
    save_brief_cache(
        cache,
        [
            BriefResult(
                id="a",
                url="https://example.com/a",
                section="HEADLINES",
                status="ok",
                headline="A",
                script=SAMPLE_SCRIPT,
            ),
            BriefResult(
                id="b",
                url="https://example.com/b",
                section="HEADLINES",
                status="ok",
                headline="B",
                script=SAMPLE_SCRIPT,
            ),
        ],
    )
    # Mid-run style save with only the first item of a new pass must keep B.
    save_brief_cache(
        cache,
        [
            BriefResult(
                id="a",
                url="https://example.com/a",
                section="HEADLINES",
                status="ok",
                headline="A updated",
                script=SAMPLE_SCRIPT,
            )
        ],
    )
    loaded = load_brief_cache(cache)
    assert loaded["https://example.com/a"].headline == "A updated"
    assert loaded["https://example.com/b"].headline == "B"


def test_briefs_from_rundown_seed_cache():
    from brief_week import briefs_from_rundown

    md = """# Open Disruption — News Hour Rundown
**Date:** 2099-01-01

## [section] HEADLINES {#section-headlines}

## [link] item-0-example
status: ok
https://example.com/ok

**Example headline**

Example script with enough words to count as a recovered brief for cache seeding.

## [link] item-1-blocked
status: unread
https://example.com/blocked

**UNREAD**

_UNREAD — no script until this link can be read._
"""
    briefs = briefs_from_rundown(md)
    assert len(briefs) == 2
    assert any(b.status == "ok" and b.script for b in briefs)
    assert any(b.status == "unread" for b in briefs)


def test_brief_cache_ignored_when_pack_rescued_from_unread(tmp_path: Path):
    """Browser rescue must re-brief even if cache still has an UNREAD stub."""
    from brief_week import BriefResult, build_week_briefs, save_brief_cache, save_fetch_cache

    brief_cache = tmp_path / "briefs.json"
    fetch_cache = tmp_path / "packs.json"
    url = "https://example.com/paywall"
    save_brief_cache(
        brief_cache,
        [
            BriefResult(
                id="item-0-paywall",
                url=url,
                section="HEADLINES",
                status="unread",
                headline="UNREAD",
                script="",
            )
        ],
    )
    save_fetch_cache(
        fetch_cache,
        [
            SourcePack(
                url=url,
                section="HEADLINES",
                status="unread",
                text="",
            )
        ],
    )

    model_calls: list[str] = []

    def model(source: SourcePack) -> dict[str, str]:
        model_calls.append(source.url)
        return {
            "status": "ok",
            "headline": "Rescued headline about the story",
            "script": SAMPLE_SCRIPT,
        }

    def read_page(_url: str) -> str:
        return (
            "<html><body><article><h1>Rescued story</h1>"
            "<p>Markets are repricing AI infrastructure after a weaker outlook, "
            "and analysts say cloud spend may slow sooner than expected.</p>"
            "<p>Extra paragraph so the unread guard treats this as readable.</p>"
            "</article></body></html>"
        )

    packs, briefs = build_week_briefs(
        f"<HEADLINES>\n{url}\n",
        get_body=lambda _u: "",
        model=model,
        browser=True,
        read_page=read_page,
        cache_file=fetch_cache,
        brief_cache_file=brief_cache,
        interactive=False,
    )
    assert packs[0].status == "ok"
    assert model_calls == [url]
    assert briefs[0].status == "ok"
    assert briefs[0].headline.startswith("Rescued")


def test_brief_cache_skips_model_on_hit(tmp_path: Path):
    from brief_week import BriefResult, SourcePack, build_week_briefs, save_brief_cache

    brief_cache = tmp_path / "briefs.json"
    fetch_cache = tmp_path / "packs.json"
    cached_brief = BriefResult(
        id="item-0-one",
        url="https://example.com/one",
        section="HEADLINES",
        status="ok",
        headline="Cached headline about the selloff",
        script=SAMPLE_SCRIPT,
    )
    save_brief_cache(brief_cache, [cached_brief])

    from brief_week import SourcePack as SP, save_fetch_cache

    save_fetch_cache(
        fetch_cache,
        [
            SP(
                url="https://example.com/one",
                section="HEADLINES",
                status="ok",
                text="Already fetched body about AI markets and datacenters.",
                title="Cached title",
            )
        ],
    )

    model_calls: list[str] = []

    def model(source: SourcePack) -> dict[str, str]:
        model_calls.append(source.url)
        return {
            "status": "ok",
            "headline": "Should not be used",
            "script": SAMPLE_SCRIPT,
        }

    packs, briefs = build_week_briefs(
        "<HEADLINES>\nhttps://example.com/one\n",
        get_body=lambda url: "<html></html>",
        model=model,
        cache_file=fetch_cache,
        brief_cache_file=brief_cache,
        log=lambda _m: None,
    )
    assert model_calls == []
    assert briefs[0].headline == "Cached headline about the selloff"
    assert packs[0].status == "ok"


def test_build_week_briefs_verbose_logs_fetch_and_brief_progress():
    from brief_week import build_week_briefs

    raw = """
<HEADLINES>
https://example.com/one
https://example.com/two
"""
    article = (FIXTURES / "article_sample.html").read_text(encoding="utf-8")
    logs: list[str] = []

    def get_body(url: str) -> str:
        return article

    def model(source: SourcePack) -> dict[str, str]:
        return {
            "status": "ok",
            "headline": "Tech stocks suffer biggest selloff since Covid",
            "script": SAMPLE_SCRIPT,
        }

    packs, briefs = build_week_briefs(
        raw,
        get_body=get_body,
        model=model,
        log=logs.append,
    )
    assert len(packs) == 2
    assert len(briefs) == 2
    joined = "\n".join(logs)
    assert "1/2" in joined and "2/2" in joined
    assert "FETCH" in joined
    assert "BRIEF" in joined
    assert "example.com/one" in joined


def test_decide_browser_pass_force_yes_skips_prompt():
    from brief_week import decide_browser_pass

    prompts: list[str] = []

    def ask(_message: str) -> str:
        prompts.append(_message)
        return "n"

    assert (
        decide_browser_pass(
            unread_count=2,
            force_browser=True,
            interactive=True,
            ask=ask,
        )
        is True
    )
    assert prompts == []


def test_decide_browser_pass_asks_when_interactive_and_unread():
    from brief_week import decide_browser_pass

    messages: list[str] = []

    def ask(message: str) -> str:
        messages.append(message)
        return "y"

    assert (
        decide_browser_pass(
            unread_count=3,
            force_browser=False,
            interactive=True,
            ask=ask,
        )
        is True
    )
    assert len(messages) == 1
    assert "3 unread" in messages[0].lower()


def test_decide_browser_pass_no_and_noninteractive_skip():
    from brief_week import decide_browser_pass

    assert (
        decide_browser_pass(
            unread_count=1,
            force_browser=False,
            interactive=True,
            ask=lambda _m: "n",
        )
        is False
    )
    assert (
        decide_browser_pass(
            unread_count=1,
            force_browser=False,
            interactive=False,
            ask=lambda _m: "y",
        )
        is False
    )
    assert (
        decide_browser_pass(
            unread_count=0,
            force_browser=True,
            interactive=True,
            ask=lambda _m: "y",
        )
        is False
    )


def test_build_week_briefs_prompts_then_runs_browser_on_yes(tmp_path: Path):
    from brief_week import build_week_briefs

    raw = (
        "<HEADLINES>\n"
        "https://example.com/blocked\n"
    )
    page_reads: list[str] = []

    def get_body(_url: str) -> str:
        return ""  # first pass → unread

    def read_page(url: str) -> str:
        page_reads.append(url)
        return (
            "<html><body><article><h1>Opened behind the wall</h1>"
            "<p>Markets are repricing AI infrastructure after a weaker outlook, "
            "and analysts say cloud spend may slow sooner than expected.</p>"
            "<p>Extra paragraph so the unread guard treats this as readable.</p>"
            "</article></body></html>"
        )

    def model(source: SourcePack) -> dict[str, str]:
        return {
            "status": "ok",
            "headline": "Opened story about AI spend",
            "script": SAMPLE_SCRIPT,
        }

    asks: list[str] = []

    packs, briefs = build_week_briefs(
        raw,
        get_body=get_body,
        model=model,
        browser=False,
        read_page=read_page,
        ask_browser=lambda message: asks.append(message) or "y",
        interactive=True,
    )
    assert asks and "1 unread" in asks[0].lower()
    assert page_reads == ["https://example.com/blocked"]
    assert packs[0].status == "ok"
    assert briefs[0].status == "ok"


def test_build_week_briefs_skips_browser_when_prompt_declined():
    from brief_week import build_week_briefs

    raw = "<HEADLINES>\nhttps://example.com/blocked\n"
    page_reads: list[str] = []

    packs, briefs = build_week_briefs(
        raw,
        get_body=lambda _u: "",
        model=lambda _p: {
            "status": "ok",
            "headline": "should not run",
            "script": SAMPLE_SCRIPT,
        },
        browser=False,
        read_page=lambda u: page_reads.append(u) or "<html></html>",
        ask_browser=lambda _m: "n",
        interactive=True,
    )
    assert page_reads == []
    assert packs[0].status == "unread"
    assert briefs[0].status == "unread"


def test_format_unread_browser_prompt_lists_urls():
    from brief_week import format_unread_browser_prompt

    packs = [
        SourcePack(url="https://a.example/1", section="HEADLINES", status="unread"),
        SourcePack(url="https://b.example/2", section="OTHER", status="ok"),
        SourcePack(url="https://c.example/3", section="OTHER", status="unread"),
    ]
    text = format_unread_browser_prompt(packs)
    assert "2 unread" in text.lower()
    assert "https://a.example/1" in text
    assert "https://c.example/3" in text
    assert "https://b.example/2" not in text
    assert "[y/N]" in text


def test_playwright_session_returns_page_html(monkeypatch):
    from brief_week import PlaywrightSession

    class FakePage:
        def goto(self, url, **_kwargs):
            self.url = url

        def content(self):
            return "<html><body><article><p>Playwright fetched body</p></article></body></html>"

        def wait_for_timeout(self, _ms):
            return None

    class FakeContext:
        def __init__(self):
            self.closed = False

        def new_page(self):
            return FakePage()

        def close(self):
            self.closed = True

    class FakeBrowser:
        def __init__(self):
            self.closed = False
            self.contexts: list[FakeContext] = []

        def new_context(self, **_kwargs):
            ctx = FakeContext()
            self.contexts.append(ctx)
            return ctx

        def close(self):
            self.closed = True

    class FakeChromium:
        def __init__(self):
            self.browser = FakeBrowser()

        def launch(self, **_kwargs):
            return self.browser

    class FakePlaywright:
        def __init__(self):
            self.chromium = FakeChromium()
            self.stopped = False

        def stop(self):
            self.stopped = True

    monkeypatch.setattr(
        "brief_week._start_playwright",
        lambda: FakePlaywright(),
    )

    session = PlaywrightSession()
    html = session.get_body("https://example.com/paywall")
    assert "Playwright fetched body" in html
    session.close()
    assert session._browser is None


def test_browser_get_body_uses_playwright_session():
    from brief_week import browser_get_body

    calls: list[str] = []

    class StubSession:
        def get_body(self, url: str) -> str:
            calls.append(url)
            return "<html><body>ok</body></html>"

    html = browser_get_body(
        "https://example.com/x",
        session=StubSession(),  # type: ignore[arg-type]
    )
    assert html == "<html><body>ok</body></html>"
    assert calls == ["https://example.com/x"]


def test_rebrief_unread_only_reads_unread_and_leaves_ok_alone():
    packs = [
        SourcePack(
            url="https://example.com/ok",
            section="HEADLINES",
            status="ok",
            text="Already read article text that is long enough to keep.",
            title="Already briefed",
        ),
        SourcePack(
            url="https://example.com/paywall",
            section="HEADLINES",
            status="unread",
            text="",
        ),
        SourcePack(
            url="https://www.google.com/search?q=topic",
            section="OTHER",
            status="search",
        ),
    ]
    page_reads: list[str] = []

    def read_page(url: str) -> str:
        page_reads.append(url)
        return (
            "<html><body><article><h1>Unlocked story</h1>"
            "<p>Investors see a premature end to the AI datacenter boom as "
            "markets reprice cloud infrastructure spend after earnings.</p>"
            "<p>This paragraph adds enough readable text for the unread guard.</p>"
            "</article></body></html>"
        )

    model_calls: list[str] = []

    def model(source: SourcePack) -> dict[str, str]:
        model_calls.append(source.url)
        return {
            "status": "ok",
            "headline": "Unlocked story on AI datacenter boom doubts",
            "script": SAMPLE_SCRIPT,
        }

    updated_packs, briefs = rebrief_unread(
        packs,
        read_page=read_page,
        model=model,
    )

    assert page_reads == ["https://example.com/paywall"]
    # Pack refresh only; briefing is deferred to build_week_briefs.
    assert model_calls == []
    assert briefs == []
    assert updated_packs[0].status == "ok"
    assert updated_packs[0].text.startswith("Already read")
    assert updated_packs[1].status == "ok"
    assert "datacenter" in updated_packs[1].text.lower()
    assert updated_packs[2].status == "search"
