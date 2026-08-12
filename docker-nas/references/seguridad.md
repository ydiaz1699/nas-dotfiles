# Seguridad y Variables — referencia completa

## Mecanismos de seguridad

| Mecanismo | Qué protege |
|-----------|-------------|
| `safe_run(list, shell=False)` | Inyección shell (nunca f-strings en comandos) |
| `validate_service_name()` | Path traversal, inyección via nombres |
| `validated_service_path()` | Escape de DOCKER_BASE |
| `readonly_guard()` | LLM ejecutando acciones destructivas |
| Dual dry-run (prompt + código) | Ejecución accidental |
| Audit log (JSON Lines) | Trazabilidad de todas las acciones |
| Backup de .bashrc antes de sed | Pérdida de configuración |
| Sanitización YAML en create_service | Inyección de contenido |
| `.env` permisos 600 | Exposición de secretos |
| Credential sanitization en read_file_content | Credenciales en exports al LLM |

---

## safe_run() — ejecución segura

Ubicación: `agent/tools/_shell.py`

```python
safe_run(
    args: list[str],     # NUNCA string con shell=True
    timeout: int = 120,
    check: bool = False,
    cwd: Path = None,
) -> str
```

Comportamiento:
- **Normal:** ejecuta subprocess con `shell=False`, retorna stdout
- **Dry-run** (`NAS_AGENT_DRYRUN=1`): NO ejecuta, retorna `[DRY-RUN] Se ejecutaría: $ comando`
- **Timeout:** retorna `ERROR: Comando excedió el timeout de Xs`
- **Error:** agrega stderr con ⚠️ al output

**Regla:** NUNCA usar `subprocess.run()` directo en tools. Siempre `safe_run()`.

---

## validate_service_name() — anti path-traversal

```python
validate_service_name(name: str) -> str  # raises InvalidServiceName
```

Reglas:
- Solo: `[a-z0-9._-]`
- Debe empezar con alfanumérico
- Máximo 64 caracteres
- Bloquea: `..`, `/`, `\`
- Nombres reservados: `.`, `..`, `cli`, `backups`, `lost+found`, `proc`, `sys`, `dev`, `tmp`, `etc`, `root`

### validated_service_path()

```python
validated_service_path(name: str) -> Path
```

Valida nombre + verifica que `(DOCKER_BASE / name).resolve()` no escape de `/docker/`.

---

## readonly_guard() — protección de tools destructivas

```python
readonly_guard(tool_name: str) -> Optional[str]  # None = permitido
```

Activar: `export NAS_AGENT_READONLY=1`

Tools bloqueadas (`_DESTRUCTIVE_TOOLS`):
- `service_stop`
- `service_update`
- `create_service`
- `restore_service`
- `backup_service`

---

## Modo Dry-Run

Activar: `export NAS_AGENT_DRYRUN=1`

Dos niveles de protección:
1. **Prompt:** el system prompt incluye instrucción de solo mostrar plan
2. **Código:** `safe_run()` intercepta ANTES de ejecutar

Desactivar: `unset NAS_AGENT_DRYRUN`

---

## Audit Log

Ubicación: `/docker/backups/agent_audit.log` (o `$NAS_AGENT_AUDIT_LOG`)
Formato: **JSON Lines** (una entrada JSON por línea)

Cada entrada registra:
```json
{
  "ts": "2026-08-11T15:30:00+00:00",
  "tool": "service_restart",
  "args": {"service": "nextcloud"},
  "result_preview": "✅ Servicio reiniciado...",
  "duration_ms": 1234.5,
  "success": true
}
```

Sanitización automática: args con keys sensibles (`password`, `token`, `secret`, `api_key`, `key`) se muestran como `***`.

Control:
- `NAS_AGENT_AUDIT=1` (default) — habilitado
- `NAS_AGENT_AUDIT=0` — deshabilitado

Fallback: si `/docker/backups/` no es escribible → `~/.nas-agent-audit.log`

Consultar: `get_session_summary(last_n=50)` retorna resumen legible.

---

## Seguridad del shell (bash)

### rm/cp/mv seguros (TTY-safe)
Las funciones en `aliases.sh` aplican `-iv` SOLO en terminal interactiva:
```bash
rm() {
  if [[ -t 0 && -t 1 ]]; then
    command rm -iv "$@"
  else
    command rm "$@"   # scripts/pipes: sin confirmación
  fi
}
```

### instal — no ejecuta sin verificar
- Verifica si el paquete ya existe → skip
- Verifica si existe en apt-cache → error limpio
- Solo entonces ejecuta `apt install`

### svc restore — doble confirmación
- Muestra qué se va a sobreescribir
- Pide `[y/N]` explícito
- Detiene el servicio antes de restaurar
- Ofrece reiniciar después

---

## Protección del agente (tools Python)

### read_file_content — sanitiza .env
Si el archivo leído es `.env`, las líneas con keys sensibles se reemplazan:
```
API_KEY=***REDACTED***
```
Keys detectadas: `password`, `secret`, `token`, `cookie`, `key`, `pass`,
`user`, `username`, `login`, `credential`, `auth`, `api_key`, `apikey`, `private`

Excepciones que NO se sanitizan: `allow_anonymous`, `allow_user`

### list_files — rutas permitidas
Solo permite listar dentro de:
- `/docker`
- `/home/<user>` (la ruta configurada)
- `/nas-dotfiles`
- `/tmp`
- `/var/log`
- `/opt`

Rutas bloqueadas explícitamente: `/etc/shadow`, `/proc`, `/sys`, `/dev`

### read_file_content — límites
- Máximo 512 KB por archivo (previene lectura de binarios grandes)
- Máximo 200 líneas por lectura
- Mismas rutas permitidas que list_files

---

## .gitignore — protección de secretos

Archivos que NUNCA deben subirse a GitHub:
```gitignore
.env.agent          # API keys del agente
.env                # Secretos de servicios
.env.*              # Variantes
!.env.example       # Templates sí
.config/user.conf   # Datos personales (username, home path)
*.log               # Logs dinámicos
.nas-agent/         # Cache y sesiones runtime
__pycache__/        # Bytecode Python
*.pyc
.venv/              # Virtual environment
*.bak.*             # Backups del instalador
.kiro/              # Config IDE local
```

---

## Modos de seguridad

| Variable | Default | Efecto |
|----------|---------|--------|
| `NAS_AGENT_READONLY` | `0` | Bloquea tools destructivas (hard guard en código) |
| `NAS_AGENT_DRYRUN` | `0` | No ejecuta nada (soft: prompt + hard: safe_run intercepta) |
| `NAS_AGENT_AUDIT` | `1` | Escribe audit log de cada tool call |

---

## Variables de entorno — referencia completa

### Paths y proyecto

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_DOTFILES` | `/nas-dotfiles` | Ruta fija al código |
| `DOCKER_BASE` | `/docker` | Ruta a datos de servicios |
| `NAV_HOME` | `/home/aadm` | Home del usuario |
| `NAV_VAR` | `aadm` | Variable exportada ($aadm) |
| `NAV_CMD` | `adm` | Comando de navegación |
| `NAS_CLI` | `bash` | CLI de svc: `bash` o `python` |

### Agente

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | `gemini` | Provider: gemini/bedrock/ollama |
| `NAS_AGENT_MODEL_ID` | (auto) | Override modelo específico |
| `GOOGLE_API_KEY` | — | API key Gemini |
| `AWS_REGION` | `us-east-1` | Región Bedrock |
| `NAS_AGENT_THINKING_BUDGET` | `10000` | Tokens razonamiento (Bedrock) |
| `OLLAMA_HOST` | `http://localhost:11434` | Host Ollama |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos antes de auto-reset |
| `NAS_AGENT_SESSIONS_DIR` | `~/.nas-agent/sessions` | Directorio sesiones |
| `NAS_AGENT_MEMORY_DIR` | `agent/memory/` | Directorio memoria |
| `NAS_AGENT_AUDIT_LOG` | `/docker/backups/agent_audit.log` | Ruta audit log |
| `NAS_AGENT_LOG_LEVEL` | `INFO` | Nivel del daemon |

---

## Convenciones del proyecto

- **Idioma del código**: inglés
- **Idioma de UI/mensajes**: español
- **Commits**: conventional commits (feat:, fix:, security:, docs:)
- **Python**: 3.10+, type hints, ruff
- **Bash**: set -e en scripts, funciones con prefijo
- **Tests**: pytest, coverage en `agent/`
- **Puertos nuevos**: 8100-8999
- **Puertos reservados**: 22, 53, 80, 443 (nunca)
- **Secrets**: en `.env`, nunca inline en compose
- **Restart policy**: `unless-stopped`
- **Nombres servicio**: `^[a-z0-9][a-z0-9._-]{0,63}$`
- **Compose file**: `compose.yml` (preferido sobre docker-compose.yml)
- **Network**: redes externas compartidas (iot_net, db_net, proxy)

---

## Resumen de mecanismos

| Amenaza | Protección | Ubicación |
|---------|-----------|-----------|
| Inyección de comandos | `safe_run(list, shell=False)` | `_shell.py` |
| Path traversal | `validate_service_name()` | `_shell.py` |
| LLM ejecuta acción destructiva | `readonly_guard()` | `_shell.py` |
| Ejecución accidental | Dual dry-run | Prompt + `safe_run()` |
| Leak de credenciales al LLM | Sanitización en `read_file_content` | `system_tools.py` |
| Audit trail | JSON Lines log | `_audit.py` |
| Secretos en Git | `.gitignore` + `.env.agent` chmod 600 | Raíz del repo |
| Backup accidental | Doble confirmación en restore | `backup.sh` |
| Pérdida de .bashrc | Backup antes de sed en install.sh | `install.sh` |
| Inyección YAML | Sanitización en create_service | `compose_tools.py` |
