# Proxima Sessao

## Onde continuar

- local: `~/Projetos/KOND-analytics-agent`
- remoto: [machado000/kond-royalties-agent](https://github.com/machado000/kond-royalties-agent) (privado, branch `main`)
- producao: `kern-data` (`~/kond-royalties-mcp/`), Docker + Caddy, OAuth via Auth0

## O que foi feito (sessoes 2026-07-01 a 2026-07-24)

Refatoracao completa do agente de marketing analytics (BigQuery) para um
agente de performance de royalties de artistas (Postgres), schema real
validado contra producao, deploy remoto em Docker com autenticacao dupla
(Bearer estatico + OAuth 2.1), conector remoto validado ponta a ponta no
claude.ai, skill/tools de qualidade de agendamento DSU, e — na sessao mais
recente (2026-07-23/24) — uma revisao tabela a tabela de toda a
documentacao de schema seguida da separacao estrutural entre royalties e
financeiro. Detalhes completos em `architecture-notes.md` e
`project-status.md`; resumo do que mudou por ultimo:

- revisao completa (14 tabelas/views) de `config/postgres_sources.yml` e
  `config/column_dictionary.yml` contra o banco real, usando um novo MCP
  local read-only Postgres (`kond-postgres-readonly`) para consulta ad-hoc
  sem shellar `psql`
- achado e corrigido um bug real de receita: `vw_ft_dados_analiticos_union`
  contava contratos DSU duplicados e incluia contratos nao-confirmados/
  cancelados como receita (~R$606mil de duplicacao + R$17,78M de shows nao
  realizados, de um total de R$37,46M) — corrigido na view (dedup +
  `WHERE status = 'CONFIRMADO'`), verificado ao vivo (R$19.669.462,75)
- **separacao royalties x financeiro (2026-07-24)**: Omie (ERP financeiro)
  identificado como inclusao parcial/acidental em `royalty_performance` —
  removido da view unificada pelo usuario diretamente no banco. Em
  resposta, o catalogo semantico (`semantic_catalog/catalog.yml`) e o
  planner (`mcp_server/planner.py`) foram reestruturados para nunca
  confundir os dois dominios: metrica `royalties` (chave/rotulo) exclusiva
  das fontes de royalty, `revenue`/`cost`/`resultado` exclusivos de
  `omie_detail`, com vocabulario de roteamento de pergunta (PT-BR)
  tambem separado — ver README.md para a tabela completa
- colunas de `vw_ft_dados_analiticos_union` e das 6 `vw_debug_*` foram
  renomeadas para PT-BR pelo usuario diretamente no banco durante a mesma
  sessao (`period`->`periodo`, `origem`->`plataforma_origem`, etc.,
  incluindo uma segunda rodada `valor_liquido`->`valor_royalties` no meio
  da sessao) — cada rename exigiu recorrigir `expression_hint`s no
  catalogo; a licao operacional: sempre reconferir schema real via MCP
  antes de assumir que `catalog.yml` bate com o banco quando alguem mais
  tem acesso direto de DDL
- 47 testes passando (`pytest -q`), deploy + smoke test validado nos dois
  dominios (royalty e financeiro) contra a URL de producao real

## Primeiro passo recomendado

Nao ha bloqueio conhecido em producao. Se retomar trabalho, ver `TODO.md`
secao Pendente — nada e critico hoje, mas os itens mais proximos de valor
sao:

1. Relatorio PDF (`reporting/`, ainda so um README) — maior gap de feature
   da V1
2. Decidir se vale expor `ft_dsu_controle_contratos` raw como fonte de
   auditoria separada (`TODO.md` item 26)
3. Automatizar rotacao dos client secrets Auth0 (hoje manual, 3
   Applications dedicadas — `TODO.md` item 20)

## Depois disso

1. Avaliar a fonte de comparacao explicita Royalties x Financeiro
   (side-by-side, nunca somada) discutida mas nao implementada — util se
   surgir uma pergunta recorrente de "receita total da empresa"
2. Expor `periodo_receita` (mes esperado de recebimento, `periodo + 3
   meses` para statements, igual a `periodo` para DSU) como dimensao no
   catalogo semantico, se surgir caso de uso

(item anterior sobre `mv_ft_dados_analiticos_agg` resolvido 2026-07-25 —
confirmada inexistente no banco, referencia removida da documentacao)

## Cuidados

- nao expor segredos em logs (`OPENAI_API_KEY`, `DATABASE_URL`,
  `pg_password`, `MCP_API_KEYS`, `OAUTH_CLIENT_SECRET` sao redigidos onde
  aplicavel; nunca colar segredos em arquivos versionados)
- manter PT-BR em prompts e respostas
- continuar sem SQL livre para usuario final
- **nunca combinar/somar `royalties` com `revenue`/`cost` de
  `omie_detail`** numa mesma resposta — sao dominios financeiros
  diferentes (royalty vs ERP), essa e a regra critica adicionada
  2026-07-24
- `.env` e `secrets/gcp-service-account.json` sao gitignored — confirmar
  antes de qualquer push que nao foram adicionados por engano
- ao registrar valores distintos de uma coluna a partir de uma amostra,
  conferir com `length()`/`repr()` antes de documentar como fato
- ao integrar um novo IdP OAuth, nao assumir convencoes de outro provedor
  (path do JWKS, presenca de barra final no `issuer`, nome do parametro de
  audience/resource) — usar descoberta OIDC padrao e testar contra o IdP
  real antes de generalizar
- o Caddyfile atende varios servicos no mesmo host — sempre
  `caddy validate` antes de `caddy reload`, e fazer backup antes de editar
- se alguem alem deste agente tem acesso direto de DDL ao banco (como
  aconteceu 2026-07-23/24, renomes de coluna aplicados fora deste repo),
  reconferir schema real via MCP antes de confiar cegamente no
  `catalog.yml`/`column_dictionary.yml` local — eles podem ficar
  desatualizados no meio de uma sessao
- processos MCP stdio de longa duracao nao recarregam codigo Python
  editado durante a sessao (modulos ja importados ficam em memoria) —
  para smoke-testar mudancas de logica (nao so config/YAML), reiniciar o
  processo ou validar contra o endpoint HTTP de producao recem-deployado
