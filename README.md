# Amazon Scraper Skills

Scrape **Amazon.co.uk** (search, product DP, seller) lewat **AWS WAF** — pola yang terbukti tembus, bukan teori.
Dibangun dari probe mentah 2026-10-06: `202` WAF shell → `503` throttle → `200 + data-asin` ✅.

> 🔑 **Butuh Bright Data API key untuk jalur utama (L5).** Key TIDAK ada di repo ini — baca [How to Use](docs/HOW_TO_USE.md).

## Ladder (fallback chain)

| Level | Cara | Hasil di VPS/DC IP |
|---|---|---|
| L0 | curl / Jina | `202` — probe sinyal saja |
| L1 | `Fetcher.get(impersonate=chrome)` | `202` ~2KB `gokuProps` — baseline murah |
| L2 | `StealthyFetcher` tanpa proxy | `503` di DC IP — skip di VPS |
| L3 | `StealthyFetcher + proxy GB` | `200 + data-asin` ✅ (butuh proxy SEHAT) |
| L4 | Browser session (Hermes) | `48 kartu` ✅ — search + DP |
| **L5** | **Bright Data datasets API** | **56 rec + DP 100 keys ✅ — PRIMARY** |

## Isi repo

```
skills/amazon-uk-scraper/
  SKILL.md                  # skill utama: ladder, detector, selector, quirks
  scripts/
    bd_amazon.py            # L5 wrapper: search <kw> [pages] | dp <ASIN>
    amazon_ladder.py        # L0/L1/L3 ladder + detector 7 sinyal
    l3_single.py            # L3 single-shot via live proxy
    l3_verify.py            # L3 verify: simpan HTML selalu + parse
    validate_proxies.py     # validasi proxy GB (curl cepat)
  references/
    ladder-probe-log.md     # log probe mentah (claim-vs-proof)
    l3_verify.json          # 48 kartu L3 (bukti)
    bd_search_creatine.json # 56 rec Bright Data (bukti)
    bd_dp_B00T7L20AQ.json   # DP 100 keys (bukti)
docs/
  HOW_TO_USE.md             # install → key → contoh → troubleshooting
  WORKFLOW.md               # workflow end-to-end + flowchart
  FRAMEWORK.md              # framework detector + arsitektur + decision matrix
```

## Quickstart

```bash
pip install "scrapling[fetchers]" && scrapling install   # untuk L0-L3 saja
export BRIGHTDATA_KEY="kamu-isi-sendiri"                # untuk L5 (primary)
python skills/amazon-uk-scraper/scripts/bd_amazon.py search "creatine" 1
python skills/amazon-uk-scraper/scripts/bd_amazon.py dp B00T7L20AQ
```

## Diagram

```mermaid
flowchart TD
    Q[query / ASIN] --> D{detector:\nstatus + goku + data-asin}
    D -->|L5 key ada| L5[Bright Data API\nsearch / DP] --> OK✅
    D -->|tanpa key| L1[Fetcher probe]
    L1 -->|202 WAF| L3[Stealthy + proxy GB\nvalidasi dulu]
    L3 -->|200 + asin| OK✅
    L3 -->|202/503| L4[Browser session]
    L4 --> OK✅
```

## Bukti (bukan klaim)

- L3: `200 len=964142 asin=53` via `StealthyFetcher + proxy GB` (2× 200) — `references/l3_verify.json`
- L5 search: `56 rec / 55 berhaga GBP` — `references/bd_search_creatine.json`
- L5 DP: `100 keys, final_price 9.89, seller Amazon` — `references/bd_dp_B00T7L20AQ.json`
- Semua yang GAGAL juga dicatat: `references/ladder-probe-log.md`

## License

MIT — pakai bebas, jangan taruh API key di repo.
