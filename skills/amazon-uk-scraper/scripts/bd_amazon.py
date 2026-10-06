"""Bright Data primary path for Amazon.co.uk — search + DP via datasets API.
Key: ~/.brightdata_key (chmod 600) or BRIGHTDATA_KEY env. Dataset search=gd_lwdb4vjm1ehb499uxs,
DP=gd_l7q7dkf244hwjntr0. Currency field typo 'GPB' (=GBP) — normalized.
Run: python3 bd_amazon.py search "creatine" | python3 bd_amazon.py dp B00T7L20AQ
Proven 2026-10-06: search 50 rec/49 harga, DP 100 keys final_price 9.89.
"""
import json
import subprocess
import sys

SEARCH_DS = "gd_lwdb4vjm1ehb499uxs"
DP_DS = "gd_l7q7dkf244hwjntr0"

# dropship-friendly column order
SEARCH_COLS = ["asin", "name", "brand", "final_price", "initial_price", "currency",
               "rating", "num_ratings", "is_prime", "sponsored", "badge", "sold",
               "delivery", "url", "page_number", "rank_on_page"]


def key() -> str:
    """Read the Bright Data API key: BRIGHTDATA_KEY env first, ~/.brightdata_key fallback.
    Never hardcode the key — it must NEVER enter the repo."""
    import os
    env = os.environ.get("BRIGHTDATA_KEY", "").strip()
    if env:
        return env
    return open(os.path.expanduser("~/.brightdata_key")).read().strip()


def call(dataset: str, payload: dict, timeout: int = 120) -> str:
    """POST the datasets API, return the raw body. 'Customer is not active' is transient -> retry 1x."""
    import time
    body = ""
    for attempt in range(2):
        p = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout),
             "-H", f"Authorization: Bearer {key()}",
             "-H", "Content-Type: application/json",
             "-d", json.dumps(payload),
             f"https://api.brightdata.com/datasets/v3/scrape?dataset_id={dataset}&notify=false&include_errors=true"],
            capture_output=True, text=True, timeout=timeout + 10)
        body = p.stdout.strip()
        if body == "Customer is not active" and attempt == 0:
            time.sleep(5)
            continue
        return body
    return body


def norm_currency(c: str) -> str:
    return {"GPB": "GBP"}.get((c or "").upper(), c or "")


def bd_search(keyword: str, pages: int = 1, domain: str = "https://www.amazon.co.uk") -> list:
    body = call(SEARCH_DS, {"input": [{"keyword": keyword, "url": domain,
                                       "pages_to_search": pages}], "limit_per_input": None})
    recs = [json.loads(l) for l in body.splitlines() if l.strip().startswith("{")]
    for r in recs:
        r["currency"] = norm_currency(r.get("currency"))
    return recs


def bd_dp(url_or_asin: str, zipcode: str = "SW1A 1AA") -> dict:
    url = url_or_asin if url_or_asin.startswith("http") else f"https://www.amazon.co.uk/dp/{url_or_asin}"
    body = call(DP_DS, {"input": [{"url": url, "zipcode": zipcode}], "limit_per_input": None})
    d = json.loads(body.splitlines()[0])
    d["currency"] = norm_currency(d.get("currency"))
    return d


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "search"
    if mode == "search":
        kw = sys.argv[2] if len(sys.argv) > 2 else "creatine"
        pages = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        recs = bd_search(kw, pages)
        json.dump(recs, open(f"bd_search_{kw}.json", "w"), indent=1)
        priced = sum(1 for r in recs if r.get("final_price"))
        print(f"search '{kw}': {len(recs)} rec, {priced} priced -> bd_search_{kw}.json", flush=True)
        for r in recs[:10]:
            print(f"  {r.get('asin')} {r.get('final_price')} {r.get('currency')} prime={r.get('is_prime')} | {(r.get('name') or '')[:60]}", flush=True)
    elif mode == "dp":
        asin = sys.argv[2]
        d = bd_dp(asin)
        json.dump(d, open(f"bd_dp_{asin}.json", "w"), indent=1)
        for k in ["asin", "title", "brand", "seller_name", "final_price", "initial_price",
                  "currency", "rating", "reviews_count", "is_available", "number_of_sellers",
                  "buybox_seller", "ships_from", "bought_past_month_text"]:
            print(f"{k} = {str(d.get(k))[:120]}", flush=True)
    else:
        print("usage: bd_amazon.py search <keyword> [pages] | bd_amazon.py dp <ASIN>", flush=True)


if __name__ == "__main__":
    main()
