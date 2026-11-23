#!/usr/bin/env python3
"""MCP-server som exponerar katalogen över öppna svenska datakällor för Claude.

Två sätt att köra:
  stdio (lokalt, startas av Claude Code):
      python3 mcp/server.py
  HTTP (på hemservern, nås av alla projekt via Tailscale):
      python3 mcp/server.py --http --port 8002

Källan läses från OPPNA_DATA_DIR (standard: ../data relativt denna fil) och
läses om automatiskt när filen ändras, så en `git pull` räcker för att få nytt innehåll.
"""
import argparse
import json
import os
import pathlib
import re

from mcp.server.fastmcp import FastMCP

DATA_DIR = pathlib.Path(os.environ.get("OPPNA_DATA_DIR", pathlib.Path(__file__).resolve().parent.parent / "data"))

_cache = {}


def _load(name):
    p = DATA_DIR / name
    mtime = p.stat().st_mtime
    if _cache.get(name, (None,))[0] != mtime:
        _cache[name] = (mtime, json.loads(p.read_text(encoding="utf-8")))
    return _cache[name][1]


def _short(r):
    return {k: r.get(k) for k in ("id", "name", "provider", "category", "status", "auth", "access", "endpoint", "data")}


def _match(r, words):
    hay = " ".join(str(r.get(k) or "") for k in ("name", "provider", "data", "tips", "use_cases", "subcategory", "endpoint", "category")).lower()
    return all(w in hay for w in words)


parser = argparse.ArgumentParser()
parser.add_argument("--http", action="store_true", help="kör som streamable HTTP i stället för stdio")
parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", type=int, default=8002)
args = parser.parse_args()

mcp = FastMCP("oppna-data-sverige", host=args.host, port=args.port)


@mcp.tool()
def sok_kallor(fraga: str = "", kategori: str = "", bara_utan_nyckel: bool = False,
               bara_fungerande: bool = False, max_antal: int = 25) -> list[dict]:
    """Sök bland öppna svenska databaser/API:er. `fraga` matchas mot namn, utgivare,
    databeskrivning och tips (alla ord måste finnas). `kategori` är en exakt kategori
    från lista_kategorier(). Returnerar en kort sammanfattning per källa; använd
    hamta_kalla(id) för endpoint, exempelanrop och tips."""
    words = [w for w in re.split(r"\s+", fraga.lower()) if w]
    out = []
    for r in _load("catalog.json"):
        if kategori and r.get("category") != kategori:
            continue
        if bara_utan_nyckel and not (r.get("auth") or "").lower().startswith("ingen"):
            continue
        if bara_fungerande and r.get("status") not in ("verifierad", "nyckel"):
            continue
        if words and not _match(r, words):
            continue
        out.append(_short(r))
    return out[:max_antal]


@mcp.tool()
def hamta_kalla(id: str) -> dict:
    """Hämta hela posten för en källa: dokumentations-URL, endpoint, exempelanrop,
    autentisering, licens, format, tips och senaste teststatus."""
    for r in _load("catalog.json"):
        if r["id"] == id:
            return r
    return {"fel": f"Ingen källa med id {id}"}


@mcp.tool()
def lista_kategorier() -> dict:
    """Lista alla kategorier med antal källor i varje."""
    counts = {}
    for r in _load("catalog.json"):
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    return {c: counts.get(c, 0) for c in _load("meta.json")["categories"]}


@mcp.tool()
def sok_ideer(fraga: str = "", kategori: str = "") -> list[dict]:
    """Sök bland verktygsidéer som kombinerar flera källor. Varje idé listar
    källornas id, som kan slås upp med hamta_kalla."""
    words = [w for w in re.split(r"\s+", fraga.lower()) if w]
    out = []
    for i in _load("ideas.json"):
        if kategori and i.get("category") != kategori:
            continue
        hay = json.dumps(i, ensure_ascii=False).lower()
        if all(w in hay for w in words):
            out.append(i)
    return out


@mcp.tool()
def kopplingsnycklar() -> str:
    """Beskrivning av nycklarna som används för att koppla ihop svenska datakällor
    (kommunkod, DeSO, koordinatsystem, organisationsnummer, elområde, Wikidata m.m.)."""
    html = _load("meta.json")["keys_html"]
    text = re.sub(r"<li>", "- ", html)
    text = re.sub(r"<h2>(.*?)</h2>", r"\n## \1\n", text)
    return re.sub(r"<[^>]+>", "", text).strip()


if __name__ == "__main__":
    mcp.run(transport="streamable-http" if args.http else "stdio")
