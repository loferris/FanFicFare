"""
Generic eFiction Platform Adapter

Handles ALL eFiction-based fanfiction archives with a single adapter.
eFiction is a popular PHP fanfiction archive system used by 20+ sites.

Supported sites (automatically):
- StoriesOnline.net
- AdultFanFiction.org
- MediaMiner.org
- Many others using eFiction software
"""
from __future__ import annotations

import re
import logging
from typing import Optional, List
from bs4 import BeautifulSoup
from datetime import datetime

from ..models import Story, Chapter, Status, Rating

logger = logging.getLogger(__name__)


class EFictionAdapter:
    """
    Generic adapter for eFiction-based archives.

    eFiction has a standard structure:
    - viewstory.php?sid=STORY_ID for story pages
    - printable version at &action=printable
    - Consistent HTML structure across sites
    """

    # Common eFiction selectors (work on most eFiction sites)
    DEFAULT_SELECTORS = {
        # Story metadata
        'title': 'div.pagetitle',
        'author': 'a[href*="viewuser.php"]',
        'summary': 'div.summary',
        'rating': 'span.label:contains("Rating") + span',
        'status': 'span.label:contains("Completed") + span',
        'category': 'span.label:contains("Category") + span',
        'genres': 'span.label:contains("Genre") + a',
        'characters': 'span.label:contains("Characters") + a',
        'published': 'span.label:contains("Published") + span',
        'updated': 'span.label:contains("Updated") + span',
        'words': 'span.label:contains("Words") + span',

        # Chapters
        'chapter_select': 'select[name="chapter"] option',
        'chapter_list': 'div.chapter-list a',

        # Content
        'content': 'div#story',
    }

    URL_PATTERN = r'viewstory\.php\?sid=(?P<story_id>\d+)'

    def __init__(self, site_domain: str, custom_selectors: Optional[dict] = None):
        """
        Args:
            site_domain: Domain name (e.g., 'storiesonline.net')
            custom_selectors: Optional overrides for default selectors
        """
        self.site_domain = site_domain
        self.selectors = {**self.DEFAULT_SELECTORS, **(custom_selectors or {})}

    def can_handle(self, url: str) -> bool:
        """Check if URL is an eFiction story URL"""
        return bool(re.search(self.URL_PATTERN, url, re.IGNORECASE))

    def extract_story_id(self, url: str) -> Optional[str]:
        """Extract story ID from URL"""
        match = re.search(self.URL_PATTERN, url, re.IGNORECASE)
        return match.group('story_id') if match else None

    def get_printable_url(self, story_id: str) -> str:
        """Get URL for printable version (easier to parse)"""
        return f"https://{self.site_domain}/viewstory.php?sid={story_id}&action=printable"

    def extract_metadata(self, html: str, url: str) -> Story:
        """
        Extract story metadata from eFiction page.

        Args:
            html: HTML content
            url: Story URL

        Returns:
            Story object with metadata (no chapter content yet)
        """
        soup = BeautifulSoup(html, 'html.parser')
        story_id = self.extract_story_id(url) or "unknown"

        # Extract title
        title_elem = soup.select_one(self.selectors['title'])
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Extract author
        author_elem = soup.select_one(self.selectors['author'])
        author = author_elem.get_text(strip=True) if author_elem else "Unknown Author"
        author_url = None
        if author_elem and author_elem.get('href'):
            author_url = self._make_absolute_url(author_elem['href'])

        # Extract summary
        summary_elem = soup.select_one(self.selectors['summary'])
        summary = summary_elem.get_text(strip=True) if summary_elem else ""

        # Extract rating
        rating_text = self._get_label_value(soup, 'Rating')
        rating = self._parse_rating(rating_text)

        # Extract status
        status_text = self._get_label_value(soup, 'Completed')
        status = Status.COMPLETED if status_text and 'yes' in status_text.lower() else Status.IN_PROGRESS

        # Extract categories/genres
        genres = []
        genre_elems = soup.select(self.selectors.get('genres', 'span.label:contains("Genre") + a'))
        for elem in genre_elems:
            genres.append(elem.get_text(strip=True))

        # Extract characters
        characters = []
        char_elems = soup.select(self.selectors.get('characters', 'span.label:contains("Characters") + a'))
        for elem in char_elems:
            characters.append(elem.get_text(strip=True))

        # Extract dates
        published_text = self._get_label_value(soup, 'Published')
        updated_text = self._get_label_value(soup, 'Updated')

        # Extract word count
        words_text = self._get_label_value(soup, 'Words')
        word_count = self._parse_number(words_text)

        # Extract chapters
        chapters = self._extract_chapter_list(soup, story_id)

        return Story(
            story_id=story_id,
            title=title,
            author=author,
            author_url=author_url,
            summary=summary,
            rating=rating,
            status=status,
            genre=genres,
            characters=characters,
            chapters=chapters,
            chapter_count=len(chapters),
            word_count=word_count,
            published=self._parse_date(published_text),
            updated=self._parse_date(updated_text),
            source_site=self.site_domain,
            source_url=url,
        )

    def _extract_chapter_list(self, soup: BeautifulSoup, story_id: str) -> List[Chapter]:
        """Extract chapter list from eFiction page"""
        chapters = []

        # Try chapter dropdown first (most common)
        chapter_options = soup.select(self.selectors['chapter_select'])
        if chapter_options:
            for i, option in enumerate(chapter_options, 1):
                chapter_id = option.get('value', str(i))
                chapter_title = option.get_text(strip=True)

                # Build chapter URL
                chapter_url = f"https://{self.site_domain}/viewstory.php?sid={story_id}&chapter={chapter_id}"

                chapters.append(Chapter(
                    number=i,
                    title=chapter_title,
                    url=chapter_url,
                ))

        # Fall back to chapter links if no dropdown
        elif chapter_links := soup.select(self.selectors.get('chapter_list', 'div.chapter-list a')):
            for i, link in enumerate(chapter_links, 1):
                chapters.append(Chapter(
                    number=i,
                    title=link.get_text(strip=True),
                    url=self._make_absolute_url(link['href']),
                ))

        # If no chapters found, treat as single-chapter story
        if not chapters:
            chapters.append(Chapter(
                number=1,
                title="Chapter 1",
                url=f"https://{self.site_domain}/viewstory.php?sid={story_id}",
            ))

        return chapters

    def extract_chapter_content(self, html: str) -> str:
        """Extract chapter text from eFiction page"""
        soup = BeautifulSoup(html, 'html.parser')

        # Find story content
        content_elem = soup.select_one(self.selectors['content'])
        if not content_elem:
            # Try common alternatives
            content_elem = soup.select_one('div.storytext')
            if not content_elem:
                content_elem = soup.select_one('div#storytext')

        if content_elem:
            # Clean up the HTML
            return self._clean_html(content_elem)

        return ""

    def _get_label_value(self, soup: BeautifulSoup, label: str) -> Optional[str]:
        """Get value following a label (common eFiction pattern)"""
        # Try format: <span class="label">Label:</span> <span>Value</span>
        label_elem = soup.find('span', class_='label', string=re.compile(label, re.IGNORECASE))
        if label_elem:
            next_elem = label_elem.find_next_sibling()
            if next_elem:
                return next_elem.get_text(strip=True)

        # Try format: <b>Label:</b> Value
        bold_elem = soup.find('b', string=re.compile(label, re.IGNORECASE))
        if bold_elem:
            # Get text after the bold tag
            text = bold_elem.next_sibling
            if text:
                return str(text).strip()

        return None

    def _parse_rating(self, rating_text: Optional[str]) -> Rating:
        """Parse rating text to Rating enum"""
        if not rating_text:
            return Rating.NOT_RATED

        rating_lower = rating_text.lower()
        if 'explicit' in rating_lower or 'nc-17' in rating_lower or 'adult' in rating_lower:
            return Rating.EXPLICIT
        elif 'mature' in rating_lower or 'r' in rating_lower:
            return Rating.MATURE
        elif 'teen' in rating_lower or 'pg-13' in rating_lower:
            return Rating.TEEN
        elif 'general' in rating_lower or 'g' in rating_lower or 'pg' in rating_lower:
            return Rating.GENERAL

        return Rating.NOT_RATED

    def _parse_date(self, date_text: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_text:
            return None

        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_text.strip(), fmt)
            except:
                continue

        return None

    def _parse_number(self, text: Optional[str]) -> int:
        """Parse number from text (handles commas, etc.)"""
        if not text:
            return 0

        # Remove non-digit characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', text)
        try:
            return int(float(cleaned))
        except:
            return 0

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
        """Clean HTML content (remove scripts, styles, etc.)"""
        # Remove unwanted elements
        for tag in element.find_all(['script', 'style', 'iframe']):
            tag.decompose()

        # Get cleaned HTML
        return str(element)
