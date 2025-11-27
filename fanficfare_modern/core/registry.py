"""
Smart Adapter Registry

Intelligent adapter selection with automatic fallback:
1. Custom adapters (for unique/complex sites)
2. Platform-based adapters (auto-detected)
3. Config-driven adapters (YAML configs)
4. Heuristic fallback (last resort)
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, Type, Any
from pathlib import Path
from urllib.parse import urlparse

from .platform_detector import PlatformDetector
from ..platform_adapters.efiction import EFictionAdapter
from ..platform_adapters.xenforo import XenForoAdapter
from ..config_adapters.config_driven import ConfigDrivenAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Smart registry that finds the right adapter for any URL.

    Adapter selection priority:
    1. Exact domain match (custom adapters)
    2. Platform detection (generic platform adapters)
    3. Config-driven (YAML configs)
    4. Heuristic fallback

    This dramatically reduces maintenance:
    - 117 adapters → ~15 custom + 10 platform + ~30 configs
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: Directory containing YAML configs (optional)
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "site_configs"
        self.detector = PlatformDetector()

        # Custom adapters for unique sites (registered manually)
        self.custom_adapters: Dict[str, Any] = {}

        # Platform adapter classes
        self.platform_adapters = {
            'efiction': EFictionAdapter,
            'xenforo': XenForoAdapter,
            # More platforms can be added here
        }

        # Cache for performance
        self._domain_cache: Dict[str, Any] = {}

    def register_custom_adapter(self, domain: str, adapter_class: Type):
        """
        Register a custom adapter for a specific domain.

        Use this for sites with unique structure that can't use generic adapters.

        Example:
            registry.register_custom_adapter('wattpad.com', WattpadAdapter)
        """
        self.custom_adapters[domain] = adapter_class
        logger.info(f"Registered custom adapter for {domain}")

    def get_adapter(self, url: str, html: Optional[str] = None) -> Optional[Any]:
        """
        Get the best adapter for a URL.

        Args:
            url: Story URL
            html: Optional HTML content (improves detection)

        Returns:
            Adapter instance or None

        Selection process:
        1. Check custom adapters by domain
        2. Detect platform from HTML/URL
        3. Try config-driven adapter
        4. Return None (caller can fall back to heuristic)
        """
        domain = urlparse(url).netloc

        # Check cache first
        if domain in self._domain_cache and not html:
            logger.debug(f"Using cached adapter for {domain}")
            adapter_info = self._domain_cache[domain]
            return self._create_adapter(adapter_info, url)

        # Tier 1: Custom adapters (exact domain match)
        if domain in self.custom_adapters:
            logger.info(f"Using custom adapter for {domain}")
            adapter_class = self.custom_adapters[domain]
            adapter = adapter_class(domain)
            self._domain_cache[domain] = ('custom', adapter_class)
            return adapter

        # Tier 2: Platform detection
        if html:
            platform = self.detector.detect(html, url)
        else:
            # Try quick URL-based detection
            platform = self.detector.detect_from_url(url)

        if platform and platform in self.platform_adapters:
            logger.info(f"Using {platform} platform adapter for {domain}")
            adapter_class = self.platform_adapters[platform]
            adapter = adapter_class(domain)
            self._domain_cache[domain] = ('platform', platform)
            return adapter

        # Tier 3: Config-driven adapter
        if self.config_dir.exists():
            config_adapter = ConfigDrivenAdapter.from_domain(domain, self.config_dir)
            if config_adapter:
                logger.info(f"Using config-driven adapter for {domain}")
                self._domain_cache[domain] = ('config', domain)
                return config_adapter

        # Tier 4: No adapter found
        logger.warning(f"No adapter found for {domain}")
        return None

    def _create_adapter(self, adapter_info: tuple, url: str) -> Any:
        """Recreate adapter from cached info"""
        adapter_type, data = adapter_info

        domain = urlparse(url).netloc

        if adapter_type == 'custom':
            adapter_class = data
            return adapter_class(domain)
        elif adapter_type == 'platform':
            platform = data
            adapter_class = self.platform_adapters[platform]
            return adapter_class(domain)
        elif adapter_type == 'config':
            return ConfigDrivenAdapter.from_domain(domain, self.config_dir)

        return None

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about registered adapters"""
        # Count config files
        config_count = 0
        if self.config_dir.exists():
            config_count = len(list(self.config_dir.glob('*.yaml')))

        return {
            'custom_adapters': len(self.custom_adapters),
            'platform_adapters': len(self.platform_adapters),
            'config_adapters': config_count,
            'cached_domains': len(self._domain_cache),
        }

    def clear_cache(self):
        """Clear domain cache (useful if configs change)"""
        self._domain_cache.clear()
        logger.info("Adapter cache cleared")


class UnifiedAdapter:
    """
    High-level adapter that uses the registry and provides a simple interface.

    Usage:
        adapter = UnifiedAdapter(registry)
        story = await adapter.get_story("https://example.com/story/123")
    """

    def __init__(self, registry: Optional[AdapterRegistry] = None):
        self.registry = registry or AdapterRegistry()

    def get_story(self, url: str, html: Optional[str] = None) -> Any:
        """
        Get story metadata from URL.

        Args:
            url: Story URL
            html: Optional pre-fetched HTML (saves a request)

        Returns:
            Story object with metadata and chapter list
        """
        # Find appropriate adapter
        adapter = self.registry.get_adapter(url, html)

        if not adapter:
            raise ValueError(f"No adapter found for URL: {url}")

        # If we don't have HTML, fetch it
        if not html:
            html = self._fetch_url(url)

        # Extract metadata
        story = adapter.extract_metadata(html, url)

        return story

    def get_chapter(self, chapter_url: str) -> str:
        """
        Get chapter content.

        Args:
            chapter_url: Chapter URL

        Returns:
            HTML content of chapter
        """
        # Find appropriate adapter
        html = self._fetch_url(chapter_url)
        adapter = self.registry.get_adapter(chapter_url, html)

        if not adapter:
            raise ValueError(f"No adapter found for URL: {chapter_url}")

        # Extract content
        content = adapter.extract_chapter_content(html)

        return content

    def _fetch_url(self, url: str) -> str:
        """
        Fetch URL content.

        In production, this would use httpx or requests.
        For now, it's a placeholder.
        """
        # Placeholder - in real implementation, use httpx
        import urllib.request

        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise
