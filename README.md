# Local Holidays Calendar

A subscribable calendar feed (iCal/ICS) that bundles all the holidays that actually
affect you: **national**, **regional/autonomic**, and **local/municipal**, for a
given city.

**MVP scope: Palma (Palma de Mallorca, Balearic Islands, Spain) only.** The
long-term vision below (multi-city, multi-country) is the north star, but the
first working version targets a single city end to end — one hardcoded feed
combining Spain's national holidays, the Balearic Islands' regional holidays,
and Palma's local holidays — before generalizing to a city picker.

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
- **Simple enough to ship fast.** Data can start as a hardcoded list (e.g. a
  JSON/YAML file) rather than a database — the point of the MVP is a working,
  subscribable feed, not a scalable data model yet.

## Non-goals (for the MVP)

- No city picker, no other cities, no multi-country data model yet — Palma is
  hardcoded. Generalizing comes after the MVP proves useful.
- Not a general-purpose events calendar (concerts, festivals without an
  associated day off, etc.) — only actual holidays/non-working days.
- No UI beyond maybe a single static page with the subscription link and
  instructions — the deliverable is the feed itself.

## MVP shape

1. **Data file** — a small structured file (JSON/YAML) listing Palma's holidays
   for the current and next year: date, name, scope (national/regional/local),
   source.
2. **Feed generator** — a script that reads the data file and produces a valid
   `.ics` file.
3. **Hosting** — the `.ics` file served at a stable, static URL that calendar
   apps can subscribe to and poll for updates.

## Future vision (post-MVP)

Once Palma works end to end, generalize to:
- A data layer structured per country → region → city, instead of one hardcoded
  file.
- A subscription endpoint per city (e.g.
  `https://.../calendar/es/balearic-islands/palma.ics`).
- A simple picker UI to search/select a city and get its subscription URL.

## Decisions

- **Data source:** the Balearic Islands government's official labor calendar
  site, https://www.caib.es/sites/calendarilaboral/es/aao_2026/ — covers
  national, regional, and local (per-municipality) holidays for the Balearics,
  including Palma. Published year by year (new year's page appears when
  available).
- **Years covered:** current + next year, when published. No historical years
  for the MVP.
- **Hosting model:** static `.ics` file, regenerated periodically (e.g. a
  scheduled GitHub Action) rather than a dynamic endpoint — simpler to host
  (e.g. GitHub Pages), no server to run, and holiday data changes rarely
  enough that periodic regeneration (weekly, or on a manual trigger) is
  plenty fresh.
