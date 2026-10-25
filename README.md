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

**Adding a city in an already-registered region** is just a
`registry/cities.json` change — add an entry with the municipality,
region, and source URL, and the next run picks it up. No code changes.

**Adding a new region** means writing that region's own source module
under `sources/`: every autonomous community publishes its own official
calendar in its own format, so there's no shared scraper to parameterize.
`sources/base.py` defines the `RegionSource` protocol any such module
must satisfy — a `SUPPORTED_LOCALES` set and a `fetch_holidays(year,
municipality, locale)` function returning holidays or `None` if that
year isn't published yet — and it doesn't need to be a class, just a
module shaped the same way. Then add one line to
`registry/region_sources.json` mapping the region's name to that
module's dotted import path — `load_region_sources()` imports each one
and checks it against `RegionSource`, so a misconfigured entry fails
loudly at startup instead of with a confusing error deep in the
pipeline.

Each region's own folder under `sources/` has its own README with the
quirks and tradeoffs specific to that source:
[`sources/illes_balears/README.md`](spanish_local_holidays_calendar/sources/illes_balears/README.md)
and
[`sources/catalunya/README.md`](spanish_local_holidays_calendar/sources/catalunya/README.md)
— worth reading both before writing a third, as two genuinely different
data points (one's an HTML scrape, the other's a JSON API).

## Project structure

```
spanish-local-holidays-calendar/
├── Dockerfile
├── Makefile
├── requirements.txt
├── spanish_local_holidays_calendar/
│   ├── models.py          # Holiday dataclass (date, name, scope, source_url)
│   ├── generate_ics.py    # builds a .ics Calendar from Holiday objects
│   ├── slug.py            # slugify() -- region/city display names to path segments
│   ├── __main__.py        # CLI entrypoint: dispatch cities x locales to their RegionSource
│   ├── registry/          # JSON-backed config: what to generate
│   │   ├── cities.py / cities.json              # CityConfig + load_cities()
│   │   ├── locales.py / locales.json            # LocaleConfig + load_locales()
│   │   └── region_sources.py / region_sources.json  # load_region_sources()
│   └── sources/           # how to get the data: the RegionSource protocol + each region's own implementation
│       ├── base.py            # RegionSource protocol
│       ├── illes_balears.py   # Balearics/CAIB source: HTML scrape
│       └── catalunya.py       # Catalonia source: Generalitat open data API
├── tests/                 # mirrors the package structure above
│   ├── registry/
│   │   ├── test_cities.py, test_locales.py, test_region_sources.py
│   ├── sources/
│   │   ├── fixtures/aao_2026_sample.html      # trimmed, stable copy of the real CA page structure
│   │   ├── fixtures/aao_2026_sample_es.html   # same, for the ES page
│   │   ├── test_base.py, test_illes_balears.py, test_catalunya.py
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
