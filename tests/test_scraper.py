from datetime import date
from pathlib import Path

from spanish_local_holidays_calendar.scraper import (
    SUPPORTED_LOCALES,
    fetch_holidays,
    fetch_page,
    parse_local_holidays,
    parse_regional_holidays,
    parse_split_local_holidays,
)

FIXTURE = Path(__file__).parent / "fixtures" / "aao_2026_sample.html"
FIXTURE_ES = Path(__file__).parent / "fixtures" / "aao_2026_sample_es.html"
SOURCE_URL = "https://example.test/aao_2026/"


def test_parse_regional_holidays_extracts_general_list():
    html = FIXTURE.read_text(encoding="utf-8")
    holidays = parse_regional_holidays(html, 2026, SOURCE_URL)

    assert {h.name for h in holidays} == {"Cap d'Any", "Festa Nacional", "Dia de Nadal"}
    assert all(h.scope == "regional" for h in holidays)
    assert all(h.source_url == SOURCE_URL for h in holidays)

    national_day = next(h for h in holidays if h.name == "Festa Nacional")
    assert national_day.date == date(2026, 10, 12)


def test_parse_local_holidays_covers_every_single_entry_municipality():
    """Covers both heading styles CAIB uses: ordinary `<p>` (Palma, Muro,
    Petra) and bare `<strong>` + `<br>`, no wrapping `<p>` (Campos)."""
    html = FIXTURE.read_text(encoding="utf-8")
    holidays_by_municipality = parse_local_holidays(html, 2026, SOURCE_URL)

    assert set(holidays_by_municipality) >= {"PALMA", "MURO", "PETRA", "CAMPOS", "SINEU"}

    palma = holidays_by_municipality["PALMA"]
    assert len(palma) == 2
    assert {h.name for h in palma} == {"Sant Sebastià", "Sant Joan"}
    assert all(h.scope == "local" for h in palma)

    sant_sebastia = next(h for h in palma if h.name == "Sant Sebastià")
    assert sant_sebastia.date == date(2026, 1, 20)

    campos = holidays_by_municipality["CAMPOS"]
    assert {h.name for h in campos} == {"Sant Julià i Santa Basilissa", "Sa Fira"}
    sa_fira = next(h for h in campos if h.name == "Sa Fira")
    assert sa_fira.date == date(2026, 10, 22)


def test_parse_local_holidays_catches_holiday_lines_not_wrapped_in_their_own_p_tag():
    """Sineu's second holiday is bare text after a <br>, not its own <p>."""
    html = FIXTURE.read_text(encoding="utf-8")
    holidays_by_municipality = parse_local_holidays(html, 2026, SOURCE_URL)

    sineu = holidays_by_municipality["SINEU"]
    assert {h.name for h in sineu} == {"Sant Marc", "Assumpció de la Mare de Déu (dia previ)"}
    assumpcio = next(h for h in sineu if h.name.startswith("Assumpció"))
    assert assumpcio.date == date(2026, 8, 14)


def test_parse_local_holidays_excludes_split_municipality():
    html = FIXTURE.read_text(encoding="utf-8")
    holidays_by_municipality = parse_local_holidays(html, 2026, SOURCE_URL)

    assert "ANDRATX" not in holidays_by_municipality


def test_parse_split_local_holidays_attributes_each_sub_locality_correctly():
    html = FIXTURE.read_text(encoding="utf-8")
    holidays_by_sub_locality = parse_split_local_holidays(html, 2026, SOURCE_URL)

    assert set(holidays_by_sub_locality) >= {"ANDRATX", "PORT D'ANDRATX", "S'ARRACÓ"}

    port_andratx = holidays_by_sub_locality["PORT D'ANDRATX"]
    assert all(h.scope == "local" for h in port_andratx)
    carme = next(h for h in port_andratx if h.name == "Mare de Déu del Carme")
    assert carme.date == date(2026, 7, 16)

    arraco = holidays_by_sub_locality["S'ARRACÓ"]
    agusti = next(h for h in arraco if h.name == "Sant Agustí")
    assert agusti.date == date(2026, 8, 28)

    # shared Dec 7 bridge day, unnamed in the source, attributed to all three
    for sub_locality in ("ANDRATX", "PORT D'ANDRATX", "S'ARRACÓ"):
        assert any(h.date == date(2026, 12, 7) for h in holidays_by_sub_locality[sub_locality])


def test_parse_split_local_holidays_skips_ambiguous_grouped_sub_localities():
    """Sant Josep de sa Talaia groups several place names per heading entry,
    so pairing would be a guess -- it's skipped instead."""
    html = FIXTURE.read_text(encoding="utf-8")
    holidays_by_sub_locality = parse_split_local_holidays(html, 2026, SOURCE_URL)

    assert not any("TALAIA" in name or "JORDI" in name for name in holidays_by_sub_locality)


def test_fetch_holidays_resolves_a_sub_locality_by_name(monkeypatch):
    html = FIXTURE.read_text(encoding="utf-8")
    monkeypatch.setattr("spanish_local_holidays_calendar.scraper.fetch_page", lambda year, locale: html)

    holidays = fetch_holidays(2026, municipality="Port d'Andratx", locale="ca")

    local_names = {h.name for h in holidays if h.scope == "local"}
    assert "Mare de Déu del Carme" in local_names


def test_fetch_holidays_works_for_a_single_entry_municipality_beyond_palma(monkeypatch):
    html = FIXTURE.read_text(encoding="utf-8")
    monkeypatch.setattr("spanish_local_holidays_calendar.scraper.fetch_page", lambda year, locale: html)

    holidays = fetch_holidays(2026, municipality="CAMPOS", locale="ca")

    local_names = {h.name for h in holidays if h.scope == "local"}
    assert local_names == {"Sant Julià i Santa Basilissa", "Sa Fira"}
    assert {h.name for h in holidays if h.scope == "regional"} == {"Cap d'Any", "Festa Nacional", "Dia de Nadal"}


def test_parse_regional_holidays_extracts_general_list_es():
    html = FIXTURE_ES.read_text(encoding="utf-8")
    holidays = parse_regional_holidays(html, 2026, SOURCE_URL)

    assert {h.name for h in holidays} == {"Año Nuevo", "Fiesta Nacional", "Día de Navidad"}
    assert all(h.scope == "regional" for h in holidays)

    national_day = next(h for h in holidays if h.name == "Fiesta Nacional")
    assert national_day.date == date(2026, 10, 12)


def test_parse_local_holidays_matches_only_target_municipality_es():
    html = FIXTURE_ES.read_text(encoding="utf-8")
    holidays_by_municipality = parse_local_holidays(html, 2026, SOURCE_URL)
    palma = holidays_by_municipality["PALMA"]

    assert len(palma) == 2
    assert {h.name for h in palma} == {"San Sebastián", "San Juan"}
    assert all(h.scope == "local" for h in palma)

    san_sebastian = next(h for h in palma if h.name == "San Sebastián")
    assert san_sebastian.date == date(2026, 1, 20)
    assert "ANDRATX" not in holidays_by_municipality


def test_parse_split_local_holidays_attributes_each_sub_locality_correctly_es():
    html = FIXTURE_ES.read_text(encoding="utf-8")
    holidays_by_sub_locality = parse_split_local_holidays(html, 2026, SOURCE_URL)

    assert set(holidays_by_sub_locality) >= {"ANDRATX", "PORT D'ANDRATX", "S'ARRACÓ"}

    port_andratx = holidays_by_sub_locality["PORT D'ANDRATX"]
    carmen = next(h for h in port_andratx if h.name == "Virgen del Carmen")
    assert carmen.date == date(2026, 7, 16)

    assert not any("TALAIA" in name or "JORGE" in name for name in holidays_by_sub_locality)


def test_fetch_page_builds_locale_specific_url(monkeypatch):
    requested_urls = []

    class FakeResponse:
        status_code = 200
        text = "<html></html>"

        def raise_for_status(self):
            pass

    def fake_get(url, timeout):
        requested_urls.append(url)
        return FakeResponse()

    monkeypatch.setattr("spanish_local_holidays_calendar.scraper.requests.get", fake_get)

    fetch_page(2026, locale="es")
    fetch_page(2026, locale="ca")

    assert requested_urls == [
        "https://www.caib.es/sites/calendarilaboral/es/aao_2026/",
        "https://www.caib.es/sites/calendarilaboral/ca/aao_2026/",
    ]


def test_supported_locales_matches_known_vocabularies():
    assert SUPPORTED_LOCALES == {"es", "ca"}
