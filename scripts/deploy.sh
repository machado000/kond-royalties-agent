#!/usr/bin/env bash
set -euo pipefail

# Deploy rapido de kond-royalties-mcp para kern-data: sincroniza o codigo,
# reconstroi a imagem Docker, reinicia o container e roda smoke tests
# contra a URL de producao. Nao toca no .env remoto (segredos ficam so no
# host) nem no Caddyfile.
#
# Uso:
#   scripts/deploy.sh
#   scripts/deploy.sh "Como foi a receita por artista nos ultimos 90 dias?"

cd "$(dirname "$0")/.."

REMOTE_HOST="kern-data"
REMOTE_DIR="kond-royalties-mcp"
BASE_URL="https://kerndata1.ddns.net/kond-royalties-mcp/mcp"

echo "==> Sincronizando codigo para ${REMOTE_HOST}..."
rsync -az --delete \
  --exclude='.venv' --exclude='__pycache__' --exclude='.pytest_cache' --exclude='.ruff_cache' \
  --exclude='.git' --exclude='.DS_Store' --exclude='secrets' --exclude='.env' --exclude='tests' \
  --exclude='.context' --exclude='build' --exclude='*.egg-info' \
  Dockerfile docker-compose.yml pyproject.toml mcp_server config semantic_catalog prompts \
  "${REMOTE_HOST}:${REMOTE_DIR}/"

echo "==> Rebuild + restart do container..."
ssh "$REMOTE_HOST" "cd ${REMOTE_DIR} && docker compose build && docker compose up -d && sleep 3 && docker compose logs --tail=20"

echo "==> Smoke test: metadados RFC 9728..."
curl -sf "https://kerndata1.ddns.net/.well-known/oauth-protected-resource/kond-royalties-mcp/mcp" | python3 -m json.tool

echo "==> Smoke test: token estatico (initialize)..."
TOKEN=$(ssh "$REMOTE_HOST" "grep '^MCP_API_KEYS=' ${REMOTE_DIR}/.env | cut -d= -f2 | cut -d, -f1")
RESP=$(curl -s -i -X POST "$BASE_URL" \
  -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"deploy-smoke-test","version":"1.0"}}}')
STATUS=$(echo "$RESP" | head -1 | grep -oE '[0-9]{3}')
if [ "$STATUS" != "200" ]; then
  echo "FALHOU: initialize retornou HTTP ${STATUS}"
  echo "$RESP"
  exit 1
fi
echo "OK (HTTP 200)"

if [ "${1:-}" != "" ]; then
  SESSION=$(echo "$RESP" | grep -i "mcp-session-id" | tr -d '\r' | awk '{print $2}')
  echo "==> Testando ask_royalties com: \"$1\""
  curl -s -o /dev/null -X POST "$BASE_URL" \
    -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" -H "mcp-session-id: ${SESSION}" \
    -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
  curl -s -X POST "$BASE_URL" \
    -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" -H "mcp-session-id: ${SESSION}" \
    -d "{\"jsonrpc\":\"2.0\",\"id\":2,\"method\":\"tools/call\",\"params\":{\"name\":\"ask_royalties\",\"arguments\":{\"question\":\"$1\",\"limit\":10}}}" \
    | python3 -c "import json,sys; d=json.loads([l for l in sys.stdin if l.startswith('data:')][0][5:]); print(json.loads(d['result']['content'][0]['text'])['answer']['answer_markdown'])"
fi

echo "==> Deploy concluido."
