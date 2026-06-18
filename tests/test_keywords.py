"""
Tests for KeywordStats (bwt_wrapper.keywords).

Covers required-field validation, enum/raw-string coercion for country and
language, and the immutable fluent builder.
"""

import pytest

from bwt_wrapper.enumerations import country, language
from bwt_wrapper.keywords import KeywordStats
from bwt_wrapper.report import Report


def test_requires_webproperty():
    with pytest.raises(TypeError):
        KeywordStats("not-a-web-property")


def test_empty_keyword_raises(site):
    with pytest.raises(ValueError):
        KeywordStats(site).keyword("   ")


def test_get_without_required_fields_lists_what_is_missing(site):
    with pytest.raises(ValueError) as exc:
        KeywordStats(site).get()
    msg = str(exc.value)
    assert "keyword()" in msg
    assert "country()" in msg
    assert "language()" in msg


def test_fluent_chain_is_immutable(site):
    base = KeywordStats(site)
    chained = base.keyword("seo")
    assert base._keyword is None
    assert chained._keyword == "seo"


def test_enum_country_and_language_are_coerced(site, fake_api):
    fake_api.keyword_rows = [{"Query": "seo", "Impressions": 1, "BroadImpressions": 2}]
    report = (
        KeywordStats(site)
        .keyword("seo tools")
        .country(country.UNITED_STATES)
        .language(language.ENGLISH)
        .get()
    )
    assert isinstance(report, Report)
    assert fake_api.keyword_args == {
        "keyword": "seo tools",
        "country_code": "us",
        "language_tag": "en",
    }


def test_raw_string_country_is_lowercased(site, fake_api):
    KeywordStats(site).keyword("x").country("US").language("en").get()
    assert fake_api.keyword_args["country_code"] == "us"


def test_keyword_is_stripped(site, fake_api):
    KeywordStats(site).keyword("  spaced  ").country("us").language("en").get()
    assert fake_api.keyword_args["keyword"] == "spaced"


def test_repr_contains_state(site):
    r = repr(KeywordStats(site).keyword("seo").country("us").language("en"))
    assert "seo" in r and "us" in r and "en" in r
