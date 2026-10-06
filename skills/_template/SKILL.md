---
name: _template
description: "Starter template for a NEW scraper target — copy this folder, fill in WAF markers + selectors, probe L0→L3, log raw evidence"
version: 1.0.0
---

# <Target Name> Scraper — copy this template

Steps: fill every `<FILL>` below, probe L0→L1→L3, keep raw logs (pass AND fail)
in `references/probe-log.md`. Only `SUCCESS` (data markers + saved file) counts as proven.

## 1. Target profile (fill first, probe second)

```python
TARGET = {
    "name": "<FILL: e.g. amazon.de>",
    "search_url": "<FILL: e.g. https://www.amazon.de/s?k={q}>",
    "detail_url": "<FILL: e.g. https://www.amazon.de/dp/{id}>",
    # Strings proving a challenge shell (view-source, lowercase compare):
    "CHALLENGE_MARKERS": ["<FILL: e.g. gokuprops>", "<FILL: e.g. awswaf>"],
    # Strings proving IP throttling (sorry pages, 429/503 bodies):
    "THROTTLE_MARKERS": ["<FILL: e.g. amazonsorry>"],
    "CONSENT_MARKERS": ["<FILL: e.g. cookie preferences>"],
    # Listing-card hooks (measure from the REAL DOM, never assume):
    "DATA_SELECTOR": "<FILL: e.g. [data-component-type=\"s-search-result\"]>",
    "ID_ATTR": "<FILL: e.g. data-asin>",
    "TITLE_SELECTOR": "<FILL>",
    "PRICE_SELECTOR": "<FILL>",
    # Geo that yields the right currency:
    "LOCALE": "<FILL: e.g. en-GB>",
    "TIMEZONE": "<FILL: e.g. Europe/London>",
    "POSTCODE": "<FILL: e.g. SW1A 1AA>",
    # Proxy pool source (Proxifly country feed or equivalent):
    "PROXY_FEED": "<FILL: country data.json URL>",
    # Bright Data dataset IDs ONLY if verified by a real API response:
    "L5_DATASETS": {"search": "<FILL or empty>", "product": "<FILL or empty>"},
}
```

## 2. Ladder (same shape for every target)

| Level | Script | Expectation |
|---|---|---|
| L0 | curl / Jina | blocked — signal probe only |
| L1 | `Fetcher.get(impersonate="chrome")` | blocked on DC IP — cheap classifier |
| L3 | `StealthyFetcher + validated proxy` (`scripts/detector.py` + wait on `DATA_SELECTOR`) | target `SUCCESS` |
| L4 | real browser session, small batches | fallback for search + detail |
| L5 | Bright Data datasets API | primary when a key exists |

## 3. Claim-vs-proof table (fill with RAW numbers)

| Path | Raw result | Verdict |
|---|---|---|
| L0 plain | `status=… len=… signal=…` | … |
| L1 fetch | `status=… len=… markers=…` | … |
| L3 + N proxies | `…` | … |

## 4. Known pitfalls (fill as you measure)

- Title hook that returned NULL: …
- Price missing because (variant-family / JS-injected / …): …
- Geo defaulted to … → wrong currency; fixed via …
- Consent wall text: … → accept via …
