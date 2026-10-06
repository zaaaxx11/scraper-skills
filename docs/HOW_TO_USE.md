# How to Use

## 1. Syarat

- Python 3.11+ (`uv` direkomendasikan)
- **Bright Data API key** (untuk jalur utama L5) — daftar di brightdata.com, isi kredit, ambil key dari dashboard.
- Key JANGAN ditulis di kode/chat publik. Simpan di env atau file:

```bash
export BRIGHTDATA_KEY="isi-key-kamu"
# atau
echo -n "isi-key-kamu" > ~/.brightdata_key && chmod 600 ~/.brightdata_key
```

> Wrapper `bd_amazon.py` baca `BRIGHTDATA_KEY` dulu, fallback `~/.brightdata_key`.
> Repo ini TIDAK berisi key siapa pun — scan sebelum push.

## 2. Install (hanya untuk jalur gratis L0–L3)

```bash
uv venv .venv && source .venv/bin/activate
uv pip install "scrapling[fetchers]"
scrapling install          # download browser (bukan `python -m scrapling install`)
```

Jalur L5 (Bright Data) TIDAK butuh install apa pun — cuma `curl` + Python stdlib.

## 3. Contoh

```bash
cd skills/amazon-uk-scraper/scripts
# L5 — search amazon.co.uk (JSONL → disimpan rapi)
python bd_amazon.py search "creatine" 1
# L5 — detail produk (100 fields: harga, seller, variants, rating)
python bd_amazon.py dp B00T7L20AQ
# L0–L3 — ladder gratis (butuh proxy GB sehat)
python validate_proxies.py 40        # validasi dulu, simpan live_proxies.json
python amazon_ladder.py "creatine" 3 # L0→L1→L3 otomatis
python l3_verify.py "creatine"       # verify + simpan HTML + parse
```

## 4. Troubleshooting

| Gejala | Artinya | Fix |
|---|---|---|
| `Customer is not active` | TRANSIENT Bright Data (bukan key mati) | retry 1× + sleep 5s (wrapper sudah otomatis) |
| `202` + `gokuProps` | AWS WAF shell | naik ladder / ganti proxy / pakai L5 |
| `503` / `Amazonsorry` | IP di-throttle | ganti proxy, cooldown ~10 mnt, JANGAN over-retry |
| `200` + 0 `data-asin` + cookie wall | sesi belum accept cookie | `page_action` klik Accept / persist cookie |
| `200` + asin TANPA harga | `SUCCESS_VARIANT` — grid variant-family | harga ada di DP per-variant |
| `json.loads` → `Extra data` | response search = JSONL | parse per-baris (lihat `bd_amazon.py`) |
| `currency: "GPB"` | typo Bright Data = GBP | normalisasi (wrapper sudah) |
| Harga IDR bukan £ | geo Indonesia | `zipcode SW1A 1AA` (L5) / `locale en-GB` (L3) |
| `ModuleNotFoundError: browserforge/msgspec` | install tanpa extra | `pip install "scrapling[fetchers]"` |
| `.get()` vs `.fetch()` AttributeError | Fetcher pakai `.get()`, browser fetcher pakai `.fetch()` | jangan ketuker |

## 5. Batasan jujur

- Proxy gratis (Proxifly) ~2–4% hidup — selalu validasi dulu, jangan pakai mentah.
- 1 IP bisa `200` di search lalu `202` di DP dalam 8 menit — rotasi pool, jangan burn 1 proxy.
- Endpoint DP lebih strict dari search (via proxy); DP paling aman via L5 atau browser session.
- Grid search kadang variant-family: ASIN + judul ada, harga final di DP.
