---
name: nas-mcp-gateway
description: >
  Decide cuándo activar el gateway MCP read-only independiente de nas-dotfiles.
  Usa el catálogo canónico para conocer las herramientas y evita iniciar el
  worker si la solicitud no requiere consultar el NAS.
---

# Skill nas-mcp-gateway

Esta Skill aporta contexto y decisión de activación; no ejecuta Docker ni
sustituye al transporte MCP.

## Fuente canónica

El archivo canónico que la Skill debe consultar es:

```text
agent/nas_mcp_manifest.json
```

# [[file:agent/nas_mcp_manifest.json]]

No copiar manualmente nombres o esquemas en esta Skill. Si una herramienta no
está en el manifest y en `tools/list`, no está disponible.

## Cuándo solicitar nas-mcp-gateway

Solicitar la capacidad solo cuando el usuario pida información real del NAS,
por ejemplo:

- estado o salud de servicios;
- diagnóstico de Docker, disco, memoria o reinicios;
- lista de capacidades del framework;
- comprobación read-only de una incidencia.

No activarlo para preguntas generales, redacción, programación local o
explicaciones que no necesiten datos del runtime.

## Reglas de seguridad

- Todas las herramientas iniciales son read-only.
- No enviar rutas, comandos, SQL, flags ni argumentos: el esquema actual usa
  objetos vacíos.
- No pedir, imprimir ni compartir `.env`, tokens, contraseñas o API keys.
- No convertir una petición de mutación en una operación read-only parecida.
- Si el usuario pide detener, iniciar, recrear, reparar o modificar algo,
  explicar que el gateway inicial no publica mutaciones y solicitar el flujo
  administrativo autorizado.

## Activación lazy

El front-door MCP responde `initialize` y `tools/list` sin iniciar el worker.
El worker se despierta únicamente con `tools/call` y se termina después del
idle timeout. Un `helper_unavailable` significa que falta el helper o el socket;
no intentar crear el socket desde el cliente.

Para clientes locales o vía SSH, preferir `stdio`. Para HTTP, usar únicamente
un proxy/red interna autorizada con Bearer token y no publicar el puerto del
compose directamente en LAN.

## Diagnóstico de disponibilidad

Distinguir estos estados:

- `tool_not_available`: el nombre no existe en el manifest;
- `worker_unavailable`: el front-door no pudo iniciar el worker;
- `helper_unavailable`: el worker no pudo conectarse al socket host;
- `operation_timeout`: la operación fija superó su límite;
- `operation_failed`: `svc` terminó con error sanitizado.

No reintentar indefinidamente. Tras un error, informar solo el código seguro y
pedir una comprobación local del helper si el usuario está autorizado.
