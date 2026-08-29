id: "nas-mcp-gateway"
name: "nas-mcp-gateway"
description: "Gateway MCP independiente read-only con front-door lazy y helper host allowlisted"
aliases:
  - nas-mcp-gateway
  - nas-mcp
  - mcp-nas
  - gateway-nas
image: "nas-dotfiles/nas-mcp-gateway:0.1.0"
category: "infraestructura"
port_internal: 8791
port_default: 8791
protocol: "streamable-http/stdio"
needs_proxy: true
needs_db: false
needs_redis: false
needs_s3: false
volumes:
  - "/run/nas/nas-mcp-gateway.sock:/run/nas/nas-mcp-gateway.sock (read-only)"
env_required:
  - NAS_DOTFILES
  - DOCKER_BASE
  - NAS_MCP_SERVICE_TOKEN
  - MCP_SOCKET_GID
  - MCP_HELPER_SOCKET
env_optional:
  - NAS_MCP_IDLE_SECONDS
  - MCP_ALLOWED_ORIGINS
healthcheck: 'GET /health en 8791'
backup_critical: false
backup_paths: []
protected: false
runtime_status: prepared
target_status: cataloged
docs_url: "docs/services/nas-mcp-gateway-guide.md"
notes: "Arquitectura independiente de LobeHub. El front-door responde initialize/tools/list sin iniciar el worker; tools/call inicia el worker y el worker usa el helper Unix read-only. El compose no publica el puerto en LAN: para clientes HTTP externos se requiere una red/proxy seguro. El modo stdio es el transporte recomendado para Kiro/Claude locales o vía SSH. No desplegar todavía; validar primero en el entorno autorizado. El token NAS_MCP_SERVICE_TOKEN es distinto de LOBEHUB_MCP_TOKEN."
networks:
  - nas_mcp_net
ports:
  http_internal: 8791
resources:
  memory_limit: "128m"
  memory_reservation: "32m"
security_extra:
  lazy_worker: "idle timeout configurable; default 600s"
mcp:
  enabled: true
  transport: "stdio + streamable-http"
  endpoint: "http://nas-mcp-gateway:8791/mcp"
  exposure: "internal only"
  auth: "independent bearer token for HTTP"
  tools:
    - nas_services
    - nas_health
    - nas_capabilities
    - nas_diagnostics
  mutations_exposed: false
---

# nas-mcp-gateway

La guía operativa única es `docs/nas-mcp-gateway.md`; esta ficha solo contiene
metadatos para descubrimiento y configuración del agente.
