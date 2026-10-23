from spanish_local_holidays_calendar import catalonia_source, scraper
from spanish_local_holidays_calendar.region_source import RegionSource


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
