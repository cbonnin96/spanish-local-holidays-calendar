# Spanish Local Holidays Calendar

A subscribable calendar feed (iCal/ICS) that bundles all the holidays that actually
affect you in Spain: **national**, **regional/autonomic**, and **local/municipal**,
for a given city.

## Implemented cities

| City | Region | Languages | Source of truth |
|------|--------|-----------|------------------|
| Palma | Balearic Islands | [ES](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/palma.es.ics) · [CA](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/palma.ca.ics) | [CAIB labor calendar](https://www.caib.es/sites/calendarilaboral/ca/aao_2026/) |

## Subscribe

Each city is available in both Spanish and Catalan — pick the one you want:

| Language | URL |
|----------|-----|
| Español (ES) | `https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/palma.es.ics` |
| Català (CA) | `https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/palma.ca.ics` |

Add the URL in your calendar app as a subscription (not a one-time import):
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
   monthly (and on demand), committing the generated `.ics` files back to the
   repo only when they actually changed. No manual execution needed, on your
   machine or otherwise.
4. **Hosting** — the committed `.ics` files are served straight from GitHub's
   raw content URL (see "Subscribe" above), which is itself stable and
   auto-updating since the Action keeps it current.

Implemented in Python, running inside Docker for local development; CI runs
natively on the GitHub Actions runner (no Docker build needed there).

**Years covered:** current + next year, when published by the source. No
historical years, by design.

**Hosting model:** static `.ics` files, regenerated on the 1st of every
month (and on manual trigger) by a GitHub Action, committed back to the
repo, and served from their raw.githubusercontent.com URLs — no server to
run, no GitHub Pages setup needed, and holiday data changes rarely enough
that monthly regeneration is plenty fresh.

**Adding a new region:** every autonomous community publishes its own
official calendar in its own format, so a new region means a new source
module, not a config tweak. `region_source.py` defines the `RegionSource`
protocol that any such module must satisfy — a `SUPPORTED_LOCALES` set and
a `fetch_holidays(year, municipality, locale)` function returning holidays
or `None` if that year isn't published yet. `scraper.py` (the Balearics/
CAIB source) is a plain module that already satisfies this protocol as-is;
a second region's source doesn't need to be a class, just another module
shaped the same way.

## Project structure

```
spanish-local-holidays-calendar/
├── Dockerfile
├── Makefile
├── requirements.txt
├── spanish_local_holidays_calendar/
│   ├── models.py          # Holiday dataclass (date, name, scope, source_url)
│   ├── cities.py          # CityConfig + load_cities() -- the city registry
│   ├── cities.json        # data: which municipalities to generate calendars for
│   ├── locales.py         # LocaleConfig + load_locales() -- per-locale display strings
│   ├── locales.json       # data: supported locales and their calendar name templates
│   ├── region_source.py   # RegionSource protocol -- the extension point for a new region
│   ├── scraper.py         # fetches + parses the CAIB (Balearics) page into Holiday objects
│   ├── generate_ics.py    # builds a .ics Calendar from Holiday objects
│   └── __main__.py        # CLI entrypoint: loop cities x locales, write per-(city,locale) .ics files
├── tests/
│   ├── fixtures/aao_2026_sample.html      # trimmed, stable copy of the real CA page structure
│   ├── fixtures/aao_2026_sample_es.html   # same, for the ES page
│   ├── test_cities.py
│   ├── test_locales.py
│   ├── test_region_source.py
│   ├── test_scraper.py
│   ├── test_generate_ics.py
│   └── test_main.py
├── .github/workflows/update-calendar.yml   # scheduled regeneration + commit
├── output/palma.es.ics    # generated artifact, committed (this is what's served)
└── output/palma.ca.ics    # generated artifact, committed (this is what's served)
```

**Build/run:**
```
make build      # docker build -t spanish-local-holidays-calendar .
make generate   # scrape live CAIB page, write output/palma.es.ics and output/palma.ca.ics
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
