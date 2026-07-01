# Notas De Arquitetura

## Direcao escolhida

A direcao atual da V1 e minimalista:

- sem frontend proprio
- sem sync local
- sem interface inspirada no ChatGPT
- sem camada visual web nesta fase
- sem ETL proprio neste repositorio (schemas `raw`/`silver`/`marts` sao
  alimentados por um pipeline externo)

Objetivo:

- usar um agente customizado do Codex ou equivalente
- conectar tools via MCP
- consultar Postgres diretamente (uma conexao, varios schemas)
- responder em PT-BR com OpenAI
- gerar artefatos quando necessario

## Racional

- o custo de manter frontend, sync, cache local e camada analitica ao mesmo tempo ficou alto demais para a V1
- a base mais util agora e semantica + query controlada + resposta executiva
- isso reduz superficie tecnica e acelera a primeira entrega validavel

## Migracao de dominio (2026-07-01)

Este repositorio comecou como um agente de marketing analytics sobre
BigQuery (GA4/Google Ads/Facebook Ads, multiplos datasets/projetos). Foi
refatorado para um agente de performance de royalties de artistas sobre
Postgres. Principais mudancas:

- BigQuery multi-projeto/multi-dataset -> Postgres com um `DATABASE_URL` e
  varios schemas via `search_path` (`POSTGRES_SCHEMAS`)
- consulta com UNION ALL entre plataformas de marketing heterogeneas ->
  consulta simples contra uma unica tabela/view de analise (`marts.*`)
- tool de listagem de datasets do BigQuery -> tool generica
  `describe_schema`, que introspecta tabelas/colunas via
  `information_schema` (nao depende de dicionario mantido a mao para
  descobrir o schema)
- metricas/dimensoes de marketing (receita, spend, ROAS, canal, campanha) ->
  metricas/dimensoes de royalties (streams, unidades, receita, royalties,
  artista, faixa, album, plataforma/DSP, territorio)
- ETL bronze/silver de GA4 (`etl/*.sql`) removido — nao se aplica ao novo
  dominio

## Fontes reais usadas pela V1 (ATUAL)

Ainda nao confirmadas. `config/postgres_sources.yml` e
`config/column_dictionary.yml` descrevem um modelo provisorio
(`marts.royalty_performance`) ate que um `DATABASE_URL` real esteja
disponivel e `describe-schema` seja executado. Ver `TODO.md` na raiz do
repositorio para o passo a passo de validacao.

## Normalizacao atual (provisoria)

A tabela/view de analise configurada assume colunas:

- `date`
- `artist`
- `track`
- `release`
- `platform`
- `territory`
- `streams`
- `units`
- `revenue`
- `royalties`

## Limites conhecidos

- a geracao de resposta da OpenAI ainda usa `requests` direto na API `POST /v1/responses`
- ainda nao existe output schema estrito com `json_schema`
- ainda nao existe geracao de PDF
- ainda nao existem tools MCP para relatorio (`generate_royalty_report` pendente)
- ainda nao existe camada de artefatos visuais alem da sugestao estruturada
- schema real do Postgres de royalties ainda nao foi introspectado/validado

## Decisao importante

O comando `config` foi ajustado para nao expor `OPENAI_API_KEY` nem
`DATABASE_URL` (ambos redigidos na saida).
