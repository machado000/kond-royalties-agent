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

## Skill/tools de qualidade de agendamento DSU (2026-07-23)

Skill `.claude/skills/dsu-dia-critico/` responde duas perguntas de negocio
sobre booking de shows ao vivo (DSU): % de shows CONFIRMADO em
`dia_critico` (sexta/sabado/vespera de feriado) por artista, e datas
futuras de `dia_critico` ainda sem contrato CONFIRMADO (oportunidade de
venda). Suporte de dados: view nova `public.vw_dsu_contratos_calendario`
(dedup de `ft_dsu_controle_contratos` por `contrato` — 25 contratos tinham
2 linhas de transicao de status — + LEFT JOIN com `dim_calendario`).
Implementado tambem como tools MCP reais (`dsu_booking_quality`,
`dsu_missed_opportunities`, `mcp_server/dsu_analytics.py`), expostas via
stdio/HTTP/CLI mantendo a paridade 1:1 (ver TODO.md item 14). `dsu_detail`
no catalogo semantico migrou para essa mesma view (antes apontava para
`ft_dsu_dados_analiticos`), ganhando `contratante`/`vendedor`/
`tipo_evento`/`tag`/`dia_critico` como dimensoes novas.

## Separacao Royalties x Financeiro (2026-07-24)

Omie e um ERP financeiro (contas a pagar/receber, passado e futuro) — nao
uma plataforma de audit de royalties como DSU/Orchard/Universal/Warner
Chappell/Warner Music. Investigacao anterior (TODO.md item 3) ja tinha
identificado que a presenca de `origem='Omie'` em
`vw_ft_dados_analiticos_union` era uma inclusao PARCIAL e ACIDENTAL (exigia
match fuzzy de artista contra um cadastro quase vazio, contagem de linhas
instavel entre sessoes). O usuario removeu Omie da view diretamente no
banco; em resposta, o catalogo semantico e o planner foram reestruturados
para tornar a separacao estrutural, nao so documental:

- **Vocabulario de metrica deliberadamente sem sobreposicao**: fontes de
  royalty (`royalty_performance` + todas as `*_detail` de plataforma de
  audit) usam a chave/rotulo `royalties`; `omie_detail` usa
  `revenue`/`cost`/`resultado` (Receita/Custo/Resultado). Nenhuma fonte
  expoe as duas — `query_builder.py` rejeita a combinacao via validacao
  contra o catalogo (`ValueError: Metricas nao aprovadas`), entao a
  separacao e imposta em tempo de execucao, nao so por convencao.
- **Roteamento de pergunta (planner.py) tambem separado**: palavras como
  "royalties"/"direitos autorais"/"remuneração autoral" mapeiam para a
  metrica `royalties`; "receita"/"custo"/"lucro"/"resultado"/"omie" mapeiam
  para `omie_detail` via `SOURCE_STANDALONE_KEYWORDS` (antes, "Omie" so
  existia como um valor de filtro em `origem` — removido, ja que Omie nao
  e mais um valor valido dessa dimensao).
- **Renomeacao de colunas (fora deste repo, direto no banco)**: a view
  unificada e as 6 `vw_debug_*` por tras dela tiveram colunas renomeadas
  para PT-BR no mesmo dia (`period`->`periodo`, `artist`->`artista`,
  `origem`->`plataforma_origem`, `revenue_type`->`tipo_remuneracao`,
  `quantity`->`quantidade`, e — numa segunda rodada, no meio da mesma
  sessao — `revenue`->`valor_liquido`->`valor_royalties`). Cada rename
  quebrou `catalog.yml` (colunas resolvidas via `expression_hint`
  apontando para nomes que deixaram de existir) ate ser recorrigido —
  ver nota operacional em `next-session.md` sobre reconferir schema real
  quando outro processo tem acesso direto de DDL.
- **Verificacao ao vivo**: ambos os dominios testados contra a URL de
  producao real pos-deploy — pergunta de royalty (`sum(valor_royalties)`
  via `royalty_performance`) e pergunta financeira ("receita e custo do
  ultimo mes", roteada para `omie_detail` com split `revenue`/`cost` por
  sinal de `valor_liquido`).

Consequencia pratica: uma pergunta ambigua tipo "qual a receita?" agora
resolve para o dominio financeiro (Omie) por padrao, nao para royalties —
mudanca deliberada, ja que "receita" no vocabulario de negocio deste
projeto passou a significar especificamente o financeiro/ERP.

## Limites conhecidos

- a geracao de resposta da OpenAI ainda usa `requests` direto na API `POST /v1/responses`
- output schema estrito com `json_schema` ja implementado (2026-07-22, ver
  `mcp_server/responder.py` — Structured Outputs, `strict: true`)
- ainda nao existe geracao de PDF
- ainda nao existem tools MCP para relatorio (`generate_royalty_report` pendente)
- ainda nao existe camada de artefatos visuais alem da sugestao estruturada
- ainda nao existe uma fonte de comparacao explicita Royalties x Financeiro
  lado a lado (discutida 2026-07-24, nao implementada — ver TODO.md)

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
