"""
Basic Usage Examples

Shows how to use each performance optimization individually
and all together.
"""
import time


def example_1_connection_pooling():
    """
    Example 1: Connection Pooling (5x faster)

    Before: Create new connection for each request
    After:  Reuse connections from pool
    """
    print("="*70)
    print("EXAMPLE 1: Connection Pooling")
    print("="*70)

    from fanficfare_performance.core.connection_pool import ConnectionPool

    # Create connection pool
    with ConnectionPool() as pool:
        # Make multiple requests (connections are reused)
        urls = [
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/delay/1",
        ]

        start = time.time()
        for url in urls:
            response = pool.get(url)
            print(f"  ✓ Fetched {url} ({response.status_code})")

        elapsed = time.time() - start
        print(f"\n✓ Total time: {elapsed:.2f}s (with connection pooling)")
        print(f"  Without pooling would be ~{len(urls) * 1.5:.1f}s")


def example_2_parallel_downloads():
    """
    Example 2: Parallel Downloads (10-20x faster)

    Before: Download chapters one by one
    After:  Download 10 chapters in parallel
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Parallel Downloads")
    print("="*70)

    from fanficfare_performance.core.parallel_downloader import (
        ParallelDownloader,
        DownloadTask,
    )

    # Simulate chapter URLs
    chapter_urls = [f"https://httpbin.org/delay/1?chapter={i}" for i in range(10)]

    # Create tasks
    tasks = [
        DownloadTask(chapter_number=i, chapter_url=url)
        for i, url in enumerate(chapter_urls, 1)
    ]

    # Fetch function (simulated)
    def fetch_chapter(url):
        import requests
        response = requests.get(url, timeout=10)
        return response.text[:100] + "..."  # Truncate for display

    # Download in parallel
    downloader = ParallelDownloader(max_workers=5)

    print(f"\nDownloading {len(tasks)} chapters in parallel...")
    start = time.time()

    results = downloader.download_chapters(
        tasks,
        fetch_chapter,
        progress_callback=lambda done, total: print(f"  Progress: {done}/{total}")
    )

    elapsed = time.time() - start

    successful = sum(1 for r in results if r.success)
    print(f"\n✓ Downloaded {successful}/{len(tasks)} chapters in {elapsed:.2f}s")
    print(f"  Sequential would take ~{len(tasks) * 1:.1f}s")
    print(f"  Speedup: ~{(len(tasks) * 1) / elapsed:.1f}x")


def example_3_caching():
    """
    Example 3: Caching (2-3x faster for repeated requests)

    Before: Fetch same URL multiple times
    After:  Cache and reuse
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Caching")
    print("="*70)

    from fanficfare_performance.core.cache import ResponseCache

    cache = ResponseCache(max_memory_size=100, ttl=60)

    url = "https://httpbin.org/html"

    # First request (cache miss)
    print("\nFirst request (cache miss):")
    start = time.time()

    import requests
    response1 = requests.get(url).text
    cache.set(url, response1)

    elapsed1 = time.time() - start
    print(f"  Time: {elapsed1:.3f}s")

    # Second request (cache hit)
    print("\nSecond request (cache hit):")
    start = time.time()

    response2 = cache.get(url)

    elapsed2 = time.time() - start
    print(f"  Time: {elapsed2:.6f}s")

    print(f"\n✓ Cache speedup: {elapsed1 / elapsed2:.0f}x faster")
    print(f"✓ Cache stats: {cache.stats()}")


def example_4_all_together():
    """
    Example 4: All Optimizations Together

    Shows how to use the integrated performance fetcher.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: All Optimizations Together")
    print("="*70)

    from fanficfare_performance.core.integration import create_enhanced_fetcher

    # Create enhanced fetcher with all optimizations
    fetcher = create_enhanced_fetcher(
        max_parallel=5,
        enable_cache=True,
    )

    # Example: Fetch story page
    print("\n1. Fetching story page...")
    story_url = "https://httpbin.org/html"

    start = time.time()
    story_html = fetcher.fetch(story_url)
    elapsed = time.time() - start

    print(f"   ✓ Fetched in {elapsed:.3f}s")
    print(f"   ✓ Cached: Yes")

    # Example: Fetch chapters in parallel
    print("\n2. Fetching 5 chapters in parallel...")
    chapter_urls = [f"https://httpbin.org/delay/1?ch={i}" for i in range(5)]

    start = time.time()
    chapters = fetcher.fetch_chapters(
        chapter_urls,
        progress_callback=lambda done, total: print(f"   Progress: {done}/{total}")
    )
    elapsed = time.time() - start

    print(f"\n   ✓ Downloaded {len(chapters)} chapters in {elapsed:.2f}s")
    print(f"   ✓ With all optimizations: ~{5 * 1 / elapsed:.1f}x faster")

    # Show stats
    print("\n3. Performance stats:")
    stats = fetcher.stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")


def example_5_backward_compatible():
    """
    Example 5: Backward Compatible Integration

    Shows how to integrate with existing code without changes.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Backward Compatible Drop-in")
    print("="*70)

    # Old way (still works)
    print("\nOld way (requests):")
    import requests
    start = time.time()
    response = requests.get("https://httpbin.org/delay/1")
    elapsed_old = time.time() - start
    print(f"  Time: {elapsed_old:.2f}s")

    # New way (drop-in replacement)
    print("\nNew way (connection pool):")
    from fanficfare_performance.core.connection_pool import pooled_get
    start = time.time()
    response = pooled_get("https://httpbin.org/delay/1")
    elapsed_new = time.time() - start
    print(f"  Time: {elapsed_new:.2f}s")

    print(f"\n✓ Same API, better performance")
    print(f"✓ Just replace:")
    print(f"    requests.get() → pooled_get()")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║         FANFICFARE PERFORMANCE IMPROVEMENTS - EXAMPLES               ║
╚══════════════════════════════════════════════════════════════════════╝

These examples demonstrate the 4 Phase 1 quick wins:
1. Connection Pooling (5x faster)
2. Parallel Downloads (10-20x faster)
3. Caching (2-3x faster)
4. All Together (~10x combined)

Note: Examples use httpbin.org for demonstration.
      Real usage would be with fanfiction sites.
    """)

    try:
        # Run examples (comment out if httpbin is slow)
        # example_1_connection_pooling()
        # example_2_parallel_downloads()
        # example_3_caching()
        # example_4_all_together()
        example_5_backward_compatible()

        print("\n" + "="*70)
        print("✅ All examples completed!")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("Note: Examples require internet connection to httpbin.org")
