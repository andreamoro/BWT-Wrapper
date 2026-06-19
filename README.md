# Bing Webmaster Tools Wrapper

[![License: GPL 3.0](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl-3.0.txt)

## Package purpose and content

`bwt_wrapper` is a package to take the pain out when working with the
[Bing Webmaster Tools API](https://learn.microsoft.com/en-us/bingwebmaster/).
It is written in Python and provides a convenient fluent interface to query:

- **Search Performance by query** (`QueryStats`) — mirrors the Top Queries view
- **Search Performance by page** (`PageStats`) — mirrors the Top Pages view
- **Keyword Research** (`KeywordStats`) — historical broad/strict impression volume
- **Blocked URLs** (`BlockedUrls`) — list, add, and remove blocked URL rules

The design deliberately mirrors the [GSC Wrapper](https://github.com/andreamoro/GSC-Wrapper) to maintain compatibility with the patterns and facilitate application re-usage.

---

## Installation & Requirements

`bwt_wrapper` requires Python 3.13 or greater (it relies on the standard
library `tomllib` module for credential parsing).

The only required runtime dependency is `requests`.  `pandas` is optional
and is only needed if you call `.to_dataframe()`.

### With pip

```bash
python -m pip install .                 # core package
python -m pip install ".[dataframe]"    # + optional pandas / DataFrame export
```

### With uv

This project ships a `uv.lock`, so [uv](https://docs.astral.sh/uv/) can build
a reproducible environment in one step:

```bash
uv sync                      # create .venv and install locked dependencies
uv sync --extra dataframe    # also pull in the optional pandas extra
uv sync --extra test         # dev/test environment (pytest + pandas)
```

Then run anything inside that environment without activating it manually:

```bash
uv run python -c "import bwt_wrapper; print(bwt_wrapper.__doc__)"
uv run pytest
```

To add `bwt_wrapper` as a dependency of *another* uv project:

```bash
uv add "bwt-wrapper @ git+https://github.com/andreamoro/BWT-Wrapper"
```

---

## Authentication

Authentication is much simpler than Google Search Console: no OAuth flow.
You need a single API key.

To generate one:

1. Sign in to [Bing Webmaster Tools](https://www.bing.com/webmaster).
2. Click **Settings** (top right) → **API Access**.
3. Accept the Terms and Conditions, then click **Generate API Key**.

One key is issued per user and grants access to all sites verified under
that account.

### Storing the key (recommended)

Copy the included example file and add your key:

```bash
cp credentials.toml.example credentials.toml
```

Then edit `credentials.toml`:

```toml
api_key = "your_api_key_here"
```

The file is already listed in `.gitignore` so it will never be committed.

You can also pass the key directly if you prefer:

```python
account = bwt_wrapper.Account(api_key='your_api_key')
```

---

## Quickstart

```python
import bwt_wrapper

account   = bwt_wrapper.Account()              # reads from credentials.toml
site_list = account.webproperties()
site      = account[0]               # or account['https://example.com']

# Query-level performance (Top Queries)
query   = bwt_wrapper.QueryStats(site)
report  = query.date_range('2024-01-01', '2024-06-30').get()
df      = report.to_dataframe()

# Page-level performance (Top Pages)
pages   = bwt_wrapper.PageStats(site)
report  = pages.filter_query('/blog/').get()

# Keyword research
kw      = bwt_wrapper.KeywordStats(site)
report  = (
    kw
    .keyword('seo tools')
    .country(bwt_wrapper.country.UNITED_STATES)
    .language(bwt_wrapper.language.ENGLISH)
    .get()
)

# Blocked URLs
blocked = bwt_wrapper.BlockedUrls(site)
report  = blocked.get()
```

---

## Reference

### Account

```python
account = bwt_wrapper.Account()                # credentials.toml (default)
account = bwt_wrapper.Account(api_key='...')   # explicit key
```

| Method / attribute         | Description                                       |
| -------------------------- | ------------------------------------------------- |
| `webproperties()`        | Returns `list[WebProperty]`; results are cached |
| `account[0]`             | Access a site by integer index                    |
| `account['https://...']` | Access a site by URL                              |

---

### QueryStats

```python
query = bwt_wrapper.QueryStats(site)
```

Maps to `GetQueryStats`.  Returns weekly rows with:
`Query`, `Date`, `Clicks`, `Impressions`, `AvgClickPosition`, `AvgImpressionPosition`, `Ctr`.

Positions are divided by 10 to match the Bing UI display values. `Ctr` is a
convenience field computed by this wrapper as `Clicks / Impressions` (a 0–1
ratio, rounded to 4 decimals) — the Bing API itself does not return it.

| Method                             | Description                                |
| ---------------------------------- | ------------------------------------------ |
| `.date_range(start, end)`        | Filter rows to a date window (client-side) |
| `.filter_query(value, contains)` | Filter rows by the Query field             |
| `.get()`                         | Fetch and return a `Report`              |
| `.execute()`                     | Same as `get()`                          |
| `.to_dataframe()`                | Shorthand for `get().to_dataframe()`     |

> **Note:** Bing's API does not accept date range parameters for
> `GetQueryStats` or `GetPageStats` — the full dataset is always
> returned and filtering happens client-side.

---

### PageStats

```python
pages = bwt_wrapper.PageStats(site)
```

Maps to `GetPageStats`.  Identical interface to `QueryStats`.  The `Query`
field in each row holds the **page URL** rather than a search term.

---

### KeywordStats

```python
kw = bwt_wrapper.KeywordStats(site)
```

Maps to `GetKeywordStats`.  Returns weekly rows with:
`Query`, `Date`, `Impressions` (strict), `BroadImpressions`.

| Method              | Description                                                       |
| ------------------- | ----------------------------------------------------------------- |
| `.keyword(term)`  | **Required.** The search term to research                   |
| `.country(code)`  | **Required.** `bwt_wrapper.country.*` enum or raw string  |
| `.language(tag)`  | **Required.** `bwt_wrapper.language.*` enum or raw string |
| `.get()`          | Fetch and return a `Report`                                     |
| `.to_dataframe()` | Shorthand for `get().to_dataframe()`                            |

---

### BlockedUrls

```python
blocked = bwt_wrapper.BlockedUrls(site)
```

| Method                                      | Description                               |
| ------------------------------------------- | ----------------------------------------- |
| `.get()`                                  | Returns a `Report` of all blocked rules |
| `.add(url, entity_type, request_type)`    | Add a blocked URL rule                    |
| `.remove(url, entity_type, request_type)` | Remove an existing rule                   |
| `.to_dataframe()`                         | Shorthand for `get().to_dataframe()`    |

**entity_type** values (from `bwt_wrapper.enumerations`):

| Constant                  | Value | Meaning          |
| ------------------------- | ----- | ---------------- |
| `entity_type.PAGE`      | 0     | Single page      |
| `entity_type.DIRECTORY` | 1     | Directory prefix |

**request_type** values:

| Constant                      | Value | Meaning                             |
| ----------------------------- | ----- | ----------------------------------- |
| `request_type.REMOVE_CACHE` | 0     | Remove cached copy from Bing        |
| `request_type.DISALLOW`     | 1     | Remove from search results entirely |

---

### Report

All data retrieval methods return a `Report` object.

| Method / attribute            | Description                                      |
| ----------------------------- | ------------------------------------------------ |
| `.rows`                     | `list[dict]` of result rows                    |
| `len(report)`               | Number of rows                                   |
| `iter(report)`              | Iterate over rows                                |
| `.to_dataframe()`           | Returns a pandas `DataFrame` (requires pandas) |
| `.to_disk(filename)`        | Persist to a pickle file                         |
| `.to_datastream()`          | Serialise to an in-memory `bytes` object       |
| `Report.from_disk(f)`       | Load a previously saved report                   |
| `Report.from_datastream(b)` | Reconstruct from bytes                           |

---

## Architecture & design notes

The package is intentionally small and layered so the higher-level classes
never deal with raw HTTP. Module responsibilities and the reasoning behind
them:

| Module             | Responsibility                                                                                                   |
| ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| `credentials.py` | Loads the API key from `credentials.toml` via `tomllib`, keeping secrets out of source.                      |
| `api.py`         | Single low-level HTTP transport (`BingApi`). Centralises URL building, JSON parsing, error handling.           |
| `account.py`     | `Account` / `WebProperty` — site discovery and lookup by index or URL, mirroring the GSC Wrapper surface.    |
| `query.py`       | `QueryStats` / `PageStats` fluent builders over the search-performance endpoints.                              |
| `keywords.py`    | `KeywordStats` fluent builder over `GetKeywordStats` (keyword research).                                      |
| `blocked.py`     | `BlockedUrls` — list/add/remove blocked URL rules.                                                            |
| `report.py`      | `Report` — wraps result rows and exports to DataFrame, pickle file, or byte stream.                          |
| `enumerations.py`| Typed `country` / `language` / `entity_type` / `request_type` constants accepted by the API.                 |

Key design decisions worth remembering:

- **Client-side filtering.** Bing's `GetQueryStats` / `GetPageStats` endpoints
  always return the full weekly dataset with no server-side date or dimension
  filtering, so `date_range()` and `filter_query()` are applied locally after
  retrieval. This is why the fluent setters clone `self` and only act at `get()`.
- **Position normalisation.** Bing stores `AvgClickPosition` /
  `AvgImpressionPosition` as integers multiplied by 10; `_normalise_positions()`
  divides by 10 so the values match what the Bing UI displays.
- **Date parsing.** Bing returns dates in the WCF `/Date(milliseconds)/` format;
  `api.py` converts these to native `datetime.date` objects and strips the
  `__type` serialiser field from every row.
- **`WebProperty` for `KeywordStats`.** Keyword research is site-agnostic, but a
  `WebProperty` is still required in the constructor to keep a single, consistent
  account-driven flow across all builders (the URL simply isn't sent for that call).
- **Optional pandas.** `pandas` is not a hard dependency; `to_dataframe()` raises
  a clear `ImportError` with install instructions when it is missing.

---

## Testing

The automated suite under [`tests/`](tests/) is **fully offline and
deterministic** — the HTTP layer is replaced with test doubles, so no API key
or network connection is required. Run it after every change:

```bash
python -m pip install ".[test]"   # installs pytest (and pandas)
pytest
```

Or with uv:

```bash
uv sync --extra test
uv run pytest
```

What is covered:

| Test module                   | What it verifies                                                        |
| ----------------------------- | ----------------------------------------------------------------------- |
| `test_credentials.py`       | TOML key loading and every failure mode (missing file/field, empty key) |
| `test_api.py`               | URL building, `/Date(...)/` parsing, GET/POST plumbing, error handling  |
| `test_account.py`           | Site discovery, caching, int/URL indexing, lookup tolerance             |
| `test_query_page_stats.py`  | Immutable fluent builders, client-side filtering, position normalisation, date validation |
| `test_keywords.py`          | Required-field validation and enum/raw-string coercion                  |
| `test_blocked.py`           | URL validation and enum→int coercion for add/remove                     |
| `test_report.py`            | DataFrame / pickle / byte-stream round-trips                            |
| `test_enumerations.py`      | Enum values and a regression guard against duplicate definitions        |

The fakes live in [`tests/conftest.py`](tests/conftest.py): `FakeSession`
exercises the transport layer; `FakeApi` lets the higher-level classes be
tested in isolation.

> [`tests/live_check.py`](tests/live_check.py) is a separate **manual** smoke
> test that hits the real Bing API (needs `credentials.toml`). It is excluded
> from the pytest run on purpose.

---

## Key differences from GSC Wrapper

The two services overlap less than their tables suggest, so the comparison is
split by what each capability actually operates on.

### A. Your site's own search-performance data

This is the shared ground: in GSC it is Search Analytics; in BWT it is
`GetQueryStats` (queries) and `GetPageStats` (pages). Both are scoped to a
verified property and report the queries/pages that earned impressions for it.

| Capability                          | GSC Wrapper                       | BWT Wrapper                                |
| ----------------------------------- | --------------------------------- | ------------------------------------------ |
| Server-side date filtering          | ✓ Supported                      | ✗ Full set returned; filtered client-side |
| Query filtering (regex / operators) | ✓ Regex + operators server-side  | ✗ Substring / exact match, client-side    |
| Combined `query+page+country+device`| ✓ Single grouped query           | ✗ One dimension per endpoint, no grouping |
| Country / device breakdown          | ✓ Supported server-side          | ✗ Not exposed by Bing                     |
| CTR field                           | ✓ Returned by the API            | ✓ Computed by this wrapper (`Clicks/Impressions`) |
| Historical depth                    | 16 months                         | 16 months                                  |

### B. Keyword research (external demand, any term)

Independent of any verified site — search volume for terms a site may or may
not rank for.

| Capability                            | GSC Wrapper      | BWT Wrapper                                  |
| ------------------------------------- | ---------------- | -------------------------------------------- |
| Search volume for arbitrary keywords  | ✗ Not in the API | ✓ `GetKeywordStats` (any term, per market) |

### C. Account & site management

| Capability             | GSC Wrapper              | BWT Wrapper           |
| ---------------------- | ------------------------ | --------------------- |
| Authentication         | OAuth 2.0 (externalised) | API key only          |
| Blocked URL management | ✗ Not available         | ✓ Add / Remove / List |

### Country and dimension support

Two points are worth clarifying, because `country` means different things in
each tool:

**Country applies to keyword research, not to search performance.**
`KeywordStats.country()` and `.language()` select the market for which search
volume is reported — for example, the volume for *seo tools* in the United
States. They are inputs to keyword research and do not filter a site's own
`QueryStats` or `PageStats` results. Because both are inputs, keyword volume
can still be segmented by market or language: request the same term across
several country and language combinations and compare the results, one call per
segment. The Bing Webmaster Tools API does not provide a country or device
breakdown of search-performance data, so those dimensions are unavailable here
regardless of the wrapper.

**Performance metrics cannot be grouped into a single combined view.**
Google Search Console can return one result keyed by query, page, country and
device together. Bing exposes each metric through a separate endpoint, with no
equivalent combined query. The Bing API does provide two related views —
queries for a single page, and pages for a single query — which a future
release of this wrapper may add. Device data is not available from the Bing
Webmaster Tools API at all.

**The two services analyse different sets of keywords.**
Google Search Console reports the queries that already produced impressions or
clicks for a verified site, and its regex and operator filters narrow that set.
It does not report demand for terms the site has never appeared for. The Bing
keyword endpoint works the other way round: it returns search volume for any
term — whether or not the site ranks for it — for a chosen country and
language. The two are complementary rather than substitutes: one measures how a
site's own queries perform, the other measures market demand for arbitrary
terms.

---

## Related projects

- **[GSC Wrapper](https://github.com/andreamoro/GSC-Wrapper)** — the Google
  Search Console wrapper this package is modeled after. If you work with both
  Bing and Google data, the two share the same `Account` / fluent-builder /
  `Report` patterns, so code written against one ports easily to the other.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
