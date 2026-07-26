# TODO

## Repositorio

- local: `~/Projetos/KOND-analytics-agent`
- remoto: [machado000/kond-royalties-agent](https://github.com/machado000/kond-royalties-agent) (privado)

## Contexto

Este projeto era um agente de marketing analytics sobre BigQuery
(GA4/Google Ads/Facebook Ads). Foi refatorado em 2026-07-01 para consultar
performance de royalties de artistas em Postgres (uma conexao, varios
schemas via `search_path`). Em 2026-07-24, apos uma revisao completa de
schema, o dominio de royalty foi separado estruturalmente do financeiro
(Omie/ERP) — ver `README.md` (referencia de vocabulario) e
`.context/architecture-notes.md` (decisao completa).

## Resolvido

Historico compacto — detalhe completo de cada item em `git log` e
`.context/architecture-notes.md`. Data = quando foi fechado.

### Qualidade de dados

- 2026-07-22 — `ft_somlivre_sonymusic` confirmado fora da view unificada
  (fonte separada, so via `somlivre_detail`).
- 2026-07-22 — `quantity` mapeado por origem/tipo de royalty (DSU sempre
  1 = contagem de shows; demais plataformas = streams/plays reais,
  negativos ocasionais esperados como estorno).
- 2026-07-22 — encoding corrompido em ~0,57% de `titulo_musica` da Orchard
  identificado como problema na origem dos statements, nao no agente.
- 2026-07-23 — re-introspeccao completa do schema: tabela dropada
  removida da doc, `warner_chappell_detail` trocado para
  `stg_warner_statement` (a versao stale `ft_warner_statement` foi
  corrigida do lado do banco no mesmo dia), 3 materialized views e 5
  tabelas de referencia da Universal documentadas.
- 2026-07-23/24 — revisao tabela a tabela (14 tabelas/views) de
  `postgres_sources.yml`/`column_dictionary.yml` contra o banco real via
  MCP local. Achado e corrigido um bug real de receita em
  `vw_ft_dados_analiticos_union`: contratos DSU contados em duplicata +
  contratos nao-confirmados/cancelados somados como receita (~R$606mil de
  duplicacao + R$17,78M de shows nao realizados, de R$37,46M) — corrigido
  na view (dedup + `WHERE status = 'CONFIRMADO'`), R$19.669.462,75
  verificado ao vivo. `dim_omie_categoria` (referencia passiva) e
  `dim_omie_grupo` (filtro ativo load-bearing) documentados;
  `warner_chappell.dim_exploitation_source` documentado como
  `detail_table` completa.
- 2026-07-24 — **`origem='Omie'` (era inclusao parcial/acidental, fuzzy
  match quase vazio, contagem instavel entre sessoes) resolvido**: Omie
  removido de `royalty_performance`/`vw_ft_dados_analiticos_union`.
  Separacao estrutural royalties x financeiro implementada no catalogo
  semantico e no planner — ver `.context/architecture-notes.md`.
- 2026-07-25 — `mv_ft_dados_analiticos_agg` confirmada inexistente no
  banco (nao aparece em `information_schema.tables` em nenhum schema —
  dropada em algum momento, provavelmente durante a limpeza de DDL do
  Omie). Nunca teve consumidor no codigo (sem `logical_source`
  correspondente). Referencia removida de `column_dictionary.yml`.

### Planner PT-BR

- 2026-07-21 — sinonimos de metricas/dimensoes ampliados com vocabulario
  real do negocio (master/gravadora, publishing/editora); dimensao
  `gravadora` exposta em `royalty_performance` via `matched_artista_id`.
- 2026-07-21 — `infer_date_range` reconhece "ultimo ano"/"last year".
- 2026-07-24 — vocabulario de metrica e roteamento de fonte separado por
  dominio (`royalties` vs `revenue`/`cost`) — ver README.md para a tabela
  completa de sinonimos.

### Enriquecimento (fontes de detalhe por plataforma)

- 2026-07-21 — fontes `*_detail` implementadas para todas as plataformas
  (dsu/omie/orchard/somlivre/universal/warner_chappell/warner_music),
  roteadas por palavra-chave ou `source` explicito.
- 2026-07-21 — `universal.dim_musica`/`dim_compositor` investigados (ja
  resolvidos via join existente na view, nada a fazer);
  `warner_chappell.dim_exploitation_source` implementado como nova
  dimensao `platform`.
- 2026-07-21 — taxa de match de `dim_artistas` por plataforma investigada
  a fundo (problema de dados, nao de codigo) — aplicado enriquecimento
  onde a cobertura e real (`dsu_detail`); demais plataformas documentadas
  como limitacao conhecida (colunas de chave quase vazias em
  `dim_artistas`, fora do escopo deste repo popular).

### Relatorio visual / infraestrutura

- 2026-07-22 — paridade CLI/MCP 1:1 confirmada para todos os comandos.
- 2026-07-22 — Structured Outputs (`json_schema`/`strict`) em
  `responder.py`, eliminando a classe de erro de `suggested_visual`
  malformado.
- 2026-07-22 — contrato de artefato visual da V1 decidido:
  `suggested_visual` + `rows` crus, sem grammar declarativa (Vega-Lite
  avaliado e descartado — ver `.context/architecture-notes.md`).
- 2026-07-16/20 — transporte HTTP (`mcp_http.py`) + OAuth 2.1 (Auth0)
  deployados em Docker/Caddy em `kern-data`, validados ponta a ponta com
  o conector remoto do claude.ai (WorkOS AuthKit tentado primeiro e
  abandonado — ver `.context/architecture-notes.md`).
- 2026-07-22 — rotacao do token `MCP_API_KEYS` automatizada via
  `scripts/deploy.sh` (sincroniza do `.env` local a cada deploy).
- 2026-07-23 — skill `dsu-dia-critico` + tools MCP `dsu_booking_quality`/
  `dsu_missed_opportunities` (qualidade de agendamento DSU em
  `dia_critico`), apoiadas pela nova view `vw_dsu_contratos_calendario`
  (dedup por contrato + join com `dim_calendario`).
- 2026-07-24 — MCP local read-only Postgres (`kond-postgres-readonly`,
  escopo `local`) para exploracao ad-hoc sem shellar `psql`.

## Pendente

### Riscos / atencao

- **Rotacao dos client secrets Auth0 ainda manual.** 3 Applications
  dedicadas (Claude, ChatGPT-Codex, Antigravity) no tenant free-tier —
  sem automatizacao nem alerta de expiracao, ao contrario do
  `MCP_API_KEYS` (ja automatizado). Risco baixo mas nao monitorado.
- **`omie_detail.artist` (`projeto`) nao e normalizado contra
  `dim_artistas`** — agora que o dominio financeiro e consultado como
  fonte de primeira classe (nao mais escondido dentro da view unificada),
  respostas sobre "receita/custo por artista" mostram o nome de projeto
  Omie bruto, nao o nome artistico. Pode ler como bug para quem nao
  conhece essa limitacao (mesma raiz do TODO historico sobre cobertura de
  match — nunca populado, fora do escopo deste repo sem ETL proprio).

### Melhorias

- **Relatorio PDF** (`reporting/`, ainda so um README) — maior gap de
  feature da V1: modulo de geracao, comando CLI `generate-report`, PDF de
  exemplo (extrato de royalties por artista/periodo), validacao local.
- **Fonte de comparacao explicita Royalties x Financeiro** lado a lado
  (nunca somada) — discutida 2026-07-24, nao implementada. Util se surgir
  pergunta recorrente tipo "receita total da empresa" que hoje nao tem
  resposta unificada por desenho.
- **`periodo_receita`** (mes esperado de recebimento — `periodo + 3
  meses` para statements, igual a `periodo` para DSU) documentado em
  `column_dictionary.yml` mas nao exposto como dimensao no catalogo
  semantico — avaliar se vale a pena expor.
- Avaliar expor `ft_dsu_controle_contratos` raw (nao deduplicado, com as
  25 linhas de transicao de status visiveis) como fonte separada de
  auditoria de historico — hoje so a view deduplicada e exposta; sem caso
  de uso concreto ainda.
