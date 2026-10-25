# Spanish Local Holidays Calendar

A subscribable calendar feed (iCal/ICS) that bundles all the holidays that actually
affect you in Spain: **national**, **regional/autonomic**, and **local/municipal**,
for a given city.

## Implemented cities

| City | Region | Languages | Source of truth |
|------|--------|-----------|------------------|
| Palma | Balearic Islands | [ES](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/illes-balears/palma.es.ics) · [CA](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/illes-balears/palma.ca.ics) | [CAIB labor calendar](https://www.caib.es/sites/calendarilaboral/ca/aao_2026/) |
| Barcelona | Catalonia | [ES](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/catalunya/barcelona.es.ics) · [CA](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/catalunya/barcelona.ca.ics) | [Generalitat open data: regional](https://analisi.transparenciacatalunya.cat/Treball/Calendari-laboral-de-Catalunya/yf2b-mjr6) / [local](https://analisi.transparenciacatalunya.cat/Treball/Calendari-de-festes-locals-a-Catalunya/b4eh-r8up) |

## Subscribe

Each city is available in both Spanish and Catalan — pick the one you want.
URLs follow `output/<region-slug>/<city-slug>.<lang>.ics`:

| City | Language | URL |
|------|----------|-----|
| Palma | Español (ES) | `https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/illes-balears/palma.es.ics` |
| Palma | Català (CA) | `https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/illes-balears/palma.ca.ics` |
| Barcelona | Español (ES) | `https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/catalunya/barcelona.es.ics` |
| Barcelona | Català (CA) | `https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/catalunya/barcelona.ca.ics` |

Add the URL in your calendar app as a subscription (not a one-time import):
Google Calendar → "Other calendars" → "From URL"; Apple Calendar → File →
"New Calendar Subscription". The file is kept current by a scheduled GitHub
Action (see below), so your calendar app will pick up changes automatically.

The table above is maintained by hand; [`output/index.json`](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/index.json)
is the generated, always-current source of truth — every `(city, region,
locale)` combination that's actually live right now, each with its `path`
and full `url`. This is what scales past a hand-maintained table once
there are many cities: read the index, don't guess the filename.

## Why

Most holiday calendars only cover national public holidays. In countries with
decentralized holiday systems (e.g. Spain, where autonomous communities and
individual municipalities each add their own non-working days), there's no single
feed that reflects the *actual* days off for a specific city. This project aims to
fix that: pick your city once, subscribe to one calendar URL, and get every holiday
that applies to you — no manual merging of three different sources, no missing the
one local "fiesta" day your city adds on top of the national/regional ones.

## Non-goals

- No city picker or search UI — cities are added to the registry one at a
  time, not chosen by visitors.
- Not a general-purpose events calendar (concerts, festivals without an
  associated day off, etc.) — only actual holidays/non-working days.
- No UI beyond maybe a single static page with the subscription links and
  instructions — the deliverable is the feed itself.

## Shape

1. **Region source** — fetches and parses each region's own official source
   for the current and next year (when published), extracting both the
   general/regional holiday list and the city's local holidays. See
   "Implemented cities" above for each city's actual source, and "Adding a
   new region" below for how a region plugs in.
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
protocol any such module must satisfy — a `SUPPORTED_LOCALES` set and a
`fetch_holidays(year, municipality, locale)` function returning holidays
or `None` if that year isn't published yet — and doesn't need to be a
class, just a module shaped the same way. `region_sources.json` maps each
region name to its source module's dotted import path — `load_region_sources()`
imports each one and checks it against `RegionSource`, so a misconfigured
entry fails loudly at startup instead of with a confusing error deep in the
pipeline. Adding a city from an already-registered region is a `cities.json`
change; adding a city from a new region means writing that region's own
source module and adding one line to `region_sources.json`.

Catalonia's source (`catalonia_source.py`) is a different shape entirely
from the Balearics' HTML scrape — it's the Generalitat's official open data
portal, queried as JSON. It has no holiday *name* field at all: regional
holidays are named via a lookup of Catalonia's known fixed dates (the two
Easter-relative ones computed from Easter Sunday, since they move every
year), and local holidays are always given a generic translated name
("Festa local"/"Fiesta local") since the source's own "festiu" text field
turned out to contain leftover test/junk entries and isn't trustworthy as
a display name.

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
│   ├── region_source.py   # RegionSource protocol + load_region_sources()
│   ├── region_sources.json # data: region name -> source module's dotted import path
│   ├── scraper.py             # Balearics/CAIB source: HTML scrape
│   ├── catalonia_source.py    # Catalonia source: Generalitat open data API
│   ├── generate_ics.py    # builds a .ics Calendar from Holiday objects
│   ├── slug.py            # slugify() -- region/city display names to path segments
│   └── __main__.py        # CLI entrypoint: dispatch cities x locales to their RegionSource
├── tests/
│   ├── fixtures/aao_2026_sample.html      # trimmed, stable copy of the real CA page structure
│   ├── fixtures/aao_2026_sample_es.html   # same, for the ES page
│   ├── test_cities.py
│   ├── test_locales.py
│   ├── test_region_source.py
│   ├── test_scraper.py
│   ├── test_catalonia_source.py
│   ├── test_slug.py
│   ├── test_generate_ics.py
│   └── test_main.py
├── .github/workflows/update-calendar.yml   # scheduled regeneration + commit
└── output/                        # generated artifacts, committed (this is what's served)
    ├── index.json                  # generated: every live (city, region, locale) + its url
    ├── illes-balears/
    │   ├── palma.es.ics            # one file per (city, locale)
    │   └── palma.ca.ics
    └── catalunya/
        ├── barcelona.es.ics
        └── barcelona.ca.ics
```

**Build/run:**
```
make build      # docker build -t spanish-local-holidays-calendar .
make generate   # fetch every registered city's holidays, write output/<region-slug>/<city-slug>.<lang>.ics
make test       # run the test suite inside the container
```

**Balearics/CAIB-specific notes:** the scraper discovers every municipality
listed on the page as a single entry (no sub-localities) — covering 48 of
the Balearics' 67 municipalities, Palma among them — but not municipalities
split into several localities (e.g. Andratx / Port d'Andratx / s'Arracó),
which the parser doesn't disambiguate and intentionally excludes rather
than guess at. The source also doesn't
separate national from regional holidays — its "general Illes Balears" list
already folds Spain's national holidays (New Year, National Day, Christmas,
etc.) in with the Balearics' own additions (e.g. Dia de les Illes Balears).
It's tagged `scope: regional` as a whole rather than guessing a split;
Palma's own holidays are tagged `scope: local`.
