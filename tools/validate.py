#!/usr/bin/env python3
"""Kontrollerar att data/catalog.json och data/ideas.json följer schemat.

Körs i CI på varje PR. Ingen extern dependency (inget jsonschema-paket) så att
den går att köra var som helst.
"""
import json
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
meta = json.loads((ROOT / "data/meta.json").read_text(encoding="utf-8"))
cat = json.loads((ROOT / "data/catalog.json").read_text(encoding="utf-8"))
ideas = json.loads((ROOT / "data/ideas.json").read_text(encoding="utf-8"))

STATUS = {"verifierad", "nyckel", "blockerad", "overifierad", "stängd"}
PTYPES = {"myndighet", "kommun/region", "statligt bolag", "universitet/forskning",
          "ideell/community", "företag", "EU/internationell"}
REQUIRED = ["id", "name", "provider", "provider_type", "category", "status", "url", "data"]

errors = []
ids = set()
for r in cat:
    rid = r.get("id", "?")
    for k in REQUIRED:
        if not r.get(k):
            errors.append(f"{rid}: saknar fältet '{k}'")
    if rid in ids:
        errors.append(f"{rid}: id förekommer flera gånger")
    ids.add(rid)
    if r.get("category") not in meta["categories"]:
        errors.append(f"{rid}: okänd kategori '{r.get('category')}'")
    if r.get("status") not in STATUS:
        errors.append(f"{rid}: okänd status '{r.get('status')}'")
    if r.get("provider_type") not in PTYPES:
        errors.append(f"{rid}: okänd provider_type '{r.get('provider_type')}'")
    for k, v in r.items():
        if k == "formats":
            if v is not None and not isinstance(v, list):
                errors.append(f"{rid}: 'formats' ska vara en lista")
        elif v is not None and not isinstance(v, str):
            errors.append(f"{rid}: fältet '{k}' ska vara text, är {type(v).__name__}")
    ev = r.get("env_var")
    if ev and not re.fullmatch(r"[A-Z][A-Z0-9_]*", ev):
        errors.append(f"{rid}: env_var '{ev}' ska vara VERSALER_MED_UNDERSTRECK")
    if ev and not any(w in (r.get("auth") or "").lower() for w in ("nyckel", "registrering", "avtal", "delvis")):
        errors.append(f"{rid}: env_var satt men auth anger inget nyckelkrav")
    if r.get("url") and not str(r["url"]).startswith("http"):
        errors.append(f"{rid}: url börjar inte med http")

for i in ideas:
    for s in i.get("sources", []):
        if s not in ids:
            errors.append(f"idé {i.get('id')}: källan {s} finns inte i katalogen")

if errors:
    print("\n".join(errors))
    print(f"\n{len(errors)} fel.")
    sys.exit(1)
print(f"OK: {len(cat)} källor, {len(ideas)} idéer.")
