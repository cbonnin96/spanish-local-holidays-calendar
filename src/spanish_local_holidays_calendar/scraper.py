from __future__ import annotations

import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from .models import Holiday

BASE_URL = "https://www.caib.es/sites/calendarilaboral/ca/aao_{year}/"

# Catalan month names, as used by the CAIB page. "de" elides to "d'" before a
# vowel-initial month (e.g. "2 d'abril"); normalized away before matching.
MONTHS = {
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


def fetch_page(year: int) -> str | None:
    """Return the raw HTML for a given year's calendar, or None if not published yet."""
    url = BASE_URL.format(year=year)
    response = requests.get(url, timeout=30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.text


def parse_regional_holidays(html: str, year: int, source_url: str) -> list[Holiday]:
    """Parse the "Festes d'àmbit general de les Illes Balears" table.

    This list is published by CAIB as a single table that already folds in
    Spain's national holidays (e.g. Festa Nacional, Nadal) alongside the
    Balearics' own regional additions (e.g. Dia de les Illes Balears) -- the
    source does not separate the two, so both are tagged scope="regional".
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


def parse_local_holidays(html: str, year: int, municipality: str, source_url: str) -> list[Holiday]:
    """Parse the local-holidays table for a single municipality.

    Only handles municipalities listed as a single entry (no sub-localities),
    which covers Palma. Municipalities split into several localities (e.g.
    Andratx / Port d'Andratx / s'Arracó) are not disambiguated by this parser.
    """
    soup = BeautifulSoup(html, "lxml")
    target = municipality.strip().upper()
    holidays: list[Holiday] = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 2:
            continue
        heading_cell, data_cell = cells
        strong = heading_cell.find("strong")
        if not strong or strong.get_text(strip=True).upper() != target:
            continue
        for paragraph in data_cell.find_all("p"):
            text = paragraph.get_text(strip=True)
            if not text:
                continue
            holiday_date = _parse_date(text, year)
            if holiday_date is None:
                continue
            name = text.split(":", 1)[1].strip() if ":" in text else municipality.title()
            holidays.append(Holiday(date=holiday_date, name=name, scope="local", source_url=source_url))
        break
    return holidays


def fetch_holidays(year: int, municipality: str = "PALMA") -> list[Holiday] | None:
    """Fetch and parse all holidays (regional + local) for a municipality and year.

    Returns None if the calendar for that year hasn't been published yet.
    """
    html = fetch_page(year)
    if html is None:
        return None
    source_url = BASE_URL.format(year=year)
    holidays = parse_regional_holidays(html, year, source_url)
    holidays += parse_local_holidays(html, year, municipality, source_url)
    return sorted(holidays, key=lambda holiday: holiday.date)
