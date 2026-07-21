# MCP Server

Dois transportes, mesmas tools:

- `mcp_stdio.py` (comando `serve-mcp`) — stdio, para uso local/dev
- `mcp_http.py` (comando `serve-http`) — Streamable HTTP, para o deploy em
  producao (ver [README.md](../README.md) na raiz para o passo a passo
  completo de deploy, Caddy e OAuth)

Ferramentas expostas:

- `get_royalty_catalog`
- `get_runtime_config`
- `diagnose_postgres_access`
- `describe_schema`
- `plan_royalty_query`
- `run_royalty_query`
- `ask_royalties`

Comando para iniciar via stdio:

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server serve-mcp
```

Nesta fase:

- `generate_royalty_report` continua pendente e nao esta exposta ainda
- o servidor declara apenas a capability `tools`
- `describe_schema` e a ferramenta usada para descobrir o schema real do
  Postgres (schemas/tabelas/colunas via `information_schema`) — use-a antes
  de confiar em `config/column_dictionary.yml`, que hoje e provisorio
- o transporte HTTP (`mcp_http.py`) exige autenticacao (`mcp_server/oauth.py`):
  token Bearer estatico (`MCP_API_KEYS`) e/ou delegacao OAuth 2.1 a um IdP
  externo (`OAUTH_ISSUER_URL`/`OAUTH_RESOURCE_URL`) — o processo recusa
  iniciar sem pelo menos um dos dois configurado
