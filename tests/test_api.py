"""
Tests for the low-level HTTP transport (bwt_wrapper.api).

Covers the pure helpers (date parsing, row normalisation), URL/param
building, the GET/POST plumbing, error handling, and the typed endpoint
methods — all without a real network connection.
"""

import datetime

import pytest

from bwt_wrapper.api import (
    BingApi,
    BingApiError,
    _normalise_row,
    _parse_bing_date,
)
from conftest import FakeResponse


# ----------------------------------------------------------------------
# Pure helpers
# ----------------------------------------------------------------------

def test_parse_bing_date_basic():
    # 1609459200000 ms == 2021-01-01 00:00:00 UTC
    assert _parse_bing_date("/Date(1609459200000)/") == datetime.date(2021, 1, 1)


def test_parse_bing_date_with_timezone_offset():
    assert _parse_bing_date("/Date(1609459200000-0800)/") == datetime.date(2021, 1, 1)


@pytest.mark.parametrize("value", ["", None, "not-a-date", "/Date()/"])
def test_parse_bing_date_returns_none_for_unparseable(value):
    assert _parse_bing_date(value) is None


def test_normalise_row_strips_type_and_converts_dates():
    row = {
        "__type": "QueryStats:#Microsoft.Bing.Webmaster.Api",
        "Date": "/Date(1609459200000)/",
        "Query": "widget",
    }
    out = _normalise_row(row)
    assert "__type" not in out
    assert out["Date"] == datetime.date(2021, 1, 1)
    assert out["Query"] == "widget"


# ----------------------------------------------------------------------
# Construction & URL building
# ----------------------------------------------------------------------

def test_empty_api_key_raises():
    with pytest.raises(ValueError):
        BingApi("")


def test_url_includes_base_method_and_apikey(api):
    url = api._url("GetUserSites")
    assert url.startswith("https://ssl.bing.com/webmaster/api.svc/json/GetUserSites?")
    assert "apikey=test-api-key" in url


def test_url_encodes_extra_params(api):
    url = api._url("GetQueryStats", {"siteUrl": "https://example.com/a b"})
    assert "siteUrl=https%3A%2F%2Fexample.com%2Fa+b" in url
    assert "apikey=test-api-key" in url


# ----------------------------------------------------------------------
# GET / POST plumbing
# ----------------------------------------------------------------------

async def test_get_returns_normalised_rows_from_d_node(api):
    api._client.get_response = FakeResponse(json_data={
        "d": [{"__type": "X", "Date": "/Date(1609459200000)/", "Query": "q"}]
    })
    rows = await api._get("GetQueryStats")
    assert rows == [{"Date": datetime.date(2021, 1, 1), "Query": "q"}]


@pytest.mark.parametrize("body", [{"d": None}, {}, {"d": []}])
async def test_get_handles_missing_or_null_d(api, body):
    api._client.get_response = FakeResponse(json_data=body)
    assert await api._get("GetUserSites") == []


async def test_get_passes_timeout_and_url(api):
    await api._get("GetUserSites")
    call = api._client.get_calls[-1]
    assert call["timeout"] == 30
    assert "GetUserSites" in call["url"]


async def test_post_returns_parsed_body(api):
    api._client.post_response = FakeResponse(json_data={"d": True})
    assert await api._post("AddBlockedUrl", {"x": 1}) == {"d": True}


async def test_post_returns_empty_dict_when_no_json_body(api):
    api._client.post_response = FakeResponse(raise_json=True)
    assert await api._post("AddBlockedUrl", {"x": 1}) == {}


# ----------------------------------------------------------------------
# Error handling
# ----------------------------------------------------------------------

async def test_non_200_raises_with_message(api):
    api._client.get_response = FakeResponse(status_code=401, json_data={"Message": "Bad key"})
    with pytest.raises(BingApiError) as exc:
        await api._get("GetUserSites")
    assert "401" in str(exc.value)
    assert "Bad key" in str(exc.value)


async def test_non_200_falls_back_to_text(api):
    api._client.get_response = FakeResponse(status_code=500, raise_json=True, text="Server boom")
    with pytest.raises(BingApiError) as exc:
        await api._get("GetUserSites")
    assert "Server boom" in str(exc.value)


# ----------------------------------------------------------------------
# Typed endpoint methods send the right method + params
# ----------------------------------------------------------------------

async def test_get_query_stats_sends_site_url(api):
    await api.get_query_stats("https://example.com")
    url = api._client.get_calls[-1]["url"]
    assert "GetQueryStats" in url and "siteUrl=https%3A%2F%2Fexample.com" in url


async def test_get_page_stats_sends_site_url(api):
    await api.get_page_stats("https://example.com")
    assert "GetPageStats" in api._client.get_calls[-1]["url"]


async def test_get_keyword_stats_sends_q_country_language(api):
    await api.get_keyword_stats("seo tools", "us", "en")
    url = api._client.get_calls[-1]["url"]
    assert "GetKeywordStats" in url
    assert "q=seo+tools" in url
    assert "country=us" in url
    assert "language=en" in url


async def test_add_blocked_url_posts_expected_payload(api):
    await api.add_blocked_url("https://example.com", "https://example.com/p", 0, 1)
    call = api._client.post_calls[-1]
    assert "AddBlockedUrl" in call["url"]
    payload = call["json"]
    assert payload["siteUrl"] == "https://example.com"
    blocked = payload["blockedUrl"]
    assert blocked["Url"] == "https://example.com/p"
    assert blocked["EntityType"] == 0
    assert blocked["RequestType"] == 1
    assert blocked["__type"].startswith("BlockedUrl:#")


async def test_remove_blocked_url_posts_expected_payload(api):
    await api.remove_blocked_url("https://example.com", "https://example.com/p", 1, 0)
    call = api._client.post_calls[-1]
    assert "RemoveBlockedUrl" in call["url"]
    assert call["json"]["blockedUrl"]["EntityType"] == 1
    assert call["json"]["blockedUrl"]["RequestType"] == 0
