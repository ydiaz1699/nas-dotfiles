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

Requisitos:
    pip install 'strands-agents[gemini]' strands-agents-tools python-frontmatter pyyaml
"""

import os
import sys
from pathlib import Path

from strands import Agent

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
# System Prompt del agente NAS
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
# RAZONAMIENTO

Antes de ejecutar cualquier acción, SIEMPRE razona paso a paso:

1. **Entender** — ¿Qué está pidiendo exactamente el usuario?
2. **Planificar** — ¿Qué información necesito? ¿En qué orden obtengo/verifico?
3. **Verificar** — Consultar el estado actual ANTES de actuar (puertos, servicios, disco)
4. **Evaluar riesgo** — ¿La acción es reversible? ¿Puede causar downtime?
5. **Ejecutar** — Solo actuar después de tener toda la información necesaria
6. **Confirmar** — ¿El resultado es el esperado? ¿Hay efectos secundarios?

## Reglas de razonamiento
- Si la tarea tiene RIESGO (stop, down, delete, restore): explica tu plan completo
  ANTES de ejecutar. Muestra qué vas a hacer y pide confirmación.
- Si hay AMBIGÜEDAD: pregunta antes de asumir. "¿Te refieres a X o Y?"
- Si NO SABÉS algo: dilo explícitamente. Nunca inventes datos ni configuraciones.
- Si algo FALLA: analiza el error, sugiere causa probable y solución concreta.
- Cuando uses múltiples herramientas: explica brevemente qué vas a consultar y por qué.

## Cadena de pensamiento para diagnóstico
```
Problema reportado → verificar estado → leer logs → identificar patrón →
sugerir causa → proponer solución → ofrecer ejecutar
```

## Cadena de pensamiento para creación
```
Servicio pedido → buscar en catálogo → si no existe, buscar en internet →
verificar puertos disponibles → verificar disco → crear compose →
validar contra reglas → ofrecer levantar
```

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
1. `service_health()` para visión general
2. `troubleshoot(service)` para un servicio específico
3. `service_logs(service)` si necesitas más detalle
4. Sugerir soluciones basadas en los errores encontrados

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

# FORMATO DE RESPUESTA

- Usar emojis para indicar estado: ✅ ok, ⚠️ advertencia, 🔴 error
- Incluir comandos específicos que el usuario puede ejecutar
- Si generas archivos, mostrar resumen de lo creado
- Terminar con el siguiente paso sugerido o pregunta de seguimiento

# ACTIVACIÓN

Cuando recibas el primer mensaje, responde brevemente:

🖥️ NAS Agent listo. ¿En qué te ayudo?
- Administrar servicios existentes
- Crear un servicio nuevo
- Diagnosticar un problema
- Ver estado del sistema
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

        model_id = model_id_override or "gemini-2.5-flash"

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


def create_nas_agent() -> Agent:
    """Crea y retorna el agente NAS configurado.

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

    agent = Agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=system_prompt,
    )

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

    # ── Header ─────────────────────────────────────────────────────────────
    if use_rich:
        console.print()
        console.print(Panel.fit(
            "[bold cyan]🖥️  NAS Agent[/bold cyan]\n"
            "[dim]Administrador inteligente de NAS[/dim]",
            border_style="cyan",
            padding=(0, 2),
        ))
    else:
        print("🖥️  nas-agent — Administrador inteligente de NAS")
        print("=" * 50)

    # ── Obtener query ──────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
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

    # ── Inicializar agente ─────────────────────────────────────────────────
    if use_rich:
        console.print("  [dim]⚡ Inicializando...[/dim]", end="")
    else:
        print("⚡ Inicializando agente...")

    try:
        agent = create_nas_agent()
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
    result = agent(query)

    # ── Mostrar respuesta con Rich ─────────────────────────────────────────
    if use_rich and result:
        console.print()
        # Obtener el texto de la respuesta
        response_text = ""
        if hasattr(result, "message") and result.message:
            if isinstance(result.message, dict):
                content = result.message.get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        response_text += block.get("text", "")
            elif isinstance(result.message, str):
                response_text = result.message
        elif hasattr(result, "text"):
            response_text = result.text
        else:
            response_text = str(result)

        if response_text.strip():
            # Renderizar como Markdown dentro de un panel
            try:
                md = Markdown(response_text.strip())
                console.print(Panel(
                    md,
                    title="[bold green]Respuesta[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                    box=box.ROUNDED,
                ))
            except Exception:
                # Fallback si Markdown falla
                console.print(Panel(
                    response_text.strip(),
                    title="Respuesta",
                    border_style="green",
                    padding=(1, 2),
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
