# Comandos Validados

Repositorio: `~/Projetos/KOND-analytics-agent`

Todos os comandos abaixo foram validados em 2026-07-01 contra o Postgres
real de producao (credenciais em `.env`, nao versionadas).

## Ambiente

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest -q
```

Resultado validado: `13 passed`.

## Configuracao

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server config
```

Observacao: `openai_api_key`, `database_url` e `pg_password` aparecem como
`***redacted***`.

## Catalogo

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server catalog
```

## Diagnostico Postgres

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server diagnose-postgres
```

Resultado validado: `status: ok`, schemas acessiveis = `public`,
`universal`, `warner_chappell` (nenhum `missing_enabled_schemas`).

## Introspeccao de schema

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server describe-schema --schema public
```

Resultado validado: 64 tabelas/views no schema `public`, incluindo
`vw_ft_dados_analiticos_union` (14 colunas), `dim_artistas` (21 colunas),
`dim_calendario`, `dim_canal`, `dim_pais` e as fact/staging tables por
distribuidora.

## Planejamento semantico

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server plan-query --question "Como foram quantidade e receita por artista nos ultimos 90 dias?"
```

## Execucao real da query

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server run-query --question "Como foram quantidade e receita por artista nos ultimos 90 dias?" --limit 20
```

Resultado validado: 7 linhas, artistas reais (DJ ARANA, DJ JAPA NK, MC
KEKEL, MC KEVINHO, etc.) com `quantity`/`revenue` agregados corretamente.

## Resposta executiva com OpenAI

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server ask --question "Como foram quantidade e receita por artista nos ultimos 90 dias?" --limit 20
```

Resultado validado: `generation_mode: "openai"`, resposta em PT-BR citando
os artistas corretos e valores batendo com `run-query`.

## Servidor MCP (stdio)

Validado manualmente via `initialize` + `tools/list` — retorna os 7 tools
esperados (`get_royalty_catalog`, `get_runtime_config`,
`diagnose_postgres_access`, `describe_schema`, `plan_royalty_query`,
`run_royalty_query`, `ask_royalties`).
