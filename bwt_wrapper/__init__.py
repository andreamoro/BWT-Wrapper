"""
Bing Webmaster Tools Wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A package to take the pain out when working with the Bing Webmaster Tools API.
Modeled after the Google Search Console Wrapper by Andrea Moro.

Basic usage::

    import bwt_wrapper

    # Reads API key from credentials.toml automatically
    account = bwt_wrapper.Account()
    site_list = account.webproperties()
    site = account['https://example.com']

    # Query search performance by query
    query = bwt_wrapper.QueryStats(site)
    results = query.get()

    # Query search performance by page
    pages = bwt_wrapper.PageStats(site)
    results = pages.get()

    # Keyword research
    keywords = bwt_wrapper.KeywordStats(site)
    results = keywords.keyword('seo tools').country('us').language('en-US').get()

    # Blocked URLs management
    blocked = bwt_wrapper.BlockedUrls(site)
    all_blocked = blocked.get()

:license: GPL 3.0
"""

from .account import Account, WebProperty
from .query import QueryStats, PageStats
from .keywords import KeywordStats
from .blocked import BlockedUrls
from .report import Report
from . import enumerations
from .enumerations import country, language

__all__ = [
    'Account',
    'WebProperty',
    'QueryStats',
    'PageStats',
    'KeywordStats',
    'BlockedUrls',
    'Report',
    'enumerations',
    'country',
    'language',
]
