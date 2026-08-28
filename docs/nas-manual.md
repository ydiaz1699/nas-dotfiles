# Manual del NAS — Especificaciones, Configuración e Infraestructura

> Documento de referencia sobre el equipo físico, ajustes del sistema operativo,
> redes Docker, almacenamiento y convenciones. Actualizar cada vez que se cambie
> hardware, se agreguen discos o se modifiquen redes.

---

## Índice

1. [Hardware](#hardware)
2. [Sistema operativo](#sistema-operativo)
3. [Almacenamiento](#almacenamiento)
4. [Red del host](#red-del-host)
5. [Redes Docker](#redes-docker)
6. [Estructura de directorios](#estructura-de-directorios)
7. [Variables globales](#variables-globales)
8. [Servicios activos](#servicios-activos)
9. [Puertos asignados](#puertos-asignados)
10. [USB Automount](#usb-automount)
11. [Notificaciones (ntfy)](#notificaciones-ntfy)
12. [Backups](#backups)
13. [Mantenimiento](#mantenimiento)
14. [Convenciones](#convenciones)

---

## Hardware

| Campo | Valor |
|-------|-------|
| **Modelo** | Dell PowerEdge T20 (tower server) |
| **CPU** | Intel (2 cores, 800–3000 MHz, escala al 51% en idle) |
| **RAM** | 8 GB DDR3 ECC (7.7 GiB usables) |
| **Disco sistema** | SSD 298 GB `/dev/sda1` (ext4, montado en `/`) |
| **Swap** | 7.9 GB `/dev/sda5` |
| **Disco datos** | _(no hay segundo disco actualmente — todo en sda1)_ |
| **Ethernet** | 1x Gigabit integrada (Broadcom) |
| **USB** | 4x USB 2.0 traseros, 2x USB 3.0 frontales |
| **Factor de forma** | Mini tower (silencioso, bajo consumo ~45W idle) |

### Notas del hardware

- El PowerEdge T20 soporta hasta 32 GB RAM ECC (4 slots DIMM DDR3)
- Tiene 4 bahías SATA internas (3.5") — se puede agregar HDD de datos en el futuro
- CPU probablemente Intel Xeon E3-1225 v3 o Pentium G3220 (verificar con `lscpu | grep "Model name"`)
- Disco al 8% de uso — amplio espacio disponible (~275 GB libres)

---

## Sistema operativo

| Campo | Valor |
|-------|-------|
| **Distro** | Debian 13 (Trixie) |
| **Kernel** | 6.12.101+deb13-amd64 |
| **Init** | systemd |
| **Shell** | Bash 5.x + nas-dotfiles framework |
| **Docker** | Docker Engine + Compose v2 |
| **Python** | 3.11+ |
| **Usuario admin** | `aadm` (uid 1000) |
| **Hostname** | `Nas` |

### Paquetes clave instalados

```
eza fzf bat lm-sensors qrencode curl jq
docker-ce docker-compose-plugin
python3 python3-pip
```

> Lista completa en `$NAS_DOTFILES/logs/packages.txt`

---

## Almacenamiento

| Punto de montaje | Dispositivo | Filesystem | Tamaño | Uso |
|------------------|-------------|------------|--------|-----|
| `/` | `/dev/sda1` | ext4 | 290 GB | Sistema + Docker + datos (8%) |
| `[SWAP]` | `/dev/sda5` | swap | 7.9 GB | Swap |
| `/NAS/USB` | (dinámico) | varios | varía | USBs automontados |

> **Nota:** Actualmente todo está en un solo disco SSD de 298 GB.
> Cuando se agregue un HDD de datos, montar en `/NAS` o `/mnt/datos` y
> actualizar esta tabla.

### Rutas importantes

```
/docker/          → $dkco — datos de servicios Docker (compose, volumes, .env)
/nas-dotfiles/    → $NAS_DOTFILES — código del framework (git repo)
/NAS/             → almacenamiento principal
/NAS/USB/         → punto base para USB automount
/NAS/Backups/     → backups de servicios Docker
```

---

## Red del host

| Interfaz | IP | Rol |
|----------|----|-----|
| `eth0` (o `eno1`) | 192.168.1.200/24 | LAN principal |
| `docker0` | 172.17.0.1/16 | Bridge Docker default |

> **Verificar:** Ejecutar `ip -br addr` para confirmar nombre exacto de interfaz y IP.

### Gateway y DNS

| Campo | Valor |
|-------|-------|
| Gateway | 192.168.1.1 (router) |
| DNS | AdGuard → 192.168.1.201 (macvlan) |

### Gestión de red

| Campo | Valor |
|-------|-------|
| Backend | systemd-networkd |
| Config file | `/etc/systemd/network/*.network` |

Para instalar o recuperar el DNS del host sin romper IPv6, Avahi, AdGuard o
Home Assistant, seguir [`docker-nas/references/networking.md`](../docker-nas/references/networking.md).

### Acceso remoto (SSH + mDNS)

| Campo | Valor |
|-------|-------|
| Servicio SSH | `sshd` (OpenSSH) |
| Puerto | 22 (default) |
| Descubrimiento | **avahi-daemon** (mDNS/DNS-SD) |
| Hostname mDNS | `Nas.local` |
| Conexión | `ssh aadm@Nas.local` |

**avahi-daemon** publica el hostname del NAS en la red local vía mDNS (protocolo Bonjour/Zeroconf).
Esto permite conectarse por nombre sin necesidad de recordar la IP:

```bash
# Desde cualquier equipo en la LAN
ssh aadm@Nas.local

# Equivalente a:
ssh aadm@192.168.1.200
```

**Requisitos en el cliente:**
- **Linux:** Instalar `avahi-utils` o `nss-mdns` (`apt install libnss-mdns`)
- **macOS:** Funciona nativamente (Bonjour integrado)
- **Windows:** Funciona nativamente desde Windows 10 (mDNS integrado)

**Gestión:**

```bash
# Estado del servicio
systemctl status avahi-daemon

# Reiniciar (si cambia hostname)
systemctl restart avahi-daemon

# Config
cat /etc/avahi/avahi-daemon.conf

# Ver qué publica
avahi-browse -a     # listar servicios publicados
avahi-resolve -n Nas.local   # resolver nombre → IP
```

**Archivo de config** (`/etc/avahi/avahi-daemon.conf`):
```ini
[server]
host-name=Nas
domain-name=local
use-ipv4=yes
use-ipv6=yes

[publish]
publish-addresses=yes
publish-hinfo=yes
publish-workstation=yes
```

---

## Redes Docker

Redes creadas manualmente para segmentación de servicios.

| Red | Driver | Propósito | Servicios conectados |
|-----|--------|-----------|---------------------|
| `adguard_macvlan_NET` | macvlan | IP dedicada para AdGuard (DNS:53 sin conflicto) | adguard |
| `db_net` | bridge | Comunicación interna entre apps y bases de datos | datasql (postgres, pgadmin, redis), flowise, n8n, lobehub (runtime confirmado) |
| `lobe_storage` | bridge | Red privada LobeHub ↔ RustFS S3 | lobehub, lobehub-rustfs, rustfs-init (runtime confirmado) |
| `iot_net` | bridge | Servicios IoT/domótica | emqx, esphome, homeassistant, ioBroker (preparado) |
| `bridge` | bridge | Default Docker (servicios sin red especial) | ntfy, filebrowser, etc. |
| `homepage_net` | bridge | Dashboard Homepage ↔ servicios internos | homepage, ntfy |
| `host` | host | Acceso directo al stack de red del host | (casos especiales) |
| `none` | null | Sin red (contenedores aislados) | — |
| `filebrowser_default` | bridge | Creada automáticamente por compose de filebrowser | filebrowser |
| `spacedrive_default` | bridge | Creada automáticamente por compose de spacedrive | spacedrive |

### Diagrama de redes

```
┌─ LAN (192.168.1.0/24) ─────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ macvlan ──────┐                                                      │
│  │ adguard        │  ← IP dedicada 192.168.1.201 (DNS sin conflicto)     │
│  │ (DNS:53)       │                                                      │
│  └────────────────┘                                                      │
│                                                                          │
│  ┌─ Host (192.168.1.200) ──────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌─ iot_net (172.x.x.0/16) ─┐  ┌─ db_net (172.y.y.0/16) ──┐  │    │
│  │  │ emqx (:1883,:18083)      │  │ postgres (interno)         │  │    │
│  │  │ esphome (:6052)          │  │ pgadmin (:5050)            │  │    │
│  │  │ homeassistant (:8123)    │  │ redis (interno)            │  │
│  │  │ iobroker (:8181, prep.)  │  │                              │  │    │
│  │  └──────────────────────────┘  └────────────────────────────┘  │    │
│  │                                                                  │    │
│  │  ┌─ bridge (default) ────────────────────────────────────────┐  │    │
│  │  │ ntfy (:8090)                                              │  │    │
│  │  │ filebrowser (:8085)                                       │  │    │
│  │  │ (otros servicios sin red especial)                        │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  │                                                                  │    │
│  │  ┌─ Nativo (systemd) ────────────────────────────────────────┐  │    │
│  │  │ usb-api (:8091)                                           │  │    │
│  │  └───────────────────────────────────────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Verificar redes compartidas

```bash
svc net
```

`lobe_storage` se crea automáticamente por el compose de LobeHub y no debe
recrearse manualmente; `db_net` es externa y compartida. Las redes externas
(`db_net`, `iot_net`, `homepage_net` y macvlan) se crean o recuperan siguiendo la sección [Redes Docker de `docs/docker-entorno.md`](docker-entorno.md#redes-docker),
que define el bootstrap inicial. Esa creación es una operación de instalación,
no una reparación normal: no eliminar `db_net` ni ejecutar `docker network prune`
durante la operación normal: otros servicios pueden depender de ella.

### Reglas de uso

- **db_net**: Solo para comunicación app↔DB. No publicar postgres/redis a la LAN; PostgreSQL puede usar únicamente `127.0.0.1:5432:5432` para Home Assistant con `network_mode: host`.
- **iot_net**: Todos los servicios IoT se conectan aquí para comunicarse entre sí vía MQTT, incluido ioBroker cuando se despliegue.
- **macvlan**: Solo para servicios que necesitan IP propia en la LAN (actualmente solo AdGuard para DNS:53).
- **bridge default**: Servicios que solo necesitan un puerto publicado y no hablan entre sí.

---

## Estructura de directorios

```
/docker/                          ← $dkco (datos de servicios)
├── .env                          ← Variables globales (SERVER_IP, TZ)
├── adguard/
│   └── compose.yml
├── datasql/
│   ├── compose.yml
│   ├── .env                      ← Secretos: POSTGRES_PASSWORD, etc.
│   └── data/
├── flowise/
│   ├── compose.yml
│   ├── .env                      ← Credenciales flowise_db y clave de cifrado
│   └── data/
├── lobehub/
│   ├── compose.yml
│   ├── .env                      ← Secretos LobeHub/RustFS/Redis
│   ├── bucket.config.json
│   └── data/rustfs/              ← Objetos S3 de LobeHub
├── emqx/
│   ├── compose.yml
│   ├── .env
│   └── data/
├── esphome/
│   ├── compose.yml
│   ├── .env
│   └── config/
├── filebrowser/
│   ├── compose.yml
│   └── config/
├── ntfy/
│   ├── compose.yml
│   ├── .env
│   ├── config/server.yml
│   └── data/
├── iobroker/
│   ├── compose.yml
│   ├── .env
│   └── data/                    ← /opt/iobroker
├── spacedrive/
│   └── compose.yml
└── backups/                      ← Backups de svc backup
```

---

## Variables globales

Archivo: `$dkco/.env` (heredado por todos los servicios via `env_file: [../.env, .env]`)

```env
SERVER_IP=192.168.1.200
TZ=America/La_Paz
```

Variables del sistema (en `/etc/environment` o shell):

```env
NTFY_URL=http://192.168.1.200:8090
NAS_DOTFILES=/nas-dotfiles
DOCKER_BASE=/docker
```

---

## Servicios activos

> Actualizar cuando se agreguen/quiten servicios. Usar `svc lista` para ver estado real.

| Servicio | Tipo | Puerto(s) | Red | Descripción |
|----------|------|-----------|-----|-------------|
| **adguard** | Docker (macvlan) | 53, 3000, 80 | adguard_macvlan_NET | DNS + bloqueador ads |
| **emqx** | Docker | 1883, 8883, 8083, 8084, 18083 | iot_net | Broker MQTT IoT |
| **esphome** | Docker | 6052 | iot_net | Firmware ESP32/ESP8266 |
| **homeassistant** | Docker (host) | 8123 | host | Automatización del hogar |
| **datasql** | Docker (multi) | 5050 (pgAdmin), 5432 (solo loopback) | db_net | PostgreSQL + pgAdmin + Redis |
| **lobehub** | Docker | 3210 (LobeHub), 9000 (RustFS S3), 9001 (solo loopback) | db_net + lobe_storage | Chat/agentes IA con PostgreSQL, Redis y S3; runtime base confirmado |
| **filebrowser** | Docker | 8085 | filebrowser_default | Explorador archivos web |
| **homepage** | Docker | 3000 | homepage_net | Dashboard de servicios |
| **ntfy** | Docker | 8090 | bridge + homepage_net | Notificaciones push |
| **iobroker** | Docker (preparado) | 8181 | iot_net | Automatización IoT y domótica |
| **spacedrive** | Docker | _(ver compose)_ | spacedrive_default | Gestor de archivos |
| **usb-api** | Nativo (systemd) | 8091 | — | API REST para USBs |

> **12 contenedores corriendo** según el prompt (`12↑`)

---

## Puertos asignados

| Puerto | Servicio | Protocolo | Notas |
|--------|----------|-----------|-------|
| 53 | AdGuard | TCP/UDP | DNS (via macvlan, IP dedicada) |
| 80 | AdGuard | TCP | Panel admin (después de setup) |
| 1883 | EMQX | TCP | MQTT sin TLS |
| 3000 | AdGuard | TCP | Asistente primer arranque |
| 3000 | Homepage | TCP | Dashboard de servicios |
| 3210 | LobeHub | TCP | Dashboard web en LAN; runtime base confirmado |
| 5050 | pgAdmin | TCP | Acceso desde la LAN (`5050:80`) |
| 5432 | PostgreSQL | TCP | Solo loopback del NAS (`127.0.0.1:5432:5432`) para Home Assistant |
| 6052 | ESPHome | TCP | Dashboard ESPHome |
| 8083 | EMQX | TCP | WebSocket MQTT |
| 8084 | EMQX | TCP | WebSocket MQTT seguro |
| 8085 | File Browser | TCP | Explorador archivos web |
| 8090 | ntfy | TCP | Notificaciones push |
| 8091 | usb-api | TCP | API REST USB (nativo) |
| 8100 | Flowise (prueba pendiente) | TCP | Reservado para la prueba; no confirmado activo |
| 8123 | Home Assistant | TCP | Automatización del hogar |
| 8181 | ioBroker (preparado) | TCP | Panel web, pendiente de despliegue y verificación en NAS |
| 8883 | EMQX | TCP | MQTT con TLS |
| 9000 | RustFS de LobeHub | TCP | Endpoint S3 en LAN; necesario para uploads/imágenes/knowledge base; runtime confirmado |
| 9001 | RustFS de LobeHub | TCP | Consola solo en loopback del NAS; runtime confirmado |
| 18083 | EMQX | TCP | Dashboard EMQX |

### Rangos reservados

| Rango | Uso |
|-------|-----|
| 22 | SSH (no tocar) |
| 53 | DNS (AdGuard macvlan) |
| 80, 443 | Reservados para reverse proxy futuro |
| 1883-1884 | MQTT |
| 3000-3999 | Dashboards de setup |
| 5000-5999 | Bases de datos internas |
| 6000-6999 | IoT |
| 8000-8999 | Aplicaciones web |
| 18000-18999 | Dashboards admin |

---

## USB Automount

Sistema automático de montaje de USBs gestionado por udev + systemd.

| Campo | Valor |
|-------|-------|
| Script | `/usr/local/bin/usb-automount.sh` |
| Config | `/etc/usb-automount.conf` |
| Mount base | `/NAS/USB/` |
| Formato mount | `/NAS/USB/usb-<dispositivo>` (ej: `/NAS/USB/usb-sdb1`) |
| Regla udev | `/etc/udev/rules.d/99-usb-automount.rules` |
| Servicio | `usb-automount@.service` |
| Limpieza | `usb-automount-cleanup.timer` (cada hora) |
| Notificaciones | ntfy topic `usb` (via `ntfy_send`) |
| Log | `/var/log/usb-automount.log` |

### Config activa (`/etc/usb-automount.conf`)

```bash
MOUNT_BASE="/NAS/USB"
MIN_SIZE_MB=100
LOG_LEVEL="INFO"
ENABLE_NOTIFICATIONS="true"
NTFY_URL="http://192.168.1.200:8090"
MOUNT_OPTIONS="noexec,nosuid,nodev"
```

### Comandos útiles

```bash
usb-automount.sh --status     # Ver USBs montados
usb-automount.sh --list       # Solo nombres (para scripts)
usb-automount.sh --cleanup    # Limpiar mountpoints huérfanos
usb-automount.sh --export     # Exportar config
```

---

## Notificaciones (ntfy)

| Campo | Valor |
|-------|-------|
| URL | `http://192.168.1.200:8090` |
| Puerto | 8090 |
| Config | `$dkco/ntfy/config/server.yml` |
| Auth | Abierto (LAN only) |
| Cache | 24h (mensajes temporales) |
| Attachments | 1GB total, 10MB por archivo, expiran 24h |

### Topics

| Topic | Fuente | Uso |
|-------|--------|-----|
| `usb` | usb-automount | Mount/unmount/unsafe disconnect |
| `docker` | svc / agente | Servicio caído, actualización |
| `backups` | cron / svc backup | Completado/fallido |
| `system` | SMART / SSH | Fallo disco, login sospechoso |
| `alarma` | Home Assistant | Movimiento + snapshot cámara |
| `nas-alerts` | catch-all | Alertas generales |

### Cómo usar desde scripts

```bash
source $dkco/cli/lib/notifications.sh
ntfy_send "topic" "Título" "Mensaje" "prioridad" "tags"
```

---

## Backups

| Campo | Valor |
|-------|-------|
| Directorio | `/NAS/Backups/` o `$dkco/backups/` |
| Herramienta | `svc backup <servicio>` |
| Formato | `<servicio>_<volumen>_YYYYMMDD_HHMMSS.tar.gz` |
| Notificación | ntfy topic `backups` |

### Servicios con backup crítico

| Servicio | Qué respaldar | Frecuencia |
|----------|---------------|------------|
| datasql | PostgreSQL (pg_dump) | Diario (cron) |
| emqx | `data/data/` (sesiones, reglas, ACL) | Semanal |
| ntfy | `data/lib/` (usuarios, si auth habilitada) | Solo si auth activa |

---

## Mantenimiento

### Tareas periódicas

| Tarea | Frecuencia | Comando |
|-------|------------|---------|
| Actualizar servicios | Semanal | `svc update-all` |
| Verificar salud | Diario | `svc health` / `svc doctor` |
| Limpiar Docker | Solo tras revisar | `svc doctor` y limpieza específica; no usar `docker system prune` automáticamente |
| Backups BD | Diario (cron) | `svc backup datasql` |
| Limpiar USBs huérfanos | Automático (timer) | `usb-automount-cleanup.timer` |
| Revisar logs | Según alertas | `svc logs <svc>` / `journalctl` |
| Actualizar framework | Cuando haya cambios | `nasfk` → `gs` → `gpl` → recargar shell si cambió la configuración |

#### Aplicar cambios publicados desde GitHub en el NAS

Kiro no opera el NAS. Para desplegar en el NAS cambios ya fusionados en
GitHub, hacerlo desde una sesión SSH y actualizar primero el checkout del
framework:

```bash
nasfk
gs
```

Si `gs` muestra archivos modificados localmente, detenerse y decidir qué hacer
con ellos; no sobrescribirlos automáticamente. Esta receta asume que el
checkout sigue la rama `main`; si `gs` muestra otra rama, detenerse antes de
hacer `gpl`. Cuando el árbol esté limpio:

```bash
gpl
```

Después verificar que el checkout contiene el comando o la guía esperada y
recargar el shell solo si se modificaron aliases o módulos de carga:

```bash
gs
_SHELL_RELOAD=1 source ~/.bashrc
```

Para el fix de `svc snapshot`, la secuencia de transición es:

```bash
NAS_CLI=bash svc snapshot datasql
# actualizar el checkout si todavía no contiene el fix
gpl
NAS_CLI=bash svc --help | grep -E 'snapshot|rollback'
NAS_CLI=python svc --help | grep snapshot
svc snapshot datasql
```

Si el CLI Python todavía muestra `No such command 'snapshot'`, conservar el
workaround `NAS_CLI=bash svc snapshot datasql`; no cambiar puertos ni ejecutar
operaciones Docker directas para resolver ese error de CLI. La guía de DataSQL
documenta además el snapshot previo y la migración segura de `db_net`.

---

## Monitoreo rápido

```bash
nas             # Dashboard completo (uptime, RAM, disco, Docker, temp)
svc health      # Estado de todos los servicios
svc doctor      # Chequeo de 8 puntos
disk            # Uso de disco
netinfo         # Interfaces + puertos en uso
svc port-map    # Mapa de puertos (detecta conflictos)
```

---

## Convenciones

### Nombres

- Servicios Docker: `^[a-z0-9][a-z0-9._-]{0,63}$`
- Archivos compose: `compose.yml` (nunca `docker-compose.yml`)
- Variables .env: `MAYUSCULAS_CON_UNDERSCORE`
- Carpetas de datos: `$dkco/<servicio>/data/`

### Redes

- Crear red personalizada SOLO si dos servicios necesitan hablar internamente
- No publicar puertos de bases de datos a la LAN (usar red interna); si Home Assistant conserva `network_mode: host`, PostgreSQL puede usar únicamente `127.0.0.1:5432:5432` y debe documentarse como excepción
- Dashboard admin en LAN (no localhost) = documentar excepción en ficha

### Seguridad

- `.env` con secretos siempre `chmod 600`
- `security_opt: [no-new-privileges:true]` en todos los compose
- `cap_drop: [ALL]` + agregar solo las necesarias
- Nunca `privileged: true` (la única excepción legítima sería Home Assistant)
- USBs montan con `noexec,nosuid,nodev`

### Orden de operaciones (para nuevos servicios)

1. `mkdir -p $dkco/<svc>/{data,config}` — crear carpetas
2. Crear `compose.yml`, `.env`, configs — crear archivos
3. `chmod 600 .env` — aplicar permisos
4. Verificar redes externas con `svc net` y seguir el procedimiento de bootstrap si falta alguna
5. `svc up <svc>` — levantar

### Documentación

- Guía operativa → `docs/services/<svc>-guide.md`
- Ficha del catálogo → `agent/catalog/services/<svc>/ficha.md`
- Compose final → `agent/catalog/services/<svc>/compose.yml`
- Las tres capas no se duplican entre sí

---

## Historial de cambios del hardware

| Fecha | Cambio | Notas |
|-------|--------|-------|
| _(original)_ | Instalación inicial | Dell PowerEdge T20, Debian 13, Docker, nas-dotfiles |
| _(pendiente)_ | Agregar HDD de datos | Hay 3 bahías SATA libres para futuro |

---

## Cómo actualizar este documento

```bash
# Verificación operativa mediante las interfaces del NAS
svc net
svc lista
svc port-map
```

Copiar la salida y actualizar las secciones marcadas con `_completar_`.
