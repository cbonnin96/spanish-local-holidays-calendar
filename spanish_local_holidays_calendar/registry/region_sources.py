from __future__ import annotations

import importlib
from pathlib import Path

from ..sources.base import RegionSource
from ._json import read_json

REGION_SOURCES_FILE = Path(__file__).parent / "region_sources.json"


def load_region_sources(path: Path = REGION_SOURCES_FILE) -> dict[str, RegionSource]:
    """Load the region -> source mapping. Each entry is a dotted module path
    (not inline code -- JSON can't hold that), imported here and checked
    against RegionSource so a misconfigured entry fails loudly at load time
    rather than with a confusing AttributeError deep in the pipeline."""
    module_paths = read_json(path)
    sources: dict[str, RegionSource] = {}
    for region, module_path in module_paths.items():
        module = importlib.import_module(module_path)
        if not isinstance(module, RegionSource):
            raise TypeError(f"{module_path!r} (region {region!r} in {path}) does not satisfy RegionSource")
        sources[region] = module
    return sources
