from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._json import read_json

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
    return [CityConfig(**entry) for entry in read_json(path)]
