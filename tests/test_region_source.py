import json

import pytest

from spanish_local_holidays_calendar import catalonia_source, scraper
from spanish_local_holidays_calendar.region_source import RegionSource, load_region_sources


def test_caib_scraper_module_satisfies_region_source_protocol():
    """The existing Balearics/CAIB scraper is a plain module, not a class
    instance, yet it must still satisfy RegionSource -- demonstrating the
    protocol doesn't force every future region's source into a particular
    object shape."""
    assert isinstance(scraper, RegionSource)


def test_catalonia_source_module_satisfies_region_source_protocol():
    assert isinstance(catalonia_source, RegionSource)


def test_region_source_protocol_rejects_an_incomplete_source():
    class IncompleteSource:
        SUPPORTED_LOCALES = frozenset({"es"})
        # missing fetch_holidays

    assert not isinstance(IncompleteSource(), RegionSource)


def test_load_region_sources_resolves_the_real_registry_to_actual_modules():
    sources = load_region_sources()

    assert sources == {"Illes Balears": scraper, "Catalunya": catalonia_source}


def test_load_region_sources_rejects_a_module_that_does_not_satisfy_the_protocol(tmp_path):
    registry = tmp_path / "region_sources.json"
    registry.write_text(json.dumps({"Nowhere": "json"}), encoding="utf-8")  # stdlib json: no fetch_holidays

    with pytest.raises(TypeError, match="does not satisfy RegionSource"):
        load_region_sources(registry)
