# Changelog

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
