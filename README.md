# Small Landlord, Calm Guide

A warm, plain-English, **education-only** manual for renting out a room, a
house, or an ADU (accessory dwelling unit) — the kind of small rental a regular
person handles on the side, not a property empire.

**This is never legal or financial advice.** It explains concepts in round
numbers and plain words so you can ask better questions. Housing laws vary a
lot by state, city, and even county — always check your local rules or talk to
a licensed professional before you act.

Built by [Asdale Dynamics, LLC](https://dylanasdale.github.io) — the same folks
who explain AI "like a friend would." No condescension, no jargon walls, no
$997 upsell.

## Who it's for

- renting out a spare room to a housemate for the first time
- renting out your house while you're away
- renting out an ADU/garage apartment/in-law suite
- anyone who's been handed a lease full of mysterious words like "abandonment"
  and "quiet enjoyment" and just wants to know what they mean

## What's inside

| Doc | What it covers |
| --- | --- |
| `docs/00-start-here.md` | How to use this guide, the mindset, the one-page disclaimer |
| `docs/01-lease-decoded.md` | Reading a lease clause by clause, using free plain-English forms |
| `docs/02-deposits.md` | Security deposits: amounts, deadlines, interest, itemized lists |
| `docs/03-rent-hikes.md` | Raising rent kindly and legally |
| `docs/04-screening-fairly.md` | Applications and background checks without discrimination |
| `docs/05-move-in-move-out.md` | Inspection checklists for both ends of a tenancy |
| `docs/06-repair-requests.md` | Handling "the sink is dripping" like a decent human |
| `docs/07-records.md` | What to keep, for how long, digital vs paper |
| `docs/08-taxes.md` | Taxes in round numbers — income, depreciation, 1099s |
| `docs/09-when-to-hire-a-pro.md` | When to hand it off (pro manager, or sell to a property company) |
| `docs/10-key-dates.md` | Companion piece to the **lease-key-dates-tracker-webapp** |
| `docs/11-glossary.md` | Every jargon word, decoded |

## Building the site

Docs are plain Markdown. A tiny dependency-free Python build script turns them
into a static HTML site in `build/`:

```bash
python3 scripts/build_site.py
# then open build/index.html in a browser, or:
python3 -m http.server --directory build 8080
```

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

The tests check that every chapter exists, the glossary covers the words the
manual actually uses, internal links resolve, checklists render, and the HTML
build produces sane output.

## Companion project

This guide pairs with **lease-key-dates-tracker-webapp**: that app tracks the
*when* (deadline countdowns for notices, renewals, deposit returns); the manual
teaches the *why* and *how*. See `docs/10-key-dates.md` for the mapping.

## License

MIT — see `LICENSE`. © 2026 Asdale Dynamics, LLC.

Education content only; not legal, tax, or financial advice.
