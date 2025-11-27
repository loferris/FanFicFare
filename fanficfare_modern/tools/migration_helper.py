"""
Migration Helper

Tools to help migrate from old adapter system to new config-driven system.
"""
from __future__ import annotations

import re
import ast
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml


class AdapterAnalyzer:
    """
    Analyzes old adapter code to extract patterns that can be converted to config.
    """

    def __init__(self, adapter_file: Path):
        self.adapter_file = adapter_file
        self.code = adapter_file.read_text()

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze adapter and extract information.

        Returns:
            Dict with adapter information
        """
        info = {
            'file': str(self.adapter_file),
            'domain': self._extract_domain(),
            'url_pattern': self._extract_url_pattern(),
            'selectors': self._extract_selectors(),
            'can_migrate': False,
            'platform': self._detect_platform(),
            'complexity': self._estimate_complexity(),
        }

        # Determine if this can be migrated to config
        info['can_migrate'] = self._can_migrate_to_config(info)

        return info

    def _extract_domain(self) -> Optional[str]:
        """Extract site domain from getSiteDomain() method"""
        match = re.search(r'def getSiteDomain\(.*?\):\s*return\s+["\']([^"\']+)["\']', self.code)
        return match.group(1) if match else None

    def _extract_url_pattern(self) -> Optional[str]:
        """Extract URL pattern from getSiteURLPattern() method"""
        match = re.search(r'def getSiteURLPattern\(.*?\):\s*return\s+r?["\']([^"\']+)["\']', self.code)
        return match.group(1) if match else None

    def _extract_selectors(self) -> Dict[str, str]:
        """Try to extract CSS selectors from code"""
        selectors = {}

        # Look for BeautifulSoup select/select_one calls
        soup_selects = re.findall(
            r'(?:select_one|select|css_first|css)\(["\']([^"\']+)["\']\)',
            self.code
        )

        # Try to categorize selectors
        for selector in soup_selects:
            if 'title' in selector.lower():
                selectors['title'] = selector
            elif 'author' in selector.lower():
                selectors['author'] = selector
            elif 'summary' in selector.lower():
                selectors['summary'] = selector
            elif 'chapter' in selector.lower():
                selectors['chapters'] = selector

        return selectors

    def _detect_platform(self) -> Optional[str]:
        """Detect if adapter inherits from a platform base"""
        if 'BaseEfictionAdapter' in self.code:
            return 'efiction'
        elif 'BaseXenForo' in self.code:
            return 'xenforo'
        elif 'BaseOTWAdapter' in self.code:
            return 'ao3'
        elif 'WordPressAdapter' in self.code:
            return 'wordpress'

        return None

    def _estimate_complexity(self) -> str:
        """Estimate adapter complexity"""
        # Count methods
        method_count = len(re.findall(r'def \w+\(', self.code))

        # Check for complex features
        has_login = 'login' in self.code.lower()
        has_javascript = 'selenium' in self.code.lower() or 'playwright' in self.code.lower()
        has_api = 'api' in self.code.lower() and 'json' in self.code.lower()

        if has_javascript or has_api or method_count > 10:
            return 'complex'
        elif has_login or method_count > 5:
            return 'medium'
        else:
            return 'simple'

    def _can_migrate_to_config(self, info: Dict[str, Any]) -> bool:
        """Determine if adapter can be migrated to YAML config"""
        # Can migrate if:
        # 1. It's simple or inherits from a platform base
        # 2. Has clear selectors
        # 3. No complex logic

        if info['platform']:
            # Platform-based adapters don't need migration
            return False

        if info['complexity'] == 'complex':
            return False

        if info['complexity'] == 'simple' and info['selectors']:
            return True

        return False


class ConfigGenerator:
    """
    Generate YAML config from adapter analysis.
    """

    def generate(self, info: Dict[str, Any]) -> str:
        """
        Generate YAML config from adapter info.

        Args:
            info: Adapter information from AdapterAnalyzer

        Returns:
            YAML string
        """
        config = {
            'name': self._make_name(info['domain']),
            'domains': [info['domain']],
            'encoding': 'utf-8',
            'story_url_pattern': self._simplify_pattern(info.get('url_pattern', '')),
            'rate_limit': 2.0,
        }

        if info.get('selectors'):
            config['selectors'] = {
                'story': info['selectors']
            }

        return yaml.dump(config, sort_keys=False, default_flow_style=False)

    def _make_name(self, domain: str) -> str:
        """Convert domain to readable name"""
        if not domain:
            return "Unknown Site"

        # Remove TLD
        name = re.sub(r'\.(com|net|org|io)$', '', domain)

        # Remove www
        name = re.sub(r'^www\.', '', name)

        # Capitalize words
        return ' '.join(word.capitalize() for word in name.split('.'))

    def _simplify_pattern(self, pattern: str) -> str:
        """Simplify regex pattern for YAML"""
        # Remove common regex escapes for YAML readability
        pattern = pattern.replace(r'\.', '.')
        pattern = pattern.replace(r'\?', '?')

        return pattern


class MigrationTool:
    """
    Main migration tool to analyze and migrate adapters.
    """

    def __init__(self, old_adapter_dir: Path, new_config_dir: Path):
        self.old_adapter_dir = old_adapter_dir
        self.new_config_dir = new_config_dir
        self.analyzer = AdapterAnalyzer
        self.generator = ConfigGenerator()

    def analyze_all(self) -> List[Dict[str, Any]]:
        """Analyze all adapters in the directory"""
        results = []

        for adapter_file in self.old_adapter_dir.glob('adapter_*.py'):
            try:
                analyzer = self.analyzer(adapter_file)
                info = analyzer.analyze()
                results.append(info)
            except Exception as e:
                print(f"Error analyzing {adapter_file}: {e}")

        return results

    def generate_report(self) -> str:
        """Generate migration report"""
        results = self.analyze_all()

        # Categorize adapters
        can_migrate = [r for r in results if r['can_migrate']]
        platform_based = [r for r in results if r['platform']]
        complex = [r for r in results if r['complexity'] == 'complex']

        report = f"""
# Migration Analysis Report

Total adapters analyzed: {len(results)}

## Migration Strategy

### ✅ Can migrate to YAML config: {len(can_migrate)}
These adapters are simple and can be converted to YAML configs.

### 🏭 Platform-based: {len(platform_based)}
These already use platform bases (eFiction, XenForo, etc.) - no action needed.

### ⚠️  Complex (keep as code): {len(complex)}
These have complex logic and should remain as custom adapters.

## Breakdown by Platform

"""
        # Group by platform
        platforms = {}
        for r in results:
            platform = r.get('platform', 'none')
            platforms.setdefault(platform, []).append(r)

        for platform, adapters in sorted(platforms.items()):
            report += f"\n### {platform.upper()}: {len(adapters)} adapters\n"

        report += f"""

## Migration Steps

1. **Platform-based adapters ({len(platform_based)}):**
   - No migration needed
   - Already use generic platform adapters

2. **Simple adapters ({len(can_migrate)}):**
   - Convert to YAML configs
   - Use config-driven adapter

3. **Complex adapters ({len(complex)}):**
   - Keep as custom adapters
   - Register in registry

## Estimated Reduction

- Before: {len(results)} adapter files
- After: ~{len(complex)} custom adapters + {len(can_migrate)} YAML configs
- Reduction: ~{100 - (len(complex) / len(results) * 100):.0f}% fewer code files to maintain
"""

        return report

    def migrate_adapter(self, adapter_file: Path) -> Optional[Path]:
        """
        Migrate a single adapter to YAML config.

        Returns:
            Path to generated config file, or None if can't migrate
        """
        analyzer = self.analyzer(adapter_file)
        info = analyzer.analyze()

        if not info['can_migrate']:
            print(f"Cannot migrate {adapter_file.name} (complexity: {info['complexity']})")
            return None

        # Generate config
        yaml_content = self.generator.generate(info)

        # Write config file
        config_filename = adapter_file.stem.replace('adapter_', '') + '.yaml'
        config_path = self.new_config_dir / config_filename

        config_path.write_text(yaml_content)
        print(f"✓ Generated {config_path}")

        return config_path
