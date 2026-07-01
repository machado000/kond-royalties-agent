# Mistral Analytics Agent

V1 simplificada do agente analítico da Mistral.

Arquitetura alvo:

- agente customizado
- servidor MCP
- BigQuery como fonte principal
- catálogo semântico em PT-BR
- relatórios em PDF como artefatos

## Objetivo

Responder perguntas de performance de marketing e ecommerce com:

- linguagem natural em português do Brasil
- métricas semânticas consistentes
- gráficos e tabelas como artefatos
- relatórios PDF sob demanda

## Escopo da V1

- BigQuery direto
- sem DuckDB
- sem frontend próprio
- foco em MCP + prompts + artefatos

## Estrutura

- `docs/`: visão de arquitetura e decisões
- `mcp_server/`: servidor MCP e ferramentas
- `prompts/`: instruções do agente e exemplos
- `reporting/`: geração de artefatos e PDF
- `semantic_catalog/`: métricas, dimensões e fontes aprovadas
- `tests/`: testes unitários iniciais

## Próximos passos

1. Formalizar o contrato das ferramentas MCP
2. Consolidar o catálogo semântico
3. Implementar o servidor MCP
4. Extrair a geração de relatórios
5. Configurar o agente customizado

## Setup para colaboradores

Pré-requisito: Python 3.12+.

```bash
git clone https://github.com/machado000/mistral-analytics-agent
cd mistral-analytics-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# preencher .env com sua OPENAI_API_KEY e demais variáveis

# colocar sua chave de service account do GCP em:
#   secrets/gcp-service-account.json
```

Validar a instalação:

```bash
pytest -m "not slow"
python -m mcp_server.server diagnose-bigquery
```

> Use `python -m mcp_server.server <comando>` (executado a partir da raiz
> do repositório, com o venv ativo) como forma principal de validar e rodar
> o agente — não depende do entry point instalado. O comando
> `mistral-agent-mcp` (instalado via `pip install -e .`) também deve
> funcionar como atalho; se ele falhar com
> `ModuleNotFoundError: No module named 'mcp_server'`, rode
> `pip install -e . --force-reinstall --no-deps` para regenerar a
> instalação editable.

### Usando como servidor MCP

O servidor expõe o comando `serve-mcp` (stdio). Os segredos **não**
precisam ser declarados na configuração do MCP — o servidor carrega o
arquivo `.env` do repositório automaticamente.

**Claude Code**

O repositório já inclui um `.mcp.json` na raiz, detectado automaticamente
ao abrir o projeto no Claude Code. Ele aponta para `.venv/bin/python`
(caminho relativo ao repositório), então basta ter o ambiente virtual
criado conforme o setup acima — nenhuma edição é necessária.

> Caminho relativo `.venv/bin/python` é específico de macOS/Linux. Em
> Windows, ajuste para `.venv\Scripts\python.exe` localmente.

**OpenAI Codex CLI**

O Codex lê configuração de MCP do seu arquivo global
(`~/.codex/config.toml`), não de um arquivo do repositório. Copie o
template em [`docs/codex-mcp-config.example.toml`](docs/codex-mcp-config.example.toml)
para o seu `~/.codex/config.toml`, ajustando o caminho absoluto do seu
clone local.

### Distribuição

Para instalar a partir do GitHub sem clonar manualmente:

```bash
pip install "git+https://github.com/machado000/mistral-analytics-agent"
```

Isso expõe o comando `mistral-agent-mcp` globalmente no ambiente Python
ativo — útil para apontar o `command` da configuração MCP diretamente para
o binário instalado (`mistral-agent-mcp serve-mcp`) em vez do caminho do
venv, caso prefira instalação isolada via `pipx`.

