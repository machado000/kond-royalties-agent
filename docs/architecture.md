# Arquitetura

## Visao geral

```text
Agente customizado
        |
        v
   Servidor MCP
        |
        v
 Postgres (raw/silver/marts) + catalogo semantico + relatorios
```

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

### Catalogo semantico

- metricas oficiais (streams, unidades, receita, royalties)
- dimensoes aceitas (data, artista, faixa, album, plataforma/DSP, territorio)
- fonte aprovada (tabela/view de analise em `marts`)
- regras de negocio

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

O schema de royalties foi validado em 2026-07-01 contra o banco de producao
(`describe-schema` + consultas de amostragem). O agente consulta
`public.vw_ft_dados_analiticos_union`, uma view que unifica as fact tables
de todas as origens/distribuidoras (DSU, Omie, Orchard, Universal, Warner
Chappell, Warner Music) no grao artista + periodo (mes) + origem + tipo de
receita. Ver `config/postgres_sources.yml` e `config/column_dictionary.yml`
para o detalhe completo, incluindo notas de qualidade de dados (ex.: grao
mensal, nao diario). Pendencias de investigacao em [TODO.md](../TODO.md).
