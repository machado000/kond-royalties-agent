# Arquitetura

## Visão geral

```text
Agente customizado
        |
        v
   Servidor MCP
        |
        v
 BigQuery + catálogo semântico + relatórios
```

## Componentes

### Agente

- interpreta perguntas
- decide qual ferramenta MCP usar
- resume resultados
- propõe próximos passos

### MCP

- valida entradas
- aplica regras semânticas
- consulta o BigQuery
- retorna payloads estruturados

### Catálogo semântico

- métricas oficiais
- dimensões aceitas
- fontes aprovadas
- regras de negócio

### Relatórios

- tabelas
- gráficos
- PDF final

## Fora de escopo da V1

- DuckDB
- sync diário local
- frontend web dedicado
- SQL livre pelo usuário

