"""Content tests for the Small Landlord, Calm Guide manual.

Run with:  python3 -m unittest discover -s tests -v
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CHAPTER_FILES = [
    "00-start-here.md",
    "01-lease-decoded.md",
    "02-deposits.md",
    "03-rent-hikes.md",
    "04-screening-fairly.md",
    "05-move-in-move-out.md",
    "06-repair-requests.md",
    "07-records.md",
    "08-taxes.md",
    "09-when-to-hire-a-pro.md",
    "10-key-dates.md",
    "11-glossary.md",
]

# Terms every reader should find in the glossary, per the project goal.
REQUIRED_GLOSSARY_TERMS = [
    "Deposit",
    "Fair housing",
    "Habability",
    "Normal wear and tear",
    "Quiet enjoyment",
    "Notice to quit",
    "Self-help eviction",
    "Depreciation",
    "Amendment",
    "Security deposit",
]

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9]{16,}",      # API-style keys
    r"AKIA[0-9A-Z]{16}",         # AWS access keys
    r"-----BEGIN [A-Z ]*PRIVATE KEY",  # private key blocks
    r"@gmail\.com",              # personal email addresses
    r"\b\d{3}-\d{2}-\d{4}\b",    # SST-style numbers
]


class TestDocs(unittest.TestCase):
    def setUp(self):
        self.md = {f: (DOCS / f).read_text(encoding="utf-8") for f in CHAPTER_FILES}
        self.glossary = self.md["11-glossary.md"]

    def test_all_chapters_exist(self):
        for name in CHAPTER_FILES:
            self.assertTrue((DOCS / name).exists(), f"missing docs/{name}")

    def test_no_extra_or_missing_files(self):
        found = sorted(p.name for p in DOCS.glob("*.md"))
        self.assertEqual(found, sorted(CHAPTER_FILES))

    def test_each_chapter_starts_with_h1(self):
        for name, text in self.md.items():
            self.assertTrue(text.lstrip().startswith("# "),
                f"{name} should start with an H1 heading")

    def test_no_stray_cjk_or_cyrillic(self):
        pattern = re.compile(r"[\u0400-\u04FF\u3040-\u30FF\u4E00-\u9FFF]")
        for name, text in self.md.items():
            m = pattern.search(text)
            self.assertIsNone(m, f"{name} contains stray non-Latin characters")

    def test_no_secrets_or_personal_data(self):
        pattern = re.compile("|".join(SECRET_PATTERNS))
        for name, text in self.md.items():
            m = pattern.search(text)
            self.assertIsNone(m, f"{name} matches suspicious pattern: {m}")

    def test_glossary_covers_core_terms(self):
        missing = [
            t for t in REQUIRED_GLOSSARY_TERMS
            if f"**{t}" not in self.glossary
        ]
        self.assertEqual(missing, [], f"glossary is missing: {missing}")

    def test_education_only_disclaimer_present(self):
        text = self.md["00-start-here.md"].lower()
        self.assertIn("education only", text)

    def test_usage_of_free_plain_forms(self):
        text = self.md["01-lease-decoded.md"]
        lowered = text.lower()
        for phrase in ("free", "attorney general", "hud"):
            self.assertIn(phrase, lowered)

    def test_taxes_use_round_numbers(self):
        text = self.md["08-taxes.md"]
        for phrase in ["round number", "$18,000", "$5,600"]:
            self.assertIn(phrase, text)

    def test_companion_app_mentioned(self):
        text = self.md["10-key-dates.md"]
        self.assertIn("lease-key-dates-tracker-webapp", text)

    def test_checklists_present_as_task_items(self):
        checklist_homes = [
            "00-start-here.md",
            "01-lease-decoded.md",
            "02-deposits.md",
            "03-rent-hikes.md",
            "04-screening-fairly.md",
            "05-move-in-move-out.md",
            "06-repair-requests.md",
            "07-records.md",
            "10-key-dates.md",
        ]
        for name in checklist_homes:
            self.assertRegex(
                self.md[name], r"\n-\s\[\s\]",
                f"{name} should contain at least one checkbox item",
            )

    def test_move_in_and_move_out_checklists_both_exist(self):
        text = self.md["05-move-in-move-out.md"]
        self.assertIn("MOVE-IN / MOVE-OUT INSPECTION", text)
        self.assertGreaterEqual(len(re.findall(r"- \[ \]", text)), 8,
            "chapter 5 should carry a full printable checklist")

    def test_hire_a_pro_covers_both_paths(self):
        text = self.md["09-when-to-hire-a-pro.md"]
        self.assertIn("property manager", text.lower())
        self.assertIn("property company", text.lower())

    def test_internal_md_links_resolve(self):
        link_re = re.compile(r"\]\(([^)]+)\)")
        for name, text in self.md.items():
            for m in link_re.finditer(text):
                target = m.group(1)
                if target.startswith(("http://", "https://", "#")):
                    continue
                self.assertTrue(
                    (DOCS / target).exists() or (ROOT / target).exists(),
                    f"{name}: broken relative link '{target}'",
                )

    def test_next_chapter_pointers_chain(self):
        for i, name in enumerate(CHAPTER_FILES[:-1]):
            next_doc = re.search(r"Next: (Chapter.+)", self.md[name])
            self.assertIsNotNone(next_doc, f"{name} should end with a Next pointer")
            self.assertIn(f"Chapter {i + 1}", next_doc.group(1),
                f"{name} should point forward to chapter {i + 1}")


class TestLicense(unittest.TestCase):
    def test_license_exists_with_exact_copyright(self):
        lic = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Copyright (c) 2026 Asdale Dynamics, LLC", lic)
        self.assertIn("Permission is hereby granted", lic)

    def test_readme_credits_and_disclaims(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Asdale Dynamics, LLC", readme)
        self.assertIn("education-only", readme.lower())
        self.assertIn("lease-key-dates-tracker-webapp", readme)
        self.assertIn("python3 scripts/build_site.py", readme)
        self.assertIn("python3 -m unittest discover", readme)


class TestMarkdownRenderer(unittest.TestCase):
    def setUp(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_site import _render_markdown
        self.render = _render_markdown

    def _mod(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_site
        return build_site

    def test_heading_gets_id(self):
        mod = self._mod()
        self.assertEqual(
            mod._render_markdown("# Hello World"),
            '<h1 id="hello-world">Hello World</h1>',
        )

    def test_paragraph_inline_formatting(self):
        html_out = self.render("This is *soft* and **firm** and `raw`.")
        self.assertIn("<em>soft</em>", html_out)
        self.assertIn("<strong>firm</strong>", html_out)
        self.assertIn("<code>raw</code>", html_out)

    def test_link(self):
        html_out = self.render("See [the repo](https://example.com/x).")
        self.assertIn('<a href="https://example.com/x">the repo</a>', html_out)

    def test_html_escaped(self):
        html_out = self.render("Use <b> tags & <script> carefully.")
        self.assertNotIn("<script>", html_out)
        self.assertIn("&amp;", html_out)

    def test_task_list(self):
        html_out = self.render("- [ ] A thing\n- [x] Another\n")
        self.assertIn('<ul class="task-list">', html_out)
        self.assertIn('<input type="checkbox" disabled > A thing', html_out)
        self.assertIn('<input type="checkbox" disabled checked> Another', html_out)

    def test_task_list_continuation(self):
        html_out = self.render(
            "- [ ] Main line\n      wrapped line\n- [ ] One more\n"
        )
        self.assertIn("wrapped line", html_out)
        self.assertEqual(html_out.count("</ul>"), 1)

    def test_ordered_list_with_continuation(self):
        html_out = self.render(
            "1. **Bold.** First item text\n   continues here with *em*.\n"
            "2. Second.\n"
        )
        self.assertIn("<ol>", html_out)
        self.assertIn("continues here with <em>em</em>", html_out)
        self.assertEqual(html_out.count("</ol>"), 1)

    def test_fence_code_block(self):
        html_out = self.render("```\n<script>bad</script>\n```\n")
        self.assertIn("<pre><code>", html_out)
        self.assertIn("&lt;script&gt;", html_out)

    def test_pipe_table(self):
        html_out = self.render(
            "| A | B |\n| --- | --- |\n| 1 | 2 |\n"
        )
        self.assertIn("<table><thead>", html_out)
        self.assertIn("<th>A</th>", html_out)
        self.assertIn("<th>B</th>", html_out)
        self.assertIn("</tr></thead><tbody>", html_out)
        self.assertIn("<td>1</td>", html_out)
        self.assertIn("<td>2</td>", html_out)
        self.assertIn("</tbody></table>", html_out)

    def test_blockquote(self):
        html_out = self.render("> Careful words\n> here\n")
        self.assertIn("<blockquote>", html_out)
        self.assertIn("Careful words", html_out)

    def test_horizontal_rule(self):
        html_out = self.render("above\n\n---\n\nbelow\n")
        self.assertIn("<hr>", html_out)


if __name__ == "__main__":
    unittest.main()
