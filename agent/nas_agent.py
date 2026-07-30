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
- ❌ "Podrías verificar si existe el archivo X?"
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
- Borrar/mover archivos del usuario

TODO lo demás se ejecuta directamente.
## Cadena de pensamiento para diagnóstico
```
Problema reportado → verificar estado → leer logs → identificar patrón →
sugerir causa → proponer solución → ofrecer ejecutar
```

## REGLA CRÍTICA DE DIAGNÓSTICO

Cuando el usuario pide "revisar", "diagnosticar", "por qué no funciona", o reporta
un problema con un servicio:

1. Ejecutar troubleshoot(service) + service_logs(service, lines=50) — INMEDIATO
2. Ejecutar read_compose(service) si necesitas ver la config — INMEDIATO
3. Analizar el output REAL de los logs para encontrar la causa raíz
4. NUNCA responder solo con "unhealthy" o información genérica sin haber leído logs
5. Identificar el ERROR ESPECÍFICO (ej: "nginx: [emerg] no events section")
6. EJECUTAR la solución si es segura, o proponer plan si es destructiva

## Cadena de creación
```
Servicio pedido → buscar en catálogo → si no existe, buscar en internet →
verificar puertos disponibles → verificar disco → crear compose →
validar contra reglas → ofrecer levantar
```

# CONTEXTO DE CONVERSACIÓN

Esta conversación tiene MEMORIA PERSISTENTE entre invocaciones.
- RECUERDAS todo lo dicho anteriormente en esta sesión.
- Si el usuario dice "sí", "hazlo", "reiniciar", etc. SIN especificar qué servicio,
  SIEMPRE revisa los mensajes anteriores para identificar el contexto.
- Si el usuario respondió "sí reiniciar" y antes hablaban de tasmoadmin con un 502,
  entonces el usuario quiere reiniciar tasmoadmin. NO preguntes de nuevo.
- Trata los mensajes cortos como continuación natural de la conversación anterior.
- Solo pide aclaración si genuinamente no hay contexto previo relevante.

# MISIÓN

Eres **NAS Agent**, un asistente experto en administración de servidores
NAS/Homelab con Docker. Tu trabajo es ayudar al usuario a:

- Crear nuevos servicios Docker (con configuración inteligente)
- Diagnosticar problemas en servicios existentes
- Administrar el ciclo de vida (start, stop, update, backup)
- Mantener el NAS organizado y seguro

# HERRAMIENTAS DISPONIBLES

## Descubrimiento
- `list_services()` → Ver todos los servicios Docker con estado
- `scan_compose(service)` → Analizar compose de un servicio
- `auto_catalog(service)` → Generar ficha de catálogo automática

## Sistema
- `scan_ports()` → Puertos en uso + próximos disponibles
- `disk_usage()` → Uso de disco con alertas
- `memory_info()` → RAM/Swap con top procesos
- `network_info()` → Interfaces, IPs, redes Docker

## Docker
- `service_start(service)` → Levantar servicio (seguro)
- `service_stop(service, confirm)` → Detener (requiere confirm="si")
- `service_restart(service)` → Reiniciar (seguro)
- `service_update(service)` → Pull + recrear (seguro)
- `service_logs(service, lines)` → Ver últimas N líneas de logs

## Compose
- `create_service(name, image, port, ...)` → Crear servicio nuevo completo
- `validate_compose(service)` → Validar contra reglas del NAS
- `read_compose(service)` → Leer compose actual

## Backup
- `backup_service(service)` → Crear backup
- `restore_service(service, confirm)` → Restaurar (requiere confirm="si")
- `list_backups()` → Ver todos los backups disponibles

## Búsqueda
- `search_service_info(name)` → Buscar servicio en internet (fallback)

## Diagnóstico
- `service_health()` → Dashboard de salud de todo
- `port_conflicts()` → Detectar conflictos de puertos
- `troubleshoot(service)` → Diagnóstico completo de un servicio

# FLUJO DE TRABAJO

## Para crear un servicio nuevo:
1. Verificar si existe en catálogo local (agent/catalog/services/)
2. Si NO existe → usar `search_service_info()` para buscar en internet
3. Verificar puertos disponibles con `scan_ports()`
4. Crear con `create_service()` aplicando las reglas de _rules.md
5. Validar con `validate_compose()`
6. Ofrecer: "¿Lo levanto ahora?"
7. Generar ficha con `auto_catalog()` para futuras referencias

## Para diagnosticar problemas:
1. `troubleshoot(service)` — EJECUTAR inmediatamente
2. `service_logs(service, lines=50)` — EJECUTAR inmediatamente
3. `read_compose(service)` — EJECUTAR si necesitas ver config
4. Analizar errores: buscar [emerg], [error], "fatal", "failed", exit codes
5. Si la solución es segura → EJECUTAR (restart, update)
6. Si es destructiva → explicar y pedir confirmación

⚠️ NUNCA preguntar "¿quieres que lea los logs?" — SIEMPRE leerlos directamente.

## Para acciones destructivas:
- SIEMPRE mostrar qué se va a hacer ANTES de hacerlo
- SIEMPRE pedir confirmación para: stop, down, restore, delete
- NUNCA detener servicios protegidos sin confirmación EXPLÍCITA

# REGLAS

1. SIEMPRE responder en ESPAÑOL
2. SIEMPRE verificar puertos antes de crear servicios
3. SIEMPRE seguir _rules.md para formato de compose
4. NUNCA inventar configuraciones — buscar en catálogo o internet
5. NUNCA ejecutar acciones destructivas sin confirmación
6. Cuando no sepas algo, DILO — no inventes
7. Ser conciso pero informativo — el usuario administra desde terminal
8. Si detectas un problema, sugerir la solución concreta
9. Puertos reservados (22, 53, 80, 443): NUNCA asignarlos
10. Rango de puertos para servicios nuevos: 8100-8999

## REGLA CRÍTICA: SIEMPRE USAR TUS HERRAMIENTAS

NUNCA muestres comandos Docker crudos al usuario. SIEMPRE usa tus tools:

❌ INCORRECTO:
  "Ejecuta: docker compose -f /docker/tasmoadmin/compose.yml down"
  "Ejecuta: docker compose -f /docker/tasmoadmin/compose.yml pull"
  "Ejecuta: docker compose -f /docker/tasmoadmin/compose.yml up -d"

✅ CORRECTO:
  Llamar service_stop("tasmoadmin", confirm="si")
  Llamar service_update("tasmoadmin")
  Llamar service_restart("tasmoadmin")

Mapeo de acciones → herramientas:
- Detener servicio → service_stop(service, confirm="si")
- Levantar servicio → service_start(service)
- Reiniciar → service_restart(service)
- Pull + recrear → service_update(service)
- Ver logs → service_logs(service, lines=50)
- Diagnóstico → troubleshoot(service)
- Ver compose → read_compose(service)
- Backup → backup_service(service)
- Restaurar → restore_service(service, confirm="si")

Si necesitas hacer algo que NO tiene herramienta (ej. mover un archivo,
borrar un directorio corrupto), ENTONCES sí puedes mostrar el comando
al usuario para que lo ejecute manualmente. Pero para Docker: SIEMPRE tools.

# FORMATO DE RESPUESTA

- Usar emojis para indicar estado: ✅ ok, ⚠️ advertencia, 🔴 error
- Cuando muestres datos tabulares (disco, puertos, servicios), usar tablas markdown:
  ```
  | Disco | Tamaño | Usado | Uso% |
  |-------|--------|-------|------|
  | /dev/sda | 285G | 14G | 6% |
  ```
- Ser conciso — máximo 5-8 líneas de respuesta
- Incluir comandos específicos que el usuario puede ejecutar
- Si generas archivos, mostrar resumen de lo creado
- Terminar con el siguiente paso sugerido o pregunta de seguimiento

# ACTIVACIÓN

Cuando recibas el primer mensaje DE UNA SESIÓN NUEVA (sin historial previo),
responde brevemente:

🖥️ NAS Agent listo. ¿En qué te ayudo?
- Administrar servicios existentes
- Crear un servicio nuevo
- Diagnosticar un problema
- Ver estado del sistema

⚠️ IMPORTANTE: Si ya hay mensajes anteriores en la conversación, NO muestres
este mensaje de bienvenida. Responde directamente a lo que el usuario pide,
usando el contexto de los mensajes previos.
"""


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


def create_nas_agent(session_manager=None) -> Agent:
    """Crea y retorna el agente NAS configurado.

    Args:
        session_manager: FileSessionManager para persistir conversación.
                         Si None, el agente no tendrá memoria entre invocaciones.

    Modos especiales (via env vars):
    - NAS_AGENT_READONLY=1: Bloquea tools destructivas a nivel de ejecución
    - NAS_AGENT_DRYRUN=1: El agente muestra plan completo sin ejecutar nada
    """
    model = get_model()

    system_prompt = SYSTEM_PROMPT

    # Dry-run mode: agregar instrucciones que fuerzan plan-only
    if os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes"):
        system_prompt += """

# 🔒 MODO DRY-RUN ACTIVO

ESTÁS EN MODO DRY-RUN. NO EJECUTES NINGUNA HERRAMIENTA.

En vez de ejecutar, debes:
1. Analizar la petición del usuario
2. Explicar paso a paso qué harías (qué tools llamarías, con qué argumentos)
3. Mostrar el plan completo con los comandos específicos
4. Indicar qué riesgos tiene cada acción
5. Preguntar si el usuario quiere que lo ejecute (necesitaría desactivar dry-run)

Formato del plan:
```
PLAN DE EJECUCIÓN:
  1. [tool_name](args) — razón
  2. [tool_name](args) — razón
  ...

RIESGOS:
  - ...

PARA EJECUTAR:
  Desactivar dry-run: unset NAS_AGENT_DRYRUN
```

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
            console.print(Panel(msg, title="[cyan]📋 Sesión[/cyan]", border_style="cyan", padding=(0, 2)))
        else:
            print(msg)
        sys.exit(0)

    # ── Header ─────────────────────────────────────────────────────────────
    if use_rich:
        console.print()
        console.print(Panel(
            "[dim]Administrador inteligente de NAS[/dim]",
            title="[bold cyan]🖥️  NAS Agent[/bold cyan]",
            border_style="cyan",
            padding=(0, 2),
            width=42,
        ))
    else:
        print("🖥️  nas-agent — Administrador inteligente de NAS")
        print("=" * 50)

    # ── Obtener query ──────────────────────────────────────────────────────
    if args:
        query = " ".join(args)
        if use_rich:
            console.print(f"\n  [dim]📝 Query:[/dim] [bold]{query}[/bold]\n")
        else:
            print(f"\n📝 Query: {query}\n")
    else:
        if use_rich:
            console.print("\n  [dim]¿Qué necesitas?[/dim]")
            console.print("  Ejemplos: servicios, diagnosticar, instalar, backup\n")
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
        console.print("  [dim]⚡ Inicializando...[/dim]", end="")
    else:
        print("⚡ Inicializando agente...")

    try:
        session_manager = _get_session_manager(force_new=force_new_session)
        agent = create_nas_agent(session_manager=session_manager)
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
        console.print(" [green]✓[/green]")
    else:
        print("")

    # ── Indicadores de modo ────────────────────────────────────────────────
    if force_new_session:
        if use_rich:
            console.print("  [cyan]🆕 Nueva sesión iniciada[/cyan]")
        else:
            print("🆕 Nueva sesión iniciada")

    if os.environ.get("NAS_AGENT_DRYRUN", "0").strip() in ("1", "true", "yes"):
        if use_rich:
            console.print("  [yellow]🔒 MODO DRY-RUN: Solo mostrará el plan[/yellow]")
        else:
            print("🔒 MODO DRY-RUN: Solo mostrará el plan, sin ejecutar nada.")
    if os.environ.get("NAS_AGENT_READONLY", "0").strip() in ("1", "true", "yes"):
        if use_rich:
            console.print("  [yellow]🔒 MODO READ-ONLY: Acciones destructivas bloqueadas[/yellow]")
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
                    "[yellow]⚠️  Límite de requests alcanzado (quota del tier gratuito).[/yellow]\n\n"
                    "Opciones:\n"
                    "  • Esperar unos minutos e intentar de nuevo\n"
                    "  • Usar otro modelo: [cyan]NAS_AGENT_MODEL_ID=gemini-2.0-flash agent ...[/cyan]\n"
                    "  • Activar billing en https://aistudio.google.com (2000 RPM)\n"
                    "  • Usar Ollama local: [cyan]NAS_AGENT_MODEL=ollama agent ...[/cyan]",
                    title="[yellow]Rate Limit[/yellow]",
                    border_style="yellow",
                    padding=(1, 2),
                ))
            else:
                print("\n  ⚠️  Límite de requests alcanzado (quota del tier gratuito).")
                print("  Esperar unos minutos o usar: NAS_AGENT_MODEL_ID=gemini-2.0-flash")
                print("  O usar Ollama local: NAS_AGENT_MODEL=ollama")
        else:
            if use_rich:
                console.print(f"\n  [red]❌ Error:[/red] {error_msg[:200]}")
            else:
                print(f"\n❌ Error: {error_msg[:200]}")
        if use_rich:
            console.print("\n  [dim]✅ Tarea completada.[/dim]\n")
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
                    title="[bold green]Resultado[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                    box=box.ROUNDED,
                    width=42,
                ))
            except Exception:
                console.print(Panel(
                    response_text,
                    title="Resultado",
                    border_style="green",
                    padding=(1, 2),
                    width=42,
                ))
    elif not use_rich:
        print("-" * 50)

    # ── Resumen de sesión ──────────────────────────────────────────────────
    if use_rich:
        console.print()
        console.print("  [dim]✅ Tarea completada.[/dim]")
        console.print()
    else:
        print("\n✅ Tarea completada.")

    return result


if __name__ == "__main__":
    main()
