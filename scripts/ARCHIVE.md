# Archived manual weekly workflow

These are the multi-step commands used before `python scripts/week.py`.
The individual scripts are still in this directory and still work. Prefer
[`week.py`](week.py) for the weekly ritual; use these when you need a one-off
step or are debugging a single stage.

See [`README.md`](README.md) for the current quick start and per-script flags.

## Manual RAW_LINKS ritual

1. Copy your Google Keep note into a new file: `RAW_LINKS/YYYY-MM-DD`
2. Convert to weekly markdown:

```bash
python scripts/raw_links_to_weekly.py --input RAW_LINKS/YYYY-MM-DD
```

3. Smart format + HTML (edit the weekly file to add the YouTube URL when ready):

```bash
python scripts/hybrid_workflow.py --input weekly-links/YYYY-MM-DD-links.md --smart-only
```

4. Open links in Chrome for office hours:

```bash
python scripts/open_links_in_chrome.py RAW_LINKS/YYYY-MM-DD --delay 3 8
```

## Older quick starts (from README)

### Smart Hybrid Workflow (template-first)

```bash
# 1. Upload your video to YouTube and get the URL
# 2. Generate template for this week with your YouTube URL
python scripts/weekly_links.py --date 2026-01-29 --video-url "https://youtube.com/watch?v=your-video"

# 3. Add your raw URLs to the generated file
# (Open weekly-links/YYYY-MM-DD-links.md and paste URLs in the "Links from Office Hours" section)

# 4. Smart formatting with metadata extraction + HTML generation
python scripts/hybrid_workflow.py --input weekly-links/2026-01-29-links.md --smart-only

# 5. Review and commit (both .md and .html files)
git add . && git commit -m "Add weekly links with smart titles and GA tracking" && git push

# 6. Open all links in Chrome for office hours
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --delay 3 8
```

### RAW_LINKS Workflow (file already in RAW_LINKS/)

```bash
# 1. Open all links in Chrome for office hours
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --delay 3 8

# 2. Convert RAW_LINKS to weekly-links and run pipeline
python scripts/raw_links_to_weekly.py --input RAW_LINKS/2026-01-29
# Edit weekly-links/2026-01-29-links.md to add YouTube URL
python scripts/hybrid_workflow.py --input weekly-links/2026-01-29-links.md --smart-only

# 3. Review and commit
git add . && git commit -m "Add weekly links for January 29" && git push
```
