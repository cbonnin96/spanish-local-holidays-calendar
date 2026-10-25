import json

from spanish_local_holidays_calendar.cities import CityConfig, load_cities


def test_load_cities_parses_the_real_registry():
    cities = load_cities()

    assert any(city.municipality == "PALMA" for city in cities)
    palma = next(city for city in cities if city.municipality == "PALMA")
    assert palma.region
    assert palma.source


def test_load_cities_parses_an_arbitrary_registry_file(tmp_path):
    registry = tmp_path / "cities.json"
    registry.write_text(
        json.dumps(
            [
                {"municipality": "PALMA", "region": "Illes Balears", "source": "https://example.test/"},
                {"municipality": "MURO", "region": "Illes Balears", "source": "https://example.test/"},
            ]
        ),
        encoding="utf-8",
    )

    cities = load_cities(registry)

    assert cities == [
        CityConfig(municipality="PALMA", region="Illes Balears", source="https://example.test/"),
        CityConfig(municipality="MURO", region="Illes Balears", source="https://example.test/"),
    ]
