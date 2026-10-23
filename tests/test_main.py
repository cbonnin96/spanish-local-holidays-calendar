from datetime import date

import spanish_local_holidays_calendar.__main__ as main_module
from spanish_local_holidays_calendar.models import Holiday

FAKE_HOLIDAYS = {
    "es": [Holiday(date=date(2026, 1, 20), name="San Sebastián", scope="local", source_url="https://example.test/es/")],
    "ca": [Holiday(date=date(2026, 1, 20), name="Sant Sebastià", scope="local", source_url="https://example.test/ca/")],
}


def test_generate_for_locale_writes_one_file_per_language(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)

    def fake_fetch_holidays(year, municipality, locale):
        return FAKE_HOLIDAYS[locale] if year == date.today().year else None

    monkeypatch.setattr(main_module, "fetch_holidays", fake_fetch_holidays)

    es_count = main_module.generate_for_locale("es")
    ca_count = main_module.generate_for_locale("ca")

    assert es_count == 1
    assert ca_count == 1

    es_file = tmp_path / "palma.es.ics"
    ca_file = tmp_path / "palma.ca.ics"
    assert es_file.exists()
    assert ca_file.exists()

    assert b"San Sebasti" in es_file.read_bytes()
    assert b"Sant Sebasti" in ca_file.read_bytes()
    assert es_file.read_bytes() != ca_file.read_bytes()


def test_main_returns_nonzero_when_no_locale_has_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main_module, "fetch_holidays", lambda year, municipality, locale: None)

    assert main_module.main() == 1
    assert list(tmp_path.iterdir()) == []


def test_main_succeeds_if_at_least_one_locale_has_data(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "OUTPUT_DIR", tmp_path)

    def fake_fetch_holidays(year, municipality, locale):
        if locale == "ca" and year == date.today().year:
            return FAKE_HOLIDAYS["ca"]
        return None

    monkeypatch.setattr(main_module, "fetch_holidays", fake_fetch_holidays)

    assert main_module.main() == 0
    assert (tmp_path / "palma.ca.ics").exists()
    assert not (tmp_path / "palma.es.ics").exists()
