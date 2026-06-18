"""
Tests for the typed enumerations (bwt_wrapper.enumerations).

These guard the contract the rest of the package depends on — including a
regression check that entity_type / request_type are each defined exactly
once (they were previously declared twice).
"""

from bwt_wrapper.enumerations import country, entity_type, language, request_type


def test_entity_type_values():
    assert entity_type.PAGE == 0
    assert entity_type.DIRECTORY == 1
    assert int(entity_type.DIRECTORY) == 1


def test_request_type_values():
    assert request_type.REMOVE_CACHE == 0
    assert request_type.DISALLOW == 1


def test_blocked_enums_have_exactly_two_members():
    # Regression: these were accidentally defined twice in the source.
    assert len(list(entity_type)) == 2
    assert len(list(request_type)) == 2


def test_country_is_str_enum_with_expected_codes():
    assert issubclass(country, str)
    assert country.UNITED_STATES.value == "us"
    assert country.UNITED_KINGDOM.value == "gb"
    assert country.ITALY.value == "it"


def test_language_is_str_enum_with_expected_codes():
    assert issubclass(language, str)
    assert language.ENGLISH.value == "en"
    assert language.ENGLISH_UK.value == "en-gb"
    # Bing uses 'jp' (not the ISO 'ja') for Japanese.
    assert language.JAPANESE.value == "jp"


def test_enum_values_are_unique():
    for enum_cls in (country, language):
        values = [m.value for m in enum_cls]
        assert len(values) == len(set(values)), f"duplicate value in {enum_cls.__name__}"
