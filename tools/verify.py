#!/usr/bin/env python3
"""Testar alla poster i data/catalog.json igen och uppdaterar status + last_checked.

Användning:
    python3 tools/verify.py                 # testa alla
    python3 tools/verify.py --ids A013 C101 # testa vissa
    python3 tools/verify.py --dry-run       # visa ändringar utan att skriva

Statuslogik (samma som när katalogen byggdes):
    verifierad  - exempel/endpoint/dokumentation svarar (2xx/3xx, eller 400/405/406 = tjänsten lever men vill ha andra parametrar)
    nyckel      - 401/403 och posten anger att nyckel/registrering krävs
    blockerad   - ingen anslutning/502/403 men posten var tidigare bekräftad; sajten blockerar troligen datacenter-IP
    overifierad - inget bekräftat svar
    stängd      - sätts bara manuellt (ej öppen data); skriptet rör inte sådana poster

Poster som går från verifierad till något sämre listas i slutet, så att en människa kan titta på dem.
"""
import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog.json"
UA = "Mozilla/5.0 (oppna-data-sverige verify; +https://github.com/frenik-4/oppna-data-sverige)"


def first_url(text):
    if not text or not isinstance(text, str):
        return None
    m = re.search(r"https?://[^\s'\"<>]+", text)
    if not m:
        return None
    u = m.group(0).rstrip(").,;")
    return None if "{" in u else u


def probe(url):
    if not url:
        return None
    try:
        out = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-L", "--max-redirs", "3", "-m", "20",
             "-H", "Accept-Encoding: gzip", "-A", UA, "-w", "%{http_code}", url],
            capture_output=True, text=True, timeout=30)
        return int(out.stdout or 0)
    except Exception:
        return 0


def classify(r):
    if r.get("status") == "stängd":
        return r["status"], None
    s = probe(first_url(r.get("example")) or first_url(r.get("endpoint")))
    if s in (None, 404):
        s2 = probe(first_url(r.get("url")))
        if s2 is not None:
            s = s2
    auth = (r.get("auth") or "").lower()
    needs_key = any(w in auth for w in ("nyckel", "registrering", "avtal", "delvis"))
    if s and (200 <= s < 400 or s in (400, 405, 406)):
        return "verifierad", s
    if s in (401, 403) and needs_key:
        return "nyckel", s
    if s in (0, 403, 429, 502, 503) and r.get("status") in ("verifierad", "nyckel", "blockerad"):
        return "blockerad", s
    return "overifierad", s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rows = json.loads(CATALOG.read_text(encoding="utf-8"))
    todo = [r for r in rows if not a.ids or r["id"] in a.ids]
    with ThreadPoolExecutor(16) as ex:
        results = list(ex.map(classify, todo))
    today = dt.date.today().isoformat()
    changed, worse = [], []
    rank = {"verifierad": 0, "nyckel": 1, "blockerad": 2, "overifierad": 3, "stängd": 4}
    for r, (status, code) in zip(todo, results):
        if status != r.get("status"):
            changed.append((r["id"], r["name"], r.get("status"), status, code))
            if rank.get(status, 9) > rank.get(r.get("status"), 9):
                worse.append((r["id"], r["name"], r.get("status"), status, code))
            r["status"] = status
        r["last_checked"] = today
    print(f"Testade {len(todo)} poster, {len(changed)} bytte status.")
    for c in changed:
        print("  %s %-50s %s -> %s (HTTP %s)" % c)
    if worse:
        print("\nFörsämrade (bör granskas manuellt):")
        for c in worse:
            print("  %s %-50s %s -> %s (HTTP %s)" % c)
    if not a.dry_run:
        CATALOG.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
