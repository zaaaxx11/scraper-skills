# How to Use

## 1. Requirements

- Python 3.11+ (`uv` recommended)
- **Bright Data API key** (for the primary L5 path) — sign up at brightdata.com, add credit, copy the key from the dashboard.
- Never write the key into code or public chat. Store it as env or file:

```bash
export BRIGHTDATA_KEY="your-key-here"
# or
echo -n "your-key-here" > ~/.brightdata_key && chmod 600 ~/.brightdata_key
```

> Wrappers read `BRIGHTDATA_KEY` first, then fall back to `~/.brightdata_key`.
> This repo contains NO keys — scan before every push.

## 2. Install (only for the free L0–L3 path)

```bash
uv venv .venv && source .venv/bin/activate
uv pip install "scrapling[fetchers]"
scrapling install          # downloads the browser (NOT `python -m scrapling install`)
```

The L5 path (Bright Data) needs no install — just `curl` + Python stdlib.

## 3. Examples (Amazon.co.uk)

```bash
cd skills/amazon-uk-scraper/scripts
# L5 — search amazon.co.uk (JSONL → saved cleanly)
python bd_amazon.py search "creatine" 1
# L5 — product detail (100 fields: price, seller, variants, rating)
python bd_amazon.py dp B00T7L20AQ
# L0–L3 — free ladder (needs a HEALTHY geo proxy)
python validate_proxies.py 40        # validate first → live_proxies.json
python amazon_ladder.py "creatine" 3 # L0→L1→L3 automatically
python l3_verify.py "creatine"       # verify + always save HTML + parse
```

## 4. Troubleshooting

| Symptom | Meaning | Fix |
|---|---|---|
| `Customer is not active` | TRANSIENT Bright Data error (not a dead key) | retry 1× + sleep 5s (wrappers do this automatically) |
| `202` + challenge markers (`gokuProps`, etc.) | WAF challenge shell | climb the ladder / rotate proxy / use L5 |
| `503` / sorry page | IP throttled | rotate proxy, cooldown ~10 min, do NOT over-retry |
| `200` + 0 data markers + consent wall | session hasn't accepted cookies | click Accept via page action / persist cookies |
| `200` + data but NO inline price | `SUCCESS_PARTIAL` — variant-family grid | real price lives on the per-variant detail page |
| `json.loads` → `Extra data` | search response is JSONL | parse line-by-line (see `bd_amazon.py`) |
| `currency: "GPB"` | Bright Data typo for GBP | normalize (wrapper already does) |
| Wrong geo/currency | request exited in the wrong region | set `zipcode` (L5) / `locale` + postcode (L3) |
| `ModuleNotFoundError: browserforge/msgspec` | installed without extras | `pip install "scrapling[fetchers]"` |
| `.get()` vs `.fetch()` AttributeError | `Fetcher` uses `.get()`, browser fetchers use `.fetch()` | don't mix them up |

## 5. Honest limits

- Free proxies (Proxifly) are ~2–4% alive — always validate before use, never use raw.
- One IP can go `200` on search then `202` on detail within 8 minutes — rotate the pool, don't burn one proxy.
- Detail endpoints are usually stricter than search — detail pages are safest via L5 or a browser session.
- Search grids are sometimes variant-family: IDs + titles present, final price only on detail.
