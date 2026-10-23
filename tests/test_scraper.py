from datetime import date
from pathlib import Path

from spanish_local_holidays_calendar.scraper import (
    SUPPORTED_LOCALES,
    fetch_page,
    parse_local_holidays,
    parse_regional_holidays,
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


def test_parse_local_holidays_matches_only_target_municipality():
    html = FIXTURE.read_text(encoding="utf-8")
    holidays = parse_local_holidays(html, 2026, "PALMA", SOURCE_URL)

    assert len(holidays) == 2
    assert {h.name for h in holidays} == {"Sant Sebastià", "Sant Joan"}
    assert all(h.scope == "local" for h in holidays)

    sant_sebastia = next(h for h in holidays if h.name == "Sant Sebastià")
    assert sant_sebastia.date == date(2026, 1, 20)


def test_parse_local_holidays_unknown_municipality_returns_empty():
    html = FIXTURE.read_text(encoding="utf-8")
    holidays = parse_local_holidays(html, 2026, "NOT-A-REAL-TOWN", SOURCE_URL)

    assert holidays == []


def test_parse_regional_holidays_extracts_general_list_es():
    html = FIXTURE_ES.read_text(encoding="utf-8")
    holidays = parse_regional_holidays(html, 2026, SOURCE_URL)

    assert {h.name for h in holidays} == {"Año Nuevo", "Fiesta Nacional", "Día de Navidad"}
    assert all(h.scope == "regional" for h in holidays)

    national_day = next(h for h in holidays if h.name == "Fiesta Nacional")
    assert national_day.date == date(2026, 10, 12)


def test_parse_local_holidays_matches_only_target_municipality_es():
    html = FIXTURE_ES.read_text(encoding="utf-8")
    holidays = parse_local_holidays(html, 2026, "PALMA", SOURCE_URL)

    assert len(holidays) == 2
    assert {h.name for h in holidays} == {"San Sebastián", "San Juan"}
    assert all(h.scope == "local" for h in holidays)

    san_sebastian = next(h for h in holidays if h.name == "San Sebastián")
    assert san_sebastian.date == date(2026, 1, 20)


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
