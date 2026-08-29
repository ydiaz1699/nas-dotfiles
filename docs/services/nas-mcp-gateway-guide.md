# Guía del servicio nas-mcp-gateway

> Esta ficha de servicio apunta a la arquitectura completa en
> [`docs/nas-mcp-gateway.md`](../nas-mcp-gateway.md). No duplicar aquí el
> manifest, la allowlist ni los comandos operativos.

## Estado

`nas-mcp-gateway` está preparado en el repositorio, pero todavía no está
desplegado ni validado contra el NAS runtime. La integración histórica de
LobeHub permanece separada.

## Fuente operativa

Consultar [`docs/nas-mcp-gateway.md`](../nas-mcp-gateway.md) antes de modificar
compose, helper, socket, permisos o transporte. Esa guía documenta el orden de
activación, el modo `stdio`, el modo HTTP interno, el worker lazy, el idle
timeout y las restricciones de seguridad.
