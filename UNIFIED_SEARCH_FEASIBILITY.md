# Unified Fanfic Search & Discovery Platform Feasibility

## The Vision

**Question:** Can we build something that searches fanfic sites from within the app with better filtering?

**Answer:** YES - and this is actually **way more valuable** than just a download tool!

---

## The Problem with Current Search

### Site-by-Site Issues:

**Archive of Our Own (AO3):**
- ✅ Good: Advanced filtering (tags, ratings, word count, etc.)
- ✅ Good: Boolean search operators
- ❌ Bad: Slow (can take 10+ seconds)
- ❌ Bad: Limited recommendation engine
- ❌ Bad: No cross-site search
- ❌ Bad: No "similar stories" feature

**FanFiction.Net (FFN):**
- ❌ Bad: Very limited filtering
- ❌ Bad: No tag system (only categories)
- ❌ Bad: Poor search quality
- ❌ Bad: Can't search by word count range
- ❌ Bad: No exclude filters
- ❌ Bad: Ancient UI

**Wattpad:**
- ⚠️ Medium: Has tags but poor organization
- ❌ Bad: Algorithm prioritizes "popular" over "relevant"
- ❌ Bad: Heavy on social features, light on search
- ❌ Bad: Can't filter by completion status reliably

**Royal Road:**
- ✅ Good: Has advanced filters
- ⚠️ Medium: Limited to specific genres (LitRPG, etc.)
- ❌ Bad: No cross-site search

### What Users Actually Want:

```
"I want to find:
- Harry Potter fanfic
- Featuring time travel
- Over 100k words
- Complete
- Rated M or higher
- NOT a romance
- Similar to stories I've liked
- FROM ALL SITES AT ONCE"
```

**Current solution:** Visit 5 different sites, search each one separately, manually filter, hope for the best.

**What should exist:** Unified search across all sites with intelligent filtering.

---

## Technical Feasibility Analysis

### Option 1: API-Based Search (If Available)

**AO3:**
```
Status: ✅ Has unofficial API
URL: https://archiveofourown.org/works/search
Method: GET with query parameters

Example:
GET https://archiveofourown.org/works/search?work_search[query]=harry+potter&work_search[word_count]=>100000&work_search[complete]=true

Returns: HTML (can be parsed)

Rate limits: Yes, be respectful (1-2 requests/second)
```

**FanFiction.Net:**
```
Status: ⚠️ No official API, but has structured URLs
Method: Screen scraping with structured queries

Example:
https://www.fanfiction.net/book/Harry-Potter/?&srt=1&r=10&len=100&s=0

Parameters:
- srt: sort order
- r: rating filter
- len: minimum length (in thousands of words)
- s: status (0=all, 1=in-progress, 2=complete)

Returns: HTML (can be parsed)

Rate limits: Yes, must be respectful
```

**Wattpad:**
```
Status: ✅ Has official API (but restricted)
Method: OAuth-based API access
Docs: https://developer.wattpad.com/

Note: Requires API key application

Returns: JSON

Rate limits: Yes, enforced per API key
```

**Royal Road:**
```
Status: ⚠️ No official API
Method: Screen scraping
URL: https://www.royalroad.com/fictions/search

Returns: HTML (can be parsed)

Rate limits: Be respectful
```

### Option 2: Web Scraping (Universal Fallback)

**How it works:**
```javascript
// Example: Search AO3 from extension
async function searchAO3(query, filters) {
  const params = new URLSearchParams({
    'work_search[query]': query,
    'work_search[word_count]': filters.minWords ? `>${filters.minWords}` : '',
    'work_search[complete]': filters.complete ? 'true' : '',
    'work_search[rating_ids]': filters.ratings.join(','),
    // ... more filters
  });

  const url = `https://archiveofourown.org/works/search?${params}`;
  const response = await fetch(url);
  const html = await response.text();

  // Parse HTML to extract results
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  const results = [];
  doc.querySelectorAll('.work').forEach(workEl => {
    results.push({
      title: workEl.querySelector('.heading a').textContent,
      author: workEl.querySelector('.authors a').textContent,
      summary: workEl.querySelector('.summary').textContent,
      tags: [...workEl.querySelectorAll('.tags li')].map(t => t.textContent),
      words: parseInt(workEl.querySelector('.words').textContent.replace(/,/g, '')),
      chapters: workEl.querySelector('.chapters').textContent,
      kudos: parseInt(workEl.querySelector('.kudos').textContent),
      url: workEl.querySelector('.heading a').href,
      site: 'AO3'
    });
  });

  return results;
}
```

**Pros:**
- ✅ Works for any site
- ✅ No API key needed
- ✅ Full control over parsing
- ✅ Can extract data not available via API

**Cons:**
- ❌ Fragile (breaks when sites update HTML)
- ❌ Slower than APIs
- ❌ Must respect rate limits
- ❌ Requires maintenance

### Option 3: Hybrid Approach (Recommended)

**Use APIs where available, scraping where necessary:**

```javascript
const searchStrategies = {
  'archiveofourown.org': {
    method: 'scrape',  // No official API, but structured
    rateLimit: 2000,   // 2 seconds between requests
    parser: parseAO3Results
  },
  'fanfiction.net': {
    method: 'scrape',
    rateLimit: 2000,
    parser: parseFFNResults
  },
  'wattpad.com': {
    method: 'api',     // Official API
    rateLimit: 1000,
    apiKey: '<user-provided>',
    endpoint: 'https://api.wattpad.com/v4/stories'
  },
  // ... 115 more sites
};

async function unifiedSearch(query, filters) {
  // Search all enabled sites in parallel
  const promises = filters.sites.map(site =>
    searchSite(site, query, filters)
      .catch(err => {
        console.error(`Failed to search ${site}:`, err);
        return [];  // Graceful degradation
      })
  );

  const results = await Promise.all(promises);

  // Merge and deduplicate
  return mergeResults(results.flat());
}
```

---

## Better Filtering: What's Possible

### Current Filtering (Site-Dependent)

Most sites support:
- ✅ Fandom/category
- ✅ Rating (K, T, M, E)
- ⚠️ Word count (some sites)
- ⚠️ Completion status (some sites)
- ⚠️ Tags (AO3 only, really)
- ❌ Cross-site search
- ❌ Similarity/recommendations
- ❌ Advanced exclusions
- ❌ Reading time estimates
- ❌ Quality metrics

### What We Could Build

**1. Universal Filters (Across All Sites)**

```javascript
const advancedFilters = {
  // Basic filters
  query: "harry potter time travel",
  fandoms: ["Harry Potter", "Marvel"],

  // Word count
  minWords: 100000,
  maxWords: 500000,

  // Reading time (calculated)
  minReadingHours: 5,
  maxReadingHours: 20,

  // Status
  complete: true,
  lastUpdated: "within-6-months",

  // Ratings
  ratings: ["M", "E"],

  // Tags (include)
  includeTags: ["time travel", "alternate universe", "fix-it"],

  // Tags (exclude)
  excludeTags: ["romance", "slash", "character death"],

  // Relationships
  includeShips: ["Harry/Hermione"],
  excludeShips: ["Harry/Ginny"],

  // Quality metrics
  minKudos: 1000,        // AO3 only
  minReviews: 500,       // FFN only
  minRating: 4.0,        // Sites with ratings

  // Author filters
  excludeAuthors: ["author1", "author2"],
  favoriteAuthors: ["author3"],

  // Sites
  sites: ["AO3", "FFN", "RoyalRoad"],

  // Advanced
  language: "en",
  crossover: false,
  POV: "first-person",
  tense: "past",

  // Similarity
  similarTo: "https://archiveofourown.org/works/507461",

  // Recommendation engine
  basedOnMyHistory: true,
  recommendedBy: "ml-model"
};
```

**2. Intelligent Tag Mapping**

Different sites use different terminology:

```javascript
const tagMappings = {
  concept: "time travel",
  ao3: ["Time Travel", "Time Loop", "Temporal Manipulation"],
  ffn: ["Time-Travel", "Time"],
  wattpad: ["timetravel", "time travel", "timetraveler"],
  royalroad: ["Time Travel", "Regression"]
};

// When user searches for "time travel", query all variations
function mapTag(tag, site) {
  const mapping = tagMappings[tag];
  return mapping ? mapping[site] : [tag];
}
```

**3. Cross-Site Deduplication**

Same story posted to multiple sites:

```javascript
function deduplicateResults(results) {
  const seen = new Map();

  for (const result of results) {
    // Generate fingerprint
    const fingerprint = generateFingerprint(result);

    if (seen.has(fingerprint)) {
      // Same story, different site
      seen.get(fingerprint).mirrors.push({
        site: result.site,
        url: result.url
      });
    } else {
      result.mirrors = [{site: result.site, url: result.url}];
      seen.set(fingerprint, result);
    }
  }

  return Array.from(seen.values());
}

function generateFingerprint(story) {
  // Use title + author + approximate word count
  const normalized = `${story.title.toLowerCase()}-${story.author.toLowerCase()}-${Math.floor(story.words / 1000)}k`;
  return normalized.replace(/[^a-z0-9-]/g, '');
}
```

**4. Quality Scoring**

Unified quality metric across sites:

```javascript
function calculateQualityScore(story) {
  let score = 0;

  // Engagement metrics (normalized by site)
  if (story.site === 'AO3') {
    score += Math.log10(story.kudos + 1) * 20;
    score += Math.log10(story.bookmarks + 1) * 15;
    score += Math.log10(story.comments + 1) * 10;
  } else if (story.site === 'FFN') {
    score += Math.log10(story.reviews + 1) * 15;
    score += Math.log10(story.favorites + 1) * 20;
    score += Math.log10(story.follows + 1) * 10;
  }

  // Completion bonus
  if (story.complete) {
    score += 10;
  }

  // Length sweet spot (100k-300k words)
  if (story.words >= 100000 && story.words <= 300000) {
    score += 15;
  }

  // Recent updates
  const daysSinceUpdate = (Date.now() - story.updated) / (1000 * 60 * 60 * 24);
  if (daysSinceUpdate < 30) {
    score += 10;
  }

  // Ratio metrics (quality signals)
  const kudosToHits = story.kudos / (story.hits || 1);
  if (kudosToHits > 0.05) {  // 5% kudos rate is good
    score += 20;
  }

  return Math.min(score, 100);  // Cap at 100
}
```

**5. Recommendation Engine**

Based on stories you've liked:

```javascript
async function getRecommendations(likedStories, limit = 20) {
  // Extract features from liked stories
  const features = extractFeatures(likedStories);

  // Find similar stories
  const candidates = await searchByFeatures(features);

  // Score by similarity
  const scored = candidates.map(story => ({
    ...story,
    similarityScore: calculateSimilarity(features, story)
  }));

  // Sort and filter
  return scored
    .filter(s => s.similarityScore > 0.7)
    .sort((a, b) => b.similarityScore - a.similarityScore)
    .slice(0, limit);
}

function extractFeatures(stories) {
  // Build feature vector
  const tagFreq = {};
  const authorFreq = {};
  let avgWordCount = 0;
  let preferComplete = 0;

  stories.forEach(story => {
    // Tag preferences
    story.tags.forEach(tag => {
      tagFreq[tag] = (tagFreq[tag] || 0) + 1;
    });

    // Author preferences
    authorFreq[story.author] = (authorFreq[story.author] || 0) + 1;

    // Length preferences
    avgWordCount += story.words;

    // Completion preferences
    if (story.complete) preferComplete++;
  });

  avgWordCount /= stories.length;
  preferComplete /= stories.length;

  return {
    preferredTags: Object.entries(tagFreq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20)
      .map(([tag]) => tag),
    preferredAuthors: Object.keys(authorFreq),
    targetWordCount: avgWordCount,
    preferComplete: preferComplete > 0.7,
    fandoms: [...new Set(stories.map(s => s.fandom))]
  };
}
```

**6. Smart Exclusions**

Natural language exclusions:

```javascript
const excludePatterns = {
  "no romance": {
    excludeTags: ["Romance", "Romantic", "Love", "Dating", "Relationship"],
    excludeShips: "all"
  },
  "no character death": {
    excludeTags: ["Major Character Death", "Character Death", "Angst"],
    requireTags: ["Happy Ending", "Fluff"]
  },
  "no harems": {
    excludeTags: ["Harem", "Multiple Relationships", "Polyamory"],
  },
  "no bashing": {
    excludeTags: ["Ron Bashing", "Dumbledore Bashing", "Molly Bashing"]
  }
};

function processNaturalLanguage(query) {
  let filters = {...defaultFilters};

  for (const [phrase, exclusion] of Object.entries(excludePatterns)) {
    if (query.toLowerCase().includes(phrase)) {
      filters.excludeTags = [...(filters.excludeTags || []), ...exclusion.excludeTags];
      query = query.replace(new RegExp(phrase, 'gi'), '').trim();
    }
  }

  return {query, filters};
}
```

---

## Architecture: Unified Search Platform

### Option A: Browser Extension with Local Search

```
┌──────────────────────────────────────────────────┐
│  USER INTERFACE (Extension Popup)               │
│  ┌────────────────────────────────────────┐    │
│  │ Search: "harry potter time travel"    │    │
│  │                                        │    │
│  │ Filters:                               │    │
│  │ ☑ Complete only                       │    │
│  │ ☑ >100k words                         │    │
│  │ ☐ No romance                          │    │
│  │                                        │    │
│  │ Sites: ☑ AO3  ☑ FFN  ☑ RR           │    │
│  └────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  SEARCH ORCHESTRATOR (Background Script)         │
│  • Parallel searches across selected sites      │
│  • Rate limiting per site                       │
│  • Error handling & retries                     │
└──────────────────────────────────────────────────┘
                      ↓
         ┌────────────┴────────────┬────────────┐
         ↓                         ↓            ↓
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ AO3 ADAPTER   │    │ FFN ADAPTER    │    │ RR ADAPTER     │
│ • Parse query │    │ • Parse query  │    │ • Parse query  │
│ • Build URL   │    │ • Build URL    │    │ • Build URL    │
│ • Fetch HTML  │    │ • Fetch HTML   │    │ • Fetch HTML   │
│ • Parse results│   │ • Parse results│    │ • Parse results│
└────────────────┘    └────────────────┘    └────────────────┘
         ↓                         ↓            ↓
         └────────────┬────────────┴────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  RESULT AGGREGATOR                               │
│  • Merge results from all sites                 │
│  • Deduplicate cross-posts                      │
│  • Calculate quality scores                     │
│  • Apply filters                                │
│  • Sort by relevance/quality                    │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  RESULTS UI                                      │
│  ┌────────────────────────────────────────┐    │
│  │ [AO3] Story Title                      │    │
│  │ by Author Name                         │    │
│  │ 150k words • Complete • M             │    │
│  │ Quality: ★★★★☆ (85/100)              │    │
│  │ Tags: Time Travel, Fix-It, AU        │    │
│  │ [Download EPUB] [Read Online] [Save]  │    │
│  └────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

**Advantages:**
- ✅ Privacy-friendly (no third-party server)
- ✅ Fast (parallel requests)
- ✅ Works offline once results cached
- ✅ No server costs

**Disadvantages:**
- ❌ Limited by browser rate limits
- ❌ Can't pre-index content
- ❌ No server-side ML models
- ❌ Slower than indexed search

### Option B: Web-Based Search Engine (Ideal but Complex)

```
┌──────────────────────────────────────────────────┐
│  CRAWLER (Background Jobs)                       │
│  • Periodically crawl all 117 sites             │
│  • Extract metadata, tags, summaries            │
│  • Store in database                            │
│  • Update existing stories                      │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  DATABASE (PostgreSQL + ElasticSearch)           │
│  • 10M+ stories indexed                         │
│  • Full-text search                             │
│  • Tag index                                    │
│  • Author index                                 │
│  • Metadata (word count, status, etc.)         │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  SEARCH API                                      │
│  • Fast indexed queries (<100ms)                │
│  • Advanced filtering                           │
│  • Recommendation engine (ML)                   │
│  • Similarity search                            │
└──────────────────────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────┐
│  WEB UI / EXTENSION                              │
│  • Search interface                             │
│  • One-click download                           │
│  • Library management                           │
└──────────────────────────────────────────────────┘
```

**Advantages:**
- ✅ Instant search (pre-indexed)
- ✅ Advanced ML recommendations
- ✅ Can analyze entire corpus
- ✅ Cross-site analytics
- ✅ Trend detection
- ✅ Similar story suggestions

**Disadvantages:**
- ❌ Complex infrastructure
- ❌ Server costs
- ❌ Legal concerns (scraping at scale)
- ❌ Storage costs (millions of stories)
- ❌ Ongoing maintenance

### Option C: Hybrid (Recommended for MVP)

**Initial search:** Client-side (browser extension)
**Popular queries:** Cached results
**Recommendations:** Optional cloud service

```javascript
async function hybridSearch(query, filters) {
  // Check cache first
  const cached = await getCachedResults(query, filters);
  if (cached && cached.age < 24 * 60 * 60 * 1000) {
    return cached.results;
  }

  // Perform live search
  const results = await unifiedSearch(query, filters);

  // Cache for future users
  await cacheResults(query, filters, results);

  // Optionally: Send to cloud for ML training
  if (userOptIn) {
    await sendToRecommendationEngine(query, results);
  }

  return results;
}
```

---

## User Experience: Search Interface

### Example UI Flow

**1. Search Tab (New)**
```
┌─────────────────────────────────────────────────┐
│ FanFicFinder                            ⚙️ 👤  │
├─────────────────────────────────────────────────┤
│                                                 │
│  🔍 Search across all fanfic sites              │
│  ┌─────────────────────────────────────────┐   │
│  │ harry potter time travel               │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  ▼ Advanced Filters                            │
│  ┌─────────────────────────────────────────┐   │
│  │ Word Count: [100,000] to [500,000]     │   │
│  │ Status: ☑ Complete  ☐ WIP  ☐ Both     │   │
│  │ Rating: ☐ K  ☐ T  ☑ M  ☑ E           │   │
│  │                                         │   │
│  │ Include Tags:                           │   │
│  │ [time travel] [fix-it] [smart harry]  │   │
│  │                                         │   │
│  │ Exclude Tags:                           │   │
│  │ [romance] [slash] [harem]              │   │
│  │                                         │   │
│  │ Sites: ☑ AO3  ☑ FFN  ☑ RR  ☐ Wattpad │   │
│  │                                         │   │
│  │ Sort by: Quality ▼                     │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│            [Search All Sites]                   │
│                                                 │
└─────────────────────────────────────────────────┘
```

**2. Results Page**
```
┌─────────────────────────────────────────────────┐
│ Found 247 stories across 3 sites         ⬅️ Back │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ [AO3] Harry Potter and the Wastelands of Time│ │
│ │ by joe6991                                  │ │
│ │                                             │ │
│ │ Take the broken shards of one world that    │ │
│ │ has been destroyed, and place them in a     │ │
│ │ world where death is the victor...          │ │
│ │                                             │ │
│ │ 📊 Quality: ★★★★★ (96/100)                 │ │
│ │ 📖 291,329 words • 31 chapters • Complete   │ │
│ │ 💬 12,453 kudos • 2,891 bookmarks           │ │
│ │ 🏷️ Time Travel • Dimension Travel • Dark    │ │
│ │                                             │ │
│ │ [Download EPUB] [Read on AO3] [Add to Lib] │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ [FFN] Backwards Compatible                   │ │
│ │ by Ruskbyte                                 │ │
│ │                                             │ │
│ │ The Yondaime's jutsu didn't quite work as   │ │
│ │ intended, and Kyuubi found a little extra   │ │
│ │ help in the sealing. The result: Naruto is  │ │
│ │ no longer a normal shinobi...               │ │
│ │                                             │ │
│ │ 📊 Quality: ★★★★☆ (82/100)                 │ │
│ │ 📖 156,713 words • 24 chapters • Complete   │ │
│ │ 💬 3,247 reviews • 5,891 favorites          │ │
│ │ 🏷️ Time Travel • Fix-It • Adventure         │ │
│ │                                             │ │
│ │ [Download EPUB] [Read on FFN] [Add to Lib] │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│                 [Load More]                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

**3. Story Detail View**
```
┌─────────────────────────────────────────────────┐
│ Harry Potter and the Wastelands of Time  ⬅️ Back│
├─────────────────────────────────────────────────┤
│ by joe6991 • Archive of Our Own                 │
│                                                 │
│ ┌─────────────────────────────────────────────┐ │
│ │ Summary                                     │ │
│ │ Take the broken shards of one world that    │ │
│ │ has been destroyed, and place them in a     │ │
│ │ world where death is the victor, and watch  │ │
│ │ the Master of Death rise up...              │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 📊 Stats                                        │
│ • 291,329 words (12 hour read)                 │
│ • 31 chapters                                  │
│ • Published: 2008-07-11                        │
│ • Completed: 2009-02-15                        │
│ • Updated: 2009-02-15                          │
│                                                 │
│ 💬 Engagement                                   │
│ • 12,453 kudos                                 │
│ • 2,891 bookmarks                              │
│ • 967 comments                                 │
│ • Quality Score: 96/100                        │
│                                                 │
│ 🏷️ Tags                                         │
│ Time Travel • Dimension Travel • Dark          │
│ Master of Death • Post-Canon • Fix-It          │
│                                                 │
│ ⚠️ Warnings                                     │
│ Violence • Character Death                     │
│                                                 │
│ 📚 Also Available On                            │
│ • FanFiction.Net (same author)                 │
│ • SpaceBattles (different author - repost)     │
│                                                 │
│ 🤝 Similar Stories (based on ML)                │
│ • "Delenda Est" by Lord Silvere               │
│ • "Oh God Not Again!" by Sarah1281            │
│ • "Backwards with Purpose" by Deadwoodpecker  │
│                                                 │
│ [📥 Download EPUB] [📖 Read Online] [💾 Save] │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Technical Implementation Plan

### Phase 1: Basic Cross-Site Search (4 weeks)

**Week 1: Core Search Engine**
```javascript
// search-engine.js
class UnifiedSearchEngine {
  constructor() {
    this.adapters = new Map();
    this.registerAdapters();
  }

  registerAdapters() {
    this.adapters.set('AO3', new AO3Adapter());
    this.adapters.set('FFN', new FFNAdapter());
    this.adapters.set('RoyalRoad', new RoyalRoadAdapter());
    // Start with top 3, expand later
  }

  async search(query, filters) {
    const sites = filters.sites || Array.from(this.adapters.keys());

    // Parallel search across selected sites
    const promises = sites.map(async (site) => {
      const adapter = this.adapters.get(site);
      try {
        return await adapter.search(query, filters);
      } catch (error) {
        console.error(`Search failed for ${site}:`, error);
        return [];
      }
    });

    const results = await Promise.all(promises);
    return this.mergeAndRank(results.flat());
  }

  mergeAndRank(results) {
    // Deduplicate
    const deduplicated = this.deduplicate(results);

    // Calculate quality scores
    deduplicated.forEach(r => {
      r.qualityScore = this.calculateQuality(r);
    });

    // Sort by quality
    return deduplicated.sort((a, b) => b.qualityScore - a.qualityScore);
  }

  deduplicate(results) {
    // Implementation from earlier
  }

  calculateQuality(story) {
    // Implementation from earlier
  }
}
```

**Week 2: Site Adapters**
```javascript
// adapters/ao3.js
class AO3Adapter {
  async search(query, filters) {
    const url = this.buildSearchURL(query, filters);
    const html = await this.fetch(url);
    return this.parseResults(html);
  }

  buildSearchURL(query, filters) {
    const params = new URLSearchParams();
    params.set('work_search[query]', query);

    if (filters.minWords) {
      params.set('work_search[word_count]', `>${filters.minWords}`);
    }

    if (filters.complete) {
      params.set('work_search[complete]', 'true');
    }

    if (filters.ratings) {
      const ratingIds = this.mapRatings(filters.ratings);
      params.set('work_search[rating_ids]', ratingIds.join(','));
    }

    return `https://archiveofourown.org/works/search?${params}`;
  }

  async fetch(url) {
    const response = await fetch(url);
    return response.text();
  }

  parseResults(html) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    const works = doc.querySelectorAll('.work');
    return Array.from(works).map(work => this.parseWork(work));
  }

  parseWork(element) {
    return {
      site: 'AO3',
      title: element.querySelector('.heading a').textContent.trim(),
      author: element.querySelector('.authors a')?.textContent.trim() || 'Anonymous',
      summary: element.querySelector('.summary')?.textContent.trim() || '',
      url: 'https://archiveofourown.org' + element.querySelector('.heading a').getAttribute('href'),
      words: this.parseNumber(element.querySelector('.words')?.textContent),
      chapters: element.querySelector('.chapters')?.textContent.trim(),
      complete: element.querySelector('.complete-yes') !== null,
      tags: Array.from(element.querySelectorAll('.tags li')).map(t => t.textContent.trim()),
      kudos: this.parseNumber(element.querySelector('.kudos')?.textContent),
      bookmarks: this.parseNumber(element.querySelector('.bookmarks')?.textContent),
      comments: this.parseNumber(element.querySelector('.comments')?.textContent),
      rating: element.querySelector('.rating')?.textContent.trim(),
      published: element.querySelector('.datetime')?.textContent.trim(),
    };
  }

  parseNumber(text) {
    if (!text) return 0;
    return parseInt(text.replace(/,/g, ''), 10) || 0;
  }

  mapRatings(ratings) {
    const map = {
      'K': '10',   // General Audiences
      'T': '11',   // Teen
      'M': '12',   // Mature
      'E': '13'    // Explicit
    };
    return ratings.map(r => map[r]).filter(Boolean);
  }
}
```

**Week 3: UI Implementation**
- Search interface
- Results display
- Filter controls
- Download integration

**Week 4: Testing & Polish**
- Cross-browser testing
- Error handling
- Rate limiting
- Performance optimization

### Phase 2: Advanced Filtering (2 weeks)

**Week 5: Smart Filters**
- Tag mapping across sites
- Natural language exclusions
- Quality scoring
- Deduplication

**Week 6: UI Enhancements**
- Advanced filter UI
- Sort options
- Save searches
- Export results

### Phase 3: Recommendations (4 weeks)

**Week 7-8: Similarity Engine**
- Feature extraction
- Similarity scoring
- "Similar stories" feature
- Tag-based recommendations

**Week 9-10: ML Recommendations**
- User history tracking
- Collaborative filtering
- Personalized recommendations
- A/B testing

---

## Competitive Advantage Analysis

### What Exists Today

**1. Site-specific search:**
- AO3's search (good but slow)
- FFN's search (poor)
- Wattpad's search (algorithm-driven, not user-focused)

**2. Third-party tools:**
- FicHub (download only, no search)
- Various Discord bots (limited)
- Subreddit recommendation threads (manual)

**3. What DOESN'T exist:**
- ❌ Unified cross-site search
- ❌ Advanced filtering across sites
- ❌ Quality scoring system
- ❌ ML-based recommendations
- ❌ One-click download from search results

### What We Could Build

**Unique Value Propositions:**

1. **Search once, find everywhere**
   - "I want Harry Potter time travel fic"
   - Search returns results from AO3, FFN, RR, etc.
   - No need to visit each site

2. **Better filtering than any site provides**
   - "Over 100k words, complete, no romance, similar to X"
   - Filters that work across all sites
   - Natural language exclusions

3. **Quality scoring**
   - Normalized quality metrics
   - "Show me the GOOD stuff"
   - Filter out low-quality content

4. **Discovery engine**
   - "Similar to stories you liked"
   - Cross-site deduplication
   - Trending stories across platforms

5. **Integrated workflow**
   - Search → Filter → Download → Read
   - All in one tool
   - No site-hopping

### Market Potential

**Target users:**
- 100M+ fanfic readers worldwide
- 10M+ active monthly readers (conservative)
- 1M+ power readers (read 10+ stories/month)

**Willingness to pay:**
- Free tier: Basic search + download
- Premium ($5/month): Advanced filters, recommendations, unlimited searches
- Power tier ($10/month): ML recommendations, reading analytics, cloud library

**Revenue potential:**
- 10,000 premium users × $5/month = $50k/month
- 1,000 power users × $10/month = $10k/month
- **Total: $60k/month = $720k/year**

(Conservative estimates assuming 0.1% conversion)

**Or:** Keep it free and build community (like AO3 model)

---

## Legal & Ethical Considerations

### Is This Legal?

**Web Scraping Legality:**
- ✅ Generally legal in US (hiQ Labs v. LinkedIn precedent)
- ✅ Public data that's freely accessible
- ⚠️ Must respect robots.txt
- ⚠️ Must respect rate limits
- ⚠️ Can't bypass paywalls/authentication

**Terms of Service:**
- Some sites prohibit automated access
- AO3: Generally permissive (has export feature)
- FFN: TOS prohibits bots (but widely ignored)
- Wattpad: Has official API (use that)

**Best Practices:**
- Respectful rate limiting (1-2 req/sec max)
- Clear user agent identification
- Caching to reduce requests
- Offer value to the ecosystem
- Consider asking for permission

### Ethical Considerations

**1. Author Rights:**
- We're not hosting content (just linking)
- Authors posted publicly on these sites
- We're making discovery easier
- Could add "request removal" feature

**2. Site Impact:**
- Rate limiting prevents overload
- Caching reduces requests
- Could drive traffic TO sites
- Could offer API partnership

**3. User Privacy:**
- No tracking unless opted in
- Local-first approach
- Encrypted cloud sync (if offered)
- Transparent data handling

---

## Recommendation

### YES - Build Unified Search! 🎯

**This is actually MORE valuable than just a download tool.**

**Why:**
1. **Solves real pain point:** Finding good stories across sites is hard
2. **No good alternative exists:** Nothing offers comprehensive cross-site search
3. **Natural workflow:** Search → Download → Read (all integrated)
4. **Huge market:** 100M+ potential users
5. **Technically feasible:** Can start simple, expand over time
6. **Competitive moat:** First-mover advantage, network effects

### Recommended Approach

**Phase 1: Browser Extension with Search (6-8 weeks)**
- Search interface
- Top 5 sites (AO3, FFN, Wattpad, RR, SB)
- Basic filters (word count, complete, rating)
- Quality scoring
- One-click download
- Local library

**Phase 2: Advanced Features (+4 weeks)**
- All 117 sites
- Advanced filtering
- Tag mapping
- Deduplication
- Saved searches

**Phase 3: Recommendations (+6 weeks)**
- Similarity search
- ML recommendations
- Personalized suggestions
- Reading analytics

**Phase 4: Optional Cloud Service**
- Cached popular searches
- ML model training
- Cross-device sync
- Premium features

---

## Example: Full Workflow

**User wants:** Harry Potter time travel fix-it, long, complete, no romance

**Current approach:**
1. Go to AO3
2. Search "harry potter time travel"
3. Click through 10 pages
4. Check word count on each
5. Check completion status
6. Read tags to verify no romance
7. Repeat on FFN
8. Repeat on SpaceBattles
9. **Total time: 2+ hours**

**With unified search:**
1. Open extension
2. Search "harry potter time travel"
3. Filter: >100k words, complete, exclude "romance"
4. See results from ALL sites, sorted by quality
5. Click "Download" on top result
6. **Total time: 2 minutes**

**60x faster, better results.**

---

## Next Steps

Want me to:

1. **Build a proof-of-concept search extension?**
   - Search AO3 + FFN + RR
   - Basic filtering
   - Quality scoring
   - Working prototype in 1-2 weeks

2. **Create detailed technical spec?**
   - Full architecture
   - API documentation
   - Database schema (if cloud)
   - Implementation guide

3. **Analyze legal risks more deeply?**
   - TOS review for top sites
   - Legal consultation recommendations
   - Risk mitigation strategies

This could be a game-changer for fanfic discovery. The download feature becomes just one part of a much more valuable search & discovery platform.
