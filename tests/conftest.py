"""
Shared pytest fixtures and test doubles for the BWT Wrapper suite.

The whole suite is offline and deterministic: nothing here ever touches the
network. Two layers of fakes are provided:

* ``FakeSession`` / ``FakeResponse`` — drop-in replacements for the
  ``requests`` session used by ``BingApi``. These exercise the low-level
  HTTP transport (URL building, JSON/date parsing, error handling) without a
  real socket.
* ``FakeApi`` — a stand-in for ``BingApi`` used by the higher-level classes
  (Account, QueryStats, BlockedUrls, …) so their logic can be tested in
  isolation from the transport layer.
"""

from __future__ import annotations

import copy
import datetime
import sys
from pathlib import Path

import pytest

# Make the package importable when the suite is run from a checkout that has
# not been ``pip install``-ed (mirrors how live_check.py bootstraps itself).
sys.path.insert(0, str(Path(__file__).parent.parent))

from bwt_wrapper.account import WebProperty  # noqa: E402
from bwt_wrapper.api import BingApi  # noqa: E402


# ----------------------------------------------------------------------
# Transport-level doubles (used by test_api.py)
# ----------------------------------------------------------------------

class FakeResponse:
    """Minimal stand-in for ``requests.Response``."""

    def __init__(self, status_code=200, json_data=None, text="", raise_json=False):
        self.status_code = status_code
        self._json_data = {} if json_data is None else json_data
        self.text = text
        # When True, .json() raises — mimics an empty/non-JSON body.
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("No JSON body")
        return self._json_data


class FakeSession:
    """
    Records every request and returns pre-seeded responses.

    Set ``get_response`` / ``post_response`` to control what the next call
    returns; inspect ``get_calls`` / ``post_calls`` to assert on what was sent.
    """

    def __init__(self):
        self.headers = {}
        self.get_calls = []
        self.post_calls = []
        self.get_response = FakeResponse(json_data={"d": []})
        self.post_response = FakeResponse(json_data={"d": True})

    def get(self, url, timeout=None):
        self.get_calls.append({"url": url, "timeout": timeout})
        return self.get_response

    def post(self, url, json=None, timeout=None):
        self.post_calls.append({"url": url, "json": json, "timeout": timeout})
        return self.post_response


@pytest.fixture
def api():
    """A ``BingApi`` whose network session is replaced with a ``FakeSession``."""
    instance = BingApi("test-api-key")
    instance._session = FakeSession()
    return instance


# ----------------------------------------------------------------------
# Service-level double (used by Account / Stats / Blocked / Keyword tests)
# ----------------------------------------------------------------------

class FakeApi:
    """
    Stand-in for ``BingApi`` exposing the same public methods the high-level
    classes call. Getters return deep copies so tests cannot accidentally
    mutate the canned data (this also mirrors the real API, which hands back
    fresh objects on every call).
    """

    def __init__(self):
        self.sites: list[dict] = []
        self.query_rows: list[dict] = []
        self.page_rows: list[dict] = []
        self.keyword_rows: list[dict] = []
        self.blocked_rows: list[dict] = []

        # Call recorders for write/read assertions.
        self.get_sites_calls = 0
        self.keyword_args = None
        self.added = []
        self.removed = []

    def get_sites(self):
        self.get_sites_calls += 1
        return copy.deepcopy(self.sites)

    def get_query_stats(self, site_url):
        self.query_site = site_url
        return copy.deepcopy(self.query_rows)

    def get_page_stats(self, site_url):
        self.page_site = site_url
        return copy.deepcopy(self.page_rows)

    def get_keyword_stats(self, keyword, country_code, language_tag):
        self.keyword_args = {
            "keyword": keyword,
            "country_code": country_code,
            "language_tag": language_tag,
        }
        return copy.deepcopy(self.keyword_rows)

    def get_blocked_urls(self, site_url):
        self.blocked_site = site_url
        return copy.deepcopy(self.blocked_rows)

    def add_blocked_url(self, site_url, url, entity_type, request_type):
        self.added.append((site_url, url, entity_type, request_type))

    def remove_blocked_url(self, site_url, url, entity_type, request_type):
        self.removed.append((site_url, url, entity_type, request_type))


@pytest.fixture
def fake_api():
    """A fresh ``FakeApi`` per test."""
    return FakeApi()


@pytest.fixture
def site(fake_api):
    """A ``WebProperty`` wired to the ``fake_api`` fixture."""
    return WebProperty("https://example.com", True, fake_api)


@pytest.fixture
def query_rows():
    """
    Three weekly query rows with native ``date`` objects and Bing's ×10
    positions, suitable for filter and normalisation assertions.
    """
    return [
        {
            "Query": "alpha widget",
            "Date": datetime.date(2025, 1, 4),
            "Clicks": 10,
            "Impressions": 100,
            "AvgClickPosition": 35,        # 3.5 after normalisation
            "AvgImpressionPosition": 50,   # 5.0 after normalisation
        },
        {
            "Query": "beta gadget",
            "Date": datetime.date(2025, 6, 7),
            "Clicks": 5,
            "Impressions": 80,
            "AvgClickPosition": 12,        # 1.2
            "AvgImpressionPosition": 20,   # 2.0
        },
        {
            "Query": "alpha gizmo",
            "Date": datetime.date(2025, 11, 1),
            "Clicks": 1,
            "Impressions": 9,
            "AvgClickPosition": 99,        # 9.9
            "AvgImpressionPosition": 100,  # 10.0
        },
    ]
