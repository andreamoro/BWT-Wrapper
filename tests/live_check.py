"""
Live, manual smoke-check for the Bing Webmaster Tools Wrapper.

This script talks to the REAL Bing API and therefore needs a valid
``credentials.toml`` and network access. It is intentionally NOT a pytest
module (its filename does not match ``test_*.py``) so the automated suite
under ``tests/test_*.py`` stays fully offline and deterministic.

Run it manually against a live account with::

    python tests/live_check.py

For the automated, offline suite run ``pytest`` from the project root.

Adapted from the Google Search Console Wrapper test suite.
"""

import asyncio
from datetime import date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

import bwt_wrapper
from bwt_wrapper import QueryStats, PageStats
from bwt_wrapper.report import Report


async def Authenticate(istest: bool) -> tuple[bwt_wrapper.Account, bwt_wrapper.WebProperty]:
    """
    Authenticate and return an Account and WebProperty tuple.

    In test mode, creates a mock account with fake credentials.
    In production mode, loads the API key from credentials.toml.

    Returns
    -------
    tuple[Account, WebProperty]
        The account and the first available web property.
    """
    if not istest:
        # Production mode: load API key from credentials.toml
        account = bwt_wrapper.Account()
        await account.webproperties()  # populate the cache so indexing works
        site = account[0]  # Get the first site
    else:
        # Test mode: create account with fake API key and mock site
        account = bwt_wrapper.Account(api_key="fake_test_api_key")

        # Create a mock WebProperty for testing
        from bwt_wrapper.api import BingApi
        api = BingApi("fake_test_api_key")
        site = bwt_wrapper.WebProperty("https://www.test1.com", True, api)
        account._properties = [site]

    return account, site


async def test_search_analytics(query: QueryStats):
    """
    Test QueryStats functionality with date range filtering.

    Note: BWT API returns full dataset and applies date filtering client-side.
    The date_range method requires explicit start and end dates (no days/months offset).
    """
    # First, fetch ALL data without date filtering to see what's available
    print("Fetching all data without date filter...")
    report_all = await query.get()
    print(f"All data report: {report_all}")
    print(f"Total rows: {len(report_all)}")

    # Show sample of raw data
    if len(report_all) > 0:
        print(f"Sample row: {report_all.rows[0]}")
        # Find min/max dates in the data
        dates = [r.get('Date') for r in report_all.rows if r.get('Date')]
        if dates:
            print(f"Date range in data: {min(dates)} to {max(dates)}")

    # Test date range filtering with string dates
    report = await query.date_range('2025-01-10', '2025-11-30').get()
    print(f"\nReport (2025-11-10 to 2025-11-30): {report}")
    print(f"Number of rows: {len(report)}")

    # Test date range filtering with date objects
    report = await query.date_range(date(2025, 1, 10), date(2025, 11, 30)).get()
    print(f"Report with date objects: {report}")

    # Test query filter (substring match on query field)
    report_filtered = await query.filter_query('test').date_range('2025-01-10', '2025-11-30').get()
    print(f"Filtered report: {report_filtered}")

    # Test exact match filter
    report_exact = await query.filter_query('exact query', contains=False).date_range('2025-01-10', '2025-11-30').get()
    print(f"Exact match filtered report: {report_exact}")

    # Test execute() method (returns raw data without additional filters)
    report_raw = await query.date_range('2025-01-10', '2025-11-30').execute()
    print(f"Raw report: {report_raw}")

    # Test to_dataframe if pandas is available
    try:
        df = report.to_dataframe()
        print(f"DataFrame shape: {df.shape}")
    except ImportError:
        print("Pandas not available, skipping DataFrame test")

    # Test report persistence
    filename = report.to_disk()
    print(f"Report saved to: {filename}")

    # Restore from disk
    restored_report = Report.from_disk(filename)
    print(f"Restored report: {restored_report}")
    assert len(report) == len(restored_report), "Report row count mismatch after persistence"


async def test_page_stats(site):
    """
    Test PageStats functionality.

    PageStats is similar to QueryStats but returns data grouped by page URL.
    """
    pages = PageStats(site)

    # Test date range filtering
    report = await pages.date_range('2025-01-10', '2025-11-30').get()
    print(f"PageStats report: {report}")
    print(f"Number of rows: {len(report)}")

    # Test filter by page URL (substring match)
    report_filtered = await pages.filter_query('/blog/').date_range('2025-01-10', '2025-11-30').get()
    print(f"Filtered PageStats report: {report_filtered}")

    # Test exact match filter
    report_exact = await pages.filter_query('https://www.test1.com/', contains=False).date_range('2025-01-10', '2025-11-30').get()
    print(f"Exact match PageStats report: {report_exact}")


async def test_report_persistence(site):
    """
    Test Report persistence to disk and restoration.
    """
    query = QueryStats(site)
    report = await query.date_range('2025-01-10', '2025-11-21').get()

    # Save to disk
    filename = report.to_disk()
    print(f"Report saved to: {filename}")

    # Load from disk
    loaded_report = bwt_wrapper.Report.from_disk(filename)
    print(f"Loaded report: {loaded_report}")
    print(f"Number of rows: {len(loaded_report)}")

    # Verify data matches
    assert len(report) == len(loaded_report), "Report row count mismatch after persistence"

    # Test to_datastream and from_datastream
    datastream = report.to_datastream()
    restored_report = Report.from_datastream(datastream)
    assert len(report) == len(restored_report), "Report row count mismatch after datastream"


async def main():
    # Authenticate (set istest=True to use fake credentials)
    account, site = await Authenticate(istest=False)
    print(f"Testing with site: {site}")

    # Close the underlying HTTP client cleanly when finished.
    async with account:
        # Test QueryStats
        print("\n=== Testing QueryStats ===")
        query = QueryStats(site)
        await test_search_analytics(query)

        # Test PageStats
        print("\n=== Testing PageStats ===")
        await test_page_stats(site)

        # Test Report persistence
        print("\n=== Testing Report Persistence ===")
        await test_report_persistence(site)

    print("\n=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())
