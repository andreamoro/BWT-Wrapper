# Changelog

## [0.3.0] – 2026-06-21

### Changed
- **BREAKING: the wrapper is now fully async.** Every network call is a
  coroutine and must be awaited (`await query.get()`,
  `await account.webproperties()`, `await blocked.add(...)`, etc.). The
  transport moved from `requests` to [`httpx`](https://www.python-httpx.org/)
  (`httpx.AsyncClient`). Synchronous callers must migrate to `asyncio`
- `Account` and `BingApi` are now async context managers that own an HTTP
  connection pool; use `async with Account() as account:` (or call
  `await account.aclose()`) so the client is closed cleanly
- `Account` indexing, `len()`, and iteration (`account[0]`, `for site in
  account`) are now synchronous *views over the cache* — call
  `await account.webproperties()` once first to populate it, otherwise a
  `RuntimeError` is raised explaining the required order

### Added
- Client-side rate limiting via
  [`aiolimiter`](https://github.com/mjpieters/aiolimiter) (default 5
  requests/second, configurable through `Account(max_rate=…,
  time_period=…, timeout=…)`), so requests can be fanned out with
  `asyncio.gather` without tripping Bing's server-side limits
- `CrawlStats` builder over `GetCrawlStats`, exposing **daily** crawl/index
  rows (`CrawledPages`, `CrawlErrors`, `InIndex`, `InLinks`, the HTTP
  status-code breakdown, etc.) with the same client-side `date_range()`
  filtering used by `QueryStats` / `PageStats`
- `schemas.py` — `TypedDict` row schemas (`QueryRow`, `PageRow`, `KeywordRow`,
  `BlockedRow`, `CrawlRow`) describing each endpoint's post-normalisation
  shape. `Report` is now generic (`Report[QueryRow]`, …); this is a
  static-typing aid only — at runtime every row is still a plain `dict`
- GitHub Actions CI workflow (`.github/workflows/tests.yml`) running the
  offline `pytest` suite on Python 3.13 via `uv`
- `pytest-asyncio` test dependency (with `asyncio_mode = "auto"`) and a
  `test_crawl.py` suite covering endpoint wiring and date filtering

## [0.2.0] – 2026-06-19

### Added
- `Ctr` (click-through rate) field on `QueryStats` / `PageStats` rows,
  computed by the wrapper as `Clicks / Impressions` (a 0–1 ratio rounded to
  4 decimals; `0.0` when there are no impressions). Bing's API does not
  return CTR, so this saves callers from deriving it
- README installation instructions for `uv` (alongside the existing `pip`
  path) and a "Related projects" link to the GSC Wrapper

### Changed
- Rewrote the "Key differences from GSC Wrapper" comparison, splitting it by
  scope — own search-performance data vs. keyword research vs. account
  management — to remove the ambiguity around country filtering and keyword
  research (search performance is site-scoped; `GetKeywordStats` reports
  market-level demand for arbitrary terms and is not tied to a property)

## [0.1.1] – 2026-06-18

### Fixed
- Replaced deprecated `datetime.utcnow()` (in `query._today`) and
  `datetime.utcfromtimestamp()` (in `api._parse_bing_date`) with
  timezone-aware UTC equivalents; both were scheduled for removal in a future
  Python and emitted `DeprecationWarning` on the required Python 3.13 runtime

### Added
- Offline, deterministic `pytest` suite covering every module (credentials,
  transport, account, query/page stats, keywords, blocked URLs, report,
  enumerations); the HTTP layer is mocked via test doubles so no API key or
  network is needed
- `[test]` optional-dependency group and `[tool.pytest.ini_options]`
  configuration in `pyproject.toml`

### Changed
- Renamed the live, network-dependent script `tests/test.py` →
  `tests/live_check.py` so it is excluded from the automated suite

## [0.1.0] – 2026-03-02

### Added
- `Account` class for API key authentication and site management
- `WebProperty` class representing a verified Bing site
- `QueryStats` fluent builder for `GetQueryStats` (Top Queries)
- `PageStats` fluent builder for `GetPageStats` (Top Pages)
- `KeywordStats` fluent builder for `GetKeywordStats` (Keyword Research)
- `BlockedUrls` class for `GetBlockedUrls` / `AddBlockedUrl` / `RemoveBlockedUrl`
- `Report` class with `to_dataframe()`, `to_disk()`, `from_disk()`, `to_datastream()`, `from_datastream()`
- `country` and `language` enumerations for `KeywordStats`
- `entity_type` and `request_type` enumerations for `BlockedUrls`
- Client-side date range and query substring filtering for `QueryStats` / `PageStats`
- Position normalisation (Bing stores positions ×10; divided here to match UI values)
