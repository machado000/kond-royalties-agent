# KOND Royalties Agent

V1 simplificada do agente analitico da KOND.

Arquitetura alvo:

- agente customizado
- servidor MCP
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

## Estrutura

- `docs/`: visao de arquitetura e decisoes
- `mcp_server/`: servidor MCP e ferramentas
- `prompts/`: instrucoes do agente e exemplos
- `reporting/`: geracao de artefatos e PDF
- `semantic_catalog/`: metricas, dimensoes e fontes aprovadas
- `config/`: conexao Postgres e dicionario de colunas
- `tests/`: testes unitarios iniciais

## Status do schema de dados

Validado em 2026-07-01 contra o Postgres de producao. O agente consulta
`public.vw_ft_dados_analiticos_union`, uma view que unifica a performance de
royalties/receita de todas as origens/distribuidoras (DSU, Omie, Orchard,
Universal, Warner Chappell, Warner Music) por artista e periodo (mes). Ver
`config/postgres_sources.yml` e `config/column_dictionary.yml` para o
detalhe completo (incluindo notas de qualidade de dados) e `TODO.md` para
pendencias de investigacao (ex.: significado de `quantity` por
origem/tipo de receita).

## Proximos passos

1. Investigar pendencias de qualidade de dados listadas em `TODO.md`
2. Avaliar enriquecimento via schemas de detalhe (`universal`,
   `warner_chappell`) e `public.dim_artistas`
3. Implementar geracao de relatorios em PDF
4. Configurar o agente customizado

## Setup para colaboradores

Pre-requisito: Python 3.12+ e acesso a um Postgres com os schemas de royalties.

```bash
git clone https://github.com/machado000/kond-royalties-agent
cd kond-royalties-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# preencher .env com sua OPENAI_API_KEY, DATABASE_URL e POSTGRES_SCHEMAS
```

Validar a instalacao:

```bash
pytest -m "not slow"
python -m mcp_server.server diagnose-postgres
```

> Use `python -m mcp_server.server <comando>` (executado a partir da raiz
> do repositorio, com o venv ativo) como forma principal de validar e rodar
> o agente — nao depende do entry point instalado. O comando
> `kond-royalties-mcp` (instalado via `pip install -e .`) tambem deve
> funcionar como atalho; se ele falhar com
> `ModuleNotFoundError: No module named 'mcp_server'`, rode
> `pip install -e . --force-reinstall --no-deps` para regenerar a
> instalacao editable.

### Usando como servidor MCP

O servidor expoe o comando `serve-mcp` (stdio). Os segredos **nao**
precisam ser declarados na configuracao do MCP — o servidor carrega o
arquivo `.env` do repositorio automaticamente.

**Claude Code**

O repositorio ja inclui um `.mcp.json` na raiz, detectado automaticamente
ao abrir o projeto no Claude Code. Ele aponta para `.venv/bin/python`
(caminho relativo ao repositorio), entao basta ter o ambiente virtual
criado conforme o setup acima — nenhuma edicao e necessaria.

> Caminho relativo `.venv/bin/python` e especifico de macOS/Linux. Em
> Windows, ajuste para `.venv\Scripts\python.exe` localmente.

**OpenAI Codex CLI**

O Codex le configuracao de MCP do seu arquivo global
(`~/.codex/config.toml`), nao de um arquivo do repositorio. Copie o
template em [`docs/codex-mcp-config.example.toml`](docs/codex-mcp-config.example.toml)
para o seu `~/.codex/config.toml`, ajustando o caminho absoluto do seu
clone local.

**Google Antigravity**

Antigravity le configuracao de MCP do arquivo global
`~/.gemini/config/mcp_config.json` (formato `mcpServers`, com `cwd`
suportado). Template em
[`docs/antigravity-mcp-config.example.json`](docs/antigravity-mcp-config.example.json).
Em vez de editar o JSON a mao, rode (com o venv ja criado):

```bash
python scripts/install_mcp_config.py --client antigravity
```

O script faz merge da entrada `kond_royalties` na configuracao existente
(sem apagar outros servidores ja configurados) usando o caminho absoluto
deste clone e do seu `.venv`. Depois, na IDE, va em **Manage MCP Servers**
e clique em **refresh** (ou reinicie a Antigravity).

**Claude Desktop**

O Claude Desktop le configuracao de MCP do arquivo global
`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) —
formato `mcpServers`, sem suporte a `cwd`. Template em
[`docs/claude-desktop-mcp-config.example.json`](docs/claude-desktop-mcp-config.example.json).
Mesmo instalador:

```bash
python scripts/install_mcp_config.py --client claude-desktop
```

Depois, **feche completamente** o Claude Desktop (Cmd+Q, nao so a janela)
e reabra — diferente da Antigravity, ele so recarrega a configuracao de
MCP na inicializacao.

> Use `--dry-run` em qualquer um dos dois comandos acima para ver o
> resultado sem escrever o arquivo.

### Transporte remoto (Streamable HTTP)

Alem do stdio local, o servidor tambem expoe um transporte HTTP
(`mcp_server/mcp_http.py`, comando `serve-http`), para hospedagem
compartilhada — ex.: um MCP acessivel por varias pessoas/maquinas sem cada
uma precisar de credenciais de Postgres localmente. Requer o extra
`pip install ".[http]"`.

Exige duas variaveis de ambiente:

- `MCP_API_KEYS`: lista de tokens Bearer validos, separados por virgula
  (o processo recusa iniciar sem isso — nunca serve sem autenticacao)
- `MCP_ALLOWED_HOSTS`: hosts reais (dominio, sem porta se atras de proxy)
  usados neste deploy, para satisfazer a protecao contra DNS rebinding do
  SDK `mcp` sem desativa-la

Ha um deploy de referencia rodando em Docker em `kern-data`, acessivel de
duas formas (ambas ativas ao mesmo tempo):

- HTTPS via Caddy: `https://kerndata1.ddns.net/royalties-mcp/mcp`
  (`handle_path` no `KERN-prefect/Caddyfile`, sem porta propria publicada)
- HTTP direto: `http://kerndata1.ddns.net:8081/mcp` (porta publicada no
  `docker-compose.yml`, mesma convencao do `mistral-analytics-mcp` em
  `:8080`)

`kern-data` hospeda varios MCPs, um por servico, cada um em uma porta
direta sequencial, e cada um tambem pode ganhar uma rota HTTPS via Caddy
(`handle_path` no `KERN-prefect/Caddyfile`) — `mistral-analytics-mcp`
recebeu a mesma tratativa: rota `https://kerndata1.ddns.net/mistral-analytics-mcp/mcp`,
alem de continuar em `http://kerndata1.ddns.net:8080/mcp`. Para isso, seu
`docker-compose.yml` tambem passou a se conectar na rede externa
`kern-prefect_default` (mesmo padrao usado aqui), e `MCP_ALLOWED_HOSTS` no
seu `.env` inclui as duas formas de Host header (`:8080` e sem porta).

| Porta | Servico |
|-------|---------|
| 8080  | `mistral-analytics-mcp` (BigQuery, legado) |
| 8081  | `kond-royalties-mcp` (este projeto) |
| 8082+ | reservado para proximos MCPs |

Ao adicionar um novo MCP nesse host, escolher a proxima porta livre e
adicionar `kerndata1.ddns.net:PORTA` em `MCP_ALLOWED_HOSTS` daquele
servico (protecao contra DNS rebinding do SDK `mcp`). Ver `Dockerfile` e
`docker-compose.yml` na raiz do repo para o padrao completo.

### Distribuicao

Para instalar a partir do GitHub sem clonar manualmente:

```bash
pip install "git+https://github.com/machado000/kond-royalties-agent"
```

Isso expoe o comando `kond-royalties-mcp` globalmente no ambiente Python
ativo — util para apontar o `command` da configuracao MCP diretamente para
o binario instalado (`kond-royalties-mcp serve-mcp`) em vez do caminho do
venv, caso prefira instalacao isolada via `pipx`.
