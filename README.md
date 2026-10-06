# Scraper Skills

A universal framework for scraping **WAF-protected e-commerce targets** — proven patterns, not theory.
Every claim is backed by raw probe evidence (`claim-vs-proof` logs in each skill's `references/`).

Reference implementation: [`skills/amazon-uk-scraper`](skills/amazon-uk-scraper/SKILL.md) —
Amazon.co.uk through AWS WAF, proven 2026-10-06 (`200 + data-asin`, Bright Data `56 rec / 55 priced`).

> 🔑 **Some levels need a Bright Data API key.** No key is stored in this repo — see [How to Use](docs/HOW_TO_USE.md).

## The Ladder (fallback chain — same shape for every target)

| Level | Method | Cost | When |
|---|---|---|---|
| L0 | Plain curl / Jina Reader | Free | Signal probe only (expect block) |
| L1 | `Fetcher.get(impersonate=chrome)` | Free | Cheap baseline, classifies the block |
| L2 | `StealthyFetcher`, no proxy | Free | Works on residential IPs; skipped on datacenter IPs |
| L3 | `StealthyFetcher` + validated geo proxy | Free–cheap | Primary free path (needs HEALTHY proxy) |
| L4 | Real browser session | Medium | Search + detail pages when L3 stalls |
| **L5** | **Bright Data datasets API** | **Paid credit** | **PRIMARY when a key exists — no WAF drama** |

Rule: **cheap first, expensive later.** One L1 request before burning proxies or credit.

## Repo layout

```
skills/
  _template/               # copy-paste starter for a NEW target
    SKILL.md
    scripts/detector.py    # generic 6-signal detector, configure markers per target
  amazon-uk-scraper/       # ✅ PROVEN reference (AWS WAF, 2026-10-06)
    SKILL.md
    scripts/               # bd_amazon.py, amazon_ladder.py, l3_*.py, validate_proxies.py
    references/            # raw probe log + proof JSONs
docs/
  HOW_TO_USE.md            # setup → key → examples → troubleshooting
  WORKFLOW.md              # end-to-end flowchart + harvest rules
  FRAMEWORK.md             # detector spec + architecture + decision matrix
  TARGETS.md               # target support matrix (proven vs wanted)
```

## Quickstart (Amazon.co.uk example)

```bash
export BRIGHTDATA_KEY="your-key-here"   # L5 (primary) — never commit this
python skills/amazon-uk-scraper/scripts/bd_amazon.py search "creatine" 1
python skills/amazon-uk-scraper/scripts/bd_amazon.py dp B00T7L20AQ

# Free path (no key): validate proxies first, then climb the ladder
python skills/amazon-uk-scraper/scripts/validate_proxies.py 40
python skills/amazon-uk-scraper/scripts/amazon_ladder.py "creatine" 3
```

## Flow

```mermaid
flowchart TD
    Q[query / product URL] --> D{detector:\nstatus + markers + data?}
    D -->|key available| L5[Bright Data datasets API] --> OK✅
    D -->|no key| L1[cheap Fetcher probe]
    L1 -->|challenge shell| L3[Stealthy + validated geo proxy]
    L3 -->|data markers| OK✅
    L3 -->|blocked| L4[real browser session]
    L4 --> OK✅
```

## Adding a new target

1. Copy `skills/_template/` → `skills/<target-slug>/`
2. Fill in the WAF markers + selectors (follow `docs/TARGETS.md`)
3. Probe L0→L1→L3, log **raw** results (pass AND fail) in `references/probe-log.md`
4. Only `SUCCESS` (data markers + saved file) counts as proven — update `TARGETS.md`

## Evidence (not claims)

- L3: `200, 964KB, 53 ASINs` via `StealthyFetcher + GB proxy` (200 twice) — `skills/amazon-uk-scraper/references/l3_verify.json`
- L5 search: `56 records / 55 priced in GBP` — `references/bd_search_creatine.json`
- L5 product: `100 fields, final_price 9.89, seller Amazon` — `references/bd_dp_B00T7L20AQ.json`
- Everything that FAILED is logged too: `references/ladder-probe-log.md`

## License

MIT — use freely, never commit API keys.
