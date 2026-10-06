# Framework

## 1. Musuh: AWS WAF (bukan Cloudflare)

Sinyal: `window.gokuProps` + `AwsWafIntegration/challenge.js` + `token.awswaf.com`.
Implikasi: Turnstile solver / `solve_cloudflare=True` TIDAK ngefek. Masalahnya =
**bot-fingerprint + IP reputation + cookie consent**, bukan rule-bypass.
Teknik injeksi (encoding, HPP, chunked, path tricks, smuggling) DIBUANG — cuma menaikkan risiko ban.

## 2. Detector — 7 sinyal (satu-satunya gerbang keputusan)

```
detect(status, html):
  202 / gokuProps / awswaf          → WAF_202        (naik ladder)
  503 / Amazonsorry                 → THROTTLE_503   (ganti proxy + cooldown)
  200 + 0 asin + cookie preferences → COOKIE_WALL    (accept + persist cookie)
  200 + 0 asin (tanpa cookie)       → EMPTY_200      (retry / naik ladder)
  200 + asin + £/a-price-whole      → SUCCESS        (parse, selesai)
  200 + asin TANPA harga inline     → SUCCESS_VARIANT (grid variant-family → DP)
  else                              → OTHER          (anggap gagal, jangan parse)
```

`SUCCESS_VARIANT` ditemukan 2026-10-06: `200 / 964KB / 53 asin`, `a-price-whole = 0`,
`a-offscreen` hanya `"N sizes, N flavours"` — judul 100% real (Applied, Myprotein, USN…).

## 3. Arsitektur fallback

```
probe murah (L1, 1 req) → detector → L5 langsung bila ada key
                        → L3 + proxy sehat (validasi dulu!) bila tanpa key
                        → L4 browser session bila L3 mentok
                        → 503 = STOP + cooldown 10 mnt (bukan retry)
```

Prinsip:
- **Murah dulu, mahal kemudian** — 1 req Fetcher sebelum bakar browser/proxy.
- **Validasi sebelum pakai** — proxy gratis 2–5% hidup; pool sehat disimpan, bukan diasumsikan.
- **Sukses = konten, bukan status** — `data-asin > 0` + harga/judul real + file di disk.
- **Rotasi, bukan over-retry** — 1 IP hangat mendingin dalam hitungan menit.

## 4. Decision matrix

| Kondisi | Jalur |
|---|---|
| Ada Bright Data key + kredit | L5 (search + DP) — tanpa drama WAF |
| Tanpa key, butuh search grid | L3 (Stealthy + proxy GB tervalidasi) |
| L3 202/503 semua proxy | L4 browser session (search OK, DP OK) |
| DP via proxy 202 | DP via L5 / browser (endpoint DP lebih strict) |
| Grid tanpa harga inline | SUCCESS_VARIANT → DP per-variant, jangan klaim harga grid |
| Butuh £ (dapat IDR) | zipcode UK (L5) / locale en-GB + UK postcode (L3/L4) |

## 5. Selector grid (diukur dari DOM asli)

- Kartu: `[data-component-type="s-search-result"][data-asin]` → `data-asin` = ASIN
- Judul: `h2.innerText` (**BUKAN** `h2 a span` — NULL di DOM ini)
- Harga inline: `.a-price .a-offscreen` / `a-price-whole` (bisa ABSEN di variant-family)
- Rating: `[aria-label*="out of 5 stars"]` · Prime: `/prime/i` di teks kartu
- Shipping strict: `#mir-layout-DELIVERY_BLOCK` (`FREE delivery` → 0, else `£X.99`)
- `totalPrice = price + shipping`; tie-break: min → most-common → `amazon-uk`
