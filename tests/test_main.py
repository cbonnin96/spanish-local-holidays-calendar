from datetime import date

import spanish_local_holidays_calendar.__main__ as main_module
from spanish_local_holidays_calendar.cities import CityConfig
from spanish_local_holidays_calendar.locales import LocaleConfig, load_locales
from spanish_local_holidays_calendar.models import Holiday

LOCALES = load_locales()

PALMA = CityConfig(municipality="PALMA", region="Illes Balears", source="https://example.test/")
MURO = CityConfig(municipality="MURO", region="Illes Balears", source="https://example.test/")
BARCELONA = CityConfig(municipality="Barcelona", region="Catalunya", source="https://example.test/")

FAKE_HOLIDAYS = {
    ("PALMA", "es"): [Holiday(date=date(2026, 1, 20), name="San Sebastián", scope="local", source_url="https://example.test/es/")],
    ("PALMA", "ca"): [Holiday(date=date(2026, 1, 20), name="Sant Sebastià", scope="local", source_url="https://example.test/ca/")],
    ("MURO", "es"): [Holiday(date=date(2026, 1, 17), name="San Antonio", scope="local", source_url="https://example.test/es/")],
    ("MURO", "ca"): [Holiday(date=date(2026, 1, 17), name="Sant Antoni", scope="local", source_url="https://example.test/ca/")],
    ("Barcelona", "es"): [Holiday(date=date(2026, 5, 25), name="Fiesta local", scope="local", source_url="https://example.test/es/")],
    ("Barcelona", "ca"): [Holiday(date=date(2026, 5, 25), name="Festa local", scope="local", source_url="https://example.test/ca/")],
}


class FakeSource:
    def __init__(self, holidays_by_key, supported_locales=frozenset({"es", "ca"})):
        self.SUPPORTED_LOCALES = supported_locales
        self._holidays_by_key = holidays_by_key

    def fetch_holidays(self, year, municipality, locale):
        if year != date.today().year:
            return None
        return self._holidays_by_key.get((municipality, locale))


def test_generate_for_city_locale_writes_one_file_per_language(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    source = FakeSource(FAKE_HOLIDAYS)

    es_count = main_module.generate_for_city_locale(PALMA, "es", LOCALES, source)
    ca_count = main_module.generate_for_city_locale(PALMA, "ca", LOCALES, source)

    assert es_count == 1
    assert ca_count == 1

    es_file = tmp_path / "illes-balears/palma.es.ics"
    ca_file = tmp_path / "illes-balears/palma.ca.ics"
    assert es_file.exists()
    assert ca_file.exists()

    assert b"San Sebasti" in es_file.read_bytes()
    assert b"Sant Sebasti" in ca_file.read_bytes()
    assert es_file.read_bytes() != ca_file.read_bytes()


def test_generate_for_city_locale_writes_to_output_region_slug_city_slug_lang_ics(tmp_path, monkeypatch):
    """Acceptance criterion for #13: output path is output/<region-slug>/
    <city-slug>.<lang>.ics, not a flat output/<city>.<lang>.ics."""
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    source = FakeSource(FAKE_HOLIDAYS)

    main_module.generate_for_city_locale(BARCELONA, "ca", LOCALES, source)

    assert (tmp_path / "catalunya" / "barcelona.ca.ics").exists()
    assert not (tmp_path / "barcelona.ca.ics").exists()


def test_generate_for_city_locale_uses_correct_localized_calendar_name(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    source = FakeSource(FAKE_HOLIDAYS)

    main_module.generate_for_city_locale(PALMA, "es", LOCALES, source)
    main_module.generate_for_city_locale(PALMA, "ca", LOCALES, source)

    assert b"X-WR-CALNAME:Festivos de Palma" in (tmp_path / "illes-balears/palma.es.ics").read_bytes()
    assert b"X-WR-CALNAME:Festius de Palma" in (tmp_path / "illes-balears/palma.ca.ics").read_bytes()


def test_main_returns_nonzero_when_no_city_has_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA])
    monkeypatch.setattr(main_module, "load_region_sources", lambda: {"Illes Balears": FakeSource({})})

    assert main_module.main() == 1
    assert list(tmp_path.iterdir()) == []


def test_main_succeeds_if_at_least_one_city_locale_has_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA])
    monkeypatch.setattr(
        main_module,
        "load_region_sources",
        lambda: {"Illes Balears": FakeSource({("PALMA", "ca"): FAKE_HOLIDAYS[("PALMA", "ca")]})},
    )

    assert main_module.main() == 0
    assert (tmp_path / "illes-balears/palma.ca.ics").exists()
    assert not (tmp_path / "illes-balears/palma.es.ics").exists()


def test_adding_a_registry_entry_produces_a_new_output_file_without_code_changes(tmp_path, monkeypatch):
    """Acceptance criterion for #10: adding a city to the registry produces a
    new output file for that city, with no scraper/generator code changes --
    exercised here by handing main() a registry with an extra, unseen city."""
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA, MURO])
    monkeypatch.setattr(main_module, "load_region_sources", lambda: {"Illes Balears": FakeSource(FAKE_HOLIDAYS)})

    assert main_module.main() == 0

    for filename in ("illes-balears/palma.es.ics", "illes-balears/palma.ca.ics", "illes-balears/muro.es.ics", "illes-balears/muro.ca.ics"):
        assert (tmp_path / filename).exists(), filename

    assert b"San Antonio" in (tmp_path / "illes-balears/muro.es.ics").read_bytes()
    assert b"Sant Antoni" in (tmp_path / "illes-balears/muro.ca.ics").read_bytes()


def test_main_dispatches_different_regions_to_their_own_source(tmp_path, monkeypatch):
    """Acceptance criterion for #17: a city from a second region is routed to
    its own RegionSource, independent of the first region's source."""
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA, BARCELONA])
    monkeypatch.setattr(
        main_module,
        "load_region_sources",
        lambda: {
            "Illes Balears": FakeSource(FAKE_HOLIDAYS),
            "Catalunya": FakeSource(FAKE_HOLIDAYS),
        },
    )

    assert main_module.main() == 0

    for filename in ("illes-balears/palma.es.ics", "illes-balears/palma.ca.ics", "catalunya/barcelona.es.ics", "catalunya/barcelona.ca.ics"):
        assert (tmp_path / filename).exists(), filename

    assert b"Festa local" in (tmp_path / "catalunya/barcelona.ca.ics").read_bytes()


def test_main_fails_loudly_if_a_city_region_has_no_registered_source(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [BARCELONA])
    monkeypatch.setattr(main_module, "load_region_sources", lambda: {"Illes Balears": FakeSource(FAKE_HOLIDAYS)})

    assert main_module.main() == 1
    assert list(tmp_path.iterdir()) == []

    err = capsys.readouterr().err
    assert "Catalunya" in err
    assert "No source registered" in err


def test_main_fails_loudly_if_locales_registry_outpaces_a_sources_support(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA])
    monkeypatch.setattr(main_module, "load_region_sources", lambda: {"Illes Balears": FakeSource(FAKE_HOLIDAYS)})
    monkeypatch.setattr(
        main_module,
        "load_locales",
        lambda: {**LOCALES, "en": LocaleConfig(calendar_name_template="{city} Holidays")},
    )

    assert main_module.main() == 1
    assert list(tmp_path.iterdir()) == []

    err = capsys.readouterr().err
    assert "en" in err
    assert "doesn't support" in err
