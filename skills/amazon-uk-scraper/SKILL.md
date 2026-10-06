---
name: amazon-uk-scraper
description: "Scrape Amazon.co.uk (search, DP, seller) through AWS WAF — Bright Data L5 primary + ladder L0-L3 + browser-session path (proven 48 ASINs) + 6-signal detector + grid selectors"
version: 2.0.0
metadata:
  hermes:
    tags: [scraping, amazon, aws-waf, scrapling, proxy, browser]
---

# Amazon.co.uk Scraper (AWS WAF bypass — proven 2026-10-06)

**The enemy is AWS WAF** (`window.gokuProps` + `AwsWafIntegration/challenge.js` + `token.awswaf.com`),
NOT Cloudflare. `solve_cloudflare=True` / Turnstile solvers have **no effect**.

## Primary path: Bright Data datasets API (L5 — PRIMARY, uses account credit)

Key: `~/.brightdata_key` (chmod 600) or `BRIGHTDATA_KEY` env. NEVER print the key in chat/logs — read it from file/env.

| Dataset | ID | Use for |
|---|---|---|
| Search | `gd_lwdb4vjm1ehb499uxs` | `keyword` + `url https://www.amazon.co.uk` + `pages_to_search` → 50–56 records/page, 49–55 priced in GBP |
| Product DP | `gd_l7q7dkf244hwjntr0` | `url https://www.amazon.co.uk/dp/{ASIN}` + `zipcode SW1A 1AA` → 100 fields (price, seller, variants, rating) |

```bash
# search
curl -s -H "Authorization: Bearer $BRIGHTDATA_KEY" -H "Content-Type: application/json" \
  -d '{"input":[{"keyword":"creatine","url":"https://www.amazon.co.uk","pages_to_search":1}],"limit_per_input":null}' \
  "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwdb4vjm1ehb499uxs&notify=false&include_errors=true"
# product detail
curl -s -H "Authorization: Bearer $BRIGHTDATA_KEY" -H "Content-Type: application/json" \
  -d '{"input":[{"url":"https://www.amazon.co.uk/dp/B00T7L20AQ","zipcode":"SW1A 1AA"}],"limit_per_input":null}' \
  "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_l7q7dkf244hwjntr0&notify=false&include_errors=true"
```

Wrapper: `scripts/bd_amazon.py` — `search <keyword> [pages]` | `dp <ASIN>` (automatic transient-retry, currency normalization, saves JSON).
Proven 2026-10-06: search `creatine` → 56 records / 55 priced in GBP (`B00T7L20AQ 9.89`, `B0CYTBM49S 7.91`) · DP `B00T7L20AQ` → 100 fields (`final_price 9.89`, seller Amazon, rating 4.6) · DP `B0CYTBM49S` (`7.91/10.95`, 4636 reviews, `10K+ bought`).

**Quirks (measured):**
- `Customer is not active` = TRANSIENT (a retry immediately succeeds) → wrapper retries 1× + 5s sleep. The key is not dead.
- Search response = **JSONL** (one object per line, 50–56 lines) — plain `json.loads` FAILS (`Extra data`). Parse line-by-line.
- `currency: "GPB"` = Bright Data's typo for GBP → normalized in the wrapper.
- `zipcode SW1A 1AA` = correct UK prices/shipping. Without it, geo can be random.
- The Browser CDP endpoint (`brd.superproxy.io:9222`) needs the real password — not usable until provided.

## What BROKE THROUGH vs what FAILED (claim-vs-proof, 2026-10-06)

| Path | Raw result | Verdict |
|---|---|---|
| L0 plain curl `s?k=creatine` | `202 len=0 signal=CHALLENGE` | FAILED — signal probe only |
| L1 `Fetcher.get(impersonate=chrome)` | `202 len=2012 goku=True awswaf=True asin=0` | FAILED — WAF shell, cheap baseline only |
| L3 `StealthyFetcher + 3 random GB proxies` | `ERR_TIMED_OUT / ERR_CONNECTION_RESET / ERR_PROXY_CONNECTION_FAILED` | FAILED — free proxies dead |
| L3 `StealthyFetcher + live proxy 2.27.53.95:3128` | `202 len=1982 asin=0 signal=CHALLENGE` | FAILED — live proxy but IP still challenged |
| Validated 40 GB proxies (curl) | `ALIVE 1/40` (only `2.27.53.95:3128 code=202`) | Free proxies ~2.5% alive — validate first, never use raw |
| Validated 80 GB proxies (curl) | `ALIVE 3/80` — `51.170.133.249:80 code=503` · 2× `code=202` | 503/1427B = sorry-page (throttle) ≠ 202 challenge shell |
| **L3 `StealthyFetcher + proxy 51.170.133.249:80`** | **`200 len=979668 asin=53` + re-verify `200 len=964142, 48 cards`** | **THROUGH ✅ — `l3_verify.html` 964KB + `l3_verify.json`** |
| **Browser session harvest** | **`48 [data-asin] cards with title, price, rating`** | **THROUGH ✅ — production path** |
| DP `/dp/B00T7L20AQ` via browser | `price + cookie-dialog=YES` | THROUGH (must click Accept first) |

Disk evidence: `references/l3_verify.json` (48 cards) + `references/bd_search_creatine.json` + `references/bd_dp_B00T7L20AQ.json`.
Raw log: `references/ladder-probe-log.md`.

## Production path: browser session (L4)

```js
// 1. open the search page, 2. extract the grid — ONE call, return the map directly
(() => {
  const cards = [...document.querySelectorAll('[data-component-type="s-search-result"][data-asin]')];
  return JSON.stringify({count: cards.length, items: cards.map(c => {
    const h2 = c.querySelector('h2');
    const p = c.querySelector('.a-price .a-offscreen');
    const r = c.querySelector('[aria-label*="out of 5 stars"]');
    return {asin: c.getAttribute('data-asin'),
      title: h2 ? h2.innerText.trim().slice(0,120) : '',
      price: p ? p.innerText.trim() : '',
      rating: r ? r.getAttribute('aria-label') : ''};
  })});
})()
```

**Harvest rules:**
- Console caps (~30s) → small batches (~14 IDs/call, concurrency 3, 250ms gap), return the map in the same call
- Don't trust `localStorage` (interstitials reset it) or `http://127.0.0.1` sinks (mixed-content block)
- Concurrency ≤4–8 + backoff; 200→503 means STOP + ~10 min cooldown, not a dead channel
- `200` alone is not proof — gate on content (`data-asin>0`, `£`, reject `robot/unavailable` boilerplate)

**Measured Amazon DOM pitfalls:**
- `h2 a span` = NULL on this search page — the title lives in `h2.innerText`.
- Default geo can mistarget (e.g. `Deliver to Indonesia` → IDR prices). For £ you need a UK postcode + `en-GB` locale.
- DP always shows a cookie dialog — click Accept before parsing.
- Seller page `/gp/aag/main?seller=`: try XHR `fetch()` from origin first (navigation vs XHR are not equivalent on WAF endpoints).

## Scrapling ladder L0→L3 (fallback / keyless sessions)

```python
from scrapling.fetchers import Fetcher, StealthyFetcher
# L1 baseline (expect 202 on datacenter IPs)
p = Fetcher.get(url, impersonate='chrome', stealthy_headers=True, timeout=30)
# L3 primary free path (needs a HEALTHY geo proxy — free ones are ~2.5% alive)
p = StealthyFetcher.fetch(url, headless=True, network_idle=True, proxy='socks5://IP:PORT',
    block_webrtc=True, locale='en-GB', timezone_id='Europe/London',
    wait_selector='[data-component-type="s-search-result"]')
```

**Detector** — see `skills/_template/scripts/detector.py` for the generic version (`CHALLENGE | THROTTLED | CONSENT_WALL | EMPTY | SUCCESS | PARTIAL | UNKNOWN`):
`202`/gokuProps → `CHALLENGE` (climb) · `503`/sorry → `THROTTLED` (rotate proxy) ·
`200`+0 IDs+consent → `CONSENT_WALL` (accept + persist) ·
`200`+IDs+`£`/`a-price-whole` → `SUCCESS` ·
`200`+IDs with NO inline price → `PARTIAL` (variant-family grid — price on per-variant DP; proven 2026-10-06: 200/964KB/53 IDs, `a-offscreen` only `N sizes`).

**Scrapling API gotchas (v0.4.15):**
`.fetch()` for browser fetchers vs `.get()` for Fetcher · proxy as string vs Playwright dict ·
`ProxyRotator` for rotation · default `is_blocked` does NOT catch 202/consent-wall → custom detector required ·
`disable_resources=True` can prevent Amazon from finishing loading.

## Install

```bash
uv venv .venv && source .venv/bin/activate
uv pip install "scrapling[fetchers]"
scrapling install   # NOT `python -m scrapling install`
```

## GB proxies (Proxifly, free, 5-min refresh)

`https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/GB/data.json`
(~359 `socks5://IP:PORT` entries). Always validate first via `scripts/validate_proxies.py` (fast curl, keep responders in `live_proxies.json`) — expect ~2–5% alive.

## Grid selectors

Cards `[data-component-type="s-search-result"][data-asin]` → `data-asin` = ID ·
title `h2` (innerText, NOT `h2 a span`) · price `.a-price .a-offscreen` (£) ·
rating `[aria-label*="out of 5 stars"]` · Prime = `/prime/i` in card text ·
strict shipping `#mir-layout-DELIVERY_BLOCK` (`FREE delivery`→0 else `£X.99`) ·
`totalPrice = price + shipping`; tie-break: lowest → most-common → `amazon-uk`.

## WAF-bypass literature: keep vs discard

✅ Keep: WAF identification, rate-limit vs block distinction, session persistence (`StealthySession` + `user_data_dir`), residential/rotating proxies.
❌ Discard: encoding/double-encode, SQLi/XSS mutation, HPP, chunked, path tricks, smuggling, origin-bypass — Amazon's problem is fingerprint+IP+cookie.
