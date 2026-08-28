# Gateway HTTP sin Docker socket ni dependencias Python externas.
FROM python:3.11-slim-bookworm

WORKDIR /app
COPY lobehub_mcp.py /app/lobehub_mcp.py

ENV PYTHONUNBUFFERED=1
ENV MCP_MODE=http

# El proceso solo necesita leer el socket helper montado por compose.
# cap_drop/no-new-privileges se refuerzan también en compose.yml.
ENTRYPOINT ["python", "/app/lobehub_mcp.py"]
