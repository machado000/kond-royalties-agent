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

1. [ ] Confirmar se `ft_somlivre_sonymusic` esta incluida em
   `vw_ft_dados_analiticos_union` (nao apareceu nos valores distintos de
   `origem` observados na amostra inicial)
2. [ ] Mapear o significado de `quantity` por combinacao de
   `origem`/`revenue_type` (ex.: para `origem='DSU'` +
   `revenue_type='Shows'`, quantity=1 parece ser contagem de
   shows/contratos, nao streams — ver `config/column_dictionary.yml`)
3. [ ] Confirmar com o time se `origem='Omie'` (ERP financeiro) deve
   continuar misturado na mesma view de "performance de royalties" ou se
   deveria ser filtrado/separado por padrao

### Planner — PT-BR

4. [ ] Ampliar sinonimos de metricas/dimensoes com o vocabulario real do
   negocio (ex.: "master" vs "gravadora", "publishing" vs "editora")
5. [ ] Avaliar se vale expor uma dimensao `label`/gravadora a partir de
   `matched_artista_id` -> `dim_artistas.gravadora` (hoje nao exposta)
6. [ ] `infer_date_range` nao reconhece "ultimo ano"/"last year" — hoje
   cai silenciosamente em "sem intervalo explicito" (todo o historico)

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
8. [ ] `universal.dim_musica`/`dim_compositor` e
   `warner_chappell.dim_exploitation_source` ainda nao usadas como JOIN de
   enriquecimento — hoje as fontes `*_detail` expoem apenas colunas da
   propria tabela fato, sem join (decisao deliberada para evitar chaves de
   join nao confirmadas — ver `.context/architecture-notes.md`)
9. [ ] Avaliar join com `public.dim_artistas` (via `matched_artista_id` ou
   chaves especificas por plataforma — `dsu_artista`, `omie_projeto`,
   `cod_sony`, etc.) para normalizar o `artist` raw das fontes `dsu_detail`,
   `omie_detail`, `somlivre_detail` e ambas Warner — hoje essas fontes
   expoem nomes brutos, nao casados contra o cadastro de artistas
   (documentado em `config/column_dictionary.yml`)
9b. [ ] Investigar titulos de faixa corrompidos (ex.: `????????????????????`)
    observados em `orchard_detail` — possivel problema de encoding na
    fonte, nao no agente

### Relatorio PDF

10. [ ] Criar modulo de PDF em `reporting/`
11. [ ] Adicionar comando CLI `generate-report`
12. [ ] Gerar PDF de exemplo: extrato de receita/royalties de um artista em
    um periodo
13. [ ] Validar localmente

### Infraestrutura

14. [ ] Converter CLI em tools MCP reais alem das ja existentes
    (`generate_royalty_report` ainda pendente)
15. [ ] Avaliar output schema mais estrito (`json_schema`) para a resposta
    da OpenAI — reduziria a chance de o `suggested_visual` vir em formato
    inesperado (ver nota de correcao acima)
16. [ ] Definir contrato de artefato visual alem da sugestao
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
19. [ ] Rotina de rotacao do token em `MCP_API_KEYS` (`kern-data:~/kond-royalties-mcp/.env`)
20. [ ] Rotina de rotacao do client secret Auth0 (Application "Claude" no
    tenant `dev-paer1atuombl2qf5.us.auth0.com`)
21. [x] Testar `ask_royalties` com dados reais atraves do conector
    conectado no claude.ai — confirmado (2026-07-21), resposta correta com
    dados reais de receita por artista
22. [x] Script de deploy rapido (`scripts/deploy.sh`): sincroniza codigo
    para `kern-data`, reconstroi a imagem, reinicia o container e roda
    smoke tests (metadados RFC 9728, token estatico, opcionalmente
    `ask_royalties` com uma pergunta real via `scripts/deploy.sh "pergunta"`)
23. [ ] Atualizar `config/postgres_sources.yml`, `config/column_dictionary.yml`
    e `semantic_catalog/catalog.yml` com novas tabelas/campos do schema
    (planejado para uma proxima sessao) — testes serao feitos direto no
    container de producao via `scripts/deploy.sh`, ja que o projeto nao e
    critico
