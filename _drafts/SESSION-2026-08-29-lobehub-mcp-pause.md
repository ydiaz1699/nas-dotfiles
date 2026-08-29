# Handoff — pausa de integración LobeHub ↔ nas-dotfiles por MCP

**Fecha de registro:** 2026-08-29
**Repositorio:** `ydiaz1699/nas-dotfiles`
**Estado:** pausado; la recreación final del sidecar y el preflight posterior aún no están confirmados en el NAS.

Este documento es autocontenido. No contiene tokens, API keys, contraseñas ni contenido de `.env`.

## 1. Objetivo y decisión de pausa

La integración MCP read-only entre LobeHub y `nas-dotfiles` se dejó funcionando durante la validación inicial y después se pausó para conservar los resultados, evitar nuevos conflictos y esperar una comprobación directa en el NAS. El diseño elegido mantiene:

- `lobehub-mcp` sin Docker socket;
- un helper host systemd read-only que ejecuta las operaciones permitidas mediante `svc`;
- diagnóstico MCP sanitizado, sin stderr crudo, rutas sensibles ni secretos;
- contexto explícito `execution_context.executor=host-helper`.

No se debe declarar que el socket quedó resuelto: el acceso SSH/runtime al NAS no está disponible desde este entorno.

## 2. Resultado MCP confirmado

Antes de la pausa se observó:

- POST JSON-RPC sin `Authorization`: `401` esperado;
- `tools/list` autenticado: `200`;
- content type autenticado: `application/json; charset=utf-8`;
- número de herramientas: `5`;
- `svc lobehub verify`: `Resultado: 0 fallos` en la sesión de validación anterior.

Herramientas publicadas:

1. `lobehub_preflight`
2. `lobehub_verify`
3. `lobehub_status`
4. `lobehub_providers`
5. `capabilities`

Configuración de LobeHub que funcionó:

- transporte: **Streamable HTTP**;
- endpoint: `http://lobehub-mcp:8790/mcp`;
- autenticación: **API Key**;
- valor del campo API Key: token sin prefijo `Bearer`;
- no publicar `8790` ni abrir el hostname Docker desde el navegador.

El endpoint es interno: el backend Docker de LobeHub puede resolver `lobehub-mcp`; el navegador no. El flujo válido es POST JSON-RPC, no una página GET.

## 3. Diagnóstico inicial y corrección de permisos

El primer fallo desde LobeHub fue:

```text
context: global_env=missing;compose=ok;common=ok;lobehub_env=ok;datasql_env=missing;docker_cli=ok;docker_access=ok
compose_resolved: compose config falló: permission_denied
```

La diferencia importante era la identidad de ejecución: la sesión manual se estaba haciendo como `root`, pero el helper corre como `aadm`.

La corrección aplicada en el NAS fue:

```bash
chgrp nas-mcp "$dkco/.env" "$dkco/datasql/.env"
chmod 640 "$dkco/.env" "$dkco/datasql/.env"
```

La unidad mostró:

```text
User=aadm
SupplementaryGroups=docker nas-mcp
```

La prueba correcta de lectura, equivalente al contexto del servicio, es:

```bash
sudo -u aadm -g nas-mcp test -r "$dkco/.env"
sudo -u aadm -g nas-mcp test -r "$dkco/datasql/.env"
sudo -u aadm -g nas-mcp test -r "$dkco/lobehub/.env"
sudo -u aadm -g nas-mcp test -r "$dkco/lobehub/compose.yml"
sudo -u aadm -g nas-mcp test -r "$dkco/_common.yml"
```

El resultado observado fue lectura confirmada para los cinco archivos. `sudo -u aadm test -r ...` no reproduce la unidad systemd completa: no incluye el grupo suplementario `nas-mcp`. No cambiar los secretos a `0644` o `0777` y no imprimir sus contenidos.

## 4. Estado tras reiniciar el helper

Después de corregir permisos se reinició el helper y se confirmó:

```text
helper_activo
```

La siguiente llamada MCP, sin embargo, devolvió:

```text
helper_unavailable
El helper read-only del NAS no está disponible.
```

Hipótesis técnica pendiente: `run_helper()` elimina y recrea `/run/nas/lobehub-mcp.sock`. El contenedor `lobehub-mcp` ya estaba creado con el socket anterior montado y puede conservar el inode antiguo. Esto es una inferencia no confirmada; solo una comprobación runtime puede cerrarla.

## 5. Acción exacta pendiente en el NAS

Ejecutar en el NAS, en este orden:

```bash
test -S /run/nas/lobehub-mcp.sock && echo "socket_host_ok"
svc config lobehub >/dev/null 2>&1 && echo "compose_ok"
svc recreate lobehub
svc ps lobehub
```

Después, desde LobeHub, ejecutar literalmente:

```text
Usa nas-dotfiles y ejecuta lobehub_preflight.
```

El resultado esperado es:

```text
executor: host-helper
context: global_env=ok;compose=ok;common=ok;lobehub_env=ok;datasql_env=ok;docker_cli=ok;docker_access=ok
compose_resolved: compose resoluble
```

Si continúa `helper_unavailable`, reportar solo el código sanitizado, el estado de la unidad y el resultado de `test -S`; no enviar logs crudos, tokens ni `.env`. La recreación no está confirmada desde este entorno.

## 6. Error Google Gemini independiente

También se recibió un error del proveedor:

```text
code=429
status=RESOURCE_EXHAUSTED
provider=google
model=gemini-3.1-pro
metric=generate_content_free_tier_requests
limit=0
```

Es un problema de cuota/billing/modelo/API key del proveedor Google y no un fallo del MCP, del helper, del socket ni de Docker. Revisar cuota o cambiar modelo/proveedor cuando se reanude el trabajo de LobeHub. No modificar el gateway para corregir este error.

## 7. Errores de pegado y comandos que no deben repetirse

Se observaron entradas de terminal corrompidas o duplicadas:

```text
getent grougetent
a sudo systemsudo
sudo -u aadsudo
echo "Peecho
bash: nas-mcp: orden no encontrada
```

Causa operativa: se pegaron prompts, etiquetas UI o bloques truncados/duplicados dentro de la shell.

Reglas para reanudar:

- pegar bloques completos, sin `root@Nas ... #` ni etiquetas de salida;
- no pegar `Endpoint:`, `Auth type:` o `API Key:` en Bash;
- no usar `set -e` ni `exit` directamente en la shell interactiva root;
- si el pegado se corrompe, cancelar y volver a ejecutar una sola línea o bloque limpio;
- no pedir ni compartir ningún secreto.

Las formas válidas de `svc exec` son distintas por CLI:

```bash
# Bash
NAS_CLI=bash svc exec lobehub lobehub-mcp python -c 'print("ok")'

# Python/Typer
NAS_CLI=python svc exec lobehub -- lobehub-mcp python -c 'print("ok")'
```

No usar:

```bash
svc exec lobehub lobehub-mcp -- python -c ...
```

Tampoco agregar `-T` al CLI Python ni repetir `lobehub` como servicio interno.

## 8. Criterio para continuar o cerrar

1. Ejecutar la secuencia de recreación en el NAS.
2. Ejecutar `lobehub_preflight` desde LobeHub.
3. Confirmar `executor=host-helper`, todos los checks del contexto en `ok` y `compose_resolved=compose resoluble`.
4. Ejecutar `lobehub_verify` y revisar el resultado sanitizado.
5. Separar cualquier `429` de Google del diagnóstico MCP.
6. Solo si todo lo anterior es correcto, reanudar la habilitación de agentes/tools en LobeHub.

## 9. Auditoría de fuentes y variantes

| Fuente | Tipo | Confianza | Elemento | Clasificación |
|---|---|---:|---|---|
| Resultados POST MCP de la sesión | HECHO | ALTA | `401` sin token, `200` autenticado y cinco tools | INTEGRADO |
| `lobehub_preflight` inicial | HECHO | ALTA | variables global/DataSQL no legibles y `permission_denied` | INTEGRADO |
| Comprobación systemd y grupo | HECHO | ALTA | `aadm`, `docker nas-mcp`, lectura con grupo explícito | INTEGRADO |
| Reinicio del helper y llamada posterior | HECHO | ALTA | `helper_activo` seguido de `helper_unavailable` | INTEGRADO |
| Ciclo de vida del bind mount Unix | INFERENCIA NO CONFIRMADA | MEDIA | posible socket stale | PENDIENTE: `svc recreate lobehub` |
| Error `429` del proveedor | HECHO | ALTA | cuota Google `limit=0` | FUERA_DE_ALCANCE: cuota/billing |
| `NAS_CLI=bash` frente a `NAS_CLI=python` | HECHO | ALTA | sintaxis separada y variante mezclada inválida | INTEGRADO |
| Acceso runtime directo al NAS | DESCONOCIDO | ALTA | no disponible desde este entorno | BLOQUEADO hasta ejecutar en NAS |

## 10. Archivos actualizados en la documentación

- `docs/lobehub-mcp-gateway.md`: guía canónica y estado de pausa.
- `.kiro/steering/svc-cli-runtime.md`: reglas de identidad efectiva, socket y proveedor.
- `.kiro/skills/nas-runtime-secrets/SKILL.md`: reglas reutilizables sin secretos.
- Este archivo: handoff autocontenido para la siguiente sesión.
