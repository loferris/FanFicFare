"""
Tests for Config-Driven Adapter
"""
import pytest
from pathlib import Path
from fanficfare_modern.models import SiteConfig
from fanficfare_modern.config_adapters.config_driven import ConfigDrivenAdapter


class TestConfigDrivenAdapter:
    """Test YAML config-driven adapter"""

    def test_load_from_yaml(self, tmp_path):
        """Test loading adapter from YAML file"""
        # Create test YAML config
        yaml_content = """
name: "Test Site"
domains:
  - example.com
story_url_pattern: '/story/(?P<story_id>\\d+)'
selectors:
  story:
    title: "h1.title"
    author: "a.author"
    summary: "div.summary"
"""
        config_file = tmp_path / "test_site.yaml"
        config_file.write_text(yaml_content)

        # Load adapter
        adapter = ConfigDrivenAdapter.from_yaml(config_file)

        assert adapter.config.name == "Test Site"
        assert "example.com" in adapter.config.domains

    def test_extract_metadata(self):
        """Test metadata extraction using selectors"""
        config = SiteConfig(
            name="Test Site",
            domains=["example.com"],
            story_url_pattern=r'/story/(?P<story_id>\d+)',
            selectors={
                'story': {
                    'title': 'h1.title',
                    'author': 'span.author',
                    'summary': 'div.summary',
                    'chapters': 'div.chapters a',
                }
            }
        )

        adapter = ConfigDrivenAdapter(config)

        html = """
        <html>
        <body>
            <h1 class="title">Test Story</h1>
            <span class="author">Test Author</span>
            <div class="summary">This is a test story about testing.</div>
            <div class="chapters">
                <a href="/story/123/chapter/1">Chapter 1</a>
                <a href="/story/123/chapter/2">Chapter 2</a>
            </div>
        </body>
        </html>
        """

        story = adapter.extract_metadata(html, "https://example.com/story/123")

        assert story.story_id == "123"
        assert story.title == "Test Story"
        assert story.author == "Test Author"
        assert "test story" in story.summary.lower()
        assert len(story.chapters) == 2
        assert story.chapters[0].title == "Chapter 1"
        assert story.source_site == "example.com"

    def test_extract_chapter_content(self):
        """Test chapter content extraction"""
        config = SiteConfig(
            name="Test Site",
            domains=["example.com"],
            story_url_pattern=r'/story/\d+',
            selectors={
                'content': 'div.chapter-text'
            }
        )

        adapter = ConfigDrivenAdapter(config)

        html = """
        <html>
        <body>
            <div class="chapter-text">
                <p>This is the first paragraph.</p>
                <p>This is the second paragraph.</p>
            </div>
        </body>
        </html>
        """

        content = adapter.extract_chapter_content(html)

        assert "first paragraph" in content
        assert "second paragraph" in content

    def test_can_handle_url(self):
        """Test URL matching"""
        config = SiteConfig(
            name="Test Site",
            domains=["example.com", "www.example.com"],
            story_url_pattern=r'/story/(?P<story_id>\d+)'
        )

        adapter = ConfigDrivenAdapter(config)

        # Should match
        assert adapter.can_handle("https://example.com/story/123")
        assert adapter.can_handle("https://www.example.com/story/456")

        # Should not match
        assert not adapter.can_handle("https://other.com/story/123")
        assert not adapter.can_handle("https://example.com/other/123")

    def test_from_domain(self, tmp_path):
        """Test loading config by domain"""
        # Create config file
        config1 = tmp_path / "site1.yaml"
        config1.write_text("""
name: "Site 1"
domains:
  - site1.com
story_url_pattern: '/story/\\d+'
""")

        config2 = tmp_path / "site2.yaml"
        config2.write_text("""
name: "Site 2"
domains:
  - site2.com
story_url_pattern: '/fic/\\d+'
""")

        # Load adapter for site1.com
        adapter = ConfigDrivenAdapter.from_domain("site1.com", tmp_path)

        assert adapter is not None
        assert adapter.config.name == "Site 1"

        # Load adapter for site2.com
        adapter = ConfigDrivenAdapter.from_domain("site2.com", tmp_path)

        assert adapter is not None
        assert adapter.config.name == "Site 2"

        # Try non-existent domain
        adapter = ConfigDrivenAdapter.from_domain("site3.com", tmp_path)

        assert adapter is None
