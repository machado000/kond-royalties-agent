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

### Distribuicao

Para instalar a partir do GitHub sem clonar manualmente:

```bash
pip install "git+https://github.com/machado000/kond-royalties-agent"
```

Isso expoe o comando `kond-royalties-mcp` globalmente no ambiente Python
ativo — util para apontar o `command` da configuracao MCP diretamente para
o binario instalado (`kond-royalties-mcp serve-mcp`) em vez do caminho do
venv, caso prefira instalacao isolada via `pipx`.
