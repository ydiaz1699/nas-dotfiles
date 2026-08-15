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

> **⚠️ COMPLETAR** con los datos reales del equipo. Ejecutar en el NAS:
> ```bash
> cat /proc/cpuinfo | head -20
> free -h
> lsblk
> lspci | grep -i 'ethernet\|network\|sata\|usb'
> cat /sys/class/dmi/id/product_name 2>/dev/null
> ```

| Campo | Valor |
|-------|-------|
| **Modelo/Marca** | _completar_ (ej: mini PC Beelink, Lenovo ThinkCentre M720q) |
| **CPU** | _completar_ (ej: Intel Celeron N5095 @ 2.9GHz, 4 cores) |
| **RAM** | _completar_ (ej: 8GB DDR4) |
| **Disco sistema** | _completar_ (ej: SSD NVMe 256GB /dev/nvme0n1) |
| **Disco datos** | _completar_ (ej: HDD 4TB /dev/sda1 → /mnt/datos) |
| **Ethernet** | _completar_ (ej: Intel I225-V 2.5GbE) |
| **USB** | _completar_ (ej: 4x USB 3.0, 2x USB-C) |
| **Consumo** | _completar_ (ej: ~15W idle) |

---

## Sistema operativo

| Campo | Valor |
|-------|-------|
| **Distro** | Debian 12 (Bookworm) |
| **Kernel** | _completar_ (`uname -r`) |
| **Init** | systemd |
| **Shell** | Bash 5.x + nas-dotfiles framework |
| **Docker** | Docker Engine + Compose v2 |
| **Python** | 3.11+ |
| **Usuario admin** | `aadm` (uid 1000) |

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
| `/` | _completar_ | ext4 | _completar_ | Sistema + Docker |
| `/NAS` | _completar_ | _completar_ | _completar_ | Datos: media, backups, compartidos |
| `/NAS/USB` | (dinámico) | varios | varía | USBs automontados |

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
| _completar_ (ej: `eth0`, `enp1s0`) | 192.168.0.200/24 | LAN principal |
| `docker0` | 172.17.0.1/16 | Bridge Docker default |

### Gateway y DNS

| Campo | Valor |
|-------|-------|
| Gateway | _completar_ (ej: 192.168.0.1) |
| DNS | _completar_ (ej: AdGuard → 192.168.0.53 o router) |

### Gestión de red

| Campo | Valor |
|-------|-------|
| Backend | _completar_ (`systemd-networkd` / `ifupdown` / `NetworkManager`) |
| Config file | _completar_ (ej: `/etc/systemd/network/10-eth.network`) |

---

## Redes Docker

Redes creadas manualmente para segmentación de servicios.

| Red | Driver | Propósito | Servicios conectados |
|-----|--------|-----------|---------------------|
| `adguard_macvlan_NET` | macvlan | IP dedicada para AdGuard (DNS:53 sin conflicto) | adguard |
| `db_net` | bridge | Comunicación interna entre apps y bases de datos | datasql (postgres, pgadmin, redis) |
| `iot_net` | bridge | Servicios IoT/domótica | emqx, esphome, (home-assistant futuro) |
| `bridge` | bridge | Default Docker (servicios sin red especial) | ntfy, filebrowser, etc. |
| `host` | host | Acceso directo al stack de red del host | (casos especiales) |
| `none` | null | Sin red (contenedores aislados) | — |
| `filebrowser_default` | bridge | Creada automáticamente por compose de filebrowser | filebrowser |
| `spacedrive_default` | bridge | Creada automáticamente por compose de spacedrive | spacedrive |

### Diagrama de redes

```
┌─ LAN (192.168.0.0/24) ─────────────────────────────────────────────────┐
│                                                                          │
│  ┌─ macvlan ──────┐                                                      │
│  │ adguard        │  ← IP dedicada 192.168.0.53 (DNS sin conflicto)     │
│  │ (DNS:53)       │                                                      │
│  └────────────────┘                                                      │
│                                                                          │
│  ┌─ Host (192.168.0.200) ──────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  ┌─ iot_net (172.x.x.0/16) ─┐  ┌─ db_net (172.y.y.0/16) ──┐  │    │
│  │  │ emqx (:1883,:18083)      │  │ postgres (interno)         │  │    │
│  │  │ esphome (:6052)          │  │ pgadmin (:5050)            │  │    │
│  │  │ (home-assistant futuro)  │  │ redis (interno)            │  │    │
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

### Crear redes (si se reinstala Docker)

```bash
docker network create db_net
docker network create iot_net
# macvlan requiere config especial — ver docs/services/adguard-guide.md
```

### Reglas de uso

- **db_net**: Solo para comunicación app↔DB. Nunca publicar puertos de postgres/redis al host.
- **iot_net**: Todos los servicios IoT se conectan aquí para comunicarse entre sí vía MQTT.
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
├── spacedrive/
│   └── compose.yml
└── backups/                      ← Backups de svc backup
```

---

## Variables globales

Archivo: `$dkco/.env` (heredado por todos los servicios via `env_file: [../.env, .env]`)

```env
SERVER_IP=192.168.0.200
TZ=America/La_Paz
```

Variables del sistema (en `/etc/environment` o shell):

```env
NTFY_URL=http://192.168.0.200:8090
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
| **datasql** | Docker (multi) | 5050 (pgadmin) | db_net | PostgreSQL + pgAdmin + Redis |
| **filebrowser** | Docker | 8085 | bridge | Explorador archivos web |
| **ntfy** | Docker | 8090 | bridge | Notificaciones push |
| **spacedrive** | Docker | _completar_ | bridge | Gestor de archivos (Spacedrive) |
| **usb-api** | Nativo (systemd) | 8091 | — | API REST para USBs |

---

## Puertos asignados

| Puerto | Servicio | Protocolo | Notas |
|--------|----------|-----------|-------|
| 53 | AdGuard | TCP/UDP | DNS (via macvlan, IP dedicada) |
| 80 | AdGuard | TCP | Panel admin (después de setup) |
| 1883 | EMQX | TCP | MQTT sin TLS |
| 3000 | AdGuard | TCP | Asistente primer arranque |
| 5050 | pgAdmin | TCP | Solo vía db_net |
| 6052 | ESPHome | TCP | Dashboard ESPHome |
| 8083 | EMQX | TCP | WebSocket MQTT |
| 8084 | EMQX | TCP | WebSocket MQTT seguro |
| 8085 | File Browser | TCP | Explorador archivos web |
| 8090 | ntfy | TCP | Notificaciones push |
| 8091 | usb-api | TCP | API REST USB (nativo) |
| 8883 | EMQX | TCP | MQTT con TLS |
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
NTFY_URL="http://192.168.0.200:8090"
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
| URL | `http://192.168.0.200:8090` |
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
| Limpiar Docker | Mensual | `docker system prune -a --volumes` |
| Backups BD | Diario (cron) | `svc backup datasql` |
| Limpiar USBs huérfanos | Automático (timer) | `usb-automount-cleanup.timer` |
| Revisar logs | Según alertas | `svc logs <svc>` / `journalctl` |
| Actualizar framework | Cuando haya cambios | `cd $NAS_DOTFILES && git pull && source ~/.bashrc` |

### Monitoreo rápido

```bash
nas             # Dashboard completo (uptime, RAM, disco, Docker, temp)
svc health      # Estado de todos los servicios
svc doctor      # Chequeo de 6 puntos
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
- Nunca publicar puertos de bases de datos al host (usar red interna)
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
4. `docker network create <red>` — crear red si necesaria
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
| _completar_ | Instalación inicial | Debian 12, Docker, nas-dotfiles |
| _completar_ | Disco datos agregado | _modelo y capacidad_ |
| _completar_ | RAM ampliada | _de X a Y GB_ |

---

## Cómo actualizar este documento

```bash
# Regenerar info automática
echo "=== Hardware ===" && lscpu | head -5 && free -h && lsblk
echo "=== Red ===" && ip -br addr && ip route | head -3
echo "=== Docker ===" && docker network ls && docker ps --format "table {{.Names}}\t{{.Ports}}"
echo "=== Puertos ===" && svc port-map
```

Copiar la salida y actualizar las secciones marcadas con `_completar_`.
