#!/usr/bin/env python3
"""Bygger härledda filer ur data/ (committas inte, se .gitignore):

    build/katalog.csv, build/verktygsideer.csv   - för Excel/Sheets
    build/oppna_data.db                          - SQLite för Datasette m.m.
    site/catalog.json, site/ideas.json, site/meta.json - för webbsidan

Användning: python3 tools/export.py
"""
import csv
import json
import pathlib
import shutil
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, BUILD, SITE = ROOT / "data", ROOT / "build", ROOT / "site"
BUILD.mkdir(exist_ok=True)

cat = json.loads((DATA / "catalog.json").read_text(encoding="utf-8"))
ideas = json.loads((DATA / "ideas.json").read_text(encoding="utf-8"))
names = {r["id"]: r["name"] for r in cat}

cols = ["id", "category", "subcategory", "name", "provider", "provider_type", "status", "auth",
        "access", "license", "update_frequency", "url", "endpoint", "example", "data",
        "use_cases", "tips", "note", "last_checked"]

with open(BUILD / "katalog.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(cat)

with open(BUILD / "verktygsideer.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["id", "titel", "kategori", "värde", "svårighet", "målgrupp", "pitch",
                "problem idag", "hur datan kopplas", "källor", "finns gratis"])
    for i in ideas:
        w.writerow([i.get("id"), i["title"], i["category"], i["value"], i["difficulty"],
                    i["audience"], i["pitch"], i["problem"], i["how"],
                    "; ".join(names.get(s, s) for s in i["sources"]), i.get("exists_free", "")])

db_path = BUILD / "oppna_data.db"
db_path.unlink(missing_ok=True)
db = sqlite3.connect(db_path)
db.execute(f"CREATE TABLE kallor ({', '.join(c + ' TEXT' for c in cols)}, formats TEXT, PRIMARY KEY(id))")
db.executemany(
    f"INSERT INTO kallor VALUES ({', '.join('?' * (len(cols) + 1))})",
    [[r.get(c) for c in cols] + [", ".join(r.get("formats") or [])] for r in cat])
db.execute("CREATE TABLE ideer (id TEXT PRIMARY KEY, title TEXT, category TEXT, value TEXT, difficulty TEXT,"
           " audience TEXT, pitch TEXT, problem TEXT, how TEXT, exists_free TEXT)")
db.executemany("INSERT INTO ideer VALUES (?,?,?,?,?,?,?,?,?,?)",
               [[i.get("id"), i["title"], i["category"], i["value"], i["difficulty"], i["audience"],
                 i["pitch"], i["problem"], i["how"], i.get("exists_free")] for i in ideas])
db.execute("CREATE TABLE ide_kallor (ide_id TEXT, kalla_id TEXT)")
db.executemany("INSERT INTO ide_kallor VALUES (?,?)",
               [(i.get("id"), s) for i in ideas for s in i["sources"]])
db.execute("CREATE VIRTUAL TABLE kallor_fts USING fts5(id UNINDEXED, name, provider, data, tips, use_cases)")
db.execute("INSERT INTO kallor_fts SELECT id, name, provider, data, tips, use_cases FROM kallor")
db.commit()
db.close()

for f in ("catalog.json", "ideas.json", "meta.json"):
    shutil.copy(DATA / f, SITE / f)

print(f"Byggt: {len(cat)} källor, {len(ideas)} idéer -> build/ och site/")
