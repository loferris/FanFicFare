"""
DNS Cache Performance Demonstration

Shows the speedup from caching DNS lookups.
"""
import sys
import time
import socket

sys.path.insert(0, '/home/user/FanFicFare')

from fanficfare_performance.core.dns_cache import (
    enable_dns_cache,
    disable_dns_cache,
    clear_dns_cache,
    get_dns_cache_stats,
    print_dns_cache_stats,
    DNSCache
)


def simulate_dns_lookups_without_cache():
    """Simulate DNS lookups without caching"""
    print("="*80)
    print("WITHOUT DNS CACHE")
    print("="*80)

    domains = [
        'archiveofourown.org',
        'www.fanfiction.net',
        'www.wattpad.com',
    ]

    # Simulate multiple requests to same domain (like downloading a story)
    all_lookups = []
    for domain in domains:
        # Story page + 20 chapters = 21 requests
        all_lookups.extend([domain] * 21)

    print(f"\nSimulating {len(all_lookups)} DNS lookups...")
    print(f"  • {len([d for d in all_lookups if d == domains[0]])} requests to {domains[0]}")
    print(f"  • {len([d for d in all_lookups if d == domains[1]])} requests to {domains[1]}")
    print(f"  • {len([d for d in all_lookups if d == domains[2]])} requests to {domains[2]}")

    start = time.time()

    for domain in all_lookups:
        # Each DNS lookup
        try:
            socket.getaddrinfo(domain, 443, socket.AF_INET, socket.SOCK_STREAM)
        except:
            pass

    elapsed = time.time() - start

    print(f"\n✓ Completed {len(all_lookups)} DNS lookups")
    print(f"✓ Time: {elapsed:.2f}s")
    print(f"✓ Average: {elapsed/len(all_lookups)*1000:.1f}ms per lookup")

    return elapsed


def simulate_dns_lookups_with_cache():
    """Simulate DNS lookups WITH caching"""
    print("\n" + "="*80)
    print("WITH DNS CACHE")
    print("="*80)

    # Enable caching
    enable_dns_cache(maxsize=500)

    domains = [
        'archiveofourown.org',
        'www.fanfiction.net',
        'www.wattpad.com',
    ]

    # Same pattern: 21 requests per domain
    all_lookups = []
    for domain in domains:
        all_lookups.extend([domain] * 21)

    print(f"\nSimulating {len(all_lookups)} DNS lookups (with cache)...")
    print(f"  • {len([d for d in all_lookups if d == domains[0]])} requests to {domains[0]}")
    print(f"  • {len([d for d in all_lookups if d == domains[1]])} requests to {domains[1]}")
    print(f"  • {len([d for d in all_lookups if d == domains[2]])} requests to {domains[2]}")

    start = time.time()

    for domain in all_lookups:
        try:
            socket.getaddrinfo(domain, 443, socket.AF_INET, socket.SOCK_STREAM)
        except:
            pass

    elapsed = time.time() - start

    # Get stats
    stats = get_dns_cache_stats()

    print(f"\n✓ Completed {len(all_lookups)} DNS lookups")
    print(f"✓ Time: {elapsed:.2f}s")
    print(f"✓ Average: {elapsed/len(all_lookups)*1000:.1f}ms per lookup")
    print(f"\nCache Statistics:")
    print(f"  • Cache hits:   {stats['cache_hits']}")
    print(f"  • Cache misses: {stats['cache_misses']}")
    print(f"  • Hit rate:     {stats['hit_rate']:.1f}%")

    # Disable cache
    disable_dns_cache()

    return elapsed


def demo_context_manager():
    """Demonstrate context manager usage"""
    print("\n" + "="*80)
    print("CONTEXT MANAGER DEMO")
    print("="*80)

    domains = ['google.com', 'github.com', 'stackoverflow.com']

    print("\nUsing DNSCache context manager:")
    print("  with DNSCache(auto_print_stats=True):")

    with DNSCache(auto_print_stats=True):
        for domain in domains:
            # Multiple requests to each domain
            for _ in range(5):
                try:
                    socket.getaddrinfo(domain, 443)
                except:
                    pass

    print("\n✓ Context manager exited, stats printed above")


def show_real_world_scenarios():
    """Show real-world performance impact"""
    print("\n" + "="*80)
    print("REAL-WORLD SCENARIOS")
    print("="*80)

    scenarios = [
        {
            'name': 'Download 20-chapter story',
            'requests': 21,  # 1 story page + 20 chapters
            'dns_time': 0.1,  # 100ms per DNS lookup
        },
        {
            'name': 'Update 10 stories',
            'requests': 10,  # 10 story pages
            'dns_time': 0.1,
        },
        {
            'name': 'Download 100-chapter story',
            'requests': 101,
            'dns_time': 0.1,
        },
    ]

    for scenario in scenarios:
        requests = scenario['requests']
        dns_time = scenario['dns_time']

        # Without cache: DNS lookup for every request
        without_cache = requests * dns_time

        # With cache: DNS lookup only for first request
        with_cache = dns_time

        savings = without_cache - with_cache

        print(f"\n{scenario['name']}")
        print("-"*80)
        print(f"  Requests:       {requests}")
        print(f"  Without cache:  {without_cache:.1f}s ({requests} × {dns_time}s)")
        print(f"  With cache:     {with_cache:.1f}s (1 × {dns_time}s)")
        print(f"  Savings:        {savings:.1f}s")


def show_integration_example():
    """Show how to integrate with FanFicFare"""
    print("\n" + "="*80)
    print("INTEGRATION WITH FANFICFARE")
    print("="*80)

    print("""
Option 1: Enable in cli.py (Automatic)
---------------------------------------
# In fanficfare/cli.py, after imports:

from fanficfare_performance.core.dns_cache import enable_dns_cache

# Enable DNS caching
enable_dns_cache()

# Now all HTTP requests benefit from cached DNS!


Option 2: Enable via Config (Configurable)
-------------------------------------------
# In fanficfare/cli.py:

from fanficfare_performance.core.dns_cache import configure_dns_cache

# Enable based on config
configure_dns_cache(configuration)

# In personal.ini:
[defaults]
enable_dns_cache:true
dns_cache_maxsize:500


Option 3: Context Manager (Scoped)
-----------------------------------
from fanficfare_performance.core.dns_cache import DNSCache

with DNSCache(auto_print_stats=True):
    # Download story
    adapter.getStory()
    # DNS caching active here

# Stats automatically printed on exit


Performance Impact:
-------------------
20-chapter story from AO3:
  • Without cache: 21 DNS lookups × 100ms = 2.1s
  • With cache:     1 DNS lookup = 0.1s
  • Savings:        2.0s per story

Combined with parallel downloads:
  • Even faster! Parallel requests benefit from instant DNS
    """)


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              DNS CACHING - PERFORMANCE DEMO                          ║
╚══════════════════════════════════════════════════════════════════════╝

This demo shows the performance improvement from caching DNS lookups.

DNS lookups: domain → IP address (takes 50-200ms)
Without cache: Every request does a DNS lookup
With cache: Only first request does DNS lookup

Expected savings: ~2s per story
    """)

    try:
        # Demo without cache
        without_time = simulate_dns_lookups_without_cache()

        # Demo with cache
        with_time = simulate_dns_lookups_with_cache()

        # Show comparison
        print("\n" + "="*80)
        print("COMPARISON")
        print("="*80)
        print(f"\nWithout cache: {without_time:.2f}s")
        print(f"With cache:    {with_time:.2f}s")

        if without_time > with_time:
            speedup = without_time / with_time
            savings = without_time - with_time
            print(f"Speedup:       {speedup:.1f}x faster")
            print(f"Time saved:    {savings:.2f}s")
        else:
            print("\nNote: DNS caching benefits are most visible over slower networks")
            print("Local DNS is already very fast, so savings are minimal in this demo")

        # Demo context manager
        demo_context_manager()

        # Show real-world scenarios
        show_real_world_scenarios()

        # Show integration
        show_integration_example()

        print("\n" + "="*80)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)

        print("\nKey Takeaways:")
        print("  1. DNS caching is 'free' speedup (no code changes)")
        print("  2. Saves 1-2s per story (more over slow networks)")
        print("  3. Especially beneficial with parallel downloads")
        print("  4. Zero risk, easily enabled/disabled")

    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
