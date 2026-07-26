# Arquitetura

## Visao geral

```text
Cliente (claude.ai, Antigravity, scripts)
        |
        v (HTTPS, OAuth ou Bearer estatico)
      Caddy
        |
        v
   Servidor MCP (container Docker, Streamable HTTP)
        |
        v
 Postgres (multiplos schemas via search_path) + catalogo semantico + relatorios
```

Para uso local/dev, o mesmo servidor tambem expoe stdio (`serve-mcp`) sem
Docker/Caddy/OAuth no caminho.

## Componentes

### Agente

- interpreta perguntas sobre performance de royalties de artistas
- decide qual ferramenta MCP usar
- resume resultados
- propoe proximos passos

### MCP

- valida entradas
- aplica regras semanticas
- consulta o Postgres (uma conexao, varios schemas via `search_path`)
- introspecta o schema real via `information_schema` quando necessario
- retorna payloads estruturados
- em producao, autentica requisicoes via token Bearer estatico e/ou OAuth
  2.1 delegado a um IdP externo (`mcp_server/oauth.py`)

### Catalogo semantico

- metricas oficiais, com dois dominios deliberadamente separados (nunca
  combinados numa mesma fonte): royalties (`royalties`, `quantity`) para
  as plataformas de audit (DSU/Orchard/Universal/Warner Chappell/Warner
  Music) e financeiro (`revenue`/`cost`/`resultado`) para o ERP Omie
  (`omie_detail`) — ver README.md para a tabela completa de metricas,
  colunas reais e sinonimos de roteamento
- dimensoes aceitas (periodo, artista, faixa, compositor, plataforma/DSP,
  territorio, origem, tipo de royalty, gravadora)
- fonte aprovada por consulta (`royalty_performance` como padrao
  cross-plataforma, mais uma `*_detail` por plataforma/dominio — ver
  `semantic_catalog/catalog.yml`)
- regras de negocio (nunca agregar entre granularidades diferentes, nunca
  combinar royalties com receita/custo do Omie)

### Relatorios

- tabelas
- graficos
- PDF final

## Fora de escopo da V1

- SQL livre pelo usuario
- frontend web dedicado
- ETL proprio dentro deste repositorio (assume-se que os schemas
  `raw`/`silver`/`marts` ja sao alimentados por um pipeline externo)

## Nota sobre o schema real

O schema de royalties foi revalidado em 2026-07-24 contra o banco de
producao. O agente consulta `public.vw_ft_dados_analiticos_union`, uma view
que unifica as fact tables das plataformas de audit de royalty (DSU,
Orchard, Universal, Warner Chappell, Warner Music) no grao artista +
periodo (mes) + origem + tipo de royalty. Omie (ERP financeiro) NAO faz
mais parte desta view (removido 2026-07-24 — era uma inclusao parcial e
acidental, ver `TODO.md`) e vive exclusivamente na fonte `omie_detail`,
com metricas/vocabulario proprios (Receita/Custo/Resultado) — ver
README.md para a referencia completa de vocabulario (metricas, colunas
reais, sinonimos de roteamento por pergunta em PT-BR). Ver
`config/postgres_sources.yml` e `config/column_dictionary.yml` para o
detalhe completo, incluindo notas de qualidade de dados (ex.: grao mensal,
nao diario). Pendencias de investigacao em [TODO.md](../TODO.md).

## Autenticacao e deploy remoto

Ver [README.md](../README.md) para o passo a passo completo de deploy em
producao (Docker + Caddy + Auth0). Resumo da decisao arquitetural: o
servidor atua apenas como *resource server* OAuth — nao implementa
`/authorize`, `/token` nem `/register`; a emissao de tokens e delegada
inteiramente a um IdP externo (Auth0 em producao), validando localmente
via JWKS. Essa escolha evita manter uma superficie de autorizacao propria
(registro de clientes, consentimento, rotacao de refresh tokens) — ver
`mcp_server/oauth.py`.
