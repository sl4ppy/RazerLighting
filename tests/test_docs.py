"""Documentation consistency checks — links, effect counts, metadata."""

import os
import re

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestMarkdownLinks:
    """Verify internal markdown links resolve to existing files."""

    def _find_md_files(self):
        md_files = []
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Skip hidden dirs, .venv, __pycache__
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for f in files:
                if f.endswith(".md"):
                    md_files.append(os.path.join(root, f))
        return md_files

    def _extract_links(self, filepath):
        """Extract all markdown links [text](path) from a file."""
        with open(filepath) as f:
            content = f.read()
        # Match [text](path) but not external URLs
        links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
        local_links = []
        for text, path in links:
            if path.startswith("http://") or path.startswith("https://"):
                continue
            # Strip anchor
            path = path.split("#")[0]
            if path:
                local_links.append((text, path))
        return local_links

    def test_all_internal_links_resolve(self):
        broken = []
        for md_file in self._find_md_files():
            md_dir = os.path.dirname(md_file)
            for text, link_path in self._extract_links(md_file):
                # Skip placeholder screenshot references (SS-xxx.png)
                # These are documented in SCREENSHOT-BRIEFS.md but not yet captured
                if re.search(r'SS-\d+\.png$', link_path):
                    continue
                full_path = os.path.normpath(os.path.join(md_dir, link_path))
                if not os.path.exists(full_path):
                    rel_md = os.path.relpath(md_file, PROJECT_ROOT)
                    broken.append(f"{rel_md}: [{text}]({link_path}) -> {full_path}")
        if broken:
            pytest.fail(f"Broken links:\n" + "\n".join(broken))


class TestEffectCounts:
    """Verify effect count is consistent across code and docs."""

    def test_readme_says_28(self):
        readme = os.path.join(PROJECT_ROOT, "README.md")
        with open(readme) as f:
            content = f.read()
        assert "28" in content, "README should mention 28 effects"

    def test_effects_md_says_28(self):
        effects_md = os.path.join(PROJECT_ROOT, "EFFECTS.md")
        if os.path.exists(effects_md):
            with open(effects_md) as f:
                content = f.read()
            assert "28" in content

    def test_discovered_count_matches(self):
        from effects.common import discover_effects
        effects = discover_effects()
        assert len(effects) == 28

    def test_categories_cover_28(self):
        from config_window import EFFECT_CATEGORIES
        total = sum(len(v) for v in EFFECT_CATEGORIES.values())
        assert total == 28, f"Categories cover {total} effects, expected 28"

    def test_descriptions_cover_28(self):
        from config_window import EFFECT_DESCRIPTIONS
        assert len(EFFECT_DESCRIPTIONS) == 28


class TestVersionConsistency:
    """Verify version is consistent across the project."""

    def test_about_window_version(self):
        from about_window import VERSION
        parts = VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_no_stale_version_refs(self):
        """Check no source files reference old version 1.0.0."""
        from about_window import VERSION
        if VERSION != "1.0.0":
            for root, dirs, files in os.walk(PROJECT_ROOT):
                dirs[:] = [d for d in dirs if not d.startswith(".")
                           and d != "__pycache__" and d != "tests"]
                for f in files:
                    if f.endswith(".py") or f.endswith(".md"):
                        path = os.path.join(root, f)
                        with open(path) as fh:
                            content = fh.read()
                        if "1.0.0" in content:
                            rel = os.path.relpath(path, PROJECT_ROOT)
                            pytest.fail(f"Stale version 1.0.0 in {rel}")


class TestNoStaleTealColors:
    """Verify old teal accent colors are fully replaced."""

    OLD_COLORS = ["#00cc88", "#00ffaa", "#00ffcc", "#00ee99", "#00aa66"]

    @pytest.mark.parametrize("color", OLD_COLORS)
    def test_no_old_teal_in_python(self, color):
        for root, dirs, files in os.walk(PROJECT_ROOT):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"
                       and d != "tests"]
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path) as fh:
                        content = fh.read()
                    if color.lower() in content.lower():
                        rel = os.path.relpath(path, PROJECT_ROOT)
                        pytest.fail(f"Old teal color {color} found in {rel}")
