"""
Configuration-Driven Adapter

Reads site configs from YAML files and extracts stories using selectors.
This allows adding new sites without writing code!
"""
from __future__ import annotations

import re
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import yaml

from ..models import Story, Chapter, Status, Rating, SiteConfig

logger = logging.getLogger(__name__)


class ConfigDrivenAdapter:
    """
    Generic adapter that works from YAML configuration files.

    Example YAML:
        name: "Archive of Our Own"
        domains:
          - archiveofourown.org
          - ao3.org

        story_url_pattern: 'works/(?P<story_id>\\d+)'

        selectors:
          title: "h2.title"
          author: "a[rel='author']"
          summary: "div.summary blockquote"
          chapters: "select#selected_id option"
          content: "div#workskin div.userstuff"
    """

    def __init__(self, config: SiteConfig):
        """
        Args:
            config: Site configuration (loaded from YAML)
        """
        self.config = config

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'ConfigDrivenAdapter':
        """Load adapter from YAML config file"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        config = SiteConfig(**config_data)
        return cls(config)

    @classmethod
    def from_domain(cls, domain: str, config_dir: Path) -> Optional['ConfigDrivenAdapter']:
        """
        Find and load config for a specific domain.

        Args:
            domain: Site domain (e.g., 'archiveofourown.org')
            config_dir: Directory containing YAML configs

        Returns:
            ConfigDrivenAdapter or None if not found
        """
        # Look for config files
        for yaml_file in config_dir.glob('*.yaml'):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)

                # Check if this config handles the domain
                if domain in config_data.get('domains', []):
                    config = SiteConfig(**config_data)
                    logger.info(f"Loaded config for {domain} from {yaml_file.name}")
                    return cls(config)
            except Exception as e:
                logger.warning(f"Failed to load {yaml_file}: {e}")

        return None

    def can_handle(self, url: str) -> bool:
        """Check if this adapter can handle the URL"""
        # Check domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.netloc not in self.config.domains:
            return False

        # Check URL pattern
        return bool(re.search(self.config.story_url_pattern, url, re.IGNORECASE))

    def extract_story_id(self, url: str) -> Optional[str]:
        """Extract story ID from URL using configured pattern"""
        match = re.search(self.config.story_url_pattern, url, re.IGNORECASE)
        if match:
            # Try to get named group 'story_id'
            try:
                return match.group('story_id')
            except:
                # Fall back to first group
                return match.group(1) if match.groups() else None
        return None

    def extract_metadata(self, html: str, url: str) -> Story:
        """Extract story metadata using configured selectors"""
        soup = BeautifulSoup(html, 'html.parser')
        story_id = self.extract_story_id(url) or "unknown"

        selectors = self.config.selectors.get('story', self.config.selectors)

        # Extract basic metadata
        title = self._extract_text(soup, selectors.get('title'), "Unknown Title")
        author = self._extract_text(soup, selectors.get('author'), "Unknown Author")
        summary = self._extract_text(soup, selectors.get('summary'), "")

        # Extract optional fields
        rating_text = self._extract_text(soup, selectors.get('rating'))
        rating = self._parse_rating(rating_text)

        status_text = self._extract_text(soup, selectors.get('status'))
        status = self._parse_status(status_text)

        # Extract lists (tags, genres, etc.)
        tags = self._extract_list(soup, selectors.get('tags', []))
        genres = self._extract_list(soup, selectors.get('genres', []))
        characters = self._extract_list(soup, selectors.get('characters', []))

        # Extract dates
        published = self._extract_date(soup, selectors.get('published'))
        updated = self._extract_date(soup, selectors.get('updated'))

        # Extract numbers
        word_count = self._extract_number(soup, selectors.get('words', selectors.get('word_count')))

        # Extract chapters
        chapters = self._extract_chapters(soup, selectors.get('chapters'), story_id, url)

        # Extract cover image
        cover_url = self._extract_attribute(soup, selectors.get('cover'), 'src')

        return Story(
            story_id=story_id,
            title=title,
            author=author,
            summary=summary,
            rating=rating,
            status=status,
            tags=tags,
            genre=genres,
            characters=characters,
            chapters=chapters,
            chapter_count=len(chapters),
            word_count=word_count,
            published=published,
            updated=updated,
            source_site=self.config.domains[0],
            source_url=url,
            cover_url=cover_url,
        )

    def extract_chapter_content(self, html: str) -> str:
        """Extract chapter content using configured selector"""
        soup = BeautifulSoup(html, 'html.parser')

        content_selector = self.config.selectors.get('chapter', {}).get('content') or \
                          self.config.selectors.get('content')

        if not content_selector:
            logger.warning("No content selector configured")
            return ""

        content = soup.select_one(content_selector)
        if content:
            return self._clean_html(content)

        return ""

    def _extract_text(self, soup: BeautifulSoup, selector: Optional[str], default: str = "") -> str:
        """Extract text using CSS selector"""
        if not selector:
            return default

        elem = soup.select_one(selector)
        return elem.get_text(strip=True) if elem else default

    def _extract_attribute(self, soup: BeautifulSoup, selector: Optional[str], attr: str) -> Optional[str]:
        """Extract attribute value using CSS selector"""
        if not selector:
            return None

        elem = soup.select_one(selector)
        return elem.get(attr) if elem else None

    def _extract_list(self, soup: BeautifulSoup, selector: Optional[str]) -> List[str]:
        """Extract list of text values using CSS selector"""
        if not selector:
            return []

        elems = soup.select(selector)
        return [elem.get_text(strip=True) for elem in elems]

    def _extract_date(self, soup: BeautifulSoup, selector: Optional[str]) -> Optional[datetime]:
        """Extract and parse date"""
        if not selector:
            return None

        # Try to get datetime attribute first
        elem = soup.select_one(selector)
        if not elem:
            return None

        # Try datetime attribute (common in <time> tags)
        if elem.get('datetime'):
            return self._parse_iso_date(elem['datetime'])

        # Try parsing text content
        date_text = elem.get_text(strip=True)
        return self._parse_date(date_text)

    def _extract_number(self, soup: BeautifulSoup, selector: Optional[str]) -> int:
        """Extract number from text"""
        text = self._extract_text(soup, selector)
        return self._parse_number(text)

    def _extract_chapters(
        self,
        soup: BeautifulSoup,
        selector: Optional[str],
        story_id: str,
        base_url: str
    ) -> List[Chapter]:
        """Extract chapter list"""
        if not selector:
            # Default to single chapter
            return [Chapter(number=1, title="Chapter 1", url=base_url)]

        chapters = []
        elems = soup.select(selector)

        for i, elem in enumerate(elems, 1):
            # Chapter title
            title = elem.get_text(strip=True)

            # Chapter URL
            href = elem.get('href') or elem.get('value')
            if href:
                chapter_url = self._make_absolute_url(href, base_url)
            else:
                chapter_url = base_url

            chapters.append(Chapter(
                number=i,
                title=title,
                url=chapter_url,
            ))

        return chapters if chapters else [Chapter(number=1, title="Chapter 1", url=base_url)]

    def _parse_rating(self, rating_text: Optional[str]) -> Rating:
        """Parse rating text to Rating enum"""
        if not rating_text:
            return Rating.NOT_RATED

        rating_lower = rating_text.lower()
        if 'explicit' in rating_lower:
            return Rating.EXPLICIT
        elif 'mature' in rating_lower:
            return Rating.MATURE
        elif 'teen' in rating_lower:
            return Rating.TEEN
        elif 'general' in rating_lower:
            return Rating.GENERAL

        return Rating.NOT_RATED

    def _parse_status(self, status_text: Optional[str]) -> Status:
        """Parse status text to Status enum"""
        if not status_text:
            return Status.IN_PROGRESS

        status_lower = status_text.lower()
        if 'complet' in status_lower:
            return Status.COMPLETED
        elif 'hiatus' in status_lower:
            return Status.HIATUS
        elif 'abandon' in status_lower:
            return Status.ABANDONED

        return Status.IN_PROGRESS

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date string"""
        if not date_text:
            return None

        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%Y/%m/%d',
            '%d.%m.%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_text.strip(), fmt)
            except:
                continue

        return None

    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """Parse ISO 8601 datetime"""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None

    def _parse_number(self, text: str) -> int:
        """Parse number from text"""
        if not text:
            return 0

        cleaned = re.sub(r'[^\d.]', '', text)
        try:
            return int(float(cleaned))
        except:
            return 0

    def _make_absolute_url(self, url: str, base_url: str) -> str:
        """Convert relative URL to absolute"""
        if url.startswith('http'):
            return url

        from urllib.parse import urljoin
        return urljoin(base_url, url)

    def _clean_html(self, element) -> str:
        """Clean HTML content"""
        for tag in element.find_all(['script', 'style', 'iframe']):
            tag.decompose()

        return str(element)
