from __future__ import annotations

import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from .models import Holiday

BASE_URL = "https://www.caib.es/sites/calendarilaboral/{locale}/aao_{year}/"

# Locale codes this scraper actually knows how to fetch and parse: CAIB
# publishes a page at this URL pattern for each, and MONTHS below covers
# both vocabularies. Update together with MONTHS when adding a new locale.
SUPPORTED_LOCALES = frozenset({"es", "ca"})

# Catalan and Spanish month names, as used by the CAIB page in each locale.
# Catalan "de" elides to "d'" before a vowel-initial month (e.g. "2 d'abril");
# normalized away before matching. Spanish has no such elision. Where a word
# is spelled identically in both languages (e.g. "abril", "octubre"), it maps
# to the same month, so one shared dict covers both locales.
MONTHS = {
    # Catalan
    "gener": 1,
    "febrer": 2,
    "marc": 3,
    "març": 3,
    "abril": 4,
    "maig": 5,
    "juny": 6,
    "juliol": 7,
    "agost": 8,
    "setembre": 9,
    "octubre": 10,
    "novembre": 11,
    "desembre": 12,
    # Spanish
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "noviembre": 11,
    "diciembre": 12,
}

DATE_RE = re.compile(r"(\d{1,2})\s+de\s+(\w+)", re.IGNORECASE)


def _parse_date(text: str, year: int) -> date | None:
    normalized = text.replace("d'", "de ")
    match = DATE_RE.search(normalized)
    if not match:
        return None
    month = MONTHS.get(match.group(2).lower())
    if month is None:
        return None
    return date(year, month, int(match.group(1)))


def fetch_page(year: int, locale: str = "ca") -> str | None:
    """Return the raw HTML for a given year's calendar and locale, or None if
    not published yet. `locale` is "ca" (Catalan) or "es" (Spanish)."""
    url = BASE_URL.format(locale=locale, year=year)
    response = requests.get(url, timeout=30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.text


def parse_regional_holidays(html: str, year: int, source_url: str) -> list[Holiday]:
    """Parse the "general Illes Balears" holidays table (either locale: CA
    "Festes d'àmbit general..." or ES "Fiestas de ámbito general...").

    This list is published by CAIB as a single table that already folds in
    Spain's national holidays (e.g. Festa Nacional/Fiesta Nacional, Nadal/
    Navidad) alongside the Balearics' own regional additions (e.g. Dia de
    les Illes Balears) -- the source does not separate the two, so both are
    tagged scope="regional".
    """
    soup = BeautifulSoup(html, "lxml")
    heading = soup.find(string=re.compile(r"mbit\w*\s+general", re.IGNORECASE))
    table = heading.find_next("table") if heading else None
    holidays: list[Holiday] = []
    if table is None:
        return holidays
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        holiday_date = _parse_date(cells[0].get_text(), year)
        name = cells[1].get_text(strip=True)
        if holiday_date and name:
            holidays.append(Holiday(date=holiday_date, name=name, scope="regional", source_url=source_url))
    return holidays


def _is_single_entry_heading(heading_cell, strong) -> bool:
    """Whether a local-holidays heading cell names one municipality with no
    sub-localities.

    A single-entry cell is just `<strong>NAME</strong>` (CAIB formats this
    inconsistently -- sometimes wrapped in a `<p>`, sometimes followed by
    bare `<br>`s -- but either way there's no other text). A split cell
    (e.g. Andratx / Port d'Andratx / s'Arracó) lists each sub-locality as
    its own line alongside the `<strong>` name, which this detects by
    checking for any text in the cell outside the `<strong>` tag itself
    (ignoring `&nbsp;` spacer text).
    """
    extra_text = "".join(
        str(node) for node in heading_cell.find_all(string=True) if node.find_parent("strong") is not strong
    )
    return extra_text.replace("\xa0", "").strip() == ""


def parse_local_holidays(html: str, year: int, source_url: str) -> dict[str, list[Holiday]]:
    """Parse the local-holidays table, returning every single-entry
    municipality's holidays keyed by municipality name (as published,
    upper-case).

    Only municipalities listed as a single entry (no sub-localities) are
    included -- this covers the large majority of Balearic municipalities.
    Municipalities split into several localities (e.g. Andratx / Port
    d'Andratx / s'Arracó) are intentionally excluded rather than
    disambiguated; see https://github.com/cbonnin96/spanish-local-holidays-calendar/issues/12.
    """
    soup = BeautifulSoup(html, "lxml")
    holidays_by_municipality: dict[str, list[Holiday]] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        heading_cell, data_cell = cells
        strong = heading_cell.find("strong")
        if not strong or not _is_single_entry_heading(heading_cell, strong):
            continue
        municipality = strong.get_text(strip=True).upper()
        holidays: list[Holiday] = []
        # One holiday per line, but CAIB doesn't consistently wrap each in
        # its own <p> -- sometimes a second line is bare text after a <br>
        # (e.g. Sineu's "dia previ" entry) -- so split on text-node
        # boundaries rather than just iterating <p> tags.
        for line in data_cell.get_text(separator="\n").split("\n"):
            text = line.strip()
            if not text:
                continue
            holiday_date = _parse_date(text, year)
            if holiday_date is None:
                continue
            name = text.split(":", 1)[1].strip() if ":" in text else municipality.title()
            holidays.append(Holiday(date=holiday_date, name=name, scope="local", source_url=source_url))
        if holidays:
            holidays_by_municipality[municipality] = holidays
    return holidays_by_municipality


def fetch_holidays(year: int, municipality: str = "PALMA", locale: str = "ca") -> list[Holiday] | None:
    """Fetch and parse all holidays (regional + local) for a municipality,
    year, and locale ("ca" or "es").

    Returns None if the calendar for that year hasn't been published yet.
    """
    html = fetch_page(year, locale)
    if html is None:
        return None
    source_url = BASE_URL.format(locale=locale, year=year)
    holidays = parse_regional_holidays(html, year, source_url)
    local_holidays = parse_local_holidays(html, year, source_url)
    holidays += local_holidays.get(municipality.strip().upper(), [])
    return sorted(holidays, key=lambda holiday: holiday.date)
