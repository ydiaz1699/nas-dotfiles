# AGENTS.md — nas-dotfiles

Framework de administración para NAS Dell PowerEdge T20 (Debian 13 + Docker).
Tres capas: Shell personalizado, CLI Docker (`svc`), Agente IA Python.

## Entorno

- **IP:** 192.168.1.200
- **Hostname:** `Nas` (acceso: `ssh aadm@Nas.local` via avahi/mDNS)
- **OS:** Debian 13 Trixie, kernel 6.12
- **Shell:** Bash 5.x + framework nas-dotfiles
- **Docker:** Engine + Compose v2
- **Python:** 3.11+

## Rutas obligatorias (NUNCA hardcodear)

| Variable | Ruta | Atajo |
|----------|------|-------|
| `$NAS_DOTFILES` | `/nas-dotfiles` | `nasfk` |
| `$dkco` | `/docker` | `dk` |
| `$aadm` | `/home/aadm` | `adm` |

## Comandos — SIEMPRE usar aliases

### Shell aliases

```
dk <svc>            →  cd /docker/<svc>
adm                 →  cd /home/aadm
nasfk               →  cd /nas-dotfiles
instal <pkg>        →  apt install
pipins <pkg>        →  pip install
gpl                 →  git pull
gs                  →  git status
ga                  →  git add
gc "msg"            →  git commit -m
gp                  →  git push
git-quick "msg"     →  add -A + commit + push
bat <file>          →  cat con colores (batcat)
nas                 →  dashboard del servidor
```

### `svc` — Comandos globales (sin servicio)

| Comando | Acción |
|---------|--------|
| `svc lista` | Servicios con estado ●/○ |
| `svc health` | Tabla: estado, uptime, restarts |
| `svc doctor` | Chequeo 8 puntos: disco, memoria, servicios, puertos, restarts, storage, secretos, permisos .env |
| `svc doctor-history` | Historial con tendencia (mem%, disk%, errores) |
| `svc update-all` | Pull + recrear todos |
| `svc backup-all` | Backup de todos los servicios en secuencia + resumen + ntfy |
| `svc port-map` | Mapa global de puertos |
| `svc size` | Disco por servicio |
| `svc net` | Redes Docker con contenedores |
| `svc watch` | Monitoreo continuo (5s refresh) |
| `svc create <nombre>` | Scaffolding nuevo servicio |
| `svc clone <origen> <nuevo>` | Duplicar servicio (compose + .env sanitizado) |
| `svc menu` | TUI interactivo (fzf) |
| `svc diff <svc>` | Compose disco vs resuelta |
| `svc logs-grep <patrón>` | Buscar en logs de todos los servicios |
| `svc cron` | Helper para agendar backups/updates via crontab (add/list/remove) |
| `svc lock <svc>` | Proteger servicio (doble confirmación para stop/down/kill/restore) |
| `svc unlock <svc>` | Quitar protección |
| `svc catalog-sync [svc]` | Generar docs en cascada (ficha, guía, script DebMenux) |
| `svc scan` | Detectar lagunas del proyecto (servicios, CLI, docs) |

### `svc` — Comandos con servicio

| Comando | Acción |
|---------|--------|
| `svc up <svc>` | Crear e iniciar (detached) |
| `svc down <svc>` | Detener y eliminar |
| `svc restart <svc>` | Reiniciar |
| `svc start/stop/kill <svc>` | Control básico |
| `svc update <svc>` | Pull + recrear |
| `svc recreate <svc>` | Recrear sin pull (force-recreate) |
| `svc logs <svc>` | Follow, tail 200 |
| `svc ps <svc>` | Contenedores |
| `svc stats <svc>` | CPU/RAM en vivo |
| `svc top <svc>` | Procesos internos |
| `svc exec <svc> <cmd>` | Ejecutar en contenedor |
| `svc backup <svc>` | Volúmenes → tar.gz (rotación: 5, verificación tar -tzf) |
| `svc restore <svc>` | Restaurar (fzf + confirmación) |
| `svc depends <svc>` | Ver dependencias |
| `svc open <svc>` | Abrir URL (auto-detecta puerto) |
| `svc env <svc>` | Ver/editar variables |
| `svc config <svc>` | Configuración resuelta |

## Servicios Docker activos

| Servicio | Puerto | Red | Homepage |
|----------|--------|-----|----------|
| adguard | 53, 80 (IP: 192.168.1.201) | adguard_macvlan_NET | ✅ labels |
| emqx | 1883, 8883, 8083, 8084, 18083 | iot_net, db_net | ✅ labels |
| esphome | 6052 | host | ✅ labels |
| datasql | 5050 (pgadmin) | db_net | ✅ labels (pgadmin) |
| filebrowser | 8085 | filebrowser_default | ✅ labels |
| homepage | 3000 | homepage_net | — (es el dashboard) |
| ntfy | 8090 | homepage_net | ✅ labels |
| node-red | 1880 | iot_net | ✅ labels |
| usb-api (systemd) | 8091 | nativo | services.yaml |
| spacedrive | — | spacedrive_default | — |

## Redes Docker

| Red | Uso | Regla |
|-----|-----|-------|
| `db_net` | Apps ↔ DBs (postgres, pgadmin, redis) | Nunca exponer puertos DB al host |
| `iot_net` | IoT (EMQX, ESPHome, HA futuro) | Todo IoT aquí |
| `homepage_net` | Homepage ↔ ntfy (widgets internos) | Para APIs internas |
| `adguard_macvlan_NET` | AdGuard IP propia (192.168.1.201) | Solo macvlan, parent: eno1 |
| `filebrowser_default` | File Browser | Creada por compose |
| `spacedrive_default` | Spacedrive | Creada por compose |

## Notificaciones

```bash
ntfy_send "topic" "título" "mensaje" "prioridad" "tags"
# Topics: usb, docker, backups, system, alarma, nas-alerts
# Librería: docker/cli/lib/notifications.sh
# NUNCA usar notify-send (headless, no hay GUI)
```

## Nuevo servicio (orden obligatorio)

1. `mkdir -p $dkco/<svc>/data`
2. Crear `compose.yml` + `.env`
3. `chmod 600 .env`
4. Agregar labels `homepage.*` en compose (auto-descubrimiento)
5. `dk <svc> && svc up <svc>`
6. `svc catalog-sync <svc>` — genera ficha, guía, script DebMenux

## Homepage

- Labels en compose.yml > services.yaml
- `services.yaml` solo para servicios nativos (systemd)
- Recrear contenedor para tomar labels nuevas: `svc recreate X`

## USB Automount

- Mount base: `/NAS/USB/`
- Formato: `/NAS/USB/<LABEL>` (con label) o `/NAS/USB/usb-<dev>` (sin label)
- API: `GET http://192.168.1.200:8091/usb/list`
- Desmontar: `POST http://192.168.1.200:8091/usb/unmount/<dev>`
- Mountpoint fantasma: `umount -l /NAS/USB/usb-X && rmdir /NAS/USB/usb-X`

## Testing / Verificación

```bash
svc health                 # Estado de todos los servicios
svc doctor                 # Chequeo de 8 puntos
svc doctor-history         # Tendencia histórica (mem%, disk%)
svc scan                   # Detectar lagunas (servicios, CLI, docs)
svc scan --verbose         # Detalle completo de cada verificación
svc catalog-sync           # Generar docs en cascada (ficha, guía, script DebMenux)
svc catalog-sync --status  # Qué servicios tienen/faltan docs
svc catalog-sync --dry-run # Previsualizar sin cambios
svc logs-grep <patrón>     # Buscar texto en logs de todos los servicios
svc diff <svc>             # Compose en disco vs resuelta (interpolada)
```

## Reglas estrictas

- **NUNCA** usar rutas hardcodeadas — siempre `$dkco`, `$NAS_DOTFILES`, `$aadm`
- **NUNCA** `docker compose` directo — siempre `svc`
- **NUNCA** `apt install` — siempre `instal`
- **NUNCA** `cd /path` — siempre `dk`, `adm`, `nasfk`
- **NUNCA** sugerir cambios a un servicio sin leer su guía primero:
  - `docs/services/<svc>-guide.md` (prioridad)
  - `agent/catalog/services/<svc>/ficha.md`
- **SIEMPRE** orden: mkdir → archivos → permisos → levantar
- **SIEMPRE** compose.yml (nunca docker-compose.yml)

## Documentación adicional

| Tema | Archivo |
|------|---------|
| Guía de servicio | `docs/services/<svc>-guide.md` |
| Ficha del catálogo | `agent/catalog/services/<svc>/ficha.md` |
| Manual del NAS (hardware, redes, puertos) | `docs/nas-manual.md` |
| Pipeline auto-docs (catalog-sync) | `docs/catalog-sync-pipeline.md` |
| Homepage (labels, widgets, config) | `docs/services/homepage-guide.md` |
| ntfy (topics, clientes, primer uso, PC) | `docs/services/ntfy-guide.md` |
| Troubleshooting | `docs/troubleshooting.md` |
| Skill completa (para LLMs) | `docker-nas/references/nas-context.md` |
| Comandos shell | `docker-nas/references/entorno.md` |
| Comandos svc | `docker-nas/references/svc.md` |
| Seguridad | `docker-nas/references/seguridad.md` |
| Diagnóstico | `docker-nas/references/diagnostic.md` |

## Pipeline auto-documentación

Al crear/modificar un `compose.yml`, ejecutar:

```bash
svc catalog-sync <svc>    # Genera: ficha, guía, .env.example, script DebMenux
svc catalog-sync --status # Ver qué servicios tienen/faltan docs
svc catalog-sync --dry-run # Previsualizar sin cambios
```

Tres puntos de entrada:
1. `svc catalog-sync` — manual en el NAS
2. `debmenu install X` — automático (register_to_catalog)
3. Hook Kiro — automático al guardar compose.yml
