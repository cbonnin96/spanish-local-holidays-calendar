# Spanish Local Holidays Calendar

A subscribable calendar feed (iCal/ICS) that bundles all the holidays that actually
affect you in Spain: **national**, **regional/autonomic**, and **local/municipal**,
for a given city.

## Implemented cities

| City | Region | Source of truth |
|------|--------|------------------|
| Palma de Mallorca | Balearic Islands | [CAIB labor calendar, Catalan edition](https://www.caib.es/sites/calendarilaboral/ca/aao_2026/) |

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

## Non-goals

- No city picker, no other cities, no multi-country data model yet — Palma is
  hardcoded. Generalizing comes after the MVP proves useful.
- Not a general-purpose events calendar (concerts, festivals without an
  associated day off, etc.) — only actual holidays/non-working days.
- No UI beyond maybe a single static page with the subscription link and
  instructions — the deliverable is the feed itself.

## Shape

1. **Scraper** — fetches and parses the official source for the current and
   next year (when published), extracting both the general/regional holiday
   list and the city's local holidays. For Palma, that's the CAIB labor
   calendar (see "Implemented cities" above).
2. **Feed generator** — turns the scraped holidays into a valid `.ics` file.
3. **Automation** — a scheduled GitHub Action re-runs the scraper + generator
   monthly (and on demand), committing `output/palma.ics` back to the repo only
   when it actually changed. No manual execution needed, on your machine or
   otherwise.
4. **Hosting** — the committed `.ics` file is served straight from GitHub's
   raw content URL (see "Subscribe" above), which is itself stable and
   auto-updating since the Action keeps it current.

Implemented in Python, running inside Docker for local development; CI runs
natively on the GitHub Actions runner (no Docker build needed there).

**Years covered:** current + next year, when published by the source. No
historical years, by design.

**Hosting model:** a static `.ics` file, regenerated on the 1st of every
month (and on manual trigger) by a GitHub Action, committed back to the
repo, and served from its raw.githubusercontent.com URL — no server to
run, no GitHub Pages setup needed, and holiday data changes rarely enough
that monthly regeneration is plenty fresh.

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
(e.g. Dia de les Illes Balears). It's tagged `scope: regional` as a whole
rather than guessing a split; Palma's own holidays are tagged `scope: local`.

## Future vision

Once Palma works end to end, generalize to:
- A data layer structured per country → region → city, instead of one hardcoded
  file.
- A subscription endpoint per city (e.g.
  `https://.../calendar/es/balearic-islands/palma.ics`).
- A simple picker UI to search/select a city and get its subscription URL.
