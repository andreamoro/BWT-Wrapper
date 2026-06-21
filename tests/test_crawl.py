"""
Tests for CrawlStats (bwt_wrapper.crawl).

Covers the WebProperty guard, that the correct endpoint/URL is used,
client-side date filtering (inclusive, string + date inputs), date
validation, and that crawl rows pass through untouched.
"""

import datetime

import pytest

from bwt_wrapper.crawl import CrawlStats
from bwt_wrapper.report import Report


@pytest.fixture
def crawl_rows():
    """
    Three daily crawl rows with native ``date`` objects, all in the past so
    date_range() bounds stay valid (it rejects future end dates).
    """
    return [
        {"Date": datetime.date(2026, 1, 4), "CrawledPages": 10, "CrawlErrors": 2, "InIndex": 100},
        {"Date": datetime.date(2026, 3, 7), "CrawledPages": 41, "CrawlErrors": 1, "InIndex": 264},
        {"Date": datetime.date(2026, 6, 15), "CrawledPages": 30, "CrawlErrors": 4, "InIndex": 300},
    ]


def test_requires_webproperty():
    with pytest.raises(TypeError):
        CrawlStats("not-a-web-property")


async def test_get_returns_report(site, fake_api, crawl_rows):
    fake_api.crawl_rows = crawl_rows
    report = await CrawlStats(site).get()
    assert isinstance(report, Report)
    assert len(report) == 3


async def test_fetch_uses_property_url(site, fake_api, crawl_rows):
    fake_api.crawl_rows = crawl_rows
    await CrawlStats(site).get()
    assert fake_api.crawl_site == "https://example.com"


async def test_rows_pass_through_untouched(site, fake_api, crawl_rows):
    fake_api.crawl_rows = crawl_rows
    rows = (await CrawlStats(site).get()).rows
    assert rows[0]["CrawledPages"] == 10
    assert rows[1]["InIndex"] == 264


async def test_date_range_filters_inclusive(site, fake_api, crawl_rows):
    fake_api.crawl_rows = crawl_rows
    report = await CrawlStats(site).date_range("2026-01-01", "2026-03-31").get()
    dates = [r["Date"] for r in report]
    assert datetime.date(2026, 1, 4) in dates
    assert datetime.date(2026, 3, 7) in dates
    assert datetime.date(2026, 6, 15) not in dates


async def test_date_range_accepts_date_objects(site, fake_api, crawl_rows):
    fake_api.crawl_rows = crawl_rows
    report = await CrawlStats(site).date_range(
        datetime.date(2026, 6, 1), datetime.date(2026, 6, 18)
    ).get()
    assert len(report) == 1


async def test_date_range_is_immutable(site):
    base = CrawlStats(site)
    ranged = base.date_range("2026-01-01", "2026-06-18")
    assert ranged is not base
    assert base._start_date is None
    assert ranged._start_date == datetime.date(2026, 1, 1)


def test_invalid_date_string_raises(site):
    with pytest.raises(ValueError):
        CrawlStats(site).date_range("01-01-2026", "2026-12-31")


def test_start_after_end_raises(site):
    with pytest.raises(ValueError):
        CrawlStats(site).date_range("2026-12-31", "2026-01-01")


def test_repr(site):
    assert "example.com" in repr(CrawlStats(site))
