"""
Typed row schemas for the data returned by each Bing endpoint.

These are ``TypedDict``s: at runtime every row is still a plain ``dict`` — so
DataFrame export, pickling, and ``row['Clicks']`` access are completely
unchanged — but static type checkers and editors gain full knowledge of each
row's keys and their value types.  They exist purely for static analysis;
nothing in this module executes any logic.

The wrapper returns rows already normalised by ``api.py`` and the stats
builders: the ``/Date(...)/`` strings are parsed to ``datetime.date``, the
``__type`` field is stripped, positions are divided by 10, and ``Ctr`` is
computed.  The types below describe rows in that post-normalisation shape.
"""

from __future__ import annotations

import datetime
from typing import TypedDict


class StatsRow(TypedDict):
    """
    One (term-or-URL, week) row from GetQueryStats / GetPageStats.

    QueryStats and PageStats share an identical shape; the only difference is
    that ``Query`` holds a search term for QueryStats and a page URL for
    PageStats.  ``QueryRow`` / ``PageRow`` below name that distinction.
    """
    Query: str
    Date: datetime.date | None
    Clicks: int
    Impressions: int
    AvgClickPosition: float       # already divided by 10 to match the Bing UI
    AvgImpressionPosition: float  # already divided by 10 to match the Bing UI
    Ctr: float                    # computed by the wrapper as Clicks / Impressions


class QueryRow(StatsRow):
    """A weekly query-level row; ``Query`` holds the search term."""


class PageRow(StatsRow):
    """A weekly page-level row; ``Query`` holds the page URL."""


class KeywordRow(TypedDict):
    """One weekly row from GetKeywordStats (keyword research)."""
    Query: str
    Date: datetime.date | None
    Impressions: int          # strict-match impressions
    BroadImpressions: int     # broad-match impressions


class BlockedRow(TypedDict):
    """One blocked-URL rule from GetBlockedUrls."""
    Url: str
    EntityType: int           # 0 = page, 1 = directory
    RequestType: int          # 0 = remove cache, 1 = disallow
    Date: datetime.date | None


class CrawlRow(TypedDict):
    """
    One day of crawl and index statistics from GetCrawlStats.

    Crawl stats are daily (one row per calendar date), unlike the weekly
    search-performance endpoints.  Alongside the headline crawl/index counts,
    Bing breaks crawl responses down by HTTP status code and failure mode.
    """
    Date: datetime.date | None
    CrawledPages: int          # pages Bing crawled that day
    CrawlErrors: int           # crawl errors encountered
    InIndex: int               # pages in the Bing index
    InLinks: int               # inbound links discovered
    BlockedByRobotsTxt: int    # pages blocked by robots.txt
    ContainsMalware: int       # pages flagged as containing malware
    Code2xx: int               # successful responses
    Code301: int               # permanent redirects
    Code302: int               # temporary redirects
    Code4xx: int               # client errors (e.g. 404)
    Code5xx: int               # server errors
    AllOtherCodes: int         # any other HTTP status
    ConnectionTimeout: int     # connection timeouts
    DnsFailures: int           # DNS resolution failures
