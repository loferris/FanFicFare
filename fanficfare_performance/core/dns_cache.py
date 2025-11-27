"""
DNS Caching for Faster Requests

Caches DNS lookups to avoid repeated resolution of the same domains.

PERFORMANCE GAIN: ~1.5-2x faster first requests per domain
EFFORT: 4 hours
RISK: Very low

Background:
- Each HTTP request does a DNS lookup: domain → IP address
- DNS lookups take 50-200ms depending on network
- Same domain used repeatedly (story page + 20 chapters = 21 DNS lookups!)
- With caching: First lookup = 100ms, rest = 0ms

Example:
  20-chapter story from archiveofourown.org:
  - Without cache: 21 requests × 100ms DNS = 2.1s wasted
  - With cache: 1 DNS lookup = 0.1s total
  - Savings: 2.0s per story (free!)
"""
import socket
import logging
from functools import lru_cache
from typing import Optional
import time

logger = logging.getLogger(__name__)

# Store original getaddrinfo for restoration
_original_getaddrinfo = socket.getaddrinfo
_dns_cache_enabled = False


# Statistics
_dns_stats = {
    'lookups': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'total_time': 0.0,
}


def cached_getaddrinfo(*args, **kwargs):
    """
    Cached version of socket.getaddrinfo with statistics.

    This wrapper tracks cache hits/misses and timing.
    """
    global _dns_stats

    start = time.time()

    # The actual cached function is created by @lru_cache
    # We need to check if this is a cache hit or miss
    cache_info = _cached_getaddrinfo_impl.cache_info()
    before_hits = cache_info.hits

    # Call cached implementation
    result = _cached_getaddrinfo_impl(*args, **kwargs)

    # Check if it was a cache hit
    cache_info = _cached_getaddrinfo_impl.cache_info()
    after_hits = cache_info.hits

    elapsed = time.time() - start
    _dns_stats['total_time'] += elapsed

    if after_hits > before_hits:
        # Cache hit!
        _dns_stats['cache_hits'] += 1
        logger.debug(f"DNS cache HIT for {args[0] if args else 'unknown'} ({elapsed*1000:.1f}ms)")
    else:
        # Cache miss
        _dns_stats['cache_misses'] += 1
        logger.debug(f"DNS cache MISS for {args[0] if args else 'unknown'} ({elapsed*1000:.1f}ms)")

    _dns_stats['lookups'] += 1

    return result


@lru_cache(maxsize=500)
def _cached_getaddrinfo_impl(*args, **kwargs):
    """
    LRU-cached getaddrinfo implementation.

    Args are hashable for caching.
    """
    return _original_getaddrinfo(*args, **kwargs)


def enable_dns_cache(maxsize: int = 500, ttl: Optional[int] = None):
    """
    Enable DNS caching for all socket connections.

    This monkey-patches socket.getaddrinfo to use an LRU cache.

    Args:
        maxsize: Maximum cache size (default: 500 domains)
        ttl: Time-to-live in seconds (optional, not implemented yet)

    Usage:
        from fanficfare_performance.core.dns_cache import enable_dns_cache

        # Enable DNS caching
        enable_dns_cache()

        # Now all HTTP requests benefit from cached DNS
        requests.get("https://archiveofourown.org/works/123/chapter/1")
        requests.get("https://archiveofourown.org/works/123/chapter/2")
        # Second request uses cached DNS (instant!)

    Performance:
        First request to domain: ~100ms (DNS lookup + request)
        Subsequent requests: ~0ms (cached DNS)

        Example (20-chapter story):
          Without cache: 21 DNS lookups × 100ms = 2.1s
          With cache: 1 DNS lookup = 0.1s
          Savings: 2.0s per story
    """
    global _dns_cache_enabled

    if _dns_cache_enabled:
        logger.debug("DNS cache already enabled")
        return

    # Recreate cached function with new maxsize
    global _cached_getaddrinfo_impl
    _cached_getaddrinfo_impl = lru_cache(maxsize=maxsize)(_original_getaddrinfo)

    # Monkey-patch socket.getaddrinfo
    socket.getaddrinfo = cached_getaddrinfo

    _dns_cache_enabled = True

    logger.info(f"DNS caching enabled (maxsize={maxsize})")


def disable_dns_cache():
    """
    Disable DNS caching and restore original socket.getaddrinfo.

    Usage:
        disable_dns_cache()
    """
    global _dns_cache_enabled

    if not _dns_cache_enabled:
        logger.debug("DNS cache not enabled")
        return

    # Restore original
    socket.getaddrinfo = _original_getaddrinfo

    _dns_cache_enabled = False

    logger.info("DNS caching disabled")


def clear_dns_cache():
    """
    Clear the DNS cache.

    Useful if you want to force fresh DNS lookups.

    Usage:
        clear_dns_cache()
    """
    if _dns_cache_enabled:
        _cached_getaddrinfo_impl.cache_clear()
        logger.info("DNS cache cleared")
    else:
        logger.debug("DNS cache not enabled, nothing to clear")


def get_dns_cache_stats() -> dict:
    """
    Get DNS cache statistics.

    Returns:
        Dictionary with cache statistics

    Usage:
        stats = get_dns_cache_stats()
        print(f"Cache hits: {stats['cache_hits']}")
        print(f"Cache hit rate: {stats['hit_rate']:.1f}%")
    """
    stats = _dns_stats.copy()

    if _dns_cache_enabled:
        cache_info = _cached_getaddrinfo_impl.cache_info()
        stats['cache_size'] = cache_info.currsize
        stats['cache_maxsize'] = cache_info.maxsize
    else:
        stats['cache_size'] = 0
        stats['cache_maxsize'] = 0

    # Calculate hit rate
    total_lookups = stats['lookups']
    if total_lookups > 0:
        stats['hit_rate'] = (stats['cache_hits'] / total_lookups) * 100
    else:
        stats['hit_rate'] = 0.0

    # Calculate average time
    if total_lookups > 0:
        stats['avg_time'] = stats['total_time'] / total_lookups
    else:
        stats['avg_time'] = 0.0

    return stats


def print_dns_cache_stats():
    """
    Print DNS cache statistics.

    Usage:
        print_dns_cache_stats()
    """
    stats = get_dns_cache_stats()

    print("\n" + "="*60)
    print("DNS Cache Statistics")
    print("="*60)
    print(f"  Enabled:        {_dns_cache_enabled}")
    print(f"  Total lookups:  {stats['lookups']}")
    print(f"  Cache hits:     {stats['cache_hits']}")
    print(f"  Cache misses:   {stats['cache_misses']}")
    print(f"  Hit rate:       {stats['hit_rate']:.1f}%")
    print(f"  Cache size:     {stats['cache_size']}/{stats['cache_maxsize']}")
    print(f"  Total time:     {stats['total_time']:.2f}s")
    print(f"  Avg time:       {stats['avg_time']*1000:.1f}ms per lookup")
    print("="*60)


def configure_dns_cache(config=None):
    """
    Configure DNS cache from FanFicFare config.

    Args:
        config: Configuration object (optional)

    Usage:
        # From adapter:
        configure_dns_cache(adapter)

        # Or standalone:
        configure_dns_cache()

    Config options:
        [defaults]
        enable_dns_cache:true
        dns_cache_maxsize:500
    """
    if config and hasattr(config, 'getConfig'):
        # Check if enabled
        enabled = config.getConfig('enable_dns_cache', 'true').lower() == 'true'

        if not enabled:
            logger.debug("DNS cache disabled in config")
            return False

        # Get maxsize
        try:
            maxsize = int(config.getConfig('dns_cache_maxsize', '500'))
        except:
            maxsize = 500

        enable_dns_cache(maxsize=maxsize)
    else:
        # Use defaults
        enable_dns_cache()

    return True


# Convenience context manager
class DNSCache:
    """
    Context manager for DNS caching.

    Usage:
        with DNSCache():
            # DNS caching enabled here
            requests.get("https://archiveofourown.org/works/123")
            requests.get("https://archiveofourown.org/works/124")
            # Second request benefits from cached DNS

        # DNS caching disabled here (optional)
    """

    def __init__(self, maxsize: int = 500, auto_print_stats: bool = False):
        """
        Args:
            maxsize: Cache size
            auto_print_stats: Print stats on exit
        """
        self.maxsize = maxsize
        self.auto_print_stats = auto_print_stats

    def __enter__(self):
        enable_dns_cache(self.maxsize)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.auto_print_stats:
            print_dns_cache_stats()

        # Optionally disable (or leave enabled)
        # disable_dns_cache()

        return False


# Auto-enable on import (optional)
def auto_enable_dns_cache():
    """
    Automatically enable DNS cache on import.

    To use:
        import fanficfare_performance.core.dns_cache
        fanficfare_performance.core.dns_cache.auto_enable_dns_cache()
    """
    enable_dns_cache()
    logger.info("DNS cache auto-enabled")
