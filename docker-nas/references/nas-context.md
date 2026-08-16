# NAS Context — Hechos Operativos para LLMs

> **Auto-generado por `svc catalog-sync`.** No editar manualmente.
> Última actualización: 2026-08-15

---

## Hardware

| Campo | Valor |
|-------|-------|
| Equipo | Dell PowerEdge T20 |
| CPU | Intel 2 cores @ 3 GHz |
| RAM | 8 GB DDR3 ECC |
| Disco | SSD 298 GB ext4 (8% usado) |
| OS | Debian 13 Trixie, kernel 6.12 |
| Hostname | `Nas` |
| IP | 192.168.1.200 |

---

## Rutas (NUNCA hardcodear, usar variables)

| Variable | Ruta | Comando rápido |
|----------|------|----------------|
| `$NAS_DOTFILES` | `/nas-dotfiles` | `nasfk` |
| `$dkco` | `/docker` | `dk` (sin args) |
| `$aadm` | `/home/aadm` | `adm` |

---

## Aliases obligatorios (NUNCA usar el comando largo)

| Alias | Equivale a | Contexto |
|-------|-----------|----------|
| `dk <svc>` | `cd /docker/<svc>` | Navegar a servicio |
| `adm` | `cd /home/aadm` | Ir a home |
| `nasfk` | `cd /nas-dotfiles` | Ir al código |
| `svc <cmd> <svc>` | `docker compose ...` | Operar Docker |
| `instal <pkg>` | `apt install` | Paquetes APT |
| `pipins <pkg>` | `pip install` | Paquetes Python |
| `gpl` | `git pull` | Pull |
| `gs` | `git status` | Status |
| `ga` | `git add` | Stage |
| `gc "msg"` | `git commit -m` | Commit |
| `gp` | `git push` | Push |
| `git-quick "msg"` | `add -A && commit && push` | Todo en uno |
| `nas` | Dashboard del servidor | Monitor |
| `disk` | Uso de disco | Info |
| `bat <file>` | `batcat` con colores | Ver archivo |

---

## Servicios activos

| Servicio | Puerto | Red | Tipo | Homepage |
|----------|--------|-----|------|----------|
| adguard | 53,80 (IP: 192.168.1.201) | adguard_macvlan_NET | Docker | ✅ labels |
| emqx | 1883,18083 | iot_net, db_net | Docker | ✅ labels |
| esphome | 6052 | host | Docker | ✅ labels |
| datasql | 5050 (pgadmin) | db_net | Docker | ✅ labels |
| filebrowser | 8085 | filebrowser_default | Docker | ✅ labels |
| homepage | 3000 | homepage_net | Docker | — |
| ntfy | 8090 | homepage_net | Docker | ✅ labels |
| usb-api | 8091 | — | systemd nativo | services.yaml |

---

## Redes Docker

| Red | Driver | Uso |
|-----|--------|-----|
| `adguard_macvlan_NET` | macvlan | AdGuard con IP propia (DNS:53) |
| `db_net` | bridge | PostgreSQL ↔ pgAdmin ↔ apps (interno) |
| `iot_net` | bridge | EMQX ↔ ESPHome ↔ HA (IoT) |
| `homepage_net` | bridge | Homepage ↔ ntfy (widgets internos) |

**Reglas:** DBs nunca exponen puerto al host. IoT va a iot_net. Homepage labels > services.yaml.

---

## Notificaciones (ntfy)

| Campo | Valor |
|-------|-------|
| URL | `http://192.168.1.200:8090` |
| Función | `ntfy_send "topic" "título" "mensaje" "prioridad" "tags"` |
| Librería | `docker/cli/lib/notifications.sh` |
| Topics | `usb`, `docker`, `backups`, `system`, `alarma`, `nas-alerts` |

---

## USB Automount

| Campo | Valor |
|-------|-------|
| Mount base | `/NAS/USB/` |
| Formato | `/NAS/USB/<LABEL>` (con label) o `/NAS/USB/usb-<dev>` (sin label) |
| Script | `/usr/local/bin/usb-automount.sh` |
| Notifica | ntfy topic `usb` |
| API | `http://192.168.1.200:8091/usb/list` |

---

## Acceso remoto

| Método | Comando |
|--------|---------|
| SSH por nombre | `ssh aadm@Nas.local` (avahi-daemon/mDNS) |
| SSH por IP | `ssh aadm@192.168.1.200` |

---

## Pipeline auto-docs (`svc catalog-sync`)

Al crear/modificar un compose.yml se genera automáticamente:
- `agent/catalog/services/<svc>/ficha.md` (metadatos)
- `agent/catalog/services/<svc>/compose.yml` (copia)
- `agent/catalog/services/<svc>/.env.example` (sanitizado)
- `docs/services/<svc>-guide.md` (placeholder)
- Script DebMenux si no existe
- Notificación ntfy

---

## Dónde buscar más info

| Necesitas | Consultar |
|-----------|-----------|
| Guía completa de un servicio | `docs/services/<svc>-guide.md` |
| Metadatos/puertos/redes | `agent/catalog/services/<svc>/ficha.md` |
| Compose real | `agent/catalog/services/<svc>/compose.yml` |
| Variables de entorno | `agent/catalog/services/<svc>/.env.example` |
| Troubleshooting | `docs/troubleshooting.md` |
| Pipeline de docs | `docs/catalog-sync-pipeline.md` |
| Manual del NAS | `docs/nas-manual.md` |
| Homepage config | `docs/services/homepage-guide.md` |
| Comandos shell | `docker-nas/references/entorno.md` |
| Comandos svc | `docker-nas/references/svc.md` |

---

## Reglas estrictas para el LLM

```
NUNCA:                              SIEMPRE:
  cd /docker/X                  →   dk X
  cd /nas-dotfiles              →   nasfk
  cd /home/aadm                 →   adm
  git pull                      →   gpl
  git status                    →   gs
  apt install                   →   instal
  docker compose up             →   svc up X
  docker compose logs           →   svc logs X
  docker restart X              →   svc restart X
  pip install                   →   pipins
  cat archivo                   →   bat archivo
  /path/to/...                  →   preguntar o deducir del contexto
  docker-compose.yml            →   compose.yml
  notify-send                   →   ntfy_send (headless, no hay GUI)
```

---

## Nuevo servicio (orden obligatorio)

1. `mkdir -p $dkco/<svc>/data`
2. Crear `compose.yml` + `.env`
3. `chmod 600 $dkco/<svc>/.env`
4. Agregar labels `homepage.*` en compose
5. `dk <svc> && svc up <svc>`
6. `svc catalog-sync <svc>` → genera toda la documentación
