FROM python:3.11-slim-bookworm

WORKDIR /app
COPY mcp/nas_mcp_gateway/nas_mcp_gateway.py /app/nas_mcp_gateway.py
COPY mcp/nas_mcp_gateway/nas_mcp_worker.py /app/nas_mcp_worker.py
COPY mcp/nas_mcp_gateway/nas_mcp_manifest.json /app/nas_mcp_manifest.json

ENV PYTHONUNBUFFERED=1
ENV NAS_MCP_MODE=http

# El front-door no recibe Docker socket; las operaciones pasan por el helper
# Unix montado como read-only.
ENTRYPOINT ["python", "/app/nas_mcp_gateway.py"]
