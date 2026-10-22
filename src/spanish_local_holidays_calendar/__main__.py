from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from .generate_ics import build_calendar
from .scraper import fetch_holidays

MUNICIPALITY = "PALMA"
OUTPUT_PATH = Path("output/palma.ics")


def main() -> int:
    current_year = date.today().year
    all_holidays = []
    found_any = False

    for year in (current_year, current_year + 1):
        holidays = fetch_holidays(year, MUNICIPALITY)
        if holidays is None:
            print(f"[skip] {year} calendar not published yet", file=sys.stderr)
            continue
        print(f"[ok] {year}: {len(holidays)} holidays", file=sys.stderr)
        all_holidays.extend(holidays)
        found_any = True

    if not found_any:
        print("No holiday data could be fetched for any year.", file=sys.stderr)
        return 1

    calendar = build_calendar(all_holidays, calendar_name=f"{MUNICIPALITY.title()} Holidays")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(calendar.to_ical())
    print(f"Wrote {OUTPUT_PATH} ({len(all_holidays)} holidays)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
