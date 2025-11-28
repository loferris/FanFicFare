"""MOBI ebook format writer.

This module provides classes for converting HTML content to MOBI/AZW3 ebook format.
It handles the PDB (Palm Database) container format and MOBI-specific headers.

Main components:
- Converter: High-level API for HTML to MOBI conversion
- Header: MOBI header generation with metadata
- Record: PDB record management and binary data handling
- _SubEntry: HTML entry processing for multi-chapter books

References:
- http://wiki.mobileread.com/wiki/MOBI
- http://membres.lycos.fr/microfirst/palm/pdb.html
"""

# Copyright(c) 2009 Andrew Chatham and Vijay Pandurangan
# Changes Copyright 2018 FanFicFare team

import logging
import random
import struct
import time
from io import BytesIO
from typing import BinaryIO, Dict, List, Optional, Tuple

from .mobihtml import HtmlProcessor

logger = logging.getLogger(__name__)

encoding: Dict[str, int] = {
    'UTF-8': 65001,
    'latin-1': 1252,
}

languages: Dict[str, int] = {
    "en-us": 0x0409,
    "sv": 0x041d,
    "fi": 0x000b,
    "en": 0x0009,
    "en-gb": 0x0809,
}


class _SubEntry:
    """HTML entry for multi-chapter MOBI books.

    Processes individual HTML chapters/articles for inclusion in MOBI file.
    Generates table of contents links and renames anchors to avoid conflicts.

    Attributes:
        pos: Position/chapter number
        html: HtmlProcessor instance for this entry
        title: Chapter/article title
        _name: Internal name for anchor generation
    """

    def __init__(self, pos: int, html_data: str) -> None:
        """Initialize a sub-entry.

        Args:
            pos: Chapter position (1-indexed)
            html_data: HTML content string
        """
        self.pos = pos
        self.html = HtmlProcessor(html_data)
        self.title = self.html.title
        self._name = f'mobi_article_{pos}'
        if not self.title:
            self.title = f'Article {self.pos}'

    def TocLink(self) -> str:
        """Generate table of contents link HTML.

        Returns:
            Anchor tag linking to this chapter (title truncated to 80 chars)
        """
        return f'<a href="#{self._name}_MOBI_START">{self.title:.80}</a>'

    def Anchor(self) -> str:
        """Generate chapter start anchor HTML.

        Returns:
            Named anchor tag for chapter start
        """
        return f'<a name="{self._name}_MOBI_START">'

    def Body(self) -> str:
        """Get chapter body HTML with renamed anchors.

        Returns:
            HTML content with anchors renamed to avoid conflicts
        """
        return self.html.RenameAnchors(self._name + '_')

class Converter:
    """Convert HTML content to MOBI ebook format.

    High-level API for creating MOBI files from HTML strings or files.
    Handles metadata, table of contents generation, and binary format output.

    Attributes:
        _header: MOBI header with metadata
        _refresh_url: Optional refresh URL (unused in current implementation)
    """

    def __init__(
        self,
        refresh_url: str = '',
        title: str = 'Unknown',
        author: str = 'Unknown',
        publisher: str = 'Unknown'
    ) -> None:
        """Initialize MOBI converter with metadata.

        Args:
            refresh_url: Optional refresh URL (unused)
            title: Book title
            author: Author name
            publisher: Publisher name
        """
        self._header = Header()
        self._header.SetTitle(title)
        self._header.SetAuthor(author)
        self._header.SetPublisher(publisher)
        self._refresh_url = refresh_url

    def ConvertString(self, s: str) -> bytes:
        """Convert single HTML string to MOBI format.

        Args:
            s: HTML content string

        Returns:
            Complete MOBI file as bytes
        """
        out = BytesIO()
        self._ConvertStringToFile(s, out)
        return out.getvalue()

    def ConvertStrings(self, html_strs: List[str]) -> bytes:
        """Convert multiple HTML strings to MOBI format.

        Combines multiple HTML documents into single MOBI with table of contents.

        Args:
            html_strs: List of HTML content strings (first is title page)

        Returns:
            Complete MOBI file as bytes
        """
        out = BytesIO()
        self._ConvertStringsToFile(html_strs, out)
        return out.getvalue()

    def ConvertFile(self, html_file: str, out_file: str) -> None:
        """Convert HTML file to MOBI file.

        Args:
            html_file: Path to input HTML file
            out_file: Path to output MOBI file
        """
        self._ConvertStringToFile(open(html_file, 'rb').read(),
                                  open(out_file, 'wb'))

    def ConvertFiles(self, html_files: List[str], out_file: str) -> None:
        """Convert multiple HTML files to MOBI file.

        Args:
            html_files: List of paths to input HTML files
            out_file: Path to output MOBI file
        """
        html_strs = [open(f, 'rb').read() for f in html_files]
        self._ConvertStringsToFile(html_strs, open(out_file, 'wb'))

    def MakeOneHTML(self, html_strs: List[str]) -> str:
        """Consolidate multiple HTML strings into single HTML file.

        Constructs table of contents and adds anchors for navigation.
        First HTML string is treated as title page.

        Args:
            html_strs: List of HTML content strings

        Returns:
            Consolidated HTML string with TOC

        Note:
            Inserts <mbp:pagebreak/> tags between sections (processed by mobihtml).
        """
        title_html: List[str] = []
        toc_html: List[str] = []
        body_html: List[str] = []

        # This gets broken by html5lib/bs4fixed being helpful, but we'll
        # fix it inside mobihtml.py
        PAGE_BREAK = '<mbp:pagebreak/>'

        # Pull out the title page, assumed first html_strs
        htmltitle = html_strs[0]
        entrytitle = _SubEntry(1, htmltitle)
        title_html.append(entrytitle.Body())

        title_html.append(PAGE_BREAK)
        toc_html.append(PAGE_BREAK)
        toc_html.append('<a name="TOCTOP"><h3>Table of Contents</h3><br />')

        for pos, html in enumerate(html_strs[1:]):
            entry = _SubEntry(pos + 1, html)
            toc_html.append(f'{entry.TocLink()}<br />')

            # Give some space between bodies of work
            body_html.append(PAGE_BREAK)

            body_html.append(entry.Anchor())

            body_html.append(entry.Body())

        # TODO: this title can get way too long with RSS feeds. Not sure how to fix
        # Cheat slightly and use the <a href> code to set filepos in references
        current_time = time.ctime(time.time())
        header = f'''<html>
<head>
<title>Bibliorize {current_time} GMT</title>
  <guide>
    <reference href="#TOCTOP" type="toc" title="Table of Contents"/>
  </guide>
</head>
<body>
'''

        footer = '</body></html>'
        all_html = header + '\n'.join(title_html + toc_html + body_html) + footer
        return all_html

    def _ConvertStringsToFile(self, html_strs: List[str], out_file: BinaryIO) -> None:
        """Convert multiple HTML strings to MOBI file (internal).

        Args:
            html_strs: List of HTML content strings
            out_file: Output binary file object
        """
        try:
            tmp = self.MakeOneHTML(html_strs)
            self._ConvertStringToFile(tmp, out_file)
        except Exception as e:
            logger.error('Error %s', e)
            raise

    def _ConvertStringToFile(self, html_data: str, out: BinaryIO) -> None:
        """Convert HTML string to MOBI file (internal).

        Args:
            html_data: HTML content string
            out: Output binary file object
        """
        html = HtmlProcessor(html_data)
        cleaned = html.CleanHtml()
        # Ensure binary data for struct packing
        data = cleaned.encode('utf-8') if isinstance(cleaned, str) else cleaned

        # Collect offsets of '<mbp:pagebreak>' tags, use to make index list
        # indexlist = [] # list of (offset,length) tuples - not in current use

        records: List[Record] = []
        record_id = 1

        # Split data into Record.MAX_SIZE chunks
        for start_pos in range(0, len(data), Record.MAX_SIZE):
            end = min(len(data), start_pos + Record.MAX_SIZE)
            record_data = data[start_pos:end]
            records.append(self._header.AddRecord(record_data, record_id))
            record_id += 1

        self._header.SetImageRecordIndex(record_id)
        records[0:0] = [self._header.MobiHeader()]

        header, rec_offset = self._header.PDBHeader(len(records))
        # Ensure binary for PDB header
        header_bytes = header.encode('utf-8') if isinstance(header, str) else header
        out.write(header_bytes)

        for record in records:
            record.WriteHeader(out, rec_offset)
            rec_offset += (len(record.data) + 1)  # Plus one for trailing null

        # Write two nuls for some reason
        out.write(b'\0\0')
        for record in records:
            record.WriteData(out)
            out.write(b'\0')
            # Needs a trailing null, I believe it indicates zero length 'overlap'
            # Otherwise, the readers eat the last char of each html record
            # Calibre writes another 6-7 bytes of stuff after that, but we seem
            # to be getting along without it

class Record:
    """PDB record for MOBI format.

    Handles individual data records in the Palm Database format.
    Each record contains a chunk of HTML data (max 4KB) or header information.

    Attributes:
        MAX_SIZE: Maximum record data size (4096 bytes)
        INDEX_LEN: Record index header length (8 bytes)
        _unique_id_seed: Class-level unique ID counter
        data: Binary record data
        _id: Record ID
    """

    MAX_SIZE: int = 4096
    INDEX_LEN: int = 8
    _unique_id_seed: int = 28  # Should be arbitrary, but taken from MobiHeader

    # TODO(chatham): Record compression doesn't look that hard

    def __init__(self, data: bytes, record_id: int) -> None:
        """Initialize a record.

        Args:
            data: Binary record data (max MAX_SIZE bytes)
            record_id: Record ID (0 for auto-generated)

        Raises:
            AssertionError: If data exceeds MAX_SIZE
        """
        assert len(data) <= self.MAX_SIZE
        self.data = data
        if record_id != 0:
            self._id = record_id
        else:
            Record._unique_id_seed += 1
            self._id = 0

    def __repr__(self) -> str:
        """String representation of record."""
        return f'Record: id={self._id} len={len(self.data)}'

    def _SetUniqueId(self) -> None:
        """Set unique record ID (internal)."""
        Record._unique_id_seed += 1
        # TODO(chatham): Wraparound handling
        self._id = Record._unique_id_seed

    def WriteData(self, out: BinaryIO) -> None:
        """Write record data to output.

        Args:
            out: Output binary file object
        """
        # Ensure data is bytes
        data_bytes = self.data.encode('utf-8') if isinstance(self.data, str) else self.data
        out.write(data_bytes)

    def WriteHeader(self, out: BinaryIO, rec_offset: int) -> None:
        """Write record index header to output.

        Args:
            out: Output binary file object
            rec_offset: Record offset in file
        """
        attributes = 64  # Dirty flag
        header = struct.pack('>IbbH',
                             rec_offset,
                             attributes,
                             0, self._id)
        assert len(header) == Record.INDEX_LEN
        out.write(header)

EXTH_HEADER_FIELDS: Dict[str, int] = {
    'author': 100,
    'publisher': 101,
}


class Header:
    """MOBI header with metadata.

    Generates MOBI format headers including PDB header, PalmDoc header,
    MOBI header, and EXTH (extended) header with metadata.

    Attributes:
        EPOCH_1904: Epoch offset for PDB timestamps (Jan 1, 1904)
        _length: Total data length
        _record_count: Number of records
        _title: Book title (bytes)
        _author: Author name (bytes)
        _publisher: Publisher name (bytes)
        _first_image_index: Index of first image record
    """

    EPOCH_1904: int = 2082844800

    def __init__(self) -> None:
        """Initialize header with default values."""
        self._length: int = 0
        self._record_count: int = 0
        self._title: bytes = b'2008_2_34'
        self._author: bytes = b'Unknown author'
        self._publisher: bytes = b'Unknown publisher'
        self._first_image_index: int = 0

    def SetAuthor(self, author: str) -> None:
        """Set author name.

        Args:
            author: Author name (converted to ASCII, non-ASCII chars ignored)
        """
        self._author = author.encode('ascii', 'ignore')

    def SetTitle(self, title: str) -> None:
        """Set book title.

        Args:
            title: Book title (converted to ASCII, non-ASCII chars ignored)

        Note:
            ASCII encoding required for compatibility with PDB header.
        """
        self._title = title.encode('ascii', 'ignore')

    def SetPublisher(self, publisher: str) -> None:
        """Set publisher name.

        Args:
            publisher: Publisher name (converted to ASCII, non-ASCII chars ignored)
        """
        self._publisher = publisher.encode('ascii', 'ignore')

    def AddRecord(self, data: bytes, record_id: int) -> Record:
        """Add a data record.

        Args:
            data: Binary record data
            record_id: Record ID

        Returns:
            Created Record object
        """
        self.max_record_size = max(Record.MAX_SIZE, len(data))
        self._record_count += 1
        self._length += len(data)
        return Record(data, record_id)

    def _ReplaceWord(self, data: bytes, pos: int, word: int) -> bytes:
        """Replace 4-byte word in binary data.

        Args:
            data: Binary data
            pos: Position to replace
            word: 32-bit value to insert

        Returns:
            Modified binary data
        """
        return data[:pos] + struct.pack('>I', word) + data[pos + 4:]

    def PalmDocHeader(self) -> bytes:
        """Generate PalmDoc header (16 bytes).

        Returns:
            PalmDoc header binary data
        """
        compression = 1  # No compression
        unused = 0
        encryption_type = 0  # No encryption
        records = self._record_count + 1  # The header record itself
        palmdoc_header = struct.pack('>HHIHHHH',
                                     compression,
                                     unused,
                                     self._length,
                                     records,
                                     Record.MAX_SIZE,
                                     encryption_type,
                                     unused)
        assert len(palmdoc_header) == 16
        return palmdoc_header

    def PDBHeader(self, num_records: int) -> Tuple[bytes, int]:
        """Generate PDB (Palm Database) header.

        Args:
            num_records: Total number of records

        Returns:
            Tuple of (header bytes, record offset)
        """
        HEADER_LEN = 32 + 2 + 2 + 9 * 4
        RECORD_INDEX_HEADER_LEN = 6

        index_len = RECORD_INDEX_HEADER_LEN + num_records * Record.INDEX_LEN
        rec_offset = HEADER_LEN + index_len + 2

        short_title = self._title[0:31]
        attributes = 0
        version = 0
        current_time = int(time.time())
        ctime = self.EPOCH_1904 + current_time
        mtime = self.EPOCH_1904 + current_time
        backup_time = self.EPOCH_1904 + current_time
        modnum = 0
        appinfo_offset = 0
        sort_offset = 0
        db_type = b'BOOK'
        creator = b'MOBI'
        id_seed = 36

        header = struct.pack('>32sHHII',
                             short_title, attributes, version,
                             ctime, mtime)
        header += struct.pack('>IIII', backup_time, modnum,
                              appinfo_offset, sort_offset)
        header += struct.pack('>4s4sI',
                              db_type, creator, id_seed)
        next_record = 0  # Not used
        header += struct.pack('>IH', next_record, num_records)
        return header, rec_offset

    def _GetExthHeader(self) -> bytes:
        """Generate EXTH (extended) header with metadata.

        Returns:
            EXTH header binary data
        """
        # Set author, publisher (could add coveroffset, thumboffset)
        data = {
            'author': self._author,
            'publisher': self._publisher,
        }

        # Turn string type names into EXTH typeids
        r: List[bytes] = []
        for key, value in data.items():
            typeid = EXTH_HEADER_FIELDS[key]
            length_encoding_len = 8
            r.append(struct.pack('>LL', typeid, len(value) + length_encoding_len) + value)
        content = b''.join(r)

        # Pad to word boundary
        while len(content) % 4:
            content += b'\0'

        TODO_mysterious = 12
        exth = b'EXTH' + struct.pack('>LL', len(content) + TODO_mysterious, len(data)) + content
        return exth

    def SetImageRecordIndex(self, idx: int) -> None:
        """Set index of first image record.

        Args:
            idx: Record index where images start
        """
        self._first_image_index = idx

    def MobiHeader(self) -> Record:
        """Generate complete MOBI header record.

        Creates header record (Record 0) containing PalmDoc, MOBI, and EXTH headers.

        Returns:
            Header Record object
        """
        exth_header = self._GetExthHeader()
        palmdoc_header = self.PalmDocHeader()

        fs = 0xffffffff

        # Record 0
        header_len = 0xE4  # TODO: Why this specific length?
        mobi_type = 2  # BOOK
        text_encoding = encoding['UTF-8']
        unique_id = random.randint(1, 1 << 32)
        creator_version = 4
        reserved = b'\xff' * 40
        nonbook_index = fs

        # Put full name after header
        full_name_offset = header_len + len(palmdoc_header) + len(exth_header)
        language = languages['en-us']
        unused = 0

        mobi_header = struct.pack('>4sIIIII40sIIIIII',
                                  b'MOBI',
                                  header_len,
                                  mobi_type,
                                  text_encoding,
                                  unique_id,
                                  creator_version,
                                  reserved,
                                  nonbook_index,
                                  full_name_offset,
                                  len(self._title),
                                  language,
                                  fs, fs)
        assert len(mobi_header) == 104 - 16

        drm_offset = 0
        drm_count = 0
        drm_size = 0
        drm_flags = 0
        exth_flags = 0x50

        mobi_header += struct.pack('>IIIIIII',
                                   creator_version,
                                   self._first_image_index,
                                   fs,
                                   unused,
                                   fs,
                                   unused,
                                   exth_flags)
        mobi_header += b'\0' * 112  # TODO: Why this much padding?

        # Set some magic offsets to be 0xFFFFFFFF
        for pos in (0x94, 0x98, 0xb0, 0xb8, 0xc0, 0xc8, 0xd0, 0xd8, 0xdc):
            mobi_header = self._ReplaceWord(mobi_header, pos, fs)

        padding = b'\0' * 48 * 4  # TODO: Why 48*4 bytes?
        total_header = palmdoc_header + mobi_header + exth_header + self._title + padding

        return self.AddRecord(total_header, 0)

if __name__ == '__main__':
    import sys
    m = Converter(title='Testing Mobi', author='Mobi Author', publisher='mobi converter')
    m.ConvertFiles(sys.argv[1:], 'test.mobi')
