from datetime import date

from spanish_local_holidays_calendar.catalonia_source import (
    LOCAL_DATASET_URL,
    REGIONAL_DATASET_URL,
    _regional_holiday_name,
    fetch_holidays,
)

# Real 2026 Easter dates: Easter Sunday is 2026-04-05, so Good Friday is
# 2026-04-03 and Easter Monday is 2026-04-06 -- matches what the open data
# portal actually returns for 2026.
GOOD_FRIDAY_2026 = date(2026, 4, 3)
EASTER_MONDAY_2026 = date(2026, 4, 6)


def test_regional_holiday_name_resolves_fixed_dates():
    assert _regional_holiday_name(date(2026, 1, 1), "ca") == "Cap d'Any"
    assert _regional_holiday_name(date(2026, 1, 1), "es") == "Año Nuevo"
    assert _regional_holiday_name(date(2026, 12, 25), "ca") == "Nadal"


def test_regional_holiday_name_resolves_easter_relative_dates():
    assert _regional_holiday_name(GOOD_FRIDAY_2026, "ca") == "Divendres Sant"
    assert _regional_holiday_name(EASTER_MONDAY_2026, "es") == "Lunes de Pascua"


def test_regional_holiday_name_falls_back_to_generic_for_unknown_dates():
    assert _regional_holiday_name(date(2026, 3, 2), "ca") == "Festa general"
    assert _regional_holiday_name(date(2026, 3, 2), "es") == "Fiesta general"


def _fake_requests_get(regional_rows, local_rows):
    class FakeResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            pass

        def json(self):
            return self._payload

    def fake_get(url, params, timeout):
        if url == REGIONAL_DATASET_URL:
            return FakeResponse(regional_rows)
        if url == LOCAL_DATASET_URL:
            return FakeResponse(local_rows)
        raise AssertionError(f"unexpected URL: {url}")

    return fake_get


def test_fetch_holidays_dedupes_rows_and_assigns_names(monkeypatch):
    regional_rows = [
        {"any_calendari": "2026", "data": "2026-01-01T00:00:00.000"},
        {"any_calendari": "2026", "data": "2026-01-01T00:00:00.000"},  # duplicate
        {"any_calendari": "2026", "data": "2026-01-01T00:00:00.000"},  # duplicate
        {"any_calendari": "2026", "data": "2026-12-25T00:00:00.000"},
    ]
    local_rows = [
        {"any_calendari": "2026", "data": "2026-05-25T00:00:00.000", "festiu": "Festiu local"},
        {"any_calendari": "2026", "data": "2026-09-24T00:00:00.000", "festiu": "test_junk_value"},
    ]
    monkeypatch.setattr(
        "spanish_local_holidays_calendar.catalonia_source.requests.get",
        _fake_requests_get(regional_rows, local_rows),
    )

    holidays = fetch_holidays(2026, "Barcelona", locale="ca")

    assert len(holidays) == 4  # 2 distinct regional dates (deduped) + 2 local dates
    regional = [h for h in holidays if h.scope == "regional"]
    local = [h for h in holidays if h.scope == "local"]

    assert {h.name for h in regional} == {"Cap d'Any", "Nadal"}
    assert all(h.name == "Festa local" for h in local)  # generic, ignores the junk "festiu" text
    assert {h.date for h in local} == {date(2026, 5, 25), date(2026, 9, 24)}


def test_fetch_holidays_returns_none_when_year_not_published(monkeypatch):
    monkeypatch.setattr(
        "spanish_local_holidays_calendar.catalonia_source.requests.get",
        _fake_requests_get(regional_rows=[], local_rows=[]),
    )

    assert fetch_holidays(2099, "Barcelona", locale="ca") is None
