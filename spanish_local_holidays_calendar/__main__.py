from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from .cities import CityConfig, load_cities
from .generate_ics import build_calendar
from .locales import LocaleConfig, load_locales
from .region_source import RegionSource, load_region_sources
from .slug import slugify

OUTPUT_DIR = Path("output")
RAW_BASE_URL = "https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output"


def generate_for_city_locale(
    city: CityConfig, locale: str, locales: dict[str, LocaleConfig], source: RegionSource
) -> tuple[int, Path | None]:
    """Generate the .ics file for one city and locale. Returns the number of
    holidays written, and the output path if a file was actually written
    (None if nothing was available for this city/locale)."""
    current_year = date.today().year
    all_holidays = []
    found_any = False

    for year in (current_year, current_year + 1):
        holidays = source.fetch_holidays(year, city.municipality, locale=locale)
        if holidays is None:
            print(f"[skip] {city.municipality}/{locale}/{year} calendar not published yet", file=sys.stderr)
            continue
        print(f"[ok] {city.municipality}/{locale}/{year}: {len(holidays)} holidays", file=sys.stderr)
        all_holidays.extend(holidays)
        found_any = True

    if not found_any:
        print(f"No holiday data could be fetched for {city.municipality}/{locale}.", file=sys.stderr)
        return 0, None

    locale_config = locales.get(locale)
    name_template = locale_config.calendar_name_template if locale_config else "{city} Holidays"
    calendar_name = name_template.format(city=city.municipality.title())
    calendar = build_calendar(all_holidays, calendar_name=calendar_name)
    output_path = OUTPUT_DIR / slugify(city.region) / f"{slugify(city.municipality)}.{locale}.ics"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(calendar.to_ical())
    print(f"Wrote {output_path} ({len(all_holidays)} holidays)", file=sys.stderr)
    return len(all_holidays), output_path


def write_index(entries: list[dict[str, str]]) -> None:
    """Write output/index.json listing every (city, locale) combination that
    actually produced a file, so it always reflects exactly what's currently
    available -- not every configured city/locale, just the live ones."""
    ordered = sorted(entries, key=lambda entry: (entry["region"], entry["city"], entry["locale"]))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.json").write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    cities = load_cities()
    locales = load_locales()
    region_sources = load_region_sources()

    city_sources: list[RegionSource] = []
    for city in cities:
        source = region_sources.get(city.region)
        if source is None:
            print(f"No source registered for region {city.region!r} (city {city.municipality}).", file=sys.stderr)
            return 1
        unsupported = set(locales) - source.SUPPORTED_LOCALES
        if unsupported:
            print(
                f"locales.json declares locale(s) the {city.region} source doesn't support yet: "
                f"{sorted(unsupported)}. That source supports: {sorted(source.SUPPORTED_LOCALES)}.",
                file=sys.stderr,
            )
            return 1
        city_sources.append(source)

    total_holidays = 0
    index_entries: list[dict[str, str]] = []
    for city, source in zip(cities, city_sources):
        for locale in locales:
            holiday_count, output_path = generate_for_city_locale(city, locale, locales, source)
            total_holidays += holiday_count
            if output_path is not None:
                relative_path = output_path.relative_to(OUTPUT_DIR).as_posix()
                index_entries.append(
                    {
                        "city": city.municipality,
                        "region": city.region,
                        "locale": locale,
                        "path": relative_path,
                        "url": f"{RAW_BASE_URL}/{relative_path}",
                    }
                )

    write_index(index_entries)

    if total_holidays == 0:
        print("No holiday data could be fetched for any city/locale/year.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
