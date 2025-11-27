"""
Performance Integration Layer

Combines all performance improvements for easy integration with existing FanFicFare code.
"""
from typing import List, Optional, Callable
import logging

from .connection_pool import get_global_pool, ConnectionPool
from .parallel_downloader import ParallelDownloader, DownloadTask
from .cache import get_global_cache, ResponseCache
from .lazy_loader import get_global_loader, LazyAdapterLoader

logger = logging.getLogger(__name__)


class PerformanceConfig:
    """Configuration for performance optimizations"""

    def __init__(
        self,
        # Connection pool
        enable_connection_pool: bool = True,
        pool_connections: int = 10,
        pool_maxsize: int = 20,

        # Parallel downloads
        enable_parallel_downloads: bool = True,
        max_parallel_workers: int = 10,
        parallel_rate_limit: Optional[float] = 2.0,

        # Caching
        enable_cache: bool = True,
        cache_ttl: int = 3600,
        cache_max_memory: int = 500,

        # Lazy loading
        enable_lazy_loading: bool = True,
    ):
        self.enable_connection_pool = enable_connection_pool
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize

        self.enable_parallel_downloads = enable_parallel_downloads
        self.max_parallel_workers = max_parallel_workers
        self.parallel_rate_limit = parallel_rate_limit

        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.cache_max_memory = cache_max_memory

        self.enable_lazy_loading = enable_lazy_loading


class PerformanceEnhancedFetcher:
    """
    Drop-in replacement for existing FanFicFare fetching logic
    with all performance optimizations enabled.

    Usage:
        fetcher = PerformanceEnhancedFetcher()
        story_html = fetcher.fetch("https://example.com/story/123")
        chapter_contents = fetcher.fetch_chapters(chapter_urls)
    """

    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()

        # Initialize components
        self.pool: Optional[ConnectionPool] = None
        self.cache: Optional[ResponseCache] = None
        self.downloader: Optional[ParallelDownloader] = None
        self.loader: Optional[LazyAdapterLoader] = None

        if self.config.enable_connection_pool:
            self.pool = get_global_pool()
            logger.info("Connection pool enabled")

        if self.config.enable_cache:
            self.cache = get_global_cache()
            logger.info("Cache enabled")

        if self.config.enable_parallel_downloads:
            self.downloader = ParallelDownloader(
                max_workers=self.config.max_parallel_workers,
                rate_limit=self.config.parallel_rate_limit,
            )
            logger.info(f"Parallel downloads enabled: {self.config.max_parallel_workers} workers")

        if self.config.enable_lazy_loading:
            self.loader = get_global_loader()
            logger.info("Lazy adapter loading enabled")

    def fetch(self, url: str, use_cache: bool = True) -> str:
        """
        Fetch a URL with all optimizations.

        Args:
            url: URL to fetch
            use_cache: Whether to use cache

        Returns:
            Response content
        """
        # Try cache first
        if use_cache and self.cache:
            cached = self.cache.get(url)
            if cached:
                logger.debug(f"Cache hit: {url}")
                return cached

        # Fetch using connection pool
        if self.pool:
            response = self.pool.get(url)
            content = response.text
        else:
            # Fallback to regular requests
            import requests
            content = requests.get(url).text

        # Cache the result
        if use_cache and self.cache:
            self.cache.set(url, content)

        return content

    def fetch_chapters(
        self,
        chapter_urls: List[str],
        fetch_func: Optional[Callable[[str], str]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[str]:
        """
        Fetch multiple chapters (parallel if enabled).

        Args:
            chapter_urls: List of chapter URLs
            fetch_func: Optional custom fetch function
            progress_callback: Optional progress callback

        Returns:
            List of chapter contents
        """
        # Default fetch function
        if fetch_func is None:
            fetch_func = lambda url: self.fetch(url)

        # Use parallel downloader if enabled
        if self.downloader:
            tasks = [
                DownloadTask(chapter_number=i, chapter_url=url)
                for i, url in enumerate(chapter_urls, 1)
            ]

            results = self.downloader.download_with_retry(
                tasks, fetch_func, progress_callback=progress_callback
            )

            return [r.content or "" for r in results]

        # Sequential fallback
        contents = []
        for i, url in enumerate(chapter_urls, 1):
            content = fetch_func(url)
            contents.append(content)

            if progress_callback:
                progress_callback(i, len(chapter_urls))

        return contents

    def get_adapter(self, url: str):
        """Get adapter for URL (using lazy loading if enabled)"""
        if self.loader:
            return self.loader.get_adapter(url)

        # Fallback to regular adapter loading
        # (would need to import from fanficfare)
        raise NotImplementedError("Lazy loading not enabled")

    def stats(self) -> dict:
        """Get performance statistics"""
        stats = {
            'connection_pool': self.config.enable_connection_pool,
            'caching': self.config.enable_cache,
            'parallel_downloads': self.config.enable_parallel_downloads,
            'lazy_loading': self.config.enable_lazy_loading,
        }

        if self.cache:
            stats['cache_stats'] = self.cache.stats()

        if self.loader:
            stats['loader_stats'] = self.loader.stats()

        return stats


# Convenience function for easy integration
def create_enhanced_fetcher(
    max_parallel: int = 10,
    enable_cache: bool = True,
) -> PerformanceEnhancedFetcher:
    """
    Create performance-enhanced fetcher with sensible defaults.

    Args:
        max_parallel: Maximum parallel chapter downloads
        enable_cache: Whether to enable caching

    Returns:
        PerformanceEnhancedFetcher instance
    """
    config = PerformanceConfig(
        max_parallel_workers=max_parallel,
        enable_cache=enable_cache,
    )

    return PerformanceEnhancedFetcher(config)
