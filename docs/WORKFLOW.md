# Workflow

End-to-end: dari keyword mentah → data harga UK siap pakai.

```mermaid
flowchart TD
    A[keyword / ASIN list] --> B{ada BRIGHTDATA_KEY?}
    B -->|ya| C[L5 search: bd_amazon.py search kw pages]
    C --> D[JSON: asin + name + final_price GBP\n+ rating + prime + sponsored]
    D --> E[per-ASIN: bd_amazon.py dp ASIN]
    E --> F[DP 100 keys: seller + variants\n+ shipping + reviews]
    F --> G[totalPrice = price + shipping\ntie-break: min → most-common → amazon-uk]
    G --> H✅[deliverable CSV/JSON]

    B -->|tidak| I[L1 Fetcher probe\nmurah, 1 req]
    I --> J{detector}
    J -->|202 WAF| K[validate_proxies.py\nambil pool GB sehat]
    K --> L[L3 Stealthy + proxy\nwait_selector data-asin]
    L --> M{detector}
    M -->|SUCCESS / VARIANT| N[parse grid\nASIN + judul]
    N --> O[DP per-variant\nvia browser session]
    O --> G
    M -->|202/503| P[ganti proxy\nmax 3-5x]
    P -->|habis| Q[cooldown 10 mnt\natau pakai L5]
    J -->|200 + asin| N
```

## Tahapan

1. **Probe (L1)** — 1 request murah, klasifikasi sinyal. Jangan langsung bakar proxy mahal.
2. **Validasi proxy** — batch 40–80 via curl cepat (`--max-time 15`), simpan yang `code != 0`. Ekspektasi 2–5% hidup.
3. **Harvest (L5/L3/L4)** — search page dulu (ASIN + judul), baru DP per-variant (harga final).
4. **Verify dari disk** — `200` saja bukan bukti. Wajib: `data-asin > 0` + (`£`/`a-price-whole` atau judul real) + file tersimpan.
5. **Match & deliver** — `totalPrice = price + shipping`; tie-break harga min → frekuensi terbanyak → `amazon-uk`.

## Aturan panen sesi browser

- Batch kecil (~14 ID/call, concurrency ≤4, gap ~250ms) — return map di call yang sama.
- `200 → 503` = sinyal BERHENTI + cooldown, bukan retry membabi-buta.
- Jangan percaya `localStorage` (interstitial me-reset) / sink `127.0.0.1` (mixed-content block).
- Persist per-batch ke disk — sesi bisa mati kapan saja.
