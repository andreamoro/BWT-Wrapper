"""
Bing Webmaster Tools Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A package to take the pain out when working with the Bing Webmaster Tools API.
Modeled after the Google Search Console Wrapper by Andrea Moro.

This is an async library built on httpx + asyncio, with client-side rate
limiting (aiolimiter) so you can safely fan requests out with
``asyncio.gather``.  Every network call is a coroutine and must be awaited.

Basic usage::

    import asyncio
    import bwt_wrapper

    async def main():
        # Reads API key from credentials.toml automatically.
        # Use as an async context manager so the HTTP client is closed cleanly.
        async with bwt_wrapper.Account() as account:
            site_list = await account.webproperties()
            site = account['https://example.com']

            # Query search performance by query
            query = bwt_wrapper.QueryStats(site)
            results = await query.get()

            # Query search performance by page
            pages = bwt_wrapper.PageStats(site)
            results = await pages.get()

            # Keyword research
            keywords = bwt_wrapper.KeywordStats(site)
            results = await keywords.keyword('seo tools').country('us').language('en-US').get()

            # Blocked URLs management
            blocked = bwt_wrapper.BlockedUrls(site)
            all_blocked = await blocked.get()

    asyncio.run(main())

:license: GPL 3.0
"""

from .account import Account, WebProperty
from .query import QueryStats, PageStats
from .keywords import KeywordStats
from .blocked import BlockedUrls
from .crawl import CrawlStats
from .report import Report
from . import enumerations
from .enumerations import country, language
from .schemas import StatsRow, QueryRow, PageRow, KeywordRow, BlockedRow, CrawlRow

__all__ = [
    'Account',
    'WebProperty',
    'QueryStats',
    'PageStats',
    'KeywordStats',
    'BlockedUrls',
    'CrawlStats',
    'Report',
    'enumerations',
    'country',
    'language',
    'StatsRow',
    'QueryRow',
    'PageRow',
    'KeywordRow',
    'BlockedRow',
    'CrawlRow',
]
