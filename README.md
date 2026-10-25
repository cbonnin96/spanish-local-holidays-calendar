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

1. **Region source** — fetches current + next year's regional and local
   holidays (when published) from each region's own official source. See
   "How to add a new region or city" below.
2. **Feed generator** — turns those holidays into a valid `.ics` file.
3. **Automation** — a monthly GitHub Action re-runs steps 1–2 and commits
   the result, only when it actually changed.
4. **Hosting** — the committed `.ics` files are served directly from
   GitHub's raw content URLs. No server to run.

Python, Dockerized for local dev; CI runs natively on the GitHub Actions
runner. No historical years — only what each source currently publishes.
The GitHub Pages page (see "Subscribe" above) is just a static client-side
view over these same committed files, not a second source of truth.

## How to add a new region or city

**New city, existing region:** add an entry to `registry/cities.json`. No code changes.

**New region:**
1. Write a module under `sources/` satisfying the `RegionSource` protocol
   (`sources/base.py`): a `SUPPORTED_LOCALES` set and a
   `fetch_holidays(year, municipality, locale)` function. A plain module
   works fine, no class needed.
2. Register it in `registry/region_sources.json`: `"<region>": "<dotted.module.path>"`.
3. Check an existing region's README first —
   [`illes_balears`](spanish_local_holidays_calendar/sources/illes_balears/README.md) (HTML scrape) or
   [`catalunya`](spanish_local_holidays_calendar/sources/catalunya/README.md) (JSON API) — since
   each source has its own quirks worth knowing before writing a third.

## Project structure

```
spanish-local-holidays-calendar/
├── spanish_local_holidays_calendar/
│   ├── models.py, generate_ics.py, slug.py, pipeline.py, __main__.py
│   ├── registry/        # JSON-backed config: what to generate (cities, locales, region_sources)
│   └── sources/         # how to get the data: the RegionSource protocol + one implementation per region
│       ├── base.py
│       ├── illes_balears/   # Balearics/CAIB source: HTML scrape (+ its own README)
│       └── catalunya/       # Catalonia source: Generalitat open-data API (+ its own README)
├── tests/                  # mirrors the package structure above
├── docs/index.html         # browsable subscribe page, published via GitHub Pages
├── output/                 # generated artifacts, committed -- this is what's served
│   ├── index.json            # every live (city, region, locale) + its url
│   └── <region-slug>/<city-slug>.<lang>.ics
└── .github/workflows/update-calendar.yml   # scheduled regeneration + commit
```

**Build/run:**
```
make build      # docker build -t spanish-local-holidays-calendar .
make generate   # fetch every registered city's holidays, write output/<region-slug>/<city-slug>.<lang>.ics
make test       # run the test suite inside the container
```
