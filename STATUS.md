# STATUS.md — Small Landlord, Calm Guide

_Last updated: 2026-10-31_

## What was built

An education-only manual (Markdown + generated static HTML site) for renting
out a room, a house, or an ADU — plain English, warm tone, never legal/financial
advice, disclaimers on every page.

**Contents:**

- `docs/` — the 12-chapter manual (00 Start Here through 11 Glossary):
  - lease decoded clause-by-clause, with pointers to free plain-English forms
    (court self-help pages, state AG guides, HUD lead-paint material)
  - deposits: what they are, state-variation tables in round numbers, itemized
    returns, the "would I have paid anyway" wear-and-tear test
  - rent hikes: notice periods, sizing increases kindly, a model letter,
    retaliation caution, rent-control awareness
  - screening fairly: written criteria applied identically to everyone, HUD's
    seven protected classes plus state/local additions, assistance animals,
    credit/background-check consent
  - move-in/move-out: printable two-end inspection checklists and photos-habit
  - repair requests: emergency ladder, three-part reply scripts, DIY-vs-pro bar
  - records: one folder per tenancy, naming habit, retention table
  - taxes in round numbers: Schedule E income, expense offsets, depreciation
    (~building basis ÷ 28), repairs vs. improvements, room-rental pro-rata,
    15-day rule, 1099-NEC for contractors over $600, selling basics
  - when to hire a pro (manager ~8–10% of rent, evaluate list) or sell to a
    property company (discount-vs-certainty, lease-subject-to cautions)
  - key-dates chapter + glossary of every jargon word used
- `scripts/build_site.py` — dependency-free (stdlib) static site builder;
  Markdown → HTML with a warm stylesheet, TOC landing page, per-chapter pages
  with prev/next navigation and disclaimer bars
- `assets/style.css` — site styles
- `tests/` — 39 tests (unittest, stdlib only)
- `README.md`, `LICENSE` (MIT, exact line: `Copyright (c) 2026 Asdale
  Dynamics, LLC`), `.gitignore`
- Companion project noted throughout: **lease-key-dates-tracker-webapp**
  (that app tracks the *when*, this manual teaches the *why*; see
  `docs/10-key-dates.md` for the mapping).

## How to run it

```bash
# build the static site (outputs to build/)
python3 scripts/build_site.py              # or -o /some/other/dir

# view it
python3 -m http.server --directory build 8080   # then open the URL locally

# run everything (all stdlib, no dependencies to install)
python3 -m unittest discover -s tests -v
```

## Verification results

- `python3 -m unittest discover -s tests -v` → **39/39 OK** (content tests,
  renderer unit tests, and end-to-end build tests)
- `python3 scripts/build_site.py` → builds 13 pages (12 chapters + TOC landing)
  + `style.css`, exit code 0, no warnings
- Build is deterministic between runs (covered by a test)
- All internal links in docs and in generated HTML resolve (tested)
- Every generated page carries the education-only disclaimer bar (tested)
- No secrets/API keys/personal data patterns in docs or README (tested)
- Manual reviewed for typos/stray characters before commit

## Known gaps

- U.S.-shaped guidance with state-by-state variability handled via
  "look up your state" roundings, not per-state tables — a future edition
  could link each state's official guide one by one.
- The HTML generator covers the Markdown subset the manual actually uses
  (headings, lists incl. task lists, tables, blockquotes, fenced code,
  inline styling, links). It intentionally is not a full CommonMark
  implementation; nested lists and some edge syntax are unsupported.
- Site search is not included (plausible future extra); navigation is
  TOC + prev/next + the numeric chapter bar.
- Line-continuation lines inside list items must be indented ≥ 2 spaces;
  not tab-tolerant.
- Companion webapp lives in its own repo — its countdown behavior is
  documented here but not integrated at run time.

## Repo layout

```
docs/            the manual (markdown)
scripts/         build_site.py
assets/          style.css
build/           generated site (gitignored; rebuild anytime)
tests/           unittest suite
```

MIT — © 2026 Asdale Dynamics, LLC.
