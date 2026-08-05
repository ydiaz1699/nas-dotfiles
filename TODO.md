# TODO — nas-dotfiles

Roadmap de features pendientes, priorizadas por impacto/esfuerzo.
Actualizado: 2026-08-05

---

## CLI (`svc`) — Próximos

| # | Feature | Descripción | Esfuerzo | Estado |
|---|---------|-------------|:--------:|:------:|
| 1 | `svc backup-all` | Backup de todos los servicios en secuencia con resumen final (análogo a `update-all`) | 20 min | ⬜ |
| 2 | `svc clone <origen> <nuevo>` | Duplicar servicio existente (compose + .env con placeholders) como base para uno nuevo | 30 min | ⬜ |
| 3 | `svc logs --grep <patrón>` | Buscar texto en logs de todos los servicios a la vez | 15 min | ⬜ |
| 4 | Verificación post-backup | `tar -tzf` automático después de crear backup, antes de confirmar éxito | 10 min | ⬜ |
| 5 | `svc lock <servicio>` | Marcar servicio como protegido en runtime (doble confirmación para stop/down/restore) | 25 min | ⬜ |
| 6 | `svc cron` | Helper para agendar backups/updates automáticos vía crontab | 20 min | ⬜ |
| 7 | Healthcheck HTTP genérico | Si un servicio no define healthcheck en compose, `svc doctor` intenta curl al puerto expuesto | 15 min | ⬜ |
| 8 | Historial de `svc doctor` | Guardar cada corrida con timestamp en log para ver tendencia de disco/memoria | 15 min | ⬜ |
| 9 | Textual dashboard (`svc dashboard`) | TUI con paneles divididos: servicios, logs, CPU/RAM en vivo | Alto | ⬜ |

---

## Agente Python — Próximos

| # | Feature | Descripción | Esfuerzo | Estado |
|---|---------|-------------|:--------:|:------:|
| 1 | Catálogo pre-cargado en contexto | Al arrancar, inyectar fichas de `catalog/services/` en el contexto del agente | 25 min | ⬜ |
| 2 | Tool `compare_catalog` | Comparar config actual de un servicio contra su ficha del catálogo, detectar drift | 20 min | ⬜ |
| 3 | Resumen post-sesión legible | Al terminar, mostrar informe humanizado de lo que hizo el agente (no JSON crudo) | 15 min | ⬜ |
| 4 | Auto-heal sugerido | Cuando troubleshoot detecta error conocido (OOM, port conflict), sugerir fix concreto con args listos | 40 min | ⬜ |
| 5 | psutil para doctor/watch | Reemplazar subprocess (free/df) por psutil — más datos, más limpio | 30 min | ⬜ |

---

## Seguridad — Backlog

| # | Feature | Descripción | Esfuerzo | Estado |
|---|---------|-------------|:--------:|:------:|
| 1 | Rotación de secretos alertada | Detectar variables PASSWORD/TOKEN en .env con valor "CAMBIAR" y alertar en `svc doctor` | 15 min | ⬜ |
| 2 | Permisos de `.env` | Forzar `chmod 600` al crear con `svc create`, verificar en `svc doctor` | 10 min | ⬜ |
| 3 | Confirmación doble canal | Para servicios con `protected: true` en catálogo, exigir confirmación extra en restore/stop | 30 min | ⬜ |

---

## Observabilidad — Backlog

| # | Feature | Descripción | Esfuerzo | Estado |
|---|---------|-------------|:--------:|:------:|
| 1 | Exportar métricas a Prometheus | `svc doctor` → textfile que Grafana levanta via node_exporter | 40 min | ⬜ |
| 2 | Notificaciones Telegram/ntfy | Alertar cuando un servicio cae, backup falla, o agente hace algo destructivo | 45 min | ⬜ |

---

## Backups — Backlog

| # | Feature | Descripción | Esfuerzo | Estado |
|---|---------|-------------|:--------:|:------:|
| 1 | Backup remoto (rclone/S3) | Subir backups a almacenamiento externo con rotación separada | Alto | ⬜ |
| 2 | `svc snapshot` / `svc rollback` | Guardar solo compose+.env (liviano) antes de cambios, para revertir config rápido | 25 min | ⬜ |

---

## Descartadas / Postergadas

| Feature | Razón |
|---------|-------|
| Dashboard web completo | `svc doctor` + `svc watch` cubren el 80% desde terminal |
| Caché de búsquedas web | Las búsquedas rara vez se repiten exacto, bajo ROI |
| Backup incremental | Solo vale si hay servicios >10GB; tar funciona para la mayoría |
| Exportar a Prometheus | Solo si ya hay Grafana+Prometheus corriendo |
| Modo "explica antes" per-tool | El agente ya tiene reglas claras de cuándo confirmar |

---

## Completadas ✅

| Feature | Fecha | Commit/PR |
|---------|-------|-----------|
| Sistema de memoria (Learning Loop) — remember/recall/learn_skill | 2026-08-05 | PR #8 |
| Daemon systemd (agent/daemon.py + nas-agent.service) | 2026-08-05 | PR #8 |
| Suite de tests (75 tests: memory, classify, validation, daemon, tool_result) | 2026-08-05 | PR #8 |
| Python CLI dual (svc_py/ — Typer + Rich + InquirerPy) | 2026-08-05 | PR #9 |
| Selector NAS_CLI=bash/python en shell/init.sh | 2026-08-05 | PR #9 |
| Docker SDK nativo en Python CLI | 2026-08-05 | feat/python-cli |
| Rich traceback para errores bonitos | 2026-08-05 | feat/python-cli |
| Menu con fuzzy search + multi-select + preview | 2026-08-05 | feat/python-cli |
| `svc recreate` (up --force-recreate sin pull) | 2026-08-05 | main |
| `pipins` — pip installer (mirrors instal para Python) | 2026-08-05 | main |
| REPL mode → `agent chat` (loop conversacional) | 2026-08-05 | main |
| Agente conoce CLI del usuario (menciona svc en respuestas) | 2026-08-05 | main |

| Feature | Fecha | Commit/PR |
|---------|-------|-----------|
| Migración Option B (sin symlinks) | 2026-07-28 | refactor/option-b |
| Google Gemini como provider default | 2026-07-28 | feat(agent) |
| Instrucciones de razonamiento en prompt | 2026-07-28 | feat(agent) |
| Extended thinking para Bedrock | 2026-07-28 | feat(agent) |
| `_shell.py` — safe_run + validate_service_name | 2026-07-28 | security: batch 1 |
| Modo NAS_AGENT_READONLY | 2026-07-28 | security: batch 1 |
| Modo NAS_AGENT_DRYRUN (dual: soft+hard) | 2026-07-28 | security |
| Backup de .bashrc antes de sed | 2026-07-28 | security: batch 1 |
| Audit log (JSON Lines) | 2026-07-28 | feat: batch 2 |
| `svc doctor` (6-point health check) | 2026-07-28 | feat: batch 2 |
| `svc diff` (compose vs resolved) | 2026-07-28 | feat: batch 2 |
| Fix: subshell pipe bugs en svc_doctor | 2026-07-28 | fix(cli) |
| Fix: memory_info() cálculo real | 2026-07-28 | fix |
| Fix: create_service() sanitización YAML | 2026-07-28 | fix |
| Fix: validate_compose() usa validated_service_path | 2026-07-28 | fix |
| CONTRIBUTING.md | 2026-07-28 | docs |
| Sistema de plugins dinámicos (base + loader) | 2026-07-28 | feat: phase 3 |
| Plugins: docker, backup, network | 2026-07-28 | feat: phase 3 |
| Event bus pub/sub (exact/wildcard/global) | 2026-07-28 | feat: phase 3 |
| MQTT listener (paho-mqtt → EventBus) | 2026-07-28 | feat: phase 3 |
| Scheduler de tareas periódicas (threaded) | 2026-07-28 | feat: phase 3 |
| Cache KV con TTL + persistencia | 2026-07-28 | feat: phase 3 |
| Config centralizada (defaults.yml) | 2026-07-28 | feat: phase 3 |
| Sesión persistente (FileSessionManager) | 2026-07-28 | feat: phase 3 |
| Rich UI (panels, colores, Markdown) | 2026-07-28 | feat: phase 3 |
| Tools: bulk_discover, export_service | 2026-07-28 | feat: phase 3 |
| Tools: list_files, read_file_content | 2026-07-28 | feat: phase 3 |
| UI más colorida + panels anchos (60 chars) | 2026-07-31 | ui/colorful-wider-panels (PR #6) |
| Actualización completa de documentación | 2026-07-31 | docs: full update |
