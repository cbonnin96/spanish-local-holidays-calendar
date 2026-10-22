from __future__ import annotations

import uuid
from datetime import timedelta

from icalendar import Calendar, Event

from .models import Holiday


def build_calendar(holidays: list[Holiday], calendar_name: str) -> Calendar:
    calendar = Calendar()
    calendar.add("prodid", "-//Spanish Local Holidays Calendar//Palma//ES")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", calendar_name)
    calendar.add("x-wr-timezone", "Europe/Madrid")

    for holiday in holidays:
        event = Event()
        event.add("summary", f"{holiday.name} ({holiday.scope})")
        event.add("dtstart", holiday.date)
        event.add("dtend", holiday.date + timedelta(days=1))
        event.add("description", f"Source: {holiday.source_url}")
        uid_seed = f"{holiday.date.isoformat()}-{holiday.scope}-{holiday.name}"
        event.add("uid", f"{uuid.uuid5(uuid.NAMESPACE_URL, uid_seed)}@spanish-local-holidays-calendar")
        calendar.add_component(event)

    return calendar
