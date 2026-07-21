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

- schema real validado contra producao: `public.vw_ft_dados_analiticos_union`
  (10.3M linhas), unificando DSU/Omie/Orchard/Universal/Warner
  Chappell/Warner Music por artista + periodo (mes) + origem + tipo de
  receita — ver `config/column_dictionary.yml` para notas de qualidade
- `catalog`, `config`, `diagnose-postgres`, `describe-schema`, `plan-query`,
  `run-query`, `ask`, `serve-mcp`, `serve-http` — todos os comandos CLI
  implementados e validados
- fluxo semantico completo: pergunta natural -> plano -> SQL controlado
  contra `public.vw_ft_dados_analiticos_union` -> Postgres -> sintese
  executiva em PT-BR via OpenAI (com fallback deterministico)

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

### Testes

- `pytest` completo: `14 passed`

## Pendente

Ver `TODO.md` na raiz — qualidade de dados (significado de `quantity` por
origem/tipo de receita, cobertura de `ft_somlivre_sonymusic`), relatorio
PDF, enriquecimento via schemas de detalhe (`universal`, `warner_chappell`,
`dim_artistas`).
