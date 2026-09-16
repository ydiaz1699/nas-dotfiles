---
name: docker-boot-order
description: >
  Arranque escalonado de contenedores Docker en el NAS (nas-dotfiles). ACTIVAR
  SIEMPRE al crear, eliminar, detener o reordenar un servicio Docker, o al
  ajustar restart policies o systemd de arranque. Garantiza que cualquier LLM
  recuerde registrar el servicio en layers.conf y usar los comandos correctos.
  Palabras clave: crear servicio, eliminar servicio, layers.conf, boot-order,
  arranque, reboot, restart policy, no-boot, capa, boot-enable.
---

# Skill `docker-boot-order`

El NAS arranca los contenedores por **capas** tras un reboot, mediante
`docker-boot-staged.service` → `$NAS_DOTFILES/shell/scripts/boot-order.sh`, que
lee `$dkco/scripts/layers.conf`. La restart policy de los servicios persistentes
es `on-failure:5` (NO `unless-stopped`) para que systemd controle el orden y no
se dispare un pico de I/O al bootear.

Guía canónica (leerla para cualquier detalle): `docs/docker-boot-staged-guide.md`.

## Regla obligatoria para el LLM

Cuando ayudes al usuario a **crear, eliminar o detener** un servicio Docker en
este NAS, NO basta con el compose y `svc up`: SIEMPRE debes cerrar el ciclo del
arranque escalonado y darle el comando exacto.

### Al CREAR un servicio nuevo
Después de `mkdir` → compose/.env → permisos → `svc up` → verificar →
`svc catalog-sync`, añadir el servicio a `$dkco/scripts/layers.conf` en la capa
correcta según sus dependencias. Dar SIEMPRE este paso al usuario, por ejemplo:

```bash
nano "$dkco/scripts/layers.conf"   # añadir <svc> en la capa que corresponda
```

Capas de referencia:
- **Capa 1:** `datasql` (base de datos).
- **Capa 2:** consumidores de la DB. **Home Assistant primero** (usa PostgreSQL).
- **Capa 3:** broker IoT y acceso a hardware (`emqx`, `esphome`).
- **Capa 4:** consumidores MQTT (`iobroker`, `node-red`, dependen de `emqx`).
- **Capa 5:** independientes/livianos (`adguard`, `filebrowser`, `ntfy`, ...).
- **Capa 6:** dashboard y herramientas al final (`homepage`, `vscode`).

Con `BOOT_ORDER_REQUIRE_ALL=1` (default), un Compose presente en `$dkco` que
falte en `layers.conf` **hace fallar el arranque** — por eso es obligatorio
registrarlo al crearlo. `flowise-worker` NO va como línea: es interno del
Compose `flowise`.

### REGLA: depends_on interno = service_started (no service_healthy)

Si un compose tiene un contenedor que depende de OTRO del MISMO compose (worker,
sidecar, init), su `depends_on` debe usar `condition: service_started`, NO
`service_healthy`. Con `service_healthy`, `docker compose up` (lo que corre
`svc up`) bloquea esperando el health; en arranque en frío con CPU saturada se
agota su wait interno con "dependency failed to start: container X is unhealthy"
y el boot falla ANTES de que boot-order.sh pueda esperar con tolerancia. Con
`service_started` el dependiente arranca cuando el principal inicia; el health
real lo vigila boot-order.sh y el contenedor conserva su healthcheck.
Dependencias hacia OTRO compose (por `db_net`) no usan `depends_on`.
Caso aplicado: flowise-worker → flowise. Pendiente: lobehub → rustfs.

### Al ELIMINAR un servicio
Quitar su línea de `$dkco/scripts/layers.conf` junto con su carpeta de `$dkco`.

### Al DETENER un servicio a propósito
Para que un reboot no lo reviva ni bloquee su capa (saltar-con-aviso):

```bash
svc no-boot <svc>       # crea $dkco/<svc>/.no-boot; el boot lo salta sin fallar
svc boot-enable <svc>   # reactivarlo
```

## Contexto de ejecución (IMPORTANTE)

- `svc` tiene dos CLIs. El usuario puede tener `NAS_CLI=python` por defecto.
  `no-boot`/`boot-enable` existen en AMBOS (Python delega a Bash).
- El arranque escalonado (`boot-order.sh`, systemd) SIEMPRE corre con
  `NAS_CLI=bash`. En procedimientos paste-safe para scripts del boot, fijar
  `NAS_CLI=bash` explícitamente.
- Separación código/datos: los scripts viven en `$NAS_DOTFILES/shell/scripts/`
  (versionados). La configuración y logs runtime viven en `$dkco/scripts/`
  (`layers.conf`, `boot-order.log`) y NO se versionan. Nunca crear scripts en
  `$dkco`.
- Dentro de una capa el arranque es SECUENCIAL por defecto
  (`BOOT_ORDER_SERIAL=1`); el orden de las líneas es el orden de arranque.
- La unidad systemd se genera con rutas reales mediante
  `shell/scripts/install-boot-service.sh` (no se copia con rutas fijas).

## Comandos de referencia

```bash
# Aplicar/actualizar el arranque escalonado
NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/boot-order.sh"          # arranque manual
NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/apply-restart-policy.sh" # migrar policies
NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/find-no-extends.sh"      # compose sin extends
cat "$dkco/scripts/boot-order.log"                                 # log del arranque

# Excluir/reactivar en el boot
svc no-boot <svc>
svc boot-enable <svc>
```
