"""
KeywordStats class for Bing Webmaster Tools Wrapper.

Maps to the GetKeywordStats endpoint, which powers the Keyword Research
tool in the Bing Webmaster Tools interface.

Returns historical weekly impression counts (broad match and strict match)
for a given keyword term, scoped by country and language.

This is a site-agnostic endpoint — results are not tied to a specific
verified property.  However, in the interest of a consistent API surface
that mirrors the GSC Wrapper, a WebProperty is accepted in the constructor
(so the same account flow is used) even though its URL is not sent to the
Bing API for this particular call.

Usage
-----
keyword_query = bwt_wrapper.KeywordStats(site)
report = await (
    keyword_query
    .keyword('seo tools')
    .country(bwt_wrapper.country.UNITED_STATES)
    .language(bwt_wrapper.language.ENGLISH_US)
    .get()
)
df = report.to_dataframe()
"""

from __future__ import annotations
import copy
from typing import cast
from .account import WebProperty
from .report import Report
from .schemas import KeywordRow
from .enumerations import country as CountryEnum, language as LanguageEnum


class KeywordStats:
    """
    Fluent builder for Bing keyword research data.

    Each row in the result represents one week of search volume and contains:
    Query, Date, Impressions (strict match), BroadImpressions (broad match).

    All three of keyword(), country(), and language() must be set before
    calling get() or execute().
    """

    def __init__(self, web_property: WebProperty) -> None:
        if not isinstance(web_property, WebProperty):
            raise TypeError(
                'Expected a WebProperty instance. '
                'Obtain one via account.webproperties() or account[n].'
            )
        self._property      = web_property
        self._keyword:  str | None = None
        self._country:  str | None = None
        self._language: str | None = None

    # ------------------------------------------------------------------
    # Fluent setters
    # ------------------------------------------------------------------

    def keyword(self, term: str) -> 'KeywordStats':
        """
        Set the keyword term to research.

        Parameters
        ----------
        term : the search term, e.g. 'seo tools'
        """
        if not term or not term.strip():
            raise ValueError('keyword term cannot be empty.')
        clone = copy.copy(self)
        clone._keyword = term.strip()
        return clone

    def country(self, code: CountryEnum | str) -> 'KeywordStats':
        """
        Set the country scope for the keyword research.

        Parameters
        ----------
        code : a bwt_wrapper.country enum member, or a raw lowercase
               ISO 3166-1 alpha-2 string, e.g. 'us'
        """
        clone = copy.copy(self)
        clone._country = str(code.value if isinstance(code, CountryEnum) else code).lower()
        return clone

    def language(self, tag: LanguageEnum | str) -> 'KeywordStats':
        """
        Set the language scope for the keyword research.

        Parameters
        ----------
        tag : a bwt_wrapper.language enum member, or a raw IETF BCP 47 tag,
              e.g. 'en-US'
        """
        clone = copy.copy(self)
        clone._language = str(tag.value if isinstance(tag, LanguageEnum) else tag)
        return clone

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(self) -> Report[KeywordRow]:
        """
        Fetch data from the API and return a Report.
        Requires keyword(), country(), and language() to have been set.
        """
        keyword, country, language = self._validate()
        rows = await self._property._api.get_keyword_stats(
            keyword=keyword,
            country_code=country,
            language_tag=language,
        )
        return Report(cast("list[KeywordRow]", rows))

    async def get(self) -> Report[KeywordRow]:
        """Primary method for retrieving keyword stats. Delegates to execute()."""
        return await self.execute()

    async def to_dataframe(self):
        """Shorthand for (await get()).to_dataframe()."""
        return (await self.get()).to_dataframe()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _validate(self) -> tuple[str, str, str]:
        """
        Ensure all required fields are set, returning them as a tuple of
        non-None strings so callers (and the type checker) can rely on them.
        """
        missing = []
        if not self._keyword:
            missing.append('keyword()')
        if not self._country:
            missing.append('country()')
        if not self._language:
            missing.append('language()')
        if missing:
            raise ValueError(
                f"The following must be set before calling get(): {', '.join(missing)}"
            )
        # The checks above guarantee these are set; assert narrows the types.
        assert self._keyword is not None
        assert self._country is not None
        assert self._language is not None
        return self._keyword, self._country, self._language

    def __repr__(self) -> str:
        return (
            f'<KeywordStats keyword={self._keyword!r} '
            f'country={self._country!r} language={self._language!r}>'
        )
