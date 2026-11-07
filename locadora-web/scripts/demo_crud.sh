#!/usr/bin/env bash
# Demonstração completa do CRUD via cURL (login -> CREATE -> READ -> UPDATE -> DELETE).
# Uso:  ADMIN_PASSWORD='sua-senha' ./scripts/demo_crud.sh [URL_BASE]
# Lê ADMIN_USERNAME/ADMIN_PASSWORD do ambiente ou do arquivo .env.
set -euo pipefail

BASE="${1:-http://localhost:${HOST_PORT:-8080}}"
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
USER_NAME="${ADMIN_USERNAME:-admin}"
: "${ADMIN_PASSWORD:?Defina ADMIN_PASSWORD (ou crie o arquivo .env)}"
JAR="$(mktemp)"; trap 'rm -f "$JAR"' EXIT
J='Content-Type: application/json'

echo "== 1. Sem login a API deve negar (401)"
curl -s -o /dev/null -w "HTTP %{http_code}\n" "$BASE/api/filmes"

echo "== 2. Login (guarda o cookie de sessão)"
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" -c "$JAR" \
     --data-urlencode "username=$USER_NAME" --data-urlencode "password=$ADMIN_PASSWORD" "$BASE/portal"

echo "== 3. CREATE"
RESP=$(curl -s -b "$JAR" -H "$J" -d '{"titulo":"Matrix","genero":"Ficção científica","valor_diaria":5.00}' "$BASE/api/filmes")
echo "$RESP"
ID=$(printf '%s' "$RESP" | sed -n 's/.*"id": *\([0-9]*\).*/\1/p')

echo "== 4. READ (API) — a mesma lista aparece em $BASE/banco"
curl -s -b "$JAR" "$BASE/api/filmes"; echo
echo "   READ (HTML): linhas com 'Matrix' em /banco = $(curl -s -b "$JAR" "$BASE/banco" | grep -c 'Matrix')"

echo "== 5. UPDATE"
curl -s -b "$JAR" -X PUT -H "$J" -d '{"titulo":"Matrix Reloaded","genero":"Ficção científica","valor_diaria":7.00}' "$BASE/api/filmes/$ID"; echo

echo "== 6. Validação: valor negativo deve ser recusado (422)"
curl -s -b "$JAR" -w "  HTTP %{http_code}\n" -H "$J" -d '{"titulo":"X","genero":"Y","valor_diaria":-1}' "$BASE/api/filmes"

echo "== 7. DELETE"
curl -s -b "$JAR" -X DELETE "$BASE/api/filmes/$ID"; echo
echo "== 8. DELETE de novo: registro inexistente (404)"
curl -s -b "$JAR" -w "  HTTP %{http_code}\n" -X DELETE "$BASE/api/filmes/$ID"

echo "== 9. Logout"
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" -b "$JAR" -X POST "$BASE/logout"
