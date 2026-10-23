from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LOCALES_FILE = Path(__file__).parent / "locales.json"


@dataclass(frozen=True)
class LocaleConfig:
    calendar_name_template: str


def load_locales(path: Path = LOCALES_FILE) -> dict[str, LocaleConfig]:
    """Load the set of supported locales and their display strings. The set
    of keys here *is* the list of locales the generator produces -- there's
    no separate hardcoded locale list to keep in sync."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {code: LocaleConfig(**fields) for code, fields in data.items()}
