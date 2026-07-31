"""
nas_agent.py — Agente inteligente para administración de NAS/Homelab

Usa Strands Agents SDK con auto-detección de servicios Docker,
catálogo local + web search como fallback, y reglas estandarizadas
para crear, diagnosticar y administrar servicios en el NAS.

Proveedores soportados:
    - Google Gemini (default) — gemini-2.5-flash (barato, rápido)
    - Amazon Bedrock — Claude Sonnet 4 (mejor tool-use, más caro)
    - Ollama (local, gratis) — llama3.1 o cualquier modelo

Uso:
    # Modo interactivo (usa Gemini por defecto)
    python -m agent.nas_agent

    # Con query directa
    python -m agent.nas_agent "¿Qué servicios están caídos?"

    # Con Bedrock (Claude)
    NAS_AGENT_MODEL=bedrock python -m agent.nas_agent "..."

    # Con Ollama local
    NAS_AGENT_MODEL=ollama python -m agent.nas_agent "..."

    # Gestión de sesión (memoria entre invocaciones)
    python -m agent.nas_agent --new "crear servicio X"   # Nueva sesión limpia
    python -m agent.nas_agent --status                   # Ver info de sesión actual
    python -m agent.nas_agent --clear                    # Borrar sesión y empezar limpio

Requisitos:
    pip install 'strands-agents[gemini]' strands-agents-tools python-frontmatter pyyaml
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

from strands import Agent
from strands.session.file_session_manager import FileSessionManager

from agent.tools import ALL_TOOLS

# ─────────────────────────────────────────────────────────────────────────────
# Cargar variables de .env.agent (API keys, config del agente)
# ─────────────────────────────────────────────────────────────────────────────

def _load_env_agent():
    """Carga variables de entorno desde .env.agent si existe."""
    env_file = Path(__file__).resolve().parent.parent / ".env.agent"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        # Saltar comentarios y líneas vacías
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            # No sobreescribir si ya está definida en el entorno
            if key and key not in os.environ:
                os.environ[key] = value

_load_env_agent()

# ─────────────────────────────────────────────────────────────────────────────
# Configuración de rutas
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
CATALOG_DIR = BASE_DIR / "catalog"
RULES_FILE = CATALOG_DIR / "_rules.md"

# ─────────────────────────────────────────────────────────────────────────────
# Gestión de sesión — Persistencia de conversación entre invocaciones
# ─────────────────────────────────────────────────────────────────────────────

# Directorio donde se guardan las sesiones del agente
SESSIONS_DIR = Path(os.environ.get(
    "NAS_AGENT_SESSIONS_DIR",
    str(Path.home() / ".nas-agent" / "sessions")
))

# Timeout de sesión: si pasan más de N minutos sin actividad, se auto-resetea
SESSION_TIMEOUT_MIN = int(os.environ.get("NAS_AGENT_SESSION_TIMEOUT", "30"))

# ID de sesión por defecto (se usa una sesión fija para mantener contexto)
DEFAULT_SESSION_ID = "nas-agent-main"


def _get_session_metadata_path() -> Path:
    """Ruta al archivo de metadatos de la sesión actual."""
    return SESSIONS_DIR / "session_metadata.json"


def _read_session_metadata() -> dict:
    """Lee los metadatos de la sesión actual."""
    meta_path = _get_session_metadata_path()
    if meta_path.exists():
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_session_metadata(meta: dict) -> None:
    """Guarda metadatos de la sesión."""
    meta_path = _get_session_metadata_path()
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _session_is_expired(meta: dict) -> bool:
    """Verifica si la sesión ha expirado por timeout."""
    last_active = meta.get("last_active", 0)
    if last_active == 0:
        return False
    elapsed_min = (time.time() - last_active) / 60
    return elapsed_min > SESSION_TIMEOUT_MIN


def _clear_session() -> None:
    """Elimina todos los datos de sesión para empezar limpio."""
    if SESSIONS_DIR.exists():
        shutil.rmtree(SESSIONS_DIR)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _get_session_manager(force_new: bool = False) -> FileSessionManager:
    """Obtiene o crea el session manager.

    Args:
        force_new: Si True, borra la sesión existente y crea una nueva.

    Returns:
        FileSessionManager configurado para persistir conversaciones.
    """
    meta = _read_session_metadata()

    # Auto-reset si la sesión expiró o si se pide nueva
    if force_new or _session_is_expired(meta):
        _clear_session()
        meta = {}

    # Actualizar timestamp de actividad
    meta["last_active"] = time.time()
    meta["session_id"] = DEFAULT_SESSION_ID
    meta["turn_count"] = meta.get("turn_count", 0) + 1
    _write_session_metadata(meta)

    return FileSessionManager(
        session_id=DEFAULT_SESSION_ID,
        storage_dir=str(SESSIONS_DIR),
    )


# ─────────────────────────────────────────────────────────────────────────────
# System Prompt del agente NAS
# ─────────────────────────────────────────────────────────────────────────────

THINKING_PROMPT = """
# RAZONAMIENTO INTERNO

Antes de responder o usar herramientas, razona:

1. CLASIFICAR: ¿Qué tipo de tarea es?
   - diagnóstico → cargar contexto de diagnóstico
   - crear servicio → cargar contexto de creación
   - administrar (start/stop/restart/update/backup) → acción directa
   - información/consulta → responder directamente
2. EVALUAR: ¿Necesito info antes de actuar? ¿Es seguro o destructivo?
3. PLANIFICAR: ¿Qué herramientas y en qué orden?
4. EJECUTAR: Actuar y reportar resultado.
"""

SYSTEM_PROMPT = """
# MODO DE OPERACIÓN: EJECUTIVO

Eres un agente que ACTÚA, no un asistente que sugiere.

## Principio fundamental
- Operaciones de LECTURA (logs, compose, health, diagnóstico): EJECUTAR INMEDIATAMENTE.
  NO preguntar "¿quieres que lea el compose?". Simplemente llámalo.
- Operaciones SEGURAS (start, restart, update): EJECUTAR directamente.
  NO preguntar "¿quieres que reinicie?". Hazlo y reporta el resultado.
- Operaciones DESTRUCTIVAS (stop, restore, delete): PRIMERO explica qué vas a hacer,
  LUEGO pide confirmación antes de ejecutar.

## Cadena de acción para diagnóstico
Cuando el usuario dice "revisar X", "diagnosticar X", "arreglar X":

1. EJECUTAR troubleshoot(service) — SIN preguntar
2. EJECUTAR service_logs(service, lines=50) — SIN preguntar
3. EJECUTAR read_compose(service) — SIN preguntar
4. Analizar TODOS los resultados juntos
5. Presentar: causa raíz + plan de acción concreto
6. Si la solución es segura (restart, update): EJECUTAR directamente
7. Si la solución es destructiva (stop + borrar datos): pedir confirmación

## Ejemplo correcto de diagnóstico
```
Usuario: "revisar tasmoadmin"
Agente:
  1. Llama troubleshoot("tasmoadmin")     ← ejecuta, no pregunta
  2. Llama service_logs("tasmoadmin", 50) ← ejecuta, no pregunta
  3. Llama read_compose("tasmoadmin")     ← ejecuta, no pregunta
  4. Analiza: "nginx.conf corrupto, falta events section"
  5. Propone: "Voy a hacer service_update() para recrear el contenedor"
  6. Ejecuta service_update("tasmoadmin") ← seguro, no pregunta
  7. Reporta resultado
```

## Lo que NUNCA debes hacer
- ❌ "¿Quieres que lea el compose?"
- ❌ "¿Prefieres que revise los logs?"
- ❌ "¿Puedo ejecutar troubleshoot?"
- ❌ Mostrar comandos docker/svc para que el usuario ejecute manualmente

## Lo que SÍ debes hacer
- ✅ Ejecutar TODAS las herramientas de lectura inmediatamente
- ✅ Encadenar varias tools en una sola respuesta
- ✅ Presentar el resultado final con la causa raíz identificada
- ✅ Ejecutar la solución si es segura (restart, update, start)
- ✅ Solo preguntar antes de: stop, restore, borrar datos

## Reglas de confirmación
SOLO pedir confirmación para estas acciones específicas:
- service_stop() — detener servicio
- restore_service() — restaurar backup (sobreescribe datos)

TODO lo demás se ejecuta directamente:
- service_restart() → EJECUTAR SIN PREGUNTAR
- service_update() → EJECUTAR SIN PREGUNTAR (es seguro, no pierde datos)
- service_start() → EJECUTAR SIN PREGUNTAR
- read_compose() → EJECUTAR SIN PREGUNTAR
- troubleshoot() → EJECUTAR SIN PREGUNTAR
- service_logs() → EJECUTAR SIN PREGUNTAR
- scan_ports() → EJECUTAR SIN PREGUNTAR

⚠️ service_update() y service_restart() SON SEGUROS. NO preguntes.

# CONTEXTO DE CONVERSACIÓN

Esta conversación tiene MEMORIA PERSISTENTE entre invocaciones.
- Si el usuario dice "sí", "hazlo", "reiniciar" SIN especificar servicio,
  SIEMPRE revisa mensajes anteriores para identificar el contexto.
- Trata los mensajes cortos como continuación natural.
- Solo pide aclaración si genuinamente no hay contexto previo relevante.

# CONTEXTO DEL NAS — Comandos del shell (NO son tus tools)

- `instal <paquete>` — APT del sistema. NO es un servicio Docker.
- `svc <cmd> <servicio>` — CLI de Docker del usuario
- `bat`, `nas`, `off`, `restart`, `adm`, `dk` — comandos del usuario

REGLA: Si dice "instal git" → es apt, NO Docker.
  Correcto: "Ejecuta `instal git` en tu terminal"
  Incorrecto: Crear servicio Docker de Gitea

# MISIÓN

Eres **NAS Agent**, experto en administración de servidores NAS/Homelab con Docker.

# HERRAMIENTAS DISPONIBLES

## Descubrimiento
- `list_services()` → Servicios Docker con estado
- `scan_compose(service)` → Analizar compose
- `auto_catalog(service)` → Generar ficha de catálogo
- `bulk_discover()` → Descubrir y catalogar todos
- `export_service(service)` → Exportar config al catálogo

## Sistema
- `scan_ports()` → Puertos en uso + disponibles
- `disk_usage()` → Uso de disco con alertas
- `memory_info()` → RAM/Swap con top procesos
- `network_info()` → Interfaces, IPs, redes Docker
- `list_files(path, max_depth)` → Listar archivos/carpetas
- `read_file_content(path, lines)` → Leer archivo de texto

## Docker
- `service_start(service)` → Levantar (seguro)
- `service_stop(service, confirm)` → Detener (requiere confirm="si")
- `service_restart(service)` → Reiniciar (seguro)
- `service_update(service)` → Pull + recrear (seguro)
- `service_logs(service, lines)` → Ver logs

## Compose
- `create_service(name, image, port, ...)` → Crear servicio nuevo
- `validate_compose(service)` → Validar contra reglas
- `read_compose(service)` → Leer compose actual

## Backup
- `backup_service(service)` → Crear backup
- `restore_service(service, confirm)` → Restaurar (requiere confirm="si")
- `list_backups()` → Listar backups

## Búsqueda
- `search_service_info(name)` → Buscar en internet

## Diagnóstico
- `service_health()` → Dashboard de salud
- `port_conflicts()` → Detectar conflictos de puertos
- `troubleshoot(service)` → Diagnóstico completo

## REGLA CRÍTICA: SIEMPRE USAR TUS HERRAMIENTAS

NUNCA muestres comandos Docker crudos. SIEMPRE usa tools:

Mapeo de acciones → herramientas:
- Detener → service_stop(service, confirm="si")
- Levantar → service_start(service)
- Reiniciar → service_restart(service)
- Actualizar → service_update(service)
- Ver logs → service_logs(service, lines=50)
- Diagnóstico → troubleshoot(service)
- Ver compose → read_compose(service)
- Backup → backup_service(service)
- Restaurar → restore_service(service, confirm="si")

# REGLAS

1. SIEMPRE responder en ESPAÑOL
2. Ser conciso (5-8 líneas) — el usuario administra desde terminal
3. Cuando no sepas algo, DILO — no inventes
4. Emojis de estado: ✅ ok, ⚠️ advertencia, 🔴 error
5. Tablas markdown para datos tabulares
6. Terminar con siguiente paso sugerido

# ACTIVACIÓN

Cuando recibas el primer mensaje DE UNA SESIÓN NUEVA (sin historial previo):
🖥️ NAS Agent listo. ¿En qué te ayudo?

Si ya hay mensajes anteriores, responder directamente sin bienvenida.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Contexto dinámico — se inyecta según el tipo de query
# ─────────────────────────────────────────────────────────────────────────────

CONTEXT_DIAGNOSTICO = """
# CONTEXTO: DIAGNÓSTICO

## Cadena completa de diagnóstico
1. troubleshoot(service) + service_logs(service, 50) — INMEDIATO
2. read_compose(service) si necesitas ver config — INMEDIATO
3. Analizar output REAL de los logs → buscar [emerg], [error], "fatal", "failed"
4. NUNCA responder solo con "unhealthy" sin haber leído logs
5. Identificar ERROR ESPECÍFICO (ej: "nginx: [emerg] no events section")
6. EJECUTAR solución si es segura, o proponer plan si es destructiva

## Patrones de error comunes
- OOMKilled → memory_info() + revisar limits en compose
- Restart loop → service_logs() últimas 100 líneas, buscar crash
- Port conflict → port_conflicts() + scan_ports()
- Permission denied → verificar user/group en compose
- Connection refused → verificar network + depends_on
"""

CONTEXT_CREACION = """
# CONTEXTO: CREACIÓN DE SERVICIOS

## Flujo completo
1. Verificar catálogo local (agent/catalog/services/)
2. Si NO existe → search_service_info() en internet
3. Verificar deps: read_file_content("/nas-dotfiles/logs/packages.txt")
   - TLS/certs → openssl
   - NFS → nfs-common
   - GPU → nvidia-container-toolkit
   - USB (zigbee) → usbutils
4. Si falta algo: "Ejecuta `instal <paquete>` primero"
   NO ejecutes instal tú — es un comando de terminal del usuario.
5. scan_ports() → verificar puertos disponibles
6. create_service() aplicando reglas
7. validate_compose()
8. Ofrecer: "¿Lo levanto ahora?"
9. auto_catalog() para futuras referencias

## Reglas de configuración
- Puertos reservados: 22, 53, 80, 443 — NUNCA asignar
- Rango servicios nuevos: 8100-8999
- Restart policy: SIEMPRE unless-stopped
- Secrets: SIEMPRE en .env, NUNCA inline en compose
- Healthcheck: agregar si expone HTTP
- Formato: seguir _rules.md del catálogo
"""

CONTEXT_BACKUP = """
# CONTEXTO: BACKUP Y RESTAURACIÓN

## Backup
- backup_service(service) → exporta volúmenes nombrados a tar.gz
- Se guardan en /docker/backups/ con timestamp
- list_backups() para ver backups disponibles

## Restauración
- restore_service(service, confirm="si") → SIEMPRE pedir confirmación
- Sobreescribe datos actuales — operación DESTRUCTIVA
- Sugerir backup previo antes de restaurar
"""

CONTEXT_ADMIN = """
# CONTEXTO: ADMINISTRACIÓN DE SERVICIOS

## Acciones seguras (ejecutar directamente)
- service_start() — levantar servicio detenido
- service_restart() — reiniciar (no pierde datos)
- service_update() — pull imagen nueva + recrear contenedor

## Acciones destructivas (pedir confirmación)
- service_stop(confirm="si") — detener servicio
- restore_service(confirm="si") — sobreescribir con backup

## Actualización masiva
- Usar service_update() servicio por servicio
- O indicar al usuario: "svc update-all" para todos de golpe
"""


def _classify_query(query: str) -> str:
    """Clasifica el tipo de query para inyectar contexto dinámico."""
    q = query.lower()

    # Diagnóstico
    if any(w in q for w in [
        "revisar", "diagnosticar", "problema", "error", "falla", "caído",
        "no funciona", "unhealthy", "reiniciar", "arreglar", "lento",
        "502", "503", "timeout", "crash", "log", "por qué",
    ]):
        return "diagnostico"

    # Creación
    if any(w in q for w in [
        "instalar", "crear", "nuevo servicio", "quiero", "montar",
        "configurar", "deployer", "levantar nuevo", "agregar",
    ]):
        return "creacion"

    # Backup
    if any(w in q for w in [
        "backup", "respaldo", "restaurar", "restore", "exportar",
    ]):
        return "backup"

    # Administración
    if any(w in q for w in [
        "start", "stop", "restart", "update", "detener", "levantar",
        "actualizar", "parar", "iniciar",
    ]):
        return "admin"

    # General / consulta
    return "general"


def _get_dynamic_context(query: str) -> str:
    """Retorna el contexto dinámico según el tipo de query."""
    category = _classify_query(query)

    if category == "diagnostico":
        return CONTEXT_DIAGNOSTICO
    elif category == "creacion":
        return CONTEXT_CREACION
    elif category == "backup":
        return CONTEXT_BACKUP
    elif category == "admin":
        return CONTEXT_ADMIN
    else:
        return ""  # Consultas generales no necesitan contexto extra


# ─────────────────────────────────────────────────────────────────────────────
# Configurar modelo según entorno
# ─────────────────────────────────────────────────────────────────────────────


def get_model():
    """Selecciona el modelo según variable de entorno NAS_AGENT_MODEL.

    Proveedores:
        - gemini (default): Google Gemini Flash — barato, rápido, buen tool-use
        - bedrock: Amazon Bedrock con Claude Sonnet 4 — mejor tool-use, más caro
                   Incluye "interleaved thinking" para razonamiento profundo
        - ollama: Modelo local via Ollama (gratis, privado)

    Variables de entorno:
        - NAS_AGENT_MODEL: gemini | bedrock | ollama (default: gemini)
        - NAS_AGENT_MODEL_ID: Override del model_id
        - GOOGLE_API_KEY: API key de Google AI Studio (para Gemini)
        - AWS_REGION: Región para Bedrock (default: us-east-1)
        - NAS_AGENT_THINKING_BUDGET: Tokens para razonamiento interno de Claude
                                      (default: 10000, solo Bedrock)
        - OLLAMA_HOST: Host de Ollama (default: http://localhost:11434)
    """
    proveedor = os.environ.get("NAS_AGENT_MODEL", "gemini").lower()
    model_id_override = os.environ.get("NAS_AGENT_MODEL_ID")

    if proveedor == "gemini":
        from strands.models.gemini import GeminiModel

        model_id = model_id_override or "gemini-3.1-flash-lite"

        # API key: se lee de GOOGLE_API_KEY automáticamente si no se pasa
        api_key = os.environ.get("GOOGLE_API_KEY")
        client_args = {}
        if api_key:
            client_args["api_key"] = api_key

        return GeminiModel(
            model_id=model_id,
            client_args=client_args if client_args else None,
            params={
                "temperature": 0.3,
                "max_output_tokens": 4096,
            },
        )

    elif proveedor == "bedrock":
        from strands.models.bedrock import BedrockModel

        model_id = model_id_override or "us.anthropic.claude-sonnet-4-20250514-v1:0"

        # Extended thinking: Claude razona internamente antes de responder
        # budget_tokens controla cuántos tokens puede usar para "pensar"
        thinking_budget = int(os.environ.get("NAS_AGENT_THINKING_BUDGET", "10000"))

        return BedrockModel(
            model_id=model_id,
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            additional_request_fields={
                "anthropic_beta": ["interleaved-thinking-2025-05-14"],
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                },
            },
        )

    elif proveedor == "ollama":
        from strands.models.ollama import OllamaModel

        model_id = model_id_override or "llama3.1"
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return OllamaModel(model_id=model_id, host=host)

    else:
        raise ValueError(
            f"Proveedor '{proveedor}' no soportado.\n"
            f"Opciones: gemini, bedrock, ollama\n"
            f"Configura con: export NAS_AGENT_MODEL=<opción>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Crear el Agente
# ─────────────────────────────────────────────────────────────────────────────


def create_nas_agent(session_manager=None, query: str = "") -> Agent:
    """Crea y retorna el agente NAS configurado.

    Ensambla el prompt en 3 capas:
      1. THINKING_PROMPT — razonamiento antes de actuar
      2. SYSTEM_PROMPT — reglas completas, herramientas, comportamiento
      3. CONTEXTO DINÁMICO — inyectado según el tipo de query

    Args:
        session_manager: FileSessionManager para persistir conversación.
        query: La query del usuario (para determinar contexto dinámico).
    """
    model = get_model()

    # ── Identidad del modelo ───────────────────────────────────────────────
    proveedor = os.environ.get("NAS_AGENT_MODEL", "gemini").lower()
    model_id_override = os.environ.get("NAS_AGENT_MODEL_ID")

    if proveedor == "gemini":
        _model_id = model_id_override or "gemini-3.1-flash-lite"
        _model_info = f"Google Gemini ({_model_id})"
    elif proveedor == "bedrock":
        _model_id = model_id_override or "us.anthropic.claude-sonnet-4-20250514-v1:0"
        _model_info = f"Amazon Bedrock Claude ({_model_id})"
    elif proveedor == "ollama":
        _model_id = model_id_override or "llama3.1"
        _model_info = f"Ollama local ({_model_id})"
    else:
        _model_info = f"{proveedor} ({model_id_override or 'default'})"

    # ── Ensamblar prompt: Thinking + Identidad + System + Contexto ─────────
    identity_block = f"""# IDENTIDAD

Eres NAS Agent. Tu modelo es: {_model_info}
Provider: {proveedor}
Si te preguntan qué modelo eres, responde EXACTAMENTE: "{_model_info}".
No inventes otro nombre.
"""

    # Contexto dinámico según la query
    dynamic_context = _get_dynamic_context(query) if query else ""

    # Ensamblar las 3 capas
    system_prompt = THINKING_PROMPT + "\n" + identity_block + "\n" + SYSTEM_PROMPT
    if dynamic_context:
        system_prompt += "\n" + dynamic_context

    # Dry-run mode: agregar instrucciones que fuerzan plan-only
    if os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes"):
        system_prompt += """

# 🔒 MODO DRY-RUN ACTIVO

ESTÁS EN MODO DRY-RUN. NO EJECUTES NINGUNA HERRAMIENTA.

En vez de ejecutar, debes:
1. Analizar la petición del usuario
2. Explicar paso a paso qué harías (qué tools llamarías, con qué argumentos)
3. Mostrar el plan completo
4. Indicar riesgos
5. Preguntar si quiere que lo ejecute (necesita desactivar dry-run)

REPITO: NO llames ninguna herramienta. Solo muestra el plan.
"""

    agent_kwargs = dict(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=system_prompt,
        callback_handler=None,  # Desactivar output de Strands — nosotros renderizamos con Rich
        agent_id="nas-agent",   # ID fijo para que la sesión siempre apunte al mismo agente
    )

    if session_manager is not None:
        agent_kwargs["session_manager"] = session_manager

    agent = Agent(**agent_kwargs)

    return agent


# ─────────────────────────────────────────────────────────────────────────────
# Cambio de modelo desde CLI
# ─────────────────────────────────────────────────────────────────────────────

# Modelos disponibles para selección rápida
_AVAILABLE_MODELS = {
    "1": ("gemini", "gemini-2.5-flash", "Gemini 2.5 Flash (mejor razonamiento)"),
    "2": ("gemini", "gemini-3.5-flash-lite", "Gemini 3.5 Flash Lite (más requests/día)"),
    "3": ("gemini", "gemini-3.5-flash", "Gemini 3.5 Flash (balance)"),
    "4": ("gemini", "gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite (actual default)"),
    "5": ("gemini", "gemini-3.6-flash", "Gemini 3.6 Flash (más nuevo)"),
    "6": ("bedrock", "us.anthropic.claude-sonnet-4-20250514-v1:0", "Claude Sonnet 4 (Bedrock)"),
    "7": ("ollama", "llama3.1", "Ollama llama3.1 (local, gratis)"),
}


def _switch_model(args: list, use_rich: bool, console) -> None:
    """Cambia el modelo del agente y lo persiste en .env.agent."""
    args_copy = list(args)
    if "--model" in args_copy:
        args_copy.remove("--model")

    env_file = Path(__file__).resolve().parent.parent / ".env.agent"

    # Si se pasó un model_id directamente: agent --model gemini-2.5-flash
    if args_copy:
        model_id = args_copy[0]
        # Determinar provider
        if model_id.startswith("gemini") or model_id.startswith("gemma"):
            provider = "gemini"
        elif "anthropic" in model_id or "claude" in model_id:
            provider = "bedrock"
        else:
            provider = "ollama"
        _persist_model(env_file, provider, model_id)
        if use_rich:
            console.print(f"  [green]✓[/green] Modelo cambiado a [bold cyan]{model_id}[/bold cyan] ({provider})")
            console.print(f"  [dim]Guardado en {env_file}[/dim]")
        else:
            print(f"✓ Modelo cambiado a {model_id} ({provider})")
        return

    # Si no se pasó argumento: mostrar menú de selección
    if use_rich:
        console.print()
        console.print("  [bold]Modelos disponibles:[/bold]\n")
        for key, (prov, mid, desc) in _AVAILABLE_MODELS.items():
            console.print(f"    [cyan]{key})[/cyan] {desc}")
            console.print(f"       [dim]{prov} / {mid}[/dim]")
        console.print()
        console.print("  [dim]También puedes escribir un model_id directamente:[/dim]")
        console.print("  [dim]  agent --model gemini-2.5-flash[/dim]\n")
    else:
        print("\nModelos disponibles:\n")
        for key, (prov, mid, desc) in _AVAILABLE_MODELS.items():
            print(f"  {key}) {desc}")
            print(f"     {prov} / {mid}")
        print("\n  También: agent --model <model_id>\n")

    choice = input("  Selecciona [1-7]: ").strip()

    if choice in _AVAILABLE_MODELS:
        provider, model_id, desc = _AVAILABLE_MODELS[choice]
        _persist_model(env_file, provider, model_id)
        if use_rich:
            console.print(f"\n  [green]✓[/green] Modelo cambiado a [bold cyan]{desc}[/bold cyan]")
            console.print(f"  [dim]Guardado en {env_file}[/dim]\n")
        else:
            print(f"\n✓ Modelo cambiado a {desc}\n")
    elif choice:
        # Asumir que escribió un model_id custom
        _persist_model(env_file, "gemini", choice)
        if use_rich:
            console.print(f"\n  [green]✓[/green] Modelo cambiado a [bold cyan]{choice}[/bold cyan]")
        else:
            print(f"\n✓ Modelo cambiado a {choice}\n")
    else:
        if use_rich:
            console.print("  [dim]Cancelado.[/dim]")
        else:
            print("  Cancelado.")


def _persist_model(env_file: Path, provider: str, model_id: str) -> None:
    """Actualiza NAS_AGENT_MODEL y NAS_AGENT_MODEL_ID en .env.agent."""
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()
    else:
        lines = ["# Configuración del agente nas-dotfiles", ""]

    # Actualizar o agregar las líneas
    new_lines = []
    found_model = False
    found_model_id = False

    for line in lines:
        if line.startswith("NAS_AGENT_MODEL=") and not line.startswith("NAS_AGENT_MODEL_ID"):
            new_lines.append(f"NAS_AGENT_MODEL={provider}")
            found_model = True
        elif line.startswith("NAS_AGENT_MODEL_ID="):
            new_lines.append(f"NAS_AGENT_MODEL_ID={model_id}")
            found_model_id = True
        elif line.startswith("# NAS_AGENT_MODEL="):
            new_lines.append(f"NAS_AGENT_MODEL={provider}")
            found_model = True
        else:
            new_lines.append(line)

    if not found_model:
        new_lines.append(f"NAS_AGENT_MODEL={provider}")
    if not found_model_id:
        new_lines.append(f"NAS_AGENT_MODEL_ID={model_id}")

    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────────────────────


def main():
    """Punto de entrada principal del agente NAS."""
    # Intentar usar Rich para output bonito
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich.text import Text
        from rich import box
        console = Console()
        use_rich = True
    except ImportError:
        console = None
        use_rich = False

    # ── Parsear flags de sesión ────────────────────────────────────────────
    args = sys.argv[1:]
    force_new_session = False

    # Flag: --new → nueva sesión limpia
    if "--new" in args:
        force_new_session = True
        args.remove("--new")

    # Flag: --model → cambiar modelo y guardarlo en .env.agent
    if "--model" in args:
        _switch_model(args, use_rich, console)
        sys.exit(0)

    # Flag: --clear → borrar sesión y salir
    if "--clear" in args:
        _clear_session()
        if use_rich:
            console.print("  [green]✓[/green] Sesión borrada. Próxima consulta empezará limpia.")
        else:
            print("✓ Sesión borrada. Próxima consulta empezará limpia.")
        sys.exit(0)

    # Flag: --status → mostrar info de sesión y salir
    if "--status" in args:
        meta = _read_session_metadata()
        if not meta:
            msg = "No hay sesión activa."
        else:
            last = meta.get("last_active", 0)
            elapsed = (time.time() - last) / 60 if last else 0
            turns = meta.get("turn_count", 0)
            expired = _session_is_expired(meta)
            status = "⚠️  Expirada" if expired else "✅ Activa"
            msg = (
                f"Sesión: {meta.get('session_id', '?')}\n"
                f"Estado: {status}\n"
                f"Turnos: {turns}\n"
                f"Última actividad: hace {elapsed:.1f} min\n"
                f"Timeout: {SESSION_TIMEOUT_MIN} min"
            )
        if use_rich:
            console.print(Panel(msg, title="[bold cyan]📋 Sesión[/bold cyan]", border_style="bright_cyan", padding=(0, 2), width=60))
        else:
            print(msg)
        sys.exit(0)

    # ── Header ─────────────────────────────────────────────────────────────
    if use_rich:
        console.print()
        console.print(Panel(
            "[bold white]Administrador inteligente de NAS[/bold white]\n"
            "[dim cyan]docker · backup · diagnóstico · catálogo[/dim cyan]",
            title="[bold cyan]🖥️  NAS Agent[/bold cyan]",
            subtitle="[dim magenta]v1.0[/dim magenta]",
            border_style="bright_cyan",
            padding=(0, 2),
            width=60,
        ))
    else:
        print("🖥️  nas-agent — Administrador inteligente de NAS")
        print("=" * 60)

    # ── Obtener query ──────────────────────────────────────────────────────
    if args:
        query = " ".join(args)
        if use_rich:
            console.print(f"\n  [dim white]📝 Query:[/dim white] [bold bright_white]{query}[/bold bright_white]\n")
        else:
            print(f"\n📝 Query: {query}\n")
    else:
        if use_rich:
            console.print("\n  [bright_white]¿Qué necesitas?[/bright_white]")
            console.print("  [dim]Ejemplos:[/dim] [cyan]servicios[/cyan], [yellow]diagnosticar[/yellow], [green]instalar[/green], [magenta]backup[/magenta]\n")
        else:
            print("\n¿Qué necesitas?")
            print("  Ejemplos:")
            print("  - ¿Qué servicios están corriendo?")
            print("  - Quiero instalar Vaultwarden")
            print("  - El nextcloud está lento, diagnostica")
            print()
        query = input("  🖥️ > ")
        if not query.strip():
            print("  Cancelado.")
            sys.exit(0)

    # ── Inicializar sesión + agente ────────────────────────────────────────
    if use_rich:
        console.print("  [bright_yellow]⚡ Inicializando...[/bright_yellow]", end="")
    else:
        print("⚡ Inicializando agente...")

    try:
        session_manager = _get_session_manager(force_new=force_new_session)
        agent = create_nas_agent(session_manager=session_manager, query=query)
    except Exception as e:
        if use_rich:
            console.print(f"\n\n  [red]❌ Error al inicializar:[/red] {e}")
        else:
            print(f"\n❌ Error al inicializar: {e}")
        proveedor = os.environ.get("NAS_AGENT_MODEL", "gemini").lower()
        if proveedor == "gemini":
            print("  - GOOGLE_API_KEY definida (obtener en https://aistudio.google.com/apikey)")
            print("  - pip install 'strands-agents[gemini]'")
        elif proveedor == "bedrock":
            print("  - AWS credentials configuradas")
            print("  - Región correcta (AWS_REGION)")
        elif proveedor == "ollama":
            print("  - Ollama corriendo (ollama serve)")
            print("  - Modelo descargado (ollama pull llama3.1)")
        print(f"\n  Provider actual: {proveedor}")
        print("  Cambiar con: export NAS_AGENT_MODEL=gemini|bedrock|ollama")
        sys.exit(1)

    if use_rich:
        console.print(" [bold green]✓[/bold green]")
    else:
        print("")

    # ── Indicadores de modo ────────────────────────────────────────────────
    if force_new_session:
        if use_rich:
            console.print("  [bold bright_cyan]🆕 Nueva sesión iniciada[/bold bright_cyan]")
        else:
            print("🆕 Nueva sesión iniciada")

    if os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes"):
        if use_rich:
            console.print("  [bold yellow]🔒 MODO DRY-RUN:[/bold yellow] [yellow]Solo mostrará el plan[/yellow]")
        else:
            print("🔒 MODO DRY-RUN: Solo mostrará el plan, sin ejecutar nada.")
    if os.environ.get("NAS_AGENT_READONLY", "0").strip() in ("1", "true", "yes"):
        if use_rich:
            console.print("  [bold yellow]🔒 MODO READ-ONLY:[/bold yellow] [yellow]Acciones destructivas bloqueadas[/yellow]")
        else:
            print("🔒 MODO READ-ONLY: Acciones destructivas bloqueadas.")

    # ── Ejecutar agente ────────────────────────────────────────────────────
    if use_rich:
        console.print()

    try:
        result = agent(query)
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "Too Many Requests" in error_msg or "quota" in error_msg.lower():
            if use_rich:
                console.print(Panel(
                    "[bold yellow]⚠️  Límite de requests alcanzado (quota del tier gratuito).[/bold yellow]\n\n"
                    "Opciones:\n"
                    "  [green]•[/green] Esperar unos minutos e intentar de nuevo\n"
                    "  [green]•[/green] Usar otro modelo: [cyan]NAS_AGENT_MODEL_ID=gemini-2.0-flash agent ...[/cyan]\n"
                    "  [green]•[/green] Activar billing en [blue]https://aistudio.google.com[/blue] (2000 RPM)\n"
                    "  [green]•[/green] Usar Ollama local: [cyan]NAS_AGENT_MODEL=ollama agent ...[/cyan]",
                    title="[bold yellow]⚠️  Rate Limit[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                    width=60,
                ))
            else:
                print("\n  ⚠️  Límite de requests alcanzado (quota del tier gratuito).")
                print("  Esperar unos minutos o usar: NAS_AGENT_MODEL_ID=gemini-2.0-flash")
                print("  O usar Ollama local: NAS_AGENT_MODEL=ollama")
        else:
            if use_rich:
                console.print(f"\n  [bold red]❌ Error:[/bold red] [red]{error_msg[:200]}[/red]")
            else:
                print(f"\n❌ Error: {error_msg[:200]}")
        if use_rich:
            console.print("\n  [dim green]✅ Tarea completada.[/dim green]\n")
        return None

    # ── Mostrar respuesta con Rich ─────────────────────────────────────────
    if use_rich and result:
        console.print()
        # AgentResult.__str__() concatena text blocks del message
        response_text = str(result).strip()

        if response_text:
            try:
                md = Markdown(response_text)
                console.print(Panel(
                    md,
                    title="[bold green]✅ Resultado[/bold green]",
                    border_style="bright_green",
                    padding=(1, 2),
                    box=box.ROUNDED,
                    width=60,
                ))
            except Exception:
                console.print(Panel(
                    response_text,
                    title="[bold green]Resultado[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                    width=60,
                ))
    elif not use_rich:
        print("-" * 60)

    # ── Resumen de sesión ──────────────────────────────────────────────────
    if use_rich:
        console.print()
        console.print("  [dim green]───────────────────────────────────────────────────[/dim green]")
        console.print("  [bold green]✅[/bold green] [bright_white]Tarea completada.[/bright_white]")
        console.print()
    else:
        print("\n✅ Tarea completada.")

    return result


if __name__ == "__main__":
    main()
