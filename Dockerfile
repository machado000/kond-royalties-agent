FROM python:3.12-slim
WORKDIR /app

COPY pyproject.toml ./
COPY mcp_server ./mcp_server
COPY config ./config
COPY semantic_catalog ./semantic_catalog
COPY prompts ./prompts

RUN pip install --no-cache-dir ".[http]"

ENV PORT=8080
EXPOSE 8080

CMD ["python", "-m", "mcp_server.server", "serve-http"]
