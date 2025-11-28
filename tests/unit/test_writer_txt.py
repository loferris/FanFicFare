"""Tests for writer_txt.py - Text story writer with word wrapping."""

import string
from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from fanficfare.writers.writer_txt import TextWriter, KludgeStringIO


class TestKludgeStringIO:
    """Test KludgeStringIO helper class."""

    def test_init_empty(self):
        """Test creating empty KludgeStringIO."""
        buf = KludgeStringIO()
        assert buf.getvalue() == ''

    def test_write_string(self):
        """Test writing string."""
        buf = KludgeStringIO()
        buf.write('hello')
        assert buf.getvalue() == 'hello'

    def test_write_bytes(self):
        """Test writing bytes (decodes to string)."""
        buf = KludgeStringIO()
        buf.write(b'hello')
        assert buf.getvalue() == 'hello'

    def test_write_unicode(self):
        """Test writing unicode."""
        buf = KludgeStringIO()
        buf.write('hello 世界')
        assert buf.getvalue() == 'hello 世界'

    def test_write_multiple(self):
        """Test writing multiple values."""
        buf = KludgeStringIO()
        buf.write('hello')
        buf.write(' ')
        buf.write('world')
        assert buf.getvalue() == 'hello world'

    def test_close(self):
        """Test close() method."""
        buf = KludgeStringIO()
        buf.write('test')
        buf.close()
        # Should still have data after close
        assert buf.getvalue() == 'test'


@pytest.fixture
def mock_configuration():
    """Create mock configuration."""
    config = Mock()
    config.getConfig.return_value = ''
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
        'summary': 'Test summary',
    }
    story.getChapterCount.return_value = 2
    story.getChapters.return_value = [
        {
            'html': '<p>Chapter 1 content</p>',
            'title': 'Chapter 1',
            'chapter': 'Chapter 1',
            'index04': '0001'
        },
        {
            'html': '<p>Chapter 2 content</p>',
            'title': 'Chapter 2',
            'chapter': 'Chapter 2',
            'index04': '0002'
        },
    ]
    story.setMetadata = Mock()
    story.extra_css = ""

    adapter.getStoryMetadataOnly.return_value = story
    adapter.getStory.return_value = story

    return adapter


@pytest.fixture
def writer(mock_configuration, mock_adapter):
    """Create text writer instance."""
    return TextWriter(mock_configuration, mock_adapter)


class TestTextWriterInit:
    """Test TextWriter initialization."""

    def test_init_calls_base_init(self, mock_configuration, mock_adapter):
        """Test initialization calls BaseStoryWriter.__init__."""
        writer = TextWriter(mock_configuration, mock_adapter)

        assert writer.adapter == mock_adapter
        assert writer.story is not None

    def test_init_sets_format_metadata(self, mock_configuration, mock_adapter):
        """Test initialization sets format name and extension."""
        writer = TextWriter(mock_configuration, mock_adapter)

        # Should set formatname and formatext
        writer.story.setMetadata.assert_any_call('formatname', 'txt')
        writer.story.setMetadata.assert_any_call('formatext', '.txt')

    def test_init_creates_templates(self, writer):
        """Test initialization creates all text templates."""
        assert isinstance(writer.TEXT_FILE_START, string.Template)
        assert isinstance(writer.TEXT_TITLE_PAGE_START, string.Template)
        assert isinstance(writer.TEXT_TITLE_ENTRY, string.Template)
        assert isinstance(writer.TEXT_TITLE_PAGE_END, string.Template)
        assert isinstance(writer.TEXT_TOC_PAGE_START, string.Template)
        assert isinstance(writer.TEXT_TOC_ENTRY, string.Template)
        assert isinstance(writer.TEXT_TOC_PAGE_END, string.Template)
        assert isinstance(writer.TEXT_CHAPTER_START, string.Template)
        assert isinstance(writer.TEXT_CHAPTER_END, string.Template)
        assert isinstance(writer.TEXT_FILE_END, string.Template)


class TestStaticMethods:
    """Test static methods."""

    def test_get_format_name(self):
        """Test getFormatName returns 'txt'."""
        assert TextWriter.getFormatName() == 'txt'

    def test_get_format_ext(self):
        """Test getFormatExt returns '.txt'."""
        assert TextWriter.getFormatExt() == '.txt'


class TestWrapLines:
    """Test wraplines method."""

    def test_wraplines_no_wrapping(self, writer):
        """Test wraplines with wrap_width=0 (no wrapping)."""
        writer.wrap_width = 0
        text = "This is a very long line that would normally be wrapped but won't be because wrapping is disabled."

        result = writer.wraplines(text)

        assert result == text

    def test_wraplines_with_width(self, writer):
        """Test wraplines with specific width."""
        writer.wrap_width = 20
        text = "This is a very long line that should be wrapped at 20 characters."

        result = writer.wraplines(text)

        # Should have line breaks
        assert '\n' in result
        # All lines should be <= 20 chars (excluding the newline)
        for line in result.split('\n'):
            assert len(line) <= 20 or line == ''

    def test_wraplines_multiple_paragraphs(self, writer):
        """Test wraplines with multiple paragraphs."""
        writer.wrap_width = 30
        text = "First paragraph.\n\nSecond paragraph with more text."

        result = writer.wraplines(text)

        # Should preserve paragraph breaks
        assert '\n\n' in result

    def test_wraplines_empty_string(self, writer):
        """Test wraplines with empty string."""
        writer.wrap_width = 80
        result = writer.wraplines('')
        assert result == '\n'


class TestLineEnds:
    """Test lineends method."""

    def test_lineends_unix(self, writer):
        """Test Unix line endings (default)."""
        writer.getConfig = Mock(return_value=False)
        text = "line1\nline2\nline3"

        result = writer.lineends(text)

        assert result == "line1\nline2\nline3"
        assert '\r\n' not in result

    def test_lineends_windows(self, writer):
        """Test Windows line endings."""
        def get_config_side_effect(key):
            if key == 'windows_eol':
                return True
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        text = "line1\nline2\nline3"

        result = writer.lineends(text)

        assert result == "line1\r\nline2\r\nline3"
        assert '\r\n' in result

    def test_lineends_removes_existing_cr(self, writer):
        """Test that existing \\r are removed first."""
        writer.getConfig = Mock(return_value=False)
        text = "line1\r\nline2\rline3"

        result = writer.lineends(text)

        # Should remove all \r
        assert '\r' not in result
        assert result == "line1\nline2line3"


class TestWriteStoryImpl:
    """Test writeStoryImpl method."""

    def test_write_basic_txt(self, writer):
        """Test writing basic text without wrapping."""
        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain story title and author
        assert 'Test Story' in output
        assert 'Test Author' in output

    def test_write_txt_with_chapters(self, writer):
        """Test writing text with chapter content."""
        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain chapter content (html2text converts <p> to plain text)
        assert 'Chapter 1 content' in output
        assert 'Chapter 2 content' in output

    def test_write_txt_with_wrapping(self, writer):
        """Test writing text with word wrapping."""
        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '40'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should have wrapped lines
        assert 'Test Story' in output

    def test_write_txt_with_toc(self, writer):
        """Test writing text with table of contents."""
        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '0'
            elif key == 'include_tocpage':
                return True
            return ''

        writer.metaonly = False
        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should contain TOC
        assert 'TABLE OF CONTENTS' in output

    def test_write_txt_custom_file_templates(self, writer):
        """Test writing text with custom file templates."""
        custom_start = 'START: ${title}'
        custom_end = 'THE END'

        def has_config_side_effect(key):
            return key in ['file_start', 'file_end']

        def get_config_side_effect(key):
            if key == 'file_start':
                return custom_start
            elif key == 'file_end':
                return custom_end
            elif key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(side_effect=has_config_side_effect)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should use custom templates
        assert 'START: Test Story' in output
        assert 'THE END' in output

    def test_write_txt_custom_chapter_templates(self, writer):
        """Test writing text with custom chapter templates."""
        custom_chapter_start = '--- ${chapter} ---'
        custom_chapter_end = '---'

        def has_config_side_effect(key):
            return key in ['chapter_start', 'chapter_end']

        def get_config_side_effect(key):
            if key == 'chapter_start':
                return custom_chapter_start
            elif key == 'chapter_end':
                return custom_chapter_end
            elif key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(side_effect=has_config_side_effect)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should use custom chapter templates
        assert '--- Chapter 1 ---' in output
        assert '---' in output

    def test_skip_empty_chapters(self, writer):
        """Test skipping chapters with no HTML content."""
        writer.story.getChapters.return_value = [
            {
                'html': '<p>Chapter 1 content</p>',
                'title': 'Chapter 1',
                'chapter': 'Chapter 1',
                'index04': '0001'
            },
            {
                'html': None,  # Empty chapter
                'title': 'Chapter 2',
                'chapter': 'Chapter 2',
                'index04': '0002'
            },
        ]

        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
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
                'index04': '0001'
            },
        ]

        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should handle Unicode without crashing
        assert '你好世界' in output

    def test_no_chapters(self, writer):
        """Test writing story with no chapters."""
        writer.story.getChapters.return_value = []
        writer.story.getChapterCount.return_value = 0

        def get_config_side_effect(key):
            if key == 'wrap_width':
                return '0'
            return ''

        writer.getConfig = Mock(side_effect=get_config_side_effect)
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=[])

        out = BytesIO()
        writer.writeStoryImpl(out)

        output = out.getvalue().decode('utf-8')

        # Should still have basic structure
        assert 'Test Story' in output
        assert 'End file' in output
