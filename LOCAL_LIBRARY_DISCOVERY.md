# Local Library Discovery & Advanced Filtering

## The Smarter Approach: Work With What You Already Have

**Your Insight:** Instead of scraping the web, provide advanced filtering and discovery for stories you've **already downloaded**.

**Why This Is Brilliant:**

✅ **No web scraping** - work with local EPUB files
✅ **No legal issues** - it's your own library
✅ **No rate limiting** - all local processing
✅ **Privacy-first** - everything stays on your device
✅ **Actually useful** - most people have 100+ stories already
✅ **Works offline** - no internet needed
✅ **Much simpler** - no maintaining 117 site adapters

---

## The Problem with Current Tools

### Calibre's Limitations:

**Search:**
- Basic keyword search only
- Can't filter by: "stories similar to X"
- Can't filter by: "stories I haven't read yet over 100k words"
- Can't filter by: "authors whose other work I liked"
- No reading analytics
- No discovery features

**Organization:**
- Manual tagging only
- No automatic tag extraction
- No tag cleanup/normalization
- No relationship detection

**Discovery:**
- No recommendations
- No "similar stories" feature
- No reading history analysis
- No quality scoring

### File Manager:

- Even worse - just filenames and folders
- No metadata at all
- No search
- No filtering

---

## What We Can Build: Smart Local Library

### Core Concept

```
You have 500 EPUBs sitting in folders:
├── complete/
│   ├── story1.epub
│   ├── story2.epub
│   └── ...
└── wip/
    ├── story3.epub
    └── ...

Problem: How do you find "that one time travel story with the fix-it ending"?

Solution: Analyze all EPUBs, extract metadata, build searchable index
```

---

## Phase 1: EPUB Analysis & Metadata Extraction

### What's Inside an EPUB?

EPUBs are ZIP files containing:

```
story.epub/
├── META-INF/
│   └── container.xml
├── OEBPS/
│   ├── content.opf       ← METADATA HERE!
│   ├── toc.ncx
│   ├── chapter1.html
│   ├── chapter2.html
│   └── ...
└── mimetype
```

**content.opf contains:**
```xml
<metadata>
  <dc:title>Harry Potter and the Wastelands of Time</dc:title>
  <dc:creator>joe6991</dc:creator>
  <dc:subject>Time Travel</dc:subject>
  <dc:subject>Dimension Travel</dc:subject>
  <dc:subject>Dark</dc:subject>
  <dc:description>Take the broken shards...</dc:description>
  <dc:date>2009-02-15</dc:date>
  <meta name="calibre:series" content=""/>
  <meta name="calibre:rating" content="9"/>
  <meta name="calibre:timestamp" content="2023-01-15"/>

  <!-- FanFicFare adds custom metadata! -->
  <meta name="site" content="archiveofourown.org"/>
  <meta name="storyId" content="123456"/>
  <meta name="numWords" content="291329"/>
  <meta name="numChapters" content="31"/>
  <meta name="status" content="Complete"/>
  <meta name="rating" content="Mature"/>
  <meta name="warnings" content="Violence"/>
  <meta name="ships" content="Harry/Hermione"/>
  <meta name="characters" content="Harry Potter, Hermione Granger"/>
  <meta name="kudos" content="12453"/>
  <meta name="bookmarks" content="2891"/>
</metadata>
```

**We can extract:**
- ✅ Title, author, summary
- ✅ All tags and categories
- ✅ Word count, chapter count
- ✅ Completion status
- ✅ Rating, warnings
- ✅ Ships/relationships
- ✅ Characters
- ✅ Original site and story ID
- ✅ Kudos, bookmarks, reviews
- ✅ Publication/update dates
- ✅ When you downloaded it
- ✅ Calibre rating (if you rated it)

### Additional Analysis We Can Do:

**From the actual content (HTML chapters):**

1. **Reading time estimate:**
   ```javascript
   const wordCount = extractWordCount(chapters);
   const readingTime = wordCount / 250; // avg words per minute
   // "This is a 12 hour read"
   ```

2. **Actual tags from text:**
   ```javascript
   // Detect common tropes from content
   const tropes = detectTropes(fullText);
   // "Contains: time loop, peggy sue, fix-it"
   ```

3. **POV and tense:**
   ```javascript
   const pov = detectPOV(chapters[0]);
   // "First person" vs "Third person"

   const tense = detectTense(chapters[0]);
   // "Past tense" vs "Present tense"
   ```

4. **Actual completion analysis:**
   ```javascript
   const lastChapter = chapters[chapters.length - 1];
   const appearsComplete = detectEnding(lastChapter);
   // "Appears complete despite WIP status"
   ```

5. **Content warnings (auto-detected):**
   ```javascript
   const warnings = detectContentWarnings(fullText);
   // Detect violence, sexual content, etc. from actual text
   ```

6. **Extract actual relationships:**
   ```javascript
   const ships = detectRelationships(fullText);
   // Who appears together most often
   ```

---

## Phase 2: Smart Indexing

### Build a Local Search Index

```javascript
class LibraryIndexer {
  async indexLibrary(directory) {
    const epubs = await this.findAllEPUBs(directory);
    const indexed = [];

    for (const epubPath of epubs) {
      console.log(`Indexing: ${epubPath}`);

      const metadata = await this.extractMetadata(epubPath);
      const content = await this.extractContent(epubPath);
      const analysis = await this.analyzeContent(content);

      indexed.push({
        path: epubPath,
        filename: path.basename(epubPath),
        ...metadata,
        ...analysis,
        indexed: Date.now()
      });
    }

    // Save index to local database
    await this.saveIndex(indexed);

    return indexed;
  }

  async extractMetadata(epubPath) {
    // Read EPUB (it's a ZIP file)
    const zip = await JSZip.loadAsync(fs.readFileSync(epubPath));

    // Extract content.opf
    const opfPath = await this.findOPF(zip);
    const opfContent = await zip.file(opfPath).async('text');

    // Parse XML
    const parser = new DOMParser();
    const opf = parser.parseFromString(opfContent, 'text/xml');

    return {
      title: this.getMetadata(opf, 'dc:title'),
      author: this.getMetadata(opf, 'dc:creator'),
      summary: this.getMetadata(opf, 'dc:description'),
      tags: this.getMetadataAll(opf, 'dc:subject'),
      published: this.getMetadata(opf, 'dc:date'),

      // FanFicFare custom fields
      site: this.getMeta(opf, 'site'),
      storyId: this.getMeta(opf, 'storyId'),
      words: parseInt(this.getMeta(opf, 'numWords') || 0),
      chapters: parseInt(this.getMeta(opf, 'numChapters') || 0),
      status: this.getMeta(opf, 'status'),
      rating: this.getMeta(opf, 'rating'),
      ships: this.getMeta(opf, 'ships')?.split(', ') || [],
      characters: this.getMeta(opf, 'characters')?.split(', ') || [],

      // Calibre fields
      calibreRating: this.getMeta(opf, 'calibre:rating'),
      calibreSeries: this.getMeta(opf, 'calibre:series'),

      // File info
      fileSize: fs.statSync(epubPath).size,
      modified: fs.statSync(epubPath).mtime
    };
  }

  async analyzeContent(content) {
    const fullText = content.chapters.join('\n\n');

    return {
      readingTimeMinutes: Math.ceil(content.wordCount / 250),
      pov: this.detectPOV(content.chapters[0]),
      tense: this.detectTense(content.chapters[0]),
      detectedTropes: this.detectTropes(fullText),
      autoTags: this.extractAutoTags(fullText),
      sentiment: this.analyzeSentiment(fullText),
      appearsComplete: this.detectEnding(content.chapters[content.chapters.length - 1])
    };
  }
}
```

### Index Storage (SQLite or JSON)

```sql
-- Simple SQLite schema
CREATE TABLE stories (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  filename TEXT,

  -- Basic metadata
  title TEXT,
  author TEXT,
  summary TEXT,
  words INTEGER,
  chapters INTEGER,
  status TEXT,
  rating TEXT,

  -- Source
  site TEXT,
  story_id TEXT,
  original_url TEXT,

  -- Tags (JSON array)
  tags TEXT, -- JSON: ["Time Travel", "Fix-It"]
  ships TEXT, -- JSON: ["Harry/Hermione"]
  characters TEXT, -- JSON: ["Harry Potter"]

  -- Analysis
  reading_time_minutes INTEGER,
  pov TEXT,
  tense TEXT,
  detected_tropes TEXT, -- JSON array
  auto_tags TEXT, -- JSON array

  -- User data
  calibre_rating REAL,
  user_rating REAL,
  read_status TEXT, -- "unread", "reading", "read"
  last_read_date INTEGER,
  times_read INTEGER DEFAULT 0,

  -- File info
  file_size INTEGER,
  indexed_date INTEGER,
  modified_date INTEGER
);

-- Full-text search index
CREATE VIRTUAL TABLE stories_fts USING fts5(
  title,
  author,
  summary,
  tags,
  content='stories'
);

-- Tag index for fast filtering
CREATE TABLE tags (
  id INTEGER PRIMARY KEY,
  story_id INTEGER,
  tag TEXT,
  FOREIGN KEY(story_id) REFERENCES stories(id)
);

CREATE INDEX idx_tags_tag ON tags(tag);
```

---

## Phase 3: Advanced Filtering

### What You Can Now Do:

```javascript
// Find stories you haven't read yet, over 100k words, complete
await library.search({
  readStatus: 'unread',
  minWords: 100000,
  status: 'Complete'
});

// Find time travel stories you rated highly
await library.search({
  tags: ['Time Travel'],
  minUserRating: 4.0
});

// Find stories similar to one you liked
await library.findSimilar(storyId, {
  similarityThreshold: 0.7,
  limit: 10
});

// Find all stories by authors whose other work you liked
await library.search({
  authors: await library.getAuthorsOfHighRatedStories(),
  excludeRead: true
});

// Complex query
await library.search({
  tags: ['Time Travel', 'Fix-It'],
  excludeTags: ['Romance', 'Slash'],
  minWords: 50000,
  maxWords: 300000,
  status: 'Complete',
  minKudos: 1000,
  readStatus: 'unread',
  sortBy: 'kudos',
  limit: 20
});

// Natural language search
await library.search({
  query: "long complete time travel stories I haven't read yet"
});
```

### Implementation:

```javascript
class SmartLibrary {
  constructor(indexPath) {
    this.db = new Database(indexPath);
  }

  async search(filters) {
    let query = 'SELECT * FROM stories WHERE 1=1';
    const params = [];

    // Read status
    if (filters.readStatus) {
      query += ' AND read_status = ?';
      params.push(filters.readStatus);
    }

    // Word count range
    if (filters.minWords) {
      query += ' AND words >= ?';
      params.push(filters.minWords);
    }
    if (filters.maxWords) {
      query += ' AND words <= ?';
      params.push(filters.maxWords);
    }

    // Status
    if (filters.status) {
      query += ' AND status = ?';
      params.push(filters.status);
    }

    // Tags (include)
    if (filters.tags && filters.tags.length > 0) {
      // JSON array search
      for (const tag of filters.tags) {
        query += ` AND tags LIKE ?`;
        params.push(`%"${tag}"%`);
      }
    }

    // Tags (exclude)
    if (filters.excludeTags && filters.excludeTags.length > 0) {
      for (const tag of filters.excludeTags) {
        query += ` AND tags NOT LIKE ?`;
        params.push(`%"${tag}"%`);
      }
    }

    // Rating
    if (filters.minUserRating) {
      query += ' AND user_rating >= ?';
      params.push(filters.minUserRating);
    }

    // Sort
    if (filters.sortBy) {
      const sortMap = {
        'kudos': 'kudos DESC',
        'words': 'words DESC',
        'rating': 'user_rating DESC',
        'recent': 'indexed_date DESC'
      };
      query += ` ORDER BY ${sortMap[filters.sortBy] || 'title'}`;
    }

    // Limit
    if (filters.limit) {
      query += ' LIMIT ?';
      params.push(filters.limit);
    }

    return this.db.all(query, params);
  }

  async findSimilar(storyId, options = {}) {
    const story = await this.getStory(storyId);

    // Extract features
    const features = {
      tags: JSON.parse(story.tags || '[]'),
      author: story.author,
      words: story.words,
      rating: story.rating,
      characters: JSON.parse(story.characters || '[]'),
      ships: JSON.parse(story.ships || '[]')
    };

    // Find all other stories
    const allStories = await this.db.all(
      'SELECT * FROM stories WHERE id != ?',
      [storyId]
    );

    // Calculate similarity scores
    const scored = allStories.map(other => ({
      ...other,
      similarity: this.calculateSimilarity(features, {
        tags: JSON.parse(other.tags || '[]'),
        author: other.author,
        words: other.words,
        rating: other.rating,
        characters: JSON.parse(other.characters || '[]'),
        ships: JSON.parse(other.ships || '[]')
      })
    }));

    // Filter and sort
    return scored
      .filter(s => s.similarity >= (options.similarityThreshold || 0.5))
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, options.limit || 10);
  }

  calculateSimilarity(a, b) {
    let score = 0;

    // Tag overlap (weighted heavily)
    const tagOverlap = this.jaccardSimilarity(a.tags, b.tags);
    score += tagOverlap * 0.4;

    // Character overlap
    const charOverlap = this.jaccardSimilarity(a.characters, b.characters);
    score += charOverlap * 0.2;

    // Same author bonus
    if (a.author === b.author) {
      score += 0.15;
    }

    // Similar length
    const lengthRatio = Math.min(a.words, b.words) / Math.max(a.words, b.words);
    score += lengthRatio * 0.1;

    // Same rating
    if (a.rating === b.rating) {
      score += 0.1;
    }

    // Ship overlap
    const shipOverlap = this.jaccardSimilarity(a.ships, b.ships);
    score += shipOverlap * 0.05;

    return score;
  }

  jaccardSimilarity(set1, set2) {
    const s1 = new Set(set1);
    const s2 = new Set(set2);

    const intersection = new Set([...s1].filter(x => s2.has(x)));
    const union = new Set([...s1, ...s2]);

    return union.size === 0 ? 0 : intersection.size / union.size;
  }
}
```

---

## Phase 4: Reading Analytics

### Track Your Reading Habits:

```javascript
class ReadingTracker {
  async markAsRead(storyId) {
    await this.db.run(`
      UPDATE stories
      SET read_status = 'read',
          last_read_date = ?,
          times_read = times_read + 1
      WHERE id = ?
    `, [Date.now(), storyId]);

    // Record in reading history
    await this.db.run(`
      INSERT INTO reading_history (story_id, read_date)
      VALUES (?, ?)
    `, [storyId, Date.now()]);
  }

  async getReadingStats() {
    return {
      totalStories: await this.getTotalStories(),
      storiesRead: await this.getStoriesRead(),
      totalWordsRead: await this.getTotalWordsRead(),
      totalReadingHours: await this.getTotalReadingHours(),
      averageRating: await this.getAverageRating(),
      favoriteAuthors: await this.getFavoriteAuthors(),
      favoriteTags: await this.getFavoriteTags(),
      readingStreak: await this.getReadingStreak(),
      storiesPerMonth: await this.getStoriesPerMonth()
    };
  }

  async getFavoriteAuthors() {
    return this.db.all(`
      SELECT author,
             COUNT(*) as count,
             AVG(user_rating) as avg_rating
      FROM stories
      WHERE read_status = 'read'
      GROUP BY author
      ORDER BY count DESC, avg_rating DESC
      LIMIT 10
    `);
  }

  async getFavoriteTags() {
    // This requires tag normalization table
    return this.db.all(`
      SELECT tag,
             COUNT(*) as count,
             AVG(s.user_rating) as avg_rating
      FROM tags t
      JOIN stories s ON t.story_id = s.id
      WHERE s.read_status = 'read'
      GROUP BY tag
      ORDER BY count DESC
      LIMIT 20
    `);
  }

  async getRecommendations() {
    // Based on your reading history
    const favoriteAuthors = await this.getFavoriteAuthors();
    const favoriteTags = await this.getFavoriteTags();
    const highRatedStories = await this.getHighRatedStories();

    // Find unread stories matching your preferences
    return this.db.all(`
      SELECT s.*,
        (
          CASE WHEN s.author IN (${favoriteAuthors.map(a => '?').join(',')}) THEN 1 ELSE 0 END +
          /* tag matching score would go here */
          0
        ) as recommendation_score
      FROM stories s
      WHERE s.read_status != 'read'
      ORDER BY recommendation_score DESC, s.words DESC
      LIMIT 20
    `, favoriteAuthors.map(a => a.author));
  }
}
```

---

## Phase 5: Browser Extension UI

### Simple, Clean Interface:

```
┌─────────────────────────────────────────────────┐
│ My Fanfic Library                      🔄 ⚙️   │
├─────────────────────────────────────────────────┤
│ 📚 Library: 487 stories (123 unread)            │
│                                                 │
│ 🔍 Search & Filter                              │
│ ┌─────────────────────────────────────────────┐ │
│ │ time travel fix-it                         │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ☐ Unread only                                   │
│ ☑ Complete only                                 │
│ ☑ >100k words                                   │
│ ☐ Exclude Romance                               │
│                                                 │
│ Sort by: Rating ▼                               │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ⭐⭐⭐⭐⭐ Wastelands of Time               │ │
│ │ by joe6991                                  │ │
│ │ 291k words • 31 chapters • Complete         │ │
│ │ 🏷️ Time Travel, Dark, Fix-It               │ │
│ │ 📖 12h read • ✅ Read 2x • Last: Jan 2024  │ │
│ │ [Open] [Mark Unread] [Find Similar]        │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ ⭐⭐⭐⭐☆ Backwards Compatible              │ │
│ │ by Ruskbyte                                 │ │
│ │ 157k words • 24 chapters • Complete         │ │
│ │ 🏷️ Time Travel, Fix-It, Adventure          │ │
│ │ 📖 8h read • 📝 Unread                      │ │
│ │ 💡 Similar to stories you loved!           │ │
│ │ [Open] [Mark Read] [Find Similar]          │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│                [Load More]                      │
└─────────────────────────────────────────────────┘

Tab: Library | Stats | Recommendations | Settings
```

---

## Implementation Roadmap

### Week 1-2: Core Library Indexer
- EPUB parsing (JSZip)
- Metadata extraction
- SQLite database
- Basic search

### Week 3: Advanced Filtering
- Complex query builder
- Tag filtering
- Similarity scoring

### Week 4: UI
- Browser extension popup
- Search interface
- Results display
- Story details

### Week 5-6: Analytics
- Reading tracker
- Statistics dashboard
- Recommendations engine

### Week 7-8: Polish
- Tag cleanup/normalization
- Performance optimization
- Auto-reindex on new files
- Export features

---

## Why This Is Better Than Web Scraping Search

**Advantages:**

✅ **Legal** - Your own files
✅ **Private** - No data sent anywhere
✅ **Fast** - Local indexing
✅ **Offline** - Works without internet
✅ **Reliable** - No site changes breaking things
✅ **Simple** - One codebase, no site adapters
✅ **Useful NOW** - Works with existing libraries

**What You Get:**

1. **Search your library** like you search AO3
2. **Filter by anything** - tags, length, status, rating, author
3. **Find similar stories** - "More like this"
4. **Track reading** - What you've read, when, how many times
5. **Get recommendations** - Based on what you like
6. **Reading analytics** - Favorite authors, tags, trends
7. **Smart organization** - Auto-tagging, cleanup

**What You Don't Deal With:**

❌ Web scraping fragility
❌ Site TOS issues
❌ Rate limiting
❌ Maintenance burden
❌ Legal gray areas

---

## Bonus: Can Still Integrate With Download

### Combined Workflow:

```
1. Download story via FanFicFare (CLI or Calibre)
   ↓
2. Auto-detect new EPUB in library folder
   ↓
3. Index it automatically
   ↓
4. Now searchable/filterable in extension
   ↓
5. Track when you read it
   ↓
6. Get recommendations based on it
```

**Extension can trigger downloads:**
```javascript
// "Download similar stories" button
async function downloadSimilarStories(storyId) {
  const similar = await library.findSimilar(storyId);

  for (const story of similar.slice(0, 5)) {
    if (story.original_url) {
      // Trigger FanFicFare download
      await exec(`fanficfare ${story.original_url}`);
    }
  }
}
```

---

## Next Steps

Want me to build a proof-of-concept that:

1. **Scans a directory of EPUBs**
2. **Extracts all metadata**
3. **Builds searchable index**
4. **Provides advanced filtering**
5. **Shows recommendations**

This could be working in 1-2 weeks and actually be useful immediately!

Much better than a web scraping search engine that might get shut down or break constantly.
