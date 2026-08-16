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

```
dk <svc>            →  cd /docker/<svc>
adm                 →  cd /home/aadm
nasfk               →  cd /nas-dotfiles
svc <cmd> <svc>     →  docker compose (up/down/logs/restart/update/backup)
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

## Servicios Docker activos

| Servicio | Puerto | Red |
|----------|--------|-----|
| adguard | 53, 80 (IP: 192.168.1.201) | macvlan |
| emqx | 1883, 18083 | iot_net, db_net |
| esphome | 6052 | host |
| datasql | 5050 (pgadmin) | db_net |
| filebrowser | 8085 | default |
| homepage | 3000 | homepage_net |
| ntfy | 8090 | homepage_net |
| usb-api (systemd) | 8091 | nativo |

## Redes Docker

| Red | Uso | Regla |
|-----|-----|-------|
| `db_net` | Apps ↔ DBs | Nunca exponer puertos DB al host |
| `iot_net` | IoT (EMQX, ESPHome, HA) | Todo IoT aquí |
| `homepage_net` | Homepage ↔ servicios | Para widgets internos |
| `adguard_macvlan_NET` | AdGuard IP propia | Solo macvlan |

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
svc health              # Estado de todos los servicios
svc doctor              # Chequeo de 6 puntos
svc catalog-sync --status  # Qué servicios tienen/faltan docs
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
| Manual del NAS | `docs/nas-manual.md` |
| Pipeline auto-docs | `docs/catalog-sync-pipeline.md` |
| Homepage | `docs/services/homepage-guide.md` |
| Troubleshooting | `docs/troubleshooting.md` |
| Skill completa | `docker-nas/references/nas-context.md` |
