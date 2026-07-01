# Estado Do Projeto

## Repositorio ativo

- caminho local: `~/Projetos/KOND-analytics-agent`
- GitHub: a definir
- branch principal: `main` (git inicializado localmente em 2026-07-01,
  primeiro commit e um snapshot do estado antigo baseado em BigQuery)

## Escopo atual da V1

- agente customizado
- servidor MCP com tools reais (stdio)
- Postgres direto (uma conexao, varios schemas via `search_path`)
- OpenAI para sintese da resposta
- catalogo semantico em PT-BR (dominio: royalties de artistas)
- sugestao de visual
- relatorio PDF ainda pendente

## O que ja funciona

### Estrutura

- `pyproject.toml` com dependencias Python (`psycopg[binary]` no lugar de
  `google-cloud-bigquery`)
- prompts PT-BR em `prompts/`
- catalogo semantico em `semantic_catalog/catalog.yml` (provisorio)
- configuracao de conexao em `config/postgres_sources.yml` (provisorio)
- dicionario de colunas em `config/column_dictionary.yml` (provisorio)

### Postgres

- carrega `.env` local automaticamente
- suporta `DATABASE_URL` OU as variaveis padrao `PGHOST`/`PGPORT`/
  `PGDATABASE`/`PGUSER`/`PGPASSWORD`/`PGSSLMODE` (libpq), mais
  `POSTGRES_SCHEMAS` (schemas reais: `public,universal,warner_chappell`)
- **validado contra o banco real em 2026-07-01**: conexao, introspeccao de
  schema e consulta funcionam fim a fim

### CLI atual

Entrypoint:

- `mcp_server/server.py`

Comandos implementados:

- `catalog`
- `config`
- `diagnose-postgres`
- `describe-schema`
- `plan-query`
- `run-query`
- `ask`
- `serve-mcp`

### Fluxo semantico

- pergunta natural -> planejamento semantico (metricas/dimensoes/periodo/filtros de royalties)
- planejamento -> SQL controlado contra a tabela/view de analise (`marts.*`)
- SQL -> Postgres
- resultado -> sintese executiva em PT-BR via OpenAI
- fallback deterministico se OpenAI falhar

### Validacoes feitas

- `pytest` completo: `13 passed`
- `diagnose-postgres`, `describe-schema`, `run-query` e `ask` (com sintese
  OpenAI real) executados com sucesso contra o banco de producao — ver
  `.context/validated-commands.md`

## Descoberta do schema real (2026-07-01)

O agente consulta `public.vw_ft_dados_analiticos_union` (10.3M linhas): uma
view que unifica as fact tables de todas as origens/distribuidoras (DSU,
Omie, Orchard, Universal, Warner Chappell, Warner Music) no grao artista +
periodo (mes) + origem + tipo de receita. Detalhes e notas de qualidade em
`config/column_dictionary.yml`.

## Pendente

Ver `TODO.md` na raiz — principalmente investigacao de qualidade de dados
(significado de `quantity` por origem/tipo de receita, confirmar cobertura
de `ft_somlivre_sonymusic`) e enriquecimento via schemas de detalhe
(`universal`, `warner_chappell`, `dim_artistas`).
