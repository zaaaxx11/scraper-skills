# Framework

## 1. The enemy: bot-protection, not the site

Typical stack: AWS WAF (`window.gokuProps`, `AwsWafIntegration/challenge.js`),
Cloudflare Turnstile, Akamai / PerimeterX / DataDome, plus cookie-consent walls.
Implication: **the problem is bot-fingerprint + IP reputation + consent state**,
not rule-bypass. Injection tricks (encoding, HPP, chunked, path tricks, smuggling)
are DISCARDED — they only raise ban risk. Identify the protector first
(headers, challenge scripts, status codes), then pick the ladder level.

## 2. Detector — 6 signals (the only decision gate)

```python
detect(status, html, markers) -> signal:
  challenge markers present (any status) → CHALLENGE   # climb ladder
  429/503 or sorry/throttle page        → THROTTLED   # rotate proxy + cooldown
  200 + 0 data markers + consent text   → CONSENT_WALL # accept + persist cookies
  200 + 0 data markers (no consent)     → EMPTY        # retry / climb ladder
  200 + data markers + price markers    → SUCCESS      # parse, done
  200 + data markers, NO inline price   → PARTIAL      # variant-family → detail pages
  else                                  → UNKNOWN      # treat as failure, never parse
```

Discovered 2026-10-06 (Amazon.co.uk): `PARTIAL` = `200 / 964KB / 53 IDs`,
zero inline-price nodes, consent text present — 100% real titles
(Applied Nutrition, Myprotein, USN…) with prices only on detail pages.

## 3. Fallback architecture

```
cheap probe (L1, 1 req) → detector → L5 immediately if a key exists
                                    → L3 + validated proxies if keyless
                                    → L4 browser session if L3 stalls
                                    → THROTTLED = STOP + 10 min cooldown (never blind-retry)
```

Principles:
- **Cheap first, expensive later** — one Fetcher request before burning browser/proxy/credit.
- **Validate before use** — free proxies are 2–5% alive; a healthy pool is stored, never assumed.
- **Success = content, not status** — data markers `> 0` + real titles/prices + file on disk.
- **Rotate, don't over-retry** — a warm IP cools down within minutes.

## 4. Decision matrix

| Condition | Path |
|---|---|
| Bright Data key + credit | L5 (search + detail) — no WAF drama |
| Keyless, need listing grid | L3 (Stealthy + validated geo proxies) |
| L3 blocked on all proxies | L4 browser session (search OK, detail OK) |
| Detail endpoint blocks proxy | Detail via L5 / browser (detail is stricter than search) |
| Grid has no inline prices | PARTIAL → per-variant detail, never quote grid prices |
| Wrong currency/geo | `zipcode` (L5) / `locale` + regional postcode (L3/L4) |

## 5. Per-target profile (what each skill must define)

Every skill under `skills/` pins these — see `skills/_template/`:

- `CHALLENGE_MARKERS` — strings proving a challenge shell (e.g. `gokuprops`, `awswaf`)
- `THROTTLE_MARKERS` — e.g. `amazonsorry`, sorry-page titles, `429`
- `DATA_SELECTOR` — listing-card selector + ID attribute (e.g. `[data-component-type="s-search-result"][data-asin]`)
- `TITLE_SELECTOR` / `PRICE_SELECTOR` / `RATING_SELECTOR` — measured from the real DOM, never assumed
- `L5_DATASETS` — Bright Data dataset IDs if known (see `docs/TARGETS.md`)
- `GEO` — locale, timezone, postcode/zipcode that yields correct currency
