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

### Enriquecimento (schemas de detalhe ainda nao usados)

7. [ ] Avaliar uso de `universal.dim_musica`/`dim_compositor` para
   analises por musica/compositor (hoje so ha o grao artista+periodo)
8. [ ] Avaliar uso de `warner_chappell.ft_warner_statement` para o mesmo
   tipo de detalhe do lado Warner Chappell
9. [ ] Avaliar join com `public.dim_artistas` (via `matched_artista_id`)
   para expor gravadora, CPF, IDs por plataforma/distribuidor

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
    `/royalties-mcp/*` (2026-07-16)
18. [ ] Avaliar OAuth sobre o transporte HTTP caso se queira registrar como
    "custom connector" remoto no claude.ai chat (hoje so Bearer token —
    suficiente para clientes que suportam header customizado, mas nao para
    o fluxo de conector do claude.ai)
19. [ ] Rotina de rotacao do token em `MCP_API_KEYS` (`kern-data:~/kond-royalties-mcp/.env`)
