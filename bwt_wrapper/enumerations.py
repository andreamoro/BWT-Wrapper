"""
Enumerations for Bing Webmaster Tools Wrapper.

Provides typed constants for countries and languages accepted by the
GetKeywordStats endpoint, mirroring the enumeration pattern used in
the GSC Wrapper.

Country codes are lowercase ISO 3166-1 alpha-2 as required by the Bing API.
Language codes follow Bing's own setLang codes (not pure IETF BCP 47 in all
cases — e.g. Bing uses 'jp' not 'ja' for Japanese).

Both lists are sourced directly from Microsoft's official Bing market codes
documentation:
  https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/market-codes

COUNTRY LIST SCOPE
------------------
The country enum covers only the markets that Bing officially supports for
keyword data.  Many countries (Iceland, Croatia, Albania, Uzbekistan,
Tajikistan, and most of Africa, Central Asia, and the Caribbean) are not
present because Bing simply does not provide keyword volume data for them —
passing an unsupported code returns an empty array from the API.  This is a
Bing platform limitation, not an omission in this wrapper.

LANGUAGE LIST SCOPE
-------------------
The language enum covers all languages listed under Bing's setLang reference,
which is broader than the market-language pairs: it includes languages such as
Croatian, Bulgarian, Icelandic, Ukrainian, and many Indic languages even though
those countries may not appear in the country enum (e.g. you can request
Croatian-language keyword data without a Croatia market).
"""

from enum import Enum


class country(str, Enum):
    """
    Countries officially supported by Bing for keyword volume data.
    Source: Bing Web Search API market codes (cc parameter list).

    Note: this is a deliberately bounded list.  Bing does not provide keyword
    data for countries outside this set.  Do not add codes speculatively — the
    API will silently return an empty result for unsupported markets.
    """
    ARGENTINA           = 'ar'
    AUSTRALIA           = 'au'
    AUSTRIA             = 'at'
    BELGIUM             = 'be'
    BRAZIL              = 'br'
    CANADA              = 'ca'
    CHILE               = 'cl'
    CHINA               = 'cn'
    DENMARK             = 'dk'
    FINLAND             = 'fi'
    FRANCE              = 'fr'
    GERMANY             = 'de'
    HONG_KONG           = 'hk'
    INDIA               = 'in'
    INDONESIA           = 'id'
    ITALY               = 'it'
    JAPAN               = 'jp'
    MALAYSIA            = 'my'
    MEXICO              = 'mx'
    NETHERLANDS         = 'nl'
    NEW_ZEALAND         = 'nz'
    NORWAY              = 'no'
    PHILIPPINES         = 'ph'
    POLAND              = 'pl'
    PORTUGAL            = 'pt'
    RUSSIA              = 'ru'
    SAUDI_ARABIA        = 'sa'
    SOUTH_AFRICA        = 'za'
    SOUTH_KOREA         = 'kr'
    SPAIN               = 'es'
    SWEDEN              = 'se'
    SWITZERLAND         = 'ch'
    TAIWAN              = 'tw'
    TURKEY              = 'tr'
    UNITED_KINGDOM      = 'gb'
    UNITED_STATES       = 'us'


class language(str, Enum):
    """
    All languages supported by Bing (setLang codes).
    Source: Bing Web Search API language support reference.

    These codes are broader than the market list: a language may be usable
    even when its primary country is not in the country enum above.
    Note that Bing uses 'jp' (not 'ja') for Japanese — this matches the
    documented code, not the ISO 639-1 standard.
    """
    ARABIC                  = 'ar'
    BASQUE                  = 'eu'
    BENGALI                 = 'bn'
    BULGARIAN               = 'bg'
    CATALAN                 = 'ca'
    CHINESE_SIMPLIFIED      = 'zh-hans'
    CHINESE_TRADITIONAL     = 'zh-hant'
    CROATIAN                = 'hr'
    CZECH                   = 'cs'
    DANISH                  = 'da'
    DUTCH                   = 'nl'
    ENGLISH                 = 'en'
    ENGLISH_UK              = 'en-gb'
    ESTONIAN                = 'et'
    FINNISH                 = 'fi'
    FRENCH                  = 'fr'
    GALICIAN                = 'gl'
    GERMAN                  = 'de'
    GUJARATI                = 'gu'
    HEBREW                  = 'he'
    HINDI                   = 'hi'
    HUNGARIAN               = 'hu'
    ICELANDIC               = 'is'
    ITALIAN                 = 'it'
    JAPANESE                = 'jp'
    KANNADA                 = 'kn'
    KOREAN                  = 'ko'
    LATVIAN                 = 'lv'
    LITHUANIAN              = 'lt'
    MALAY                   = 'ms'
    MALAYALAM               = 'ml'
    MARATHI                 = 'mr'
    NORWEGIAN_BOKMAL        = 'nb'
    POLISH                  = 'pl'
    PORTUGUESE_BRAZIL       = 'pt-br'
    PORTUGUESE_PORTUGAL     = 'pt-pt'
    PUNJABI                 = 'pa'
    ROMANIAN                = 'ro'
    RUSSIAN                 = 'ru'
    SERBIAN_CYRILLIC        = 'sr'
    SLOVAK                  = 'sk'
    SLOVENIAN               = 'sl'
    SPANISH                 = 'es'
    SWEDISH                 = 'sv'
    TAMIL                   = 'ta'
    TELUGU                  = 'te'
    THAI                    = 'th'
    TURKISH                 = 'tr'
    UKRAINIAN               = 'uk'
    VIETNAMESE              = 'vi'


class entity_type(int, Enum):
    """
    Entity types for blocked URL rules.
    Used by BlockedUrls.add() to specify whether to block a page or directory.
    """
    PAGE        = 0
    DIRECTORY   = 1


class request_type(int, Enum):
    """
    Cache directive for blocked URL entries.
    REMOVE_CACHE removes the cached copy only; DISALLOW prevents Bing from
    showing the URL entirely.
    """
    REMOVE_CACHE    = 0
    DISALLOW        = 1
