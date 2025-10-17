# Weekly Links Script Documentation

This script automates the creation of weekly AI news link collections for Open Disruption. It generates markdown files with proper formatting and automatically updates the archive index.

## 🚀 Quick Start

### Basic Usage
```bash
# Create a new weekly links file for today
python weekly_links.py

# Create for a specific date
python weekly_links.py --date 2025-01-29

# Add YouTube video link
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=your-video-id" --youtube-text "Watch This Week's Office Hours"
```

## 📋 Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--date` | Date in YYYY-MM-DD format | Today's date | `--date 2025-01-29` |
| `--video-url` | YouTube URL for the episode | `https://youtube.com/your-video-link` | `--video-url "https://youtube.com/watch?v=abc123"` |
| `--youtube-text` | Link text for YouTube video | `YouTube Link Here` | `--youtube-text "Watch This Week's Office Hours"` |
| `--force` | Overwrite existing file | False | `--force` |
| `--dry-run` | Preview changes without creating files | False | `--dry-run` |

## 📁 Generated Files

The script creates and manages these files:

### Weekly Files
- **Location**: `weekly-links/YYYY-MM-DD-links.md`
- **Example**: `weekly-links/2025-01-29-links.md`
- **Content**: Curated AI news, research papers, tools, and threads

### Archive Index
- **Location**: `weekly-links/index.md`
- **Content**: Automatically updated list of all weekly collections
- **Features**: Sorted by date (newest first)

## 🎯 Common Use Cases

### 1. Create This Week's Links
```bash
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=abc123" --youtube-text "January 29 Office Hours"
```

### 2. Preview Before Creating
```bash
python weekly_links.py --date 2025-01-29 --dry-run
```

### 3. Overwrite Existing File
```bash
python weekly_links.py --date 2025-01-29 --force
```

### 4. Update Archive Only
If you manually edit a weekly file, run the script to update the archive:
```bash
python weekly_links.py --date 2025-01-29 --force
```

## 📝 Workflow

### Weekly Content Creation Process

1. **Generate the template**:
   ```bash
   python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=your-video" --youtube-text "This Week's Office Hours"
   ```

2. **Edit the generated file**:
   - Open `weekly-links/2025-01-29-links.md`
   - Replace example links with real AI news
   - Add your curated content

3. **Commit and push**:
   ```bash
   git add weekly-links/2025-01-29-links.md
   git commit -m "Add weekly links for January 29, 2025"
   git push origin main
   ```

## 🔧 Advanced Features

### External Link Handling
The script automatically converts external links to HTML with `target="_blank"` for better user experience:
- External links: `<a href="url" target="_blank" rel="noopener noreferrer">text</a>`
- Internal links: `<a href="url">text</a>`

### Template System
- **Primary**: Uses `weekly-links/template.md` if it exists
- **Fallback**: Uses built-in template if no custom template found
- **Customization**: Edit `template.md` to change the format

### Archive Management
- Automatically sorts weekly files by date (newest first)
- Updates archive index with all available weeks
- Maintains consistent formatting across all entries

## 🐛 Troubleshooting

### Common Issues

**File already exists error**:
```bash
# Use --force to overwrite
python weekly_links.py --date 2025-01-29 --force
```

**Invalid date format**:
```bash
# Use YYYY-MM-DD format
python weekly_links.py --date 2025-01-29  # ✅ Correct
python weekly_links.py --date 01/29/2025  # ❌ Wrong format
```

**Template not found**:
- The script will use the built-in template if `weekly-links/template.md` doesn't exist
- Create a custom template by copying the default one

### Debug Mode
Use `--dry-run` to preview changes without creating files:
```bash
python weekly_links.py --date 2025-01-29 --dry-run
```

## 📊 File Structure

```
scripts/
├── weekly_links.py          # Main script
└── README.md               # This documentation

weekly-links/
├── template.md             # Custom template (optional)
├── index.md                # Archive index (auto-generated)
├── 2025-01-15-links.md     # Individual weekly files
├── 2025-01-22-links.md
└── ...
```

## 🔗 Integration with GitHub Pages

The generated markdown files work seamlessly with GitHub Pages:
- **Archive**: `https://opendisruption.com/weekly-links/`
- **Individual weeks**: `https://opendisruption.com/weekly-links/2025-01-29-links.html`

## 📞 Support

For issues or questions:
1. Check this documentation first
2. Use `--dry-run` to preview changes
3. Verify date format is YYYY-MM-DD
4. Ensure you have write permissions in the `weekly-links/` directory

---

*This script is part of the Open Disruption project. For more information, visit [opendisruption.com](https://opendisruption.com/).*
