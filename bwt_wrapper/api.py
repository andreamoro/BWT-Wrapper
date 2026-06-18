"""
Low-level HTTP transport for the Bing Webmaster Tools API.

All API communication is centralised here so the higher-level classes
never deal with raw HTTP, JSON parsing, or the odd /Date(timestamp)/
date format that Bing returns.

The Bing API base URL is:
    https://ssl.bing.com/webmaster/api.svc/json/{METHOD}?apikey={KEY}

Authentication is via a plain API key appended to every request.
No OAuth flow is needed.
"""

import re
import datetime
from urllib.parse import urlencode, quote_plus

import requests


_BASE_URL = 'https://ssl.bing.com/webmaster/api.svc/json'
_DATE_RE  = re.compile(r'/Date\((-?\d+)([+-]\d{4})?\)/')


def _parse_bing_date(value: str) -> datetime.date | None:
    """
    Convert the /Date(milliseconds)/ format returned by Bing into a
    Python date.  Returns None when the value cannot be parsed rather
    than raising an exception, so callers can decide how to handle it.
    """
    if not value:
        return None
    m = _DATE_RE.search(value)
    if not m:
        return None
    ms = int(m.group(1))
    # Bing timestamps are UTC milliseconds; build a timezone-aware UTC
    # datetime (utcfromtimestamp() is deprecated for removal) and take the date.
    return datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).date()


def _normalise_row(row: dict) -> dict:
    """
    Strip the __type field added by Bing's WCF serialiser and convert
    all /Date(...)/ values to Python date objects in-place.
    """
    row.pop('__type', None)
    for key, value in row.items():
        if isinstance(value, str) and _DATE_RE.search(value):
            row[key] = _parse_bing_date(value)
    return row


class BingApiError(Exception):
    """Raised when the Bing API returns a non-200 status or an error body."""
    pass


class BingApi:
    """
    Thin wrapper around the Bing Webmaster Tools JSON API.

    Parameters
    ----------
    api_key : str
        The API key generated in Bing Webmaster Tools → Settings → API Access.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError('An API key is required.')
        self._api_key = api_key
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json; charset=utf-8',
        })

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, method: str, extra_params: dict | None = None) -> str:
        """Build the full endpoint URL with the API key."""
        params = {'apikey': self._api_key}
        if extra_params:
            params.update(extra_params)
        return f'{_BASE_URL}/{method}?{urlencode(params, quote_via=quote_plus)}'

    def _get(self, method: str, params: dict | None = None) -> list[dict]:
        """
        Perform a GET request and return the normalised list from the 'd' node.
        """
        url = self._url(method, params)
        response = self._session.get(url, timeout=30)
        self._raise_for_error(response)
        data = response.json()
        rows = data.get('d', []) or []
        return [_normalise_row(row) for row in rows]

    def _post(self, method: str, payload: dict) -> dict:
        """
        Perform a POST request with a JSON body.
        Returns the parsed response body.
        """
        url = self._url(method)
        response = self._session.post(url, json=payload, timeout=30)
        self._raise_for_error(response)
        # Some POST endpoints return nothing useful in the body
        try:
            return response.json()
        except Exception:
            return {}

    @staticmethod
    def _raise_for_error(response: requests.Response) -> None:
        if response.status_code == 200:
            return
        try:
            body = response.json()
            message = body.get('Message') or body.get('d') or response.text
        except Exception:
            message = response.text
        raise BingApiError(
            f'Bing API returned HTTP {response.status_code}: {message}'
        )

    # ------------------------------------------------------------------
    # Site management
    # ------------------------------------------------------------------

    def get_sites(self) -> list[dict]:
        """Return all sites registered in the account."""
        return self._get('GetUserSites')

    # ------------------------------------------------------------------
    # Search performance
    # ------------------------------------------------------------------

    def get_query_stats(self, site_url: str) -> list[dict]:
        """
        Return weekly query-level performance stats for the given site.
        Maps to the Search Performance → Top Queries view in the UI.
        """
        return self._get('GetQueryStats', {'siteUrl': site_url})

    def get_page_stats(self, site_url: str) -> list[dict]:
        """
        Return weekly page-level performance stats for the given site.
        Maps to the Search Performance → Top Pages view in the UI.
        """
        return self._get('GetPageStats', {'siteUrl': site_url})

    # ------------------------------------------------------------------
    # Keyword research
    # ------------------------------------------------------------------

    def get_keyword_stats(
        self,
        keyword: str,
        country_code: str,
        language_tag: str,
    ) -> list[dict]:
        """
        Return historical weekly impression data (broad + strict match) for a
        given keyword, country and language combination.

        Parameters
        ----------
        keyword      : the search term to analyse (URL-encoding is handled here)
        country_code : lowercase ISO 3166-1 alpha-2 code, e.g. 'us'
        language_tag : IETF BCP 47 tag, e.g. 'en-US'
        """
        return self._get('GetKeywordStats', {
            'q':        keyword,
            'country':  country_code,
            'language': language_tag,
        })

    # ------------------------------------------------------------------
    # Blocked URLs
    # ------------------------------------------------------------------

    def get_blocked_urls(self, site_url: str) -> list[dict]:
        """Return all blocked URL rules for the given site."""
        return self._get('GetBlockedUrls', {'siteUrl': site_url})

    def add_blocked_url(
        self,
        site_url: str,
        url: str,
        entity_type: int,
        request_type: int,
    ) -> None:
        """
        Add a blocked URL rule.

        Parameters
        ----------
        site_url     : the verified site URL, e.g. 'https://example.com'
        url          : the URL or URL prefix to block
        entity_type  : 0 = page, 1 = directory
        request_type : 0 = remove cache, 1 = disallow
        """
        self._post('AddBlockedUrl', {
            'siteUrl': site_url,
            'blockedUrl': {
                '__type':      'BlockedUrl:#Microsoft.Bing.Webmaster.Api',
                'Date':        '/Date(-62135568000000-0800)/',
                'EntityType':  entity_type,
                'RequestType': request_type,
                'Url':         url,
            },
        })

    def remove_blocked_url(
        self,
        site_url: str,
        url: str,
        entity_type: int,
        request_type: int,
    ) -> None:
        """
        Remove a previously added blocked URL rule.

        Parameters mirror add_blocked_url().
        """
        self._post('RemoveBlockedUrl', {
            'siteUrl': site_url,
            'blockedUrl': {
                '__type':      'BlockedUrl:#Microsoft.Bing.Webmaster.Api',
                'Date':        '/Date(-62135568000000-0800)/',
                'EntityType':  entity_type,
                'RequestType': request_type,
                'Url':         url,
            },
        })
