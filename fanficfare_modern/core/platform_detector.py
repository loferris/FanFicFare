"""
Platform Detection System

Automatically detects which platform a fanfiction site uses,
allowing us to use generic platform adapters instead of site-specific ones.
"""
from __future__ import annotations

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlatformSignature:
    """Signature for detecting a platform"""
    name: str
    priority: int  # Higher = checked first
    html_signatures: List[str]  # CSS selectors or text patterns
    meta_tags: List[Tuple[str, str]]  # (name/property, content pattern)
    url_patterns: List[str]  # URL structure patterns
    script_patterns: List[str]  # JavaScript file patterns


class PlatformDetector:
    """
    Detects which platform a fanfiction site is built on.

    Supports:
    - eFiction (and derivatives)
    - XenForo (forum-based stories)
    - WordPress
    - Archive of Our Own (OTW/AO3 software)
    - MediaWiki
    - Dreamwidth
    - LiveJournal
    - Custom platforms (Wattpad, FanFiction.Net, etc.)
    """

    # Platform signatures in priority order
    PLATFORMS = [
        PlatformSignature(
            name="ao3",
            priority=100,
            html_signatures=[
                'meta[name="generator"][content*="ArchiveOfOurOwn"]',
                'body#inner',
                'div#workskin',
                'a[href*="archiveofourown.org"]',
            ],
            meta_tags=[
                ("generator", "ArchiveOfOurOwn"),
                ("twitter:site", "@ao3org"),
            ],
            url_patterns=[
                r'/works/\d+',
                r'/series/\d+',
            ],
            script_patterns=[
                r'archiveofourown\.org/.*\.js',
            ]
        ),

        PlatformSignature(
            name="efiction",
            priority=90,
            html_signatures=[
                'meta[name="generator"][content*="eFiction"]',
                'link[href*="efiction"]',
                'a[href*="viewstory.php"]',
                'a[href*="viewuser.php"]',
                'div.pagetitle',
                'select[name="chapter"]',
            ],
            meta_tags=[
                ("generator", "eFiction"),
            ],
            url_patterns=[
                r'viewstory\.php\?sid=\d+',
                r'viewuser\.php\?uid=\d+',
            ],
            script_patterns=[
                r'efiction.*\.js',
            ]
        ),

        PlatformSignature(
            name="xenforo",
            priority=85,
            html_signatures=[
                'html[data-template*="xenforo"]',
                'html[id*="XenForo"]',
                'div.p-body',
                'div.threadmarks',
                'a.threadmarks-control',
            ],
            meta_tags=[
                ("generator", "XenForo"),
            ],
            url_patterns=[
                r'/threads/.*\.\d+/',
                r'/forums/.*\.\d+/',
            ],
            script_patterns=[
                r'xenforo.*\.js',
                r'js/xenforo/',
            ]
        ),

        PlatformSignature(
            name="wordpress",
            priority=80,
            html_signatures=[
                'meta[name="generator"][content*="WordPress"]',
                'link[href*="wp-content"]',
                'link[href*="wp-includes"]',
                'body[class*="wordpress"]',
            ],
            meta_tags=[
                ("generator", r"WordPress.*"),
            ],
            url_patterns=[
                r'/wp-content/',
                r'/wp-admin/',
            ],
            script_patterns=[
                r'wp-content/.*\.js',
                r'wp-includes/.*\.js',
            ]
        ),

        PlatformSignature(
            name="mediawiki",
            priority=75,
            html_signatures=[
                'meta[name="generator"][content*="MediaWiki"]',
                'body.mediawiki',
                'div#mw-page-base',
            ],
            meta_tags=[
                ("generator", "MediaWiki"),
            ],
            url_patterns=[
                r'/wiki/',
                r'index\.php\?title=',
            ],
            script_patterns=[
                r'mediawiki.*\.js',
            ]
        ),

        PlatformSignature(
            name="vbulletin",
            priority=70,
            html_signatures=[
                'meta[name="generator"][content*="vBulletin"]',
                'body[class*="vbulletin"]',
            ],
            meta_tags=[
                ("generator", r"vBulletin.*"),
            ],
            url_patterns=[
                r'/showthread\.php',
                r'/forumdisplay\.php',
            ],
            script_patterns=[
                r'vbulletin.*\.js',
            ]
        ),

        PlatformSignature(
            name="dreamwidth",
            priority=65,
            html_signatures=[
                'a[href*="dreamwidth.org"]',
                'link[href*="dreamwidth"]',
            ],
            meta_tags=[],
            url_patterns=[
                r'\.dreamwidth\.org',
            ],
            script_patterns=[]
        ),

        PlatformSignature(
            name="livejournal",
            priority=60,
            html_signatures=[
                'a[href*="livejournal.com"]',
                'link[href*="livejournal"]',
            ],
            meta_tags=[],
            url_patterns=[
                r'\.livejournal\.com',
            ],
            script_patterns=[]
        ),

        # Known custom platforms (not generic)
        PlatformSignature(
            name="wattpad",
            priority=95,
            html_signatures=[
                'meta[property="og:site_name"][content="Wattpad"]',
            ],
            meta_tags=[
                ("og:site_name", "Wattpad"),
            ],
            url_patterns=[
                r'wattpad\.com/story/\d+',
            ],
            script_patterns=[]
        ),

        PlatformSignature(
            name="fanfictionnet",
            priority=95,
            html_signatures=[
                'link[href*="fanfiction.net"]',
                'div#profile_top',
            ],
            meta_tags=[],
            url_patterns=[
                r'fanfiction\.net/s/\d+',
                r'fictionpress\.com/s/\d+',
            ],
            script_patterns=[]
        ),
    ]

    def __init__(self):
        # Sort platforms by priority
        self.platforms = sorted(
            self.PLATFORMS,
            key=lambda p: p.priority,
            reverse=True
        )

    def detect(self, html: str, url: str = "") -> Optional[str]:
        """
        Detect platform from HTML and URL.

        Args:
            html: HTML content of the page
            url: URL of the page (optional, helps with detection)

        Returns:
            Platform name (e.g., 'efiction', 'xenforo') or None
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        for platform in self.platforms:
            score = 0
            max_score = 0

            # Check HTML signatures (CSS selectors)
            for signature in platform.html_signatures:
                max_score += 1
                try:
                    if soup.select_one(signature):
                        score += 1
                except:
                    pass

            # Check meta tags
            for meta_name, pattern in platform.meta_tags:
                max_score += 2  # Meta tags are more reliable
                meta = soup.find('meta', attrs={'name': meta_name})
                if not meta:
                    meta = soup.find('meta', attrs={'property': meta_name})

                if meta and meta.get('content'):
                    if re.search(pattern, meta['content'], re.IGNORECASE):
                        score += 2

            # Check URL patterns
            for pattern in platform.url_patterns:
                max_score += 1
                if url and re.search(pattern, url, re.IGNORECASE):
                    score += 1

            # Check script patterns
            scripts = soup.find_all('script', src=True)
            for pattern in platform.script_patterns:
                max_score += 1
                for script in scripts:
                    if re.search(pattern, script['src'], re.IGNORECASE):
                        score += 1
                        break

            # If we got >50% match, consider it detected
            if max_score > 0 and score / max_score > 0.5:
                logger.info(
                    f"Detected platform '{platform.name}' "
                    f"(score: {score}/{max_score}, {score/max_score*100:.1f}%)"
                )
                return platform.name

        logger.warning(f"Could not detect platform for URL: {url[:100]}")
        return None

    def detect_from_url(self, url: str) -> Optional[str]:
        """Quick detection from URL alone (no HTTP request needed)"""
        for platform in self.platforms:
            for pattern in platform.url_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    logger.info(f"Detected platform '{platform.name}' from URL pattern")
                    return platform.name
        return None

    def get_platform_info(self, platform_name: str) -> Optional[PlatformSignature]:
        """Get detailed info about a platform"""
        for platform in self.platforms:
            if platform.name == platform_name:
                return platform
        return None
