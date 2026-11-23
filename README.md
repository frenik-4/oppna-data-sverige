# Öppna data Sverige

Central katalog över öppna och gratis databaser och API:er med svensk data. Den täcker myndigheter, kommuner, forskning, föreningar, företag och internationella källor. Varje post beskriver vilken data du får ut, hur du når den (endpoint och exempelanrop), om nyckel krävs och om tjänsten svarade senast den testades.

Det här repot är den enda källan. Andra projekt (CCounter, MyHome, ATG m.fl.) läser härifrån och har inga egna kopior.

| | |
|---|---|
| Källor | 541, i 18 kategorier |
| Verktygsidéer | 61, som kombinerar flera källor |
| Senast fulltestad | 2026-11-22 |

## Innehåll

```
data/catalog.json   Kanonisk källa: en post per datakälla/API
data/ideas.json     Verktygsidéer; `sources` pekar på id i catalog.json
data/meta.json      Kategorier, kopplingsnycklar och metodtext
tools/validate.py   Kontrollerar formatet (körs i CI på varje PR)
tools/verify.py     Testar alla endpoints igen och uppdaterar status
tools/export.py     Bygger CSV, SQLite och filerna webbsidan behöver (till build/ och site/)
site/index.html     Sökbar webbsida över katalogen
mcp/server.py       MCP-server så att Claude kan söka i katalogen
server/             Docker Compose för hemservern (Datasette + MCP)
```

## Använda katalogen i andra projekt

### 1. Via hemservern (rekommenderas)

Klona repot på servern och starta båda tjänsterna:

```bash
git clone https://github.com/frenik-4/oppna-data-sverige.git
cd oppna-data-sverige
docker compose -f server/docker-compose.yml up -d --build
```

- **Datasette** på `http://<server>:8001`: webbgränssnitt med facetter, fritextsökning och ett JSON-API. Exempel:
  - `/oppna_data/kallor.json?category=Energi+%26+el&_shape=array`
  - `/oppna_data/kallor_fts.json?_search=radon&_shape=array`
  - `/oppna_data?sql=select+name,endpoint+from+kallor+where+auth+like+'ingen%25'`
- **MCP-servern** på `http://<server>:8002/mcp`.

Är port 8001 eller 8002 redan upptagen: kopiera `server/.env.example` till `server/.env` och välj andra portar (`ODS_DATASETTE_PORT`, `ODS_MCP_PORT`). Med `ODS_BIND` kan tjänsterna bindas till enbart Tailscale-IP:n.

Håll servern uppdaterad med en cron-rad. Skriptet gör `git pull` och bygger om Datasette bara om något har ändrats:

```
15 4 * * * /sökväg/till/oppna-data-sverige/server/update.sh
```

### 2. Som MCP-server i Claude Code

Lägg till servern en gång. Därefter kan Claude i alla projekt anropa `sok_kallor`, `hamta_kalla`, `lista_kategorier`, `sok_ideer` och `kopplingsnycklar`.

Mot hemservern (över Tailscale):

```bash
claude mcp add --scope user --transport http oppna-data http://pre3430:8002/mcp
```

Eller lokalt via stdio, utan server:

```bash
pip install -r mcp/requirements.txt
claude mcp add --scope user oppna-data -- python3 /sökväg/till/oppna-data-sverige/mcp/server.py
```

### 3. Direkt i kod

Läs JSON-filen från en lokal klon (`data/catalog.json`) eller från GitHub:

```python
import json, urllib.request
URL = "https://raw.githubusercontent.com/frenik-4/oppna-data-sverige/main/data/catalog.json"
katalog = json.load(urllib.request.urlopen(URL))
energi = [k for k in katalog if k["category"] == "Energi & el" and k["status"] == "verifierad"]
```

Råfilerna på GitHub kräver inloggning om repot är privat. Använd då en lokal klon eller hemservern.

Kopiera inte `catalog.json` in i andra repon, för då glider kopiorna isär. Behöver ett projekt en fast version, lägg till repot som git submodule och lås en commit.

## Poster

| Fält | Betydelse |
|---|---|
| `id` | Stabilt id, t.ex. `A013`. Ändras aldrig; idéer och andra projekt refererar till det. |
| `category` | En av kategorierna i `data/meta.json`. |
| `status` | `verifierad`, `nyckel` (svarar men kräver nyckel), `blockerad` (blockerar molnservrar men bekräftad), `overifierad`, `stängd` (ej öppen). |
| `auth` | `ingen`, `gratis API-nyckel`, `registrering/avtal` eller `delvis`. |
| `url` / `endpoint` / `example` | Dokumentation, API-bas och ett konkret exempelanrop. |
| `data` / `use_cases` / `tips` | Vad du får ut, vad det kan användas till, och praktiska ingångar och fallgropar. |
| `last_checked` | Datum för senaste automatiska test. |

## Uppdatera katalogen

1. Skapa en branch och ändra i `data/catalog.json`. Nya poster får nästa lediga id med samma bokstavsprefix som området.
2. Kör `python3 tools/validate.py`, och `python3 tools/verify.py --ids <id>` för nya eller ändrade poster.
3. Öppna en PR. CI validerar formatet.

GitHub Actions testar alla endpoints varje måndag och öppnar en PR om någon status har ändrats. Många svenska myndighetssajter blockerar molnservrar, så poster som byter till `blockerad` i den PR:en bör kontrolleras från en vanlig anslutning, till exempel hemservern (`python3 tools/verify.py --ids ...`), innan PR:en mergas.

## Licens och ansvar

Katalogen beskriver andras data. Licensen för varje källa står i posten och gäller den källans data. Kontrollera alltid användarvillkoren hos källan, särskilt för poster märkta som inofficiella eller odokumenterade.
