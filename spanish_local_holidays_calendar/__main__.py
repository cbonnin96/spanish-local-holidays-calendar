from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from .generate_ics import build_calendar
from .scraper import fetch_holidays

MUNICIPALITY = "PALMA"
LOCALES = ("es", "ca")
CALENDAR_NAMES = {
    "es": "Fiestas de Palma",
    "ca": "Festes de Palma",
}
OUTPUT_DIR = Path("output")


def generate_for_locale(locale: str) -> int:
    """Generate the .ics file for one locale. Returns the number of holidays written."""
    current_year = date.today().year
    all_holidays = []
    found_any = False

    for year in (current_year, current_year + 1):
        holidays = fetch_holidays(year, MUNICIPALITY, locale=locale)
        if holidays is None:
            print(f"[skip] {locale}/{year} calendar not published yet", file=sys.stderr)
            continue
        print(f"[ok] {locale}/{year}: {len(holidays)} holidays", file=sys.stderr)
        all_holidays.extend(holidays)
        found_any = True

    if not found_any:
        print(f"No holiday data could be fetched for locale {locale}.", file=sys.stderr)
        return 0

    calendar_name = CALENDAR_NAMES.get(locale, f"{MUNICIPALITY.title()} Holidays")
    calendar = build_calendar(all_holidays, calendar_name=calendar_name)
    output_path = OUTPUT_DIR / f"{MUNICIPALITY.lower()}.{locale}.ics"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(calendar.to_ical())
    print(f"Wrote {output_path} ({len(all_holidays)} holidays)", file=sys.stderr)
    return len(all_holidays)


def main() -> int:
    total_holidays = sum(generate_for_locale(locale) for locale in LOCALES)

    if total_holidays == 0:
        print("No holiday data could be fetched for any locale/year.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
