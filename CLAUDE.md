# Öppna data Sverige — instruktioner för Claude

## Språk
Svara och skriv på svenska i det här projektet (README, poster, commit-meddelanden).

## Vad repot är
Central, kanonisk katalog över öppna svenska datakällor/API:er. Andra projekt
(CCounter, MyHome, ATG) läser härifrån via hemserverns Datasette/MCP eller en
lokal klon. **Kopiera aldrig `data/catalog.json` in i andra repon.**

## GitHub — via PR
- Pusha aldrig direkt till `main`. Skapa branch, committa, öppna PR.
- Merga aldrig själv utan användarens uttryckliga OK.
- Commit-meddelanden avslutas med en `Co-Authored-By:`-rad för Claude.

## Regler för katalogen
- `id` är stabila och återanvänds aldrig. Idéer i `data/ideas.json` och andra
  projekt refererar till dem. En nedlagd källa får `status: "stängd"` och en
  förklaring i `note`; den tas inte bort.
- Nya poster: nästa lediga nummer med områdets prefix (A statistik/ekonomi,
  B arbete/utbildning/hälsa, C geo/väder/natur, D energi/transport,
  E juridik/kris/kataloger, F kultur/forskning, G kommuner/konsument/sport,
  H internationellt/dolda ingångar).
- `category` måste finnas i `data/meta.json`.
- Sätt bara `status: "verifierad"` om ett anrop faktiskt svarat. Kör
  `python3 tools/verify.py --ids <id>`.
- Inga källor med persondata om privatpersoner, inget som kräver BankID eller betalning.
- Odokumenterade JSON-anrop bakom webbplatser markeras tydligt som inofficiella i `tips`.
- Källor som kräver nyckel får `env_var` (VERSALER_MED_UNDERSTRECK). Återanvänd
  befintligt namn för samma tjänst. Nycklar committas aldrig.
- Kör `python3 tools/validate.py` före commit.

## Kända fallgropar
- Många myndighetssajter (esv.se, jobtechdev.se, diva-portal.org,
  Energimyndighetens PxWeb m.fl.) blockerar molnservrar/GitHub Actions. En
  status som byter till `blockerad` i veckotestet ska kontrolleras från
  hemservern innan PR:en mergas.
- SCB PxWeb v1 avvecklas vid årsskiftet 2026/27. Nya exempel ska använda v2.
- `nvdbapiles` är norska Statens vegvesen, inte Trafikverket.
