# Notas De Arquitetura

## Direcao escolhida

A direcao atual da V1 e minimalista:

- sem frontend proprio
- sem DuckDB
- sem sync local
- sem interface inspirada no ChatGPT
- sem camada visual web nesta fase

Objetivo:

- usar um agente customizado do Codex ou equivalente
- conectar tools via MCP
- consultar BigQuery diretamente
- responder em PT-BR com OpenAI
- gerar artefatos quando necessario

## Racional

- o custo de manter frontend, sync, cache local e camada analitica ao mesmo tempo ficou alto demais para a V1
- a base mais util agora e semantica + query controlada + resposta executiva
- isso reduz superficie tecnica e acelera a primeira entrega validavel

## Fontes reais usadas pela V1

As queries foram baseadas nos schemas reais ja explorados no projeto anterior:

- `ga4_silver.ga4_general_traffic`
- `ga4_bronze.ga4_events_ecommerce`
- `google_ads.p_ads_ad_group_ad_8784814486`
- `facebook_ads_silver.fb_ad_insights`

## Normalizacao atual

O SQL controlado unifica as fontes em uma base logica com colunas:

- `date`
- `channel`
- `platform`
- `campaign`
- `sessions`
- `engaged_sessions`
- `users`
- `new_users`
- `conversions`
- `orders`
- `revenue`
- `spend`

## Limites conhecidos

- a geracao de resposta da OpenAI ainda usa `requests` direto na API `POST /v1/responses`
- ainda nao existe output schema estrito com `json_schema`
- ainda nao existe geracao de PDF
- ainda nao existem tools MCP formais; por enquanto existem comandos CLI
- ainda nao existe camada de artefatos visuais alem da sugestao estruturada

## Decisao importante

O comando `config` foi ajustado para nao expor `OPENAI_API_KEY`.

