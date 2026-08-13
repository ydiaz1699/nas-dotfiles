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
| Credential sanitization | Credenciales en exports |

## Modos de seguridad

| Variable | Default | Efecto |
|----------|---------|--------|
| `NAS_AGENT_READONLY` | `0` | Bloquea tools destructivas (hard guard) |
| `NAS_AGENT_DRYRUN` | `0` | No ejecuta nada (soft: prompt + hard: safe_run) |
| `NAS_AGENT_AUDIT` | `1` | Escribe audit log |

## Variables de entorno — referencia completa

### Paths y proyecto

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_DOTFILES` | `/nas-dotfiles` | Ruta al código (configurable) |
| `DOCKER_BASE` | `/docker` | Ruta a datos de servicios (= `$dkco`) |
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
| `NAS_AGENT_AUDIT_LOG` | `$DOCKER_BASE/backups/agent_audit.log` | Ruta audit log |

## Convenciones del proyecto

- **Idioma del código**: inglés
- **Idioma de UI/mensajes**: español
- **Commits**: conventional commits (feat:, fix:, security:, docs:)
- **Python**: 3.10+, type hints, ruff
- **Bash**: set -e en scripts, funciones con prefijo
- **Tests**: pytest, coverage en `agent/`
- **Puertos nuevos**: 8100-8999
- **Puertos reservados**: 22, 53, 80, 443 (nunca)
- **Secrets**: en `.env`, nunca inline
- **Restart policy**: `unless-stopped`
- **Nombres servicio**: `^[a-z0-9][a-z0-9._-]{0,63}$`
