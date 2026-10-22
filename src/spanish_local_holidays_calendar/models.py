from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Holiday:
    date: date
    name: str
    scope: str  # "regional" (CAIB's general Illes Balears list, includes national holidays) or "local"
    source_url: str
