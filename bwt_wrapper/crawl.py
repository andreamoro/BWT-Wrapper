"""
CrawlStats class for Bing Webmaster Tools Wrapper.

Maps to the GetCrawlStats endpoint — the data behind the Crawl Information /
site-overview view in the Bing Webmaster Tools UI.

Returns one row per day with crawl and index counts (crawled pages, crawl
errors, pages in index, inbound links) plus an HTTP status-code breakdown.
Unlike the search-performance endpoints (QueryStats / PageStats), which bucket
data weekly, crawl stats are daily.

Bing returns the full available history in a single call, so date_range()
filtering is applied client-side — mirroring QueryStats / PageStats.

Usage
-----
crawl = bwt_wrapper.CrawlStats(site)
report = await crawl.date_range('2026-01-01', '2026-01-31').get()
df = report.to_dataframe()
"""

from __future__ import annotations
import datetime
import copy
from typing import Self, cast
from .account import WebProperty
from .report import Report
from .schemas import CrawlRow
from .query import _parse_date, _validate_date_range


class CrawlStats:
    """
    Fluent builder for Bing daily crawl and index statistics.

    Maps to GetCrawlStats → Crawl Information in the UI.

    Each row represents one (site, day) combination and contains: Date,
    CrawledPages, CrawlErrors, InIndex, InLinks, BlockedByRobotsTxt,
    ContainsMalware, Code2xx, Code301, Code302, Code4xx, Code5xx,
    AllOtherCodes, ConnectionTimeout, DnsFailures.
    """

    def __init__(self, web_property: WebProperty) -> None:
        if not isinstance(web_property, WebProperty):
            raise TypeError(
                'Expected a WebProperty instance. '
                'Obtain one via account.webproperties() or account[n].'
            )
        self._property   = web_property
        self._start_date: datetime.date | None = None
        self._end_date:   datetime.date | None = None

    # ------------------------------------------------------------------
    # Fluent setters – each returns a clone to allow method chaining
    # ------------------------------------------------------------------

    def date_range(
        self,
        start: str | datetime.date,
        end:   str | datetime.date,
    ) -> Self:
        """
        Restrict results to days whose Date falls within [start, end].

        Filtering is applied client-side because Bing returns the full crawl
        history for this endpoint.

        Parameters
        ----------
        start : 'YYYY-MM-DD' string or datetime.date
        end   : 'YYYY-MM-DD' string or datetime.date
        """
        clone = copy.copy(self)
        clone._start_date = _parse_date(start)
        clone._end_date   = _parse_date(end)
        _validate_date_range(clone._start_date, clone._end_date)
        return clone

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(self) -> Report[CrawlRow]:
        """
        Fetch data from the API, apply any date filter, and return a Report.
        """
        rows = await self._property._api.get_crawl_stats(self._property.url)
        return Report(cast("list[CrawlRow]", self._apply_date_filter(rows)))

    async def get(self) -> Report[CrawlRow]:
        """Primary method for retrieving crawl stats. Delegates to execute()."""
        return await self.execute()

    async def to_dataframe(self):
        """Shorthand for (await get()).to_dataframe()."""
        return (await self.get()).to_dataframe()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _apply_date_filter(self, rows: list[dict]) -> list[dict]:
        result = rows
        if self._start_date is not None:
            result = [
                r for r in result
                if isinstance(r.get('Date'), datetime.date)
                and r['Date'] >= self._start_date
            ]
        if self._end_date is not None:
            result = [
                r for r in result
                if isinstance(r.get('Date'), datetime.date)
                and r['Date'] <= self._end_date
            ]
        return result

    def __repr__(self) -> str:
        return f'<CrawlStats site={self._property.url!r}>'
