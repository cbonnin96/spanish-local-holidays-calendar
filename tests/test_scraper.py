from datetime import date
from pathlib import Path

from spanish_local_holidays_calendar.scraper import parse_local_holidays, parse_regional_holidays

FIXTURE = Path(__file__).parent / "fixtures" / "aao_2026_sample.html"
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
