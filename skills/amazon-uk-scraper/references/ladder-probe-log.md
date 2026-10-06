# Ladder probe log — 2026-10-06 (mentah, claim-vs-proof)

## L0 curl polos
- `GET https://www.amazon.co.uk/s?k=creatine` → `status=202 len=0 signal=WAF_202`

## L1 Fetcher
- `Fetcher.get(url, impersonate='chrome', stealthy_headers=True)` → `INFO: Fetched (202)` → `status=202 len=2012 goku=True awswaf=True asin=0 cookie=False sorry=False`

## L3 StealthyFetcher + 3 proxy GB acak
- try 1 `socks5://104.239.83.246:9056` → `PROXY_CONNECTION_FAILED`
- try 2 `http://8.211.200.183:8123` → `ERR_CONNECTION_RESET` → retry → `ERR_TIMED_OUT` ×2 → `Failed after 3 attempts`
- try 3 `socks5://8.211.195.173:9797` → `Timeout 60000ms` ×2 → `ERR_PROXY_CONNECTION_FAILED`
- Verdict: `L3 BELUM tembus`

## Validasi 40 proxy GB (curl --max-time 15)
- `HIDUP: 1/40` → `http://2.27.53.95:3128 code=202 size=0 ms=4943`
- 39/40 dead (code=0: timeout 15s / connection-refused dalam 200-600ms)

## L3 single via live proxy
- `StealthyFetcher.fetch(url, proxy=http://2.27.53.95:3128, ...)` → `ERROR: Timeout 90000ms waiting for selector [data-component-type="s-search-result"]` → `INFO: Fetched (202)` → `status=202 len=1982 asin=0 signal=WAF_202`
- Verdict: proxy hidup tapi IP-nya tetap kena WAF (202 shell, bukan 200 grid)

## Validasi 80 proxy GB (curl --max-time 15) — 2026-10-06 08:17
- `HIDUP: 3/80` → `51.170.133.249:80 code=503 size=1427` · `176.126.241.182:1080 code=202` · `178.62.83.124:32766 code=202`
- 77/80 dead. Catatan: 503/1427B = Amazonsorry (IP nyambung tapi throttle) ≠ 202 WAF shell.

## L3 ulang via 3 proxy batch-80 (TEMBUS ✅ 2026-10-06 08:18)
- try 1 `http://51.170.133.249:80` → `INFO: Fetched (200)` → `status=200 len=979668 asin=53` — TEMBUS
- try 2 `socks5://176.126.241.182:1080` → selector timeout → `202 len=186716 asin=0 WAF_202`
- try 3 `http://178.62.83.124:32766` → selector timeout → `503 len=1098 THROTTLE_503`

## L3 verify ulang via proxy pemenang (200 CONFIRM 2026-10-06 08:26)
- `status=200 len=964142 asin_attr=53 gbp=0 goku=False cookie=True(2x)` → `l3_verify.html` (964KB) + `l3_verify.json` (48 kartu terparse)
- Anatomi grid: `a-price-whole/fraction/symbol = 0`, `s-price = 48`, `a-offscreen` cuma `N sizes / N flavours` (14 varian string) — grid ini **variant-family**: harga TIDAK inline, harus ke DP per-variant.
- Judul real semua (Applied Nutrition, Myprotein, USN, Reflex, DY Nutrition...) — grid data ASLI, bukan shell.
- Detector dikoreksi: `OTHER` + asin>0 → `SUCCESS_VARIANT` (grid real tanpa harga inline). `h2 a span` NULL → judul via `h2.innerText`.
- DP `/dp/B00T7L20AQ` via proxy SAMA → `202 len=1981 gokuProps=1 AwsWaf=4` — endpoint DP lebih strict dari search; DP via browser Hermes tetap jalur utama (`price=IDR234,294.10`).
- Pelajaran proxy: 1 IP bisa 200 di search + 202 di DP dalam 8 menit — IP hangat mendingin cepat; jangan over-retry (burn proxy), rotasi pool.

## Browser Hermes (TEMBUS ✅)
- `browser_navigate https://www.amazon.co.uk/s?k=creatine` → snapshot 654 elemen, heading `1-48 of 150 results for "creatine"`
- `browser_console` hitung → `{asin: 58, gbp: 1, title: "Amazon.co.uk : creatine"}`
- Ekstrak 48 kartu → `browser_harvest_creatine.json` (ASIN+title+price+rating+prime). Judul via `h2.innerText` (`h2 a span` = NULL di DOM ini).
- DP `/dp/B00T7L20AQ` → `price=IDR234,294.10, cookie-dialog=YES`, title `Optimum Nutrition Micronised Creatine Monohydrate Powder, 317g ...`
- Catatan geo: `Deliver to Indonesia` → harga IDR; untuk £ butuh UK postcode + en-GB.
