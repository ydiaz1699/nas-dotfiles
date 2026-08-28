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
| `svc capabilities [consulta]` | Descubrir capacidades reales desde manifests e índice dinámico |
| `svc lobehub <acción>` | Preflight, verify, proveedores, DB, RustFS y backup lógico |
| `svc scan` | Detectar lagunas del proyecto (servicios, CLI, docs) |
| `svc snapshot <svc>` | Guardar compose+.env antes de cambios (liviano, rotación 10) |
| `svc rollback <svc>` | Restaurar config desde snapshot anterior (fzf + confirmación) |

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

`svc snapshot` se registra en el CLI Python actual y delega a la implementación
Bash mediante `bash_bridge.py`; `rollback` sigue siendo Bash-only. Si el NAS
todavía ejecuta un checkout anterior y aparece `No such command 'snapshot'`, usar
`NAS_CLI=bash svc snapshot <svc>` hasta actualizarlo con `nasfk` + `gpl`.

## Servicios Docker activos o preparados

| Servicio | Puerto | Red | Homepage |
|----------|--------|-----|----------|
| adguard | 53, 80 (IP: 192.168.1.201) | adguard_macvlan_NET | ✅ labels |
| emqx | 1883, 8883, 8083, 8084, 18083 | iot_net, db_net | ✅ labels |
| esphome | 6052 | host | ✅ labels |
| datasql | 5432 (loopback), 5050 (pgAdmin) | db_net | ✅ labels (datapostgres/datapgadmin/dataredis) |
| flowise | 8100 | db_net | ✅ labels |
| n8n | 5678 | db_net | ✅ labels (PostgreSQL/runtime auditado; hardening pendiente) |
| lobehub | 3210 (+ RustFS S3 9000) | db_net + lobe_storage | ✅ labels (runtime base confirmado; opcionales pendientes) |
| filebrowser | 8085 | filebrowser_default | ✅ labels |
| homepage | 3000 | homepage_net | — (es el dashboard) |
| ntfy | 8090 | homepage_net | ✅ labels |
| node-red | 1880 | iot_net | ✅ labels |
| iobroker | 8181 (preparado) | iot_net | ✅ labels |
| usb-api (systemd) | 8091 | nativo | services.yaml |
| spacedrive | — | spacedrive_default | — |

> Flowise está activo en el NAS y usa `flowise_db` + `dataredis`; n8n está activo,
> usa `n8n_db` con `n8n_user` y su conexión/runtime ya fue auditado. LobeHub ya
> completó migración PostgreSQL, inició LobeHub/RustFS y validó Redis autenticado;
> el runtime base está operativo. Queda configurar claves válidas de proveedores
> (OpenAI/DeepSeek) si se van a usar, y QStash/marketplace solo para esas funciones.
> La ficha, guía y compose objetivo de n8n están catalogados; queda verificar su
> hardening y pin `2.36.7` antes de declararlos aplicados.

## Redes Docker

| Red | Uso | Regla |
|-----|-----|-------|
| `db_net` | Apps ↔ DBs (postgres, pgAdmin, redis) | PostgreSQL solo en `127.0.0.1:5432` para Home Assistant; pgAdmin usa la excepción LAN `5050`; Redis no publica puerto |
| `iot_net` | IoT (EMQX, ESPHome, HA futuro, ioBroker) | Todo IoT aquí |
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
2. Crear `compose.yml` + `.env` si hay secretos
3. El compose debe usar `extends.file: ../_common.yml` y `env_file: [../.env, .env]`
4. `chmod 600 .env`
5. Agregar labels `homepage.*` en compose (auto-descubrimiento)
6. `dk <svc> && svc config <svc>` para validar
7. `svc up <svc>` y verificar health, logs y consumo
8. `svc catalog-sync <svc>` — genera ficha, guía, script DebMenux

Si necesita PostgreSQL o Redis, leer `docs/services/datasql-guide.md` para el estado del stack, crear bases/roles y conectar consumidores; usar `db_net`, crear DB/usuario dedicados, no publicar DBs en la LAN y no usar `depends_on` contra un compose externo. `db_net` no prueba que una aplicación
use una base: confirmar compose, configuración y runtime. Consumidores confirmados: Flowise (`flowise_db` + `dataredis`), Home Assistant
(`homeassistant_db` por `127.0.0.1:5432`), n8n (`n8n_db` con `n8n_user` por
`datapostgres:5432` dentro de `db_net`) y LobeHub (`lobehub_db` con
`lobehub_user`, `dataredis` y RustFS; runtime base confirmado). El runtime
 de n8n está auditado; el hardening y pin `2.36.7` quedan pendientes de verificación.
El stack operativo único es `datasql`, con ParadeDB PostgreSQL
17, pgvector/pg_search/pg_cron, pgAdmin y Redis; sus contenedores finales son
`datapostgres`, `datapgadmin` y `dataredis`. `aipostgres` es la base
administrativa y un alias histórico, no un segundo stack. RustFS es un servicio
S3 separado y solo se instala con LobeHub u otro consumidor real de objetos.

La instalación limpia elimina el stack DataSQL anterior y no conserva sus bases;
después se crean bases y roles vacíos dedicados para cada consumidor verificado.

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
- **SIEMPRE**, si la petición trata de `_drafts`, unificación o evolución de herramientas, leer `.kiro/skills/documentation-evolution/SKILL.md` antes de responder
- **SIEMPRE** compose.yml (nunca docker-compose.yml)

## Documentación adicional

| Tema | Archivo |
|------|---------|
| Guía de servicio | `docs/services/<svc>-guide.md` |
| Ficha del catálogo | `agent/catalog/services/<svc>/ficha.md` |
| Manual del NAS (hardware, redes, puertos) | `docs/nas-manual.md` |
| Redes host y DNS (networkd, resolved, Avahi, IPv6, macvlan) | `docker-nas/references/networking.md` |
| Instalación futura de red | `docker-nas/references/networking-install.md` |
| Migración de backend o rango IP | `docker-nas/references/networking-migration.md` |
| Recuperación de red y DNS | `docker-nas/references/networking-recovery.md` |
| Meta-prompt de unificación | `docs/meta-prompt-unificar.md` |
| Bootstrap portable para cualquier chat LLM | `docs/llm-context-bootstrap.md` |
| Skill del chat para unificar y evolucionar herramientas | `.kiro/skills/documentation-evolution/SKILL.md` |
| Bootstrap automático del chat | `.kiro/hooks/documentation-evolution-on-prompt.json` |
| Consistencia arquitectónica | `docs/architecture-consistency.md` |
| Mapa canónico de arquitectura, gaps y criterios | `docs/framework-knowledge-compilation.md` |
| Contratos arquitectónicos | `agent/architecture/contracts.json` |
| Homepage (labels, widgets, config) | `docs/services/homepage-guide.md` |
| ioBroker (IoT, MQTT, backups, upgrades) | `docs/services/iobroker-guide.md` |
| DataSQL y servicios con PostgreSQL | `docs/services/datasql-guide.md` | PostgreSQL+pgvector+pg_search+pg_cron, consumidores, creación de roles/bases, Redis compartido, instalación, permisos y db_net |
| Flowise (prueba con DataSQL) | `docs/services/flowise-guide.md` |
| n8n (auditoría, PostgreSQL y handoff a LobeHub) | `docs/services/n8n-guide.md` |
| LobeHub (instalación auditada, DataSQL, RustFS y verificación) | `docs/services/lobehub-guide.md` |
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
