# Comandos Validados

Todos os comandos abaixo foram validados no repositorio:

- repositorio: `/Users/joao/Documents/Codex/2026-06-25/mistral-analytics-agent`

## Ambiente

Criacao de ambiente e instalacao:

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Testes

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests -q
```

Resultado validado:

- `9 passed`

## Configuracao

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server config
```

Observacao:

- `openai_api_key` aparece como `***redacted***`

## Catalogo

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server catalog
```

## Diagnostico BigQuery

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server diagnose-bigquery
```

Observacao:

- esse comando depende de rede e autenticacao validas

## Planejamento semantico

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server plan-query --question "Como foi receita, investimento e ROAS por canal nos ultimos 7 dias?"
```

## Execucao real da query

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server run-query --question "Como foi receita, investimento e ROAS por canal nos ultimos 7 dias?" --limit 20
```

## Resposta executiva com OpenAI

```bash
PYTHONPATH=. .venv/bin/python -m mcp_server.server ask --question "Como foi receita, investimento e ROAS por canal nos ultimos 7 dias?" --limit 20
```

