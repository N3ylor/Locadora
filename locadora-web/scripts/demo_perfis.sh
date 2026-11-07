#!/usr/bin/env bash
# Demonstra perfis: o ADMIN cadastra jogo e cliente; o CLIENTE entra, consulta e é barrado ao tentar alterar.
# Uso:  ./scripts/demo_perfis.sh [URL_BASE]     (lê ADMIN_USERNAME/ADMIN_PASSWORD do .env ou do ambiente)
set -euo pipefail

BASE="${1:-http://localhost:${HOST_PORT:-8080}}"
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
: "${ADMIN_PASSWORD:?Defina ADMIN_PASSWORD (ou crie o arquivo .env)}"
ADM="$(mktemp)"; CLI="$(mktemp)"; trap 'rm -f "$ADM" "$CLI"' EXIT
J='Content-Type: application/json'
SUF="$RANDOM"; USERC="cliente$SUF"

echo "== 1. ADMIN faz login"
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" -c "$ADM" \
     --data-urlencode "username=${ADMIN_USERNAME:-admin}" --data-urlencode "password=$ADMIN_PASSWORD" "$BASE/portal"

echo "== 2. ADMIN cadastra um jogo"
RJ=$(curl -s -b "$ADM" -H "$J" -d '{"titulo":"Zelda","plataforma":"Nintendo Switch","valor_diaria":8.50}' "$BASE/api/jogos"); echo "$RJ"
IDJ=$(printf '%s' "$RJ" | sed -n 's/.*"id": *\([0-9]*\).*/\1/p')

echo "== 3. ADMIN cadastra um cliente ($USERC)"
curl -s -b "$ADM" -H "$J" -d "{\"username\":\"$USERC\",\"nome\":\"Maria Silva\",\"senha\":\"senha-da-maria\"}" "$BASE/api/clientes"; echo

echo "== 4. CLIENTE faz login (deve ir para /cliente)"
curl -s -o /dev/null -w "HTTP %{http_code} -> %{redirect_url}\n" -c "$CLI" \
     --data-urlencode "username=$USERC" --data-urlencode "password=senha-da-maria" "$BASE/portal"

echo "== 5. CLIENTE vê o catálogo (página HTML e API de leitura)"
echo "   /cliente contém 'Zelda': $(curl -s -b "$CLI" "$BASE/cliente" | grep -c 'Zelda') linha(s)"
curl -s -b "$CLI" "$BASE/api/jogos"; echo

echo "== 6. CLIENTE tenta cadastrar jogo (deve ser 403) e abrir /banco (deve redirecionar)"
curl -s -b "$CLI" -w "  HTTP %{http_code}\n" -H "$J" -d '{"titulo":"X","plataforma":"Y","valor_diaria":1}' "$BASE/api/jogos"
curl -s -o /dev/null -b "$CLI" -w "/banco -> HTTP %{http_code} -> %{redirect_url}\n" "$BASE/banco"
curl -s -b "$CLI" -w "  /api/clientes -> HTTP %{http_code}\n" "$BASE/api/clientes"

echo "== 7. ADMIN troca a senha do cliente; a sessão antiga do cliente cai"
curl -s -b "$ADM" -X PUT -H "$J" -d '{"senha":"outra-senha-123"}' "$BASE/api/clientes/$USERC"; echo
curl -s -o /dev/null -b "$CLI" -w "/cliente com cookie antigo -> HTTP %{http_code} -> %{redirect_url}\n" "$BASE/cliente"

echo "== 8. Limpeza: ADMIN exclui cliente e jogo"
curl -s -b "$ADM" -X DELETE "$BASE/api/clientes/$USERC"; echo
curl -s -b "$ADM" -X DELETE "$BASE/api/jogos/$IDJ"; echo
