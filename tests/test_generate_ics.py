from datetime import date

from spanish_local_holidays_calendar.generate_ics import build_calendar
from spanish_local_holidays_calendar.models import Holiday


def test_build_calendar_produces_valid_vevents():
    holidays = [
        Holiday(date=date(2026, 1, 20), name="Sant Sebastià", scope="local", source_url="https://example.test"),
        Holiday(date=date(2026, 10, 12), name="Festa Nacional", scope="regional", source_url="https://example.test"),
    ]

    calendar = build_calendar(holidays, "Palma Holidays")
    raw = calendar.to_ical().decode("utf-8")

    assert "BEGIN:VCALENDAR" in raw
    assert raw.count("BEGIN:VEVENT") == 2
    assert "DTSTART;VALUE=DATE:20260120" in raw
    assert "DTEND;VALUE=DATE:20260121" in raw
    assert "X-WR-CALNAME:Palma Holidays" in raw


def test_build_calendar_uids_are_stable_and_unique():
    holidays = [
        Holiday(date=date(2026, 1, 20), name="Sant Sebastià", scope="local", source_url="https://example.test"),
        Holiday(date=date(2026, 6, 24), name="Sant Joan", scope="local", source_url="https://example.test"),
    ]

    first_pass = build_calendar(holidays, "Palma Holidays").to_ical()
    second_pass = build_calendar(holidays, "Palma Holidays").to_ical()

    assert first_pass == second_pass
