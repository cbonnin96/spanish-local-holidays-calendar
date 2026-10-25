from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .generate_ics import build_calendar
from .registry.cities import CityConfig
from .registry.locales import LocaleConfig
from .slug import slugify
from .sources.base import RegionSource, SourceUnavailableError


@dataclass
class CalendarPipeline:
    """Validates the registries against each other, generates every
    (city, locale)'s `.ics` file, and writes the index of what it actually
    produced. Constructed with its dependencies explicitly rather than
    reading them off module globals, so tests can hand it exactly the
    registries/output directory they want without monkeypatching."""

    cities: list[CityConfig]
    locales: dict[str, LocaleConfig]
    region_sources: dict[str, RegionSource]
    output_dir: Path
    raw_base_url: str

    def validate_sources(self) -> list[RegionSource] | None:
        """Return each city's RegionSource, in `self.cities` order, or None
        (having already printed why to stderr) if a city's region has no
        registered source, or that source doesn't support a locale
        `self.locales` configures."""
        city_sources: list[RegionSource] = []
        for city in self.cities:
            source = self.region_sources.get(city.region)
            if source is None:
                print(f"No source registered for region {city.region!r} (city {city.municipality}).", file=sys.stderr)
                return None
            unsupported = set(self.locales) - source.SUPPORTED_LOCALES
            if unsupported:
                print(
                    f"locales.json declares locale(s) the {city.region} source doesn't support yet: "
                    f"{sorted(unsupported)}. That source supports: {sorted(source.SUPPORTED_LOCALES)}.",
                    file=sys.stderr,
                )
                return None
            city_sources.append(source)
        return city_sources

    def generate_for_city_locale(
        self, city: CityConfig, locale: str, source: RegionSource
    ) -> tuple[int, Path | None]:
        """Generate the .ics file for one city and locale. Returns the number
        of holidays written, and the output path if a file was actually
        written (None if nothing was available for this city/locale)."""
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

        locale_config = self.locales.get(locale)
        name_template = locale_config.calendar_name_template if locale_config else "{city} Holidays"
        calendar_name = name_template.format(city=city.municipality.title())
        calendar = build_calendar(all_holidays, calendar_name=calendar_name)
        output_path = self.output_dir / slugify(city.region) / f"{slugify(city.municipality)}.{locale}.ics"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(calendar.to_ical())
        print(f"Wrote {output_path} ({len(all_holidays)} holidays)", file=sys.stderr)
        return len(all_holidays), output_path

    def write_index(self, entries: list[dict[str, str]]) -> None:
        """Write output/index.json listing every (city, locale) combination
        that actually produced a file, so it always reflects exactly what's
        currently available -- not every configured city/locale, just the
        live ones."""
        ordered = sorted(entries, key=lambda entry: (entry["region"], entry["city"], entry["locale"]))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "index.json").write_text(
            json.dumps(ordered, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    def run(self) -> int:
        city_sources = self.validate_sources()
        if city_sources is None:
            return 1

        total_holidays = 0
        index_entries: list[dict[str, str]] = []
        for city, source in zip(self.cities, city_sources):
            for locale in self.locales:
                try:
                    holiday_count, output_path = self.generate_for_city_locale(city, locale, source)
                except SourceUnavailableError as error:
                    print(f"{city.region} source unavailable, aborting: {error}", file=sys.stderr)
                    return 1
                total_holidays += holiday_count
                if output_path is not None:
                    relative_path = output_path.relative_to(self.output_dir).as_posix()
                    index_entries.append(
                        {
                            "city": city.municipality,
                            "region": city.region,
                            "locale": locale,
                            "path": relative_path,
                            "url": f"{self.raw_base_url}/{relative_path}",
                        }
                    )

        self.write_index(index_entries)

        if total_holidays == 0:
            print("No holiday data could be fetched for any city/locale/year.", file=sys.stderr)
            return 1
        return 0
