from datetime import date

import spanish_local_holidays_calendar.__main__ as main_module
from spanish_local_holidays_calendar.registry.cities import CityConfig
from spanish_local_holidays_calendar.models import Holiday

PALMA = CityConfig(municipality="PALMA", region="Illes Balears", source="https://example.test/")


class FakeSource:
    SUPPORTED_LOCALES = frozenset({"es", "ca"})

    def fetch_holidays(self, year, municipality, locale):
        if year != date.today().year:
            return None
        return [Holiday(date=date(2026, 1, 20), name="Sant Sebastià", scope="local", source_url="https://example.test/")]


def test_main_wires_the_registries_into_a_working_pipeline(tmp_path, monkeypatch):
    """main() itself has no branching logic left to test -- it just loads
    the four registries and hands them to CalendarPipeline. This confirms
    that wiring actually produces a working pipeline, without
    re-exercising CalendarPipeline's own behavior (see test_pipeline.py)."""
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA])
    monkeypatch.setattr(main_module, "load_region_sources", lambda: {"Illes Balears": FakeSource()})

    assert main_module.main() == 0
    assert (tmp_path / "illes-balears/palma.es.ics").exists()
    assert (tmp_path / "illes-balears/palma.ca.ics").exists()
