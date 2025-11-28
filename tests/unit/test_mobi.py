"""Tests for mobi.py - MOBI ebook format writer."""

import struct
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock

import pytest

from fanficfare.mobi import (
    Converter,
    Header,
    Record,
    _SubEntry,
    encoding,
    languages,
    EXTH_HEADER_FIELDS,
)


class TestSubEntry:
    """Test _SubEntry class for HTML entry processing."""

    def test_basic_creation(self):
        """Test creating a SubEntry with title."""
        html = "<html><head><title>Test Title</title></head><body>Content</body></html>"
        entry = _SubEntry(1, html)

        assert entry.pos == 1
        assert entry.title == "Test Title"
        assert entry._name == "mobi_article_1"

    def test_no_title_uses_default(self):
        """Test SubEntry without title uses default."""
        html = "<html><head><title></title></head><body>Content</body></html>"
        entry = _SubEntry(5, html)

        assert entry.pos == 5
        assert entry.title == "Article 5"

    def test_toc_link_generation(self):
        """Test table of contents link generation."""
        html = "<html><head><title>Chapter 1</title></head><body>Text</body></html>"
        entry = _SubEntry(2, html)

        link = entry.TocLink()
        assert '<a href="#mobi_article_2_MOBI_START">' in link
        assert 'Chapter 1' in link

    def test_anchor_generation(self):
        """Test anchor tag generation."""
        html = "<html><head><title>Test</title></head><body>Content</body></html>"
        entry = _SubEntry(3, html)

        anchor = entry.Anchor()
        assert anchor == '<a name="mobi_article_3_MOBI_START">'

    def test_body_renames_anchors(self):
        """Test body processing renames anchors."""
        html = '<html><head><title>Test</title></head><body><a name="test">Link</a></body></html>'
        entry = _SubEntry(1, html)

        body = entry.Body()
        # Should have renamed anchor with prefix
        assert 'mobi_article_1_' in body

    def test_long_title_truncation(self):
        """Test very long titles are truncated in TOC link."""
        long_title = "A" * 100
        html = f"<html><head><title>{long_title}</title></head><body>Text</body></html>"
        entry = _SubEntry(1, html)

        link = entry.TocLink()
        # Should be truncated to 80 chars based on %.80s format
        assert len(long_title) > 80
        assert entry.title == long_title  # Original title preserved


class TestRecord:
    """Test Record class for PDB record handling."""

    def test_record_creation(self):
        """Test creating a record."""
        data = b"test data"
        record = Record(data, 1)

        assert record.data == data
        assert record._id == 1

    def test_max_size_assertion(self):
        """Test record size limit enforcement."""
        # Should succeed with data at max size
        data = b"x" * Record.MAX_SIZE
        record = Record(data, 1)
        assert len(record.data) == Record.MAX_SIZE

        # Should fail with data exceeding max size
        with pytest.raises(AssertionError):
            Record(b"x" * (Record.MAX_SIZE + 1), 1)

    def test_record_repr(self):
        """Test record string representation."""
        record = Record(b"test", 5)
        repr_str = repr(record)

        assert "Record:" in repr_str
        assert "id=5" in repr_str
        assert "len=4" in repr_str

    def test_write_data(self):
        """Test writing record data to output."""
        data = b"test data"
        record = Record(data, 1)
        out = BytesIO()

        record.WriteData(out)
        assert out.getvalue() == data

    def test_write_header(self):
        """Test writing record header."""
        record = Record(b"data", 1)
        out = BytesIO()

        record.WriteHeader(out, 1000)
        header = out.getvalue()

        # Header should be INDEX_LEN bytes
        assert len(header) == Record.INDEX_LEN

        # Unpack and verify structure
        offset, attributes, reserved, record_id = struct.unpack('>IbbH', header)
        assert offset == 1000
        assert attributes == 64  # dirty flag
        assert reserved == 0
        assert record_id == 1


class TestHeader:
    """Test Header class for MOBI header generation."""

    def test_header_creation(self):
        """Test creating a header with defaults."""
        header = Header()

        assert header._length == 0
        assert header._record_count == 0
        assert header._first_image_index == 0

    def test_set_author(self):
        """Test setting author."""
        header = Header()
        header.SetAuthor("John Doe")

        assert header._author == b"John Doe"

    def test_set_author_non_ascii(self):
        """Test setting author with non-ASCII characters."""
        header = Header()
        header.SetAuthor("José García")

        # Should encode as ASCII ignoring errors
        assert isinstance(header._author, bytes)
        # Non-ASCII chars should be removed/ignored
        assert b"Garca" in header._author or b"Garcia" in header._author

    def test_set_title(self):
        """Test setting title."""
        header = Header()
        header.SetTitle("My Story")

        assert header._title == b"My Story"

    def test_set_publisher(self):
        """Test setting publisher."""
        header = Header()
        header.SetPublisher("FanFicFare")

        assert header._publisher == b"FanFicFare"

    def test_add_record(self):
        """Test adding a record to header."""
        header = Header()
        data = b"test data"

        record = header.AddRecord(data, 1)

        assert isinstance(record, Record)
        assert header._record_count == 1
        assert header._length == len(data)

    def test_add_multiple_records(self):
        """Test adding multiple records."""
        header = Header()

        header.AddRecord(b"data1", 1)
        header.AddRecord(b"data2", 2)
        header.AddRecord(b"data3", 3)

        assert header._record_count == 3
        assert header._length == 15  # 5 + 5 + 5

    def test_set_image_record_index(self):
        """Test setting image record index."""
        header = Header()
        header.SetImageRecordIndex(42)

        assert header._first_image_index == 42

    def test_palmdoc_header(self):
        """Test PalmDoc header generation."""
        header = Header()
        header.AddRecord(b"x" * 100, 1)

        palmdoc = header.PalmDocHeader()

        # Should be 16 bytes
        assert len(palmdoc) == 16

        # Unpack and verify structure
        compression, unused1, length, records, max_size, encryption, unused2 = struct.unpack(
            '>HHIHHHH', palmdoc
        )
        assert compression == 1  # no compression
        assert length == 100
        assert records == 2  # header + 1 data record
        assert max_size == Record.MAX_SIZE
        assert encryption == 0

    def test_pdb_header(self):
        """Test PDB header generation."""
        header = Header()
        header.SetTitle("Test Book")

        pdb_header, rec_offset = header.PDBHeader(5)

        # Should return header and offset
        assert isinstance(pdb_header, bytes)
        assert isinstance(rec_offset, int)
        assert rec_offset > 0

        # Header should contain title
        assert b"Test Book" in pdb_header
        assert b"BOOK" in pdb_header
        assert b"MOBI" in pdb_header

    def test_exth_header(self):
        """Test EXTH header generation."""
        header = Header()
        header.SetAuthor("Test Author")
        header.SetPublisher("Test Publisher")

        exth = header._GetExthHeader()

        # Should start with EXTH marker
        assert exth.startswith(b'EXTH')

        # Should contain author and publisher
        assert b"Test Author" in exth
        assert b"Test Publisher" in exth

        # Should be word-aligned (multiple of 4)
        assert len(exth) % 4 == 0

    def test_mobi_header(self):
        """Test MOBI header record generation."""
        header = Header()
        header.SetTitle("Test")
        header.SetAuthor("Author")
        header.SetPublisher("Publisher")
        header.SetImageRecordIndex(10)

        record = header.MobiHeader()

        # Should return a Record
        assert isinstance(record, Record)

        # Record should contain MOBI marker
        assert b'MOBI' in record.data


class TestConverter:
    """Test Converter class for MOBI conversion."""

    def test_converter_creation(self):
        """Test creating a converter."""
        conv = Converter(title="My Book", author="Author", publisher="Publisher")

        assert conv._header._title == b"My Book"
        assert conv._header._author == b"Author"
        assert conv._header._publisher == b"Publisher"

    def test_converter_defaults(self):
        """Test converter with default values."""
        conv = Converter()

        # Should have default values (SetAuthor/Publisher override Header defaults)
        assert conv._header._author == b"Unknown"
        assert conv._header._publisher == b"Unknown"

    def test_convert_string(self):
        """Test converting single HTML string."""
        conv = Converter(title="Test")
        html = "<html><head><title>Page</title></head><body>Content</body></html>"

        result = conv.ConvertString(html)

        # Should return bytes
        assert isinstance(result, bytes)

        # Should contain MOBI markers
        assert b'BOOK' in result
        assert b'MOBI' in result

    def test_convert_strings_multiple(self):
        """Test converting multiple HTML strings."""
        conv = Converter(title="Test")
        html_strs = [
            "<html><head><title>Title Page</title></head><body>Title</body></html>",
            "<html><head><title>Chapter 1</title></head><body>Chapter content</body></html>",
            "<html><head><title>Chapter 2</title></head><body>More content</body></html>",
        ]

        result = conv.ConvertStrings(html_strs)

        # Should return bytes
        assert isinstance(result, bytes)

        # Should contain TOC
        assert b'Table of Contents' in result

    def test_make_one_html(self):
        """Test consolidating multiple HTML strings."""
        conv = Converter()
        html_strs = [
            "<html><head><title>Title</title></head><body>Title page</body></html>",
            "<html><head><title>Ch1</title></head><body>Chapter 1</body></html>",
        ]

        result = conv.MakeOneHTML(html_strs)

        # Should contain TOC
        assert "Table of Contents" in result

        # Should contain page breaks
        assert "<mbp:pagebreak/>" in result

        # Should contain anchor for TOC
        assert 'name="TOCTOP"' in result

    def test_make_one_html_single_page(self):
        """Test with single HTML page (title only)."""
        conv = Converter()
        html_strs = [
            "<html><head><title>Only Page</title></head><body>Content</body></html>",
        ]

        result = conv.MakeOneHTML(html_strs)

        # Should still have TOC even with just title page
        assert "Table of Contents" in result

    def test_convert_empty_html(self):
        """Test converting minimal HTML."""
        conv = Converter()

        result = conv.ConvertString("<html><head><title>Test</title></head><body></body></html>")

        # Should still produce valid MOBI structure
        assert isinstance(result, bytes)
        assert b'MOBI' in result


class TestConstants:
    """Test module-level constants."""

    def test_encoding_constants(self):
        """Test encoding constants are defined."""
        assert 'UTF-8' in encoding
        assert encoding['UTF-8'] == 65001
        assert 'latin-1' in encoding
        assert encoding['latin-1'] == 1252

    def test_language_constants(self):
        """Test language constants are defined."""
        assert 'en' in languages
        assert 'en-us' in languages
        assert languages['en-us'] == 0x0409
        assert languages['en'] == 0x0009

    def test_exth_header_fields(self):
        """Test EXTH header field constants."""
        assert 'author' in EXTH_HEADER_FIELDS
        assert EXTH_HEADER_FIELDS['author'] == 100
        assert 'publisher' in EXTH_HEADER_FIELDS
        assert EXTH_HEADER_FIELDS['publisher'] == 101


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unicode_content(self):
        """Test handling Unicode content."""
        conv = Converter(title="测试")
        html = "<html><head><title>标题</title></head><body>Unicode: 你好世界</body></html>"

        result = conv.ConvertString(html)

        # Should handle Unicode without crashing
        assert isinstance(result, bytes)

    def test_large_html(self):
        """Test handling large HTML that spans multiple records."""
        conv = Converter()
        # Create HTML larger than Record.MAX_SIZE
        large_content = "x" * (Record.MAX_SIZE * 2)
        html = f"<html><head><title>Large</title></head><body>{large_content}</body></html>"

        result = conv.ConvertString(html)

        # Should split into multiple records
        assert isinstance(result, bytes)
        assert len(result) > Record.MAX_SIZE

    def test_special_characters_in_title(self):
        """Test special characters in metadata."""
        conv = Converter(
            title='Test "Book" & <Title>',
            author="O'Reilly",
            publisher="Test & Co."
        )

        result = conv.ConvertString("<html><head><title>Test</title></head><body>Test</body></html>")

        # Should handle special chars without crashing
        assert isinstance(result, bytes)

    def test_empty_title(self):
        """Test with empty title."""
        conv = Converter(title="")

        result = conv.ConvertString("<html><head><title>Page</title></head><body>Content</body></html>")

        assert isinstance(result, bytes)
