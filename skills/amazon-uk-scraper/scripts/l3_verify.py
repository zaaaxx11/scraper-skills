"""L3 verify: re-fetch via the winning proxy, ALWAYS save HTML, parse + prove.
Run: python3 l3_verify.py "creatine" -> l3_verify.html + l3_verify.json
"""
import json
import re
import sys
import urllib.parse


def parse_grid(html: str) -> list:
    cards = re.findall(r'data-asin="(B0[A-Z0-9]{8})"(.*?)(?=data-asin="B0|\Z)', html, re.S)
    out = []
    for asin, chunk in cards:
        chunk = chunk[:8000]
        title = re.search(r"<h2[^>]*>.*?<span[^>]*>(.*?)</span>", chunk, re.S)
        if not title:
            title = re.search(r"<h2[^>]*>(.*?)</h2>", chunk, re.S)
        price = re.search(r'class="a-offscreen">([^<]{1,30})<', chunk)
        out.append({
            "asin": asin,
            "title": (re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else "")[:120],
            "price": price.group(1).strip() if price else "",
        })
    return out


def main() -> None:
    from scrapling.fetchers import StealthyFetcher
    query = sys.argv[1] if len(sys.argv) > 1 else "creatine"
    proxy = "http://51.170.133.249:80"  # winner 08:18 — 200/979KB/53 asins
    url = "https://www.amazon.co.uk/s?k=" + urllib.parse.quote_plus(query)
    print(f"fetch via {proxy} ...", flush=True)
    try:
        p = StealthyFetcher.fetch(
            url, headless=True, network_idle=True, proxy=proxy,
            block_webrtc=True, locale="en-GB", timezone_id="Europe/London",
            wait_selector='[data-component-type="s-search-result"]',
            timeout=120000,
        )
        body = p.body.decode("utf-8", "ignore") if isinstance(p.body, bytes) else (p.body or "")
        status = getattr(p, "status", 200) or 200
    except Exception as e:
        print(f"FETCH ERROR: {type(e).__name__}: {str(e)[:300]}", flush=True)
        # tetap coba baca body parsial bila ada
        body, status = "", 0
    open("l3_verify.html", "w").write(body)
    print(f"status={status} len={len(body)} asin_attr={body.count('data-asin')} gbp={body.count(chr(163))} goku={'gokuprops' in body.lower()} cookie={'cookie preferences' in body.lower()}", flush=True)
    print(f"HTML saved: l3_verify.html ({len(body)} bytes)", flush=True)
    items = parse_grid(body)
    print(f"cards parsed: {len(items)}", flush=True)
    for it in items[:10]:
        print(f"  - {it['asin']} | {it['price']} | {it['title'][:60]}", flush=True)
    json.dump({"status": status, "len": len(body), "items": items}, open("l3_verify.json", "w"), indent=1)
    print("items -> l3_verify.json", flush=True)


if __name__ == "__main__":
    main()
