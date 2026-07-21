# Comandos Validados

Repositorio: `~/Projetos/KOND-analytics-agent`

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Resultado validado: `14 passed`.

## CLI local (stdio) — dev

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server config
PYTHONPATH=. .venv/bin/python -m mcp_server.server catalog
PYTHONPATH=. .venv/bin/python -m mcp_server.server diagnose-postgres
PYTHONPATH=. .venv/bin/python -m mcp_server.server describe-schema --schema public
PYTHONPATH=. .venv/bin/python -m mcp_server.server plan-query --question "Como foram quantidade e receita por artista nos ultimos 90 dias?"
PYTHONPATH=. .venv/bin/python -m mcp_server.server run-query --question "Como foram quantidade e receita por artista nos ultimos 90 dias?" --limit 20
PYTHONPATH=. .venv/bin/python -m mcp_server.server ask --question "Como foram quantidade e receita por artista nos ultimos 90 dias?" --limit 20
```

Resultados validados: `diagnose-postgres` -> `status: ok`, schemas
acessiveis = `public`, `universal`, `warner_chappell`. `describe-schema`
-> 64 tabelas/views em `public`. `run-query`/`ask` -> linhas reais
(DJ ARANA, DJ JAPA NK, MC KEKEL, MC KEVINHO, etc.), `ask` com
`generation_mode: "openai"`.

## Deploy em producao (Docker + Caddy) — `kern-data`

```bash
ssh kern-data
cd kond-royalties-mcp
docker compose build
docker compose up -d
docker compose logs --tail=30
```

Sempre validar o Caddyfile antes de recarregar (atende varios servicos):

```bash
docker exec kern-prefect-caddy-1 caddy validate --config /etc/caddy/Caddyfile
docker exec kern-prefect-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

## Verificacao HTTP remota

```bash
# metadados RFC 9728
curl https://kerndata1.ddns.net/.well-known/oauth-protected-resource/kond-royalties-mcp/mcp

# sem token -> 401
curl -X POST https://kerndata1.ddns.net/kond-royalties-mcp/mcp -H "Content-Type: application/json" -d '{}'

# com token estatico -> 200
curl -X POST https://kerndata1.ddns.net/kond-royalties-mcp/mcp \
  -H "Authorization: Bearer <MCP_API_KEYS>" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

Resultado validado: `200` com sessao MCP estabelecida; porta direta
(`:8081`) e rota HTTPS via Caddy ambas testadas.

## Conector remoto claude.ai (OAuth via Auth0)

Validado ponta a ponta em producao (2026-07-20): Settings → Connectors →
Add custom connector → URL `https://kerndata1.ddns.net/kond-royalties-mcp/mcp`
→ Advanced settings com Client ID/Secret da Application Auth0 → Connect →
login Auth0 → consentimento → conector conectado. Confirmado nos logs do
servidor: `ListToolsRequest`, `ListResourcesRequest`, `ListPromptsRequest`
todos com `200 OK` apos sessao autenticada criada.

## Servidor MCP (stdio)

Validado manualmente via `initialize` + `tools/list` — retorna os 7 tools
esperados (`get_royalty_catalog`, `get_runtime_config`,
`diagnose_postgres_access`, `describe_schema`, `plan_royalty_query`,
`run_royalty_query`, `ask_royalties`).
