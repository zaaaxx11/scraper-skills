# Workflow

End-to-end: from a raw keyword → clean, priced, geo-correct data.

```mermaid
flowchart TD
    A[keyword / product URL list] --> B{BRIGHTDATA_KEY set?}
    B -->|yes| C[L5 search: wrapper search kw pages]
    C --> D[JSON: id + name + final_price\n+ rating + prime + sponsored]
    D --> E[per-ID: wrapper detail call]
    E --> F[detail fields: seller + variants\n+ shipping + reviews]
    F --> G[totalPrice = price + shipping\ntie-break: min → most-common → first-party]
    G --> H✅[CSV/JSON deliverable]

    B -->|no| I[L1 cheap probe\n1 request]
    I --> J{detector}
    J -->|challenge shell| K[validate proxies\ntake a healthy geo pool]
    K --> L[L3 Stealthy + proxy\nwait for data selector]
    L --> M{detector}
    M -->|SUCCESS / PARTIAL| N[parse grid\nIDs + titles]
    N --> O[per-variant detail\nvia browser session]
    O --> G
    M -->|blocked| P[rotate proxy\nmax 3-5x]
    P -->|exhausted| Q[cooldown 10 min\nor switch to L5]
    J -->|data markers| N
```

## Stages

1. **Probe (L1)** — one cheap request, classify the signal. Never burn an expensive proxy first.
2. **Validate proxies** — batches of 40–80 via fast curl (`--max-time 15`), keep responders (`code != 0`). Expect 2–5% alive.
3. **Harvest (L5/L3/L4)** — search/listing page first (IDs + titles), then detail per variant (final price).
4. **Verify from disk** — `200` alone is NOT proof. Required: data markers `> 0` + (price markers or real titles) + saved file.
5. **Match & deliver** — `totalPrice = price + shipping`; tie-break: lowest price → most frequent → first-party seller.

## Browser-session harvest rules

- Small batches (~14 IDs/call, concurrency ≤4, ~250ms gap) — return the map in the same call.
- `200 → 503` means STOP + cooldown, not blind retry.
- Don't trust `localStorage` (interstitials wipe it) or `127.0.0.1` sinks (mixed-content block).
- Persist per-batch to disk — sessions can die at any time.
