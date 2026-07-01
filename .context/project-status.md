# Estado Do Projeto

## Repositorio ativo

- caminho local: `/Users/joao/Documents/Codex/2026-06-25/mistral-analytics-agent`
- GitHub: `https://github.com/machado000/mistral-analytics-agent`
- branch principal: `main`

## Ultimos commits

- `234884e` Add OpenAI-powered answer synthesis
- `f1ff729` Add controlled BigQuery query flow
- `9583971` Add MCP config and BigQuery scaffolding
- `79889a0` Scaffold V1 MCP analytics agent
- `a8f9ce4` Initial workspace scaffold

## O que foi abandonado

- arquitetura antiga com frontend proprio
- arquitetura antiga com DuckDB como cache da V1
- sync diario local como requisito da primeira entrega

## Escopo atual da V1

- agente customizado
- servidor MCP ou base equivalente de tools
- BigQuery direto
- OpenAI para sintese da resposta
- catalogo semantico em PT-BR
- sugestao de visual
- relatorio PDF ainda pendente

## O que ja funciona

### Estrutura

- `pyproject.toml` com dependencias Python
- `.venv` local criado no repositorio ativo
- prompts PT-BR em `prompts/`
- catalogo semantico em `semantic_catalog/catalog.yml`
- configuracao de fontes em `config/bigquery_sources.yml`

### BigQuery

- carrega `.env` local automaticamente
- usa `BIGQUERY_PROJECT_ID=mistral-analytics`
- datasets mapeados:
  - `analytics_253977277`
  - `ga4_bronze`
  - `ga4_silver`
  - `google_ads`
  - `facebook_ads_bronze`
  - `facebook_ads_silver`

### CLI atual

Entrypoint:

- `mcp_server/server.py`

Comandos implementados:

- `catalog`
- `config`
- `diagnose-bigquery`
- `plan-query`
- `run-query`
- `ask`

### Fluxo semantico

- pergunta natural -> planejamento semantico
- planejamento -> SQL controlado
- SQL -> BigQuery
- resultado -> sintese executiva em PT-BR via OpenAI
- fallback deterministico se OpenAI falhar

### Validacoes feitas

- `pytest -m "not slow"` passa com `12 passed` (testes unitarios)
- `pytest -m slow` passa com `2 passed` (validacao de acuracia contra BigQuery)
- `run-query` foi executado com sucesso no BigQuery
- `ask` foi executado com sucesso com BigQuery + OpenAI

### Teste de acuracia entre datasets

Arquivo: `tests/test_dataset_accuracy.py`

Valida que ga4_bronze, ga4_silver e analytics_253977277 retornam receita
identica por canal para um periodo fixo (2026-06-19 a 2026-06-23).
Requer acesso ao BigQuery. Executar com `pytest -m slow`.

Resultado validado em 2026-06-26: R$ 301.784,38 em 9 canais, identico nos 3 datasets.

### Status (2026-06-26, sessao de auditoria de schemas)

Novas tabelas descobertas no BigQuery (criadas externamente, fora deste repositorio):

- `ga4_bronze.ga4_dim_session_traffic` — definida como tabela canonica de dimensao
  de sessao, substituindo a antiga `dim_session_traffic`. Todas as referencias em
  `mcp_server/query_builder.py` e `etl/*.sql` foram atualizadas.
- `google_ads`: `p_ads_asset_group_8784814486`, `p_ads_conversion_action_8784814486`,
  `p_ads_keyword_view_8784814486`, `p_ads_search_term_view_8784814486`,
  `p_ads_video_8784814486` — ainda nao integradas ao agente MCP.
- `facebook_ads_bronze` e `facebook_ads_silver`: `fb_ad_accounts`, `fb_ad_summary`,
  `fb_adsets`, `fb_campaigns` — metadados de conta/campanha/adset, ainda nao
  integrados ao agente MCP.
- `analytics_253977277`: novos shards `pseudonymous_users_*`, `users_*`, e tabelas
  auxiliares `conversion_events`, `ecommerce_events`, `engagement_events`,
  `page_view_events`, `session_start_events` (nao exploradas).

Dicionario de colunas atualizado em `config/column_dictionary.yml` com mapeamento
completo das novas tabelas e notas de qualidade.

**RESOLVIDO 2026-06-26:** apos autorizacao do usuario, foram executados:

1. MERGE de atribuicao de trafego em `ga4_events_ecommerce/click/pageview/submit`
   usando `ga4_dim_session_traffic` como fonte (COALESCE preservando valores ja
   preenchidos, sem sobrescrever dados validos)
2. Recalculo completo de `ga4_silver.ga4_ecommerce` (range 2024-04-10 ate ontem)
3. `pytest -m slow` confirmado: 2 passed
4. Suite completa `pytest`: 14 passed

Pendente apenas: avaliar remocao da tabela antiga `ga4_bronze.dim_session_traffic`
(ver TODO.md item 0).

## Exemplo real validado

Pergunta:

- `Como foi receita, investimento e ROAS por canal nos ultimos 7 dias?`

Resultado observado na execucao:

- `paid_search`: receita `62770.16`, spend `4922.68`, ROAS `12.75`
- `paid_social`: receita `0`, spend `27055.97`, ROAS `0`

Observacao:

- a sintese inicial da OpenAI errou porque recebia as primeiras linhas alfabeticas, quase todas zeradas
- isso foi corrigido priorizando linhas relevantes antes de montar o prompt

