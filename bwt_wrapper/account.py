"""
Account and WebProperty classes for Bing Webmaster Tools Wrapper.

Mirrors the Account / WebProperty hierarchy in the GSC Wrapper.
Authentication is simpler here: no OAuth, just an API key.
"""

from __future__ import annotations

import os

from .api import BingApi
from .credentials import load_api_key


class WebProperty:
    """
    Represents a single verified website within a Bing Webmaster account.

    You rarely construct this directly.  Obtain instances from
    Account.webproperties() or by indexing an Account object.

    Attributes
    ----------
    url         : the site URL as registered in Bing Webmaster Tools
    is_verified : whether the site has been verified
    """

    def __init__(self, url: str, is_verified: bool, api: BingApi) -> None:
        self.url         = url
        self.is_verified = is_verified
        self._api        = api

    def __repr__(self) -> str:
        verified = '✓' if self.is_verified else '✗'
        return f'<WebProperty [{verified}] {self.url}>'

    def __str__(self) -> str:
        return self.url


class Account:
    """
    Entry point for the Bing Webmaster Tools Wrapper.

    Parameters
    ----------
    api_key : str, optional
        The API key from Bing Webmaster Tools → Settings → API Access.
        Only one key per user account is issued; it grants access to all
        verified sites owned by that account.
    credentials_file : str or path, optional
        Path to a TOML file containing the API key (default:
        ``credentials.toml`` in the current working directory).

    When *api_key* is omitted the key is loaded automatically from
    the credentials file.

    Usage
    -----
    # Option 1 – credentials file (recommended)
    account = Account()

    # Option 2 – explicit key
    account = Account(api_key='your_api_key')

    sites = account.webproperties()
    site  = account[0]
    site  = account['https://example.com']
    """

    def __init__(
        self,
        api_key: str | None = None,
        credentials_file: str | os.PathLike | None = None,
    ) -> None:
        if api_key is None:
            api_key = load_api_key(credentials_file)
        self._api        = BingApi(api_key)
        self._properties: list[WebProperty] | None = None

    # ------------------------------------------------------------------
    # Site discovery
    # ------------------------------------------------------------------

    def webproperties(self) -> list[WebProperty]:
        """
        Return all sites registered in the account.

        Results are cached for the lifetime of this Account object to
        avoid repeated API calls when accessing sites by index or URL.
        """
        if self._properties is None:
            self._properties = [
                WebProperty(
                    url=row.get('Url', ''),
                    is_verified=row.get('IsVerified', False),
                    api=self._api,
                )
                for row in self._api.get_sites()
            ]
        return self._properties

    # ------------------------------------------------------------------
    # Indexing  – mirrors GSC-Wrapper's account[0] / account['url']
    # ------------------------------------------------------------------

    def __getitem__(self, key: int | str) -> WebProperty:
        """
        Access a WebProperty by index (int) or by site URL (str).

        Examples
        --------
        site = account[0]
        site = account['https://example.com']
        """
        properties = self.webproperties()

        if isinstance(key, int):
            return properties[key]

        if isinstance(key, str):
            # Attempt exact match first, then a prefix/suffix comparison
            for prop in properties:
                if prop.url == key:
                    return prop
            # Fallback: case-insensitive, trailing-slash tolerant
            normalised = key.rstrip('/')
            for prop in properties:
                if prop.url.rstrip('/').lower() == normalised.lower():
                    return prop
            raise KeyError(f"No verified site found for '{key}'")

        raise TypeError(
            f'Account indices must be int or str, not {type(key).__name__}'
        )

    def __len__(self) -> int:
        return len(self.webproperties())

    def __iter__(self):
        return iter(self.webproperties())

    def __repr__(self) -> str:
        count = len(self.webproperties())
        return f'<Account sites={count}>'
