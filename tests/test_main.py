from datetime import date

import spanish_local_holidays_calendar.__main__ as main_module
from spanish_local_holidays_calendar.cities import CityConfig
from spanish_local_holidays_calendar.locales import load_locales
from spanish_local_holidays_calendar.models import Holiday

LOCALES = load_locales()

PALMA = CityConfig(municipality="PALMA", region="Illes Balears", source="https://example.test/")
MURO = CityConfig(municipality="MURO", region="Illes Balears", source="https://example.test/")

FAKE_HOLIDAYS = {
    ("PALMA", "es"): [Holiday(date=date(2026, 1, 20), name="San Sebastián", scope="local", source_url="https://example.test/es/")],
    ("PALMA", "ca"): [Holiday(date=date(2026, 1, 20), name="Sant Sebastià", scope="local", source_url="https://example.test/ca/")],
    ("MURO", "es"): [Holiday(date=date(2026, 1, 17), name="San Antonio", scope="local", source_url="https://example.test/es/")],
    ("MURO", "ca"): [Holiday(date=date(2026, 1, 17), name="Sant Antoni", scope="local", source_url="https://example.test/ca/")],
}


def fake_fetch_holidays_for(registry):
    def fake_fetch_holidays(year, municipality, locale):
        if year != date.today().year:
            return None
        return registry.get((municipality, locale))

    return fake_fetch_holidays


def test_generate_for_city_locale_writes_one_file_per_language(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "fetch_holidays", fake_fetch_holidays_for(FAKE_HOLIDAYS))

    es_count = main_module.generate_for_city_locale(PALMA, "es", LOCALES)
    ca_count = main_module.generate_for_city_locale(PALMA, "ca", LOCALES)

    assert es_count == 1
    assert ca_count == 1

    es_file = tmp_path / "palma.es.ics"
    ca_file = tmp_path / "palma.ca.ics"
    assert es_file.exists()
    assert ca_file.exists()

    assert b"San Sebasti" in es_file.read_bytes()
    assert b"Sant Sebasti" in ca_file.read_bytes()
    assert es_file.read_bytes() != ca_file.read_bytes()


def test_generate_for_city_locale_uses_correct_localized_calendar_name(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "fetch_holidays", fake_fetch_holidays_for(FAKE_HOLIDAYS))

    main_module.generate_for_city_locale(PALMA, "es", LOCALES)
    main_module.generate_for_city_locale(PALMA, "ca", LOCALES)

    assert b"X-WR-CALNAME:Festivos de Palma" in (tmp_path / "palma.es.ics").read_bytes()
    assert b"X-WR-CALNAME:Festius de Palma" in (tmp_path / "palma.ca.ics").read_bytes()


def test_main_returns_nonzero_when_no_city_has_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA])
    monkeypatch.setattr(main_module, "fetch_holidays", lambda year, municipality, locale: None)

    assert main_module.main() == 1
    assert list(tmp_path.iterdir()) == []


def test_main_succeeds_if_at_least_one_city_locale_has_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA])

    def fake_fetch_holidays(year, municipality, locale):
        if municipality == "PALMA" and locale == "ca" and year == date.today().year:
            return FAKE_HOLIDAYS[("PALMA", "ca")]
        return None

    monkeypatch.setattr(main_module, "fetch_holidays", fake_fetch_holidays)

    assert main_module.main() == 0
    assert (tmp_path / "palma.ca.ics").exists()
    assert not (tmp_path / "palma.es.ics").exists()


def test_adding_a_registry_entry_produces_a_new_output_file_without_code_changes(tmp_path, monkeypatch):
    """Acceptance criterion for #10: adding a city to the registry produces a
    new output file for that city, with no scraper/generator code changes --
    exercised here by handing main() a registry with an extra, unseen city."""
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "load_cities", lambda: [PALMA, MURO])
    monkeypatch.setattr(main_module, "fetch_holidays", fake_fetch_holidays_for(FAKE_HOLIDAYS))

    assert main_module.main() == 0

    for filename in ("palma.es.ics", "palma.ca.ics", "muro.es.ics", "muro.ca.ics"):
        assert (tmp_path / filename).exists(), filename

    assert b"San Antonio" in (tmp_path / "muro.es.ics").read_bytes()
    assert b"Sant Antoni" in (tmp_path / "muro.ca.ics").read_bytes()
