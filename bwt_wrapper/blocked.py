"""
BlockedUrls class for Bing Webmaster Tools Wrapper.

Maps to the GetBlockedUrls / AddBlockedUrl / RemoveBlockedUrl endpoints
in the Bing Webmaster Tools API.

Blocked URL rules tell Bing to either remove the cached copy of a URL
or to stop showing it in search results entirely.

Usage
-----
blocked = bwt_wrapper.BlockedUrls(site)

# List all currently blocked URLs
report = blocked.get()
df = report.to_dataframe()

# Block a page (remove cache only)
from bwt_wrapper.enumerations import entity_type, request_type
blocked.add(
    url='https://example.com/old-page',
    entity_type=entity_type.PAGE,
    request_type=request_type.REMOVE_CACHE,
)

# Block an entire directory and disallow indexing
blocked.add(
    url='https://example.com/private/',
    entity_type=entity_type.DIRECTORY,
    request_type=request_type.DISALLOW,
)

# Remove a previously added rule
blocked.remove(
    url='https://example.com/old-page',
    entity_type=entity_type.PAGE,
    request_type=request_type.REMOVE_CACHE,
)
"""

from __future__ import annotations
from .account import WebProperty
from .report import Report
from .enumerations import entity_type as EntityType, request_type as RequestType


class BlockedUrls:
    """
    Manages the list of blocked URL rules for a single verified site.

    Parameters
    ----------
    web_property : a WebProperty instance obtained from Account
    """

    def __init__(self, web_property: WebProperty) -> None:
        if not isinstance(web_property, WebProperty):
            raise TypeError(
                'Expected a WebProperty instance. '
                'Obtain one via account.webproperties() or account[n].'
            )
        self._property = web_property

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self) -> Report:
        """
        Return all currently active blocked URL rules for the site.

        Each row contains: Url, EntityType, RequestType, Date.
        """
        rows = self._property._api.get_blocked_urls(self._property.url)
        return Report(rows)

    def to_dataframe(self):
        """Shorthand for get().to_dataframe()."""
        return self.get().to_dataframe()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add(
        self,
        url: str,
        entity_type: EntityType | int = EntityType.PAGE,
        request_type: RequestType | int = RequestType.REMOVE_CACHE,
    ) -> None:
        """
        Add a blocked URL rule.

        Parameters
        ----------
        url          : the exact page URL or directory prefix to block
        entity_type  : entity_type.PAGE (0) or entity_type.DIRECTORY (1)
        request_type : request_type.REMOVE_CACHE (0) removes the cached
                       copy; request_type.DISALLOW (1) prevents Bing from
                       showing the URL in search results at all
        """
        self._validate_url(url)
        self._property._api.add_blocked_url(
            site_url=self._property.url,
            url=url,
            entity_type=int(entity_type),
            request_type=int(request_type),
        )

    def remove(
        self,
        url: str,
        entity_type: EntityType | int = EntityType.PAGE,
        request_type: RequestType | int = RequestType.REMOVE_CACHE,
    ) -> None:
        """
        Remove a previously added blocked URL rule.

        Parameters mirror add().  All four fields must exactly match the
        rule that was originally submitted.
        """
        self._validate_url(url)
        self._property._api.remove_blocked_url(
            site_url=self._property.url,
            url=url,
            entity_type=int(entity_type),
            request_type=int(request_type),
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_url(url: str) -> None:
        if not url or not url.strip():
            raise ValueError('url cannot be empty.')
        if not url.startswith(('http://', 'https://')):
            raise ValueError(
                f"url must start with 'http://' or 'https://'. Got: '{url}'"
            )

    def __repr__(self) -> str:
        return f'<BlockedUrls site={self._property.url!r}>'
