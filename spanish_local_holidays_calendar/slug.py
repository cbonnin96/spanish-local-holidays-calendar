from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    """Normalize a display name into a URL/path-safe slug: lowercase ASCII,
    words separated by single hyphens (e.g. "Illes Balears" -> "illes-balears").
    """
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
