# Arranque escalonado de contenedores Docker

Esta implementación evita que Docker arranque todos los Compose en paralelo al reiniciar el NAS. Los servicios se agrupan en capas en `$dkco/scripts/layers.conf`; por defecto se arrancan **uno a uno dentro de cada capa** (arranque secuencial), esperando que cada contenedor esté `running` y, cuando tiene healthcheck, `healthy`, antes de pasar al siguiente. La siguiente capa no empieza hasta terminar la actual. Con `BOOT_ORDER_SERIAL=0` los servicios de una misma capa arrancan en paralelo.

## Diferencias importantes respecto al borrador original

- El código permanece en `$NAS_DOTFILES/shell/scripts`; `$dkco/scripts` contiene solo configuración, logs y lock runtime.
- El script invoca el CLI Bash real de `svc` y no trata `dk` como si fuese un ejecutor. `dk` solo cambia de directorio.
- `flowise-worker` no es una capa: es un servicio interno del Compose `flowise` y se levanta con ese proyecto.
- Un job one-shot como `lobehub-rustfs-init` puede terminar con código 0 sin bloquear el arranque; los servicios que terminan con error sí detienen las capas dependientes.
- El timeout de health por contenedor es 120 segundos por defecto. Un fallo aborta las capas siguientes para no iniciar consumidores contra una dependencia rota.
- La plantilla no conoce qué carpetas existen en el NAS real. `layers.conf` debe reflejar el resultado de `svc lista`; con `BOOT_ORDER_REQUIRE_ALL=1`, olvidar un Compose hace fallar el arranque de forma visible.
- **Pausas de estabilización (hardware modesto):** en un NAS con pocos cores, arrancar contenedores mientras el sistema recién booteado aún está saturado hace que sus healthchecks tarden o fallen (CPU al 100%). Por eso el arranque espera `BOOT_ORDER_INITIAL_DELAY` antes de la primera capa y `BOOT_ORDER_SETTLE_DELAY` entre servicios/capas, dando margen a que el CPU se asiente. En el arranque manual con el sistema ya caliente, poner ambas a `0` para no esperar.

## `depends_on` interno: usar `service_started`, no `service_healthy`

Cuando un compose tiene varios contenedores y uno depende de otro del **mismo** compose (ej. un worker que depende del servicio principal, o un init de un sidecar), ese `depends_on` debe usar **`condition: service_started`**, no `service_healthy`.

Motivo: `docker compose up -d` (lo que ejecuta `svc up`) **bloquea esperando** a que la dependencia esté `healthy` cuando la condición es `service_healthy`. En arranque en frío con CPU saturada, el servicio principal tarda en pasar su healthcheck y el wait interno de Compose se agota con `dependency failed to start: container X is unhealthy`, haciendo **fallar `svc up` y abortar el boot** — antes de que `boot-order.sh` pueda esperar con su propia tolerancia.

Con `service_started`, el dependiente arranca en cuanto el principal **inicia** (no cuando está healthy); el health real lo vigila `boot-order.sh`. El contenedor conserva su propio `healthcheck`.

Casos conocidos en el catálogo:
- **flowise:** `flowise-worker` → `flowise` usa `service_started` (aplicado).
- **lobehub:** `lobehub` → `rustfs` y `rustfs-init` → `rustfs` usan `service_healthy`. Pendiente de migrar a `service_started` cuando se reactive lobehub (hoy está en `.no-boot`).

Dependencias hacia servicios de **otro** compose (ej. consumidores de `datapostgres`/`dataredis` por `db_net`) NO usan `depends_on` — el orden lo da `layers.conf`.

La política `on-failure:5` es intencional: Docker documenta que `on-failure` reinicia solo ante salida con error y no vuelve a arrancar un contenedor simplemente porque se reinició el daemon. Así, `docker-boot-staged.service` recupera el control del orden después de un reboot. Durante la operación normal, los fallos siguen teniendo hasta cinco reintentos automáticos. Fuente: [Docker — Start containers automatically](https://docs.docker.com/config/containers/start-containers-automatically/).

## Archivos

| Archivo | Propósito |
|---|---|
| `shell/scripts/boot-order.sh` | Orquestador por capas, health gates, timeout y lock |
| `shell/scripts/layers.conf.example` | Plantilla editable de capas |
| `shell/scripts/find-no-extends.sh` | Detecta Compose que no usan `extends` |
| `shell/scripts/apply-restart-policy.sh` | Migra contenedores existentes sin arrancarlos todos |
| `shell/scripts/install-boot-service.sh` | Genera e instala la unidad systemd con las rutas reales |
| `systemd/docker-boot-staged.service.template` | Plantilla de la unidad (placeholders `{{NAS_DOTFILES}}`/`{{DOCKER_BASE}}`) |
| `$dkco/scripts/layers.conf` | Configuración runtime del NAS |
| `$dkco/scripts/boot-order.log` | Log del último/actual arranque |
| `$dkco/scripts/restart-policy-report.txt` | Resultado de la migración de policies |

## Instalación en el NAS

Ejecuta estos pasos por SSH en el NAS, con el checkout instalado y `$dkco` definido. La secuencia es deliberada: **crear carpetas → crear/copiar archivos → aplicar permisos → validar → levantar**.

### 1. Crear la carpeta runtime y copiar la configuración

```bash
mkdir -p "$dkco/scripts"
cp "$NAS_DOTFILES/shell/scripts/layers.conf.example" "$dkco/scripts/layers.conf"
chmod 755 "$NAS_DOTFILES/shell/scripts/boot-order.sh" \
  "$NAS_DOTFILES/shell/scripts/find-no-extends.sh" \
  "$NAS_DOTFILES/shell/scripts/apply-restart-policy.sh"
```

Edita la configuración y conserva únicamente servicios que realmente existan:

```bash
nano "$dkco/scripts/layers.conf"
svc lista
```

`layers.conf` debe contener todos los Compose que muestre `svc lista`, cada uno una sola vez. Para servicios que no existen en ese NAS, déjalos comentados. Si el NAS tiene un servicio no incluido, `boot-order.sh` lo señalará y no continuará mientras `BOOT_ORDER_REQUIRE_ALL=1`.

### 2. Confirmar Compose especiales

```bash
NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/find-no-extends.sh"
```

La salida es informativa: `extends` no es obligatorio para que el orquestador funcione, pero esos Compose deben declarar explícitamente `restart: on-failure:5` y no recibirán la policy desde `$dkco/_common.yml`.

### 3. Migrar contenedores existentes sin arranque masivo

Antes de ejecutar, confirma que el catálogo/runtime ya contienen la policy `on-failure:5`. El script usa `docker update` sobre contenedores existentes; no ejecuta `svc up` en todos los servicios y no imprime secretos.

```bash
NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/apply-restart-policy.sh"
cat "$dkco/scripts/restart-policy-report.txt"
```

`lobehub-rustfs-init` conserva `restart: no` porque es un job one-shot. Si el reporte contiene un error, corrígelo antes de continuar.

### 4. Probar el arranque manualmente

```bash
BOOT_ORDER_REQUIRE_ALL=1 NAS_CLI=bash \
  "$NAS_DOTFILES/shell/scripts/boot-order.sh"
cat "$dkco/scripts/boot-order.log"
svc health
```

La prueba debe terminar en `Arranque completo.`. Si una capa falla, las siguientes no se levantan. Revisa `svc logs <servicio>` y el healthcheck del servicio antes de repetirla.

### 5. Instalar y habilitar systemd

La unidad se **genera desde una plantilla** con las rutas reales de esta
instalación (`NAS_DOTFILES` y `DOCKER_BASE`), en vez de copiar un archivo con
rutas fijas. Usa el instalador:

```bash
sudo NAS_DOTFILES="$NAS_DOTFILES" DOCKER_BASE="$DOCKER_BASE" \
  "$NAS_DOTFILES/shell/scripts/install-boot-service.sh"
```

Esto escribe `/etc/systemd/system/docker-boot-staged.service` con tus rutas y
hace `daemon-reload`, pero **no** lo habilita todavía (para que pruebes primero
el Paso 4). Cuando estés conforme, habilítalo:

```bash
sudo systemctl enable docker-boot-staged.service
```

O en un solo paso, generar + habilitar:

```bash
sudo NAS_DOTFILES="$NAS_DOTFILES" DOCKER_BASE="$DOCKER_BASE" \
  "$NAS_DOTFILES/shell/scripts/install-boot-service.sh" --enable
```

Para probar la unidad sin reiniciar:

```bash
sudo systemctl start docker-boot-staged.service
systemctl is-enabled docker-boot-staged.service
sudo systemctl status docker-boot-staged.service --no-pager
```

El servicio usa `RequiresMountsFor=$DOCKER_BASE`, espera `network-online.target`
y exige que todos los Compose descubiertos estén representados en `layers.conf`.
El instalador falla si quedan placeholders sin sustituir, así que la unidad
siempre queda con rutas coherentes con la instalación. No edites el unit file a
mano en `/etc`: regenéralo con el instalador si cambian las rutas.

## Variables de entorno del arranque

| Variable | Default | Efecto |
|---|---|---|
| `BOOT_ORDER_CONFIG` | `$dkco/scripts/layers.conf` | Ruta del archivo de capas |
| `BOOT_ORDER_LOG` | `$dkco/scripts/boot-order.log` | Log del arranque |
| `BOOT_ORDER_HEALTH_TIMEOUT` | `480` | Segundos máximos de espera de readiness por contenedor. Margen amplio para arranque en frío en hardware modesto (2 cores); el arranque secuencial evita competencia de CPU/IO pero cada servicio pesado tarda más en frío |
| `BOOT_ORDER_DAEMON_TIMEOUT` | `60` | Segundos máximos de espera a que Docker responda |
| `BOOT_ORDER_REQUIRE_ALL` | `1` | Falla si un Compose de `$dkco` no está en `layers.conf` |
| `BOOT_ORDER_ALLOW_MISSING` | `0` | Con `1`, omite (en vez de fallar) servicios de `layers.conf` sin Compose |
| `BOOT_ORDER_SERIAL` | `1` | Default: arranca los servicios de cada capa uno a uno esperando readiness entre ellos. Con `0`, arranca toda la capa en paralelo |
| `BOOT_ORDER_INITIAL_DELAY` | `30` | Segundos de espera antes de la primera capa, para que el sistema recién booteado (kernel/systemd/dockerd) se estabilice antes de cargar CPU con contenedores. Poner `0` en arranque manual |
| `BOOT_ORDER_SETTLE_DELAY` | `10` | Segundos de pausa entre servicios y entre capas, para que el CPU del anterior se asiente antes del siguiente. Evita saturar CPU al 100% en hardware con pocos cores. Poner `0` en arranque manual |

## Operación

- **Agregar un servicio nuevo:** además de crearlo (compose, carpetas, `svc up`, `svc catalog-sync`), añadir su nombre a `$dkco/scripts/layers.conf` en la capa que corresponda según sus dependencias. Con `BOOT_ORDER_REQUIRE_ALL=1` (default), si el Compose existe en `$dkco` pero falta en `layers.conf`, el arranque **falla de forma visible** — por eso hay que registrarlo al crearlo.
- **Eliminar un servicio:** quitar/comentar su línea de `layers.conf` **antes o junto con** eliminar su carpeta de `$dkco`. Si borras solo el Compose y dejas la línea, el boot lo trata como faltante (salta con aviso si `BOOT_ORDER_ALLOW_MISSING=1`, o falla si es `0`).
- **Reordenar:** mover el servicio a otro bloque separado por una línea en blanco. Dentro de una capa (modo secuencial) el orden de las líneas es el orden de arranque.

### Detener un servicio a propósito sin romper el boot

Si paras un servicio deliberadamente y no quieres que el próximo reboot lo reviva ni que quede bloqueando su capa:

```bash
svc no-boot <svc>      # boot-order.sh lo salta con aviso (no bloquea, no falla)
svc stop <svc>         # (opcional) detenerlo ahora mismo
```

Para reactivarlo en el arranque:

```bash
svc boot-enable <svc>
svc up <svc>           # (opcional) levantarlo ahora
```

`svc no-boot` crea el marcador `$dkco/<svc>/.no-boot`; `boot-order.sh` lo detecta, registra `OMITIDO: <svc> tiene .no-boot` y **continúa con el siguiente servicio de la capa** sin esperar su healthcheck. Es la forma correcta de sacar un servicio del boot sin editar `layers.conf`.

- Arranque manual rápido (sin esperas de estabilización, útil cuando el sistema ya está caliente): `BOOT_ORDER_INITIAL_DELAY=0 BOOT_ORDER_SETTLE_DELAY=0 NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/boot-order.sh"`.
- Arranque manual como en el boot real (con pausas de estabilización): `NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/boot-order.sh"`.
- Arranque manual en paralelo dentro de capa: `BOOT_ORDER_SERIAL=0 NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/boot-order.sh"`.
- Log: `cat "$dkco/scripts/boot-order.log"`.
- Estado: `svc health`.
- Estado de systemd: `sudo systemctl status docker-boot-staged.service`.

No uses `systemctl restart docker` como sustituto del orquestador ni vuelvas a `unless-stopped` en los Compose que deban respetar este orden: esa policy devuelve el arranque al daemon Docker y puede recrear el pico de I/O durante el boot.
