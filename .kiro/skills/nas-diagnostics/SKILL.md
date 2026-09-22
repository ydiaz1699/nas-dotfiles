---
name: nas-diagnostics
description: >
  Diagnostica y opera servicios Docker YA EXISTENTES en el NAS (nas-dotfiles)
  cuando algo falla o se comporta mal: contenedor caído, unhealthy, crash loop,
  reinicios, OOM, alto consumo de CPU/RAM/disco, conflicto de puerto, problemas
  de red entre servicios, o el arranque escalonado quedó a medias. Activar
  cuando el usuario reporte que un servicio EXISTENTE no funciona, está lento,
  se reinicia, no arranca, da unhealthy, o quiere revisar el estado del boot.
  Palabras clave: falla, unhealthy, caído, no arranca, reinicia, crash, OOM,
  lento, alto consumo, conflicto de puerto, no conecta, restart count,
  boot-status, arranque a medias, diagnosticar, revisar servicio.
  NO usar para CREAR/eliminar/reordenar servicios (usar docker-boot-order) ni
  para configurar bases/secretos (usar datasql / nas-runtime-secrets).
license: MIT
metadata:
  author: ydiaz1699
  version: "1.0"
  scope: [services]
  auto_invoke:
    - "Un servicio EXISTENTE falla/unhealthy/lento/crash loop/no arranca"
    - "Conflicto de puerto, OOM, red entre servicios o revisar boot-status"
---

# Skill `nas-diagnostics`

Punto de entrada para **diagnosticar y operar servicios que ya existen** en el
NAS. No crea servicios ni edita `layers.conf` (eso es `docker-boot-order`), no
configura bases ni secretos (`datasql` / `nas-runtime-secrets`): aquí el objetivo
es entender por qué un servicio existente falla o rinde mal y qué comando seguro
correr.

Guías dueñas (leerlas para el detalle; esta skill NO las duplica):

- Recetas por escenario (caído, OOM, crash loop, puerto, lento, unhealthy, red):
  `.kiro/skills/dotfile-skill/references/diagnostic.md`
- Problemas reales resueltos (síntoma → causa raíz → solución):
  `docs/troubleshooting.md`
- Arranque escalonado y su estado: `docs/docker-boot-staged-guide.md`

## Regla de arranque: primero decidir contexto

Antes de "arreglar" un servicio, distinguir si el NAS **está terminando el
arranque escalonado** de un fallo real. Tras un reboot en frío el boot tarda
~11–14 min a propósito (pausas de estabilización + servicios lentos como
flowise). No juzgar como fallo a mitad:

```bash
svc boot-status        # EN PROCESO / TERMINADO / FALLÓ
```

- `EN PROCESO` → esperar; un servicio "aún no arriba" es normal.
- `TERMINADO` → si algo sigue mal, es fallo real: diagnosticar.
- `FALLÓ` → leer el mensaje (es accionable) y revisar `$dkco/scripts/layers.conf`.

Un servicio en `.no-boot` (p. ej. porque se detuvo a propósito) aparece omitido
en el boot; eso no es un fallo. Reactivar con `svc boot-enable <svc>` si se
quiere que vuelva al arranque.

## Flujo de decisión

Seguir en orden; detenerse en cuanto se identifique la causa. Cada rama enlaza a
su receta en `references/diagnostic.md`; no reescribir esas recetas aquí.

```
1. svc health              → panorama global (¿quién está mal?)
2. svc boot-status         → ¿el NAS todavía está arrancando? (ver arriba)
3. svc ps <svc>            → ¿corre? ¿exit code? ¿restart count?
4. svc logs <svc>          → ¿qué dice el servicio? (ERROR/FATAL/Killed)
5. svc doctor              → ¿es del host? (disco, RAM, puertos, restarts)
```

Según el síntoma, ir a la receta:

| Síntoma | Receta (`references/diagnostic.md`) |
|---|---|
| No arranca / exit code ≠ 0 | «Servicio caído» |
| Exit 137 / "Killed" / OOMKilled | «OOM» |
| Se reinicia en bucle / restart count alto | «Crash loop» |
| "address already in use" | «Conflicto de puerto» |
| Alto CPU/RAM/disco, lento | «Servicio lento / alto consumo» |
| `unhealthy` en `svc health` | «Healthcheck fallando» |
| No conecta con otro servicio | «Red / conectividad» |

Antes de dar por «raro» un fallo nuevo, buscar si ya está resuelto en
`docs/troubleshooting.md` (incluye casos no evidentes: `ipv4_address` en
`db_net`, warnings de `SERVER_IP` no exportada, rate limit del proveedor LLM que
NO se arregla con `svc restart`, etc.).

## svc vs agent para diagnosticar

| Situación | Usar |
|---|---|
| Sabes qué comprobar (ps, logs, stats, restart) | `svc` directo |
| Hay que interpretar logs + contexto, o «¿qué está fallando?» | `agent "diagnostica <svc>"` |
| Quieres probar sin ejecutar nada destructivo | `NAS_AGENT_DRYRUN=1 agent "..."` |

## Reglas seguras al operar (no romper el arranque)

- `svc restart <svc>` reinicia el contenedor pero **no recrea la red**; si
  cambiaste red o el problema es de red, usar `svc down <svc> && svc up <svc>`.
- **No** ejecutar `docker network prune` para "limpiar": `db_net`, `iot_net`,
  etc. son externas y compartidas; tumbarlas afecta a otros servicios.
- Detener un servicio a propósito mientras investigas está bien, pero si va a
  quedar parado y hay reboots de por medio, usar `svc no-boot <svc>` para que el
  boot lo salte con aviso en vez de fallar la capa (`BOOT_ORDER_REQUIRE_ALL=1`).
  Revertir con `svc boot-enable <svc>`.
- Si un comando `svc` del CLI Python no existe todavía en el checkout del NAS
  (`No such command '<x>'`), reintentar con `NAS_CLI=bash svc <x>` mientras se
  actualiza el checkout.
- No cambiar `.env`, credenciales ni recrear servicios para "resolver" un error
  que en realidad es del proveedor de la API/LLM (rate limit): ver
  `docs/troubleshooting.md`.

## Casos abiertos en el NAS (referencia)

- `tasmoadmin` puede aparecer `unhealthy` y estar en `.no-boot`: revisar su
  healthcheck (receta «Healthcheck fallando») antes de reactivarlo.
- `lobehub` en `.no-boot` comparte el patrón interno `service_healthy` (rustfs)
  que bloqueaba a flowise; al reactivarlo, aplicar `service_started` en el
  `depends_on` interno.
