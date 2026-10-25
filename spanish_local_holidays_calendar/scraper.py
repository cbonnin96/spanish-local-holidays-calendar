from __future__ import annotations

import re
import sys
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
    d'Andratx / s'Arracó) are excluded here; see `parse_split_local_holidays`
    for those.
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


def _sub_locality_names(heading_cell, strong) -> list[str]:
    """The sub-locality names listed in a split heading cell, in document
    order, excluding the `<p>` that holds the municipality's own `<strong>`
    name and any blank `&nbsp;` spacer lines."""
    name_paragraph = strong.find_parent("p")
    names = []
    for paragraph in heading_cell.find_all("p"):
        if paragraph is name_paragraph:
            continue
        text = paragraph.get_text(strip=True)
        if text:
            names.append(text)
    return names


def parse_split_local_holidays(html: str, year: int, source_url: str) -> dict[str, list[Holiday]]:
    """Parse the local-holidays table's split/sub-locality municipalities
    (e.g. Andratx / Port d'Andratx / s'Arracó), returning each sub-locality's
    holidays keyed by sub-locality name (as published, upper-case).

    CAIB lists a split municipality's sub-localities as a sequence of names
    in the heading cell, and lines up the data cell as one blank spacer line
    followed by exactly two holiday lines per sub-locality, in the same
    order as the heading names (the two lines are often one holiday shared
    by the whole municipality plus one specific to that sub-locality). Where
    a row doesn't fit that shape -- e.g. Sant Josep de sa Talaia groups
    several place names into each heading entry instead of listing them
    one-by-one -- the pairing is ambiguous, and that sub-locality is skipped
    rather than guessed at, consistent with this project's preference for
    not fabricating data it isn't confident about.
    """
    soup = BeautifulSoup(html, "lxml")
    holidays_by_sub_locality: dict[str, list[Holiday]] = {}
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        heading_cell, data_cell = cells
        strong = heading_cell.find("strong")
        if not strong or _is_single_entry_heading(heading_cell, strong):
            continue
        sub_localities = _sub_locality_names(heading_cell, strong)
        data_lines = [paragraph.get_text(strip=True) for paragraph in data_cell.find_all("p")]
        if not data_lines or data_lines[0] != "" or len(data_lines) - 1 != 2 * len(sub_localities):
            print(
                f"[skip] {strong.get_text(strip=True)}: sub-locality holidays don't line up "
                "cleanly, not disambiguated",
                file=sys.stderr,
            )
            continue
        rest = data_lines[1:]
        for index, sub_locality in enumerate(sub_localities):
            holidays: list[Holiday] = []
            for text in rest[2 * index : 2 * index + 2]:
                holiday_date = _parse_date(text, year)
                if holiday_date is None:
                    continue
                name = text.split(":", 1)[1].strip() if ":" in text else sub_locality.title()
                holidays.append(Holiday(date=holiday_date, name=name, scope="local", source_url=source_url))
            if holidays:
                holidays_by_sub_locality[sub_locality.upper()] = holidays
    return holidays_by_sub_locality


def fetch_holidays(year: int, municipality: str = "PALMA", locale: str = "ca") -> list[Holiday] | None:
    """Fetch and parse all holidays (regional + local) for a municipality,
    year, and locale ("ca" or "es"). `municipality` can be a single-entry
    municipality's name or a split municipality's sub-locality name (e.g.
    "Port d'Andratx") -- both are resolved the same way.

    Returns None if the calendar for that year hasn't been published yet.
    """
    html = fetch_page(year, locale)
    if html is None:
        return None
    source_url = BASE_URL.format(locale=locale, year=year)
    holidays = parse_regional_holidays(html, year, source_url)
    target = municipality.strip().upper()
    local_holidays = parse_local_holidays(html, year, source_url)
    if target in local_holidays:
        holidays += local_holidays[target]
    else:
        holidays += parse_split_local_holidays(html, year, source_url).get(target, [])
    return sorted(holidays, key=lambda holiday: holiday.date)
