# MCP Server

Servidor MCP real por `stdio`.

Ferramentas expostas:

- `get_royalty_catalog`
- `get_runtime_config`
- `diagnose_postgres_access`
- `describe_schema`
- `plan_royalty_query`
- `run_royalty_query`
- `ask_royalties`

Comando para iniciar:

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server serve-mcp
```

Nesta fase:

- `generate_royalty_report` continua pendente e nao esta exposta ainda
- o transporte suportado e `stdio`
- o servidor declara apenas a capability `tools`
- `describe_schema` e a ferramenta usada para descobrir o schema real do
  Postgres (schemas/tabelas/colunas via `information_schema`) — use-a antes
  de confiar em `config/column_dictionary.yml`, que hoje e provisorio
