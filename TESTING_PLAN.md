# FanFicFare Testing Plan

## Current Status

✅ **CLI confirmed working** - User verified the original CLI works
⚠️ **No test suite** - Need comprehensive testing before modernization
🎯 **Goal:** >80% test coverage with reliable CI/CD

---

## Testing Strategy

### 1. Test Pyramid

```
        /\
       /  \  E2E Tests (Few)
      /____\
     /      \  Integration Tests (Some)
    /________\
   /          \  Unit Tests (Many)
  /______________\
```

**Unit Tests (70%):**
- Individual functions and classes
- Fast, isolated, deterministic
- Mock external dependencies

**Integration Tests (25%):**
- Adapter tests with real HTML fixtures
- EPUB generation
- Update logic

**E2E Tests (5%):**
- Full download workflow
- Real site tests (fragile, run manually)

---

## Testing Infrastructure Setup

### Step 1: Install Testing Dependencies

```bash
# pyproject.toml or requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
pytest-asyncio>=0.21.0  # if using async
responses>=0.23.0       # HTTP mocking
beautifulsoup4>=4.12.0  # Already have this
freezegun>=1.2.0        # Time mocking
faker>=19.0.0           # Test data generation
```

```bash
pip install -e ".[dev]"
```

### Step 2: Project Structure

```
FanFicFare/
├── fanficfare/          # Source code
│   ├── adapters/
│   ├── writers/
│   └── ...
├── tests/               # NEW: Test directory
│   ├── __init__.py
│   ├── conftest.py      # Pytest configuration & fixtures
│   ├── fixtures/        # Test data (HTML, EPUBs)
│   │   ├── ao3/
│   │   │   ├── work_page.html
│   │   │   ├── chapter_page.html
│   │   │   └── search_results.html
│   │   ├── ffn/
│   │   └── ...
│   ├── unit/            # Unit tests
│   │   ├── test_adapters/
│   │   ├── test_writers/
│   │   └── test_utils/
│   ├── integration/     # Integration tests
│   │   ├── test_download_flow.py
│   │   └── test_update_flow.py
│   └── e2e/            # End-to-end tests
│       └── test_real_downloads.py
├── pytest.ini          # Pytest config
└── .coveragerc         # Coverage config
```

### Step 3: Pytest Configuration

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Useful options
addopts =
    -v                    # Verbose
    --strict-markers      # Error on unknown markers
    --cov=fanficfare      # Coverage
    --cov-report=html     # HTML coverage report
    --cov-report=term     # Terminal coverage
    --cov-fail-under=80   # Fail if <80% coverage

markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, uses fixtures)
    e2e: End-to-end tests (slow, hits real sites)
    slow: Slow tests (skip in CI)
```

**.coveragerc:**
```ini
[run]
source = fanficfare
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## Test Categories

### 1. Unit Tests (Priority: HIGH)

#### A. Adapter Tests

**What to test:**
- URL detection
- Metadata extraction
- Chapter list parsing
- Content cleaning

**Example: test_adapter_ao3.py**

```python
import pytest
from fanficfare.adapters import adapter_archiveofourownorg as ao3
from pathlib import Path

@pytest.fixture
def ao3_work_html():
    """Load fixture HTML for AO3 work page"""
    fixture_path = Path(__file__).parent.parent / 'fixtures' / 'ao3' / 'work_page.html'
    return fixture_path.read_text()

@pytest.fixture
def ao3_adapter(config):
    """Create AO3 adapter instance"""
    url = "https://archiveofourown.org/works/507461"
    return ao3.ArchiveOfOurOwnOrgAdapter(config, url)

class TestAO3Adapter:
    """Test AO3 adapter functionality"""

    def test_site_detection(self):
        """Test that AO3 URLs are correctly detected"""
        assert ao3.ArchiveOfOurOwnOrgAdapter.getSiteDomain() == 'archiveofourown.org'

        valid_urls = [
            'https://archiveofourown.org/works/507461',
            'http://archiveofourown.org/works/507461',
            'https://ao3.org/works/507461',
        ]
        for url in valid_urls:
            assert ao3.ArchiveOfOurOwnOrgAdapter.getSiteDomain() in url

    def test_work_id_extraction(self, ao3_adapter):
        """Test extracting work ID from URL"""
        assert ao3_adapter.story.getMetadata('storyId') == '507461'

    def test_metadata_extraction(self, ao3_adapter, ao3_work_html, mocker):
        """Test extracting story metadata from HTML"""
        # Mock the HTTP request
        mocker.patch.object(ao3_adapter, '_fetchUrl', return_value=ao3_work_html)

        # Extract metadata
        ao3_adapter.extractChapterUrlsAndMetadata()

        # Verify extracted data
        assert ao3_adapter.story.getMetadata('title') == 'The Road to Erebor'
        assert ao3_adapter.story.getMetadata('author') == 'Kaykhosrow'
        assert ao3_adapter.story.getMetadata('rating') == 'Teen And Up Audiences'
        assert 'Time Travel' in ao3_adapter.story.getMetadata('genre')
        assert int(ao3_adapter.story.getMetadata('numWords')) > 0

    def test_chapter_list_extraction(self, ao3_adapter, ao3_work_html, mocker):
        """Test extracting chapter list"""
        mocker.patch.object(ao3_adapter, '_fetchUrl', return_value=ao3_work_html)

        ao3_adapter.extractChapterUrlsAndMetadata()

        chapters = ao3_adapter.getChapterUrls()
        assert len(chapters) > 0
        assert all('url' in ch for ch in chapters)

    def test_invalid_url(self, config):
        """Test that invalid URLs raise appropriate errors"""
        with pytest.raises(Exception):  # Or specific exception
            ao3.ArchiveOfOurOwnOrgAdapter(config, "https://invalid.com/works/123")

    def test_deleted_work(self, ao3_adapter, mocker):
        """Test handling of deleted works"""
        deleted_html = "<html><body>This work has been deleted</body></html>"
        mocker.patch.object(ao3_adapter, '_fetchUrl', return_value=deleted_html)

        with pytest.raises(Exception):  # Or specific exception
            ao3_adapter.extractChapterUrlsAndMetadata()
```

#### B. Writer Tests

**test_epub_writer.py:**

```python
import pytest
from fanficfare.writers import epub
import zipfile

class TestEPUBWriter:
    """Test EPUB generation"""

    @pytest.fixture
    def story_data(self):
        """Create mock story data"""
        # Return mock Story object with metadata
        pass

    def test_epub_structure(self, story_data, tmp_path):
        """Test that generated EPUB has correct structure"""
        output_path = tmp_path / "test_story.epub"

        writer = epub.EPUBWriter(story_data)
        writer.writeStory(str(output_path))

        # Verify EPUB is valid ZIP
        assert zipfile.is_zipfile(output_path)

        with zipfile.ZipFile(output_path) as zf:
            # Check required files
            assert 'mimetype' in zf.namelist()
            assert 'META-INF/container.xml' in zf.namelist()
            # content.opf should exist
            assert any('content.opf' in name for name in zf.namelist())

    def test_metadata_inclusion(self, story_data, tmp_path):
        """Test that metadata is correctly written to EPUB"""
        output_path = tmp_path / "test_story.epub"

        writer = epub.EPUBWriter(story_data)
        writer.writeStory(str(output_path))

        # Read and verify metadata from content.opf
        with zipfile.ZipFile(output_path) as zf:
            opf_path = [n for n in zf.namelist() if 'content.opf' in n][0]
            opf_content = zf.read(opf_path).decode('utf-8')

            assert '<dc:title>' in opf_content
            assert '<dc:creator>' in opf_content
            # Verify FanFicFare custom metadata
            assert 'storyId' in opf_content
```

#### C. Utility Tests

**test_configuration.py:**

```python
import pytest
from fanficfare import configuration

class TestConfiguration:
    """Test configuration management"""

    def test_default_config(self):
        """Test default configuration values"""
        config = configuration.get_config()
        assert config is not None
        # Test specific defaults
        assert config.getConfig('generate_cover_settings', 'use_default_cover') == 'true'

    def test_config_override(self):
        """Test that configuration can be overridden"""
        config = configuration.get_config()
        config.setConfig('section', 'key', 'value')
        assert config.getConfig('section', 'key') == 'value'

    def test_personal_ini_loading(self, tmp_path):
        """Test loading personal.ini"""
        ini_path = tmp_path / 'personal.ini'
        ini_path.write_text('[defaults]\nuse_ssl_unverified_context=true')

        config = configuration.get_config(str(ini_path))
        assert config.getConfig('defaults', 'use_ssl_unverified_context') == 'true'
```

### 2. Integration Tests (Priority: MEDIUM)

#### test_download_flow.py

```python
import pytest
from fanficfare import adapters, writers
from pathlib import Path

@pytest.mark.integration
class TestDownloadFlow:
    """Test complete download workflow"""

    @pytest.fixture
    def ao3_fixture_adapter(self, mocker):
        """Create adapter that uses fixture HTML instead of real requests"""
        # Load all necessary fixture files
        work_html = (Path(__file__).parent.parent / 'fixtures' / 'ao3' / 'work_page.html').read_text()
        chapter1_html = (Path(__file__).parent.parent / 'fixtures' / 'ao3' / 'chapter1.html').read_text()

        def mock_fetch(url):
            if 'chapters' in url:
                return chapter1_html
            return work_html

        adapter = adapters.getAdapter(None, "https://archiveofourown.org/works/507461")
        mocker.patch.object(adapter, '_fetchUrl', side_effect=mock_fetch)
        return adapter

    def test_full_download(self, ao3_fixture_adapter, tmp_path):
        """Test downloading a complete story to EPUB"""
        output_path = tmp_path / "story.epub"

        # Extract metadata
        ao3_fixture_adapter.extractChapterUrlsAndMetadata()

        # Download chapters
        ao3_fixture_adapter.getStory()

        # Write EPUB
        writer = writers.getWriter('epub', ao3_fixture_adapter)
        writer.writeStory(str(output_path))

        # Verify
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_update_existing(self, ao3_fixture_adapter, tmp_path):
        """Test updating an existing EPUB with new chapters"""
        # First create initial EPUB with 10 chapters
        # Then create updated version with 15 chapters
        # Verify only new chapters downloaded
        pass
```

#### test_performance_optimizations.py

```python
import pytest
import time
from fanficfare_performance.core import (
    html_parser,
    dns_cache,
    parallel_downloader
)

@pytest.mark.integration
class TestPerformanceOptimizations:
    """Test that performance optimizations work correctly"""

    def test_lxml_parser_faster(self):
        """Test that lxml is faster than html5lib"""
        html = "<html><body><p>Test</p></body></html>" * 1000

        # Measure html5lib
        start = time.time()
        for _ in range(10):
            soup = BeautifulSoup(html, 'html5lib')
        html5lib_time = time.time() - start

        # Measure lxml
        start = time.time()
        for _ in range(10):
            soup = BeautifulSoup(html, 'lxml')
        lxml_time = time.time() - start

        # lxml should be significantly faster
        assert lxml_time < html5lib_time * 0.5  # At least 2x faster

    def test_dns_cache_works(self):
        """Test DNS caching reduces lookup time"""
        dns_cache.enable_dns_cache()

        import socket

        # First lookup (cache miss)
        start = time.time()
        socket.getaddrinfo('archiveofourown.org', 443)
        first_lookup = time.time() - start

        # Second lookup (cache hit)
        start = time.time()
        socket.getaddrinfo('archiveofourown.org', 443)
        second_lookup = time.time() - start

        # Cached lookup should be much faster
        assert second_lookup < first_lookup * 0.1  # At least 10x faster

        dns_cache.disable_dns_cache()
```

### 3. End-to-End Tests (Priority: LOW)

**These are fragile and should run manually or in separate CI job**

```python
import pytest

@pytest.mark.e2e
@pytest.mark.slow
class TestRealDownloads:
    """Test downloading from real sites (fragile, run manually)"""

    def test_download_ao3_oneshot(self, tmp_path):
        """Test downloading a real AO3 one-shot"""
        url = "https://archiveofourown.org/works/507461"  # Known stable fic
        output = tmp_path / "story.epub"

        # Use actual CLI
        import subprocess
        result = subprocess.run(
            ['fanficfare', '-o', str(output), url],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert output.exists()

    @pytest.mark.skip(reason="FFN is flaky")
    def test_download_ffn_multichapter(self, tmp_path):
        """Test downloading a real FFN multi-chapter story"""
        pass
```

---

## Fixtures Strategy

### Collecting Fixtures

**Script to save test fixtures:**

```python
# scripts/save_fixtures.py
"""
Save HTML fixtures for testing.
Run manually to update test fixtures when sites change.
"""

import requests
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / 'tests' / 'fixtures'

FIXTURE_URLS = {
    'ao3': {
        'work_page.html': 'https://archiveofourown.org/works/507461?view_adult=true',
        'chapter1.html': 'https://archiveofourown.org/works/507461/chapters/654321',
        'multichapter.html': 'https://archiveofourown.org/works/123456?view_adult=true',
    },
    'ffn': {
        'story_page.html': 'https://www.fanfiction.net/s/4536005/1/',
        'chapter2.html': 'https://www.fanfiction.net/s/4536005/2/',
    }
}

def save_fixtures():
    for site, pages in FIXTURE_URLS.items():
        site_dir = FIXTURES_DIR / site
        site_dir.mkdir(parents=True, exist_ok=True)

        for filename, url in pages.items():
            print(f"Fetching {url}...")
            response = requests.get(url)

            output_path = site_dir / filename
            output_path.write_text(response.text)
            print(f"  Saved to {output_path}")

if __name__ == '__main__':
    save_fixtures()
```

### Shared Fixtures

**tests/conftest.py:**

```python
import pytest
from fanficfare import configuration
from pathlib import Path

@pytest.fixture
def config():
    """Provide test configuration"""
    cfg = configuration.Configuration(['test'], 'epub')
    cfg.setConfig('defaults', 'use_ssl_unverified_context', 'false')
    return cfg

@pytest.fixture
def fixtures_dir():
    """Path to fixtures directory"""
    return Path(__file__).parent / 'fixtures'

@pytest.fixture
def ao3_work_html(fixtures_dir):
    """Load AO3 work page fixture"""
    return (fixtures_dir / 'ao3' / 'work_page.html').read_text()

@pytest.fixture
def ffn_story_html(fixtures_dir):
    """Load FFN story page fixture"""
    return (fixtures_dir / 'ffn' / 'story_page.html').read_text()

@pytest.fixture
def tmp_epub(tmp_path):
    """Provide temporary EPUB path"""
    return tmp_path / "test_story.epub"
```

---

## CI/CD Setup

### GitHub Actions Workflow

**.github/workflows/test.yml:**

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.8', '3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run tests
      run: |
        pytest tests/unit tests/integration -v --cov --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install ruff mypy

    - name: Run ruff
      run: ruff check fanficfare/

    - name: Run mypy
      run: mypy fanficfare/
```

---

## Implementation Timeline

### Week 1: Setup

- [x] Document testing plan
- [ ] Install pytest and dependencies
- [ ] Set up project structure (tests/ directory)
- [ ] Configure pytest.ini and .coveragerc
- [ ] Set up GitHub Actions

### Week 2-3: Unit Tests

- [ ] Write adapter tests (AO3, FFN, top 5 sites)
- [ ] Write writer tests (EPUB generation)
- [ ] Write utility tests (config, helpers)
- [ ] Collect fixtures from real sites
- [ ] Target: 60% coverage

### Week 4: Integration Tests

- [ ] Write download flow tests
- [ ] Write update flow tests
- [ ] Test performance optimizations
- [ ] Target: 75% coverage

### Week 5: Polish & Documentation

- [ ] Write remaining tests for edge cases
- [ ] Document how to run tests
- [ ] Document how to add new tests
- [ ] Set up coverage reporting
- [ ] Target: 80%+ coverage

### Week 6: CI/CD & Release

- [ ] Finalize GitHub Actions
- [ ] Set up automated releases
- [ ] Tag v1.0.0 release
- [ ] Announce to community

---

## Running Tests

### Local Development

```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest tests/unit

# Run specific test file
pytest tests/unit/test_adapters/test_ao3.py

# Run specific test
pytest tests/unit/test_adapters/test_ao3.py::TestAO3Adapter::test_metadata_extraction

# Run with coverage
pytest --cov

# Run and generate HTML coverage report
pytest --cov --cov-report=html
# Then open htmlcov/index.html

# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

### CI/CD

```bash
# What runs in CI
pytest tests/unit tests/integration -v --cov --cov-fail-under=80
```

---

## Coverage Goals

### Target Coverage by Module

- **Adapters:** 70%+ (hard to test all edge cases)
- **Writers:** 90%+ (critical path)
- **Configuration:** 80%+
- **Utilities:** 85%+
- **Overall:** 80%+

### Areas We Can Skip

- Legacy code scheduled for removal
- Third-party integrations (Calibre plugin)
- GUI code (if any)
- Debug utilities

---

## Next Steps

1. **Immediate:** Set up pytest infrastructure
2. **This Week:** Write first adapter tests (AO3)
3. **Next Week:** Expand to more adapters
4. **Week 3:** Integration tests
5. **Week 4-5:** Polish to 80% coverage
6. **Week 6:** Release with confidence!

Once testing is solid, we can confidently:
- Refactor code (tests catch regressions)
- Add type hints (tests verify behavior)
- Optimize performance (tests ensure correctness)
- Add new features (tests prevent breakage)

**Testing is the foundation for everything else on the roadmap!**
