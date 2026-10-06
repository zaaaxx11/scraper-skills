# Scraper Skills 🔥

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Scrapling](https://img.shields.io/badge/powered_by-scrapling-orange.svg)](https://github.com/D4Vinci/Scrapling)
[![Bright Data](https://img.shields.io/badge/L5-Bright_Data-purple.svg)](https://brightdata.com/)

A universal framework for scraping **WAF-protected e-commerce targets** — proven patterns, not theory.
Every claim is backed by raw probe evidence (`claim-vs-proof` logs in each skill's `references/`).

Reference implementation: [`skills/amazon-uk-scraper`](skills/amazon-uk-scraper/SKILL.md) —
Amazon.co.uk through AWS WAF, proven 2026-10-06 (`200 + data-asin`, Bright Data `56 records / 55 priced`).

> 🔑 **Some levels need a Bright Data API key.** No key is stored in this repo — see [How to Use](docs/HOW_TO_USE.md).

## Contents

- [The Ladder](#the-ladder-fallback-chain--same-shape-for-every-target)
- [Repo layout](#repo-layout)
- [Quickstart](#quickstart-amazoncouk-example)
- [Flow](#flow)
- [Adding a new target](#adding-a-new-target)
- [Evidence](#evidence-not-claims)
- [Docs](#docs)
- [License](#license)

## The Ladder (fallback chain — same shape for every target)

| Level | Method | Cost | When |
|---|---|---|---|
| L0 | Plain curl / Jina Reader | Free | Signal probe only (expect block) |
| L1 | `Fetcher.get(impersonate=chrome)` | Free | Cheap baseline, classifies the block |
| L2 | `StealthyFetcher`, no proxy | Free | Works on residential IPs; skipped on datacenter IPs |
| L3 | `StealthyFetcher` + validated geo proxy | Free–cheap | Primary free path (needs a HEALTHY proxy) |
| L4 | Real browser session | Medium | Search + detail pages when L3 stalls |
| **L5** | **Bright Data datasets API** | **Paid credit** | **PRIMARY when a key exists — no WAF drama** |

Rule: **cheap first, expensive later.** One L1 request before burning proxies or credit.
Success = **content, not status** — data markers `> 0` + real titles/prices + file on disk.

## Repo layout

```
skills/
  _template/                       # copy-paste starter for a NEW target
    SKILL.md                       # target profile checklist + claim-vs-proof table
    scripts/detector.py            # generic 7-signal detector, configure markers per target
  amazon-uk-scraper/               # ✅ PROVEN reference (AWS WAF, 2026-10-06)
    SKILL.md                       # ladder, detector, selectors, quirks
    scripts/
      bd_amazon.py                 # L5 wrapper: search <keyword> [pages] | dp <ASIN>
      amazon_ladder.py             # L0/L1/L3 ladder + detector
      l3_single.py                 # L3 single-shot via validated live proxies
      l3_verify.py                 # L3 verify: always save HTML + parse + prove
      validate_proxies.py          # fast curl proxy validation → live_proxies.json
    references/
      ladder-probe-log.md          # raw probe log (pass AND fail)
      l3_verify.json               # 48 cards from L3 breakthrough (proof)
      bd_search_creatine.json      # 56 Bright Data search records (proof)
      bd_dp_B00T7L20AQ.json        # 100-field Bright Data product (proof)
docs/
  HOW_TO_USE.md                    # setup → key → examples → troubleshooting
  WORKFLOW.md                      # end-to-end flowchart + harvest rules
  FRAMEWORK.md                     # detector spec + architecture + decision matrix
  TARGETS.md                       # support matrix: proven vs wanted targets
```

## Quickstart (Amazon.co.uk example)

```bash
# L5 primary — no install needed, just the key (never commit it)
export BRIGHTDATA_KEY="your-key-here"
python skills/amazon-uk-scraper/scripts/bd_amazon.py search "creatine" 1
python skills/amazon-uk-scraper/scripts/bd_amazon.py dp B00T7L20AQ

# Free path (no key) — needs scrapling + healthy geo proxies
pip install "scrapling[fetchers]" && scrapling install
python skills/amazon-uk-scraper/scripts/validate_proxies.py 40
python skills/amazon-uk-scraper/scripts/amazon_ladder.py "creatine" 3
```

Expected L5 output: `56 records, 55 priced in GBP` on search; `final_price 9.89, seller Amazon, rating 4.6` on the sample DP.

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

Detector signals (`skills/_template/scripts/detector.py`):
`CHALLENGE` → climb · `THROTTLED` → rotate + cooldown · `CONSENT_WALL` → accept + persist ·
`EMPTY` → retry/climb · `SUCCESS` → parse, done · `PARTIAL` → variant-family grid, go per-variant detail ·
`UNKNOWN` → treat as failure, never parse.

## Adding a new target

1. Copy `skills/_template/` → `skills/<target-slug>/`
2. Fill in WAF markers + selectors (see [`docs/TARGETS.md`](docs/TARGETS.md) + [`docs/FRAMEWORK.md`](docs/FRAMEWORK.md))
3. Probe L0 → L1 → L3, log **raw** results (pass AND fail) in `references/probe-log.md`
4. Only `SUCCESS` (data markers + saved file) counts as proven — then update `TARGETS.md`

## Evidence (not claims)

- L3: `200, 964KB, 53 IDs` via `StealthyFetcher + GB proxy` (200 twice) — [`skills/amazon-uk-scraper/references/l3_verify.json`](skills/amazon-uk-scraper/references/l3_verify.json)
- L5 search: `56 records / 55 priced in GBP` — [`skills/amazon-uk-scraper/references/bd_search_creatine.json`](skills/amazon-uk-scraper/references/bd_search_creatine.json)
- L5 product: `100 fields, final_price 9.89, seller Amazon` — [`skills/amazon-uk-scraper/references/bd_dp_B00T7L20AQ.json`](skills/amazon-uk-scraper/references/bd_dp_B00T7L20AQ.json)
- Everything that FAILED is logged too — [`skills/amazon-uk-scraper/references/ladder-probe-log.md`](skills/amazon-uk-scraper/references/ladder-probe-log.md)

## Docs

| Doc | What |
|---|---|
| [HOW_TO_USE](docs/HOW_TO_USE.md) | Setup, key handling, examples, troubleshooting table, honest limits |
| [WORKFLOW](docs/WORKFLOW.md) | End-to-end flowchart, 5 stages, browser-session harvest rules |
| [FRAMEWORK](docs/FRAMEWORK.md) | Protector taxonomy, detector spec, fallback architecture, decision matrix |
| [TARGETS](docs/TARGETS.md) | Proven vs wanted matrix + how to verify new Bright Data dataset IDs |

## Security

- No API keys, tokens, or passwords in this repo — wrappers read `BRIGHTDATA_KEY` env first, `~/.brightdata_key` fallback.
- Scan before every push. If a secret leaks, rotate it immediately (don't just delete the file — git history keeps it).

## License

MIT — use freely, never commit API keys.
