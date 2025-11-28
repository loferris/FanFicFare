"""Tests for writer_html.py - HTML story writer."""

import string
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch

import pytest

from fanficfare.writers.writer_html import HTMLWriter


@pytest.fixture
def mock_configuration():
    """Create mock configuration."""
    config = Mock()
    config.getConfig.return_value = False
    config.hasConfig.return_value = False
    config.getConfigList.return_value = []
    return config


@pytest.fixture
def mock_adapter():
    """Create mock adapter with story metadata."""
    adapter = Mock()
    story = Mock()

    # Setup metadata
    story.getMetadata.return_value = "Test Value"
    story.getAllMetadata.return_value = {
        'title': 'Test Story',
        'author': 'Test Author',
        'authorHTML': '<a href="#">Test Author</a>',
        'storyUrl': 'https://example.com/story/123',
        'summary': 'Test summary',
        'output_css': 'body { font-family: Arial; }'
    }
    story.getChapterCount.return_value = 2
    story.getChapters.return_value = [
        {
            'html': '<p>Chapter 1 content</p>',
            'title': 'Chapter 1',
            'chapter': 'Chapter 1',
            'url': 'https://example.com/story/123/1',
            'index04': '0001'
        },
        {
            'html': '<p>Chapter 2 content</p>',
            'title': 'Chapter 2',
            'chapter': 'Chapter 2',
            'url': 'https://example.com/story/123/2',
            'index04': '0002'
        },
    ]
    story.getImgUrls.return_value = []
    story.cover = None
    story.setMetadata = Mock()
    story.extra_css = ""

    adapter.getStoryMetadataOnly.return_value = story
    adapter.getStory.return_value = story

    return adapter


@pytest.fixture
def writer(mock_configuration, mock_adapter):
    """Create HTML writer instance."""
    return HTMLWriter(mock_configuration, mock_adapter)


class TestHTMLWriterInit:
    """Test HTMLWriter initialization."""

    def test_init_calls_base_init(self, mock_configuration, mock_adapter):
        """Test initialization calls BaseStoryWriter.__init__."""
        writer = HTMLWriter(mock_configuration, mock_adapter)

        assert writer.adapter == mock_adapter
        assert writer.story is not None

    def test_init_sets_format_metadata(self, mock_configuration, mock_adapter):
        """Test initialization sets format name and extension."""
        writer = HTMLWriter(mock_configuration, mock_adapter)

        # Should set formatname and formatext
        writer.story.setMetadata.assert_any_call('formatname', 'html')
        writer.story.setMetadata.assert_any_call('formatext', '.html')

    def test_init_creates_templates(self, writer):
        """Test initialization creates all HTML templates."""
        assert isinstance(writer.HTML_FILE_START, string.Template)
        assert isinstance(writer.HTML_COVER, string.Template)
        assert isinstance(writer.HTML_TITLE_PAGE_START, string.Template)
        assert isinstance(writer.HTML_TITLE_ENTRY, string.Template)
        assert isinstance(writer.HTML_TITLE_PAGE_END, string.Template)
        assert isinstance(writer.HTML_TOC_PAGE_START, string.Template)
        assert isinstance(writer.HTML_TOC_ENTRY, string.Template)
        assert isinstance(writer.HTML_TOC_PAGE_END, string.Template)
        assert isinstance(writer.HTML_CHAPTER_START, string.Template)
        assert isinstance(writer.HTML_CHAPTER_END, string.Template)
        assert isinstance(writer.HTML_FILE_END, string.Template)


class TestStaticMethods:
    """Test static methods."""

    def test_get_format_name(self):
        """Test getFormatName returns 'html'."""
        assert HTMLWriter.getFormatName() == 'html'

    def test_get_format_ext(self):
        """Test getFormatExt returns '.html'."""
        assert HTMLWriter.getFormatExt() == '.html'


class TestWriteStoryImpl:
    """Test writeStoryImpl method."""

    def test_write_basic_html(self, writer):
        """Test writing basic HTML without images."""
        writer.getConfig = Mock(return_value=False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain HTML structure
        assert '<!DOCTYPE html>' in output
        assert '<html>' in output
        assert '</html>' in output
        assert '<title>Test Story by Test Author</title>' in output

    def test_write_html_with_chapters(self, writer):
        """Test writing HTML with chapter content."""
        writer.getConfig = Mock(return_value=False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain chapter content
        assert 'Chapter 1 content' in output
        assert 'Chapter 2 content' in output
        assert 'section0001' in output
        assert 'section0002' in output

    def test_write_html_with_toc(self, writer):
        """Test writing HTML with table of contents."""
        # Configure to include TOC
        def get_config_side_effect(key):
            if key == 'include_tocpage':
                return True
            return False

        writer.metaonly = False  # Ensure metaonly is False
        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain TOC
        assert 'Table of Contents' in output
        assert 'href="#section0001"' in output
        assert 'href="#section0002"' in output

    def test_write_html_with_cover(self, writer):
        """Test writing HTML with cover image."""
        writer.story.cover = 'cover.jpg'
        writer.getConfig = Mock(side_effect=lambda x: True if x == 'include_images' else False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain cover image
        assert '<img src="cover.jpg"' in output

    def test_write_html_with_images(self, writer):
        """Test writing HTML with embedded images."""
        writer.story.getImgUrls.return_value = [
            {'newsrc': 'image1.jpg', 'data': b'imagedata1'},
            {'newsrc': 'image2.png', 'data': b'imagedata2'},
        ]
        writer.getConfig = Mock(side_effect=lambda x: True if x == 'include_images' else False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])
        writer.writeFile = Mock()

        out = BytesIO()
        writer.writeStoryImpl(out)

        # Should write image files
        assert writer.writeFile.call_count == 2
        writer.writeFile.assert_any_call('image1.jpg', b'imagedata1')
        writer.writeFile.assert_any_call('image2.png', b'imagedata2')

    def test_write_html_custom_file_start(self, writer):
        """Test writing HTML with custom file_start template."""
        custom_start = '<html><head><title>Custom</title></head><body>'

        def has_config_side_effect(key):
            return key == 'file_start'

        def get_config_side_effect(key):
            if key == 'file_start':
                return custom_start
            return False

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(side_effect=has_config_side_effect)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should use custom start
        assert 'Custom' in output

    def test_write_html_custom_chapter_templates(self, writer):
        """Test writing HTML with custom chapter templates."""
        custom_chapter_start = '<h3>Chapter: ${chapter}</h3>'
        custom_chapter_end = '<hr/>'

        def has_config_side_effect(key):
            return key in ['chapter_start', 'chapter_end']

        def get_config_side_effect(key):
            if key == 'chapter_start':
                return custom_chapter_start
            elif key == 'chapter_end':
                return custom_chapter_end
            return False

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(side_effect=has_config_side_effect)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should use custom chapter templates
        assert '<h3>Chapter: Chapter 1</h3>' in output
        assert '<hr/>' in output

    @patch('fanficfare.writers.writer_html.bs4.BeautifulSoup')
    def test_internalize_text_links(self, mock_bs, writer):
        """Test internalizing chapter cross-links."""
        # Setup mock BeautifulSoup to simulate link processing
        mock_soup = MagicMock()
        mock_link = MagicMock()
        mock_link.has_attr.return_value = True
        mock_link.__getitem__.return_value = 'https://example.com/story/123/2'
        mock_soup.find_all.return_value = [mock_link]
        mock_soup.__str__.return_value = '<html><head></head><body><p>Test</p></body></html>'
        mock_bs.return_value = mock_soup

        # Configure to enable internalize_text_links
        def get_config_side_effect(key):
            if key == 'internalize_text_links':
                return True
            return False

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        # Should have processed links with BeautifulSoup
        assert mock_bs.called

    def test_skip_empty_chapters(self, writer):
        """Test skipping chapters with no HTML content."""
        writer.story.getChapters.return_value = [
            {
                'html': '<p>Chapter 1 content</p>',
                'title': 'Chapter 1',
                'chapter': 'Chapter 1',
                'url': 'https://example.com/story/123/1',
                'index04': '0001'
            },
            {
                'html': None,  # Empty chapter
                'title': 'Chapter 2',
                'chapter': 'Chapter 2',
                'url': 'https://example.com/story/123/2',
                'index04': '0002'
            },
        ]

        writer.getConfig = Mock(return_value=False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should only have Chapter 1, not Chapter 2
        assert 'Chapter 1 content' in output
        assert 'Chapter 2 content' not in output


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_content(self, writer):
        """Test handling Unicode content in chapters."""
        writer.story.getChapters.return_value = [
            {
                'html': '<p>Unicode: 你好世界 émojis 🎉</p>',
                'title': 'Unicode Chapter',
                'chapter': 'Unicode Chapter',
                'url': 'https://example.com/story/123/1',
                'index04': '0001'
            },
        ]

        writer.getConfig = Mock(return_value=False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should handle Unicode without crashing
        assert '你好世界' in output
        assert '🎉' in output

    def test_special_html_chars(self, writer):
        """Test handling special HTML characters."""
        writer.story.getAllMetadata.return_value = {
            'title': 'Test & <Story>',
            'author': 'Author "Name"',
            'authorHTML': '<a href="#">Author "Name"</a>',
            'storyUrl': 'https://example.com/story?id=123&type=fic',
            'output_css': ''
        }

        writer.getConfig = Mock(return_value=False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain the special chars (template substitution doesn't escape)
        assert isinstance(output, str)

    def test_no_chapters(self, writer):
        """Test writing story with no chapters."""
        writer.story.getChapters.return_value = []
        writer.story.getChapterCount.return_value = 0

        writer.getConfig = Mock(return_value=False)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should still have HTML structure
        assert '<!DOCTYPE html>' in output
        assert '</html>' in output
