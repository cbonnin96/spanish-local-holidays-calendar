from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..models import Holiday


@runtime_checkable
class RegionSource(Protocol):
    """Contract a region's official holiday source must satisfy to plug into
    the scrape -> generate -> publish pipeline.

    Each autonomous community publishes its own calendar with its own HTML
    structure, language(s), and publishing cadence -- this protocol is
    deliberately thin so the pipeline depends only on this shape, not on
    *how* a given region fetches or parses its data.

    A plain module (like `illes_balears.py` today) satisfies this protocol
    just as well as a class instance would: Protocol conformance here is
    checked by attribute presence, not by being a particular kind of
    object, so `fetch_holidays` doesn't need to be a bound method.
    """

    SUPPORTED_LOCALES: frozenset[str]

    def fetch_holidays(self, year: int, municipality: str, locale: str) -> list[Holiday] | None:
        """Return all holidays for a municipality/year/locale, or None if
        that year's calendar hasn't been published yet by this source."""
        ...
