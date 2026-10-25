import json

import pytest

from spanish_local_holidays_calendar.registry.region_sources import load_region_sources
from spanish_local_holidays_calendar.sources import catalunya, illes_balears


def test_load_region_sources_resolves_the_real_registry_to_actual_modules():
    sources = load_region_sources()

    assert sources == {"Illes Balears": illes_balears, "Catalunya": catalunya}


def test_load_region_sources_rejects_a_module_that_does_not_satisfy_the_protocol(tmp_path):
    registry = tmp_path / "region_sources.json"
    registry.write_text(json.dumps({"Nowhere": "json"}), encoding="utf-8")  # stdlib json: no fetch_holidays

    with pytest.raises(TypeError, match="does not satisfy RegionSource"):
        load_region_sources(registry)
