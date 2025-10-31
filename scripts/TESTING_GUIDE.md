# Testing Guide for Enhanced Link Title Generation

This guide explains how to test the improved link title generation system.

## Quick Start Testing

### 1. Run the Test Suite

```bash
cd scripts
python3 test_link_generation.py
```

This interactive test suite will:
- Test URL path parsing (fast, no network)
- Optionally test metadata extraction (makes HTTP requests)
- Optionally test Twitter scraping (makes HTTP requests)
- Compare before/after improvements

### 2. Test with Your Actual File (Dry Run)

Preview changes without modifying the file:

```bash
# Basic formatter (uses path parsing)
python3 scripts/format_urls.py --input-file weekly-links/2025-10-30-links.md --dry-run

# Smart formatter (uses metadata extraction + path parsing)
python3 scripts/smart_url_formatter.py --input-file weekly-links/2025-10-30-links.md --dry-run
```

### 3. Test Individual URLs

```bash
# Test a few URLs
python3 scripts/format_urls.py --urls "https://openai.com/index/introducing-aardvark/ https://x.com/sama/status/123"

# Test with smart formatter (will attempt metadata extraction)
python3 scripts/smart_url_formatter.py --urls "https://openai.com/index/introducing-aardvark/"
```

## What to Look For

### ✅ Improvements You Should See

**Before:**
- `https://openai.com/index/introducing-aardvark/` → "OpenAI"
- `https://openai.com/foundation/` → "OpenAI"
- `https://x.com/sama/status/123` → "sama — AI Discussion"

**After:**
- `https://openai.com/index/introducing-aardvark/` → "OpenAI: Introducing Aardvark"
- `https://openai.com/foundation/` → "OpenAI: Foundation"
- `https://x.com/sama/status/123` → "sama — [actual tweet text]" (if scraping enabled)

### 📊 Examples from Your File

Here are some improvements you'll see:

1. **OpenAI Links** - Now show descriptive titles:
   - `https://openai.com/index/built-to-benefit-everyone/` → "OpenAI: Built To Benefit Everyone"
   - `https://openai.com/index/introducing-aardvark/` → "OpenAI: Introducing Aardvark"
   - `https://openai.com/foundation/` → "OpenAI: Foundation"

2. **Blog Posts** - Path parsing extracts meaningful content:
   - `https://blog.google/technology/google-labs/notebooklm-custom-personas-engine-upgrade/` → "Blog.Google: Notebooklm Custom Personas Engine Upgrade"
   - `https://research.google/blog/how-we-are-building-the-personal-health-coach/` → "Research.Google: How We Are Building The Personal Health Coach"

3. **GitHub/HuggingFace** - Better repository descriptions:
   - `https://huggingface.co/MiniMaxAI/MiniMax-M2` → "Huggingface.Co: Mini Max M2"
   - `https://github.com/johannschopplich/toon` → "GitHub: johannschopplich/toon" (already good)

## Testing Scenarios

### Scenario 1: Quick Test (No Network)
Test path parsing without making HTTP requests:

```bash
python3 scripts/format_urls.py --urls "https://openai.com/index/introducing-aardvark/" --dry-run
```

### Scenario 2: Full Test with Metadata Extraction
Test with actual page title extraction (slower, makes HTTP requests):

```bash
python3 scripts/smart_url_formatter.py --input-file weekly-links/2025-10-30-links.md --dry-run
```

### Scenario 3: Twitter Scraping Test
Test Twitter/X link scraping (makes HTTP requests, may be rate-limited):

```bash
python3 -c "
from scripts.twitter_scraper import generate_twitter_title
print(generate_twitter_title('https://x.com/sama/status/1983584366547829073', enable_scraping=True))
"
```

## Applying Changes

Once you're satisfied with the results:

### Option 1: Use Basic Formatter (Fast)
```bash
python3 scripts/format_urls.py --input-file weekly-links/2025-10-30-links.md
```

### Option 2: Use Smart Formatter (Slower, Better Titles)
```bash
python3 scripts/smart_url_formatter.py --input-file weekly-links/2025-10-30-links.md
```

### Option 3: Use Hybrid Workflow (Recommended)
```bash
python3 scripts/hybrid_workflow.py --input weekly-links/2025-10-30-links.md
```

This combines fast formatting with smart extraction for optimal results.

## Testing Individual Components

### Test Path Parsing Only

```python
from scripts.format_urls import parse_url_path_to_title

url = "https://openai.com/index/introducing-aardvark/"
title = parse_url_path_to_title(url)
print(title)  # "Introducing Aardvark"
```

### Test Metadata Extraction Only

```python
from scripts.smart_url_formatter import extract_title_from_url

url = "https://openai.com/index/introducing-aardvark/"
title = extract_title_from_url(url)
print(title)  # Actual page title from HTML
```

### Test Twitter Scraping Only

```python
from scripts.twitter_scraper import scrape_tweet_content, generate_twitter_title

url = "https://x.com/sama/status/1983584366547829073"
tweet_text = scrape_tweet_content(url)
title = generate_twitter_title(url, tweet_text)
print(title)
```

## Expected Results Summary

| URL Type | Before | After (Path Parsing) | After (Metadata Extraction) |
|----------|--------|---------------------|---------------------------|
| OpenAI blog | "OpenAI" | "OpenAI: Introducing Aardvark" | "Introducing Aardvark: OpenAI's agentic security researcher" |
| Twitter/X | "sama — AI Discussion" | "sama — AI Discussion" | "sama — [actual tweet text]" |
| GitHub | "GitHub: repo/name" | "GitHub: repo/name" | "GitHub: repo/name" |
| Blog posts | "Domain: AI Resource" | "Domain: Article Title" | "[Actual page title]" |

## Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the project root:
```bash
cd /Users/todd/Documents/AI\ DEVELOPMENT/OPEN_DISRUPTION
python3 scripts/format_urls.py --help
```

### Twitter Scraping Not Working
Twitter/X may rate limit or block scraping. The system will automatically fall back to username-based categorization if scraping fails.

### Metadata Extraction Failing
Some sites may block scrapers or require JavaScript. The system will fall back to path parsing or domain-based titles.

### Rate Limiting
If you're testing many URLs with metadata extraction, add delays between requests:
```python
import time
time.sleep(1)  # Between requests
```

## Next Steps

1. Run the test suite to see improvements
2. Test with your actual file using `--dry-run`
3. Review the results
4. Apply changes when satisfied
5. Consider using the hybrid workflow for best results

For questions or issues, check the script docstrings or review the implementation in:
- `scripts/format_urls.py` - Basic formatter with path parsing
- `scripts/smart_url_formatter.py` - Enhanced formatter with metadata extraction
- `scripts/twitter_scraper.py` - Twitter/X scraping functionality

