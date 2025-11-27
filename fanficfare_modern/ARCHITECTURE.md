# Architecture Overview

## System Design

```
                    ┌─────────────────────────────┐
                    │     User Request (URL)      │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │    Smart Adapter Registry    │
                    │  (Intelligent Fallback)      │
                    └──────────────┬──────────────┘
                                   │
                 ┌─────────────────┼─────────────────┐
                 │                 │                 │
                 ▼                 ▼                 ▼
      ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐
      │ Custom Adapters  │  │  Platform    │  │ Config-Driven│
      │  (~15-20 sites)  │  │  Adapters    │  │  Adapters    │
      │                  │  │ (~10-15)     │  │ (~30-40)     │
      │ • Wattpad        │  │              │  │              │
      │ • FFNet          │  │ • eFiction   │  │ • YAML       │
      │ • Complex sites  │  │ • XenForo    │  │   configs    │
      │                  │  │ • WordPress  │  │ • Selectors  │
      └──────────────────┘  └──────┬───────┘  └──────┬───────┘
                                   │                 │
                                   └────────┬────────┘
                                            ▼
                              ┌─────────────────────────┐
                              │  Platform Detector      │
                              │                         │
                              │  • HTML signatures      │
                              │  • URL patterns         │
                              │  • Meta tags            │
                              └─────────────────────────┘
```

## Data Flow

```
1. URL Request
   │
   ├─→ Extract domain
   │
   ├─→ Check cache
   │    └─→ Found? Return cached adapter
   │
   ├─→ Check custom adapters (exact match)
   │    └─→ Found? Return custom adapter
   │
   ├─→ Fetch HTML (if needed)
   │
   ├─→ Detect platform
   │    ├─→ Check HTML signatures
   │    ├─→ Check URL patterns
   │    └─→ Check meta tags
   │
   ├─→ Platform detected?
   │    └─→ Yes: Return platform adapter
   │
   ├─→ Check config directory
   │    └─→ Found YAML? Return config adapter
   │
   └─→ No adapter found (error or fallback)

2. Extract Metadata
   │
   ├─→ Parse HTML with BeautifulSoup
   ├─→ Apply selectors (CSS/XPath)
   ├─→ Extract:
   │    ├─→ Title, Author, Summary
   │    ├─→ Chapters list
   │    ├─→ Metadata (rating, tags, etc.)
   │    └─→ Stats (words, kudos, etc.)
   │
   └─→ Return Story object (Pydantic model)

3. Get Chapter Content
   │
   ├─→ Fetch chapter URL
   ├─→ Parse HTML
   ├─→ Extract content (CSS selector)
   ├─→ Clean HTML
   └─→ Return chapter content
```

## Component Breakdown

### 1. Models (`models.py`)
**Purpose**: Type-safe data structures

```python
Story (Pydantic Model)
├── story_id, title, author
├── summary, rating, status
├── chapters: List[Chapter]
├── tags, genre, characters
├── word_count, kudos, etc.
└── Validation & serialization

Chapter (Pydantic Model)
├── number, title, url
├── content (optional)
└── Validation

SiteConfig (Pydantic Model)
├── name, domains
├── story_url_pattern
├── selectors (dict)
└── options
```

### 2. Platform Detector (`core/platform_detector.py`)
**Purpose**: Auto-detect site platform

```python
PlatformDetector
├── PLATFORMS (signatures)
│   ├── eFiction
│   ├── XenForo
│   ├── WordPress
│   └── ... 10+ more
│
├── detect(html, url) → platform_name
│   ├── Check HTML signatures
│   ├── Check meta tags
│   ├── Check URL patterns
│   └── Score & return best match
│
└── detect_from_url(url) → platform_name
    └── Quick detection (no HTTP needed)
```

### 3. Platform Adapters (`platform_adapters/`)
**Purpose**: Generic adapters for common platforms

```python
EFictionAdapter
├── can_handle(url)
├── extract_story_id(url)
├── extract_metadata(html, url) → Story
│   ├── Parse title, author, summary
│   ├── Extract chapters
│   └── Parse dates, ratings
└── extract_chapter_content(html) → str

XenForoAdapter
├── can_handle(url)
├── extract_thread_id(url)
├── extract_metadata(html, url) → Story
│   ├── Parse thread title
│   ├── Extract threadmarks
│   └── Get author from first post
└── extract_chapter_content(html) → str
```

### 4. Config-Driven Adapter (`config_adapters/config_driven.py`)
**Purpose**: YAML-based adapter

```python
ConfigDrivenAdapter
├── __init__(config: SiteConfig)
├── from_yaml(yaml_path) → ConfigDrivenAdapter
├── from_domain(domain, config_dir) → ConfigDrivenAdapter
│
├── extract_metadata(html, url) → Story
│   ├── Apply selectors from config
│   ├── Extract using CSS/XPath
│   └── Build Story object
│
└── extract_chapter_content(html) → str
    └── Apply content selector
```

### 5. Smart Registry (`core/registry.py`)
**Purpose**: Intelligent adapter selection

```python
AdapterRegistry
├── custom_adapters: Dict[domain, adapter_class]
├── platform_adapters: Dict[platform, adapter_class]
├── config_dir: Path
├── detector: PlatformDetector
│
├── register_custom_adapter(domain, adapter_class)
├── get_adapter(url, html?) → adapter
│   │
│   ├─→ Tier 1: Custom adapter (domain match)
│   ├─→ Tier 2: Platform adapter (auto-detect)
│   ├─→ Tier 3: Config adapter (YAML)
│   └─→ Tier 4: None (no match)
│
└── get_stats() → Dict[str, int]

UnifiedAdapter (High-level wrapper)
├── get_story(url, html?) → Story
└── get_chapter(chapter_url) → str
```

## Key Design Patterns

### 1. Strategy Pattern
Different adapters (custom, platform, config) but same interface

### 2. Factory Pattern
Registry creates appropriate adapter based on URL

### 3. Chain of Responsibility
Fallback chain: custom → platform → config → error

### 4. Template Method
Base adapters define template, subclasses override specifics

### 5. Registry Pattern
Central registry for adapter discovery and caching

## Performance Optimizations

### 1. Caching
```python
# Domain → adapter mapping cached
_domain_cache: Dict[str, tuple]
```

### 2. Lazy Loading
```python
# Configs loaded on-demand
from_domain() loads only needed config
```

### 3. Quick Detection
```python
# URL-only detection (no HTTP request)
detect_from_url() for fast routing
```

### 4. Selector Optimization
```python
# CSS selectors (fast)
vs. XPath (slower)
vs. regex (slowest)
```

## Extensibility Points

### 1. Add Platform Adapter
```python
# platform_adapters/newplatform.py
class NewPlatformAdapter:
    def can_handle(url): ...
    def extract_metadata(html, url): ...

# Register in registry.py
platform_adapters['newplatform'] = NewPlatformAdapter
```

### 2. Add Site Config
```yaml
# site_configs/newsite.yaml
name: "New Site"
domains: [newsite.com]
selectors: {...}
```

### 3. Add Custom Adapter
```python
# Register at runtime
registry.register_custom_adapter('unique.com', UniqueAdapter)
```

## Migration Path

```
Phase 1: Coexistence
├── Old adapters still work
├── New system in parallel
└── No breaking changes

Phase 2: Gradual Migration
├── Migrate platform-based (automatic)
├── Migrate simple (YAML)
├── Keep complex (custom)
└── Test each migration

Phase 3: Full Migration
├── All sites on new system
├── Old system deprecated
└── Remove old code
```

## Testing Strategy

```
Unit Tests
├── test_platform_detector.py
│   └── Test each platform signature
├── test_config_driven.py
│   └── Test YAML loading & extraction
└── test_models.py
    └── Test Pydantic validation

Integration Tests
├── test_real_sites.py
│   └── Test against real HTML (fixtures)
└── test_registry.py
    └── Test adapter selection logic

End-to-End Tests
└── test_complete_workflow.py
    └── URL → Story → Chapter → EPUB
```

## Metrics & Monitoring

```python
# Track adapter usage
metrics = {
    'custom_adapter_hits': Counter,
    'platform_adapter_hits': Counter,
    'config_adapter_hits': Counter,
    'detection_time': Histogram,
    'extraction_time': Histogram,
}

# Log adapter selection
logger.info(f"Selected {adapter_type} for {domain}")
```

## Future Enhancements

1. **AI-Powered Selector Discovery**
   - Use LLM to auto-generate selectors
   - Cache discovered selectors

2. **Visual Config Builder**
   - Web UI to create configs
   - Click elements to generate selectors

3. **Automatic Config Updates**
   - Detect site changes
   - Auto-update selectors

4. **Community Configs**
   - Central repository
   - Auto-download configs

5. **Performance Monitoring**
   - Track extraction success rates
   - Alert on failures
   - A/B test adapters
