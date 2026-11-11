#!/usr/bin/env bash
# Restaura dumps/<base>.dump con neo4j-admin database load.
# Sustituye la base local. Neo4j Community exige la base detenida.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${NEO4J_PASSWORD:?Falta NEO4J_PASSWORD. Copia .env.example a .env}"
DB="${NEO4J_DATABASE:-neo4j}"
DUMP="dumps/${DB}.dump"

if [[ ! -f "$DUMP" ]]; then
  echo "No está ${DUMP}. Primero corre ./scripts/neo4j-dump.sh en la máquina de origen." >&2
  exit 1
fi

echo "Deteniendo Neo4j para cargar ${DUMP}..."
docker compose stop neo4j

docker compose run --rm -T --no-deps neo4j \
  neo4j-admin database load "$DB" \
  --from-path=/dumps \
  --overwrite-destination=true \
  --verbose

echo "Base ${DB} restaurada desde ${DUMP}"
docker compose start neo4j
echo "Neo4j arrancando otra vez."
