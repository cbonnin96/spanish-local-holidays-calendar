from spanish_local_holidays_calendar.slug import slugify


def test_slugify_lowercases_and_hyphenates_spaces():
    assert slugify("Illes Balears") == "illes-balears"
    assert slugify("Barcelona") == "barcelona"


def test_slugify_strips_accents():
    assert slugify("País Basc") == "pais-basc"
    assert slugify("Sant Joan Despí") == "sant-joan-despi"


def test_slugify_collapses_non_alphanumeric_runs_and_strips_edges():
    assert slugify("  Port d'Andratx!! ") == "port-d-andratx"
