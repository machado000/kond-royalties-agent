# TODO

## Repositorio

- local: `~/Projetos/KOND-analytics-agent`
- remoto: a definir (renomear/criar `kond-royalties-agent` no GitHub)

## Contexto da refatoracao (2026-07-01)

Este projeto era um agente de marketing analytics sobre BigQuery
(GA4/Google Ads/Facebook Ads). Foi refatorado para consultar performance de
royalties/receita de artistas em Postgres (uma conexao, varios schemas via
`search_path`). O schema real foi validado em 2026-07-01 contra o banco de
producao (`describe-schema` + consultas de amostragem): o agente consulta
`public.vw_ft_dados_analiticos_union` (10.3M linhas), uma view que unifica
as fact tables de todas as origens/distribuidoras (DSU, Omie, Orchard,
Universal, Warner Chappel, Warner Music).

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
4. [ ] Avaliar se `origem='Warner Chappel'` (grafia com uma letra 'l' no
   dado) deveria ser corrigida na origem, ou se o agente deve continuar
   compensando isso no planner (ja implementado em
   `mcp_server/planner.py::FILTER_KEYWORDS`)

### Planner — PT-BR

5. [ ] Ampliar sinonimos de metricas/dimensoes com o vocabulario real do
   negocio (ex.: "master" vs "gravadora", "publishing" vs "editora")
6. [ ] Avaliar se vale expor uma dimensao `label`/gravadora a partir de
   `matched_artista_id` -> `dim_artistas.gravadora` (hoje nao exposta)

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
15. [ ] Avaliar output schema mais estrito para resposta OpenAI
16. [ ] Definir contrato de artefato visual alem da sugestao
17. [ ] Decidir se o repositorio remoto sera renomeado/criado como
    `kond-royalties-agent` no GitHub
