from spanish_local_holidays_calendar.sources import catalunya, illes_balears
from spanish_local_holidays_calendar.sources.base import RegionSource


def test_illes_balears_module_satisfies_region_source_protocol():
    """illes_balears is a plain module, not a class instance, yet it must
    still satisfy RegionSource -- demonstrating the protocol doesn't force
    every future region's source into a particular object shape."""
    assert isinstance(illes_balears, RegionSource)


def test_catalunya_module_satisfies_region_source_protocol():
    assert isinstance(catalunya, RegionSource)


def test_region_source_protocol_rejects_an_incomplete_source():
    class IncompleteSource:
        SUPPORTED_LOCALES = frozenset({"es"})
        # missing fetch_holidays

    assert not isinstance(IncompleteSource(), RegionSource)
