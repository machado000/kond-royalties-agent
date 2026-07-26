# Estado Do Projeto

## Repositorio ativo

- caminho local: `~/Projetos/KOND-analytics-agent`
- GitHub: [machado000/kond-royalties-agent](https://github.com/machado000/kond-royalties-agent) (privado, branch `main`)
- deploy de producao: `kern-data` (`~/kond-royalties-mcp/`), Docker + Caddy

## Escopo atual da V1

- agente customizado
- servidor MCP com dois transportes: stdio (dev local) e Streamable HTTP
  (producao, autenticado)
- Postgres direto (uma conexao, varios schemas via `search_path`)
- OpenAI para sintese da resposta
- catalogo semantico em PT-BR (dominio: royalties de artistas)
- sugestao de visual
- relatorio PDF ainda pendente

## O que ja funciona

### Dados

- schema real revalidado contra producao em 2026-07-24 (14 tabelas/views
  revisadas tabela a tabela): `public.vw_ft_dados_analiticos_union`
  unifica DSU/Orchard/Universal/Warner Chappell/Warner Music por artista +
  periodo (mes) + origem + tipo de royalty
- **separacao royalties x financeiro (2026-07-24)**: Omie (ERP financeiro)
  removido da view unificada — era inclusao parcial/acidental (ver
  `TODO.md`, secao Resolvido). Vocabulario/metricas agora deliberadamente
  distintos por dominio (`royalties` vs `revenue`/`cost`/`resultado`),
  nunca coexistem na mesma fonte do catalogo — ver README.md para a
  tabela completa de metricas/colunas/sinonimos
- `catalog`, `config`, `diagnose-postgres`, `describe-schema`, `plan-query`,
  `run-query`, `ask`, `serve-mcp`, `serve-http`, `dsu-booking-quality`,
  `dsu-missed-opportunities` — todos os comandos CLI implementados e
  validados, com paridade 1:1 nas tools MCP
- fluxo semantico completo: pergunta natural -> plano -> SQL controlado
  contra a fonte resolvida (`royalty_performance` ou uma `*_detail`) ->
  Postgres -> sintese executiva em PT-BR via OpenAI (com fallback
  deterministico)
- skill `dsu-dia-critico` (qualidade de agendamento de shows DSU em
  `dia_critico`) com tools MCP dedicadas (`dsu_booking_quality`,
  `dsu_missed_opportunities`), validadas em producao

### Deploy remoto e autenticacao

- container Docker (`kond-royalties-mcp`) rodando em `kern-data`, atras de
  Caddy, acessivel por porta direta (`:8081`) e por rota HTTPS
  (`/kond-royalties-mcp/*`)
- autenticacao dupla no mesmo processo (`mcp_server/oauth.py`): token
  Bearer estatico (`MCP_API_KEYS`) e OAuth 2.1 delegado a um tenant Auth0
  dedicado
- **conector remoto do claude.ai validado ponta a ponta em producao**:
  login via Auth0, consentimento, `ListToolsRequest`/`ListResourcesRequest`/
  `ListPromptsRequest` todos confirmados nos logs do servidor
- `mistral-analytics-mcp` (servico legado, projeto separado) recebeu o
  mesmo padrao de rota Caddy, sem impacto no seu funcionamento

### Ferramental local (dev/exploracao)

- MCP local read-only Postgres (`kond-postgres-readonly`, escopo `local`
  em `~/.claude.json`, fora do repositorio) para SELECT/WITH/EXPLAIN
  ad-hoc sem precisar shellar `psql` — bloqueia writes/DDL no proprio
  servidor. Processos de longa duracao (stdio) nao recarregam codigo
  Python editado na sessao — reiniciar apos mudancas em `mcp_server/*.py`
  antes de usar como smoke test de logica (config/YAML e sempre lido
  fresco, isso nao se aplica a eles)

### Testes

- `pytest` completo: `47 passed`

## Pendente

Ver `TODO.md` na raiz, secao Pendente — relatorio PDF (nao iniciado),
rotina de rotacao dos client secrets Auth0, exposicao opcional de
`ft_dsu_controle_contratos` (raw) como fonte de auditoria, e itens de
limpeza de documentacao menores.
