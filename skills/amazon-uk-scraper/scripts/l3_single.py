"""L3 single-shot: StealthyFetcher via proxy hidup dari live_proxies.json.
Run: python3 l3_single.py "creatine" -> l3_result.json + l3_success.html (kalo tembus)
"""
import json
import re
import sys
import urllib.parse


def detect(status: int, html: str) -> str:
    low = html.lower()
    if status == 202 or "gokuprops" in low or "awswaf" in low:
        return "WAF_202"
    if status == 503 or "amazonsorry" in low:
        return "THROTTLE_503"
    if status == 200 and html.count("data-asin") == 0:
        return "COOKIE_WALL" if ("cookie" in low and "preferences" in low) else "EMPTY_200"
    if status == 200 and html.count("data-asin") > 0 and "£" in html:
        return "SUCCESS"
    return "OTHER"


def parse_grid_regex(html: str) -> list:
    cards = re.findall(r'data-asin="(B0[A-Z0-9]{8})"(.*?)(?=data-asin="B0|\Z)', html, re.S)
    out = []
    for asin, chunk in cards:
        chunk = chunk[:8000]
        title = re.search(r"<h2[^>]*>.*?<span[^>]*>(.*?)</span>", chunk, re.S)
        price = re.search(r'class="a-offscreen">([^<]*£[^<]*)<', chunk)
        out.append({
            "asin": asin,
            "title": (re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else "")[:120],
            "price": price.group(1).strip() if price else "",
            "prime": "prime" in chunk.lower(),
        })
    return out


def main() -> None:
    from scrapling.fetchers import StealthyFetcher
    query = sys.argv[1] if len(sys.argv) > 1 else "creatine"
    live = json.load(open("live_proxies.json"))
    print(f"live proxies: {len(live)}", flush=True)
    url = "https://www.amazon.co.uk/s?k=" + urllib.parse.quote_plus(query)
    results = []
    for i, entry in enumerate(live):
        px = entry["proxy"]
        print(f"-- L3 try {i+1}/{len(live)} proxy={px}", flush=True)
        try:
            p = StealthyFetcher.fetch(
                url, headless=True, network_idle=True, proxy=px,
                block_webrtc=True, locale="en-GB", timezone_id="Europe/London",
                wait_selector='[data-component-type="s-search-result"]',
                timeout=90000,
            )
            body = p.body.decode("utf-8", "ignore") if isinstance(p.body, bytes) else (p.body or "")
            status = getattr(p, "status", 200) or 200
        except Exception as e:
            print(f"   ERROR: {type(e).__name__}: {str(e)[:200]}", flush=True)
            results.append({"proxy": px, "signal": "FETCH_ERROR", "err": str(e)[:200]})
            continue
        sig = detect(status, body)
        print(f"   status={status} len={len(body)} asin={body.count('data-asin')} signal={sig}", flush=True)
        results.append({"proxy": px, "status": status, "len": len(body),
                        "asin": body.count("data-asin"), "signal": sig})
        if sig == "SUCCESS":
            items = parse_grid_regex(body)
            print(f"   TEMBUS ✅ {len(items)} kartu", flush=True)
            for it in items[:5]:
                print(f"   - {it['asin']} | {it['price']} | prime={it['prime']} | {it['title'][:60]}", flush=True)
            open("l3_success.html", "w").write(body)
            json.dump(items, open("l3_items.json", "w"), indent=1)
            break
    json.dump(results, open("l3_result.json", "w"), indent=1)
    print(f"done. results -> l3_result.json", flush=True)


if __name__ == "__main__":
    main()
