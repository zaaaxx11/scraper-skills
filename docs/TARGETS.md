# Targets

Support matrix. **Proven** = `SUCCESS` with saved evidence in the skill's `references/`.
**Wanted** = follow `skills/_template/` and log raw probes (pass AND fail).

## Proven

| Target | Protector | L5 datasets (Bright Data) | Free path | Evidence |
|---|---|---|---|---|
| `amazon.co.uk` | AWS WAF (`gokuProps` + `challenge.js`) | search `gd_lwdb4vjm1ehb499uxs` · product `gd_l7q7dkf244hwjntr0` | L3 Stealthy + GB proxy ✅ / L4 browser ✅ | [`amazon-uk-scraper/references/`](skills/amazon-uk-scraper/references/) |
| `amazon.com` | AWS WAF (same family) | same dataset IDs, `url: https://www.amazon.com` | L3 pattern should transfer (not yet probed) | — |

> The two dataset IDs above are verified with `amazon.co.uk` + `amazon.com` URLs.
> Other Amazon locales (`.de`, `.es`, …) take the same `url` parameter pattern but are UNPROBED.

## Wanted (copy `skills/_template/`)

| Target | Notes |
|---|---|
| `amazon.de` / `amazon.es` / other locales | Same datasets likely work — probe + log |
| `ebay.*` | Needs its own detector profile + probe log |
| `walmart.com` | Needs its own detector profile + probe log |
| `idealo.*` (price comparison) | Query needs a SIZE token or tiles return 0; Amazon seller data only via session `fetch` on `/gp/aag/main` (curl/Jina/Playwright get 503) |

## How to find a Bright Data dataset ID

1. Bright Data dashboard → Datasets / Data Collector → pick the target template.
2. The `dataset_id` looks like `gd_xxxxxxxxxxxxxxx` — pin it in the skill's `L5_DATASETS`.
3. Verify with one search call + one detail call, save both JSONs under `references/`.
4. Never invent dataset IDs — only list ones confirmed by a real API response.
