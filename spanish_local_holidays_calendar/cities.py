from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CITIES_FILE = Path(__file__).parent / "cities.json"


@dataclass(frozen=True)
class CityConfig:
    municipality: str
    region: str
    source: str


def load_cities(path: Path = CITIES_FILE) -> list[CityConfig]:
    """Load the city registry: every municipality the generator should produce
    a calendar for, with its region and official source (the latter currently
    informational -- all registered cities share the single CAIB scraper for
    now; per-region sources are future work, see epic for multi-region support).
    """
    entries = json.loads(path.read_text(encoding="utf-8"))
    return [CityConfig(**entry) for entry in entries]
