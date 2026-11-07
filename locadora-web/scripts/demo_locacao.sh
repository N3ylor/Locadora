#!/usr/bin/env bash
# Demonstra locação e devolução: o ADMIN cadastra filme, jogo e cliente; o CLIENTE aluga e devolve.
# Uso:  ./scripts/demo_locacao.sh [URL_BASE]     (lê ADMIN_USERNAME/ADMIN_PASSWORD do .env ou do ambiente)
set -euo pipefail

BASE="${1:-http://localhost:${HOST_PORT:-8080}}"
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then set -a; . ./.env; set +a; fi
: "${ADMIN_PASSWORD:?Defina ADMIN_PASSWORD (ou crie o arquivo .env)}"
ADM="$(mktemp)"; CLI="$(mktemp)"; OUT="$(mktemp)"; trap 'rm -f "$ADM" "$CLI" "$OUT"' EXIT
J='Content-Type: application/json'
USERC="demo$RANDOM"
idde() { sed -n 's/.*"id": *\([0-9]*\).*/\1/p'; }

curl -s -o /dev/null -c "$ADM" --data-urlencode "username=${ADMIN_USERNAME:-admin}" --data-urlencode "password=$ADMIN_PASSWORD" "$BASE/portal"
FID=$(curl -s -b "$ADM" -H "$J" -d '{"titulo":"Filme Demo","genero":"Ação","valor_diaria":6.00}' "$BASE/api/filmes" | idde)
JID=$(curl -s -b "$ADM" -H "$J" -d '{"titulo":"Jogo Demo","plataforma":"PC","valor_diaria":10.00}' "$BASE/api/jogos" | idde)
curl -s -o /dev/null -b "$ADM" -H "$J" -d "{\"username\":\"$USERC\",\"nome\":\"Cliente Demo\",\"senha\":\"senha-demo-123\"}" "$BASE/api/clientes"
echo "== Preparação: admin cadastrou filme $FID, jogo $JID e o cliente $USERC"

curl -s -o /dev/null -c "$CLI" --data-urlencode "username=$USERC" --data-urlencode "password=senha-demo-123" "$BASE/portal"

echo "== 1. Página do cliente tem o botão Alugar? $(curl -s -b "$CLI" "$BASE/cliente" | grep -c 'action="/cliente/alugar"') formulário(s)"

echo "== 2. CLIENTE aluga o filme por 3 dias (como o botão da página faz)"
curl -s -o /dev/null -b "$CLI" -w "HTTP %{http_code} -> %{redirect_url}\n" \
     -d "tipo=filme&item_id=$FID&dias=3" "$BASE/cliente/alugar"

echo "== 3. CLIENTE aluga o jogo por 5 dias pela API (10% de desconto: 50,00 -> 45,00)"
RESP=$(curl -s -b "$CLI" -H "$J" -d "{\"tipo\":\"jogo\",\"item_id\":$JID,\"dias\":5}" "$BASE/api/locacoes"); echo "$RESP"
LID=$(printf '%s' "$RESP" | idde)

echo "== 4. Outro pedido do mesmo filme deve falhar (409: já alugado)"
curl -s -b "$CLI" -w "  HTTP %{http_code}\n" -H "$J" -d "{\"tipo\":\"filme\",\"item_id\":$FID,\"dias\":1}" "$BASE/api/locacoes"

echo "== 5. Minhas locações"
curl -s -b "$CLI" "$BASE/api/locacoes"; echo

echo "== 6. ADMIN vê todas as locações no painel (linhas com $USERC: $(curl -s -b "$ADM" "$BASE/banco" | grep -c "$USERC"))"

echo "== 7. CLIENTE devolve o jogo (API) e o filme (formulário)"
curl -s -b "$CLI" -X POST "$BASE/api/locacoes/$LID/devolucao"; echo
curl -s -o /dev/null -b "$CLI" -w "HTTP %{http_code} -> %{redirect_url}\n" -X POST "$BASE/cliente/devolver/$((LID-1))"

echo "== 8. Devolver de novo (409)"
curl -s -b "$CLI" -w "  HTTP %{http_code}\n" -X POST "$BASE/api/locacoes/$LID/devolucao"

echo "== 9. Limpeza: admin exclui cliente, filme e jogo"
curl -s -o /dev/null -b "$ADM" -X DELETE "$BASE/api/clientes/$USERC"
curl -s -o /dev/null -b "$ADM" -X DELETE "$BASE/api/filmes/$FID"
curl -s -o /dev/null -b "$ADM" -X DELETE "$BASE/api/jogos/$JID"
echo "ok"
