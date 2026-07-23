# TODO

## Repositorio

- local: `~/Projetos/KOND-analytics-agent`
- remoto: [machado000/kond-royalties-agent](https://github.com/machado000/kond-royalties-agent) (privado)

## Contexto da refatoracao (2026-07-01)

Este projeto era um agente de marketing analytics sobre BigQuery
(GA4/Google Ads/Facebook Ads). Foi refatorado para consultar performance de
royalties/receita de artistas em Postgres (uma conexao, varios schemas via
`search_path`). O schema real foi validado em 2026-07-01 contra o banco de
producao (`describe-schema` + consultas de amostragem): o agente consulta
`public.vw_ft_dados_analiticos_union` (10.3M linhas), uma view que unifica
as fact tables de todas as origens/distribuidoras (DSU, Omie, Orchard,
Universal, Warner Chappell, Warner Music).

## Corrigido durante os testes de "chat" (2026-07-01)

- `mcp_server/query_runner.py` nao convertia `Decimal` (retornado pelo
  psycopg para colunas `numeric`) para `float`, quebrando a serializacao
  JSON e forcando `ask` a cair no fallback deterministico
- `RoyaltyAnswer.suggested_visual` exigia validacao estrita contra
  `VisualSuggestion`; quando a OpenAI retornava um formato ligeiramente
  diferente (ex.: `y_axis` como string em vez de lista), a resposta
  quebrava com `ValidationError` e caia no fallback — agora aceita
  `str | dict | VisualSuggestion`
- corrigida uma afirmacao incorreta deste proprio TODO/dicionario: o valor
  real da coluna `origem` e `'Warner Chappell'` (duas letras 'l'), nao
  `'Warner Chappel'` como foi registrado por engano na primeira sessao de
  introspeccao

## Tarefas pendentes

### Qualidade de dados — investigar

1. [x] Confirmado (2026-07-22): `ft_somlivre_sonymusic` NAO esta incluida
   em `vw_ft_dados_analiticos_union`. `pg_get_viewdef` mostra que a view
   uniona exatamente 6 `vw_debug_*` (DSU, Omie, Orchard, Universal, Warner
   Chappell, Warner Music) — nao existe `vw_debug_somlivre_sonymusic`. E
   uma fonte genuinamente separada, so acessivel via `somlivre_detail`.
2. [x] Mapeado (2026-07-22, ver `config/column_dictionary.yml` para o
   detalhe completo): DSU/Shows sempre quantity=1 (contagem de
   shows/contratos, nao streams); Omie sempre NULL em todo revenue_type
   (nao aplicavel, e financeiro/ERP); Orchard/Universal/Warner
   Chappell/Warner Music (todos revenue_type='Gravadora' na uniao) tem
   contagem real de streams/plays, com valores negativos ocasionais
   esperados (linhas de ajuste/estorno, nao erro de dado).
3. [ ] Investigado a fundo (2026-07-22) — achado significativo muda o
   enquadramento da pergunta original: `origem='Omie'` hoje NAO e uma
   inclusao deliberada/completa, e uma inclusao PARCIAL e ACIDENTAL.
   `vw_debug_omie_dados_analiticos` exige match de artista bem-sucedido
   (`da.id IS NOT NULL`, fuzzy contra `dim_artistas.artista_keyword`,
   quase vazio — ver item 9) para uma linha de Omie entrar na uniao. A
   contagem de linhas de Omie na view flutuou entre 11 e 2004 durante uma
   unica sessao de ~5min (evidencia de escrita concorrente em
   `dim_artistas` fora deste repositorio) — a fatia de Omie que aparece em
   `royalty_performance` hoje e essencialmente arbitraria (quais projetos
   Omie por acaso batem com uma das poucas keywords cadastradas), nao o
   financeiro completo do Omie. Decisao de politica ainda pendente com o
   time — 3 opcoes reais: (a) manter como esta hoje (inclusao parcial
   nao-intencional, confusa); (b) excluir origem='Omie' de
   `royalty_performance` por padrao (usar so `omie_detail` quando a
   pergunta for explicitamente financeira); (c) corrigir a view
   `vw_debug_omie_dados_analiticos` do lado do banco para incluir TODAS as
   linhas de Omie, nao so as com match de artista (fora do escopo deste
   repositorio, que nao tem ETL proprio).

### Planner — PT-BR

4. [x] Ampliar sinonimos de metricas/dimensoes com o vocabulario real do
   negocio (ex.: "master" vs "gravadora", "publishing" vs "editora") — ja
   coberto em `FILTER_KEYWORDS["revenue_type"]` desde a implementacao
   multi-fonte (2026-07-21); adicionado tambem `gravadora`/`label`/`selo`
   como sinonimos de dimensao (ver item 5)
5. [x] Dimensao `gravadora` exposta em `royalty_performance` via
   `matched_artista_id -> dim_artistas.gravadora` (2026-07-21). Esparsa (36
   de 660 artistas tem gravadora cadastrada), mas cobre a maior parte da
   receita na pratica (poucos artistas com gravadora concentram grande
   parte do faturamento) — linhas sem match aparecem como null, o que e
   esperado e correto (nao e um erro de matching)
6. [x] `infer_date_range` agora reconhece "ultimo ano"/"last year"
   (2026-07-21)

### Enriquecimento (fontes de detalhe por plataforma)

7. [x] Multiplas fontes de detalhe por plataforma implementadas
   (2026-07-21): `dsu_detail`, `omie_detail`, `orchard_detail`,
   `somlivre_detail`, `universal_detail`, `warner_chappell_detail`,
   `warner_music_detail` — cada uma com seu proprio schema de
   metrics/dimensions em `semantic_catalog/catalog.yml`, roteadas via novo
   campo `source` em `PlannedQuery`/`RoyaltyQueryRequest` (inferido pelo
   planner via palavras-chave de faixa/musica/compositor + plataforma, ou
   passado explicitamente pelo chamador). Validado ponta a ponta em
   producao via `ask_royalties` (faixas da Orchard por artista).
8. [x] Investigado (2026-07-21): `universal.dim_musica` JA esta joinada
   dentro da propria view `ft_universal_dados_analiticos` (por
   `codigo_musica`), expondo `titulo_musica`/`compositor` diretamente —
   nada a fazer. `universal.dim_compositor` e so a tabela de normalizacao
   de `dim_musica.compositor` (enforce de unicidade), nao adiciona nada
   alem do que ja vem via `dim_musica` — nao vale joinar separadamente.
   `warner_chappell.dim_exploitation_source` NAO estava joinada em
   `warner_chappell_detail` (que usa a tabela base
   `warner_chappell.ft_warner_statement`, sem esse join) — implementada
   como nova dimensao `platform` (canal: Spotify, Youtube, Radio, TV, Show
   etc.), validada contra o banco real.
9. [x] Investigado a fundo (2026-07-21) — NAO e viavel hoje, e um problema
   de DADOS, nao de codigo/SQL. `dim_artistas` (660 linhas) tem colunas
   dedicadas de match por plataforma quase todas vazias: `dsu_artista`
   6/660, `omie_projeto` 0/660, `cod_sony` 0/660,
   `warner_chappel_deal_scope_name` 1/660, `warner_music_artist_name`
   4/660, `artista_keyword` (usado no fuzzy-match das `vw_debug_*`) 9/660.
   Taxa de match real por plataforma (artistas distintos casados/total):
   DSU 6/7 (bom — catalogo pequeno), Omie 0/269, Somlivre 0/64, Warner
   Music 1/59, Warner Chappell 0/229. Orchard/Universal ja tem matching
   proprio resolvido dentro das suas views (ver item 8). Implementado
   apenas onde a cobertura e real: `dsu_detail.artist` agora usa
   `coalesce(match exato contra dsu_artista, nome bruto)`. Para as outras 4
   plataformas, enriquecer exigiria primeiro POPULAR as colunas de chave em
   `dim_artistas` (fora do escopo deste repositorio — nao ha ETL aqui) —
   documentado em `config/column_dictionary.yml` para nao precisar
   reinvestigar.
9b. [x] Investigado (2026-07-21): confirmado problema de encoding na fonte,
    nao no agente. 53.672 de 9.362.461 linhas de `ft_orchard_dados_analiticos`
    (~0,57%) tem `titulo_musica` corrompido (ex.:
    `????????????????????`) — padrao classico de caractere de substituicao
    (mismatch de encoding nos arquivos de statement da Orchard, antes de
    chegar neste banco). Nao ha o que corrigir no agente/SQL; item
    permanece como nota para quem mantém a ingestao dos statements da
    Orchard, caso quiram investigar do lado deles.

### Relatorio PDF

10. [ ] Criar modulo de PDF em `reporting/`
11. [ ] Adicionar comando CLI `generate-report`
12. [ ] Gerar PDF de exemplo: extrato de receita/royalties de um artista em
    um periodo
13. [ ] Validar localmente

### Infraestrutura

14. [x] Verificado (2026-07-22): todo comando CLI ja tem tool MCP real
    equivalente 1:1 (`catalog`/`config`/`diagnose-postgres`/
    `describe-schema`/`plan-query`/`run-query`/`ask` <->
    `get_royalty_catalog`/`get_runtime_config`/`diagnose_postgres_access`/
    `describe_schema`/`plan_royalty_query`/`run_royalty_query`/
    `ask_royalties`). O unico gap real e `generate_royalty_report`, que
    depende do modulo de PDF (itens 10-13, `reporting/` ainda so tem um
    README) — nao ha o que converter antes desse modulo existir.
15. [x] Implementado (2026-07-22): `mcp_server/responder.py` agora envia
    `text.format` (Structured Outputs, `json_schema` + `strict: true`) na
    chamada `POST /v1/responses`, com o schema completo de `RoyaltyAnswer`
    (`suggested_visual` como objeto com `type`/`x_axis`/`y_axis`/`title`,
    tudo em `required` com `null` para opcionais). Elimina na origem a
    classe de erro corrigida em 2026-07-01 (`y_axis` como string). Validado
    contra a OpenAI real e dados de producao (`generation_mode: openai`,
    `suggested_visual` com `y_axis` sempre lista).
16. [x] Decidido (2026-07-22), sem codigo novo: o contrato de artefato
    visual da V1 e `RoyaltyAnswer.suggested_visual` (tipo/eixos/titulo,
    endurecido pelo item 15) + as linhas cruas de
    `RoyaltyQueryResult.rows`. Avaliado adicionar uma grammar declarativa
    renderizavel (Vega-Lite) e descartado: os consumidores reais
    observados (Claude via Artifacts, Antigravity via codigo Python
    executado) ja constroem seus proprios visuais interativos a partir dos
    dados brutos que a tool devolve — nenhum dos dois consome uma spec
    declarativa (Claude escreve React/Recharts, nao roda Vega-Lite), entao
    uma grammar server-side nao pouparia trabalho real de nenhum agente.
    Revisitar so se surgir um consumidor que realmente precise de uma
    imagem ja renderizada (ex.: o futuro modulo de PDF, itens 10-13).
17. [x] Transporte HTTP remoto (`mcp_http.py`, `serve-http`) portado da
    versao BigQuery e deployado em Docker em `kern-data`
    (`~/kond-royalties-mcp/`), atras do Caddy do Prefect via path
    `/kond-royalties-mcp/*` (2026-07-16, renomeado de `/royalties-mcp/*`)
18. [x] OAuth 2.1 sobre o transporte HTTP para o conector remoto do
    claude.ai — implementado em `mcp_server/oauth.py` (delegacao a IdP
    externo, coexiste com `MCP_API_KEYS`), validado ponta a ponta em
    producao via Auth0 (2026-07-20). WorkOS AuthKit foi tentado primeiro e
    abandonado apos falha nao diagnosticada de `invalid_target` no token
    exchange — ver `.context/architecture-notes.md`
19. [x] Rotina de rotacao do token em `MCP_API_KEYS` implementada (2026-07-22):
    `scripts/deploy.sh` agora sincroniza `MCP_API_KEYS` do `.env` LOCAL para
    o `.env` remoto (`kern-data:~/kond-royalties-mcp/.env`) a cada deploy —
    rotacionar passa a ser so editar o valor localmente e rodar o deploy,
    sem SSH manual
20. [ ] Rotina de rotacao dos client secrets Auth0 — agora 3 Applications
    dedicadas no tenant `dev-paer1atuombl2qf5.us.auth0.com` (Claude,
    ChatGPT-Codex, Antigravity; ver README.md). Client ID/Secret de cada
    uma guardados em `.env` local (`OAUTH_CLAUDE_*`/`OAUTH_CHATGPT_*`/
    `OAUTH_ANTIGRAVITY_*`) apenas como referencia — o servidor nao le essas
    vars, sao coladas manualmente na configuracao de cada cliente externo
21. [x] Testar `ask_royalties` com dados reais atraves do conector
    conectado no claude.ai — confirmado (2026-07-21), resposta correta com
    dados reais de receita por artista
22. [x] Script de deploy rapido (`scripts/deploy.sh`): sincroniza codigo
    para `kern-data`, reconstroi a imagem, reinicia o container e roda
    smoke tests (metadados RFC 9728, token estatico, opcionalmente
    `ask_royalties` com uma pergunta real via `scripts/deploy.sh "pergunta"`)
23. [x] Re-introspeccao completa do schema real feita (2026-07-22),
    achados corrigidos nos 3 arquivos de config:
    - `ft_dsu_shows_logs` nao existe mais no banco (tabela dropada) —
      referencia removida de `column_dictionary.yml`
    - `warner_chappell_detail` apontava para `warner_chappell.ft_warner_statement`,
      que se revelou STALE (congelada em 2025-12, 39.143 linhas, identica
      a `stg_warner_statement_old` — parece uma copia pontual nunca mais
      atualizada). Trocado para `warner_chappell.stg_warner_statement`
      (34 colunas, 130.473 linhas, 2024-03 a 2026-03, dedup confirmado via
      unique(source_file, line_number) e row_hash sem duplicatas) em
      `postgres_sources.yml`/`catalog.yml`/`column_dictionary.yml`,
      validado contra o banco real (`run_planned_query`). Root cause
      corrigido do lado do banco no mesmo dia (fora deste repo):
      `ft_warner_statement` foi dropada e recriada como VIEW sobre
      `stg_warner_statement` (sempre atualizada dai em diante), e
      `public.ft_warner_chappell_dados_analiticos` passou a ler direto de
      `stg_warner_statement` — `warner_chappell_detail` continua em
      `stg_warner_statement` (mais colunas), mas a staleness em si nao
      existe mais em nenhuma das duas views
    - Documentadas 3 materialized views ate entao nao catalogadas
      (`mv_ft_dados_analiticos_agg`, `mv_ft_orchard_revenue`,
      `mv_ft_universal_magmedia`) e 5 tabelas de referencia da Universal
      (`dim_cliente`/`dim_fonte`/`dim_grupo_renda`/`dim_magmedia_fields`/
      `dim_tipo_renda`) — a maioria ja resolvida indiretamente dentro das
      views `ft_*_dados_analiticos` existentes, sem necessidade de novo
      join no agente
24. [x] Skill `dsu-dia-critico` criada (2026-07-23,
    `.claude/skills/dsu-dia-critico/`) para qualidade de agendamento DSU:
    % de shows CONFIRMADO em `dia_critico` (sexta/sabado/vespera de
    feriado) por artista, e datas futuras de `dia_critico` sem contrato
    CONFIRMADO (oportunidade de venda perdida). Criada
    `public.vw_dsu_contratos_calendario` (view) para dar suporte barato a
    uso repetido: dedup de `ft_dsu_controle_contratos` por `contrato`
    (25 contratos tinham 2 linhas — transicao de status ao longo do
    tempo, mantida so `max(inserted_at)`) + LEFT JOIN com
    `dim_calendario`. `dsu_detail` (catalogo semantico) migrado para essa
    view (antes `ft_dsu_dados_analiticos`), ganhando `contratante`/
    `vendedor`/`tipo_evento`/`tag`/`dia_critico` como dimensoes.
25. [x] Tools MCP `dsu_booking_quality` e `dsu_missed_opportunities`
    criadas (2026-07-23, `mcp_server/dsu_analytics.py`) implementando as
    duas queries do skill acima como tools reais — expostas via stdio,
    HTTP e CLI (`dsu-booking-quality`/`dsu-missed-opportunities`),
    mantendo a paridade CLI/MCP 1:1 do item 14. Corrigido durante o
    desenvolvimento: `data_livre` (coluna DATE) nao era serializavel para
    JSON via `mcp_stdio.py` (sem `default=str`, ao contrario do CLI) —
    `_normalize_value` agora converte `date`/`datetime` para ISO string,
    alem do `Decimal` ja tratado em `query_runner.py`. Validado ponta a
    ponta em producao (CLI + `tools/call` HTTP real).
26. [ ] Avaliar se vale expor `ft_dsu_controle_contratos` (tabela raw,
    nao deduplicada, com as 25 linhas de transicao de status visiveis)
    como fonte separada para auditoria de historico de status — hoje so
    `vw_dsu_contratos_calendario` (deduplicada) e exposta; nao implementado
    por falta de caso de uso concreto ainda.
