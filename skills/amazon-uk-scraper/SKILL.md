---
name: amazon-uk-scraper
description: "Scrape Amazon.co.uk (search, DP, seller) lewat AWS WAF — Bright Data L5 primary + ladder L0-L3 + jalur browser Hermes (proven 48 ASIN) + detector 6 sinyal + selector grid"
version: 1.1.0
metadata:
  hermes:
    tags: [scraping, amazon, aws-waf, scrapling, proxy, browser]
---

# Amazon.co.uk Scraper (AWS WAF bypass — proven 2026-10-06)

**Musuh = AWS WAF** (`window.gokuProps` + `AwsWafIntegration/challenge.js` + `token.awswaf.com`),
BUKAN Cloudflare. `solve_cloudflare=True` / Turnstile solver **tidak ngefek**.

## Jalur utama: Bright Data datasets API (L5 — PRIMARY, pakai kredit Raja)

Key: `~/.brightdata_key` (chmod 600, 36 char). JANGAN tulis key di chat/log — baca dari file.

| Dataset | ID | Pakai untuk |
|---|---|---|
| Search | `gd_lwdb4vjm1ehb499uxs` | `keyword` + `url https://www.amazon.co.uk` + `pages_to_search` → 50-56 rec/halaman, 49-55 berharga GBP |
| Product DP | `gd_l7q7dkf244hwjntr0` | `url https://www.amazon.co.uk/dp/{ASIN}` + `zipcode SW1A 1AA` → 100 keys (price, seller, variants, rating) |

```bash
KEY=$(cat ~/.brightdata_key)
# search
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"input":[{"keyword":"creatine","url":"https://www.amazon.co.uk","pages_to_search":1}],"limit_per_input":null}' \
  "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwdb4vjm1ehb499uxs&notify=false&include_errors=true"
# DP
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"input":[{"url":"https://www.amazon.co.uk/dp/B00T7L20AQ","zipcode":"SW1A 1AA"}],"limit_per_input":null}' \
  "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_l7q7dkf244hwjntr0&notify=false&include_errors=true"
```

Wrapper: `scripts/bd_amazon.py` — `search <keyword> [pages]` | `dp <ASIN>` (retry transient otomatis, normalisasi currency, simpan JSON).
Quirks lengkap: `references/brightdata-l5-quirks.md`.
Proven 2026-10-06: search `creatine` 56 rec/55 harga GBP (`B00T7L20AQ 9.89`, `B0CYTBM49S 7.91`) · DP `B00T7L20AQ` 100 keys (`final_price 9.89`, seller Amazon, rating 4.6) · DP `B0CYTBM49S` (`7.91/10.95`, 4636 reviews, `10K+ bought`).

**Quirks (diukur):**
- `Customer is not active` = TRANSIENT (sekali 200 OK, retry langsung sukses) → wrapper retry 1× + sleep 5s. Bukan key mati.
- Search response = **JSONL** (satu objek per baris, 50-56 baris) — `json.loads` langsung GAGAL (`Extra data`). Parse per-baris.
- `currency: "GPB"` = typo Bright Data untuk GBP → normalisasi di wrapper.
- `zipcode SW1A 1AA` = harga/shipping UK. Tanpa zipcode bisa geo random.
- Browser CDP endpoint (`brd.superproxy.io:9222`) butuh password asli (Raja kirim `**********` = masked) — belum bisa dipakai sampai Raja kirim password real.

## Jalur yang TEMBUS vs yang GAGAL (claim-vs-proof 2026-10-06)

| Jalur | Hasil mentah | Verdict |
|---|---|---|
| L0 curl polos `s?k=creatine` | `202 len=0 signal=WAF_202` | GAGAL — probe sinyal saja |
| L1 `Fetcher.get(impersonate=chrome)` | `202 len=2012 goku=True awswaf=True asin=0` | GAGAL — WAF shell, baseline murah saja |
| L3 `StealthyFetcher + 3 proxy GB` (acak) | `ERR_TIMED_OUT / ERR_CONNECTION_RESET / ERR_PROXY_CONNECTION_FAILED` | GAGAL — proxy gratisan mati |
| L3 `StealthyFetcher + live proxy 2.27.53.95:3128` | `202 len=1982 asin=0 signal=WAF_202` | GAGAL — proxy hidup tapi IP-nya tetap kena WAF |
| Validasi 40 proxy GB (curl) | `HIDUP 1/40` (cuma `2.27.53.95:3128 code=202`) | Proxy gratisan ~2.5% hidup — validasi dulu, jangan langsung pakai |
| Validasi 80 proxy GB (curl) | `HIDUP 3/80` — `51.170.133.249:80 code=503` · 2× `code=202` | 503/1427B = Amazonsorry (throttle) ≠ 202 WAF shell |
| **L3 `StealthyFetcher + proxy 51.170.133.249:80`** | **`200 len=979668 asin=53` + verify ulang `200 len=964142, 48 kartu** | **TEMBUS ✅ — `l3_verify.html` 964KB + `l3_verify.json`** |
| **Browser Hermes `browser_navigate` + `browser_console`** | **`48 kartu [data-asin], judul, harga, rating`** | **TEMBUS ✅ — jalur produksi saat ini** |
| DP `/dp/B00T7L20AQ` via browser | `price=IDR234,294.10, cookie-dialog=YES` | TEMBUS (perlu klik Accept cookie) |

Bukti disk: `browser_harvest_creatine.json` (48 ASIN) + `browser_harvest_creatine_meta.json` + `l3_result.json` + `live_proxies.json`.
Log mentah: `references/ladder-probe-log.md`.

## Jalur produksi: browser Hermes (L4)

```js
// 1. buka search page
// browser_navigate("https://www.amazon.co.uk/s?k=creatine")
// 2. ekstrak grid — SATU call, langsung return map (Rule 2b: tool result = satu-satunya exit)
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

**Aturan panen (dari `web-automation-toolkit` ref `waf-protected-origin-harvest.md`):**
- `browser_console` cap ~30 dtk → batch kecil (~14 ID/call, concurrency 3, gap 250ms), return map di call yang sama
- Jangan percayai `localStorage` (interstitial Amazon me-reset-nya) dan jangan pakai sink `http://127.0.0.1` (mixed-content block)
- Concurrency ≤4-8 + backoff; 200→503 = sinyal berhenti + cooldown ~10 mnt, bukan channel mati
- `200` saja bukan bukti — gate di konten (`data-asin>0`, `£`, tolak boilerplate `robot/unavailable`)

**Pitfall DOM Amazon (diukur, bukan teori):**
- `h2 a span` = NULL di search page ini — judul ada di `h2.innerText`. Selector `c.css('h2 a span::text')` return kosong.
- Geo = ID (`Deliver to Indonesia`) → harga IDR. Untuk £ butuh UK postcode + `locale en-GB`.
- DP selalu munculkan cookie dialog (`Select your cookie preferences`) — klik Accept dulu sebelum parse.
- Seller page `/gp/aag/main?seller=` : coba XHR `fetch()` dari origin dulu sebelum navigasi (navigation vs XHR tidak ekuivalen di endpoint WAF).

## Ladder Scrapling L0→L3 (fallback / VPS tanpa browser Hermes)

```python
from scrapling.fetchers import Fetcher, StealthyFetcher
# L1 baseline (ekspektasi 202 di DC IP)
p = Fetcher.get(url, impersonate='chrome', stealthy_headers=True, timeout=30)
# L3 senjata utama (butuh proxy GB residential yang SEHAT — gratisan ~2.5% hidup)
p = StealthyFetcher.fetch(url, headless=True, network_idle=True, proxy='socks5://IP:PORT',
    block_webrtc=True, locale='en-GB', timezone_id='Europe/London',
    wait_selector='[data-component-type="s-search-result"]')
```

**Detector** (`detect(status, html)` di `scripts/amazon_ladder.py`):
`202`/gokuProps → `WAF_202` (naik ladder) · `503`/Amazonsorry → `THROTTLE_503` (ganti proxy) ·
`200`+0 asin+cookie → `COOKIE_WALL` (page_action accept + persist cookie) ·
`200`+asin+`£`/`a-price-whole` → `SUCCESS` ·
`200`+asin TANPA harga inline → `SUCCESS_VARIANT` (grid variant-family real — harga di DP per-variant; proven 2026-10-06: 200/964KB/53 asin, `a-offscreen` cuma `N sizes`).

**API gotchas (docs Scrapling v0.4.15):**
`.fetch()` untuk browser fetcher vs `.get()` untuk Fetcher · proxy string vs dict Playwright ·
`ProxyRotator` untuk rotasi · `is_blocked` default TIDAK nangkep 202/cookie-wall → custom detector wajib ·
`disable_resources=True` bisa bikin Amazon tak finish loading.

## Install

```bash
uv venv .venv && source .venv/bin/activate
uv pip install "scrapling[fetchers]"
scrapling install   # bukan `python -m scrapling install`
```

## Proxy GB (Proxifly, gratis, update 5 mnt)

`https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/GB/data.json`
(~359 entries `socks5://IP:PORT`). Validasi dulu via `scripts/validate_proxies.py` (curl cepat, simpan yang hidup ke `live_proxies.json`) — ekspektasi ~2-5% hidup.

## Selector grid

Kartu `[data-component-type="s-search-result"][data-asin]` → `data-asin` = ASIN ·
judul `h2` (innerText, BUKAN `h2 a span`) · harga `.a-price .a-offscreen` (£) ·
rating `[aria-label*="out of 5 stars"]` · Prime = `/prime/i` di teks kartu ·
shipping strict `#mir-layout-DELIVERY_BLOCK` (`FREE delivery`→0 else `£X.99`) ·
`totalPrice = price + shipping`; tie-break harga min → frekuensi terbanyak → `amazon-uk`.

## Dari yaklang waf-bypass: pakai vs buang

✅ Pakai: identifikasi WAF, bedain rate-limit vs block, session persistence (`StealthySession` + `user_data_dir`), proxy residential/rotasi.
❌ Buang: encoding/double-encode, SQLi/XSS mutation, HPP, chunked, path tricks, smuggling, origin-bypass — masalah Amazon = fingerprint+IP+cookie.
