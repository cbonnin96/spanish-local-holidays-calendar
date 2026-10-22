# Spanish Local Holidays Calendar

A subscribable calendar feed (iCal/ICS) that bundles all the holidays that actually
affect you in Spain: **national**, **regional/autonomic**, and **local/municipal**,
for a given city.

**MVP scope: Palma (Palma de Mallorca, Balearic Islands, Spain) only.** The
long-term vision below (multi-city, multi-country) is the north star, but the
first working version targets a single city end to end — one hardcoded feed
combining Spain's national holidays, the Balearic Islands' regional holidays,
and Palma's local holidays — before generalizing to a city picker.

## Subscribe

```
https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/palma.ics
```

Add this URL in your calendar app as a subscription (not a one-time import):
Google Calendar → "Other calendars" → "From URL"; Apple Calendar → File →
"New Calendar Subscription". The file is kept current by a scheduled GitHub
Action (see below), so your calendar app will pick up changes automatically.

## Why

Most holiday calendars only cover national public holidays. In countries with
decentralized holiday systems (e.g. Spain, where autonomous communities and
individual municipalities each add their own non-working days), there's no single
feed that reflects the *actual* days off for a specific city. This project aims to
fix that: pick your city once, subscribe to one calendar URL, and get every holiday
that applies to you — no manual merging of three different sources, no missing the
one local "fiesta" day your city adds on top of the national/regional ones.

## MVP goals (Palma only)

- **One feed, three layers.** A single `.ics` file/URL for Palma combining:
  - Spain's national public holidays
  - The Balearic Islands' regional (autonomic) holidays
  - Palma's local/municipal holidays (e.g. Sant Sebastià)
- **Standard calendar subscription.** Output a standard `.ics` feed that any
  calendar app (Google Calendar, Apple Calendar, Outlook, etc.) can subscribe to
  and auto-refresh, not a one-time import.
- **Correct and complete for the current + next year.** Since this is hardcoded
  to one city, accuracy matters more than coverage — every holiday Palma
  actually observes should be in there, with the right date (including any
  "moved to Monday" substitutions).
- **Transparent sourcing.** Each holiday traceable to an official or reliable
  source, so it's easy to verify and to update year over year.
- **Self-updating, no manual transcription.** The feed is built by scraping the
  official source directly, so a new year's holidays flow in automatically
  once published, instead of someone hand-copying dates into a file.

## Non-goals (for the MVP)

- No city picker, no other cities, no multi-country data model yet — Palma is
  hardcoded. Generalizing comes after the MVP proves useful.
- Not a general-purpose events calendar (concerts, festivals without an
  associated day off, etc.) — only actual holidays/non-working days.
- No UI beyond maybe a single static page with the subscription link and
  instructions — the deliverable is the feed itself.

## MVP shape

1. **Scraper** — fetches and parses the official CAIB labor calendar page for
   the current and next year (when published), extracting both the general
   Illes Balears holiday list and Palma's local holidays.
2. **Feed generator** — turns the scraped holidays into a valid `.ics` file.
3. **Automation** — a scheduled GitHub Action re-runs the scraper + generator
   weekly (and on demand), committing `output/palma.ics` back to the repo only
   when it actually changed. No manual execution needed, on your machine or
   otherwise.
4. **Hosting** — the committed `.ics` file is served straight from GitHub's
   raw content URL (see "Subscribe" above), which is itself stable and
   auto-updating since the Action keeps it current.

Implemented in Python, running inside Docker for local development; CI runs
natively on the GitHub Actions runner (no Docker build needed there).

## Project structure

```
spanish-local-holidays-calendar/
├── Dockerfile
├── Makefile
├── requirements.txt
├── spanish_local_holidays_calendar/
│   ├── models.py          # Holiday dataclass (date, name, scope, source_url)
│   ├── scraper.py         # fetches + parses the CAIB page into Holiday objects
│   ├── generate_ics.py    # builds a .ics Calendar from Holiday objects
│   └── __main__.py        # CLI entrypoint: scrape current+next year, write output/palma.ics
├── tests/
│   ├── fixtures/aao_2026_sample.html   # trimmed, stable copy of the real page structure
│   ├── test_scraper.py
│   └── test_generate_ics.py
├── .github/workflows/update-calendar.yml   # scheduled regeneration + commit
└── output/palma.ics       # generated artifact, committed (this is what's served)
```

**Build/run:**
```
make build      # docker build -t spanish-local-holidays-calendar .
make generate   # scrape live CAIB page, write output/palma.ics
make test       # run the test suite inside the container
```

The scraper is scoped to municipalities listed as a single entry (no
sub-localities) — this covers Palma, but not municipalities split into
several localities (e.g. Andratx / Port d'Andratx / s'Arracó), which the
parser doesn't disambiguate.

The CAIB source doesn't separate national from regional holidays — its
"general Illes Balears" list already folds Spain's national holidays (New
Year, National Day, Christmas, etc.) in with the Balearics' own additions
(e.g. Dia de les Illes Balears). The MVP tags that whole list `scope:
regional` rather than guessing a split; Palma's own holidays are tagged
`scope: local`.

## Future vision (post-MVP)

Once Palma works end to end, generalize to:
- A data layer structured per country → region → city, instead of one hardcoded
  file.
- A subscription endpoint per city (e.g.
  `https://.../calendar/es/balearic-islands/palma.ics`).
- A simple picker UI to search/select a city and get its subscription URL.

## Decisions

- **Data source:** the Balearic Islands government's official labor calendar
  site, Catalan edition — https://www.caib.es/sites/calendarilaboral/ca/aao_2026/
  — covers national, regional, and local (per-municipality) holidays for the
  Balearics, including Palma, with holiday names in Catalan (e.g. "Sant
  Sebastià", "Cap d'Any"). Published year by year (new year's page appears
  when available).
- **Years covered:** current + next year, when published. No historical years
  for the MVP.
- **Hosting model:** static `.ics` file, regenerated weekly (and on manual
  trigger) by a GitHub Action, committed back to the repo, and served from
  its raw.githubusercontent.com URL — no server to run, no GitHub Pages setup
  needed, and holiday data changes rarely enough that weekly regeneration is
  plenty fresh.
