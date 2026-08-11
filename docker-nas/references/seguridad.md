# Seguridad — referencia completa

## Principios

1. **shell=False** siempre — previene inyección de comandos
2. **Validar nombres** antes de construir rutas — previene path traversal
3. **Modo read-only** para bloquear acciones destructivas
4. **Auditoría completa** de todas las invocaciones de tools
5. **Dual dry-run** — nivel prompt + nivel código

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

Sanitización automática: args con keys sensibles (`password`, `token`, `secret`, `api_key`) se muestran como `***`.

Control:
- `NAS_AGENT_AUDIT=1` (default) — habilitado
- `NAS_AGENT_AUDIT=0` — deshabilitado

Fallback: si `/docker/backups/` no es escribible → `~/.nas-agent-audit.log`

---

## Seguridad del shell (bash)

### rm/cp/mv seguros
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
- Verifica si el paquete ya existe
- Verifica si existe en apt-cache
- Solo entonces ejecuta `apt install`

### svc restore — doble confirmación
- Muestra qué se va a sobreescribir
- Pide `[y/N]` explícito
- Detiene el servicio antes de restaurar

---

## Protección del agente (tools Python)

### read_file_content — sanitiza .env
Si el archivo leído es `.env`, las líneas con keys sensibles se reemplazan:
```
API_KEY=***REDACTED***
```
Keys detectadas: `password`, `secret`, `token`, `api_key`, `key`, `pass`, `user`, `login`, `credential`, `auth`, `private`

### list_files — rutas permitidas
Solo permite listar dentro de:
- `/docker`
- `/home/<user>` (la ruta configurada)
- `/nas-dotfiles`
- `/tmp`
- `/var/log`
- `/opt`

Rutas bloqueadas explícitamente: `/etc/shadow`, `/proc`, `/sys`, `/dev`

---

## .gitignore — protección de secretos

Archivos que NUNCA deben subirse a GitHub:
```gitignore
.env.agent          # API keys del agente
.env                # Secretos de servicios
.config/user.conf   # Datos personales (username, home path)
*.log               # Logs dinámicos
.nas-agent/         # Cache y sesiones runtime
```

---

## Resumen de mecanismos

| Amenaza | Protección | Ubicación |
|---------|-----------|-----------|
| Inyección de comandos | `safe_run(list, shell=False)` | `_shell.py` |
| Path traversal | `validate_service_name()` | `_shell.py` |
| LLM ejecuta acción destructiva | `readonly_guard()` | `_shell.py` |
| Ejecución accidental | Dual dry-run | Prompt + `safe_run()` |
| Leak de credenciales | Sanitización en `read_file_content` | `system_tools.py` |
| Audit trail | JSON Lines log | `_audit.py` |
| Secretos en Git | `.gitignore` + `.env.agent` | Raíz del repo |
| Backup accidental | Doble confirmación en restore | `backup.sh` |
