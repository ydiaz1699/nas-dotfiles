# Arranque escalonado de contenedores Docker

Esta implementación evita que Docker arranque todos los Compose en paralelo al reiniciar el NAS. Los servicios se agrupan en capas en `$dkco/scripts/layers.conf`; dentro de una capa se arrancan en paralelo, pero la siguiente espera a que todos los contenedores estén `running` y, cuando tienen healthcheck, `healthy`.

## Diferencias importantes respecto al borrador original

- El código permanece en `$NAS_DOTFILES/shell/scripts`; `$dkco/scripts` contiene solo configuración, logs y lock runtime.
- El script invoca el CLI Bash real de `svc` y no trata `dk` como si fuese un ejecutor. `dk` solo cambia de directorio.
- `flowise-worker` no es una capa: es un servicio interno del Compose `flowise` y se levanta con ese proyecto.
- Un job one-shot como `lobehub-rustfs-init` puede terminar con código 0 sin bloquear el arranque; los servicios que terminan con error sí detienen las capas dependientes.
- El timeout de health por contenedor es 120 segundos por defecto. Un fallo aborta las capas siguientes para no iniciar consumidores contra una dependencia rota.
- La plantilla no conoce qué carpetas existen en el NAS real. `layers.conf` debe reflejar el resultado de `svc lista`; con `BOOT_ORDER_REQUIRE_ALL=1`, olvidar un Compose hace fallar el arranque de forma visible.

La política `on-failure:5` es intencional: Docker documenta que `on-failure` reinicia solo ante salida con error y no vuelve a arrancar un contenedor simplemente porque se reinició el daemon. Así, `docker-boot-staged.service` recupera el control del orden después de un reboot. Durante la operación normal, los fallos siguen teniendo hasta cinco reintentos automáticos. Fuente: [Docker — Start containers automatically](https://docs.docker.com/config/containers/start-containers-automatically/).

## Archivos

| Archivo | Propósito |
|---|---|
| `shell/scripts/boot-order.sh` | Orquestador por capas, health gates, timeout y lock |
| `shell/scripts/layers.conf.example` | Plantilla editable de capas |
| `shell/scripts/find-no-extends.sh` | Detecta Compose que no usan `extends` |
| `shell/scripts/apply-restart-policy.sh` | Migra contenedores existentes sin arrancarlos todos |
| `systemd/docker-boot-staged.service` | Unidad que ejecuta el orquestador en cada boot |
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

Primero crea la unidad en `/etc` y luego recarga/habilita:

```bash
sudo cp "$NAS_DOTFILES/systemd/docker-boot-staged.service" \
  /etc/systemd/system/docker-boot-staged.service
sudo systemctl daemon-reload
sudo systemctl enable docker-boot-staged.service
```

Para probar la unidad sin reiniciar:

```bash
sudo systemctl start docker-boot-staged.service
systemctl is-enabled docker-boot-staged.service
sudo systemctl status docker-boot-staged.service --no-pager
```

El servicio usa `RequiresMountsFor=/docker`, espera `network-online.target` y exige que todos los Compose descubiertos estén representados en `layers.conf`. Si el unit file se instala en una ruta distinta de `/nas-dotfiles`, no lo habilites hasta corregir `ExecStart` y `Environment`.

## Variables de entorno del arranque

| Variable | Default | Efecto |
|---|---|---|
| `BOOT_ORDER_CONFIG` | `$dkco/scripts/layers.conf` | Ruta del archivo de capas |
| `BOOT_ORDER_LOG` | `$dkco/scripts/boot-order.log` | Log del arranque |
| `BOOT_ORDER_HEALTH_TIMEOUT` | `120` | Segundos máximos de espera de readiness por contenedor |
| `BOOT_ORDER_DAEMON_TIMEOUT` | `60` | Segundos máximos de espera a que Docker responda |
| `BOOT_ORDER_REQUIRE_ALL` | `1` | Falla si un Compose de `$dkco` no está en `layers.conf` |
| `BOOT_ORDER_ALLOW_MISSING` | `0` | Con `1`, omite (en vez de fallar) servicios de `layers.conf` sin Compose |
| `BOOT_ORDER_SERIAL` | `0` | Con `1`, arranca los servicios de cada capa uno a uno esperando readiness entre ellos, en vez de en paralelo |

## Operación

- Agregar un servicio: añadir su nombre en la capa adecuada de `$dkco/scripts/layers.conf`.
- Quitar un servicio: eliminar/comentar su línea. Si el Compose sigue instalado y `BOOT_ORDER_REQUIRE_ALL=1`, el script lo considerará omitido; para retirarlo del boot hay que retirar también el Compose o mantener una decisión documentada de no arrancarlo.
- Reordenar: mover el servicio a otro bloque separado por una línea en blanco.
- Arranque manual: `NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/boot-order.sh"`.
- Arranque manual secuencial (menor pico de I/O): `BOOT_ORDER_SERIAL=1 NAS_CLI=bash "$NAS_DOTFILES/shell/scripts/boot-order.sh"`.
- Log: `cat "$dkco/scripts/boot-order.log"`.
- Estado: `svc health`.
- Estado de systemd: `sudo systemctl status docker-boot-staged.service`.

No uses `systemctl restart docker` como sustituto del orquestador ni vuelvas a `unless-stopped` en los Compose que deban respetar este orden: esa policy devuelve el arranque al daemon Docker y puede recrear el pico de I/O durante el boot.
