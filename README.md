# Spanish Local Holidays Calendar

A subscribable calendar feed (iCal/ICS) that bundles all the holidays that actually
affect you in Spain: **national**, **regional/autonomic**, and **local/municipal**,
for a given city.

## Subscribe

Browse available cities and languages, filter by city or autonomous
community, and subscribe directly: **[cbonnin96.github.io/spanish-local-holidays-calendar](https://cbonnin96.github.io/spanish-local-holidays-calendar/)**. Each language has a "Subscribe" link
(`webcal://`, opens your calendar app directly) and a plain `.ics` URL if
you'd rather add it manually — see that page for exact steps.

That page ([`docs/index.html`](docs/index.html)) is static with no build
step: it fetches [`output/index.json`](https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output/index.json)
client-side — the generated, always-current list of every `(city, region,
locale)` combination that's actually live, each with its `path` and full
`url` — so it can't drift from what's actually published. Read that JSON
directly if you want the data instead of the page.

## Why

Most holiday calendars only cover national public holidays. In countries with
decentralized holiday systems (e.g. Spain, where autonomous communities and
individual municipalities each add their own non-working days), there's no single
feed that reflects the *actual* days off for a specific city. This project aims to
fix that: pick your city once, subscribe to one calendar URL, and get every holiday
that applies to you — no manual merging of three different sources, no missing the
one local "fiesta" day your city adds on top of the national/regional ones.

## Shape

1. **Region source** — fetches and parses each region's own official source
   for the current and next year (when published), extracting both the
   general/regional holiday list and the city's local holidays. See the
   browsable index above for current coverage, and "How to add a new
   region or city" below for how a region plugs in.
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
run, and holiday data changes rarely enough that monthly regeneration is
plenty fresh. The optional GitHub Pages browsing page (see "Subscribe"
above) doesn't change this: it's a static client-side view of the same
committed files, not a second source of truth.

## How to add a new region or city

**Adding a city in an already-registered region** is just a `cities.json`
change — add an entry with the municipality, region, and source URL, and
the next run picks it up. No code changes.

**Adding a new region** means writing that region's own source module:
every autonomous community publishes its own official calendar in its own
format, so there's no shared scraper to parameterize. `region_source.py`
defines the `RegionSource` protocol any such module must satisfy — a
`SUPPORTED_LOCALES` set and a `fetch_holidays(year, municipality,
locale)` function returning holidays or `None` if that year isn't
published yet — and it doesn't need to be a class, just a module shaped
the same way. Then add one line to `region_sources.json` mapping the
region's name to that module's dotted import path —
`load_region_sources()` imports each one and checks it against
`RegionSource`, so a misconfigured entry fails loudly at startup instead
of with a confusing error deep in the pipeline.

Catalonia's source (`catalonia_source.py`) is a useful second data point
before writing a third: it's a different shape entirely from the
Balearics' HTML scrape (`scraper.py`) — the Generalitat's official open
data portal, queried as JSON. It has no holiday *name* field at all:
regional holidays are named via a lookup of Catalonia's known fixed dates
(the two Easter-relative ones computed from Easter Sunday, since they
move every year), and local holidays are always given a generic
translated name ("Festa local"/"Fiesta local") since the source's own
"festiu" text field turned out to contain leftover test/junk entries and
isn't trustworthy as a display name.

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
├── docs/
│   └── index.html              # browsable index, published via GitHub Pages
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
listed on the page as a single entry (no sub-localities) — 48 of the
Balearics' 67 municipalities, Palma among them — plus the individual
sub-localities of municipalities split into several of them (e.g. Andratx /
Port d'Andratx / s'Arracó), fetchable by sub-locality name just like any
other municipality. CAIB consistently lines up a split municipality's data
cell as one shared holiday followed by one sub-locality-specific holiday,
repeated per sub-locality in the same order as the heading names — but
where a row doesn't fit that shape (Sant Josep de sa Talaia groups several
place names under each heading entry instead of listing them one-by-one),
the pairing would be a guess, so it's skipped rather than risking a
misattributed holiday. The source also doesn't
separate national from regional holidays — its "general Illes Balears" list
already folds Spain's national holidays (New Year, National Day, Christmas,
etc.) in with the Balearics' own additions (e.g. Dia de les Illes Balears).
It's tagged `scope: regional` as a whole rather than guessing a split;
Palma's own holidays are tagged `scope: local`.
