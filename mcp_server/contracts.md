# Contrato MCP

## Ferramentas iniciais

### `get_royalty_catalog`

Retorna o catalogo semantico ativo, com metricas, dimensoes e fontes aprovadas.

Resposta esperada:

- versao do catalogo
- metricas disponiveis
- dimensoes disponiveis
- fontes autorizadas (tabela/view em Postgres)

### `diagnose_postgres_access`

Valida a conexao com o Postgres e lista os schemas acessiveis.

### `describe_schema`

Introspecta tabelas e colunas reais de um ou mais schemas via
`information_schema`. Usada para descobrir o schema real do banco de
royalties, substituindo a manutencao manual do dicionario de colunas como
unica fonte de verdade.

Entradas:

- `schema` (opcional): nome do schema. Se omitido, usa todos os schemas
  habilitados em `POSTGRES_SCHEMAS`.

Saida:

- `schema` -> `tabela` -> lista de colunas (`column`, `data_type`, `is_nullable`)

### `run_royalty_query`

Executa uma consulta analitica controlada no Postgres.

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

### `ask_royalties`

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

### `generate_royalty_report`

Gera relatorio executivo em PDF a partir de uma pergunta ou de um resultado
estruturado (ex.: extrato de royalties por artista/periodo).

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

## Autenticacao (transporte HTTP)

Todo acesso via `serve-http` exige autenticacao — token Bearer estatico
(`MCP_API_KEYS`) e/ou OAuth 2.1 delegado a um IdP externo
(`mcp_server/oauth.py`). O servidor atua apenas como *resource server*:
nao implementa `/authorize`, `/token` nem `/register`. Ver
[README.md](../README.md) para o deploy completo (Docker, Caddy, Auth0).
