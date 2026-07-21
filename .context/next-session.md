# Proxima Sessao

## Onde continuar

- local: `~/Projetos/KOND-analytics-agent`
- remoto: [machado000/kond-royalties-agent](https://github.com/machado000/kond-royalties-agent) (privado, branch `main`)
- producao: `kern-data` (`~/kond-royalties-mcp/`), Docker + Caddy, OAuth via Auth0

## O que foi feito (sessoes 2026-07-01 a 2026-07-20)

Refatoracao completa do agente de marketing analytics (BigQuery) para um
agente de performance de royalties de artistas (Postgres), schema real
validado contra producao, deploy remoto em Docker com autenticacao dupla
(Bearer estatico + OAuth 2.1), e **conector remoto validado ponta a ponta
no claude.ai**. Detalhes completos em `architecture-notes.md` e
`project-status.md`; resumo do que mudou por ultimo:

- transporte HTTP (`mcp_server/mcp_http.py`) deployado em Docker em
  `kern-data`, atras de Caddy, com rotas para o app principal
  (`/kond-royalties-mcp/*`) e para os metadados RFC 9728
  (`/.well-known/oauth-protected-resource/kond-royalties-mcp/*`, sem
  remocao de prefixo)
- autenticacao OAuth 2.1 (`mcp_server/oauth.py`) tentada primeiro com
  WorkOS AuthKit (abandonado apos falha consistente e nao diagnosticada de
  `invalid_target` no token exchange — ver `architecture-notes.md`), depois
  migrada para Auth0, que funcionou apos habilitar o toggle **Resource
  Parameter Compatibility Profile**
- dois bugs de portabilidade entre IdPs corrigidos: JWKS URL agora via
  OpenID Connect Discovery (nao mais um path hardcoded do WorkOS), e
  validacao do claim `iss` usa o valor auto-declarado pelo IdP na
  descoberta (nao uma normalizacao propria que quebraria com IdPs que usam
  barra final, como o Auth0)
- README.md reescrito: removidas as instrucoes de instalacao/execucao
  local, substituidas por um guia completo de deploy em producao (Docker,
  Caddy, Auth0, conexao de clientes)

## Primeiro passo recomendado

Trabalhar a lista de pendencias de qualidade de dados em `TODO.md`,
principalmente:

1. Confirmar se `ft_somlivre_sonymusic` esta coberta por
   `vw_ft_dados_analiticos_union` (nao apareceu na amostra de `origem`)
2. Mapear o significado de `quantity` por `origem`/`revenue_type`
3. Decidir se `origem='Omie'` (ERP financeiro) deve continuar na mesma
   view de "performance de royalties" por padrao

## Depois disso

1. Avaliar enriquecimento via `public.dim_artistas` e os schemas de
   detalhe (`universal.dim_musica`, `warner_chappell.ft_warner_statement`)
2. Implementar geracao de relatorio PDF (`reporting/`)
3. Ampliar vocabulario PT-BR do planner com termos reais do negocio
4. `infer_date_range` nao reconhece "ultimo ano"/"last year"
5. Rotina de rotacao do token em `MCP_API_KEYS`
   (`kern-data:~/kond-royalties-mcp/.env`)

## Cuidados

- nao expor segredos em logs (`OPENAI_API_KEY`, `DATABASE_URL`,
  `pg_password`, `MCP_API_KEYS`, `OAUTH_CLIENT_SECRET` sao redigidos onde
  aplicavel; nunca colar segredos em arquivos versionados)
- manter PT-BR em prompts e respostas
- continuar sem SQL livre para usuario final
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
