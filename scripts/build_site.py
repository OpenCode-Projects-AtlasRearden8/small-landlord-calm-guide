#!/usr/bin/env python3
"""Small Landlord, Calm Guide — static site builder.

Turns the Markdown manual in docs/ into a plain, static HTML site in build/.
Standard library only: no dependencies, no network, no secrets.

Usage:
    python3 scripts/build_site.py            # build into ./build
    python3 scripts/build_site.py -o outdir  # build elsewhere
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ASSETS = ROOT / "assets"

SITE_TITLE = "Small Landlord, Calm Guide"
SITE_TAGLINE = "Renting out a room, a house, or an ADU — explained like a friend would."
DISCLAIMER = (
    "Education only — this is never legal, tax, or financial advice. "
    "Rules vary by state, city, and county; check your local sources before you act."
)
FOOTER = (
    "An Asdale Dynamics, LLC project. MIT licensed. "
    'Part of the <a href="https://dylanasdale.github.io">dylanasdale.github.io</a> '
    "collection of calm, plain-English guides."
)

# ---------------------------------------------------------------- markdown ---

def _inline(text: str) -> str:
    """Escape HTML, then apply inline markdown."""
    out = html.escape(text, quote=False)
    # inline code must run first so code contents aren't further munged
    out = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", out)
    out = re.sub(r"(?<!\*)\*([^*\s][^*]*)\*(?!\*)", lambda m: f"<em>{m.group(1)}</em>", out)
    out = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: _link(m.group(1), m.group(2)), out
    )
    return out


def _link(label: str, target: str) -> str:
    return f'<a href="{html.escape(target, quote=True)}">{label}</a>'


def _slug(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[\s_]+", "-", s) or "section"


def _close_list(open_tag: str) -> str:
    return "</ul>" if open_tag.startswith("<ul") else "</ol>"


_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _render_markdown(md: str) -> str:
    """Very small markdown subset -> HTML body string.

    Supports: ATX headings, paragraphs, blockquotes, fenced code blocks,
    pipe tables, ordered/unordered lists (with - [ ] task items), and ---/***
    horizontal rules. Everything else is escaped plain text.
    """
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    in_task_list = False

    def close_task_list() -> None:
        nonlocal in_task_list
        if in_task_list:
            out.append("</ul>")
            in_task_list = False

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            close_task_list()
            i += 1
            continue

        m = _HEADER_RE.match(line)
        if m:
            close_task_list()
            level = len(m.group(1))
            text = m.group(2).strip()
            slug = _slug(text)
            out.append(
                f'<h{level} id="{slug}">{_inline(text)}</h{level}>'
            )
            i += 1
            continue

        if re.match(r"^\s{0,3}(\*\s*\*\s*\*|-{3,}|_{3,})\s*$", line):
            close_task_list()
            out.append("<hr>")
            i += 1
            continue

        if line.lstrip().startswith("```"):
            close_task_list()
            out.append("<pre><code>")
            i += 1
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                out.append(html.escape(lines[i]))
                i += 1
            out.append("</code></pre>")
            i += 1  # skip closing fence
            continue

        if line.startswith(">"):
            close_task_list()
            quote: list[str] = []
            while i < len(lines) and lines[i].startswith(">"):
                quote.append(lines[i].lstrip()[1:].lstrip())
                i += 1
            out.append("<blockquote>")
            out.append(_render_markdown("\n".join(quote)))
            out.append("</blockquote>")
            continue

        if "|" in line and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]):
            close_task_list()
            rows = []
            header = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>")
            for cell in header:
                out.append(f"<th>{_inline(cell)}</th>")
            out.append("</tr></thead><tbody>")
            for row in rows:
                out.append("<tr>")
                for cell in row:
                    out.append(f"<td>{_inline(cell)}</td>")
                out.append("</tr>")
            out.append("</tbody></table>")
            continue

        li_match = re.match(r"^\s*[-*]\s+(.*)$", line)
        ol_match = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if li_match or ol_match:
            close_task_list()
            open_tag: str | None = None
            while True:
                text = (ol_match or li_match).group(1)
                task = re.match(r"\[([ xX])\]\s+(.*)$", text)
                # decide the list container for this item
                if task and not ol_match:
                    container = '<ul class="task-list">'
                elif ol_match:
                    container = "<ol>"
                else:
                    container = "<ul>"
                if open_tag != container:
                    if open_tag:
                        out.append(_close_list(open_tag))
                    out.append(container)
                    open_tag = container
                if task:
                    checked = "checked" if task.group(1).lower() == "x" else ""
                    out.append(
                        f'<li><input type="checkbox" disabled {checked}> {_inline(task.group(2))}'
                    )
                else:
                    out.append(f"<li>{_inline(text)}")
                # fold indented continuation lines into this item
                j = i + 1
                continuation: list[str] = []
                while j < len(lines):
                    nxt = lines[j]
                    if not nxt.strip():
                        if j + 1 < len(lines) and re.match(r"^\s*([-*]\s+|\d+\.\s+)", lines[j + 1]):
                            break
                        break
                    if (
                        nxt.startswith("  ")
                        and not _HEADER_RE.match(nxt)
                        and not nxt.lstrip().startswith("```")
                        and not nxt.startswith(">")
                        and "|" not in nxt
                        and not re.match(r"^\s*([-*])\s+", nxt)
                        and not re.match(r"^\s*\d+\.\s+", nxt)
                        and not re.match(r"^\s*([-*_]\s*){3,}$", nxt)
                    ):
                        continuation.append(nxt.strip())
                        j += 1
                    else:
                        break
                i = j
                if continuation:
                    out[-1] += _inline(" " + " ".join(continuation))
                out[-1] += "</li>"
                if i >= len(lines):
                    break
                # next item?
                li_match = re.match(r"^\s*[-*]\s+(.*)$", lines[i])
                ol_match = re.match(r"^\s*\d+\.\s+(.*)$", lines[i])
                if not (li_match or ol_match):
                    break
            if open_tag:
                out.append(_close_list(open_tag))
            continue

        close_task_list()
        para: list[str] = [line]
        while (
            i + 1 < len(lines)
            and lines[i + 1].strip()
            and not _HEADER_RE.match(lines[i + 1])
            and not lines[i + 1].startswith(">")
            and not lines[i + 1].lstrip().startswith("```")
            and "|" not in lines[i + 1]
            and not re.match(r"^\s*[-*]\s+", lines[i + 1])
            and not re.match(r"^\s*\d+\.\s+", lines[i + 1])
            and not re.match(r"^\s*([-*_]\s*){3,}$", lines[i + 1])
        ):
            i += 1
            para.append(lines[i])
        out.append(f"<p>{_inline(' '.join(p.strip() for p in para))}</p>")
        i += 1

    close_task_list()
    return "\n".join(out)


# -------------------------------------------------------------------- site ---


def doc_title(md: str) -> str:
    for line in md.splitlines():
        m = _HEADER_RE.match(line)
        if m:
            return m.group(2).strip()
    return "Untitled"


def collect_docs() -> list[tuple[Path, str]]:
    files = sorted(DOCS.glob("*.md"))
    if not files:
        raise SystemExit("docs/ contains no markdown files")
    return [(f, f.read_text(encoding="utf-8")) for f in files]


def page(title: str, body_html: str, nav_html: str, prevnext: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — {SITE_TITLE}</title>
<meta name="description" content="{html.escape(SITE_TAGLINE + ' ' + DISCLAIMER)}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<div class="disclaimer-bar">{html.escape(DISCLAIMER)}</div>
<nav class="topbar">
<a href="index.html" style="font-weight:bold">{html.escape(SITE_TITLE)}</a>
<span class="chapters">{nav_html}</span>
</nav>
{body_html}
<nav class="prevnext">{prevnext}</nav>
<footer class="site-footer">{FOOTER}</footer>
</main>
</body>
</html>
"""


def build(outdir: Path) -> None:
    docs = collect_docs()
    outdir.mkdir(parents=True, exist_ok=True)
    for stale in outdir.glob("*.html"):
        stale.unlink()

    chapters: list[tuple[str, str, str]] = []  # (html_name, title, slug-fragment)
    for path, md in docs:
        name = f"{path.stem}.html"
        title = doc_title(md)
        chapters.append((name, title, path.stem))
        body = _render_markdown(md)
        page_html = page(title, body, _nav(chapters, path.stem), "")
        if not page_html:
            raise SystemExit(f"empty page generated for {path.name}")
        (outdir / name).write_text(page_html, encoding="utf-8")

    # landing page: intro + full table of contents
    toc_items = []
    for name, title, stem in chapters:
        toc_items.append(
            f'<li><a href="{name}">{html.escape(title)}</a></li>'
        )
    toc_html = "<ol>\n" + "\n".join(toc_items) + "\n</ol>"
    intro = (
        "<p class=\"hero\">A plain-English manual for renting out one room, one house, "
        "or one ADU: leases decoded, deposits explained, screening done fairly, "
        "checklists that end arguments, records that keep you calm, and the "
        "round-number way to think about taxes and about handing it off.</p>"
        '<div class="toc-card"><h2>The manual</h2>' + toc_html + "</div>"
    )
    index_html = page(
        "Start here",
        f"<h1>{SITE_TITLE}</h1>\n{intro}\n{DISCLAIMER_PARA}",
        _nav(chapters, None),
        "",
    )
    (outdir / "index.html").write_text(index_html, encoding="utf-8")

    css_out = outdir / "style.css"
    if css_out.exists():
        css_out.unlink()  # write fresh copy
    shutil.copy(ASSETS / "style.css", css_out)

    # prev/next links get a second pass once all chapters are known
    for path, md in docs:
        name = f"{path.stem}.html"
        body = _render_markdown(md)
        title = doc_title(md)
        (outdir / name).write_text(
            page(
                title,
                body,
                _nav(chapters, path.stem),
                _prevnext(chapters, path.stem),
            ),
            encoding="utf-8",
        )

    print(f"Built {len(chapters) + 1} pages + style.css into {outdir}")


def _nav(chapters: list[tuple[str, str, str]], current: str | None) -> str:
    links = []
    for name, _title, stem in chapters:
        label = stem.split("-")[0]  # "00", "01"...
        cls = ' style="font-weight:bold"' if stem == current else ""
        links.append(f'<a href="{name}"{cls}>{label}</a>')
    return " · ".join(links)


def _prevnext(chapters: list[tuple[str, str, str]], current: str) -> str:
    idx = [stem for _n, _t, stem in chapters].index(current)
    parts = []
    if idx > 0:
        pname, ptitle, _ = chapters[idx - 1]
        parts.append(f'<a href="{pname}">&larr; {html.escape(ptitle)}</a>')
    else:
        parts.append("<span></span>")
    if idx < len(chapters) - 1:
        nname, ntitle, _ = chapters[idx + 1]
        parts.append(f'<a href="{nname}">{html.escape(ntitle)} &rarr;</a>')
    else:
        parts.append("<span></span>")
    return "".join(parts)


DISCLAIMER_PARA = (
    "<blockquote><p><strong>The one rule above all rules:</strong> this guide is "
    "education only — never legal, tax, or financial advice. Housing law varies a "
    "lot by state and city. Check local sources or a licensed professional before "
    "you act.</p></blockquote>"
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static site")
    parser.add_argument("-o", "--out", default=str(ROOT / "build"),
                        help="output directory (default: build/)")
    args = parser.parse_args()
    build(Path(args.out))


if __name__ == "__main__":
    main()