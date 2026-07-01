# Contrato MCP

## Ferramentas iniciais

### `get_marketing_catalog`

Retorna o catalogo semantico ativo, com metricas, dimensoes e fontes aprovadas.

Resposta esperada:

- versao do catalogo
- metricas disponiveis
- dimensoes disponiveis
- datasets autorizados

### `run_marketing_query`

Executa uma consulta analitica controlada em BigQuery.

Entradas:

- `question`: pergunta original do usuario
- `metrics`: lista de metricas aprovadas
- `dimensions`: lista de dimensoes aprovadas
- `date_range`: intervalo solicitado
- `filters`: filtros estruturados
- `limit`: limite de linhas

Saida:

- `sql`
- `rows`
- `row_count`
- `source_tables`

### `ask_marketing`

Ferramenta de alto nivel para responder perguntas analiticas em portugues.

Entradas:

- `question`
- `context`: contexto opcional da conversa

Saida:

- `answer_markdown`
- `summary`
- `suggested_visual`
- `suggested_followups`
- `query_result`

### `generate_marketing_report`

Gera relatorio executivo em PDF a partir de uma pergunta ou de um resultado estruturado.

Entradas:

- `question`
- `analysis_context`
- `query_result`
- `report_title`

Saida:

- `pdf_path`
- `sections`
- `generated_at`

## Restricoes da V1

- somente fontes aprovadas no catalogo
- sem SQL livre exposto ao usuario final
- respostas em portugues do Brasil
- prioridade para clareza executiva e consistencia de metricas
