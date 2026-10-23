from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from .models import Holiday

REGION_SOURCES_FILE = Path(__file__).parent / "region_sources.json"


@runtime_checkable
class RegionSource(Protocol):
    """Contract a region's official holiday source must satisfy to plug into
    the scrape -> generate -> publish pipeline.

    Each autonomous community publishes its own calendar with its own HTML
    structure, language(s), and publishing cadence -- this protocol is
    deliberately thin so the pipeline depends only on this shape, not on
    *how* a given region fetches or parses its data.

    A plain module (like `scraper.py` today) satisfies this protocol just as
    well as a class instance would: Protocol conformance here is checked by
    attribute presence, not by being a particular kind of object, so
    `fetch_holidays` doesn't need to be a bound method.
    """

    SUPPORTED_LOCALES: frozenset[str]

    def fetch_holidays(self, year: int, municipality: str, locale: str) -> list[Holiday] | None:
        """Return all holidays for a municipality/year/locale, or None if
        that year's calendar hasn't been published yet by this source."""
        ...


def load_region_sources(path: Path = REGION_SOURCES_FILE) -> dict[str, RegionSource]:
    """Load the region -> source mapping. Each entry is a dotted module path
    (not inline code -- JSON can't hold that), imported here and checked
    against RegionSource so a misconfigured entry fails loudly at load time
    rather than with a confusing AttributeError deep in the pipeline."""
    module_paths = json.loads(path.read_text(encoding="utf-8"))
    sources: dict[str, RegionSource] = {}
    for region, module_path in module_paths.items():
        module = importlib.import_module(module_path)
        if not isinstance(module, RegionSource):
            raise TypeError(f"{module_path!r} (region {region!r} in {path}) does not satisfy RegionSource")
        sources[region] = module
    return sources
