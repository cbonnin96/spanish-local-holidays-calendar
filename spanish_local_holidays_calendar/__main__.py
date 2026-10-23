from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from .cities import CityConfig, load_cities
from .generate_ics import build_calendar
from .locales import LocaleConfig, load_locales
from .scraper import fetch_holidays

OUTPUT_DIR = Path("output")


def generate_for_city_locale(city: CityConfig, locale: str, locales: dict[str, LocaleConfig]) -> int:
    """Generate the .ics file for one city and locale. Returns the number of holidays written."""
    current_year = date.today().year
    all_holidays = []
    found_any = False

    for year in (current_year, current_year + 1):
        holidays = fetch_holidays(year, city.municipality, locale=locale)
        if holidays is None:
            print(f"[skip] {city.municipality}/{locale}/{year} calendar not published yet", file=sys.stderr)
            continue
        print(f"[ok] {city.municipality}/{locale}/{year}: {len(holidays)} holidays", file=sys.stderr)
        all_holidays.extend(holidays)
        found_any = True

    if not found_any:
        print(f"No holiday data could be fetched for {city.municipality}/{locale}.", file=sys.stderr)
        return 0

    locale_config = locales.get(locale)
    name_template = locale_config.calendar_name_template if locale_config else "{city} Holidays"
    calendar_name = name_template.format(city=city.municipality.title())
    calendar = build_calendar(all_holidays, calendar_name=calendar_name)
    output_path = OUTPUT_DIR / f"{city.municipality.lower()}.{locale}.ics"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(calendar.to_ical())
    print(f"Wrote {output_path} ({len(all_holidays)} holidays)", file=sys.stderr)
    return len(all_holidays)


def main() -> int:
    cities = load_cities()
    locales = load_locales()
    total_holidays = sum(
        generate_for_city_locale(city, locale, locales) for city in cities for locale in locales
    )

    if total_holidays == 0:
        print("No holiday data could be fetched for any city/locale/year.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
