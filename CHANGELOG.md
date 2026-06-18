# Changelog

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
