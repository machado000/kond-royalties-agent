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
- metricas semanticas consistentes (streams, unidades, receita, royalties)
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

Validado em 2026-07-01 contra o Postgres de producao. O agente consulta
`public.vw_ft_dados_analiticos_union`, uma view que unifica a performance de
royalties/receita de todas as origens/distribuidoras (DSU, Omie, Orchard,
Universal, Warner Chappell, Warner Music) por artista e periodo (mes). Ver
`config/postgres_sources.yml` e `config/column_dictionary.yml` para o
detalhe completo (incluindo notas de qualidade de dados) e `TODO.md` para
pendencias de investigacao (ex.: significado de `quantity` por
origem/tipo de receita).

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
toca no `.env` remoto nem no Caddyfile.

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
   silenciosamente o parametro `resource` que o claude.ai envia (RFC 8707)
   e cai no comportamento legado baseado em `audience` — o sintoma e um
   erro de token exchange sem pista clara da causa.
3. **Applications → APIs → Create API**: Identifier = `OAUTH_RESOURCE_URL`
   exato (ex.: `https://kerndata1.ddns.net/kond-royalties-mcp/mcp`),
   Signing Algorithm RS256.
4. **Applications → Applications → Create Application**: tipo *Regular Web
   Application*, com **Allowed Callback URLs** incluindo
   `https://claude.ai/api/mcp/auth_callback` e
   `https://claude.com/api/mcp/auth_callback`. Confirmar na aba **APIs**
   que essa aplicacao esta autorizada contra a API criada no passo 3.
5. Usar o **Domain** da aplicacao (com `https://` na frente) como
   `OAUTH_ISSUER_URL`, e o **Client ID**/**Client Secret** ao adicionar o
   conector no claude.ai (ver abaixo).

### Conectando clientes ao servidor remoto

**claude.ai (Settings → Connectors → Add → Custom Connectors)**:

- Nome: livre
- Remote MCP server URL: `https://kerndata1.ddns.net/kond-royalties-mcp/mcp`
- Advanced settings → OAuth Client ID / OAuth Client Secret: os valores da
  Application Auth0 criada acima

Ao clicar Connect, o fluxo redireciona para o login do Auth0, pede
consentimento e volta para o claude.ai com o conector conectado — DCR
(Dynamic Client Registration) **nao** e necessario, o claude.ai suporta
credenciais inseridas manualmente.

**Antigravity, scripts, outros clientes com suporte a MCP remoto +
header customizado**: usar o token estatico (`MCP_API_KEYS`) direto, sem
OAuth. Formato `mcpServers` (Antigravity usa `serverUrl`; outros clientes
podem usar `url`):

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
