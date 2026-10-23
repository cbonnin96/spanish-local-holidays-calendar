from __future__ import annotations

from datetime import date

import requests
from dateutil.easter import easter

from .models import Holiday

SUPPORTED_LOCALES = frozenset({"es", "ca"})

REGIONAL_DATASET_URL = "https://analisi.transparenciacatalunya.cat/resource/yf2b-mjr6.json"
LOCAL_DATASET_URL = "https://analisi.transparenciacatalunya.cat/resource/b4eh-r8up.json"

# Catalonia's official open-data portal gives dates but no holiday names (the
# regional dataset has no name field at all; the local dataset's "festiu"
# field is generic and, on inspection, full of leftover test/junk entries --
# neither is trustworthy as a display name). So:
#
# - Regional holidays: Catalonia's 12 fixed-date occasions (Ordre EMT/66/2025
#   and its yearly equivalents) are named via this lookup by (month, day);
#   the two Easter-relative ones are matched by computing Easter Sunday for
#   the year rather than a fixed date, since they move every year.
# - Local holidays: always given a generic translated name (we don't trust
#   the source's "festiu" text), since there's no reliable per-town name.
FIXED_REGIONAL_NAMES = {
    "ca": {
        (1, 1): "Cap d'Any",
        (1, 6): "Reis",
        (5, 1): "Festa del Treball",
        (6, 24): "Sant Joan",
        (8, 15): "L'Assumpció",
        (9, 11): "Diada Nacional de Catalunya",
        (10, 12): "Festa Nacional d'Espanya",
        (12, 8): "La Immaculada",
        (12, 25): "Nadal",
        (12, 26): "Sant Esteve",
    },
    "es": {
        (1, 1): "Año Nuevo",
        (1, 6): "Reyes",
        (5, 1): "Fiesta del Trabajo",
        (6, 24): "San Juan",
        (8, 15): "La Asunción",
        (9, 11): "Fiesta Nacional de Catalunya",
        (10, 12): "Fiesta Nacional de España",
        (12, 8): "La Inmaculada",
        (12, 25): "Navidad",
        (12, 26): "San Esteban",
    },
}

# Keyed by offset (days) from Easter Sunday.
EASTER_RELATIVE_NAMES = {
    "ca": {-2: "Divendres Sant", 1: "Dilluns de Pasqua"},
    "es": {-2: "Viernes Santo", 1: "Lunes de Pascua"},
}

GENERIC_REGIONAL_NAME = {"ca": "Festa general", "es": "Fiesta general"}
GENERIC_LOCAL_NAME = {"ca": "Festa local", "es": "Fiesta local"}


def _regional_holiday_name(holiday_date: date, locale: str) -> str:
    fixed = FIXED_REGIONAL_NAMES[locale].get((holiday_date.month, holiday_date.day))
    if fixed:
        return fixed
    offset = (holiday_date - easter(holiday_date.year)).days
    movable = EASTER_RELATIVE_NAMES[locale].get(offset)
    if movable:
        return movable
    return GENERIC_REGIONAL_NAME[locale]


def _fetch_rows(url: str, where: str) -> list[dict]:
    response = requests.get(url, params={"$where": where}, timeout=30)
    response.raise_for_status()
    return response.json()


def _distinct_dates(rows: list[dict]) -> list[date]:
    return sorted({date.fromisoformat(row["data"][:10]) for row in rows})


def fetch_holidays(year: int, municipality: str = "Barcelona", locale: str = "ca") -> list[Holiday] | None:
    """Fetch and parse all holidays (regional + local) for a Catalan
    municipality, year, and locale ("ca" or "es"), from Catalonia's official
    open data portal (analisi.transparenciacatalunya.cat).

    Returns None if that year isn't published in the regional dataset yet.
    """
    regional_rows = _fetch_rows(REGIONAL_DATASET_URL, f"any_calendari='{year}'")
    regional_dates = _distinct_dates(regional_rows)
    if not regional_dates:
        return None

    local_rows = _fetch_rows(
        LOCAL_DATASET_URL,
        f"any_calendari='{year}' AND ajuntament_o_nucli_municipal='{municipality}'",
    )
    local_dates = _distinct_dates(local_rows)

    holidays = [
        Holiday(date=d, name=_regional_holiday_name(d, locale), scope="regional", source_url=REGIONAL_DATASET_URL)
        for d in regional_dates
    ]
    holidays += [
        Holiday(date=d, name=GENERIC_LOCAL_NAME[locale], scope="local", source_url=LOCAL_DATASET_URL)
        for d in local_dates
    ]
    return sorted(holidays, key=lambda holiday: holiday.date)
