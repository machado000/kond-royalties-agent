# KOND Royalties Agent

V1 simplificada do agente analitico da KOND.

Arquitetura:

- agente customizado
- servidor MCP (Streamable HTTP para producao)
- Postgres (multiplos schemas) como fonte principal
- catalogo semantico em PT-BR
- relatorios em PDF como artefatos

## Objetivo

Responder perguntas de performance de royalties de artistas com:

- linguagem natural em portugues do Brasil
- metricas semanticas consistentes, com dominios deliberadamente separados:
  royalties (streams, unidades, royalties) e financeiro (receita, custo do
  ERP Omie) — ver referencia de vocabulario abaixo
- graficos e tabelas como artefatos
- relatorios PDF sob demanda

## Escopo da V1

- Postgres direto (uma conexao, varios schemas via `search_path`)
- sem frontend proprio
- foco em MCP + prompts + artefatos
- hospedagem compartilhada em producao (Docker + Caddy + OAuth)

## Estrutura

- `docs/`: visao de arquitetura e decisoes
- `mcp_server/`: servidor MCP e ferramentas
- `prompts/`: instrucoes do agente e exemplos
- `reporting/`: geracao de artefatos e PDF
- `semantic_catalog/`: metricas, dimensoes e fontes aprovadas
- `config/`: conexao Postgres e dicionario de colunas
- `tests/`: testes unitarios iniciais
- `Dockerfile`, `docker-compose.yml`: imagem e deploy do transporte HTTP

## Status do schema de dados

Revalidado em 2026-07-24 contra o Postgres de producao. O agente consulta
`public.vw_ft_dados_analiticos_union`, uma view que unifica a performance de
**royalties** de todas as origens/distribuidoras de audit (DSU, Orchard,
Universal, Warner Chappell, Warner Music) por artista e periodo (mes).

**Separacao royalties x financeiro (2026-07-24)**: Omie (ERP financeiro —
contas a pagar/receber) foi removido desta view — era uma inclusao parcial
e acidental (ver `TODO.md`, secao Resolvido), e semanticamente e um
dominio diferente de royalty. Omie agora vive exclusivamente na fonte
`omie_detail`, com metricas e vocabulario proprios (Receita/Custo/
Resultado), deliberadamente distintos de Royalties/Direitos autorais para
nunca serem confundidos/somados numa mesma resposta — ver a referencia de
vocabulario abaixo. Colunas da view unificada tambem foram renomeadas para
PT-BR nesse mesmo dia.

Ver `config/postgres_sources.yml` e `config/column_dictionary.yml` para o
detalhe completo (incluindo notas de qualidade de dados) e `TODO.md` para
pendencias de investigacao.

### Referencia de vocabulario: metricas, colunas e sinonimos

Cada fonte do catalogo semantico (`semantic_catalog/catalog.yml`) declara
seus proprios `metrics`/`dimensions`, com `expression_hint` resolvendo para
a coluna real. O planner (`mcp_server/planner.py`) infere fonte/metrica a
partir de palavras-chave da pergunta em PT-BR — a tabela abaixo documenta
esse mapeamento.

**Metricas**

| Metric key | Dominio | Label (PT) | Coluna/expressao real | Onde existe | Sinonimos (roteamento por pergunta) |
|---|---|---|---|---|---|
| `royalties` | Royalty | Royalties | `valor_royalties` (uniao), `valor_liquido` (DSU), `valor_liquido_moeda_conta` (Orchard), `royalty_liquido` (Somlivre), `royalties_a_pagar` (Universal), `amount_paid_less_tax` (Warner Chappell), `royalty_payable` (Warner Music) | `royalty_performance` + todas as `*_detail` de royalty | royalties, royalty, direitos autorais, remuneração autoral, repasse, arrecadação, monetização |
| `quantity` | Ambos | Quantidade | `quantidade` (uniao), varia por fonte (`unidades`, `units`, `sale_units`, `count(*)` para shows DSU) | `royalty_performance` + maioria das `*_detail` | quantidade, streams, unidades, shows, quantity, reproduções, playback, plays, play |
| `revenue` | Financeiro (Omie) | Receita | `sum(valor_liquido)` onde `valor_liquido >= 0` | so `omie_detail` | receita, faturamento |
| `cost` | Financeiro (Omie) | Custo | `sum(abs(valor_liquido))` onde `valor_liquido <= 0` | so `omie_detail` | custo, custos, despesa, despesas |
| `resultado` | Financeiro (Omie) | Resultado | `sum(valor_liquido)` (liquido) | so `omie_detail` | lucro, resultado (roteiam a fonte, nao a metrica) |
| `payable` | Financeiro (Omie) | A pagar/receber | `sum(a_pagar_ou_receber)` | so `omie_detail` | sem sinonimo dedicado — so via parametro `metrics` explicito |

**Dimensoes** (`royalty_performance`/uniao)

| Dimension key | Coluna real | Label (PT) | Sinonimos |
|---|---|---|---|
| `period` | `periodo` | Periodo | periodo, por mes, por data, mensal, anual, trimestre, semestre, data, dia, ano, mês |
| `artist` | `artista` | Artista | artista, artist, cantor, cantora, banda, grupo, mc, dj, intérprete, talento, dupla, projeto, collab, colab |
| `origem` | `plataforma_origem` | Origem | origem, distribuidora, sistema de origem, publisher, plataforma, fonte |
| `revenue_type` | `tipo_remuneracao` | Tipo de royalty | tipo de royalty, categoria de royalty, tipo de receita, categoria de receita, revenue type, tipo de arrecadação, tipo de faturamento, rubrica, linha de receita |
| `gravadora` | subquery via `matched_artista_id` -> `dim_artistas.gravadora` | Gravadora | gravadora, label, selo, master, master rights, produtora, companhia, produtora fonográfica |

**Roteamento de fonte** (qual dominio uma pergunta acessa)

| Fonte | Gatilho | Sinonimos |
|---|---|---|
| `royalty_performance` | fallback padrao | usada quando nada abaixo casa |
| `omie_detail` | palavra-chave isolada | omie, financeiro, fluxo de caixa, contas a pagar, contas a receber, erp, receita, custo, custos, despesa, despesas, lucro, resultado |
| `dsu_detail` | palavra-chave isolada | show, shows, evento, eventos, contrato de show |
| `orchard_detail`/`universal_detail`/`somlivre_detail`/`warner_chappell_detail`/`warner_music_detail` | nome da plataforma **+** palavra-chave de faixa | plataforma: orchard / universal / som livre, somlivre, sony(music) / warner chappell(l) / warner music — combinada com: faixa, musica, compositor, isrc, obra, cancao, track |

`royalties` e `revenue`/`cost` nunca coexistem na mesma fonte (validado por
`query_builder.py` contra o catalogo) — a separacao e estrutural, nao so
cosmetica.

## Deploy em producao (Docker)

O servidor roda como container Docker expondo o transporte Streamable HTTP
(`mcp_server/mcp_http.py`, comando `serve-http`), atras de um reverse proxy
Caddy que ja atende outros servicos no mesmo host. Isso permite que varias
pessoas/clientes usem o agente sem cada um precisar de credenciais de
Postgres localmente.

### Deploy rapido

```bash
scripts/deploy.sh
scripts/deploy.sh "Como foi a receita por artista nos ultimos 90 dias?"  # + testa ask_royalties
```

Sincroniza o codigo para `kern-data`, reconstroi a imagem, reinicia o
container e roda smoke tests (metadados RFC 9728, token estatico, e
opcionalmente um `ask_royalties` real se uma pergunta for passada). Nao
toca no Caddyfile nem no restante do `.env` remoto — exceto
`MCP_API_KEYS`, que e sincronizado a partir do `.env` LOCAL quando
definido. Para rotacionar o token estatico: editar `MCP_API_KEYS` no
`.env` local e rodar `scripts/deploy.sh` normalmente.

### Imagem e container

`Dockerfile` na raiz constroi a imagem (`python:3.12-slim`, instala
`.[http]`, expoe a porta 8080). `docker-compose.yml` define o servico,
carrega `.env` via `env_file`, publica uma porta direta no host e conecta
o container na rede Docker externa compartilhada com o Caddy
(`kern-prefect_default`):

```bash
docker compose build
docker compose up -d
docker compose logs --tail=30
```

### Variaveis de ambiente (`.env`)

Ver `.env.example` para o arquivo completo. Resumo:

**Postgres** — `DATABASE_URL` ou `PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/
`PGPASSWORD`/`PGSSLMODE`, mais `POSTGRES_SCHEMAS`.

**OpenAI** — `OPENAI_API_KEY`, `OPENAI_MODEL`.

**Autenticacao HTTP** (`mcp_server/oauth.py`) — pelo menos uma das duas
precisa estar configurada, o processo recusa iniciar sem nenhuma:

- `MCP_API_KEYS`: lista de tokens Bearer estaticos, separados por virgula
  — caminho rapido, sem chamada de rede, para clientes que aceitam um
  header customizado (Antigravity, scripts)
- `OAUTH_ISSUER_URL` + `OAUTH_RESOURCE_URL`: delegacao OAuth 2.1 para um
  IdP externo (Auth0 em producao) — necessario para clientes que fazem o
  fluxo OAuth completo (ex.: conector remoto do claude.ai). Token validado
  localmente como JWT (assinatura RS256 via JWKS, descoberto
  automaticamente por OpenID Connect Discovery; `iss`/`aud`/`exp`
  conferidos). `OAUTH_JWKS_URL` e `OAUTH_REQUIRED_SCOPES` sao opcionais.

Os dois mecanismos coexistem no mesmo processo: o verificador tenta o
token estatico primeiro (sem custo de rede), depois valida como JWT do IdP.

**Sempre, independente do metodo de auth**:

- `MCP_ALLOWED_HOSTS`: hosts reais (dominio[:porta]) usados neste deploy,
  para satisfazer a protecao contra DNS rebinding do SDK `mcp` sem
  desativa-la

### Reverse proxy (Caddy)

O deploy de referencia roda em `kern-data`, atras do Caddy que tambem
atende o Prefect nesse host (`KERN-prefect/Caddyfile`). Duas rotas sao
necessarias por servico:

```
kerndata1.ddns.net {
  handle /.well-known/oauth-protected-resource/kond-royalties-mcp/* {
    reverse_proxy kond-royalties-mcp:8080
  }

  handle_path /kond-royalties-mcp/* {
    reverse_proxy kond-royalties-mcp:8080
  }

  handle {
    reverse_proxy prefect-server:4200
  }

  encode gzip
}
```

- `handle_path /kond-royalties-mcp/*`: rota principal, com prefixo
  removido antes de encaminhar ao container.
- `handle /.well-known/oauth-protected-resource/kond-royalties-mcp/*`
  (**sem** remocao de prefixo): exigida pelo RFC 9728. O SDK `mcp` registra
  o endpoint de metadados usando o caminho completo do
  `OAUTH_RESOURCE_URL` (incluindo `/kond-royalties-mcp`), entao a rota
  precisa encaminhar a URL original intacta — `handle_path` quebraria isso.

Sempre validar antes de recarregar (o Caddyfile atende varios servicos, um
erro de sintaxe derruba o roteamento de todos):

```bash
docker exec kern-prefect-caddy-1 caddy validate --config /etc/caddy/Caddyfile
docker exec kern-prefect-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

### Multiplos MCPs no mesmo host

`kern-data` hospeda varios MCPs, um por servico, cada um em uma porta
direta sequencial (alem da rota HTTPS via Caddy):

| Porta | Servico |
|-------|---------|
| 8080  | `mistral-analytics-mcp` (BigQuery, legado) |
| 8081  | `kond-royalties-mcp` (este projeto) |
| 8082+ | reservado para proximos MCPs |

Ao adicionar um novo MCP nesse host: escolher a proxima porta livre,
adicionar `kerndata1.ddns.net:PORTA` em `MCP_ALLOWED_HOSTS` daquele
servico, e conectar seu `docker-compose.yml` na rede externa
`kern-prefect_default` (mesmo padrao usado aqui) para que o Caddy consiga
alcanca-lo por nome de servico.

### OAuth (Auth0) — configuracao do IdP

`kond-royalties-mcp` delega autenticacao OAuth para um tenant Auth0
dedicado. Passo a passo:

1. Criar um tenant Auth0 (free tier e suficiente).
2. **Critico**: em **Settings → Advanced → Settings**, habilitar
   **Resource Parameter Compatibility Profile** e **Include Issuer in
   Authorization Responses** (tenant-wide). Sem isso, o Auth0 ignora
   silenciosamente o parametro `resource` que os conectores enviam (RFC
   8707) e cai no comportamento legado baseado em `audience` — o sintoma e
   um erro de token exchange sem pista clara da causa.
3. **Applications → APIs → Create API**: Identifier = `OAUTH_RESOURCE_URL`
   exato (ex.: `https://kerndata1.ddns.net/kond-royalties-mcp/mcp`),
   Signing Algorithm RS256. Por padrao a API exige **Client Grant**
   explicito para autorizar qualquer client (`subject_type_authorization`
   com policy `require_client_grant` para `user` e `client`) — isso vale
   para toda aplicacao, first-party ou nao, entao o passo 5 abaixo e
   obrigatorio para cada client novo.
4. **Uma Application dedicada por cliente** (tipo *Regular Web
   Application*, first-party), cada uma com seu proprio **Allowed Callback
   URL** fixo — nao compartilhar a mesma Application entre clientes
   diferentes. Ver a tabela de modalidades de conexao abaixo para o
   callback exato de cada um.
5. Para cada Application criada, autorizar contra a API do passo 3
   (**Applications → [App] → APIs**, ou via Management API
   `POST /api/v2/client-grants` com `subject_type: "user"` — necessario
   para o fluxo Authorization Code com login real de usuario, distinto do
   `subject_type: "client"` usado em Client Credentials/M2M).
6. Usar o **Domain** do tenant (com `https://` na frente) como
   `OAUTH_ISSUER_URL`, e o **Client ID**/**Client Secret** de cada
   Application ao configurar o respectivo cliente (ver abaixo).

**Dynamic Client Registration (DCR) fica desabilitado**
(`Settings → Advanced → OIDC Dynamic Application Registration`, ou via
Management API `PATCH /api/v2/tenants/settings` com
`flags.enable_dynamic_client_registration: false`). Clientes que suportam
DCR (ChatGPT/Codex, Antigravity) registram uma Application nova e efemera
a cada conexao — no free tier do Auth0 isso estoura rapido o limite de
apps do tenant e passa a bloquear login de novos usuarios. Com DCR
desligado, todo cliente usa uma Application predefinida (passo 4) com
credenciais coladas manualmente na configuracao do cliente.

### Conectando clientes ao servidor remoto

Quatro modalidades de conexao suportadas, todas contra a mesma URL
(`https://kerndata1.ddns.net/kond-royalties-mcp/mcp`):

| Modalidade | Cliente | Autenticacao |
|---|---|---|
| Bearer estatico | scripts, curl, clientes sem suporte a OAuth | Header `Authorization` direto |
| OAuth (Application dedicada) | claude.ai | Login Auth0 + consentimento |
| OAuth (Application dedicada) | ChatGPT / Codex | Login Auth0 + consentimento |
| OAuth (Application dedicada) | Antigravity | Login Auth0 + consentimento |

#### Bearer estatico

Para scripts e clientes MCP que aceitam um header customizado direto, sem
fluxo OAuth. Formato `mcpServers` (alguns clientes usam `serverUrl`,
outros `url` — checar a documentacao do cliente especifico):

```json
{
  "mcpServers": {
    "kond_royalties": {
      "serverUrl": "https://kerndata1.ddns.net/kond-royalties-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <token de MCP_API_KEYS>"
      }
    }
  }
}
```

#### OAuth — claude.ai

Settings → Connectors → Add → Custom Connectors:

- Nome: livre
- Remote MCP server URL: `https://kerndata1.ddns.net/kond-royalties-mcp/mcp`
- Advanced settings → OAuth Client ID / OAuth Client Secret: valores da
  Application Auth0 "Claude" (callback
  `https://claude.ai/api/mcp/auth_callback` e
  `https://claude.com/api/mcp/auth_callback`)

Ao clicar Connect, o fluxo redireciona para o login do Auth0, pede
consentimento e volta para o claude.ai com o conector conectado.

#### OAuth — ChatGPT / Codex

Desde a fusao dos dois produtos no app desktop, o cliente que aparece na
tela de consentimento do Auth0 se chama "Codex" independente de qual dos
dois foi usado para iniciar a conexao.

Pre-requisito: habilitar **Developer Mode** em chatgpt.com (Configuracoes
→ Conectores → Avancado, ou Configuracoes de Workspace → Permissoes,
dependendo do tipo de conta) — o app desktop sozinho nao consegue invocar
tools de conectores customizados sem isso, mesmo que a conexao apareca
como bem-sucedida.

Ao adicionar o conector (URL do servidor + credenciais OAuth avancadas),
usar o Client ID / Client Secret da Application Auth0 "ChatGPT-Codex"
(callback fixo `https://chatgpt.com/connector_platform_oauth_redirect`).
Sem uma Application dedicada, o ChatGPT tentaria DCR automaticamente — ver
nota sobre DCR desabilitado acima.

#### OAuth — Antigravity

Configuracao central de MCP do Antigravity
(`~/.gemini/config/mcp_config.json`), com `clientId`/`clientSecret`
explicitos da Application Auth0 "Antigravity" (callback fixo
`https://antigravity.google/oauth-callback`). Sem essas credenciais
explicitas, o Antigravity tentaria DCR automaticamente (suportado
nativamente pelo cliente) — ver nota sobre DCR desabilitado acima.

### Verificacao pos-deploy

```bash
# metadados RFC 9728 (deve refletir o issuer OAuth configurado)
curl https://kerndata1.ddns.net/.well-known/oauth-protected-resource/kond-royalties-mcp/mcp

# sem token -> 401
curl -X POST https://kerndata1.ddns.net/kond-royalties-mcp/mcp -H "Content-Type: application/json" -d '{}'

# com token estatico -> 200
curl -X POST https://kerndata1.ddns.net/kond-royalties-mcp/mcp \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

Depois, confirmar que os demais servicos no mesmo host (outros MCPs,
Prefect) continuam respondendo normalmente.

## Proximos passos

1. Investigar pendencias de qualidade de dados listadas em `TODO.md`
2. Avaliar enriquecimento via schemas de detalhe (`universal`,
   `warner_chappell`) e `public.dim_artistas`
3. Implementar geracao de relatorios em PDF
4. Configurar o agente customizado
