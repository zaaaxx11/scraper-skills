# Ladder probe log — 2026-10-06 (raw, claim-vs-proof)

All commands below ran against `https://www.amazon.co.uk/s?k=creatine` from a
datacenter VPS. Raw numbers only — verdicts in the last column of each line.

## L0 plain curl
- `GET https://www.amazon.co.uk/s?k=creatine` → `status=202 len=0 signal=CHALLENGE`

## L1 Fetcher
- `Fetcher.get(url, impersonate='chrome', stealthy_headers=True)` → `INFO: Fetched (202)` → `status=202 len=2012 goku=True awswaf=True asin=0 cookie=False sorry=False`

## L3 StealthyFetcher + 3 random GB proxies
- try 1 `socks5://104.239.83.246:9056` → `PROXY_CONNECTION_FAILED`
- try 2 `http://8.211.200.183:8123` → `ERR_CONNECTION_RESET` → retry → `ERR_TIMED_OUT` ×2 → `Failed after 3 attempts`
- try 3 `socks5://8.211.195.173:9797` → `Timeout 60000ms` ×2 → `ERR_PROXY_CONNECTION_FAILED`
- Verdict: `L3 NOT through`

## 40-proxy GB validation (curl --max-time 15)
- `ALIVE: 1/40` → `http://2.27.53.95:3128 code=202 size=0 ms=4943`
- 39/40 dead (code=0: 15s timeout / connection-refused within 200–600ms)

## L3 single via live proxy
- `StealthyFetcher.fetch(url, proxy=http://2.27.53.95:3128, ...)` → `ERROR: Timeout 90000ms waiting for selector [data-component-type="s-search-result"]` → `INFO: Fetched (202)` → `status=202 len=1982 asin=0 signal=CHALLENGE`
- Verdict: proxy alive but its IP is still challenged (202 shell, not a 200 grid)

## 80-proxy GB validation (curl --max-time 15) — 2026-10-06 08:17
- `ALIVE: 3/80` → `51.170.133.249:80 code=503 size=1427` · `176.126.241.182:1080 code=202` · `178.62.83.124:32766 code=202`
- 77/80 dead. Note: 503/1427B = sorry page (IP connects but is throttled) ≠ 202 challenge shell.

## L3 retry via the 3 batch-80 proxies (THROUGH ✅ 2026-10-06 08:18)
- try 1 `http://51.170.133.249:80` → `INFO: Fetched (200)` → `status=200 len=979668 asin=53` — THROUGH
- try 2 `socks5://176.126.241.182:1080` → selector timeout → `202 len=186716 asin=0 CHALLENGE`
- try 3 `http://178.62.83.124:32766` → selector timeout → `503 len=1098 THROTTLED`

## L3 re-verify via the winning proxy (200 CONFIRMED 2026-10-06 08:26)
- `status=200 len=964142 asin_attr=53 gbp=0 goku=False cookie=True(2x)` → `l3_verify.html` (964KB) + `l3_verify.json` (48 parsed cards)
- Grid anatomy: `a-price-whole/fraction/symbol = 0`, `s-price = 48`, `a-offscreen` only `N sizes / N flavours` (14 distinct strings) — this grid is **variant-family**: NO inline price, must visit per-variant DP.
- All titles real (Applied Nutrition, Myprotein, USN, Reflex, DY Nutrition…) — genuine grid data, not a shell.
- Detector corrected: `UNKNOWN` + asin>0 → `PARTIAL` (real grid without inline price). `h2 a span` NULL → title via `h2.innerText`.
- DP `/dp/B00T7L20AQ` via the SAME proxy → `202 len=1981 gokuProps=1 AwsWaf=4` — the DP endpoint is stricter than search; browser session stays the primary DP path.
- Proxy lesson: one IP can return 200 on search + 202 on DP within 8 minutes — warm IPs cool fast; don't over-retry (burns the proxy), rotate the pool.

## Browser session (THROUGH ✅)
- search page → heading `1-48 of 150 results for "creatine"`, 58 `[data-asin]` nodes counted
- extracted 48 cards → ASIN+title+price+rating+prime. Title via `h2.innerText` (`h2 a span` = NULL in this DOM).
- DP `/dp/B00T7L20AQ` → price found, cookie-dialog=YES, title `Optimum Nutrition Micronised Creatine Monohydrate Powder, 317g ...`
- Geo note: default geo mistargeted (IDR prices); £ needs a UK postcode + en-GB.
