# TODO

## Repositorio

- local: `/Users/joao/Documents/Codex/2026-06-25/mistral-analytics-agent`
- remoto: `https://github.com/machado000/mistral-analytics-agent`

## Arquitetura de dados (multi-projeto)

- Projetos de origem com pipelines agendados de fetch: `g-analytics-487213` (GA4),
  `facebook-ads-487216`, `gads-487211`
- O service account do MCP nao tem permissao nesses projetos de origem
- Todas as tabelas sao copiadas para `mistral-analytics`, onde rodam os testes,
  validacoes e o agente MCP consulta os dados
- Os scripts ETL bronze/silver (`etl/*.sql`) sao agendados como scheduled queries
  dentro de `g-analytics-487213`, na mesma pipeline que faz o fetch — os dados
  processados sao copiados para `mistral-analytics` junto com o resto
- `bronze_dim_session_traffic.sql` ja foi agendado nesse fluxo (2026-06-26)

## Estado validado

- query controlada em BigQuery: pronta
- selecao de datasets GA4 (bronze/silver/raw): pronta
- atribuicao de trafego via ga4_dim_session_traffic: pronta (tabela canonica trocada em 2026-06-26)
- silver ga4_ecommerce (receita agregada): pronta, recalculada contra ga4_dim_session_traffic
- teste de acuracia entre datasets: pronto, `pytest -m slow` 2 passed (corrigido em 2026-06-26)
- suite completa: `pytest` 14 passed
- dicionario de colunas: pronto (`config/column_dictionary.yml`), com secao
  `mutually_exclusive_groups` formalizando a regra GA4
- `config/bigquery_sources.yml`: documenta projetos de origem e resolucao de
  fonte padrao (default/alternatives) por logical_source
- `semantic_catalog/catalog.yml`: 4 novas metricas (users, orders,
  engaged_sessions, new_users), validadas contra BigQuery
- sintese com OpenAI: pronta
- fallback deterministico: pronto

## Tarefas pendentes

### Limpeza

0. [ ] Avaliar se a tabela antiga `ga4_bronze.dim_session_traffic` pode ser removida (substituida por `ga4_dim_session_traffic`)

### Planner — proximo passo

20. [ ] Adicionar keywords PT-BR para as novas metricas no planner (`usuarios`,
    `novos usuarios`, `pedidos`, `sessoes engajadas`) — hoje a inferencia de
    linguagem natural nao reconhece esses termos, so funciona passando
    `metrics` explicitamente

### Novas tabelas descobertas (2026-06-26) — avaliar integracao

1. [ ] google_ads: avaliar uso de `p_ads_search_term_view_8784814486` (termos de busca reais) para enriquecer analise de keywords
2. [ ] google_ads: avaliar uso de `p_ads_asset_group_8784814486` para campanhas Performance Max
3. [ ] google_ads: investigar `p_ads_video_8784814486` com apenas 16 linhas — confirmar se e gap de coleta ou dado esperado
4. [ ] facebook: avaliar uso de `fb_campaigns`, `fb_adsets`, `fb_ad_summary` para enriquecer dimensoes de campanha (objective, status, targeting)
5. [ ] facebook: `fb_ad_accounts` — avaliar uso para multi-conta caso aplicavel

### Qualidade de dados — ads

6. [ ] Revisar conexao com `google_ads` — verificar schema, cobertura de datas e completude de metricas (cost, conversions, impressions)
7. [ ] Revisar conexao com `facebook_ads_bronze` e `facebook_ads_silver` — verificar schema, cobertura e metricas disponiveis (spend, reach, purchase)
8. [ ] Criar rotina de validacao para `facebook_ads_bronze` vs `facebook_ads_silver` (mesmo padrao do teste GA4: comparar totais entre camadas)
9. [ ] Identificar problemas de qualidade em `google_ads` — campos nulos, metricas zeradas, gaps de datas, duplicatas
10. [ ] Identificar problemas de qualidade em `facebook_ads_bronze` — campos nulos, metricas zeradas, gaps de datas, duplicatas
11. [ ] Identificar problemas de qualidade em `facebook_ads_silver` — campos nulos, metricas zeradas, gaps de datas, consistencia com bronze
12. [ ] Validar cobertura e completude das novas tabelas `fb_ad_accounts`, `fb_ad_summary`, `fb_adsets`, `fb_campaigns`

### Relatorio PDF

13. [ ] Criar modulo de PDF em `reporting/`
14. [ ] Adicionar comando CLI `generate-report`
15. [ ] Gerar PDF com base na pergunta: "Como foi receita, investimento e ROAS por canal nos ultimos 7 dias?"
16. [ ] Validar localmente

### Infraestrutura

17. [ ] Converter CLI em tools MCP reais
18. [ ] Avaliar output schema mais estrito para resposta OpenAI
19. [ ] Definir contrato de artefato visual alem da sugestao
