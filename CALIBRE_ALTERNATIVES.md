# Alternatives to Calibre for FanFicFare

## The Problem: Calibre is Complex and Heavyweight

Your experience illustrates the core issue:
- You installed FanFicFare
- You have Calibre GUI open
- **You can't even find where plugins are**

This is the experience for most new users! Calibre is powerful but has a steep learning curve.

---

## How to Use FanFicFare Plugin in Calibre (Immediate Help)

### Finding Plugins in Calibre GUI:

```
1. Open Calibre
2. Look at the toolbar at the top
3. Click "Preferences" (gear icon)
4. In the Preferences window, find the "Advanced" section
5. Click "Plugins"
6. You should see a list of installed plugins
7. Look for "FanFicFare" in the list
```

**If FanFicFare is installed:**
```
1. After installing the plugin, you may need to restart Calibre
2. Look for a new icon in the toolbar (FFF icon)
3. OR right-click on a book → "FanFicFare" menu
4. OR go to the menu bar → select the FanFicFare option
```

**If FanFicFare is NOT in the plugin list:**
```
The AUR package may have only installed the CLI tool, not the plugin!

To install the Calibre plugin:
1. Download the plugin ZIP from: https://github.com/JimmXinu/FanFicFare/releases
2. In Calibre: Preferences → Plugins → "Load plugin from file"
3. Select the downloaded ZIP
4. Restart Calibre
5. The FFF icon should appear in toolbar
```

**Common Issue:**
Many users install via pip/AUR thinking it includes the Calibre plugin, but:
- `pip install FanFicFare` = CLI tool only
- `yay -S fanficfare` (AUR) = Likely CLI only
- **Calibre plugin = separate manual install**

This confusion is exactly why simpler alternatives are needed!

---

## All Alternatives to Calibre

### Option 1: Command Line Interface (CLI) ✅ **You Already Have This!**

**What it is:**
Pure command-line tool, no GUI needed

**How to use:**
```bash
# Download a single story
fanficfare https://archiveofourown.org/works/12345

# Update existing story
fanficfare -u story.epub

# Update all EPUBs in a directory
fanficfare -u *.epub

# Custom output location
fanficfare -o ~/fanfics/ https://archiveofourown.org/works/12345

# Custom format
fanficfare --format mobi https://archiveofourown.org/works/12345
```

**Pros:**
- ✅ You already have it installed!
- ✅ No Calibre complexity
- ✅ Fast and simple
- ✅ Great for scripting/automation
- ✅ All 117 sites supported
- ✅ Update functionality works perfectly

**Cons:**
- ❌ No library management
- ❌ No GUI
- ❌ Manual file organization
- ❌ No automatic e-reader sync
- ❌ Must track which EPUBs need updates manually

**Best for:**
- Technical users comfortable with terminal
- Simple workflows (download → read → delete)
- Automation via scripts

**Example Workflow:**
```bash
# Create a directory for fanfics
mkdir ~/fanfics
cd ~/fanfics

# Download a story
fanficfare https://archiveofourown.org/works/12345

# Result: Story downloaded as EPUB in current directory
# Open with any EPUB reader (FBReader, Foliate, etc.)

# Update weekly
fanficfare -u *.epub
```

---

### Option 2: Simple File Manager + EPUB Reader

**What it is:**
Use CLI to download, organize files yourself, read with dedicated EPUB reader

**Setup:**
```bash
# 1. Create organized directory structure
mkdir -p ~/fanfics/{complete,wip,to-read}

# 2. Download stories
fanficfare -o ~/fanfics/wip/ https://url1
fanficfare -o ~/fanfics/wip/ https://url2

# 3. Open with EPUB reader
# Linux: Foliate, Calibre's ebook-viewer, FBReader
# Windows: Calibre viewer, Sumatra PDF
# Mac: Books.app, Calibre viewer
```

**Pros:**
- ✅ Simple file-based organization
- ✅ Use any EPUB reader you prefer
- ✅ No heavyweight library software
- ✅ Portable (just copy EPUB files)
- ✅ Works on any OS

**Cons:**
- ❌ Manual organization
- ❌ No metadata search
- ❌ No automatic updates
- ❌ Must remember which stories to update

**Best for:**
- Users who read few stories
- Users who prefer simple file management
- Users who don't need library features

---

### Option 3: Python Scripts (Custom Automation)

**What it is:**
Write Python scripts using FanFicFare as a library

**Example - Auto-Update Script:**
```python
#!/usr/bin/env python3
# auto_update.py

import os
import glob
from fanficfare import adapters, writers

def update_all_stories(directory):
    """Update all EPUB files in directory"""
    epubs = glob.glob(f"{directory}/*.epub")

    for epub_path in epubs:
        print(f"Checking {epub_path}...")

        try:
            # FanFicFare can update from existing EPUB
            adapter = adapters.getAdapter(None, None)
            adapter.setChaptersRange(None)

            # Update the story
            writer = writers.getWriter('epub', adapter)
            writer.writeStory(epub_path, epub_path)

            print(f"✓ Updated {epub_path}")
        except Exception as e:
            print(f"✗ Failed: {e}")

if __name__ == "__main__":
    update_all_stories("~/fanfics/wip")
```

**Usage:**
```bash
# Weekly cron job
0 0 * * 0 python3 ~/scripts/auto_update.py
```

**Pros:**
- ✅ Full automation
- ✅ Custom logic (filters, notifications, etc.)
- ✅ Integration with other tools
- ✅ Scheduled updates via cron

**Cons:**
- ❌ Requires Python knowledge
- ❌ Manual script maintenance
- ❌ No GUI

**Best for:**
- Programmers
- Users who want custom workflows
- Automation enthusiasts

---

### Option 4: Web-Based Tools (Third Party)

**Existing Services:**

**4a. FicHub.net**
- Web interface for downloading fanfics
- Supports AO3, FFN, others
- No installation needed
- Just paste URL → download EPUB

**Pros:**
- ✅ Zero installation
- ✅ Works on any device
- ✅ Simple UX

**Cons:**
- ❌ Limited site support
- ❌ No library management
- ❌ No updates
- ❌ Privacy concerns (third party)
- ❌ Requires internet

**4b. Archive of Our Own (Built-in)**
- AO3 has built-in download feature
- Click "Download" → select EPUB
- Works for AO3 only

**Pros:**
- ✅ Official feature
- ✅ No extra tools
- ✅ Always up to date

**Cons:**
- ❌ AO3 only
- ❌ No bulk operations
- ❌ No update detection
- ❌ No library management

---

### Option 5: Browser Extensions (Future - See BROWSER_EXTENSION_FEASIBILITY.md)

**What it could be:**
One-click download from any fanfic site

**Status:**
- ✅ Feasible (see analysis)
- ❌ Doesn't exist yet (comprehensive version)
- ⚠️ Limited extensions available (FicSave, etc.)

**Existing Extension: FicSave**
- Chrome/Firefox extension
- Downloads from some sites
- Limited features

---

### Option 6: Mobile Apps

**iOS:**
- **Marvin 3** - EPUB reader, can import from URLs
- **Books** - Apple's built-in app (manual import)

**Android:**
- **Moon+ Reader** - EPUB reader with cloud sync
- **FBReader** - Open source EPUB reader

**Note:** None have FanFicFare integration
- Must download EPUBs elsewhere
- Transfer to mobile manually or via cloud

---

### Option 7: E-Reader Direct (Kindle, Kobo, etc.)

**Kindle:**
```bash
# Download EPUB
fanficfare --format mobi https://url

# Send via email
# Use Amazon's "Send to Kindle" email address
# Or use: calibre-smtp (CLI tool)
```

**Kobo:**
```bash
# Download EPUB
fanficfare https://url

# Copy to Kobo via USB
cp story.epub /media/KOBOeReader/
```

**Pros:**
- ✅ Read on dedicated device
- ✅ No computer needed for reading

**Cons:**
- ❌ Manual transfer workflow
- ❌ Updates require re-downloading
- ❌ Organizational overhead

---

## Comparison Matrix

| Method | Installation | Ease of Use | Library Mgmt | Updates | E-reader Sync | Best For |
|--------|-------------|-------------|--------------|---------|---------------|----------|
| **CLI** | Easy (pip/AUR) | Medium | ❌ Manual | ✅ Yes | ❌ Manual | Technical users |
| **File Manager** | Easy | Easy | ❌ Manual | ❌ Manual | ❌ Manual | Casual readers |
| **Python Scripts** | Easy | Hard | Custom | ✅ Auto | Custom | Programmers |
| **FicHub** | None | Very Easy | ❌ No | ❌ No | ❌ Manual | Quick downloads |
| **AO3 Download** | None | Very Easy | ❌ No | ❌ Manual | ❌ Manual | AO3-only users |
| **Browser Ext** | Very Easy | Very Easy | ⚠️ Basic | ⚠️ Some | ❌ Manual | Future (doesn't exist) |
| **Calibre** | Medium | Hard | ✅ Excellent | ✅ Yes | ✅ Yes | Power users |

---

## Recommended Setup Based on Your Needs

### If You Read <10 Stories:
```
Use: CLI + File Manager + EPUB Reader

Workflow:
1. fanficfare -o ~/fanfics/ https://url
2. Open ~/fanfics/ in file manager
3. Double-click EPUB to read
4. Weekly: fanficfare -u ~/fanfics/*.epub

No Calibre needed!
```

### If You Read 10-50 Stories:
```
Use: CLI + Simple Organization Script

Workflow:
1. Keep a text file with URLs
2. Run script to download/update all
3. Use any EPUB reader
4. Optionally: Sync EPUBs to e-reader via rsync/cloud

No Calibre needed!
```

### If You Read 50+ Stories:
```
Use: Calibre (worth the learning curve)

The library management features become essential at this scale:
- Search by author, tag, series
- Automatic metadata
- E-reader sync
- Update tracking
- Reading progress

Yes, it's complex, but it's worth it for large libraries.
```

### If You're Waiting for Better UX:
```
Use: CLI for now, watch for browser extension

The browser extension (see BROWSER_EXTENSION_FEASIBILITY.md) would be the ideal middle ground:
- Easy as web tools
- Powerful as CLI
- Library features without Calibre complexity
```

---

## Simple Getting Started (No Calibre)

Since you already have FanFicFare installed via AUR:

```bash
# 1. Create a fanfic directory
mkdir -p ~/fanfics/{wip,complete}

# 2. Download a story
fanficfare -o ~/fanfics/wip/ https://archiveofourown.org/works/12345

# 3. Install an EPUB reader (if you don't have one)
# Arch Linux options:
sudo pacman -S foliate      # Modern GTK EPUB reader
# OR
sudo pacman -S fbreader     # Lightweight reader
# OR
sudo pacman -S calibre      # Just use the viewer, not the library

# 4. Open the EPUB
foliate ~/fanfics/wip/*.epub

# 5. Weekly updates
cd ~/fanfics/wip
fanficfare -u *.epub

# 6. Move completed stories
mv "Story Name.epub" ../complete/
```

**That's it!** No Calibre library complexity needed.

---

## Advanced: Update Script Without Calibre

Create `~/bin/update-fanfics.sh`:

```bash
#!/bin/bash
# update-fanfics.sh - Update all WIP fanfics

WIP_DIR="$HOME/fanfics/wip"
LOG_FILE="$HOME/fanfics/update.log"

echo "=== Update started: $(date) ===" >> "$LOG_FILE"

cd "$WIP_DIR" || exit 1

for epub in *.epub; do
    if [ -f "$epub" ]; then
        echo "Updating: $epub"
        fanficfare -u "$epub" 2>&1 | tee -a "$LOG_FILE"

        if [ $? -eq 0 ]; then
            echo "✓ Success: $epub" | tee -a "$LOG_FILE"
        else
            echo "✗ Failed: $epub" | tee -a "$LOG_FILE"
        fi
    fi
done

echo "=== Update completed: $(date) ===" >> "$LOG_FILE"
echo "Check $LOG_FILE for details"
```

Make it executable:
```bash
chmod +x ~/bin/update-fanfics.sh
```

Add to crontab for weekly updates:
```bash
crontab -e

# Add this line (updates every Sunday at 8 AM):
0 8 * * 0 /home/yourusername/bin/update-fanfics.sh
```

---

## My Recommendation for You

Based on your situation (just installed via AUR, struggling with Calibre):

### Option A: Skip Calibre Entirely (Recommended)

```bash
# 1. Use the CLI you already have
# 2. Organize with simple directories
# 3. Read with Foliate (best Linux EPUB reader)

sudo pacman -S foliate
mkdir ~/fanfics
fanficfare -o ~/fanfics/ <url>
foliate ~/fanfics/*.epub
```

**Advantages:**
- ✅ Start reading in 30 seconds
- ✅ No learning curve
- ✅ All FanFicFare features available
- ✅ Simple and maintainable

### Option B: Learn Calibre (If You Need Library Features)

**Only worth it if:**
- You have 50+ stories
- You need search/filtering
- You sync to e-reader regularly
- You want automatic metadata

**Where to find plugins in Calibre:**
1. Preferences (gear icon in toolbar)
2. Plugins (under "Advanced" section)
3. "Load plugin from file"
4. Download from: https://github.com/JimmXinu/FanFicFare/releases
5. Install the `.zip` file
6. Restart Calibre
7. Look for FFF icon in toolbar

---

## The Real Answer to Your Question

**"Are there options other than Calibre?"**

**YES! Many:**

1. **CLI + File Manager** ← Simplest, you have this now
2. **Web tools** (FicHub, AO3 download) ← No install
3. **Python scripts** ← Most flexible
4. **Browser extension** ← Doesn't exist yet (but should!)
5. **Mobile apps** ← For reading only

**Calibre is NOT required!**

It's the most full-featured option, but also the most complex. For most users, the CLI + a good EPUB reader is perfectly sufficient.

The fact that you installed FanFicFare but can't figure out where Calibre plugins are proves that:
1. Calibre is too complex for average users
2. Better alternatives are needed
3. A browser extension would fill this gap perfectly

---

## Next Steps

**Immediate (5 minutes):**
```bash
# Try the CLI approach right now
mkdir ~/fanfics
fanficfare -o ~/fanfics/ https://archiveofourown.org/works/507461  # example story
ls ~/fanfics/  # You should see the EPUB

# Install Foliate to read it
sudo pacman -S foliate
foliate ~/fanfics/*.epub
```

**This Week:**
- Try the CLI workflow for a few stories
- Decide if you need Calibre's library features
- If yes: Install Calibre plugin properly
- If no: Stick with CLI + Foliate!

**Future:**
- Watch for browser extension development
- Consider contributing to making it happen

---

## Questions?

Common questions:

**Q: Can I organize EPUBs without Calibre?**
A: Yes! Just use directories:
```
~/fanfics/
  ├── authors/
  │   ├── Author1/
  │   └── Author2/
  ├── fandoms/
  │   ├── Harry Potter/
  │   └── Marvel/
  ├── wip/
  └── complete/
```

**Q: How do I update stories without Calibre?**
A: `fanficfare -u story.epub` - same update logic!

**Q: Can I sync to Kindle without Calibre?**
A: Yes! Email the EPUB to your Kindle email address, or use `calibre-smtp` CLI tool

**Q: What's the best EPUB reader for Linux?**
A: Foliate (modern) or Calibre's ebook-viewer (just the reader, not the library)

**Q: Is the CLI missing any features?**
A: No! CLI has all the same features as Calibre plugin. Only difference is library management.

The Calibre plugin is just a GUI wrapper around the CLI tool!
