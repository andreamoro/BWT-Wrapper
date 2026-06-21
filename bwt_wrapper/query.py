"""
QueryStats and PageStats classes for Bing Webmaster Tools Wrapper.

Both classes expose a fluent interface that mirrors the Query class in the
GSC Wrapper.  Because the Bing API does not support date range or dimension
filtering server-side on these endpoints (you always get the full dataset),
filtering is applied client-side after retrieval.

Bing returns data in weekly buckets (each row represents a Saturday or Friday
depending on the endpoint), so client-side date filtering is the only way to
scope results to a specific window.

Key differences from GSC:
- No server-side dimension grouping (query+page+country+device in one call).
- No regex, contains, or operator filters.
- Positions are stored as integers (x10 by Bing); they are divided by 10
  here to match the decimal format GSC users are familiar with.
"""

from __future__ import annotations
import datetime
import copy
from typing import Generic, Self, TypeVar, cast
from .account import WebProperty
from .report import Report
from .schemas import QueryRow, PageRow


_MIN_DATE = datetime.date(2000, 1, 1)

# The row type produced by a concrete stats builder (QueryRow / PageRow).
RowT = TypeVar("RowT")


def _today() -> datetime.date:
    # Timezone-aware UTC "today" (utcnow() is deprecated for removal).
    return datetime.datetime.now(datetime.UTC).date()


class _BaseStats(Generic[RowT]):
    """Shared logic between QueryStats and PageStats."""

    def __init__(self, web_property: WebProperty) -> None:
        if not isinstance(web_property, WebProperty):
            raise TypeError(
                'Expected a WebProperty instance. '
                'Obtain one via account.webproperties() or account[n].'
            )
        self._property     = web_property
        self._start_date: datetime.date | None = None
        self._end_date:   datetime.date | None = None
        self._filters:    list[dict]           = []

    # ------------------------------------------------------------------
    # Fluent setters – each returns self to allow method chaining
    # ------------------------------------------------------------------

    def date_range(
        self,
        start: str | datetime.date,
        end:   str | datetime.date,
    ) -> Self:
        """
        Restrict results to rows whose Date falls within [start, end].

        Filtering is applied client-side because Bing's API always returns
        the full dataset for these endpoints.

        Parameters
        ----------
        start : 'YYYY-MM-DD' string or datetime.date
        end   : 'YYYY-MM-DD' string or datetime.date
        """
        clone = copy.copy(self)
        clone._start_date = _parse_date(start)
        clone._end_date   = _parse_date(end)
        _validate_date_range(clone._start_date, clone._end_date)
        return clone

    def filter_query(self, value: str, contains: bool = True) -> Self:
        """
        Filter rows by the Query field (which holds the search term in
        QueryStats, or the page URL in PageStats).

        Parameters
        ----------
        value    : the string to match against
        contains : True (default) for a substring match; False for exact match
        """
        clone = copy.copy(self)
        clone._filters = list(self._filters) + [{
            'field':    'Query',
            'value':    value,
            'contains': contains,
        }]
        return clone

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(self) -> Report[RowT]:
        """
        Fetch data from the API and return a Report without any additional
        processing.  Equivalent to get() but returns only what the API
        sends back.  Positions are still normalised (divided by 10).
        """
        raw = await self._fetch()
        # Rows are built dynamically as plain dicts; cast to the concrete row
        # type (QueryRow / PageRow) bound by the subclass for the caller.
        return Report(cast("list[RowT]", self._apply_filters(raw)))

    async def get(self) -> Report[RowT]:
        """
        Fetch data, apply all configured filters, and return a Report.
        This is the primary method for retrieving data.
        """
        return await self.execute()

    async def to_dataframe(self):
        """Shorthand for (await get()).to_dataframe()."""
        return (await self.get()).to_dataframe()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _fetch(self) -> list[dict]:
        raise NotImplementedError

    def _apply_filters(self, rows: list[dict]) -> list[dict]:
        result = rows

        # Date range filter
        if self._start_date is not None:
            result = [
                r for r in result
                if isinstance(r.get('Date'), datetime.date)
                and r['Date'] >= self._start_date
            ]
        if self._end_date is not None:
            result = [
                r for r in result
                if isinstance(r.get('Date'), datetime.date)
                and r['Date'] <= self._end_date
            ]

        # Query/URL substring or exact filters
        for f in self._filters:
            field = f['field']
            value = f['value'].lower()
            if f['contains']:
                result = [
                    r for r in result
                    if value in str(r.get(field, '')).lower()
                ]
            else:
                result = [
                    r for r in result
                    if str(r.get(field, '')).lower() == value
                ]

        return result

    @staticmethod
    def _normalise_positions(row: dict) -> dict:
        """
        Bing stores average positions as integers multiplied by 10.
        Divide here so the data matches what users see in the UI.
        """
        for field in ('AvgClickPosition', 'AvgImpressionPosition'):
            if field in row and isinstance(row[field], (int, float)):
                row[field] = row[field] / 10
        return row

    @staticmethod
    def _add_ctr(row: dict) -> dict:
        """
        Add a computed click-through-rate ('Ctr') field.

        Bing returns Clicks and Impressions but, unlike Google Search Console,
        no CTR. Computing it here saves every caller from deriving it. The
        value is a 0–1 ratio (e.g. 0.125 == 12.5%) rounded to 4 decimals; rows
        with zero impressions get a CTR of 0.0 to avoid division by zero. Rows
        missing either field are left untouched.
        """
        clicks = row.get('Clicks')
        impressions = row.get('Impressions')
        if isinstance(clicks, (int, float)) and isinstance(impressions, (int, float)):
            row['Ctr'] = round(clicks / impressions, 4) if impressions else 0.0
        return row


class QueryStats(_BaseStats[QueryRow]):
    """
    Fluent builder for Bing query-level search performance data.

    Maps to GetQueryStats → Search Performance → Top Queries in the UI.

    Each row in the result represents one (query, week) combination and
    contains: Query, Date, Clicks, Impressions, AvgClickPosition,
    AvgImpressionPosition, and Ctr (click-through rate, computed by this
    wrapper as Clicks / Impressions).

    Usage
    -----
    query = QueryStats(site)
    report = await query.date_range('2025-11-01', '2025-11-30').get()
    df = report.to_dataframe()
    """

    async def _fetch(self) -> list[dict]:
        rows = await self._property._api.get_query_stats(self._property.url)
        return [self._add_ctr(self._normalise_positions(row)) for row in rows]


class PageStats(_BaseStats[PageRow]):
    """
    Fluent builder for Bing page-level search performance data.

    Maps to GetPageStats → Search Performance → Top Pages in the UI.

    Each row in the result represents one (page URL, week) combination.
    The Query field in the response holds the page URL.

    Usage
    -----
    pages = PageStats(site)
    report = await pages.filter_query('/blog/').date_range('2025-01-01', '2025-12-31').get()
    df = report.to_dataframe()
    """

    async def _fetch(self) -> list[dict]:
        rows = await self._property._api.get_page_stats(self._property.url)
        return [self._add_ctr(self._normalise_positions(row)) for row in rows]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_date(value: str | datetime.date) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        raise ValueError(
            f"Invalid date '{value}'. Expected 'YYYY-MM-DD' format."
        )


def _validate_date_range(
    start: datetime.date,
    end:   datetime.date,
) -> None:
    if start > end:
        raise ValueError(
            f'start_date ({start}) must be earlier than end_date ({end}).'
        )
    if end > _today():
        raise ValueError(
            f'end_date ({end}) cannot be in the future.'
        )
    if start < _MIN_DATE:
        raise ValueError(
            f'start_date cannot be earlier than {_MIN_DATE}.'
        )
