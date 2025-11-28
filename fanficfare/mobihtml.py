"""HTML processing for MOBI format ebook generation.

This module processes HTML content specifically for the MOBI ebook format,
handling internal anchors, pre-formatted text, and MOBI-specific tags.
Used exclusively by mobi.py.

Note:
    Renamed July 2018 to avoid conflict with other 'html' packages.

Original Copyright (c) 2009 Andrew Chatham and Vijay Pandurangan
Changes Copyright 2018 FanFicFare team
"""

import logging
import re
from typing import List, Optional, Tuple
from urllib.parse import unquote

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HtmlProcessor:
    """Process HTML content for MOBI ebook format.

    Handles internal anchors, pre-formatted text, and MOBI-specific tag
    conversions. Removes unsupported tags and fixes HTML structure for
    optimal MOBI rendering.

    Attributes:
        WHITESPACE_RE: Regex pattern for matching whitespace
        unfill: Flag for paragraph vs line break mode (0=br, 1=p)
        title: Extracted title from HTML
        _soup: BeautifulSoup parsed HTML document
        _anchor_references: List of (anchor_num, href) tuples for internal links
    """

    WHITESPACE_RE = re.compile(r'\s')

    def __init__(self, html: str, unfill: int = 0) -> None:
        """Initialize HTML processor with content.

        Args:
            html: HTML content to process
            unfill: Paragraph mode flag (0 for line breaks, 1 for paragraphs)

        Note:
            Moves <guide> tag from <body> to <head> for MOBI compatibility.
            html5lib parser automatically moves it to body, so we fix it.
        """
        self.unfill = unfill
        self._soup = BeautifulSoup(html, 'html5lib')

        # MOBI format wants <guide> tag inside <head>
        # html5lib moves it to <body>, so we move it back
        guide = self._soup.find('guide')
        if guide:
            self._soup.head.append(guide)

        if self._soup.title.contents:
            self.title = self._soup.title.contents[0]
        else:
            self.title = None

  # Unnecessary with BS4
  # def _ProcessRawHtml(self, html):
  #   new_html, count = HtmlProcessor.BAD_TAG_RE.subn('<', html)
  #   if count:
  #     print >>sys.stderr, 'Replaced %d bad tags' % count
  #   return new_html

    def _StubInternalAnchors(self) -> None:
        """Replace internal anchors with fixed-size filepos placeholders.

        Finds all anchors with href="#myanchor" and replaces them with
        filepos="00000000050" placeholders. Stores anchor references for
        later replacement with actual file positions.

        Note:
            Also handles <reference> tags which are treated like anchor tags
            for table of contents functionality.
        """
        self._anchor_references: List[Tuple[int, str]] = []
        anchor_num = 0

        # Find anchor links
        anchorlist = self._soup.find_all('a', href=re.compile('^#'))
        # Treat reference tags like anchor tags for TOC
        anchorlist.extend(self._soup.find_all('reference', href=re.compile('^#')))

        for anchor in anchorlist:
            self._anchor_references.append((anchor_num, anchor['href']))
            anchor['filepos'] = f'{anchor_num:010d}'
            del anchor['href']
            anchor_num += 1

    def _ReplaceAnchorStubs(self) -> bytes:
        """Replace anchor filepos stubs with actual byte positions.

        Converts the HTML to bytes and finds the actual position of each
        anchor target, then replaces the placeholder filepos values with
        the actual byte offsets.

        Returns:
            HTML content as UTF-8 bytes with actual filepos values

        Note:
            Also fixes <mbp:pagebreak> tags to be self-closing for MOBI.
            TODO: Browsers allow extra whitespace in href names.
            TODO: Using regexes and looking for name= would be better.
        """
        assembled_text = str(self._soup).encode('utf-8')

        # html5lib/bs4 creates close tags for <mbp:pagebreak>, fix them
        assembled_text = assembled_text.replace(b'<mbp:pagebreak>', b'<mbp:pagebreak/>')
        assembled_text = assembled_text.replace(b'</mbp:pagebreak>', b'')

        del self._soup  # Shouldn't touch this anymore

        for anchor_num, original_ref in self._anchor_references:
            ref = unquote(original_ref[1:])  # Remove leading '#'

            # Find the position of ref in the UTF-8 document
            newpos = assembled_text.find(b'name="' + ref.encode('utf-8'))
            if newpos == -1:
                logger.warning(f'Could not find anchor "{original_ref}"')
                continue

            # Go right in front of the <a> tag by finding the < before it
            newpos = assembled_text.rfind(b'<', 0, newpos)

            old_filepos = f'filepos="{anchor_num:010d}"'.encode('utf-8')
            new_filepos = f'filepos="{newpos:010d}"'.encode('utf-8')
            assert assembled_text.find(old_filepos) != -1
            assembled_text = assembled_text.replace(old_filepos, new_filepos, 1)

        return assembled_text

    def _FixPreTags(self) -> None:
        """Replace <pre> tags with HTML-ified text.

        Converts preformatted text blocks to HTML with proper spacing,
        replacing whitespace with &nbsp; and adding line breaks or paragraphs.
        """
        pres = self._soup.find_all('pre')
        for pre in pres:
            pre.replace_with(self._FixPreContents(str(pre.contents[0])))

    def _FixPreContents(self, text: str) -> str:
        """Convert pre-formatted text to HTML with proper spacing.

        Args:
            text: Pre-formatted text content

        Returns:
            HTML-formatted text with &nbsp; for spaces and <br> or <p> tags

        Note:
            Uses <br> tags if unfill=0, <p> tags if unfill=1.
        """
        if self.unfill:
            line_splitter = '\n\n'
            line_joiner = '<p>'
        else:
            line_splitter = '\n'
            line_joiner = '<br>'

        lines = []
        for line in text.split(line_splitter):
            lines.append(self.WHITESPACE_RE.subn('&nbsp;', line)[0])

        return line_joiner.join(lines)

    def _RemoveUnsupported(self) -> None:
        """Remove tags that Kindle cannot handle.

        Removes <script> and <style> tags which are not supported
        in MOBI format ebooks.

        Note:
            TODO: Consider removing <link> tags to scripts as well.
        """
        unsupported_tags = ('script', 'style')
        for tag_type in unsupported_tags:
            for element in self._soup.find_all(tag_type):
                element.extract()

    def RenameAnchors(self, prefix: str) -> str:
        """Rename all internal anchors with the given prefix.

        Adds a prefix to all anchor hrefs and names to avoid conflicts
        when combining multiple HTML documents.

        Args:
            prefix: String to prepend to all anchor names and hrefs

        Returns:
            Contents of the body tag as a string

        Note:
            TODO: Sometimes body comes out as NoneType, need to investigate.
        """
        for anchor in self._soup.find_all('a', href=re.compile('^#')):
            anchor['href'] = '#' + prefix + anchor['href'][1:]

        for a in self._soup.find_all('a'):
            if a.get('name'):
                a['name'] = prefix + a['name']

        content = []
        if self._soup.body is not None:
            content = [str(c) for c in self._soup.body.contents]

        return '\n'.join(content)

    def CleanHtml(self) -> bytes:
        """Clean and process HTML for MOBI format.

        Main processing method that orchestrates all cleaning operations:
        1. Remove unsupported tags (script, style)
        2. Stub internal anchors with filepos placeholders
        3. Fix pre-formatted text blocks
        4. Replace anchor stubs with actual byte positions

        Returns:
            Processed HTML as UTF-8 bytes ready for MOBI format

        Note:
            TODO: Implement fix_html_br and fix_html improvements.
        """
        self._RemoveUnsupported()
        self._StubInternalAnchors()
        self._FixPreTags()
        return self._ReplaceAnchorStubs()


if __name__ == '__main__':
  FILE ='/tmp/documentation.html'
  #FILE = '/tmp/multipre.html'
  FILE = '/tmp/view.html'
  d = open(FILE).read()
  h = HtmlProcessor(d)
  s = h.CleanHtml()
  #print s
