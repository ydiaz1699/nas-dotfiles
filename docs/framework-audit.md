# Auditoría del Framework — nas-dotfiles + DebMenux

> **Mapa canónico de arquitectura, estado, gaps y criterios:** [`docs/framework-knowledge-compilation.md`](framework-knowledge-compilation.md). Este archivo conserva la orientación ejecutiva e inventario rápido; no sustituye contratos ni verificaciones.

> **Última actualización:** 2026-08-17
> **Propósito:** Evitar que el LLM relea todo el proyecto en cada sesión.
> Leer SOLO este archivo para tener el mapa completo.
> Para detalles de un archivo específico → usar lazy loading.

---

## Arquitectura (5 capas + 2 repos)

```
┌── ~/.bashrc ───────────────────────────────────────────────────────────────┐
│  source $NAS_DOTFILES/shell/init.sh                                        │
│    ├── 9 módulos: aliases, nav, docker, system, instal, pipins, git,       │
│    │              completions, prompt                                       │
│    ├── svc() → bash/python según NAS_CLI                                   │
│    ├── agent() → python -m agent.nas_agent                                 │
│    └── Source $DOCKER_BASE/.env (SERVER_IP, TZ)                            │
└────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌── svc (35+ comandos) ──────────────────────────────────────────────────────┐
│  NAS_CLI=bash → docker/cli/svc.sh (9 libs)                                 │
│  NAS_CLI=python → svc_py/ (Typer + Rich + InquirerPy, 8 módulos)           │
│  Estrategia: bash=verdad (lógica), python=interfaz (UI bonita)             │
└────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌── agent (28 tools, 8 plugins) ─────────────────────────────────────────────┐
│  Providers: Gemini (default) · Bedrock (Claude) · Ollama (local)           │
│  Prompt: clasificación dinámica → solo carga bloques relevantes            │
│  Catálogo: pre-cargado al arrancar (resumen de servicios sin llamar tools) │
│  Daemon: systemd → scheduler + plugins 24/7                                │
└────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌── Verificación (3 tools + compare) ───────────────────────────────────────┐
│  svc scan          → DETECTA lagunas (Git + snapshot; ledger por archivo pendiente de implementar) │
│  svc catalog-sync  → GENERA lo que falta (ficha, guía, script)             │
│  dependency-map.md → DOCUMENTA las reglas (grafos A–I)                     │
│  compare_catalog() → DETECTA drift (compose real vs catálogo)              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Estado real del scanner incremental

`svc scan` ya usa `git diff`, `git ls-files` y `agent/cache/project-snapshot.json`
para detectar cambios desde `last_commit`. Sin embargo, el snapshot aún no conserva
un ledger por archivo que indique `processed`, `pending` o `failed`. La versión actual
filtra inconsistencias por servicio y no debe describirse como procesamiento
incremental completo.

La siguiente fase pendiente es comparar commits, staged, unstaged, no trackeados y
eliminados; guardar hash/estado por archivo; persistir pendientes y exponer
`svc scan --status`. El diseño detallado está en
`_drafts/IDEA-scanner-incremental-git.md`.

---

### Shell (`shell/`)

| Archivo | Función |
|---------|---------|
| `init.sh` | Loader principal (sourced por ~/.bashrc) |
| `lib/aliases.sh` | ll, la, lt, cp/mv/rm interactivo |
| `lib/nav.sh` | dk, adm, nasfk, up, admf, dkf |
| `lib/docker.sh` | dps, dpa, dim, dnet, dvol, dprune + completions svc |
| `lib/system.sh` | nas, disk, netinfo, logs |
| `lib/instal.sh` | APT wrapper + registro |
| `lib/pipins.sh` | pip wrapper |
| `lib/git.sh` | gpl, gs, ga, gc, gp, git-quick |
| `lib/completions.sh` | TAB completions generales |
| `lib/prompt.sh` | PS1 con contenedores + disco% |

### Docker CLI bash (`docker/cli/`)

| Archivo | Función |
|---------|---------|
| `svc.sh` | Entrypoint (22 cases globales + passthrough) |
| `lib/discovery.sh` | svc_list, svc_compose_file |
| `lib/docker.sh` | svc_update_all |
| `lib/health.sh` | svc_health, svc_lista, svc_doctor |
| `lib/backup.sh` | svc_backup, svc_restore, svc_backup_all, svc_snapshot, svc_rollback |
| `lib/extras.sh` | port-map, size, net, env, create, clone, cron, lock, doctor-history, watch, diff, open, depends |
| `lib/catalog-sync.sh` | Pipeline auto-docs en cascada |
| `lib/notifications.sh` | ntfy_send() |
| `lib/menu.sh` | TUI con fzf |
| `lib/help.sh` | Texto de ayuda |

### Docker CLI python (`svc_py/`)

| Archivo | Función |
|---------|---------|
| `app.py` | Typer app, registra comandos |
| `commands/health.py` | health, doctor, watch |
| `commands/backup.py` | backup, restore |
| `commands/catalog.py` | catalog-sync (wrapper bash) |
| `commands/compose.py` | create, diff |
| `commands/docker.py` | update-all |
| `commands/info.py` | port-map, size, net, depends, env, open |
| `commands/menu.py` | InquirerPy menu |
| `commands/scanner.py` | scan (subprocess al scanner) |
| `core/bash_bridge.py` | Bridge genérico → svc.sh |
| `core/discovery.py` | Detección de servicios |
| `core/docker.py` | compose_run, passthrough |

### Agente (`agent/`)

| Archivo | Función |
|---------|---------|
| `nas_agent.py` | Prompt dinámico, clasificador, REPL, multi-provider |
| `daemon.py` | Systemd daemon (scheduler + plugins) |
| `tools/__init__.py` | ALL_TOOLS (28 tools registradas) |
| `tools/discovery_tools.py` | list_services, scan_compose, auto_catalog, bulk_discover, export_service |
| `tools/system_tools.py` | scan_ports, disk_usage, memory_info, network_info, list_files, read_file_content |
| `tools/docker_tools.py` | service_start/stop/restart/update/logs |
| `tools/compose_tools.py` | create_service, validate_compose, read_compose |
| `tools/backup_tools.py` | backup_service, restore_service, list_backups |
| `tools/diagnostic_tools.py` | service_health, port_conflicts, troubleshoot |
| `tools/search_tools.py` | search_service_info (web fallback) |
| `tools/memory_tools.py` | remember, recall, learn_skill, update_user_model, memory_stats |
| `tools/project_scanner.py` | project_scan (incremental git-based) |
| `tools/compare_tools.py` | compare_catalog (drift detection) |
| `plugins/docker_plugin.py` | Monitoreo de contenedores |
| `plugins/backup_plugin.py` | Backups programados |
| `plugins/notification_plugin.py` | Alertas ntfy |
| `plugins/network_plugin.py` | Monitoreo de redes |
| `plugins/memory_plugin.py` | Persistencia de memoria |
| `plugins/ha_discovery_plugin.py` | Descubrimiento Home Assistant |

### Catálogo (`agent/catalog/services/`)

| Servicio | Ficha | Compose | .env.example | Guía | Script DebMenux |
|----------|:-----:|:-------:|:------------:|:----:|:---------------:|
| datasql | ✅ | ✅ | ✅ | ✅ | ✅ |
| flowise | ✅ | ✅ | ✅ | ✅ | ✅ |
| emqx | ✅ | ✅ | ❌ | ✅ | ✅ |
| esphome | ✅ | ✅ | ✅ | ✅ | ✅ |
| filebrowser | ✅ | ✅ | ✅ | ✅ | ✅ |
| homeassistant | ✅ | ✅ | ✅ | ✅ | ✅ |
| homepage | ✅ | ✅ | ✅ | ✅ | ✅ |
| node-red | ✅ | ✅ | ✅ | ✅ | ✅ |
| ntfy | ✅ | ✅ | ✅ | ✅ | ✅ |
| usb-api | ✅ | ✅ | ✅ | ⚠️ | ✅ |
| adguard | ❌ | ❌ | ❌ | ❌ | ✅ |

### Documentación (`docs/`)

| Archivo | Propósito |
|---------|-----------|
| `docker-entorno.md` | **LEER ANTES de tocar compose** — reglas env_file, redes, convenciones |
| `dependency-map.md` | **LEER DESPUÉS de cualquier cambio** — grafos A–I, tabla CLI |
| `ideas-decisions.md` | Historial de 15 decisiones (problema → solución → learning) |
| `nas-manual.md` | Hardware, IPs, puertos, redes del NAS real |
| `catalog-sync-pipeline.md` | Cómo funciona el pipeline auto-docs |
| `services/<svc>-guide.md` | Guía operativa por servicio (9 guías) |
| `troubleshooting.md` | Problemas resueltos con soluciones |
| `framework-knowledge-compilation.md` | **MAPA CANÓNICO** — ideas, arquitectura, estado, gaps y criterios de aceptación |
| `framework-audit.md` | **ESTE ARCHIVO** — mapa ejecutivo sin releer |

### Skill Kiro (`docker-nas/references/`)

| Archivo | Propósito |
|---------|-----------|
| `nas-context.md` | Skill completa: entorno, servicios, reglas, progressive updates |
| `svc.md` | Referencia completa de comandos svc |
| `entorno.md` | Detalle del shell framework |
| `seguridad.md` | Reglas de seguridad |
| `diagnostic.md` | Procedimiento de diagnóstico |
| `networking.md` | Redes Docker (macvlan, bridge) |
| `agent.md` | Arquitectura del agente |
| `extend.md` | Cómo extender el framework |

### DebMenux (`DebMenux-/`)

| Archivo | Propósito |
|---------|-----------|
| `menu` | Entry point (dialog TUI) |
| `install.sh` | Instalador |
| `services.json` | Registry de servicios |
| `lib/docker.sh` | Helpers Docker |
| `lib/integration.sh` | Hooks nas-dotfiles |
| `lib/notifications.sh` | ntfy helpers |
| `lib/utils.sh` | Utilidades comunes |
| `scripts/services/*.sh` | 10 scripts de instalación |
| `templates/usb-automount/` | Templates udev + systemd |

---

## Servicios activos en el NAS

| Servicio | Puerto | Red | Tipo |
|----------|--------|-----|------|
| adguard | 53, 80 (IP .201) | macvlan | DNS/ad-block |
| emqx | 1883, 18083 | iot_net | Broker MQTT |
| esphome | 6052 | host | IoT firmware |
| datasql | 5050 (pgadmin) | db_net | PostgreSQL + pgAdmin + Redis |
| filebrowser | 8085 | default | Explorador archivos |
| homeassistant | 8123 | host | Automatización |
| homepage | 3000 | homepage_net | Dashboard |
| ntfy | 8090 | homepage_net | Notificaciones push |
| node-red | 1880 | iot_net | Automatización flujos |
| usb-api | 8091 | nativo (systemd) | REST API USBs |

---

## Comandos svc (22 globales + passthrough)

### Globales

```
lista, health, doctor, doctor-history, update-all, backup-all,
port-map, size, net, watch, create, clone, menu, diff,
logs-grep, cron, lock, unlock, catalog-sync, scan,
snapshot, rollback
```

### Con servicio

```
up, down, restart, start, stop, kill, update, recreate,
logs, ps, stats, top, exec, backup, restore, depends,
open, env, config + passthrough docker compose
```

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Servicios Docker | 10 |
| Comandos svc | 35+ |
| Tools del agente | 28 |
| Plugins | 8 |
| Guías operativas | 8 |
| Shell modules | 9 |
| Ideas/decisiones | 15 |
| Tests | 9 archivos |

---

## Para el próximo LLM

1. **Leer este archivo** → tienes el mapa completo
2. **Si vas a tocar compose** → leer `docs/docker-entorno.md`
3. **Después de cualquier cambio** → consultar `docs/dependency-map.md`
4. **Si creaste algo nuevo** → `svc scan` para verificar que está conectado
5. **Al cerrar sesión** → verificar: tabla CLI actualizada? Progressive Updates? PENDIENTES?
