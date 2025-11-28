"""Tests for base_writer.py - Base class for all story writers."""

import datetime
import os
import string
import tempfile
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch, call
from zipfile import ZipFile

import pytest

from fanficfare.writers.base_writer import BaseStoryWriter


class TestStoryWriter(BaseStoryWriter):
    """Concrete implementation of BaseStoryWriter for testing."""

    @staticmethod
    def getFormatName():
        return 'test'

    @staticmethod
    def getFormatExt():
        return '.tst'

    def writeStoryImpl(self, out):
        """Minimal implementation for testing."""
        out.write(b"Test story content")


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
    story.getMetadataRaw.return_value = datetime.datetime(2024, 1, 1)
    story.getAllMetadata.return_value = {
        'title': 'Test Story',
        'author': 'Test Author',
        'summary': 'Test summary'
    }
    story.getChapterCount.return_value = 1
    story.getChapters.return_value = []
    story.formatFileName.return_value = "test_story.tst"
    story.setMetadata = Mock()
    story.extra_css = ""

    adapter.getStoryMetadataOnly.return_value = story
    adapter.getStory.return_value = story

    return adapter


@pytest.fixture
def writer(mock_configuration, mock_adapter):
    """Create test writer instance."""
    return TestStoryWriter(mock_configuration, mock_adapter)


class TestBaseWriterInit:
    """Test BaseStoryWriter initialization."""

    def test_init_calls_requestable_init(self, mock_configuration, mock_adapter):
        """Test initialization calls parent Requestable.__init__."""
        writer = TestStoryWriter(mock_configuration, mock_adapter)

        assert writer.adapter == mock_adapter
        assert writer.story is not None

    def test_init_sets_format_metadata(self, mock_configuration, mock_adapter):
        """Test initialization sets format name and extension in metadata."""
        writer = TestStoryWriter(mock_configuration, mock_adapter)

        # Should call setMetadata twice: once for formatname, once for formatext
        assert writer.story.setMetadata.call_count == 2
        writer.story.setMetadata.assert_any_call('formatname', 'test')
        writer.story.setMetadata.assert_any_call('formatext', '.tst')


class TestStaticMethods:
    """Test static methods."""

    def test_get_format_name(self):
        """Test getFormatName returns correct name."""
        assert TestStoryWriter.getFormatName() == 'test'

    def test_get_format_ext(self):
        """Test getFormatExt returns correct extension."""
        assert TestStoryWriter.getFormatExt() == '.tst'


class TestMetadata:
    """Test metadata handling."""

    def test_get_metadata(self, writer):
        """Test getMetadata strips HTML."""
        writer.story.getMetadata.return_value = "<b>Bold Text</b>"

        result = writer.getMetadata('test_key')

        assert result == "Bold Text"

    def test_get_metadata_with_removeallentities(self, writer):
        """Test getMetadata with removeallentities parameter."""
        writer.getMetadata('test_key', removeallentities=True)

        writer.story.getMetadata.assert_called_once_with('test_key', True)


class TestFilenames:
    """Test filename generation."""

    def test_get_output_filename_no_zip(self, writer):
        """Test getOutputFileName without zip output."""
        writer.getConfig = Mock(return_value=False)
        writer.story.formatFileName.return_value = "output.tst"

        result = writer.getOutputFileName()

        assert result == "output.tst"

    def test_get_output_filename_with_zip(self, writer):
        """Test getOutputFileName with zip output."""
        def config_side_effect(key):
            if key == 'zip_output':
                return True
            if key == 'zip_filename':
                return 'archive.zip'
            if key == 'allow_unsafe_filename':
                return False
            return None

        writer.getConfig = Mock(side_effect=config_side_effect)
        writer.story.formatFileName.return_value = "archive.zip"

        result = writer.getOutputFileName()

        assert result == "archive.zip"

    def test_get_base_filename(self, writer):
        """Test getBaseFileName."""
        writer.getConfig = Mock(side_effect=lambda x: False if x == 'allow_unsafe_filename' else 'pattern')
        writer.story.formatFileName.return_value = "story.tst"

        result = writer.getBaseFileName()

        assert result == "story.tst"

    def test_get_zip_filename(self, writer):
        """Test getZipFileName."""
        writer.getConfig = Mock(side_effect=lambda x: False if x == 'allow_unsafe_filename' else 'zip_pattern')
        writer.story.formatFileName.return_value = "archive.zip"

        result = writer.getZipFileName()

        assert result == "archive.zip"


class TestWrite:
    """Test _write method."""

    def test_write_string(self, writer):
        """Test _write converts string to bytes."""
        out = BytesIO()

        writer._write(out, "test string")

        assert out.getvalue() == b"test string"

    def test_write_bytes(self, writer):
        """Test _write handles bytes."""
        out = BytesIO()

        writer._write(out, b"test bytes")

        assert out.getvalue() == b"test bytes"


class TestTOCPage:
    """Test Table of Contents page logic."""

    def test_include_toc_page_always(self, writer):
        """Test includeToCPage when set to 'always'."""
        writer.getConfig = Mock(return_value='always')
        writer.metaonly = False

        assert writer.includeToCPage() is True

    def test_include_toc_page_multi_chapter(self, writer):
        """Test includeToCPage with multiple chapters."""
        writer.getConfig = Mock(return_value=True)
        writer.story.getChapterCount.return_value = 5
        writer.metaonly = False

        assert writer.includeToCPage() is True

    def test_exclude_toc_page_single_chapter(self, writer):
        """Test includeToCPage with single chapter."""
        writer.getConfig = Mock(return_value=True)
        writer.story.getChapterCount.return_value = 1
        writer.metaonly = False

        assert writer.includeToCPage() is False

    def test_exclude_toc_page_metaonly(self, writer):
        """Test includeToCPage when metaonly is True."""
        writer.getConfig = Mock(return_value=True)
        writer.story.getChapterCount.return_value = 5
        writer.metaonly = True

        assert writer.includeToCPage() is False


class TestWriteTitlePage:
    """Test writeTitlePage method."""

    def test_write_title_page_basic(self, writer):
        """Test writing basic title page."""
        writer.getConfig = Mock(side_effect=lambda x: True if x == 'include_titlepage' else [])
        writer.hasConfig = Mock(return_value=False)
        writer.isValidMetaEntry = Mock(return_value=True)
        writer.get_label = Mock(return_value="Label")
        writer.getConfigList = Mock(return_value=['title', 'author'])
        writer.story.getAllMetadata.return_value = {'title': 'Test', 'author': 'Author'}

        out = BytesIO()
        START = string.Template("<start>")
        ENTRY = string.Template("<entry>$label: $value</entry>")
        END = string.Template("</end>")

        writer.writeTitlePage(out, START, ENTRY, END)

        output = out.getvalue().decode('utf-8')
        assert "<start>" in output
        assert "</end>" in output

    def test_write_title_page_skip_when_disabled(self, writer):
        """Test title page is skipped when disabled."""
        writer.getConfig = Mock(return_value=False)  # include_titlepage=False

        out = BytesIO()
        START = string.Template("<start>")
        ENTRY = string.Template("<entry>$label: $value</entry>")
        END = string.Template("</end>")

        writer.writeTitlePage(out, START, ENTRY, END)

        assert out.getvalue() == b""


class TestWriteTOCPage:
    """Test writeTOCPage method."""

    def test_write_toc_page(self, writer):
        """Test writing TOC page."""
        writer.includeToCPage = Mock(return_value=True)
        writer.hasConfig = Mock(return_value=False)
        writer.story.getAllMetadata.return_value = {'title': 'Test Story'}
        writer.story.getChapters.return_value = [
            {'html': 'Chapter 1', 'chapter': 'Chapter 1'},
            {'html': 'Chapter 2', 'chapter': 'Chapter 2'},
        ]

        out = BytesIO()
        START = string.Template("<toc>")
        ENTRY = string.Template("<li>$chapter</li>")
        END = string.Template("</toc>")

        writer.writeTOCPage(out, START, ENTRY, END)

        output = out.getvalue().decode('utf-8')
        assert "<toc>" in output
        assert "<li>Chapter 1</li>" in output
        assert "<li>Chapter 2</li>" in output
        assert "</toc>" in output

    def test_write_toc_page_skip_when_not_included(self, writer):
        """Test TOC page is skipped when not included."""
        writer.includeToCPage = Mock(return_value=False)

        out = BytesIO()
        START = string.Template("<toc>")
        ENTRY = string.Template("<li>$chapter</li>")
        END = string.Template("</toc>")

        writer.writeTOCPage(out, START, ENTRY, END)

        assert out.getvalue() == b""


class TestWriteStory:
    """Test writeStory method."""

    def test_write_story_to_stream(self, writer):
        """Test writing story to stream."""
        writer.getConfig = Mock(side_effect=lambda x: {
            'zip_output': False,
            'output_css': ''
        }.get(x, ''))

        out = BytesIO()
        writer.writeStory(outstream=out, metaonly=True)

        # Should write test content
        assert out.getvalue() == b"Test story content"

    def test_write_story_sets_css_metadata(self, writer):
        """Test writeStory sets output_css metadata."""
        writer.getConfig = Mock(side_effect=lambda x: {
            'zip_output': False,
            'output_css': 'body { color: red; }'
        }.get(x, ''))
        writer.story.extra_css = '/* author css */'

        out = BytesIO()
        writer.writeStory(outstream=out, metaonly=True)

        # Should combine extra_css and output_css
        writer.story.setMetadata.assert_called()
        calls = [call for call in writer.story.setMetadata.call_args_list
                 if call[0][0] == 'output_css']
        assert len(calls) > 0
        css_value = calls[0][0][1]
        assert '/* author css */' in css_value
        assert 'body { color: red; }' in css_value

    @patch('os.path.exists')
    @patch('builtins.open')
    def test_write_story_to_file(self, mock_open, mock_exists, writer):
        """Test writing story to file."""
        mock_exists.return_value = False
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        writer.getConfig = Mock(side_effect=lambda x: {
            'zip_output': False,
            'output_css': '',
            'make_directories': False,
            'always_overwrite': True
        }.get(x, False))

        writer.writeStory(outfilename='test.tst', metaonly=True)

        mock_open.assert_called_once_with('test.tst', 'wb')

    def test_write_story_zip_output(self, writer, tmp_path):
        """Test writing story with zip output."""
        zip_file = tmp_path / "archive.zip"

        writer.getConfig = Mock(side_effect=lambda x: {
            'zip_output': True,
            'output_css': '',
            'make_directories': False,
            'always_overwrite': True
        }.get(x, False))
        writer.getBaseFileName = Mock(return_value='story.tst')

        writer.writeStory(outfilename=str(zip_file), metaonly=True)

        # Verify zip file was created
        assert zip_file.exists()

        # Verify content in zip
        with ZipFile(zip_file, 'r') as zf:
            assert 'story.tst' in zf.namelist()
            assert zf.read('story.tst') == b'Test story content'


class TestWriteFile:
    """Test writeFile method."""

    def test_write_file_no_zip(self, writer, tmp_path):
        """Test writeFile without zip output."""
        # Set outfilename without directory to avoid path issues
        writer.getConfig = Mock(return_value=False)
        writer.outfilename = "story.tst"

        # Write file in tmp directory
        output_path = tmp_path / 'image.jpg'
        writer.writeFile(str(output_path), b'image data')

        # Verify file was written
        assert output_path.exists()
        assert output_path.read_bytes() == b'image data'

    def test_write_file_with_zip(self, writer):
        """Test writeFile with zip output."""
        writer.getConfig = Mock(return_value=True)
        writer.zipout = Mock()
        writer.getBaseFileName = Mock(return_value='')  # No base directory

        writer.writeFile('image.jpg', b'image data')

        # When base filename has no directory, just use the filename
        writer.zipout.writestr.assert_called_once_with('image.jpg', b'image data')

    def test_write_file_with_zip_and_directory(self, writer):
        """Test writeFile with zip output and subdirectory."""
        writer.getConfig = Mock(return_value=True)
        writer.zipout = Mock()
        writer.getBaseFileName = Mock(return_value='output/story.tst')

        writer.writeFile('image.jpg', b'image data')

        # Should include the directory from base filename
        writer.zipout.writestr.assert_called_once_with('output/image.jpg', b'image data')


class TestAbstractMethod:
    """Test abstract method enforcement."""

    def test_base_writer_write_story_impl_not_implemented(self):
        """Test that BaseStoryWriter.writeStoryImpl raises NotImplementedError."""
        # BaseStoryWriter now raises NotImplementedError
        # Subclasses must override it
        writer = BaseStoryWriter.__new__(BaseStoryWriter)
        out = BytesIO()

        # Should raise NotImplementedError
        with pytest.raises(NotImplementedError, match="Subclasses must implement writeStoryImpl"):
            writer.writeStoryImpl(out)
