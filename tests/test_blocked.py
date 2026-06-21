"""
Tests for BlockedUrls (bwt_wrapper.blocked).

Covers URL validation, enum-to-int coercion of entity/request types, and
that add/remove forward the right arguments to the transport layer.
"""

import pytest

from bwt_wrapper.blocked import BlockedUrls
from bwt_wrapper.enumerations import entity_type, request_type
from bwt_wrapper.report import Report


def test_requires_webproperty():
    with pytest.raises(TypeError):
        BlockedUrls("not-a-web-property")


async def test_get_returns_report(site, fake_api):
    fake_api.blocked_rows = [{"Url": "https://example.com/x", "EntityType": 0, "RequestType": 1}]
    report = await BlockedUrls(site).get()
    assert isinstance(report, Report)
    assert len(report) == 1
    assert fake_api.blocked_site == "https://example.com"


@pytest.mark.parametrize("bad_url", ["", "   ", "example.com", "ftp://example.com"])
async def test_add_rejects_invalid_url(site, bad_url):
    with pytest.raises(ValueError):
        await BlockedUrls(site).add(bad_url)


async def test_add_uses_defaults(site, fake_api):
    await BlockedUrls(site).add("https://example.com/old")
    assert fake_api.added == [
        ("https://example.com", "https://example.com/old", 0, 0)
    ]


async def test_add_coerces_enums_to_int(site, fake_api):
    await BlockedUrls(site).add(
        "https://example.com/dir/",
        entity_type=entity_type.DIRECTORY,
        request_type=request_type.DISALLOW,
    )
    site_url, url, et, rt = fake_api.added[-1]
    assert (et, rt) == (1, 1)
    assert isinstance(et, int) and isinstance(rt, int)


async def test_add_accepts_raw_ints(site, fake_api):
    await BlockedUrls(site).add("https://example.com/p", entity_type=1, request_type=0)
    assert fake_api.added[-1][2:] == (1, 0)


async def test_remove_forwards_arguments(site, fake_api):
    await BlockedUrls(site).remove(
        "https://example.com/old",
        entity_type=entity_type.PAGE,
        request_type=request_type.REMOVE_CACHE,
    )
    assert fake_api.removed == [
        ("https://example.com", "https://example.com/old", 0, 0)
    ]


async def test_remove_rejects_invalid_url(site):
    with pytest.raises(ValueError):
        await BlockedUrls(site).remove("not-a-url")


def test_repr(site):
    assert "example.com" in repr(BlockedUrls(site))
