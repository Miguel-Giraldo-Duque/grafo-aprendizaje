#!/usr/bin/env bash
# Vuelca la base con neo4j-admin database dump.
# Neo4j Community exige la base detenida. El script la para y la vuelve a arrancar.
# El archivo queda en dumps/<base>.dump, que está fuera de git.

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

mkdir -p dumps
# neo4j-admin corre como uid 7474 y tiene que poder crear el .dump.
chmod a+rwx dumps

echo "Deteniendo Neo4j para volcar la base ${DB}..."
docker compose stop neo4j

docker compose run --rm -T --no-deps neo4j \
  neo4j-admin database dump "$DB" \
  --to-path=/dumps \
  --overwrite-destination=true \
  --verbose

echo "Volcado en dumps/${DB}.dump"
docker compose start neo4j
echo "Neo4j arrancando otra vez."
