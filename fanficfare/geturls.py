"""URL extraction and processing utilities.

This module provides functions to extract fanfiction URLs from various sources:
- Web pages (HTML parsing)
- Plain text (regex-based extraction)
- Email via IMAP
- MIME data (for Calibre drag-and-drop)

It handles URL normalization, cleanup, and validation using site adapters.
"""

# Copyright 2015 Fanficdownloader team, 2020 FanFicFare team
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

import collections
import email
import imaplib
import logging
import re
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urlparse, urlunparse
from urllib.request import urlopen

from bs4 import BeautifulSoup, Tag

from . import adapters
from .configurable import Configuration
from .exceptions import UnknownSite, FetchEmailFailed

logger = logging.getLogger(__name__)

def get_urls_from_page(
    url: str,
    configuration: Optional[Configuration] = None,
    normalize: bool = False
) -> Dict[str, List[str]]:
    """Extract fanfiction URLs from a web page.

    Attempts to use a site-specific adapter to extract URLs. Falls back to
    generic HTML parsing for unknown sites.

    Args:
        url: URL of the page to extract from
        configuration: Configuration object (creates default if None)
        normalize: If True, return all URL variants; if False, return longest

    Returns:
        Dictionary with 'urllist' key containing extracted story URLs

    Examples:
        >>> # get_urls_from_page("https://archiveofourown.org/works/123")
        >>> # {'urllist': ['https://archiveofourown.org/works/123']}
    """
    if not configuration:
        configuration = Configuration(["test1.com"], "EPUB", lightweight=True)
    try:
        adapter = adapters.getAdapter(configuration, url, anyurl=True)
        return adapter.get_urls_from_page(url, normalize)
    except UnknownSite:
        # No adapter with anyurl=True, must be a random site
        # Use fake adapter just for get_request()
        # This allows users to set website_encodings for [test1.com]
        logger.debug(f"Using [test1.com] settings for unknown site URL({url})")
        adapter = adapters.getAdapter(configuration, "test1.com", anyurl=True)
        data = adapter.get_request(url)

        return {'urllist': get_urls_from_html(data, url, configuration, normalize)}
    return {}

def get_urls_from_html(
    data: Union[str, BeautifulSoup, Tag],
    url: Optional[str] = None,
    configuration: Optional[Configuration] = None,
    normalize: bool = False,
    foremail: bool = False
) -> List[str]:
    """Extract fanfiction URLs from HTML content.

    Parses HTML to find anchor tags with story URLs. Uses site adapters to
    validate and normalize URLs. Double-soups the HTML for better handling
    of malformed markup.

    Args:
        data: HTML string or BeautifulSoup object to parse
        url: Base URL for resolving relative links
        configuration: Configuration object (creates default if None)
        normalize: If True, return all URLs; if False, return longest per story
        foremail: If True, apply email-specific URL cleanup

    Returns:
        List of extracted story URLs (longest URL per story by default)

    Examples:
        >>> html = '<a href="https://example.com/story/123">Story</a>'
        >>> # get_urls_from_html(html)
        >>> # ['https://example.com/story/123']
    """
    urls = collections.OrderedDict()

    if not configuration:
        configuration = Configuration(["test1.com"], "EPUB", lightweight=True)

    if isinstance(data, (BeautifulSoup, Tag)):
        soup = data
    else:
        # Soup and re-soup because BS4/html5lib is more forgiving of
        # incorrectly nested tags that way
        soup = BeautifulSoup(str(BeautifulSoup(data, "html5lib")), "html5lib")

    for a in soup.find_all('a'):
        if a.has_attr('href'):
            href = form_url(url, a['href'])
            href = cleanup_url(href, configuration, foremail)
            try:
                adapter = adapters.getAdapter(configuration, href)
                if adapter.story.getMetadata('storyUrl') not in urls:
                    urls[adapter.story.getMetadata('storyUrl')] = [href]
                else:
                    urls[adapter.story.getMetadata('storyUrl')].append(href)
            except Exception:
                pass

    # Return all URLs if normalize, otherwise return longest URL per story
    return list(urls.keys()) if normalize else [max(value, key=len) for key, value in urls.items()]

def get_urls_from_text(
    data: Union[str, bytes],
    configuration: Optional[Configuration] = None,
    normalize: bool = False,
    foremail: bool = False
) -> List[str]:
    """Extract fanfiction URLs from plain text using regex.

    Finds URLs using regex pattern and validates them with site adapters.
    Handles markdown-style parentheses around URLs.

    Args:
        data: Text content (str or bytes)
        configuration: Configuration object (creates default if None)
        normalize: If True, return all URLs; if False, return longest per story
        foremail: If True, apply email-specific URL cleanup

    Returns:
        List of extracted story URLs (longest URL per story by default)

    Examples:
        >>> text = "Check out https://example.com/story/123"
        >>> # get_urls_from_text(text)
        >>> # ['https://example.com/story/123']
    """
    urls = collections.OrderedDict()
    try:
        # Python 3: handle bytes data
        if isinstance(data, bytes):
            data = data.decode('utf8', errors='replace')
        else:
            data = str(data)
    except UnicodeDecodeError:
        data = data.decode('utf8', errors='replace')

    if not configuration:
        configuration = Configuration(["test1.com"], "EPUB", lightweight=True)

    # Regex to find HTTP/HTTPS URLs
    url_pattern = r'\(?http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\)?'
    for href in re.findall(url_pattern, data):
        # Detect and remove parentheses around URL (markdown style)
        if href[0] == '(' and href[-1] == ')':
            href = href[1:-1]

        href = cleanup_url(href, configuration, foremail)
        try:
            adapter = adapters.getAdapter(configuration, href)
            if adapter.story.getMetadata('storyUrl') not in urls:
                urls[adapter.story.getMetadata('storyUrl')] = [href]
            else:
                urls[adapter.story.getMetadata('storyUrl')].append(href)
        except Exception:
            pass

    # Return all URLs if normalize, otherwise return longest URL per story
    return list(urls.keys()) if normalize else [max(value, key=len) for key, value in urls.items()]


def form_url(parenturl: Optional[str], url: str) -> str:
    """Form absolute URL from parent URL and relative/absolute URL.

    Resolves relative URLs to absolute using the parent URL as base.
    Handles absolute paths, relative paths, and protocol-relative URLs.

    Args:
        parenturl: Parent/base URL for resolution (can be None)
        url: URL to resolve (relative or absolute)

    Returns:
        Absolute URL string

    Examples:
        >>> form_url("https://example.com/stories/", "chapter2.html")
        "https://example.com/stories//chapter2.html"

        >>> form_url("https://example.com/page", "/about")
        "https://example.com/about"

    Note:
        Strips whitespace from URL to handle malformed markup.
        Double slashes in paths are valid and browser-compatible.
    """
    # Strip whitespace - we've seen images with spaces in src
    # Browsers handle it, so we should too
    url = url.strip()

    if "//" in url or parenturl is None:
        return url

    parsedUrl = urlparse(parenturl)
    if url.startswith("/"):
        # Absolute path
        return urlunparse((
            parsedUrl.scheme,
            parsedUrl.netloc,
            url,
            '', '', ''
        ))
    else:
        # Relative path
        if parsedUrl.path.endswith("/"):
            toppath = parsedUrl.path
        else:
            toppath = parsedUrl.path[:parsedUrl.path.rindex('/')]

        return urlunparse((
            parsedUrl.scheme,
            parsedUrl.netloc,
            toppath + '/' + url,
            '', '', ''
        ))

def cleanup_url(
    href: str,
    configuration: Configuration,
    foremail: bool = False
) -> str:
    """Clean up and normalize URLs for common issues.

    Handles site-specific URL cleanup including:
    - eFiction story.php parameter extraction
    - XenForo forum URL normalization for emails
    - Royal Road click-through redirect resolution
    - Parent directory (..) path cleanup

    Args:
        href: URL to clean up
        configuration: Configuration object for adapter access
        foremail: If True, apply email-specific cleanup rules

    Returns:
        Cleaned URL string (may be empty if URL should be skipped)

    Examples:
        >>> cleanup_url("https://site.com/story.php?sid=123&extra=1", config)
        "https://site.com/story.php?sid=123"

    Note:
        Some forum post URLs return empty string when from email.
        Royal Road click-through links are resolved by following redirect.
    """
    # Catch normal story links, javascript age-check links, and 'Report This' links
    if 'story.php' in href:  # Various eFiction and similar sites
        m = re.search(r"(?P<sid>(view)?story\.php\?(sid|psid|no|story|stid)=\d+)", href)
        if m is not None:
            href = form_url(href, m.group('sid'))

    if foremail and 'forum' in href:
        # XenForo emails: remove unread and page/post URLs
        # Emails only sent for thread updates
        # Handles AH, QQ, SB, SV; XF2 uses /posts/ or /post- instead of #post-
        if '/threads/' in href:
            href = re.sub(r"/(unread|page-\d+)?(#post-\d+)?(\?new=1)?", r"/", href)
        if re.match(r'.*/post(-|s/)\d+/?$', href):
            href = ""  # Skip post-only URLs

    # Royal Road has changed domains/URLs multiple times
    if foremail and ('click' in href or 'fiction/chapter' in href) and 'royalroad' in href:
        try:
            logger.debug(f"Doing Royal Road click-through link workaround({href})")
            adapter = adapters.getAdapter(configuration, "royalroad.com", anyurl=True)
            href = adapter.get_request_redirected(href)[1]
            href = href.replace('&index=1', '')
        except Exception as e:
            logger.warning(f"Skipping Royal Road email URL {href}, got HTTP error {e}")

    if '/../' in href:
        # For mcstories.com and similar, see issue #1160
        # urljoin() gets complex with javascript links and parameter URLs
        # normpath() would give backslashes on Windows
        href = re.sub(r'([^/]+/../)', r'', href)

    return href

def get_urls_from_imap(
    srv: str,
    user: str,
    passwd: str,
    folder: str,
    markread: bool = True,
    normalize_urls: bool = False
) -> Set[str]:
    """Extract story URLs from unread emails via IMAP.

    Connects to IMAP server, reads unread messages from specified folder,
    extracts URLs from both HTML and plain text email parts, and optionally
    marks messages as read.

    Args:
        srv: IMAP server address (e.g., "imap.gmail.com")
        user: IMAP username/email
        passwd: IMAP password
        folder: Folder name to check (e.g., "INBOX", "FanFic")
        markread: If True, mark processed emails as read
        normalize_urls: If True, return all URL variants; if False, longest

    Returns:
        Set of unique story URLs extracted from emails

    Raises:
        FetchEmailFailed: If login fails, folder not found, or selection fails

    Examples:
        >>> # urls = get_urls_from_imap("imap.gmail.com", "user", "pass", "INBOX")
        >>> # {'https://example.com/story/1', 'https://example.com/story/2'}

    Note:
        Uses SSL connection (IMAP4_SSL).
        Always calls mail.shutdown() via try/finally.
        Folder names with spaces are automatically quoted.
    """
    mail = imaplib.IMAP4_SSL(srv)
    try:
        status = mail.login(user, passwd)
        if status[0] != 'OK':
            raise FetchEmailFailed("Failed to login to mail server")
        # Out: list of "folders" aka labels in gmail.
        status = mail.list()
        # logger.debug(status)

        folders = []
        try:
            for f in status[1]:
                m = re.match(r'^\(.*\) "?."? "?(?P<folder>.+?)"?$',str(f))
                if m:
                    folders.append(m.group("folder").replace("\\",""))
                    # logger.debug(folders[-1])
                else:
                    logger.warning(f"Failed to parse IMAP folder line({str(f)})")
        except:
            folders = []
            logger.warning("Failed to parse IMAP folder list, continuing without list.")

        if status[0] != 'OK':
            raise FetchEmailFailed("Failed to list folders on mail server")

        # Needs to be quoted incase there are spaces, etc.  imaplib
        # doesn't correctly quote folders with spaces.  However, it does
        # check and won't quote strings that already start and end with ",
        # so this is safe.  There may be other chars than " that need escaping.
        escaped_folder = folder.replace('"', '\\"')
        status = mail.select(f'"{escaped_folder}"')
        if status[0] != 'OK':
            # logger.debug(status)
            if folders:
                raise FetchEmailFailed(f"Failed to select folder({folder}) on mail server (folder list:{folders})")
            else:
                raise FetchEmailFailed(f"Failed to select folder({folder}) on mail server")

        result, data = mail.uid('search', None, "UNSEEN")

        #logger.debug("result:%s"%result)
        #logger.debug("data:%s"%data)
        urls=set()

        #latest_email_uid = data[0].split()[-1]
        for email_uid in data[0].split():

            result, data = mail.uid('fetch', email_uid, '(BODY.PEEK[])') #RFC822

            # logger.debug("result:%s"%result)
            # logger.debug("data:%s"%data)

            raw_email = data[0][1]

        #raw_email = data[0][1] # here's the body, which is raw text of the whole email
        # including headers and alternate payloads

            try:
                email_message = email.message_from_string(str(raw_email))
            except Exception as e:
                logger.error(f"Failed decode email message: {e}", exc_info=True)
                continue

            # logger.debug("To:%s"%email_message['To'])
            # logger.debug("From:%s"%email_message['From'])
            # logger.debug("Subject:%s"%email_message['Subject'])
            # logger.debug("payload:%r"%email_message.get_payload(decode=True))

            urllist=[]
            for part in email_message.walk():
                try:
                    # logger.debug("part mime:%s"%part.get_content_type())
                    if part.get_content_type() == 'text/plain':
                        urllist.extend(get_urls_from_text(part.get_payload(decode=True),foremail=True, normalize=normalize_urls))
                    if part.get_content_type() == 'text/html':
                        urllist.extend(get_urls_from_html(part.get_payload(decode=True),foremail=True, normalize=normalize_urls))
                except Exception as e:
                    logger.error(f"Failed to read email content: {e}", exc_info=True)

            if urllist and markread:
                #obj.store(data[0].replace(' ',','),'+FLAGS','\Seen')
                r,d = mail.uid('store',email_uid,'+FLAGS','(\\SEEN)')
                #logger.debug("seen result:%s->%s"%(email_uid,r))

            [ urls.add(x) for x in urllist ]

        return urls
    finally:
        mail.shutdown()

def get_urls_from_mime(mime_data: Any) -> List[str]:
    """Extract story URLs from MIME data (drag-and-drop from email clients).

    Handles drag-and-drop of emails and links from Thunderbird and other email
    clients into Calibre. Processes .eml files, HTML content, plain text, and
    URI lists from the MIME data.

    Args:
        mime_data: QMimeData object from Qt drag-and-drop operation

    Returns:
        List of extracted story URLs from the MIME data

    Examples:
        >>> # When user drags .eml file from Thunderbird to Calibre:
        >>> # mime_data contains file:///path/to/message.eml
        >>> # urls = get_urls_from_mime(mime_data)
        >>> # ['https://example.com/story/123']

    Note:
        Supports multiple MIME formats:
        - text/uri-list: Direct file/URL drag
        - text/html: HTML content drag
        - text/plain: Plain text drag

        .eml files are parsed for both HTML and plain text parts.
        Firefox bookmarks may have encoded trailing CR (%0D) which is removed.
        Thunderbird RSS feeds include Content-Base header for URL extraction.
    """
    urllist = []
    if mime_data.hasFormat('text/uri-list'):
        # logger.debug("text/uri-list")
        # logger.debug(mime_data.urls())
        for qurl in mime_data.urls():
            f = qurl.toString()
            if f.endswith('%0D'):
                ## Firefox bookmarks, when dragged over, have an
                ## encoded trailing CR for... reasons?
                f = f[:-3]
            # logger.debug("filename:%s"%f)
            if f.endswith(".eml"):
                # logger.debug("calling urlopen(%s)"%f)
                # Using urllib.request.urlopen for file:// URLs only
                fhandle = urlopen(f)
                # Python 3: Use binary file reading
                msg = email.message_from_binary_file(fhandle)
                if msg.is_multipart():
                    for part in msg.walk():
                        # logger.debug("part type:%s"%part.get_content_type())
                        if part.get_content_type() == "text/html":
                            # logger.debug("URL list:%s"%get_urls_from_html(part.get_payload(decode=True)))
                            urllist.extend(get_urls_from_html(part.get_payload(decode=True),foremail=True))
                        if part.get_content_type() == "text/plain":
                            # logger.debug("part content:text/plain")
                            # logger.debug("part content:%s"%part.get_payload(decode=True))
                            urllist.extend(get_urls_from_text(part.get_payload(decode=True),foremail=True))
                else:
                    # logger.debug(msg.get_payload(decode=True))
                    urllist.extend(get_urls_from_text(msg.get_payload(decode=True),foremail=True))
                if 'Content-Base' in msg:
                    ## try msg header Content-Base.  Only known case
                    ## is Thunderbird RSS because one person uses it
                    ## and isn't shy about asking for stuff.
                    urllist.extend(get_urls_from_text(msg['Content-Base'],foremail=True))

            else:
                urllist.extend(get_urls_from_text(f))
    elif mime_data.hasFormat('text/html'):
        # logger.debug("text/html")
        urllist.extend(get_urls_from_html(mime_data.html()))
    elif mime_data.hasFormat('text/plain'):
        # logger.debug("text/plain")
        urllist.extend(get_urls_from_text(mime_data.text()))
    return urllist
