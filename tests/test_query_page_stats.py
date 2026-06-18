"""
Tests for QueryStats / PageStats (bwt_wrapper.query).

Covers the fluent (immutable) builder pattern, client-side date and
substring filtering, position normalisation, and date validation.
"""

import datetime

import pytest

from bwt_wrapper.query import PageStats, QueryStats
from bwt_wrapper.report import Report


def test_requires_webproperty():
    with pytest.raises(TypeError):
        QueryStats("not-a-web-property")


def test_fluent_methods_return_new_clones_without_mutating_original(site):
    base = QueryStats(site)
    ranged = base.date_range("2025-01-01", "2025-12-31")
    filtered = base.filter_query("alpha")

    assert ranged is not base
    assert filtered is not base
    # Original remains pristine.
    assert base._start_date is None
    assert base._filters == []
    # Clones carry only their own state.
    assert ranged._start_date == datetime.date(2025, 1, 1)
    assert filtered._filters[0]["value"] == "alpha"


def test_get_returns_report(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    report = QueryStats(site).get()
    assert isinstance(report, Report)
    assert len(report) == 3


def test_fetch_uses_property_url(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    QueryStats(site).get()
    assert fake_api.query_site == "https://example.com"


def test_positions_are_divided_by_ten(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    rows = QueryStats(site).get().rows
    assert rows[0]["AvgClickPosition"] == 3.5
    assert rows[0]["AvgImpressionPosition"] == 5.0


def test_date_range_filters_inclusive(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    report = QueryStats(site).date_range("2025-01-01", "2025-06-30").get()
    dates = [r["Date"] for r in report]
    assert datetime.date(2025, 1, 4) in dates
    assert datetime.date(2025, 6, 7) in dates
    assert datetime.date(2025, 11, 1) not in dates


def test_date_range_accepts_date_objects(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    report = QueryStats(site).date_range(
        datetime.date(2025, 6, 1), datetime.date(2025, 6, 30)
    ).get()
    assert len(report) == 1


def test_filter_query_substring(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    report = QueryStats(site).filter_query("alpha").get()
    queries = {r["Query"] for r in report}
    assert queries == {"alpha widget", "alpha gizmo"}


def test_filter_query_exact_match(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    report = QueryStats(site).filter_query("alpha widget", contains=False).get()
    assert len(report) == 1
    assert report.rows[0]["Query"] == "alpha widget"


def test_filters_compose(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    report = (
        QueryStats(site)
        .filter_query("alpha")
        .date_range("2025-01-01", "2025-06-30")
        .get()
    )
    assert len(report) == 1
    assert report.rows[0]["Query"] == "alpha widget"


def test_get_and_execute_are_equivalent(site, fake_api, query_rows):
    fake_api.query_rows = query_rows
    stats = QueryStats(site).date_range("2025-01-01", "2025-06-30")
    assert len(stats.get()) == len(stats.execute())


# --- date validation -------------------------------------------------

def test_invalid_date_string_raises(site):
    with pytest.raises(ValueError):
        QueryStats(site).date_range("01-01-2025", "2025-12-31")


def test_start_after_end_raises(site):
    with pytest.raises(ValueError):
        QueryStats(site).date_range("2025-12-31", "2025-01-01")


def test_future_end_date_raises(site):
    with pytest.raises(ValueError):
        QueryStats(site).date_range("2025-01-01", "2999-01-01")


def test_start_before_minimum_raises(site):
    with pytest.raises(ValueError):
        QueryStats(site).date_range("1999-01-01", "2025-01-01")


# --- PageStats -------------------------------------------------------

def test_pagestats_uses_page_endpoint(site, fake_api):
    fake_api.page_rows = [{"Query": "https://example.com/blog/x", "Date": datetime.date(2025, 1, 1)}]
    report = PageStats(site).get()
    assert fake_api.page_site == "https://example.com"
    assert len(report) == 1


def test_pagestats_filter_on_url(site, fake_api):
    fake_api.page_rows = [
        {"Query": "https://example.com/blog/x", "Date": datetime.date(2025, 1, 1)},
        {"Query": "https://example.com/shop/y", "Date": datetime.date(2025, 1, 1)},
    ]
    report = PageStats(site).filter_query("/blog/").get()
    assert len(report) == 1
    assert "/blog/" in report.rows[0]["Query"]
