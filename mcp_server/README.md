# MCP Server

Servidor MCP real por `stdio`.

Ferramentas expostas:

- `get_marketing_catalog`
- `get_runtime_config`
- `diagnose_bigquery_access`
- `plan_marketing_query`
- `run_marketing_query`
- `ask_marketing`

Comando para iniciar:

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server serve-mcp
```

Nesta fase:

- `generate_marketing_report` continua pendente e nao esta exposta ainda
- o transporte suportado e `stdio`
- o servidor declara apenas a capability `tools`
