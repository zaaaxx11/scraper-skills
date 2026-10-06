"""Validate Proxifly GB proxies: fast curl per proxy, keep responders.
Run: python3 validate_proxies.py [N=40] -> live_proxies.json
"""
import json
import subprocess
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
TARGET = "https://www.amazon.co.uk/s?k=creatine"


def fetch_pool() -> list:
    """Fetch the GB proxy list from Proxifly (jsDelivr, 5-min refresh)."""
    url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/countries/GB/data.json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode())


def test_proxy(proxy: str, timeout: int = 15) -> dict:
    """curl via proxy, return {proxy, code, size, ms}. code=0 means the proxy is dead."""
    import time
    t0 = time.time()
    try:
        p = subprocess.run(
            ["curl", "-s", "-o", "/tmp/probe_body.tmp", "-w", "%{http_code} %{size_download}",
             "-x", proxy, "--max-time", str(timeout), TARGET],
            capture_output=True, text=True, timeout=timeout + 5)
        ms = int((time.time() - t0) * 1000)
        parts = p.stdout.strip().split()
        code = int(parts[0]) if parts and parts[0].isdigit() else 0
        size = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return {"proxy": proxy, "code": code, "size": size, "ms": ms}
    except Exception as e:
        return {"proxy": proxy, "code": 0, "size": 0, "ms": -1, "err": str(e)[:80]}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    pool = fetch_pool()
    print(f"pool GB: {len(pool)}", flush=True)
    import random
    random.shuffle(pool)
    cand = [x["proxy"] for x in pool[:n]]
    live = []
    for i, px in enumerate(cand):
        r = test_proxy(px)
        flag = "LIVE" if r["code"] else "dead"
        print(f"[{i+1}/{len(cand)}] {flag} {px[:40]} code={r['code']} size={r['size']} ms={r['ms']}", flush=True)
        if r["code"]:
            live.append(r)
    live.sort(key=lambda x: x["ms"])
    with open("live_proxies.json", "w") as f:
        json.dump(live, f, indent=1)
    print(f"ALIVE: {len(live)}/{len(cand)} -> live_proxies.json", flush=True)
    for r in live[:10]:
        print(f"  {r['proxy']} code={r['code']} size={r['size']} ms={r['ms']}", flush=True)


if __name__ == "__main__":
    main()
