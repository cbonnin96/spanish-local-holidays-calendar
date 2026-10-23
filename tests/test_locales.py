import json

from spanish_local_holidays_calendar.locales import LocaleConfig, load_locales


def test_load_locales_parses_the_real_registry():
    locales = load_locales()

    assert set(locales) == {"es", "ca"}
    assert locales["es"].calendar_name_template == "Festivos de {city}"
    assert locales["ca"].calendar_name_template == "Festius de {city}"


def test_load_locales_parses_an_arbitrary_registry_file(tmp_path):
    registry = tmp_path / "locales.json"
    registry.write_text(
        json.dumps({"en": {"calendar_name_template": "{city} Holidays"}}),
        encoding="utf-8",
    )

    locales = load_locales(registry)

    assert locales == {"en": LocaleConfig(calendar_name_template="{city} Holidays")}
