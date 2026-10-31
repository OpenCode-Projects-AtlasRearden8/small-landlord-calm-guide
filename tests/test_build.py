"""End-to-end build tests for the static site generator.

Run with:  python3 -m unittest discover -s tests -v
"""

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPT = ROOT / "scripts" / "build_site.py"


class TestBuild(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="slcg-build-"))
        cls.out = cls.tmp / "site"
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "-o", str(cls.out)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        cls.result = result
        cls.generated = sorted(p.name for p in cls.out.glob("*.html"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_build_exit_ok(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)

    def test_build_no_warnings(self):
        self.assertNotIn("Warning", self.result.stderr)

    def test_pages_generated(self):
        expected = {"index.html", "style.css"} | {
            f.replace(".md", ".html") for f in sorted((ROOT / "docs").glob("*.md"))
            for f in [f.name]
        }
        found = set(self.generated) | {"style.css", "index.html"}
        self.assertEqual(found, expected)

    def test_index_links_every_chapter(self):
        index = (self.out / "index.html").read_text(encoding="utf-8")
        for f in sorted((ROOT / "docs").glob("*.md")):
            self.assertIn(f'{f.stem}.html', index,
                f"index should link {f.stem}.html")

    def test_every_page_has_disclaimer(self):
        for page in self.out.glob("*.html"):
            html_out = page.read_text(encoding="utf-8")
            self.assertIn("disclaimer-bar", html_out, page.name)
            self.assertIn("education only", html_out.lower(), page.name)

    def test_every_page_links_stylesheet(self):
        copied = (self.out / "style.css").read_text(encoding="utf-8")
        self.assertIn("--paper", copied)
        for page in self.out.glob("*.html"):
            self.assertIn('<link rel="stylesheet" href="style.css">',
                          page.read_text(encoding="utf-8"), page.name)

    def test_all_internal_links_resolve(self):
        for page in self.out.glob("*.html"):
            html_out = page.read_text(encoding="utf-8")
            for m in re.finditer(r'href="([^"#]+)"', html_out):
                target = m.group(1)
                if target.startswith(("http://", "https://")):
                    continue
                self.assertTrue((self.out / target).exists(),
                    f"{page.name}: broken link to {target}")

    def test_prevnext_chains(self):
        chapters = sorted((ROOT / "docs").glob("*.md"))
        for i, f in enumerate(chapters):
            page = self.out / f"{f.stem}.html"
            navm = re.search(r'class="prevnext">(.*?)</nav>', page.read_text(encoding="utf-8"), re.S)
            self.assertIsNotNone(navm, f"{f.name} should have a prevnext nav")
            nav = navm.group(1)
            if i == 0:
                self.assertIn("&rarr;", nav)
                self.assertNotIn("&larr;", nav)
            elif i == len(chapters) - 1:
                self.assertIn("&larr;", nav)
                self.assertNotIn("&rarr;", nav)
            else:
                self.assertIn("&rarr;", nav)
                self.assertIn("&larr;", nav)
            if i > 0:
                self.assertIn(chapters[i - 1].stem + ".html", nav,
                    f"{f.name} should link back")
            if i < len(chapters) - 1:
                self.assertIn(chapters[i + 1].stem + ".html", nav,
                    f"{f.name} should link forward")

    def test_checkboxes_render_on_site(self):
        page = (self.out / "05-move-in-move-out.html").read_text(encoding="utf-8")
        self.assertIn('class="task-list"', page)
        self.assertGreaterEqual(page.count('type="checkbox"'), 8)

    def test_rebuild_is_clean(self):
        # Building twice must not litter or diverge (spot-check one page).
        result2 = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "-o", str(self.out)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(result2.returncode, 0, result2.stderr)

    def test_deterministic_between_runs(self):
        first = (self.out / "index.html").read_text(encoding="utf-8")
        shutil.rmtree(self.out)
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT), "-o", str(self.out)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(first, (self.out / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
