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
# Arquitectura: Thinking Prompt + Bloques Dinámicos
#
# El agente NO recibe un system prompt monolítico.
# Python pre-clasifica la query y selecciona bloques relevantes.
# El thinking prompt le indica al modelo qué bloques tiene y que razone.
# ─────────────────────────────────────────────────────────────────────────────

THINKING_PROMPT = """
# INSTRUCCIÓN DE RAZONAMIENTO

Se han cargado bloques de contexto según tu tarea. Antes de actuar:

1. CONFIRMAR: ¿Los bloques cargados cubren lo que necesito?
2. CLASIFICAR: ¿La acción es lectura / segura / destructiva?
3. PLANIFICAR: ¿Qué herramientas, en qué orden?
4. EJECUTAR: Sin preguntar si es segura. Confirmar si es destructiva.
5. RESPONDER: Conciso, con resultado + siguiente paso.

IMPORTANTE: Sigue las reglas de los bloques cargados. No inventes reglas que no están.
"""

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUES MODULARES — se cargan según la tarea
# ─────────────────────────────────────────────────────────────────────────────

BLOCK_IDENTIDAD = """
# IDENTIDAD

Eres **NAS Agent**, experto en administración de servidores NAS/Homelab con Docker.
Tu trabajo: crear servicios, diagnosticar problemas, administrar ciclo de vida, mantener seguro.

Modelo: {model_info}
Provider: {provider}
Si preguntan qué modelo eres → responder EXACTAMENTE: "{model_info}". No inventar otro nombre.
"""

BLOCK_REGLAS_CORE = """
# REGLAS DE EJECUCIÓN

## Principio: ACTUAR, no sugerir
- LECTURA (logs, compose, health, diagnóstico): EJECUTAR INMEDIATAMENTE sin preguntar.
- SEGURAS (start, restart, update): EJECUTAR directamente sin preguntar.
- DESTRUCTIVAS (stop, restore): EXPLICAR primero, CONFIRMAR después.

## Ejecutar SIN preguntar (NUNCA pedir permiso para estas):
troubleshoot · service_logs · read_compose · scan_ports · disk_usage
memory_info · network_info · list_services · service_health · port_conflicts
list_files · read_file_content · scan_compose · validate_compose
service_start · service_restart · service_update · search_service_info

## Requiere confirm="si":
service_stop · restore_service

## Lo que NUNCA hacer:
- ❌ "¿Quieres que lea el compose?" / "¿Puedo ejecutar troubleshoot?"
- ❌ Mostrar comandos docker crudos — SIEMPRE usar tools
- ❌ Inventar configuraciones sin buscar en catálogo o internet

## Mapeo acción → herramienta:
Detener → service_stop(svc, confirm="si") | Levantar → service_start(svc)
Reiniciar → service_restart(svc) | Actualizar → service_update(svc)
Logs → service_logs(svc, 50) | Diagnóstico → troubleshoot(svc)
Compose → read_compose(svc) | Backup → backup_service(svc)
Restaurar → restore_service(svc, confirm="si")

## Ejemplo de ejecución correcta:
```
Usuario: "revisar tasmoadmin"
→ troubleshoot("tasmoadmin")     ← ejecuta sin preguntar
→ service_logs("tasmoadmin", 50) ← ejecuta sin preguntar
→ Analiza errores reales
→ service_update("tasmoadmin")   ← seguro, ejecuta
→ Reporta resultado
```
"""

BLOCK_SEGURIDAD = """
# SEGURIDAD

## Credenciales
- NUNCA mostrar credenciales en claro en respuestas
- .env → secretos con ${VAR}, nunca inline en compose
- Puertos reservados (22, 53, 80, 443): NUNCA asignar
- Rango servicios nuevos: 8100-8999

## Modos de protección
- NAS_AGENT_READONLY=1 → tools destructivas bloqueadas en código
- NAS_AGENT_DRYRUN=1 → nada se ejecuta, solo muestra plan

## Servicios protegidos
- NUNCA detener sin confirmación EXPLÍCITA del usuario
- stop y restore son las ÚNICAS acciones destructivas
"""

BLOCK_HERRAMIENTAS = """
# HERRAMIENTAS DISPONIBLES

## Descubrimiento
- list_services() → Servicios Docker con estado
- scan_compose(service) → Analizar compose
- auto_catalog(service) → Generar ficha de catálogo
- bulk_discover() → Descubrir y catalogar todos
- export_service(service) → Exportar config al catálogo

## Sistema
- scan_ports() → Puertos en uso + disponibles
- disk_usage() → Uso de disco con alertas
- memory_info() → RAM/Swap con top procesos
- network_info() → Interfaces, IPs, redes Docker
- list_files(path, max_depth) → Listar archivos/carpetas
- read_file_content(path, lines) → Leer archivo de texto

## Docker
- service_start(service) → Levantar (seguro)
- service_stop(service, confirm) → Detener (requiere confirm="si")
- service_restart(service) → Reiniciar (seguro)
- service_update(service) → Pull + recrear (seguro)
- service_logs(service, lines) → Ver logs

## Compose
- create_service(name, image, port, ...) → Crear servicio nuevo
- validate_compose(service) → Validar contra reglas
- read_compose(service) → Leer compose actual

## Backup
- backup_service(service) → Crear backup
- restore_service(service, confirm) → Restaurar (requiere confirm="si")
- list_backups() → Listar backups

## Búsqueda y Diagnóstico
- search_service_info(name) → Buscar en internet
- service_health() → Dashboard de salud
- port_conflicts() → Detectar conflictos
- troubleshoot(service) → Diagnóstico completo
- project_scan(verbose) → Escanear proyecto y detectar lagunas/inconsistencias

## Memoria Persistente
- remember(fact, category) → Guardar hecho/lección
- recall(query) → Buscar en memoria (USAR ANTES de resolver)
- learn_skill(name, procedure, trigger) → Crear skill reutilizable
- update_user_model(key, value) → Actualizar perfil del usuario
- memory_stats() → Estado de la memoria
"""

BLOCK_FORMATO = """
# FORMATO DE RESPUESTA

- Idioma: SIEMPRE español
- Longitud: conciso, 5-8 líneas máximo
- Emojis: ✅ ok, ⚠️ advertencia, 🔴 error
- Datos tabulares: tablas markdown
- Terminar con siguiente paso sugerido
- Si generas archivos: mostrar resumen de lo creado
"""

BLOCK_CONTEXTO_NAS = """
# CONTEXTO DEL NAS

## Memoria de sesión
- Conversación PERSISTENTE entre invocaciones
- Si dice "sí", "hazlo" sin servicio → usar contexto anterior
- Mensajes cortos = continuación natural de conversación previa
- Solo pedir aclaración si NO hay contexto previo relevante

## CLI del usuario — comandos que YA tiene disponibles:
El usuario tiene un CLI propio (`svc`) para administrar servicios Docker.
Cuando pregunte sobre comandos Docker, MENCIONARLE SUS COMANDOS:

### Comandos del CLI `svc` (usa bash o python según NAS_CLI):
- `svc up <servicio>` → docker compose up -d
- `svc down <servicio>` → docker compose down
- `svc start <servicio>` → iniciar detenido
- `svc stop <servicio>` → detener
- `svc restart <servicio>` → reiniciar
- `svc update <servicio>` → pull imagen + recrear
- `svc recreate <servicio>` → recrear sin pull (compose up -d --force-recreate)
- `svc update-all` → actualizar todos (con multi-select en Python CLI)
- `svc logs <servicio>` → ver logs en vivo
- `svc health` → dashboard de salud de todos los servicios
- `svc doctor` → chequeo completo del NAS (disco, RAM, Docker, puertos)
- `svc watch` → monitoreo en vivo
- `svc menu` → menú interactivo (fzf en bash, InquirerPy en python)
- `svc backup <servicio>` → backup de volúmenes
- `svc restore <servicio>` → restaurar backup
- `svc port-map` → mapa de puertos
- `svc net` → mapa de redes Docker
- `svc size` → disco por servicio
- `svc create <nombre>` → scaffolding de nuevo servicio
- `svc diff <servicio>` → comparar compose vs resuelto
- `svc env <servicio>` → ver variables de entorno
- `svc open <servicio>` → mostrar URL
- `svc lista` → listar servicios con estado (activo/detenido)
- `svc catalog-sync [servicio]` → sincronizar documentación del catálogo
- `svc scan` → detectar lagunas e inconsistencias del proyecto
- `svc depends <servicio>` → ver dependencias de un servicio

### Agente (este programa):
- `agent "pregunta"` → consulta puntual
- `agent chat` → modo conversacional (REPL)
- `agent --new "pregunta"` → nueva sesión limpia
- `agent --model` → cambiar modelo
- `agent --status` → info de sesión
- `agent --clear` → borrar sesión

### Otros comandos shell del usuario (NO son tus tools):
- `instal <pkg>` → APT del sistema. "instal git" = paquete apt, NO Docker
- `pipins <pkg>` → pip install (Python packages)
- `bat`, `nas`, `off`, `restart`, `adm`, `dk` → comandos shell del usuario

## Regla de respuesta sobre comandos:
- Si preguntan "qué hace X" o "cómo hago Y" → EXPLICAR + MENCIONAR el comando svc equivalente
- Si preguntan sobre docker compose → explicar Y decir "en tu NAS: `svc <acción> <servicio>`"
- NUNCA decir solo "yo me encargo" — SIEMPRE dar el comando CLI también
- El usuario puede ejecutar cosas SIN el agente usando `svc`

## Activación (primera sesión)
Si no hay historial previo: 🖥️ NAS Agent listo. ¿En qué te ayudo?
Si hay historial: responder directamente sin bienvenida.
"""

BLOCK_DIAGNOSTICO = """
# CONTEXTO CARGADO: DIAGNÓSTICO

## Cadena completa (ejecutar TODO inmediato, SIN preguntar)
1. troubleshoot(service) — analiza estado + health + config
2. service_logs(service, lines=50) — buscar errores reales
3. read_compose(service) — si necesitas ver config
4. Analizar output REAL → identificar ERROR ESPECÍFICO
   Buscar: [emerg], [error], "fatal", "failed", exit codes, OOM
5. NUNCA responder genérico ("unhealthy") sin haber leído logs
6. Ejecutar solución si es segura / proponer plan si es destructiva

## Patrones de error → herramientas
- OOMKilled → memory_info() + revisar limits en compose
- Restart loop (>3 restarts) → logs últimas 100 líneas
- Port conflict → port_conflicts() + scan_ports()
- Permission denied → verificar user/group en compose
- Connection refused → verificar network + depends_on
- Disk full → disk_usage() + revisar volúmenes
- Image pull error → service_update() para reintentar
"""

BLOCK_CREACION = """
# CONTEXTO CARGADO: CREACIÓN DE SERVICIOS

## Flujo completo
1. Buscar catálogo local: agent/catalog/services/
2. Si NO existe → search_service_info() en internet
3. Deps sistema: read_file_content("/nas-dotfiles/logs/packages.txt")
   - TLS/certs → openssl | NFS → nfs-common | GPU → nvidia-container-toolkit
   - Healthcheck HTTP → curl | USB (zigbee) → usbutils
4. Si falta algo: "Ejecuta `instal <paquete>` primero"
   (NO ejecutes instal tú — es comando del usuario)
5. scan_ports() → verificar disponibilidad
6. create_service() → validate_compose()
7. Ofrecer: "¿Lo levanto ahora?"
8. auto_catalog() para futuras referencias

## Reglas de configuración
- Puertos reservados: 22, 53, 80, 443 — NUNCA
- Rango servicios nuevos: 8100-8999
- Restart policy: SIEMPRE unless-stopped
- Secrets: SIEMPRE en .env, NUNCA inline en compose
- Healthcheck: agregar si expone HTTP
- Formato: seguir _rules.md del catálogo
- Network: usar red bridge dedicada si interactúa con otros servicios
"""

BLOCK_BACKUP = """
# CONTEXTO CARGADO: BACKUP Y RESTAURACIÓN

## Backup
- backup_service(service) → exporta volúmenes nombrados a tar.gz
- Destino: /docker/backups/ con timestamp
- list_backups() → ver backups disponibles
- Verificar espacio con disk_usage() antes si el servicio es grande

## Restauración (DESTRUCTIVA — siempre confirmar)
- restore_service(service, confirm="si") — sobreescribe datos actuales
- SIEMPRE sugerir hacer backup ANTES de restaurar
- Explicar qué se va a sobreescribir antes de pedir confirmación
"""

BLOCK_MEMORIA = """
# MEMORIA PERSISTENTE

Tienes memoria entre sesiones. Úsala activamente:

## Antes de actuar en un problema:
- recall("descripción del problema") → busca si ya lo resolviste antes
- Si encuentra un SKILL → aplicar directamente (no re-investigar)

## Después de resolver algo complejo o nuevo:
- remember("lección concisa", category="leccion|patron|entorno")
- Si fueron >3 pasos → learn_skill(nombre, procedimiento, trigger)

## Cuando observes preferencias del usuario:
- update_user_model("clave", "valor observado")

## NO guardar:
- Cosas triviales ("el usuario dijo hola")
- Info duplicada (ya existe en MEMORY.md)
- Datos sensibles (passwords, tokens, IPs privadas)

## Herramientas de memoria:
- remember(fact, category) → guardar hecho/lección
- recall(query) → buscar en memoria
- learn_skill(name, procedure, trigger) → crear procedimiento reutilizable
- update_user_model(key, value) → actualizar perfil del usuario
- memory_stats() → ver estado de la memoria
"""

BLOCK_ADMIN = """
# CONTEXTO CARGADO: ADMINISTRACIÓN

## Acciones seguras → ejecutar directamente sin preguntar
- service_start(svc) — levantar servicio detenido
- service_restart(svc) — reiniciar (no pierde datos)
- service_update(svc) — pull imagen + recrear contenedor (seguro)

⚠️ REPITO: restart y update SON SEGUROS. NO preguntes "¿procedo?".
   SIMPLEMENTE EJECUTA Y REPORTA RESULTADO.

## Acciones destructivas → pedir confirmación
- service_stop(svc, confirm="si") — detener servicio
- restore_service(svc, confirm="si") — sobreescribir con backup

## Actualización masiva
- Para un servicio: service_update(svc)
- Para todos: indicar al usuario "svc update-all" en terminal
"""


# ─────────────────────────────────────────────────────────────────────────────
# Motor de clasificación y ensamblaje de bloques
# ─────────────────────────────────────────────────────────────────────────────

def _classify_query(query: str) -> list:
    """Pre-clasifica la query y retorna lista de bloques a cargar.

    Python hace la primera clasificación (rápida, sin tokens).
    El thinking prompt le dice al modelo que confirme/ajuste.
    """
    q = query.lower()
    blocks = ["identidad"]  # Siempre

    # Diagnóstico
    if any(w in q for w in [
        "revisar", "diagnosticar", "problema", "error", "falla", "caído",
        "no funciona", "unhealthy", "arreglar", "lento", "crash",
        "502", "503", "timeout", "log", "por qué", "qué pasa",
    ]):
        blocks.extend(["reglas_core", "herramientas", "memoria", "diagnostico", "formato"])
        return blocks

    # Creación
    if any(w in q for w in [
        "instalar", "crear", "nuevo servicio", "quiero", "montar",
        "configurar", "deployer", "agregar", "setup",
    ]):
        blocks.extend(["reglas_core", "herramientas", "seguridad", "creacion", "formato"])
        return blocks

    # Backup
    if any(w in q for w in [
        "backup", "respaldo", "restaurar", "restore", "exportar catálogo",
    ]):
        blocks.extend(["reglas_core", "herramientas", "backup", "formato"])
        return blocks

    # Administración
    if any(w in q for w in [
        "start", "stop", "restart", "update", "detener", "levantar",
        "actualizar", "parar", "iniciar", "reiniciar", "subir", "bajar",
    ]):
        blocks.extend(["reglas_core", "herramientas", "admin", "formato"])
        return blocks

    # Info del sistema
    if any(w in q for w in [
        "servicios", "estado", "salud", "health", "disco", "memoria",
        "puertos", "red", "lista",
    ]):
        blocks.extend(["reglas_core", "herramientas", "formato"])
        return blocks

    # Identidad / modelo
    if any(w in q for w in [
        "modelo", "quién eres", "qué eres", "identidad", "versión",
    ]):
        return blocks  # Solo identidad

    # Memoria
    if any(w in q for w in [
        "recuerda", "recordar", "memoria", "aprendiste", "skill",
        "olvida", "qué sabes",
    ]):
        blocks.extend(["reglas_core", "memoria", "formato"])
        return blocks

    # General / conversación
    blocks.extend(["reglas_core", "contexto_nas", "memoria", "formato"])
    return blocks


def _assemble_prompt(blocks: list, model_info: str, provider: str) -> str:
    """Ensambla el prompt final: Thinking + bloques seleccionados."""
    block_map = {
        "identidad": BLOCK_IDENTIDAD.format(model_info=model_info, provider=provider),
        "reglas_core": BLOCK_REGLAS_CORE,
        "seguridad": BLOCK_SEGURIDAD,
        "herramientas": BLOCK_HERRAMIENTAS,
        "formato": BLOCK_FORMATO,
        "contexto_nas": BLOCK_CONTEXTO_NAS,
        "diagnostico": BLOCK_DIAGNOSTICO,
        "creacion": BLOCK_CREACION,
        "backup": BLOCK_BACKUP,
        "admin": BLOCK_ADMIN,
        "memoria": BLOCK_MEMORIA,
    }

    parts = [THINKING_PROMPT]
    loaded = [b for b in blocks if b in block_map]
    parts.append(f"\n# BLOQUES CARGADOS PARA ESTA TAREA: {', '.join(loaded)}\n")

    for name in loaded:
        parts.append(block_map[name])

    return "\n".join(parts)
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

    Arquitectura de prompt:
      Thinking Prompt → selecciona bloques → ensambla prompt dinámico

    Python pre-clasifica la query para elegir bloques relevantes.
    El thinking prompt le dice al modelo que confirme/ajuste.
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

    # ── Clasificar query y ensamblar bloques ───────────────────────────────
    blocks = _classify_query(query) if query else ["identidad", "reglas_core", "memoria", "contexto_nas", "formato"]
    system_prompt = _assemble_prompt(blocks, _model_info, proveedor)

    # Dry-run mode
    if os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes"):
        system_prompt += """

# 🔒 MODO DRY-RUN ACTIVO

NO EJECUTES NINGUNA HERRAMIENTA. Solo muestra el plan:
1. Qué tools llamarías y con qué argumentos
2. En qué orden
3. Qué riesgos tiene
4. Cómo desactivar dry-run: unset NAS_AGENT_DRYRUN
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
# REPL Mode — Loop conversacional
# ─────────────────────────────────────────────────────────────────────────────


def _repl_mode(use_rich: bool, console, force_new_session: bool) -> None:
    """Modo REPL: loop interactivo que mantiene el agente vivo entre preguntas.

    Beneficios vs modo single-shot:
    - Modelo se carga UNA vez (no cada pregunta)
    - Contexto inmediato entre preguntas (misma instancia)
    - Conversación fluida tipo chat

    Comandos especiales del REPL:
    - exit / quit / salir → terminar
    - clear → borrar sesión y empezar limpio
    - status → info de sesión
    - model → cambiar modelo
    """
    # ── Header ─────────────────────────────────────────────────────────────
    if use_rich:
        from rich.panel import Panel
        from rich.markdown import Markdown
        from rich import box
        console.print()
        console.print(Panel(
            "[bold white]NAS Agent — Modo REPL[/bold white]\n"
            "[dim cyan]Conversación continua · exit para salir · clear para resetear[/dim cyan]",
            title="[bold cyan]🖥️  NAS Agent REPL[/bold cyan]",
            subtitle="[dim magenta]v1.0[/dim magenta]",
            border_style="bright_cyan",
            padding=(0, 2),
            width=60,
        ))
        console.print()
    else:
        print("\n🖥️  NAS Agent — Modo REPL")
        print("  Conversación continua. exit para salir, clear para resetear.")
        print("=" * 60)
        print()

    # ── Inicializar agente UNA vez ─────────────────────────────────────────
    if use_rich:
        console.print("  [bright_yellow]⚡ Inicializando agente...[/bright_yellow]", end="")
    else:
        print("⚡ Inicializando agente...")

    try:
        session_manager = _get_session_manager(force_new=force_new_session)
        # Crear agente con prompt genérico (cubre todos los bloques)
        agent = create_nas_agent(session_manager=session_manager, query="")
    except Exception as e:
        if use_rich:
            console.print(f"\n  [red]❌ Error al inicializar:[/red] {e}")
        else:
            print(f"\n❌ Error al inicializar: {e}")
        return

    if use_rich:
        console.print(" [bold green]✓[/bold green]\n")
    else:
        print("✓ Listo.\n")

    # Indicadores de modo
    if os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes"):
        if use_rich:
            console.print("  [bold yellow]🔒 MODO DRY-RUN activo[/bold yellow]\n")
        else:
            print("🔒 MODO DRY-RUN activo\n")

    turn = 0

    # ── Loop principal ─────────────────────────────────────────────────────
    while True:
        try:
            # Prompt de input
            if use_rich:
                query = input("  🖥️ > ")
            else:
                query = input("🖥️ > ")
        except (EOFError, KeyboardInterrupt):
            # Ctrl+C o Ctrl+D → salir limpio
            if use_rich:
                console.print("\n\n  [dim]Sesión terminada.[/dim]\n")
            else:
                print("\n\nSesión terminada.")
            break

        query = query.strip()

        # ── Comandos especiales del REPL ───────────────────────────────────
        if not query:
            continue

        if query.lower() in ("exit", "quit", "salir", "q"):
            if use_rich:
                console.print("\n  [dim green]👋 Hasta luego.[/dim green]\n")
            else:
                print("\n👋 Hasta luego.")
            break

        if query.lower() == "clear":
            _clear_session()
            session_manager = _get_session_manager(force_new=True)
            agent = create_nas_agent(session_manager=session_manager, query="")
            turn = 0
            if use_rich:
                console.print("  [green]✓[/green] Sesión borrada. Contexto limpio.\n")
            else:
                print("✓ Sesión borrada. Contexto limpio.\n")
            continue

        if query.lower() == "status":
            meta = _read_session_metadata()
            turns_total = meta.get("turn_count", 0)
            if use_rich:
                console.print(f"  [cyan]Turnos esta sesión:[/cyan] {turn}")
                console.print(f"  [cyan]Turnos totales:[/cyan] {turns_total}\n")
            else:
                print(f"  Turnos: {turn} (total: {turns_total})\n")
            continue

        if query.lower() == "help":
            if use_rich:
                console.print("  [bold]Comandos REPL:[/bold]")
                console.print("    [cyan]exit[/cyan]   — salir")
                console.print("    [cyan]clear[/cyan]  — borrar sesión y resetear")
                console.print("    [cyan]status[/cyan] — info de sesión")
                console.print("    [cyan]help[/cyan]   — este mensaje")
                console.print("    [dim]Cualquier otra cosa → pregunta al agente[/dim]\n")
            else:
                print("  exit   — salir")
                print("  clear  — borrar sesión")
                print("  status — info de sesión")
                print("  help   — este mensaje\n")
            continue

        # ── Ejecutar query ─────────────────────────────────────────────────
        turn += 1

        try:
            result = agent(query)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Too Many Requests" in error_msg or "quota" in error_msg.lower():
                if use_rich:
                    console.print("\n  [yellow]⚠️  Rate limit — espera unos segundos e intenta de nuevo.[/yellow]\n")
                else:
                    print("\n  ⚠️  Rate limit — espera e intenta de nuevo.\n")
            else:
                if use_rich:
                    console.print(f"\n  [red]❌ Error:[/red] {error_msg[:150]}\n")
                else:
                    print(f"\n❌ Error: {error_msg[:150]}\n")
            continue

        # ── Mostrar respuesta ──────────────────────────────────────────────
        if use_rich and result:
            from rich.markdown import Markdown
            from rich import box
            console.print()
            response_text = str(result).strip()
            if response_text:
                try:
                    md = Markdown(response_text)
                    console.print(Panel(
                        md,
                        border_style="bright_green",
                        padding=(1, 2),
                        box=box.ROUNDED,
                        width=60,
                    ))
                except Exception:
                    console.print(f"  {response_text}")
            console.print()
        elif result:
            print(f"\n{str(result).strip()}\n")
        else:
            if use_rich:
                console.print("  [dim](sin respuesta)[/dim]\n")
            else:
                print("  (sin respuesta)\n")


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

    # Flag: --repl / chat → modo conversacional (loop)
    if "--repl" in args or (args and args[0] == "chat"):
        if "--repl" in args:
            args.remove("--repl")
        elif args[0] == "chat":
            args.pop(0)
        _repl_mode(use_rich, console, force_new_session)
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
