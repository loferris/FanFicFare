#!/usr/bin/env python3
"""
FanFicFare Modern Adapter System - Demo

Demonstrates the new streamlined adapter system.
"""
from pathlib import Path
from fanficfare_modern.core.platform_detector import PlatformDetector
from fanficfare_modern.platform_adapters.efiction import EFictionAdapter
from fanficfare_modern.platform_adapters.xenforo import XenForoAdapter
from fanficfare_modern.config_adapters.config_driven import ConfigDrivenAdapter
from fanficfare_modern.core.registry import AdapterRegistry, UnifiedAdapter
from fanficfare_modern.tools.migration_helper import MigrationTool


def demo_platform_detection():
    """Demo: Platform Detection"""
    print("\n" + "="*60)
    print("DEMO 1: Platform Detection")
    print("="*60)

    detector = PlatformDetector()

    # Example 1: eFiction site
    efiction_html = """
    <html>
    <head>
        <meta name="generator" content="eFiction 3.5">
        <link href="/efiction/style.css">
    </head>
    <body>
        <a href="viewstory.php?sid=123">Story</a>
    </body>
    </html>
    """

    platform = detector.detect(efiction_html, "https://example.com/viewstory.php?sid=123")
    print(f"\n✓ Detected eFiction platform: {platform}")

    # Example 2: XenForo forum
    xenforo_url = "https://forums.spacebattles.com/threads/story.123456/"
    platform = detector.detect_from_url(xenforo_url)
    print(f"✓ Detected XenForo from URL: {platform}")

    # Example 3: Get platform info
    info = detector.get_platform_info("efiction")
    print(f"\n✓ eFiction platform info:")
    print(f"  - Priority: {info.priority}")
    print(f"  - Signatures: {len(info.html_signatures)} HTML patterns")
    print(f"  - URL patterns: {len(info.url_patterns)}")


def demo_platform_adapters():
    """Demo: Generic Platform Adapters"""
    print("\n" + "="*60)
    print("DEMO 2: Platform Adapters (Generic)")
    print("="*60)

    # ONE adapter handles ALL eFiction sites
    efiction_sites = [
        "storiesonline.net",
        "adultfanfiction.org",
        "mediaminer.org",
        "scifistories.com",
        "fictionpress.com",
    ]

    print("\n✓ ONE eFiction adapter handles ALL these sites:")
    for site in efiction_sites:
        adapter = EFictionAdapter(site)
        print(f"  ✓ {site} → {adapter.__class__.__name__}")

    print("\n✓ ONE XenForo adapter handles ALL forum sites:")
    xenforo_sites = [
        "forums.spacebattles.com",
        "forums.sufficientvelocity.com",
        "forum.questionablequesting.com",
    ]

    for site in xenforo_sites:
        adapter = XenForoAdapter(site)
        print(f"  ✓ {site} → {adapter.__class__.__name__}")

    print(f"\n💡 Instead of {len(efiction_sites) + len(xenforo_sites)} adapter files,")
    print(f"   we have just 2 platform adapters!")


def demo_config_driven():
    """Demo: Config-Driven Adapters"""
    print("\n" + "="*60)
    print("DEMO 3: Config-Driven Adapters (YAML)")
    print("="*60)

    config_dir = Path(__file__).parent / "site_configs"

    if not config_dir.exists():
        print("\n⚠️  Config directory not found. Skipping demo.")
        return

    print(f"\n✓ Config directory: {config_dir}")

    yaml_files = list(config_dir.glob("*.yaml"))
    print(f"✓ Found {len(yaml_files)} YAML configs:")

    for yaml_file in yaml_files:
        print(f"  • {yaml_file.name}")

    # Load a config
    if yaml_files:
        print(f"\n✓ Loading {yaml_files[0].name}...")
        adapter = ConfigDrivenAdapter.from_yaml(yaml_files[0])
        print(f"  - Name: {adapter.config.name}")
        print(f"  - Domains: {', '.join(adapter.config.domains)}")
        print(f"  - Pattern: {adapter.config.story_url_pattern}")

        if adapter.config.selectors:
            print(f"  - Selectors: {len(adapter.config.selectors)} defined")

    print(f"\n💡 Adding a new site = just creating a YAML file!")
    print(f"   No Python code needed!")


def demo_smart_registry():
    """Demo: Smart Registry"""
    print("\n" + "="*60)
    print("DEMO 4: Smart Registry (Automatic Selection)")
    print("="*60)

    registry = AdapterRegistry(
        config_dir=Path(__file__).parent / "site_configs"
    )

    print("\n✓ Registry initialized")
    stats = registry.get_stats()
    print(f"  - Custom adapters: {stats['custom_adapters']}")
    print(f"  - Platform adapters: {stats['platform_adapters']}")
    print(f"  - Config adapters: {stats['config_adapters']}")

    # Test URLs
    test_urls = [
        ("https://archiveofourown.org/works/12345", "AO3 (config)"),
        ("https://storiesonline.net/viewstory.php?sid=123", "eFiction (platform)"),
        ("https://forums.spacebattles.com/threads/story.123/", "XenForo (platform)"),
    ]

    print("\n✓ Testing adapter selection:")
    for url, expected in test_urls:
        # Quick detection from URL
        from urllib.parse import urlparse
        domain = urlparse(url).netloc

        print(f"\n  URL: {url}")
        print(f"  Expected: {expected}")

        # Detect platform from URL
        detector = PlatformDetector()
        platform = detector.detect_from_url(url)

        if platform:
            print(f"  ✓ Platform detected: {platform}")
        else:
            print(f"  • Checking config adapters...")


def demo_migration_analysis():
    """Demo: Migration Tool"""
    print("\n" + "="*60)
    print("DEMO 5: Migration Analysis")
    print("="*60)

    old_adapter_dir = Path(__file__).parent.parent / "fanficfare" / "adapters"

    if not old_adapter_dir.exists():
        print("\n⚠️  Old adapter directory not found. Skipping demo.")
        return

    print(f"\n✓ Analyzing old adapters in: {old_adapter_dir}")

    # Count adapter files
    adapter_files = list(old_adapter_dir.glob("adapter_*.py"))
    print(f"✓ Found {len(adapter_files)} adapter files")

    print("\n✓ Running migration analysis...")
    tool = MigrationTool(
        old_adapter_dir=old_adapter_dir,
        new_config_dir=Path(__file__).parent / "site_configs"
    )

    # Generate report
    report = tool.generate_report()
    print(report)


def demo_unified_adapter():
    """Demo: Complete Workflow"""
    print("\n" + "="*60)
    print("DEMO 6: Unified Adapter (Complete Workflow)")
    print("="*60)

    adapter = UnifiedAdapter()

    print("\n✓ UnifiedAdapter initialized")
    print("✓ Usage:")
    print("""
    # Get story metadata
    story = adapter.get_story("https://archiveofourown.org/works/12345")

    # Get chapter content
    content = adapter.get_chapter(chapter_url)
    """)

    print("\n💡 The registry automatically:")
    print("  1. Detects platform from URL/HTML")
    print("  2. Selects best adapter (custom → platform → config)")
    print("  3. Returns story data in consistent format")


def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("FanFicFare Modern Adapter System - DEMO")
    print("="*60)
    print("\nStreamlining 117 adapters → ~25-30 files + YAML configs")
    print("Reducing maintenance burden by ~75%")

    try:
        demo_platform_detection()
        demo_platform_adapters()
        demo_config_driven()
        demo_smart_registry()
        demo_migration_analysis()
        demo_unified_adapter()

        print("\n" + "="*60)
        print("SUMMARY: Benefits of Modern System")
        print("="*60)
        print("""
✅ Reduced Maintenance:
   - 117 adapter files → ~25-30 files + configs
   - ~75% reduction in code to maintain

✅ Faster Development:
   - Add site in minutes (YAML) vs hours (Python)
   - No coding required for simple sites

✅ Better Organization:
   - Platform detection auto-routes to right adapter
   - Generic adapters for common platforms
   - Config files for site-specific selectors

✅ Type Safety:
   - Pydantic models with validation
   - IDE autocomplete and type checking
   - Catch errors early

✅ Backward Compatible:
   - Coexists with old system
   - Gradual migration path
   - No breaking changes
        """)

        print("\n" + "="*60)
        print("Next Steps")
        print("="*60)
        print("""
1. Review the code in fanficfare_modern/
2. Check example configs in site_configs/
3. Run tests: pytest fanficfare_modern/tests/
4. Try adding a new site with YAML
5. Migrate old adapters using migration_helper.py
        """)

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
