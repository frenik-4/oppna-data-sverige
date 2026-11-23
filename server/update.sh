#!/usr/bin/env bash
# Cron på hemservern, t.ex. 15 4 * * * /sökväg/till/oppna-data-sverige/server/update.sh
# Hämtar senaste katalogen och bygger om Datasette bara om något ändrats.
set -euo pipefail
cd "$(dirname "$0")/.."
before=$(git rev-parse HEAD)
git pull --ff-only -q
if [ "$before" != "$(git rev-parse HEAD)" ]; then
  docker compose -f server/docker-compose.yml up -d --build datasette
fi
