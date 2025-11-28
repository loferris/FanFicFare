"""Base writer class for all story output formats.

This module provides the BaseStoryWriter abstract class that serves as the foundation
for all story format writers (EPUB, MOBI, HTML, TXT, etc.). It handles common
functionality like metadata formatting, title pages, table of contents, and file output.

All format-specific writers should inherit from this class and implement writeStoryImpl().
"""

# Copyright 2011 Fanficdownloader team, 2020 FanFicFare team
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

import datetime
import logging
import os.path
import string
from io import BytesIO
from typing import Any, BinaryIO, Callable, Optional, Union
from zipfile import ZipFile, ZIP_DEFLATED

from ..htmlcleanup import stripHTML
from ..requestable import Requestable

logger = logging.getLogger(__name__)

class BaseStoryWriter(Requestable):
    """Base class for all story format writers.

    Abstract base class that provides common functionality for writing stories
    in various formats (EPUB, MOBI, HTML, TXT, etc.). Handles metadata formatting,
    title pages, table of contents, and file I/O including zip output.

    Subclasses must implement:
        - getFormatName(): Return format name (e.g., 'epub', 'mobi')
        - getFormatExt(): Return file extension (e.g., '.epub', '.mobi')
        - writeStoryImpl(out): Write the actual story content

    Attributes:
        adapter: Story adapter instance
        story: Story metadata/content object
        metaonly: Whether to write only metadata (no chapters)
        outfilename: Output filename
        zipout: ZipFile instance when using zip output
    """

    @staticmethod
    def getFormatName() -> str:
        """Get the format name for this writer.

        Returns:
            Format name string (e.g., 'epub', 'mobi', 'html')
        """
        return 'base'

    @staticmethod
    def getFormatExt() -> str:
        """Get the file extension for this format.

        Returns:
            File extension including dot (e.g., '.epub', '.mobi')
        """
        return '.bse'

    def __init__(self, configuration: Any, adapter: Any) -> None:
        """Initialize the base writer.

        Args:
            configuration: Configuration object
            adapter: Story adapter instance
        """
        Requestable.__init__(self, configuration)

        self.adapter = adapter
        self.story = adapter.getStoryMetadataOnly()  # Only cache metadata initially

        self.story.setMetadata('formatname', self.getFormatName())
        self.story.setMetadata('formatext', self.getFormatExt())

    def getMetadata(self, key: str, removeallentities: bool = False) -> str:
        """Get metadata value with HTML stripped.

        Args:
            key: Metadata key to retrieve
            removeallentities: Whether to remove all HTML entities

        Returns:
            Metadata value with HTML tags stripped
        """
        return stripHTML(self.story.getMetadata(key, removeallentities))

    def getOutputFileName(self) -> str:
        """Get the output filename (zip or base depending on config).

        Returns:
            Output filename string
        """
        if self.getConfig('zip_output'):
            return self.getZipFileName()
        else:
            return self.getBaseFileName()

    def getBaseFileName(self) -> str:
        """Get the base output filename (story file without zip).

        Returns:
            Formatted base filename
        """
        return self.story.formatFileName(self.getConfig('output_filename'),
                                         self.getConfig('allow_unsafe_filename'))

    def getZipFileName(self) -> str:
        """Get the zip archive filename.

        Returns:
            Formatted zip filename
        """
        return self.story.formatFileName(self.getConfig('zip_filename'),
                                         self.getConfig('allow_unsafe_filename'))

    def _write(self, out: BinaryIO, text: Union[str, bytes]) -> None:
        """Write text to output stream as binary.

        Args:
            out: Output binary stream
            text: Text to write (str or bytes)
        """
        if isinstance(text, str):
            out.write(text.encode('utf-8'))
        else:
            out.write(text)

    def includeToCPage(self) -> bool:
        """Check if table of contents page should be included.

        Returns:
            True if TOC should be included, False otherwise
        """
        return ((self.getConfig("include_tocpage") == 'always' or
                (self.story.getChapterCount() > 1 and self.getConfig("include_tocpage")))
                and not self.metaonly)

    def writeTitlePage(self,
                       out: BinaryIO,
                       START: string.Template,
                       ENTRY: string.Template,
                       END: string.Template,
                       WIDE_ENTRY: Optional[string.Template] = None,
                       NO_TITLE_ENTRY: Optional[string.Template] = None) -> None:
        """Write the title page with metadata entries.

        Only includes entries that have metadata values. Templates can be
        overridden via configuration.

        Args:
            out: Output binary stream
            START: Template for title page start (uses Story.metadata names)
            ENTRY: Template for metadata entries (uses 'label', 'id', 'value')
            END: Template for title page end (uses Story.metadata names)
            WIDE_ENTRY: Optional template for wide entries (table columns)
            NO_TITLE_ENTRY: Optional template for entries without labels

        Note:
            Templates can be overridden via config: titlepage_start, titlepage_entry,
            titlepage_end, titlepage_wide_entry, titlepage_no_title_entry
        """
        if self.getConfig("include_titlepage"):

            if self.hasConfig("titlepage_start"):
                START = string.Template(self.getConfig("titlepage_start"))

            if self.hasConfig("titlepage_entry"):
                ENTRY = string.Template(self.getConfig("titlepage_entry"))

            if self.hasConfig("titlepage_end"):
                END = string.Template(self.getConfig("titlepage_end"))

            if self.hasConfig("titlepage_wide_entry"):
                WIDE_ENTRY = string.Template(self.getConfig("titlepage_wide_entry"))

            if self.hasConfig("titlepage_no_title_entry"):
                NO_TITLE_ENTRY = string.Template(self.getConfig("titlepage_no_title_entry"))

            self._write(out,START.substitute(self.story.getAllMetadata()))

            ## should only be include when titlepage_use_table:true
            if WIDE_ENTRY==None:
                WIDE_ENTRY=ENTRY

            titleEntriesList = self.getConfigList("titlepage_entries") + self.getConfigList("extra_titlepage_entries")
            wideTitleEntriesList = self.getConfigList("wide_titlepage_entries")

            for entry in titleEntriesList:
                # logger.debug("entry:%s"%entry)
                show_empty = False
                if entry.endswith('.SHOW_EMPTY'):
                    entry = entry[:-len('.SHOW_EMPTY')]
                    show_empty = True
                # logger.debug("entry:%s"%entry)
                # logger.debug("show_empty:%s"%show_empty)
                if self.isValidMetaEntry(entry):
                    if self.story.getMetadata(entry) or show_empty:
                        if entry in wideTitleEntriesList:
                            TEMPLATE=WIDE_ENTRY
                        else:
                            TEMPLATE=ENTRY

                        label=self.get_label(entry)

                        # If the label for the title entry is empty, use the
                        # 'no title' option if there is one.
                        if label == "" and NO_TITLE_ENTRY:
                           TEMPLATE= NO_TITLE_ENTRY

                        self._write(out,TEMPLATE.substitute({'label':label,
                                                             'id':entry,
                                                             'value':self.story.getMetadata(entry)}))
                else:
                    self._write(out, entry)

            self._write(out,END.substitute(self.story.getAllMetadata()))

    def writeTOCPage(self,
                     out: BinaryIO,
                     START: string.Template,
                     ENTRY: string.Template,
                     END: string.Template) -> None:
        """Write the table of contents page.

        Only writes TOC if there are multiple chapters and it's configured.
        Templates can be overridden via configuration.

        Args:
            out: Output binary stream
            START: Template for TOC start (uses Story.metadata names)
            ENTRY: Template for chapter entries (uses chapter dict keys)
            END: Template for TOC end (uses Story.metadata names)

        Note:
            Templates can be overridden via config: tocpage_start, tocpage_entry, tocpage_end
        """
        # Only do TOC if there's more than one chapter and it's configured
        if self.includeToCPage():
            if self.hasConfig("tocpage_start"):
                START = string.Template(self.getConfig("tocpage_start"))

            if self.hasConfig("tocpage_entry"):
                ENTRY = string.Template(self.getConfig("tocpage_entry"))

            if self.hasConfig("tocpage_end"):
                END = string.Template(self.getConfig("tocpage_end"))

            self._write(out,START.substitute(self.story.getAllMetadata()))

            for index, chap in enumerate(self.story.getChapters(fortoc=True)):
                if chap['html']:
                    self._write(out,ENTRY.substitute(chap))

            self._write(out,END.substitute(self.story.getAllMetadata()))

    def writeStory(self,
                   outstream: Optional[BinaryIO] = None,
                   metaonly: bool = False,
                   outfilename: Optional[str] = None,
                   forceOverwrite: bool = False,
                   notification: Callable[[Any, Any], Any] = lambda x, y: x) -> None:
        """Write the complete story to output stream or file.

        Main entry point for story writing. Handles both file and stream output,
        with optional zip compression. Fetches full story content unless metaonly
        is True. Checks file modification dates to avoid overwriting newer files.

        Args:
            outstream: Optional output binary stream. If None, writes to file.
            metaonly: If True, only write metadata (no chapter content).
            outfilename: Output filename. If None, uses getOutputFileName().
            forceOverwrite: If True, overwrite existing files regardless of date.
            notification: Callback for progress notifications (chapter_num, total).

        Note:
            - If outstream is None, writes to file specified by outfilename
            - Creates parent directories if make_directories config is True
            - Skips writing if existing file is newer than story update date
            - Supports zip output when zip_output config is True
        """

        self.metaonly = metaonly
        if outfilename == None:
            outfilename=self.getOutputFileName()

        self.outfilename = outfilename

        temp_css = ''
        # if the story has author-defined(AO3 workskin) CSS that we
        # want to include, include in FFF's CSS.
        if self.story.extra_css:
            temp_css = self.story.extra_css

        # output_css setting last so it can override
        if self.getConfig("output_css"):
            temp_css += self.getConfig("output_css")

        # minor cheat, tucking css into metadata.
        self.story.setMetadata("output_css",
                               temp_css,
                               condremoveentities=False)

        if not outstream:
            close=True
            logger.info(f"Save directly to file: {outfilename}")
            if self.getConfig('make_directories'):
                path=""
                # Ensure outfilename is a string (should already be from type hint)
                outfilename_str = outfilename if isinstance(outfilename, str) else str(outfilename)
                outputdirs = os.path.dirname(outfilename_str).split('/')
                for dir in outputdirs:
                    path+=dir+"/"
                    if not os.path.exists(path):
                        os.mkdir(path) ## os.makedirs() doesn't work in 2.5.2?

            ## Check for output file date vs updated date here
            if not (self.getConfig('always_overwrite') or forceOverwrite):
                if os.path.exists(outfilename):
                    ## date() truncs off time, which files have, but sites don't report.
                    lastupdated=self.story.getMetadataRaw('dateUpdated').date()
                    fileupdated=datetime.datetime.fromtimestamp(os.stat(outfilename)[8]).date()
                    if fileupdated > lastupdated:
                        logger.warning(f"File({outfilename}) Updated({fileupdated}) more recently than Story({lastupdated}) - Skipping")
                        return
            if not metaonly:
                # get full story now, just before writing.  Fetch
                # before opening file.
                self.story = self.adapter.getStory(notification)
            outstream = open(outfilename,"wb")
        else:
            close=False
            logger.debug("Save to stream")

        if not metaonly:
            # get full story now, just before writing.  Okay if double
            # called with above, it will only fetch once.
            self.story = self.adapter.getStory(notification)
        if self.getConfig('zip_output'):
            out = BytesIO()
            self.zipout = ZipFile(outstream, 'w', compression=ZIP_DEFLATED)
            self.writeStoryImpl(out)
            self.zipout.writestr(self.getBaseFileName(),out.getvalue())
            # declares all the files created by Windows.  otherwise, when
            # it runs in appengine, windows unzips the files as 000 perms.
            for zf in self.zipout.filelist:
                zf.create_system = 0
            self.zipout.close()
            out.close()
        else:
            self.writeStoryImpl(outstream)

        if close:
            outstream.close()

    def writeFile(self, filename: str, data: bytes) -> None:
        """Write a file to output (standalone file or zip archive).

        Helper method for writing additional files like images, CSS, or
        metadata files. Handles both zip and non-zip output modes.

        Args:
            filename: Output filename (relative to story file)
            data: Binary file content to write

        Note:
            - In zip mode, files are added to the zip archive
            - In non-zip mode, files are written alongside the story file
            - Automatically creates parent directories if needed
        """
        logger.debug(f"writeFile: {filename}")

        if self.getConfig('zip_output'):
            outputdirs = os.path.dirname(self.getBaseFileName())
            if outputdirs:
                filename=outputdirs+'/'+filename
            self.zipout.writestr(filename,data)
        else:
            outputdirs = os.path.dirname(self.outfilename)
            if outputdirs:
                filename=outputdirs+'/'+filename

            dir = os.path.dirname(filename)
            if not os.path.exists(dir):
                os.mkdir(dir) ## os.makedirs() doesn't work in 2.5.2?

            outstream = open(filename,"wb")
            outstream.write(data)
            outstream.close()

    def writeStoryImpl(self, out: BinaryIO) -> None:
        """Write format-specific story content (must be overridden by subclasses).

        Abstract method that subclasses must implement to write the actual
        story content in the specific format (EPUB, MOBI, HTML, TXT, etc.).

        Args:
            out: Output binary stream to write story content to

        Raises:
            NotImplementedError: If subclass doesn't implement this method

        Note:
            This is an abstract method. Subclasses should:
            - Write complete story content to the output stream
            - Use self.story for accessing metadata and chapters
            - Call writeTitlePage/writeTOCPage as appropriate
            - Handle format-specific formatting and structure
        """
        raise NotImplementedError("Subclasses must implement writeStoryImpl()")
