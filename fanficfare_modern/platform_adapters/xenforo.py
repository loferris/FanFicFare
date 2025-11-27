"""
Generic XenForo Platform Adapter

Handles ALL XenForo forum-based fanfiction sites.
XenForo forums often host stories in threads with threadmarks for chapters.

Supported sites (automatically):
- forums.spacebattles.com
- forums.sufficientvelocity.com
- forum.questionablequesting.com
- alternatehistory.com forums
- Many others
"""
from __future__ import annotations

import re
import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from datetime import datetime

from ..models import Story, Chapter, Status, Rating

logger = logging.getLogger(__name__)


class XenForoAdapter:
    """
    Generic adapter for XenForo forum-based stories.

    XenForo stories are typically posted as forum threads with:
    - Threadmarks to mark story posts
    - Reader mode/Story-only view
    - First post contains story info
    """

    URL_PATTERN = r'/threads/([^/]+)\.(\d+)'

    def __init__(self, site_domain: str):
        self.site_domain = site_domain

    def can_handle(self, url: str) -> bool:
        """Check if URL is a XenForo thread URL"""
        return bool(re.search(self.URL_PATTERN, url, re.IGNORECASE))

    def extract_thread_id(self, url: str) -> Optional[str]:
        """Extract thread ID from URL"""
        match = re.search(self.URL_PATTERN, url, re.IGNORECASE)
        return match.group(2) if match else None

    def get_reader_mode_url(self, thread_id: str) -> str:
        """Get URL for reader/story-only mode"""
        return f"https://{self.site_domain}/threads/{thread_id}/reader"

    def get_threadmarks_url(self, thread_id: str) -> str:
        """Get URL for threadmarks list"""
        return f"https://{self.site_domain}/threads/{thread_id}/threadmarks"

    def extract_metadata(self, html: str, url: str) -> Story:
        """Extract story metadata from XenForo thread"""
        soup = BeautifulSoup(html, 'html.parser')
        thread_id = self.extract_thread_id(url) or "unknown"

        # Title is usually in h1.p-title-value
        title_elem = soup.select_one('h1.p-title-value, div.p-title h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Author is thread creator
        author_elem = soup.select_one('a.username, a[data-user-id]')
        author = author_elem.get_text(strip=True) if author_elem else "Unknown Author"

        # First post often contains summary
        first_post = soup.select_one('article.message--post:first-of-type div.bbWrapper')
        summary = ""
        if first_post:
            # Try to extract just the first paragraph as summary
            first_para = first_post.find('p')
            if first_para:
                summary = first_para.get_text(strip=True)[:500]

        # Extract threadmarks as chapters
        chapters = self._extract_threadmarks(soup, thread_id)

        # Dates
        published_elem = soup.select_one('time[datetime]')
        published = None
        if published_elem and published_elem.get('datetime'):
            published = self._parse_iso_date(published_elem['datetime'])

        return Story(
            story_id=thread_id,
            title=title,
            author=author,
            summary=summary,
            rating=Rating.NOT_RATED,  # Forums don't typically have ratings
            status=Status.IN_PROGRESS,  # Assume in progress
            chapters=chapters,
            chapter_count=len(chapters),
            published=published,
            source_site=self.site_domain,
            source_url=url,
        )

    def _extract_threadmarks(self, soup: BeautifulSoup, thread_id: str) -> List[Chapter]:
        """Extract threadmarks as chapters"""
        chapters = []

        # Look for threadmarks
        threadmark_items = soup.select('div.threadmarks-item, li.threadmark-item')

        if threadmark_items:
            for i, item in enumerate(threadmark_items, 1):
                # Threadmark title
                title_elem = item.select_one('a.threadmarks-label, a')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get('href', '')

                # Make absolute URL
                chapter_url = self._make_absolute_url(href)

                chapters.append(Chapter(
                    number=i,
                    title=title,
                    url=chapter_url,
                ))

        # If no threadmarks, try to extract from reader mode
        elif reader_posts := soup.select('article.message--post[data-content="threadmark-post"]'):
            for i, post in enumerate(reader_posts, 1):
                # Extract post ID for URL
                post_id = post.get('data-post-id', post.get('id', '').replace('post-', ''))

                # Try to find chapter title
                title_elem = post.select_one('h3, strong')
                title = title_elem.get_text(strip=True) if title_elem else f"Chapter {i}"

                chapter_url = f"https://{self.site_domain}/threads/{thread_id}/page-1#{post_id}"

                chapters.append(Chapter(
                    number=i,
                    title=title,
                    url=chapter_url,
                ))

        # If still no chapters, treat as single post
        if not chapters:
            chapters.append(Chapter(
                number=1,
                title="Chapter 1",
                url=f"https://{self.site_domain}/threads/{thread_id}/",
            ))

        return chapters

    def extract_chapter_content(self, html: str, chapter_number: int = 1) -> str:
        """Extract chapter content from XenForo post"""
        soup = BeautifulSoup(html, 'html.parser')

        # In reader mode, content is in article div.bbWrapper
        # In normal mode, it's in the post with matching threadmark

        # Try reader mode first
        content_elems = soup.select('article.message--post div.bbWrapper')

        if content_elems and chapter_number <= len(content_elems):
            content = content_elems[chapter_number - 1]
            return self._clean_html(content)

        # Fall back to first post content
        elif content_elems:
            return self._clean_html(content_elems[0])

        return ""

    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO 8601 datetime"""
        try:
            # Handle various ISO formats
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    def _make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute"""
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return f"https://{self.site_domain}{url}"
        return f"https://{self.site_domain}/{url}"

    def _clean_html(self, element) -> str:
        """Clean HTML content"""
        for tag in element.find_all(['script', 'style', 'iframe']):
            tag.decompose()

        return str(element)
