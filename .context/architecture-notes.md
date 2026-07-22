# Notas De Arquitetura

## Direcao atual

- servidor MCP com dois transportes: `stdio` (dev local) e Streamable HTTP
  (`serve-http`, producao)
- producao roda em Docker atras de Caddy, com autenticacao obrigatoria
  (Bearer estatico e/ou OAuth 2.1 delegado a um IdP externo)
- Postgres direto (uma conexao, varios schemas via `search_path`)
- resposta em PT-BR via OpenAI, com fallback deterministico
- sem ETL proprio neste repositorio (schemas alimentados por pipeline
  externo)
- sem frontend proprio

## Migracao de dominio (2026-07-01)

Este repositorio comecou como um agente de marketing analytics sobre
BigQuery (GA4/Google Ads/Facebook Ads). Foi refatorado para um agente de
performance de royalties de artistas sobre Postgres — ver `TODO.md` e
`config/column_dictionary.yml` para o schema real validado.

## Deploy remoto e OAuth (2026-07-16 a 2026-07-20)

O servidor ganhou um segundo transporte (`mcp_server/mcp_http.py`,
Streamable HTTP) portado da versao anterior sobre BigQuery, e foi
deployado em Docker em `kern-data`, atras do Caddy que tambem atende o
Prefect nesse host. Duas camadas de autenticacao coexistem no mesmo
processo (`mcp_server/oauth.py`):

- token Bearer estatico (`MCP_API_KEYS`) — caminho simples, sem IdP
- OAuth 2.1 delegado a um IdP externo — necessario para o conector remoto
  do claude.ai, que exige o fluxo OAuth completo (nao aceita so um header
  estatico via configuracao normal)

**WorkOS AuthKit foi tentado primeiro e abandonado.** A conexao,
descoberta RFC 9728/8414, DCR e o login/consentimento funcionavam, mas o
*token exchange* falhava consistentemente com `invalid_target` — testado
com Dynamic Client Registration ligado e desligado, com app recriada do
zero, com e sem `localhost` registrado como resource indicator adicional,
sempre com a mesma assinatura (nenhuma requisicao autenticada chegava ao
servidor). Pesquisa em issues publicas do `anthropics/claude-ai-mcp`
mostrou multiplos relatos identicos especificamente com WorkOS AuthKit; a
causa raiz nao foi isolada do nosso lado antes de trocar de provedor.

**Auth0 foi adotado no lugar e funcionou.** Detalhe critico: Auth0 ignora
silenciosamente o parametro `resource` (RFC 8707) que o claude.ai envia, a
menos que o toggle **Resource Parameter Compatibility Profile** esteja
habilitado em Settings → Advanced (tenant-wide) — sem isso, cai no
comportamento legado baseado em `audience` e o sintoma seria identico ao
do WorkOS. Ver README.md para o passo a passo completo.

Dois bugs reais corrigidos durante a integracao (nao especificos de
nenhum provedor):

- o JWKS URL era derivado por um path hardcoded (`/oauth2/jwks`,
  convencao do WorkOS) em vez de OpenID Connect Discovery — quebraria
  silenciosamente com qualquer outro IdP
- o claim `iss` do token era comparado contra uma normalizacao propria
  (barra final sempre removida) em vez do valor `issuer` auto-declarado
  pelo IdP na descoberta OIDC — WorkOS nao usa barra final, Auth0 usa;
  a normalizacao propria teria rejeitado todo token Auth0 valido

Ambos corrigidos em `mcp_server/oauth.py` usando descoberta OIDC padrao
(`{issuer}/.well-known/openid-configuration`) para tanto o `jwks_uri`
quanto o `issuer` de referencia — o codigo hoje e generico o suficiente
para qualquer IdP compativel, nao apenas Auth0.

## Limites conhecidos

- a geracao de resposta da OpenAI ainda usa `requests` direto na API `POST /v1/responses`
- ainda nao existe output schema estrito com `json_schema`
- ainda nao existe geracao de PDF
- ainda nao existem tools MCP para relatorio (`generate_royalty_report` pendente)
- ainda nao existe camada de artefatos visuais alem da sugestao estruturada

## Decisao importante

O comando `config` foi ajustado para nao expor segredos (`OPENAI_API_KEY`,
`DATABASE_URL`, `pg_password`) — todos redigidos na saida.

## Contrato de artefato visual (2026-07-22)

Avaliada e descartada uma grammar declarativa renderizavel (Vega-Lite) para
`suggested_visual`. Os consumidores reais em uso (Claude via Artifacts,
Antigravity via codigo Python executado) ja constroem seus proprios
visuais interativos a partir das linhas cruas que a tool MCP devolve —
nenhum consome uma spec declarativa (Claude escreve React/Recharts, nao
interpreta Vega-Lite). O contrato de V1 e simplesmente
`RoyaltyAnswer.suggested_visual` (tipo/eixos/titulo, endurecido via
Structured Outputs da OpenAI — `text.format`/`json_schema`/`strict` em
`mcp_server/responder.py`) + `RoyaltyQueryResult.rows`. Revisitar so se
surgir um consumidor que precise de uma imagem ja renderizada (ex.: modulo
de PDF, TODO.md itens 10-13) — nesse caso, a rota mais compativel entre
agentes (Claude/ChatGPT/Gemini) seria devolver um PNG via content block
`image` nativo do MCP, nao uma spec declarativa (nenhum desses agentes
renderiza Vega-Lite/Plotly/Chart.js nativamente a partir de JSON de texto).
