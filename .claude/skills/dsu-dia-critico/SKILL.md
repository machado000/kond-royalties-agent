---
name: dsu-dia-critico
description: Analisa a qualidade de agendamento de shows DSU (live/presenciais) contra os dias "dia_critico" (sexta, sabado e vesperas de feriado — as melhores noites para um show). Use quando a pergunta envolver "qualidade de agendamento DSU", "% de shows em dia critico", "dias criticos livres", "oportunidade de show perdida", ou pedir para comparar artistas por aproveitamento de agenda.
---

# DSU — qualidade de agendamento em dia_critico

Responde duas perguntas de negocio sobre o time de booking de shows DSU
(ao vivo/presenciais), usando `public.vw_dsu_contratos_calendario` — uma
view criada especificamente para este skill (2026-07-23), que ja cruza
`public.ft_dsu_controle_contratos` (contratos) com `public.dim_calendario`
(calendario com `dia_critico` pre-calculado) e ja resolve a
deduplicacao por contrato (ver abaixo):

1. **Qualidade de agendamento**: que % dos shows CONFIRMADOS de cada
   artista (ou de todos) caem em dia_critico vs. dia comum.
2. **Oportunidade perdida**: quais datas futuras de dia_critico ainda nao
   tem contrato CONFIRMADO para um dado artista — ou seja, dias bons que
   a equipe de booking ainda pode vender.

**As duas perguntas ja tem tools MCP dedicadas** (2026-07-23):
`dsu_booking_quality` (`artist` opcional) e `dsu_missed_opportunities`
(`artist` e `lookahead_days` opcionais, default 90) —
`mcp_server/dsu_analytics.py`, expostas via stdio, HTTP e CLI
(`kond-royalties-mcp dsu-booking-quality`/`dsu-missed-opportunities`).
Se estiver rodando dentro do Claude Code com acesso a essas tools MCP,
**prefira chama-las diretamente** em vez de rodar SQL manualmente — elas
implementam exatamente as queries abaixo, ja testadas contra producao.
As queries SQL ficam documentadas aqui como referencia (o que as tools
fazem por baixo) e como fallback caso as tools nao estejam disponiveis
(ex.: sessao sem o servidor MCP conectado, mas com acesso direto ao
Postgres via `.env`: `DATABASE_URL` ou
`PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD`, via `psql` ou um
script curto com `psycopg`). Manter as duas em sincronia se uma mudar.

`ft_dsu_controle_contratos`/`dim_calendario` tambem estao disponiveis via
`dsu_detail` no catalogo semantico (`plan_royalty_query`/
`run_royalty_query`/`ask_royalties`) para perguntas simples sobre
`contratante`/`vendedor`/`tipo_evento`/`local`/`status`.

## Fatos importantes sobre os dados (nao redescobrir)

- **So `status = 'CONFIRMADO'` conta como show ativo** para as duas
  perguntas — `FINANCEIRO/AGUARDAR` (aguardando financeiro),
  `CANCELADO/REMARCAR` (cancelado) e `QUALIDADE` (1 linha isolada) sao
  ignorados. Isso significa que uma data com so um contrato
  `FINANCEIRO/AGUARDAR` (nao confirmado) aparece como "livre" na query 2
  — e uma escolha deliberada (so contar o que e certo), nao um bug.
- `vw_dsu_contratos_calendario` **ja deduplica por `contrato`** (alguns
  contratos tem 2 linhas representando transicao de status ao longo do
  tempo — mesmo `contrato`/`dt_show`/`valor`, `status`/`inserted_at`
  diferentes; a view mantem so a linha com `max(inserted_at)`). Por isso
  as queries abaixo NAO precisam de `DISTINCT ON`/CTE de dedup proprio —
  so filtrar `status = 'CONFIRMADO'` direto na view.
- Existem so **7 artistas** que fazem shows DSU — `distinct artista from
  vw_dsu_contratos_calendario` da a lista completa; nao usar o cadastro
  completo de `dim_artistas` (660 artistas, a maioria nunca faz show ao
  vivo). Nome bruto (`artista`, formato "CODIGO - Nome Artistico") e
  suficiente — nao precisa casar contra `dim_artistas.dsu_artista`.
- `dia_critico` (boolean) vem de `dim_calendario`, que so cobre
  2026-01-01 a 2027-12-31. Contratos com `dt_show` anterior (2025-08 em
  diante, ~22% do total em 2026-07-23) tem `dia_critico` NULL, nao false
  — **sempre filtrar `dia_critico is not null`** na query 1 para nao
  distorcer o percentual artificialmente para baixo.
- `dt_show` cobre passado E futuro (contratos ja confirmados ate
  2027-12-31) — isso e um pipeline de booking vivo.

## Query 1 — qualidade de agendamento (% em dia_critico)

Por artista (adicionar `and dt_show <= current_date` ou
`> current_date` para separar retrospectivo/prospectivo se pedido):

```sql
select
  artista,
  count(*) as total_shows,
  count(*) filter (where dia_critico) as shows_dia_critico,
  round(100.0 * count(*) filter (where dia_critico) / nullif(count(*), 0), 1) as pct_dia_critico
from vw_dsu_contratos_calendario
where status = 'CONFIRMADO' and dia_critico is not null
group by artista
order by pct_dia_critico desc;
```

Apresentar como tabela markdown por artista, mais uma linha "Geral"
somando todos. `pct_dia_critico` alto = time de booking aproveitando bem
os melhores dias; baixo = oportunidade de melhorar a estrategia de
agenda.

## Query 2 — datas de dia_critico livres (oportunidade perdida)

Por padrao, proximos 90 dias; se o pedido mencionar um artista
especifico, filtrar `a.artista = '...'` (usar o valor exato, ex.:
`'ARA - DJ ARANA'`). Ajustar o `+ 90` se pedirem uma janela diferente.

```sql
with booked as (
  select artista, dt_show
  from vw_dsu_contratos_calendario
  where status = 'CONFIRMADO'
),
artists as (
  select distinct artista from vw_dsu_contratos_calendario
),
future_critical_days as (
  select data from dim_calendario
  where dia_critico and data between current_date and current_date + 90
)
select a.artista, f.data as data_livre
from artists a
cross join future_critical_days f
left join booked b on b.artista = a.artista and b.dt_show = f.data
where b.dt_show is null
order by a.artista, f.data;
```

Apresentar agrupado por artista, com a lista de datas livres compacta
(ex.: "ARA - DJ ARANA: 13 datas livres nos proximos 90 dias, incluindo
2026-07-31, 2026-08-07, ..."). Mencionar a janela usada e deixar claro
que "livre" considera so contratos CONFIRMADO (uma data com negociacao
em andamento — FINANCEIRO/AGUARDAR — ainda aparece aqui como livre). Se a
lista for longa, mostrar so as proximas 5-10 por artista e o total.

**Atencao**: um artista com agenda 100% ocupada simplesmente NAO aparece
no resultado (o `GROUP BY`/join nao gera linha com contagem 0) — se a
pergunta for sobre um artista especifico e ele nao aparecer, reportar
explicitamente "sem datas livres na janela" em vez de dizer que a query
falhou ou que o artista nao existe.
