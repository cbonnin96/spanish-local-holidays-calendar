from __future__ import annotations

from pathlib import Path

from .pipeline import CalendarPipeline
from .registry.cities import load_cities
from .registry.locales import load_locales
from .registry.region_sources import load_region_sources

OUTPUT_DIR = Path("output")
RAW_BASE_URL = "https://raw.githubusercontent.com/cbonnin96/spanish-local-holidays-calendar/main/output"


def main() -> int:
    pipeline = CalendarPipeline(
        cities=load_cities(),
        locales=load_locales(),
        region_sources=load_region_sources(),
        output_dir=OUTPUT_DIR,
        raw_base_url=RAW_BASE_URL,
    )
    return pipeline.run()


if __name__ == "__main__":
    raise SystemExit(main())
