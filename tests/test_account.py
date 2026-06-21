"""
Tests for Account and WebProperty (bwt_wrapper.account).

Focus on site discovery, caching, and the int/URL indexing behaviour that
mirrors the GSC Wrapper.
"""

import pytest

from bwt_wrapper.account import Account, WebProperty


@pytest.fixture
async def account(fake_api):
    """
    An Account whose transport is replaced with the FakeApi fixture, with its
    site list already loaded so synchronous indexing/len/iteration work.
    """
    acc = Account(api_key="test-key")
    acc._api = fake_api
    fake_api.sites = [
        {"Url": "https://example.com", "IsVerified": True},
        {"Url": "https://blog.example.com/", "IsVerified": False},
    ]
    await acc.webproperties()
    return acc


async def test_webproperties_returns_webproperty_objects(account):
    props = await account.webproperties()
    assert len(props) == 2
    assert all(isinstance(p, WebProperty) for p in props)
    assert props[0].url == "https://example.com"
    assert props[0].is_verified is True


async def test_webproperties_are_cached(account, fake_api):
    await account.webproperties()
    await account.webproperties()
    account[0]
    # Despite multiple accesses (incl. the fixture's load), the API is hit once.
    assert fake_api.get_sites_calls == 1


async def test_indexing_before_load_raises_runtimeerror(fake_api):
    acc = Account(api_key="test-key")
    acc._api = fake_api
    with pytest.raises(RuntimeError):
        acc[0]


async def test_index_by_int(account):
    assert account[1].url == "https://blog.example.com/"


async def test_index_by_exact_url(account):
    assert account["https://example.com"].is_verified is True


async def test_index_by_url_is_trailing_slash_and_case_insensitive(account):
    # Stored as 'https://blog.example.com/' — look it up without the slash
    # and with different casing.
    assert account["HTTPS://BLOG.EXAMPLE.COM"].url == "https://blog.example.com/"


async def test_unknown_url_raises_keyerror(account):
    with pytest.raises(KeyError):
        account["https://missing.example.com"]


async def test_invalid_index_type_raises_typeerror(account):
    with pytest.raises(TypeError):
        account[1.5]


async def test_len_and_iter(account):
    assert len(account) == 2
    urls = [p.url for p in account]
    assert urls == ["https://example.com", "https://blog.example.com/"]


async def test_account_repr(account):
    assert "sites=2" in repr(account)


def test_webproperty_repr_and_str():
    verified = WebProperty("https://a.com", True, api=None)
    unverified = WebProperty("https://b.com", False, api=None)
    assert "✓" in repr(verified)
    assert "✗" in repr(unverified)
    assert str(verified) == "https://a.com"
