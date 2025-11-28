"""Text writer for FanFicFare stories.

This module provides the TextWriter class for exporting stories to plain text
files with optional word wrapping, table of contents, and configurable line endings.
"""

# Copyright 2011 Fanficdownloader team, 2018 FanFicFare team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
import string
from io import StringIO
from textwrap import wrap
from typing import Any, BinaryIO

from .base_writer import BaseStoryWriter
from ..htmlcleanup import removeAllEntities

logger = logging.getLogger(__name__)

from html2text import html2text


class KludgeStringIO:
    """String buffer that handles both str and bytes inputs.

    Helper class for buffering text content before word wrapping.
    Automatically decodes bytes to strings for compatibility with
    BaseStoryWriter's _write method which outputs bytes.

    In Python 3, this is primarily for backward compatibility.
    Could be replaced with io.StringIO if _write method is modified
    to not encode strings.
    """

    def __init__(self, buf: str = '') -> None:
        """Initialize empty string buffer.

        Args:
            buf: Initial buffer content (unused, for compatibility)
        """
        self.buflist = []

    def write(self, s: Any) -> None:
        """Write string or bytes to buffer.

        Args:
            s: String or bytes to write. Bytes are decoded to UTF-8.
        """
        try:
            s = s.decode('utf-8')
        except:
            pass
        self.buflist.append(s)

    def getvalue(self) -> str:
        """Get the complete buffer contents.

        Returns:
            Joined string from all written values
        """
        return ''.join(self.buflist)

    def close(self) -> None:
        """Close the buffer (no-op for compatibility).

        Note:
            This method is a no-op, provided for compatibility with
            file-like interface expectations.
        """
        pass


class TextWriter(BaseStoryWriter):
    """Plain text format writer for stories.

    Writes stories to plain text files with configurable word wrapping,
    table of contents, and line ending styles. Converts HTML content to
    plain text using html2text.

    Features:
        - Configurable word wrapping (wrap_width config)
        - Optional table of contents
        - Windows or Unix line endings (windows_eol config)
        - Custom templates for all text sections
        - HTML to plain text conversion
        - Entity removal for clean text output

    All text templates can be overridden via configuration.
    """

    @staticmethod
    def getFormatName() -> str:
        """Get the format name for this writer.

        Returns:
            Format name 'txt'
        """
        return 'txt'

    @staticmethod
    def getFormatExt() -> str:
        """Get the file extension for this format.

        Returns:
            File extension '.txt'
        """
        return '.txt'

    def __init__(self, config: Any, story: Any) -> None:
        """Initialize the text writer.

        Args:
            config: Configuration object
            story: Story adapter instance
        """
        
        BaseStoryWriter.__init__(self, config, story)

        self.TEXT_FILE_START = string.Template('''


${title}

by ${author}


''')

        self.TEXT_TITLE_PAGE_START = string.Template('''
''')

        self.TEXT_TITLE_ENTRY = string.Template('''${label}: ${value}
''')

        self.TEXT_TITLE_PAGE_END = string.Template('''


''')

        self.TEXT_TOC_PAGE_START = string.Template('''

TABLE OF CONTENTS

''')

        self.TEXT_TOC_ENTRY = string.Template('''
${chapter}
''')

        self.TEXT_TOC_PAGE_END = string.Template('''
''')

        self.TEXT_CHAPTER_START = string.Template('''

\t${chapter}

''')
        self.TEXT_CHAPTER_END = string.Template('')

        self.TEXT_FILE_END = string.Template('''

End file.
''')

    def writeStoryImpl(self, out: BinaryIO) -> None:
        """Write the text story content to output stream.

        Generates plain text output with story metadata, optional table of
        contents, and all chapter content. Applies word wrapping and line
        ending normalization.

        Args:
            out: Output binary stream to write text content to

        Note:
            - Converts HTML chapter content to plain text using html2text
            - Applies word wrapping based on wrap_width configuration
            - Normalizes line endings based on windows_eol configuration
            - Removes HTML entities for clean text output
        """

        self.wrap_width = self.getConfig('wrap_width')
        if self.wrap_width == '' or self.wrap_width == '0':
            self.wrap_width = 0
        else:
            self.wrap_width = int(self.wrap_width)
        
        wrapout = KludgeStringIO()
        
        if self.hasConfig("file_start"):
            FILE_START = string.Template(self.getConfig("file_start"))
        else:
            FILE_START = self.TEXT_FILE_START
            
        if self.hasConfig("file_end"):
            FILE_END = string.Template(self.getConfig("file_end"))
        else:
            FILE_END = self.TEXT_FILE_END
            
        wrapout.write(FILE_START.substitute(self.story.getAllMetadata()))

        self.writeTitlePage(wrapout,
                            self.TEXT_TITLE_PAGE_START,
                            self.TEXT_TITLE_ENTRY,
                            self.TEXT_TITLE_PAGE_END)
        towrap = wrapout.getvalue()
        
        self.writeTOCPage(wrapout,
                          self.TEXT_TOC_PAGE_START,
                          self.TEXT_TOC_ENTRY,
                          self.TEXT_TOC_PAGE_END)

        towrap = wrapout.getvalue()
        wrapout.close()
        towrap = removeAllEntities(towrap)
        
        self._write(out,self.lineends(self.wraplines(towrap)))

        if self.hasConfig('chapter_start'):
            CHAPTER_START = string.Template(self.getConfig("chapter_start"))
        else:
            CHAPTER_START = self.TEXT_CHAPTER_START
        
        if self.hasConfig('chapter_end'):
            CHAPTER_END = string.Template(self.getConfig("chapter_end"))
        else:
            CHAPTER_END = self.TEXT_CHAPTER_END
        
        for index, chap in enumerate(self.story.getChapters()):
            if chap['html']:
                # logger.debug('Writing chapter text for: %s' % chap['title'])
                self._write(out,self.lineends(self.wraplines(removeAllEntities(CHAPTER_START.substitute(chap)))))
                self._write(out,self.lineends(html2text(chap['html'],bodywidth=self.wrap_width)))
                self._write(out,self.lineends(self.wraplines(removeAllEntities(CHAPTER_END.substitute(chap)))))

        self._write(out,self.lineends(self.wraplines(FILE_END.substitute(self.story.getAllMetadata()))))

    def wraplines(self, text: str) -> str:
        """Apply word wrapping to text based on wrap_width.

        Wraps text to the configured line width, preserving paragraph breaks.
        If wrap_width is 0 or not set, returns text unchanged.

        Args:
            text: Text to wrap

        Returns:
            Wrapped text with line breaks inserted at wrap_width

        Note:
            - wrap_width of 0 disables wrapping
            - Preserves paragraph breaks (\\n\\n)
            - Each paragraph is wrapped independently
        """
        if not self.wrap_width:
            return text

        result = ''
        for para in text.split("\n"):
            first = True
            for line in wrap(para, self.wrap_width):
                if first:
                    first = False
                else:
                    result += "\n"
                result += line
            result += "\n"
        return result

    def lineends(self, txt: str) -> str:
        """Normalize line endings based on configuration.

        Converts Unix line endings (\\n) to Windows line endings (\\r\\n)
        if windows_eol config is True. Always removes existing \\r characters
        first to avoid double conversion.

        Args:
            txt: Text with Unix line endings

        Returns:
            Text with normalized line endings

        Note:
            - Always removes existing \\r characters first
            - Windows EOL mode: converts \\n to \\r\\n
            - Unix EOL mode (default): leaves \\n as-is
        """
        txt = txt.replace('\r', '')
        if self.getConfig("windows_eol"):
            txt = txt.replace('\n', '\r\n')
        return txt
                       
