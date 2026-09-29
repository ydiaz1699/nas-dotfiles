# CODE-MAP — nas-dotfiles

> **Índice generado — no editar a mano.** Qué hace cada archivo de código, sus símbolos y sus conexiones internas. Igual que n8n-mcp indexa los nodos: consulta este mapa para saber QUÉ archivo tocar sin releer todo el repo, y luego abre solo ese archivo. Complemento de `docs/dependency-map.md` (qué actualizar en cascada al tocar un archivo).

> Archivos de código mapeados: **111**. Regenerar con `svc code-map` (o `python3 agent/tools/project_index.py --code-map`).

> **Conexiones** = imports internos (Python) o `source` (Bash). **Usado por** = quién importa este archivo (grafo inverso, solo Python). Ambos son mejor-esfuerzo.


## `agent/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `agent/__init__.py` | nas-agent — Agente inteligente para administración de NAS/Homelab | — | — | — |
| `agent/catalog/__init__.py` | — | — | — | — |
| `agent/catalog/_index.py` | Generador de índice del catálogo de servicios. | _parse_frontmatter(), build_index(), write_index(), load_index(), lookup_service(), services_by_category(), services_by_network(), main() | — | `agent/plugins/backup_plugin.py`, `agent/tools/discovery_tools.py` |
| `agent/catalog/services/openwa/wa-send.sh` | wa-send — enviar un mensaje de WhatsApp por la API de OpenWA desde la terminal. | die(), cleanup() | — | — |
| `agent/config/__init__.py` | — | — | — | — |
| `agent/core/__init__.py` | agent/core/ — Capa de lógica de negocio del agente NAS. | — | — | — |
| `agent/core/_result.py` | Resultado estructurado para tools del agente. | class Status, class ToolResult (ok, warn, error, to_dict), class Timer (elapsed_ms) | — | `agent/core/backup_manager.py`, `agent/core/compose_manager.py`, `agent/core/memory.py`, `agent/core/service_manager.py`, … (+5) |
| `agent/core/backup_manager.py` | Gestión de backups de servicios Docker. | class BackupManager (backup, restore, list_all) | `agent.core._result`, `agent.tools._shell` | `agent/plugins/backup_plugin.py`, `agent/tools/backup_tools.py` |
| `agent/core/compose_manager.py` | Generación y validación de archivos compose. | class ComposeManager (load_rules, load_compose_base_anchors, sanitize_value, read, validate) | `agent.core._result`, `agent.tools._shell` | `agent/tools/compose_tools.py`, `tests/test_compose_generation.py` |
| `agent/core/memory.py` | MemoryManager: gestión de archivos de memoria persistente. | class MemoryManager (ensure_initialized, load_memory, load_memory_section, add_to_memory, load_user_model, update_user_model), _now() | `agent.core._result` | `agent/daemon.py`, `agent/plugins/memory_plugin.py`, `agent/tools/memory_tools.py`, `tests/test_memory.py` |
| `agent/core/service_manager.py` | Operaciones de ciclo de vida de servicios Docker. | class ServiceManager (start, stop, restart, update, logs) | `agent.core._result`, `agent.tools._shell` | `agent/tools/docker_tools.py` |
| `agent/daemon.py` | Entry point para modo daemon (systemd). | _load_env_agent(), class Scheduler (add_task, start, stop), class NASAgentDaemon (setup, start, stop, signal_stop), _signal_handler(), main() | `agent.core.memory`, `agent.plugins` | `tests/test_daemon.py` |
| `agent/events/__init__.py` | agent/events/ — Event bus para comunicación asíncrona. | — | `agent.events.bus`, `agent.events.mqtt_listener` | — |
| `agent/events/bus.py` | Event bus interno del agente. | class Event, class EventBus (on, off, emit, event_count, history, last_events) | — | `agent/events/__init__.py`, `tests/test_phase3.py` |
| `agent/events/mqtt_listener.py` | Listener MQTT que conecta el broker al event bus. | class MQTTListener (add_mapper, start, stop, connected) | — | `agent/events/__init__.py` |
| `agent/lobehub_mcp.py` | Gateway MCP estrecho para consultar el framework nas-dotfiles desde LobeHub. | _json_bytes(), _redact_text(), _audit_path(), audit(), _error(), _check_lines(), _status_services(), _safe_capabilities(), _run_svc(), _local_operation(), _helper_request(), class Gateway (call), … (+12) | — | — |
| `agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py` | Front-door MCP lazy para nas-dotfiles. | class ManifestError, _manifest_path(), load_manifest(), _error(), _json_bytes(), _tool_schema(), class WorkerSupervisor (stop, request, shutdown), class Gateway (call, close), _rpc_result(), _rpc_error(), handle_rpc(), class StdioServer (run), … (+3) | — | — |
| `agent/mcp/nas_mcp_gateway/nas_mcp_worker.py` | Worker y helper read-only para nas-mcp-gateway. | _error(), _redact(), _safe_output(), _audit(), _run_fixed_svc(), _socket_path(), _helper_request(), _client_loop(), _serve_helper(), main() | — | — |
| `agent/nas_agent.py` | Agente inteligente para administración de NAS/Homelab | _load_env_agent(), _get_session_metadata_path(), _read_session_metadata(), _write_session_metadata(), _session_is_expired(), _clear_session(), _get_session_manager(), _load_catalog_summary(), _get_catalog_block(), _classify_query(), _assemble_prompt(), get_model(), … (+5) | `agent.tools` | `tests/test_classify.py` |
| `agent/plugins/__init__.py` | agent/plugins/ — Sistema de plugins dinámicos. | — | `agent.plugins.base`, `agent.plugins.loader` | `agent/daemon.py` |
| `agent/plugins/backup_plugin.py` | Plugin de backup automático. | class BackupPlugin (setup) | `agent.catalog._index`, `agent.core.backup_manager`, `agent.plugins.base`, `agent.tools.backup_tools` | — |
| `agent/plugins/base.py` | Clase base para plugins del agente NAS. | class ScheduleConfig, class EventHandler, class PluginMeta, class BasePlugin (name, enabled, enabled, tools, event_handlers, schedules) | — | `agent/plugins/__init__.py`, `agent/plugins/backup_plugin.py`, `agent/plugins/docker_plugin.py`, `agent/plugins/ha_discovery_plugin.py`, … (+6) |
| `agent/plugins/docker_plugin.py` | Plugin de gestión Docker. | class DockerPlugin (setup) | `agent.plugins.base`, `agent.tools._shell`, `agent.tools.discovery_tools`, `agent.tools.docker_tools` | — |
| `agent/plugins/ha_discovery_plugin.py` | MQTT Discovery para Home Assistant. | class HADiscoveryPlugin (setup, teardown) | `agent.plugins.base` | — |
| `agent/plugins/loader.py` | Descubrimiento y carga dinámica de plugins. | class PluginLoader (plugins, discover, load_plugin, unload_plugin, get_plugin, all_tools) | `agent.plugins.base` | `agent/plugins/__init__.py`, `tests/test_phase3.py` |
| `agent/plugins/memory_plugin.py` | Plugin de memoria persistente y auto-mejora. | class MemoryPlugin (setup) | `agent.core.memory`, `agent.plugins.base`, `agent.tools.memory_tools` | — |
| `agent/plugins/network_plugin.py` | Plugin de monitoreo de red. | class NetworkPlugin (setup) | `agent.plugins.base`, `agent.tools._shell`, `agent.tools.diagnostic_tools`, `agent.tools.system_tools` | — |
| `agent/plugins/notification_plugin.py` | Plugin de notificaciones via ntfy para el agente NAS. | class NotificationPlugin (setup, configure, ntfy_send, on_service_unhealthy, on_service_down, on_backup_complete) | `agent.plugins.base` | — |
| `agent/scheduler/__init__.py` | agent/scheduler/ — Ejecutor de tareas periódicas (cron-like). | — | `agent.scheduler.runner` | — |
| `agent/scheduler/runner.py` | Scheduler de tareas periódicas. | class TaskState, class Scheduler (add, remove, start, stop, running, status) | `agent.plugins.base` | `agent/scheduler/__init__.py` |
| `agent/tools/__init__.py` | Herramientas (tools) del nas-agent. | — | `agent.tools.backup_tools`, `agent.tools.capability_tools`, `agent.tools.compare_tools`, `agent.tools.compose_tools`, `agent.tools.diagnostic_tools`, `agent.tools.discovery_tools`, `agent.tools.docker_tools`, `agent.tools.memory_tools`, `agent.tools.project_scanner`, `agent.tools.search_tools`, `agent.tools.system_tools` | `agent/nas_agent.py` |
| `agent/tools/_audit.py` | Sistema de auditoría para el agente NAS. | _get_log_path(), _is_audit_enabled(), log_tool_call(), _sanitize_args(), audited(), get_session_summary() | — | — |
| `agent/tools/_result.py` | Resultado estructurado para tools del agente. | class Status, class ToolResult (ok, warn, error, to_dict), class Timer (elapsed_ms) | — | — |
| `agent/tools/_shell.py` | Módulo común de ejecución segura de comandos. | class InvalidServiceName, validate_service_name(), validated_service_path(), safe_run(), find_compose(), service_exists_or_error(), is_readonly(), is_dryrun(), readonly_guard() | — | `agent/core/backup_manager.py`, `agent/core/compose_manager.py`, `agent/core/service_manager.py`, `agent/plugins/docker_plugin.py`, … (+8) |
| `agent/tools/backup_tools.py` | Herramientas de backup y restore para servicios Docker. | _get_backup_manager(), @tool backup_service(), @tool restore_service(), @tool list_backups() | `agent.core.backup_manager` | `agent/plugins/backup_plugin.py`, `agent/tools/__init__.py` |
| `agent/tools/capabilities.py` | Consulta el inventario dinámico de capacidades del NAS. | _manifests(), _index(), _operations(), main() | — | `agent/tools/capability_tools.py` |
| `agent/tools/capability_tools.py` | Tools de descubrimiento de capacidades sin ejecutar mutaciones. | @tool discover_capabilities() | `agent.tools.capabilities` | `agent/tools/__init__.py` |
| `agent/tools/compare_tools.py` | Detecta drift entre el compose real y el catálogo. | _compose_candidates(), _find_compose(), _discover_services(), _extract_ports(), _extract_networks(), _extract_volumes(), _extract_env_vars(), _extract_image(), _has_env_file_global(), _has_healthcheck(), _has_security_opt(), _has_resource_limits(), … (+2) | — | `agent/tools/__init__.py` |
| `agent/tools/compose_tools.py` | Herramientas para crear y validar archivos docker-compose. | _get_compose_manager(), @tool read_compose(), @tool validate_compose(), @tool create_service() | `agent.core._result`, `agent.core.compose_manager`, `agent.tools._shell` | `agent/tools/__init__.py` |
| `agent/tools/diagnostic_tools.py` | Herramientas de diagnóstico para el NAS. | @tool service_health(), @tool port_conflicts(), @tool troubleshoot() | `agent.tools._shell` | `agent/plugins/network_plugin.py`, `agent/tools/__init__.py` |
| `agent/tools/discovery_tools.py` | Herramientas de descubrimiento de servicios Docker. | _catalogize_compose_paths(), @tool list_services(), @tool scan_compose(), @tool auto_catalog(), @tool bulk_discover(), @tool export_service() | `agent.catalog._index`, `agent.core._result`, `agent.tools._shell` | `agent/plugins/docker_plugin.py`, `agent/tools/__init__.py` |
| `agent/tools/docker_tools.py` | Herramientas para control de servicios Docker. | _get_service_manager(), @tool service_start(), @tool service_stop(), @tool service_restart(), @tool service_update(), @tool service_logs() | `agent.core.service_manager` | `agent/plugins/docker_plugin.py`, `agent/tools/__init__.py` |
| `agent/tools/memory_tools.py` | Tools de memoria persistente para el agente. | _mgr(), _now(), @tool remember(), @tool recall(), @tool learn_skill(), @tool update_user_model(), @tool memory_stats() | `agent.core.memory` | `agent/plugins/memory_plugin.py`, `agent/tools/__init__.py` |
| `agent/tools/project_index.py` | Índice estructural del ecosistema nas-dotfiles + DebMenux. | _relative(), _iter_repo_files(), _classify_path(), _sha256(), _read_text(), _file_records(), _extract_bash_commands(), _extract_python_commands(), _extract_completion_commands(), _extract_prompt_commands(), _extract_registered_tools(), _extract_capabilities(), … (+22) | — | — |
| `agent/tools/project_scanner.py` | Detecta lagunas e inconsistencias en el ecosistema nas-dotfiles. | class Snapshot (save, load), _get_current_commit(), _get_changed_files(), _hash_file(), _classify_changed_file(), _build_snapshot_from_scan(), incremental_scan(), class Issue, class ScanResult (errors, warnings, summary, to_dict), _detect_services(), _get_debmenux_scripts_dir(), _check_services(), … (+8) | — | `agent/tools/__init__.py` |
| `agent/tools/search_tools.py` | Herramienta de búsqueda web para servicios no catalogados. | @tool search_service_info(), _search_dockerhub(), _search_github_compose(), _extract_info_from_readme() | `agent.tools._shell` | `agent/tools/__init__.py` |
| `agent/tools/system_tools.py` | Herramientas de sistema para el NAS. | @tool scan_ports(), _parse_ports(), @tool disk_usage(), @tool memory_info(), _calc_mem_pct(), @tool network_info(), @tool list_files(), @tool read_file_content() | `agent.tools._shell` | `agent/plugins/network_plugin.py`, `agent/tools/__init__.py` |

## `docker/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `docker/cli/lib/backup.sh` | Backup y restore de volumenes Docker con rotacion | svc_backup(), _svc_backup_rotate(), svc_restore(), svc_backup_all(), _svc_backup_verify(), svc_logs_grep(), svc_snapshot(), svc_rollback() | `${NAS_DOTFILES:-/nas-dotfiles}/docker/cli/lib/notifications.sh` | — |
| `docker/cli/lib/catalog-sync.sh` | nas-dotfiles — Pipeline de Auto-Documentación en Cascada | _sync_log(), _sync_info(), _sync_ok(), _sync_skip(), _sync_new(), _sync_warn(), _extract_from_compose(), _generate_ficha_from_compose(), _catalogize_compose(), _sync_compose(), _sync_env_example(), _generate_guide_placeholder(), … (+8) | `${NAS_DOTFILES:-/nas-dotfiles}/docker/cli/lib/notifications.sh` | — |
| `docker/cli/lib/discovery.sh` | Deteccion de servicios Docker Compose | svc_list(), svc_compose_file(), svc_lista() | — | — |
| `docker/cli/lib/docker.sh` | update-all con confirmacion y uso correcto de svc_compose_file | svc_update_all() | — | — |
| `docker/cli/lib/extras.sh` | Comandos adicionales: open, depends, port-map, size, net, env, create, watch | svc_depends(), svc_open(), svc_port_map(), svc_size(), svc_net(), svc_env(), svc_create(), _svc_layers_reminder(), svc_watch(), svc_doctor(), svc_diff(), svc_clone(), … (+14) | — | — |
| `docker/cli/lib/health.sh` | Dashboard de salud con healthcheck, uptime, y restart count | svc_health() | — | — |
| `docker/cli/lib/help.sh` | — | _svc_ayuda() | — | — |
| `docker/cli/lib/lobehub.sh` | Operaciones seguras y repetibles para LobeHub. | _lobe_usage(), _lobe_compose_args(), _lobe_compose(), _lobe_env_value(), _lobe_context_report(), _lobe_context_check(), _lobe_compose_resolve_hint(), _lobe_result(), _lobe_confirm(), _lobe_secret_bytes(), _lobe_preflight(), _lobe_sql_admin(), … (+10) | — | — |
| `docker/cli/lib/menu.sh` | — | svc_menu(), _svc_preview(), _svc_status_list() | — | — |
| `docker/cli/lib/notifications.sh` | nas-dotfiles — Librería de Notificaciones (ntfy) | ntfy_send(), ntfy_service_down(), ntfy_service_restarted(), ntfy_update_complete(), ntfy_backup_complete(), ntfy_backup_failed(), ntfy_system_alert(), ntfy_health_failed() | — | — |
| `docker/cli/svc.sh` | — | — | `lib/backup.sh`, `lib/discovery.sh`, `lib/docker.sh`, `lib/extras.sh`, `lib/health.sh`, `lib/help.sh`, `lib/lobehub.sh`, `lib/menu.sh` | — |

## `install.sh/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `install.sh` | Instalador bash interactivo (fallback sin Python) | _check_install_pkg(), _detect(), _configure_bashrc() | — | — |

## `setup/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `setup` | setup — Entry point universal de instalación | — | — | — |

## `shell/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `shell/init.sh` | Loader único del shell framework | path_add(), svc(), agent() | `$_NAS_USER_CONF`, `$_f`, `.env` | — |
| `shell/lib/aliases.sh` | Navegacion | reload(), rm(), cp(), mv() | `~/.bashrc` | — |
| `shell/lib/completions.sh` | Completions adicionales | _instal_complete(), _logs_complete() | — | — |
| `shell/lib/docker.sh` | Autocompletado de svc | _svc_services(), _lobe_actions(), _svc_complete() | — | — |
| `shell/lib/git.sh` | Aliases y helpers de git | git-clean-branches(), git-quick() | — | — |
| `shell/lib/instal.sh` | _apt_cmd — detecta apt-fast o fallback a apt-get | _apt_cmd(), _apt_cache_stale(), instal() | — | — |
| `shell/lib/nav.sh` | subir N niveles | up(), _nav(), _nav_complete(), _nav_fzf(), dk(), dkf(), _dk_completions(), nasfk(), nasfkf(), _nasfk_completions() | — | — |
| `shell/lib/pipins.sh` | pipins — Instalador de paquetes pip (equivalente a instal para Python) | _pip_cmd(), pipins() | — | — |
| `shell/lib/prompt.sh` | Prompt resultante (ejemplo): | _prompt_cache_docker(), _prompt_cache_disk(), _prompt_git(), _build_prompt() | — | — |
| `shell/lib/system.sh` | nas — dashboard rapido del NAS | nas(), disk(), netinfo(), logs() | — | — |
| `shell/scripts/apply-restart-policy.sh` | Migra contenedores existentes a on-failure:5 sin arrancar todos los servicios. | svc_cli(), compose_services() | — | — |
| `shell/scripts/boot-order.sh` | Arranque escalonado de Compose por capas. | log(), fail(), svc_cli(), compose_file(), discovered_services(), trim(), flush_layer(), load_layers(), validate_layers(), wait_for_docker(), wait_service_ready(), svc_up_one(), … (+5) | — | — |
| `shell/scripts/find-no-extends.sh` | Detecta Compose que no heredan los defaults de _common.yml. | — | — | — |
| `shell/scripts/install-boot-service.sh` | Genera e instala docker-boot-staged.service con las rutas reales de esta | render() | — | — |
| `shell/scripts/install_docker.sh` | Instalación de Docker Engine en Debian | usage(), parse_args(), echo_info(), echo_warn(), echo_error(), setup_logging(), print_command(), run_command(), run_optional_command(), apt_update_once(), detect_docker_user(), select_docker_user(), … (+13) | `$OS_RELEASE_FILE` | — |
| `shell/scripts/restart-all.sh` | Baja TODOS los servicios en orden inverso a las capas y reinicia el NAS. | — | — | — |
| `shell/scripts/start-all.sh` | Compatibilidad: el arranque canónico ahora vive en boot-order.sh. | — | — | — |
| `shell/scripts/stop-all.sh` | Baja TODOS los servicios en orden inverso a las capas y apaga el NAS. | — | — | — |
| `shell/scripts/stop-order.sh` | Apagado escalonado de Compose por capas, en ORDEN INVERSO al arranque. | log(), svc_cli(), compose_file(), is_running(), trim(), flush_layer(), load_layers() | — | — |

## `svc_py/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `svc_py/__init__.py` | svc_py — Python CLI para administración de servicios Docker en el NAS. | — | — | — |
| `svc_py/__main__.py` | Entry point: python -m svc_py | — | `svc_py.app` | — |
| `svc_py/app.py` | Aplicación principal Typer que registra todos los comandos. | snapshot(), capabilities(), lobehub(), no_boot(), boot_enable(), boot_status(), lista(), up(), down(), start(), stop(), restart(), … (+17) | `svc_py.commands`, `svc_py.core.bash_bridge`, `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | `svc_py/__main__.py` |
| `svc_py/commands/__init__.py` | CLI command modules. | — | — | `svc_py/app.py`, `svc_py/commands/menu.py` |
| `svc_py/commands/backup.py` | Backup y restore con Rich progress + InquirerPy selector. | _get_volumes(), _get_bind_mounts(), _rotate_backups(), backup(), restore() | `svc_py.config`, `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | `svc_py/commands/menu.py` |
| `svc_py/commands/catalog.py` | Comando catalog-sync para el Python CLI. | catalog_sync(), _show_status(), _regenerate_index(), _run_bash_catalog_sync(), _native_catalog_sync() | `svc_py.config`, `svc_py.core.discovery`, `svc_py.ui` | — |
| `svc_py/commands/codemap.py` | Comando 'svc code-map' para el Python CLI. | code_map() | `svc_py.config`, `svc_py.ui` | — |
| `svc_py/commands/compose.py` | Comandos de compose: create (wizard) y diff. | create(), diff() | `svc_py.config`, `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | — |
| `svc_py/commands/docker.py` | Comando update-all con InquirerPy + Rich progress. | update_all() | `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | — |
| `svc_py/commands/health.py` | Comandos de salud: health, doctor, watch. | _uptime_str(), _build_health_table(), health(), doctor(), watch() | `svc_py.config`, `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | — |
| `svc_py/commands/info.py` | Comandos informativos: port-map, size, net, depends, env, open. | port_map(), size(), net(), depends(), env_cmd(), open_cmd() | `svc_py.config`, `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | — |
| `svc_py/commands/menu.py` | Menú TUI interactivo avanzado con InquirerPy + Rich. | _service_preview(), _execute_action(), _multi_select_flow(), menu() | `svc_py.commands`, `svc_py.commands.backup`, `svc_py.core.discovery`, `svc_py.core.docker`, `svc_py.ui` | — |
| `svc_py/commands/scanner.py` | Comando 'svc scan' para el Python CLI. | scan() | `svc_py.config`, `svc_py.ui` | — |
| `svc_py/config.py` | Configuración centralizada del CLI. | — | — | `svc_py/commands/backup.py`, `svc_py/commands/catalog.py`, `svc_py/commands/codemap.py`, `svc_py/commands/compose.py`, … (+5) |
| `svc_py/core/__init__.py` | Core modules: discovery and docker interaction. | — | — | — |
| `svc_py/core/bash_bridge.py` | Puente entre Python CLI y bash CLI (svc.sh). | _svc_sh_path(), _build_env(), svc(), svc_output(), svc_passthrough(), svc_check(), svc_list_services(), is_svc_sh_available() | `svc_py.config`, `svc_py.core.discovery` | `svc_py/app.py` |
| `svc_py/core/discovery.py` | Detección de servicios Docker Compose. | svc_list(), svc_compose_file(), svc_dir(), service_exists() | `svc_py.config` | `svc_py/app.py`, `svc_py/commands/backup.py`, `svc_py/commands/catalog.py`, `svc_py/commands/compose.py`, … (+5) |
| `svc_py/core/docker.py` | Docker SDK nativo + compose subprocess. | _get_client(), compose_run(), compose_output(), compose_passthrough(), docker_run(), is_service_running(), get_container_ids(), container_inspect(), get_container_stats(), get_container_info(), list_all_containers(), get_networks(), … (+1) | — | `svc_py/app.py`, `svc_py/commands/backup.py`, `svc_py/commands/compose.py`, `svc_py/commands/docker.py`, … (+3) |
| `svc_py/ui.py` | Rich helpers para el CLI. | error(), warn(), success(), info(), header(), status_dot(), health_colored(), restart_colored(), service_table(), confirm_action() | — | `svc_py/app.py`, `svc_py/commands/backup.py`, `svc_py/commands/catalog.py`, `svc_py/commands/codemap.py`, … (+6) |

## `tests/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `tests/__init__.py` | — | — | — | — |
| `tests/conftest.py` | Fixtures compartidos para la suite de tests del agente NAS. | isolate_memory(), mock_safe_run(), populated_memory() | — | — |
| `tests/simulate_install_docker.sh` | Simulador seguro de install_docker.sh. | cleanup(), fail(), pass(), assert_contains(), assert_status(), write_os_release(), run_installer(), run_installer_from_env(), test_help(), test_valid_debian(), test_dry_run_env(), test_invalid_os(), … (+2) | — | — |
| `tests/test_classify.py` | Tests para la clasificación de queries (prompt dinámico). | class TestDiagnostico (test_revisar, test_error, test_no_funciona, test_502, test_por_que), class TestCreacion (test_instalar, test_crear, test_quiero), class TestBackup (test_backup, test_restaurar, test_respaldo), class TestAdmin (test_restart, test_detener, test_actualizar, test_start), class TestSistema (test_servicios, test_disco, test_puertos), class TestIdentidad (test_modelo, test_quien_eres), class TestMemoria (test_recuerda, test_skill, test_que_sabes), class TestGeneral (test_hola, test_siempre_tiene_identidad, test_general_tiene_formato) | `agent.nas_agent` | — |
| `tests/test_compose_generation.py` | Tests para generación y validación de compose. | class TestComposeManagerSanitize (test_valor_normal, test_strip_espacios, test_path_traversal_falla, test_backslash_falla, test_control_chars_falla, test_backtick_falla), class TestComposeManagerAnchors (test_fallback_anchors_contiene_bloques, test_load_compose_base_anchors_retorna_string), class TestComposeManagerRules (test_load_rules_retorna_dict) | `agent.core.compose_manager`, `agent.tools._shell` | — |
| `tests/test_daemon.py` | Tests para el daemon (scheduler). | class TestScheduler (test_task_executes, test_stop_is_graceful, test_error_in_task_doesnt_crash, test_multiple_tasks) | `agent.daemon` | — |
| `tests/test_memory.py` | Tests para el sistema de memoria (MemoryManager). | class TestEnsureInitialized (test_creates_files, test_idempotent), class TestAddToMemory (test_add_leccion, test_add_entorno, test_invalid_category, test_too_long, test_duplicate_detection, test_updates_timestamp), class TestRecall (test_recall_from_memory, test_recall_from_skills, test_recall_from_sessions, test_recall_not_found, test_recall_short_query), class TestAddSkill (test_add_skill_success, test_add_duplicate_skill, test_skill_counter_increments), class TestUpdateUserModel (test_add_new_key, test_update_existing_key), class TestSaveSession (test_save_session), class TestCuration (test_trim_sessions, test_prune_old_entries), class TestMemoryStats (test_stats_structure, test_stats_with_data) | `agent.core._result`, `agent.core.memory` | — |
| `tests/test_phase3.py` | Tests para Phase 3: plugins, event bus, scheduler, cache. | class TestEventBus (test_emit_y_handler, test_wildcard_handler, test_global_handler, test_off_desregistra, test_history, test_last_events_filtrado), class TestCache (test_set_get, test_ttl_expiry, test_invalidate, test_invalidate_prefix, test_stats, test_clear), class TestBasePlugin (test_plugin_basico, test_plugin_con_schedule, test_plugin_con_event), class TestPluginLoader (test_load_plugin_manual, test_unload_plugin, test_summary) | `agent.cache.store`, `agent.events.bus`, `agent.plugins.base`, `agent.plugins.loader` | — |
| `tests/test_result.py` | Tests para ToolResult dataclass. | class TestToolResult (test_ok_basico, test_error_basico, test_warn_basico, test_ok_con_data, test_ok_con_suggestions, test_ok_con_elapsed), class TestTimer (test_timer_mide_tiempo, test_timer_zero_sin_sleep) | `agent.core._result` | — |
| `tests/test_tool_result.py` | Tests para la dataclass ToolResult. | class TestToolResultOk (test_ok_is_success, test_ok_str, test_ok_data, test_ok_suggestions), class TestToolResultError (test_error_not_success, test_error_str), class TestToolResultWarn (test_warn_is_success), class TestToolResultSerialization (test_to_dict, test_repr), class TestTimer (test_timer_measures_time) | `agent.core._result` | — |
| `tests/test_validation.py` | Tests para validación de inputs (seguridad). | class TestValidateServiceName (test_valid_simple, test_valid_with_dash, test_valid_with_numbers, test_valid_underscore, test_path_traversal, test_empty_name) | `agent.tools._shell` | — |

## `ui/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `ui/setup.py` | TUI de primera instalación para nas-dotfiles | run_cmd(), detect_system(), check_mark(), show_header(), show_system_info(), ask_configuration(), show_summary(), execute_installation(), _step_copy(), _step_bashrc_user(), _step_user_conf(), _step_bashrc_root(), … (+5) | — | — |

## `uninstall.sh/`

| Archivo | Qué hace | Símbolos | Conexiones | Usado por |
|---|---|---|---|---|
| `uninstall.sh` | Revierte la instalación de nas-dotfiles | _remove_if_symlink() | — | — |
