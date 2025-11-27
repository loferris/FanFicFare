"""
Tests for Platform Detector
"""
import pytest
from fanficfare_modern.core.platform_detector import PlatformDetector


class TestPlatformDetector:
    """Test platform detection"""

    def setup_method(self):
        self.detector = PlatformDetector()

    def test_detect_efiction(self):
        """Test eFiction site detection"""
        html = """
        <html>
        <head>
            <meta name="generator" content="eFiction 3.5">
            <link href="/efiction/style.css" rel="stylesheet">
        </head>
        <body>
            <a href="viewstory.php?sid=123">Story</a>
            <select name="chapter">
                <option value="1">Chapter 1</option>
            </select>
        </body>
        </html>
        """
        url = "https://example.com/viewstory.php?sid=123"

        platform = self.detector.detect(html, url)
        assert platform == "efiction"

    def test_detect_xenforo(self):
        """Test XenForo forum detection"""
        html = """
        <html id="XenForo" data-template="thread_view">
        <head>
            <meta name="generator" content="XenForo 2.2">
        </head>
        <body>
            <div class="threadmarks">
                <div class="threadmarks-item">
                    <a href="/threads/story.123/page-1">Chapter 1</a>
                </div>
            </div>
        </body>
        </html>
        """
        url = "https://forums.example.com/threads/story.123/"

        platform = self.detector.detect(html, url)
        assert platform == "xenforo"

    def test_detect_ao3(self):
        """Test AO3 detection"""
        html = """
        <html>
        <head>
            <meta name="generator" content="ArchiveOfOurOwn">
            <meta name="twitter:site" content="@ao3org">
        </head>
        <body id="inner">
            <div id="workskin">
                <h2 class="title">Story Title</h2>
                <a rel="author" href="/users/author">Author</a>
            </div>
        </body>
        </html>
        """
        url = "https://archiveofourown.org/works/12345"

        platform = self.detector.detect(html, url)
        assert platform == "ao3"

    def test_detect_wordpress(self):
        """Test WordPress detection"""
        html = """
        <html>
        <head>
            <meta name="generator" content="WordPress 6.0">
            <link href="https://example.com/wp-content/themes/theme/style.css">
        </head>
        <body class="wordpress">
        </body>
        </html>
        """

        platform = self.detector.detect(html)
        assert platform == "wordpress"

    def test_detect_from_url_only(self):
        """Test detection from URL patterns alone"""
        # eFiction URL
        url = "https://example.com/viewstory.php?sid=123"
        platform = self.detector.detect_from_url(url)
        assert platform == "efiction"

        # XenForo URL
        url = "https://forums.example.com/threads/story-title.12345/"
        platform = self.detector.detect_from_url(url)
        assert platform == "xenforo"

        # AO3 URL
        url = "https://archiveofourown.org/works/12345"
        platform = self.detector.detect_from_url(url)
        assert platform == "ao3"

    def test_no_detection(self):
        """Test when platform can't be detected"""
        html = "<html><body>Generic page</body></html>"
        url = "https://example.com/story"

        platform = self.detector.detect(html, url)
        assert platform is None
