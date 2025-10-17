# Quick Usage Guide

## 🚀 Most Common Commands

### Create This Week's Links
```bash
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=your-video" --youtube-text "This Week's Office Hours"
```

### Preview Before Creating
```bash
python weekly_links.py --date 2025-01-29 --dry-run
```

### Overwrite Existing File
```bash
python weekly_links.py --date 2025-01-29 --force
```

## 📋 All Options

| Option | What it does | Example |
|--------|--------------|---------|
| `--date` | Set the date (YYYY-MM-DD) | `--date 2025-01-29` |
| `--video-url` | YouTube video URL | `--video-url "https://youtube.com/watch?v=abc123"` |
| `--youtube-text` | Link text for video | `--youtube-text "Watch This Week's Office Hours"` |
| `--force` | Overwrite existing file | `--force` |
| `--dry-run` | Preview without creating | `--dry-run` |

## 📁 What Gets Created

- **Weekly file**: `weekly-links/2025-01-29-links.md`
- **Updated archive**: `weekly-links/index.md`

## 🔄 Typical Workflow

1. **Generate**: `python weekly_links.py --date 2025-01-29 --video-url "your-video-url"`
2. **Edit**: Open the generated file and add your curated links
3. **Commit**: `git add . && git commit -m "Add weekly links" && git push`

---
*For detailed documentation, see [README.md](./README.md)*
