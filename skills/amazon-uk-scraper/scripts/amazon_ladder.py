"""Amazon.co.uk ladder scraper — L0 probe -> L1 Fetcher -> L3 Stealthy+GB proxy.
Detector: 202/gokuProps | 503 Amazonsorry | 200 cookie-wall | 200 + data-asin = SUKSES.
Run: source .venv/bin/activate && python3 amazon_ladder.py "creatine" 2
Fakta: L1 202/2012B/goku=True (2026-10-06). L3 target: 200 + data-asin + £.
Asumsi: Proxifly GB socks5 publik (fluktuatif) — pool sehat divalidasi dulu.
"""
import json
import random
import re
import sys
import urllib.parse
import urllib.request

SEARCH = "https://www.amazon.co.uk/s?k={q}"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def detect(status: int, html: str) -> str:
    """Klasifikasi sinyal blokir Amazon.
    Return: WAF_202 | THROTTLE_503 | COOKIE_WALL | EMPTY_200 | SUCCESS | SUCCESS_VARIANT | OTHER.
    SUCCESS_VARIANT = grid real (data-asin>0) tapi tanpa harga inline (variant-family,
    harga di DP). Ditemukan 2026-10-06: 200/964KB/53 asin, a-offscreen cuma 'N sizes'.
    """
    low = html.lower()
    n_asin = html.count("data-asin")
    if status == 202 or "gokuprops" in low or "awswaf" in low:
        return "WAF_202"
    if status == 503 or "amazonsorry" in low:
        return "THROTTLE_503"
    if status == 200 and n_asin == 0:
        if "cookie" in low and "preferences" in low:
            return "COOKIE_WALL"
        return "EMPTY_200"
    if status == 200 and n_asin > 0:
        if "£" in html or "&pound;" in html or "a-price-whole" in html:
            return "SUCCESS"
        return "SUCCESS_VARIANT"  # grid real, harga di DP per-variant
    return "OTHER"


def parse_grid(html: str) -> list:
    """Parse kartu search-result dari HTML sukses. Return list dict(asin,title,price,prime)."""
    from selectolax.parser import HTMLParser  # noqa - fallback ke regex bila absen
    raise NotImplementedError  # placeholder, implementasi regex di bawah


def parse_grid_regex(html: str) -> list:
    """Parse grid tanpa dependency tambahan (regex, cukup untuk proof)."""
    cards = re.findall(r'data-asin="(B0[A-Z0-9]{8})"(.*?)(?=data-asin="B0|\Z)', html, re.S)
    out = []
    for asin, chunk in cards:
        chunk = chunk[:8000]
        title = re.search(r"<h2[^>]*>.*?<span[^>]*>(.*?)</span>", chunk, re.S)
        price = re.search(r'class="a-offscreen">([^<]*£[^<]*)<', chunk)
        prime = "prime" in chunk.lower()
        out.append({
            "asin": asin,
            "title": (re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else "")[:120],
            "price": price.group(1).strip() if price else "",
            "prime": prime,
        })
    return out


def l0_probe(query: str) -> tuple:
    """L0: curl polos — ekspektasi gagal (202/cookie-wall), cuma buat deteksi sinyal."""
    url = SEARCH.format(q=urllib.parse.quote_plus(query))
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "ignore")
            return r.status, html
    except Exception as e:
        code = getattr(e, "code", 0) or 0
        try:
            html = e.read().decode("utf-8", "ignore")
        except Exception:
            html = ""
        return code, html


def l1_fetch(query: str) -> tuple:
    """L1: Fetcher murah — baseline. Bukti: 202/2012B di DC IP."""
    from scrapling.fetchers import Fetcher
    url = SEARCH.format(q=urllib.parse.quote_plus(query))
    p = Fetcher.get(url, impersonate="chrome", stealthy_headers=True, timeout=30)
    body = p.body.decode("utf-8", "ignore") if isinstance(p.body, bytes) else p.body
    return p.status, body


def gb_pool(n: int = 10) -> list:
    """Ambil n proxy GB acak dari Proxifly (jsDelivr, update 5 mnt)."""
    url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/GB/data.json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode())
    random.shuffle(data)
    return [x["proxy"] for x in data[:n] if x.get("proxy")]


def l3_stealth(query: str, proxy: str, timeout_ms: int = 60000) -> tuple:
    """L3: StealthyFetcher + proxy GB. Senjata utama — target SUCCESS."""
    from scrapling.fetchers import StealthyFetcher
    url = SEARCH.format(q=urllib.parse.quote_plus(query))
    p = StealthyFetcher.fetch(
        url, headless=True, network_idle=True, proxy=proxy,
        block_webrtc=True, locale="en-GB", timezone_id="Europe/London",
        wait_selector='[data-component-type="s-search-result"]',
        timeout=timeout_ms,
    )
    body = p.body.decode("utf-8", "ignore") if isinstance(p.body, bytes) else (p.body or "")
    status = getattr(p, "status", 200) or 200
    return status, body


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "creatine"
    max_proxy = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    print(f"=== L0 probe: {query} ===", flush=True)
    s0, h0 = l0_probe(query)
    print(f"L0: status={s0} len={len(h0)} signal={detect(s0, h0)}", flush=True)

    print("=== L1 Fetcher ===", flush=True)
    s1, h1 = l1_fetch(query)
    print(f"L1: status={s1} len={len(h1)} signal={detect(s1, h1)}", flush=True)

    print("=== L3 Stealthy + GB proxy ===", flush=True)
    proxies = gb_pool(max_proxy * 2)
    print(f"pool: {len(proxies)} proxies", flush=True)
    for i, px in enumerate(proxies[:max_proxy]):
        print(f"-- try {i+1}/{max_proxy} proxy={px[:30]}...", flush=True)
        try:
            s3, h3 = l3_stealth(query, px)
        except Exception as e:
            print(f"   ERROR: {type(e).__name__}: {str(e)[:200]}", flush=True)
            continue
        sig = detect(s3, h3)
        print(f"   status={s3} len={len(h3)} asin={h3.count('data-asin')} signal={sig}", flush=True)
        if sig == "SUCCESS":
            items = parse_grid_regex(h3)
            print(f"   TEMBUS ✅ {len(items)} kartu", flush=True)
            for it in items[:5]:
                print(f"   - {it['asin']} | {it['price']} | prime={it['prime']} | {it['title'][:60]}", flush=True)
            with open("l3_success.html", "w") as f:
                f.write(h3)
            with open("l3_items.json", "w") as f:
                json.dump(items, f, indent=1)
            print("   tersimpan: l3_success.html + l3_items.json", flush=True)
            return
    print("L3 BELUM tembus — coba lagi / tambah proxy / IP VPS kena throttle berat.", flush=True)


if __name__ == "__main__":
    main()
