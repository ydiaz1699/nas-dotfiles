"""
nas_agent.py — Agente inteligente para administración de NAS/Homelab

Usa Strands Agents SDK con auto-detección de servicios Docker,
catálogo local + web search como fallback, y reglas estandarizadas
para crear, diagnosticar y administrar servicios en el NAS.

Proveedores soportados:
    - Amazon Bedrock (default) — Claude Sonnet
    - Ollama (local, gratis) — llama3.1 o cualquier modelo

Uso:
    # Modo interactivo
    python -m agent.nas_agent

    # Con query directa
    python -m agent.nas_agent "¿Qué servicios están caídos?"

    # Con Ollama local
    NAS_AGENT_MODEL=ollama python -m agent.nas_agent "..."

Requisitos:
    pip install strands-agents strands-agents-tools python-frontmatter pyyaml
"""

import os
import sys
from pathlib import Path

from strands import Agent

from agent.tools import ALL_TOOLS

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
        - bedrock (default): Amazon Bedrock con Claude Sonnet 4
        - ollama: Modelo local via Ollama (gratis, privado)

    Variables de entorno:
        - NAS_AGENT_MODEL: bedrock | ollama
        - NAS_AGENT_MODEL_ID: Override del model_id
        - AWS_REGION: Región para Bedrock (default: us-east-1)
        - OLLAMA_HOST: Host de Ollama (default: http://localhost:11434)
    """
    proveedor = os.environ.get("NAS_AGENT_MODEL", "bedrock").lower()
    model_id_override = os.environ.get("NAS_AGENT_MODEL_ID")

    if proveedor == "bedrock":
        from strands.models.bedrock import BedrockModel
        model_id = model_id_override or "us.anthropic.claude-sonnet-4-20250514-v1:0"
        return BedrockModel(
            model_id=model_id,
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
        )

    elif proveedor == "ollama":
        from strands.models.ollama import OllamaModel
        model_id = model_id_override or "llama3.1"
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return OllamaModel(model_id=model_id, host=host)

    else:
        raise ValueError(
            f"Proveedor '{proveedor}' no soportado.\n"
            f"Opciones: bedrock, ollama\n"
            f"Configura con: export NAS_AGENT_MODEL=<opción>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Crear el Agente
# ─────────────────────────────────────────────────────────────────────────────


def create_nas_agent() -> Agent:
    """Crea y retorna el agente NAS configurado."""
    model = get_model()

    agent = Agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )

    return agent


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada
# ─────────────────────────────────────────────────────────────────────────────


def main():
    """Punto de entrada principal del agente NAS."""
    print("🖥️  nas-agent — Administrador inteligente de NAS")
    print("=" * 50)

    # Obtener query del usuario
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\n📝 Query: {query}\n")
    else:
        print("\n¿Qué necesitas?")
        print("  Ejemplos:")
        print("  - ¿Qué servicios están corriendo?")
        print("  - Quiero instalar Vaultwarden")
        print("  - El nextcloud está lento, diagnostica")
        print("  - ¿Hay conflictos de puertos?")
        print("  - Hazme backup de grafana")
        print()
        query = input("🖥️ > ")
        if not query.strip():
            print("❌ No se proporcionó ninguna query.")
            sys.exit(0)

    # Crear y ejecutar el agente
    print("⚡ Inicializando agente...")
    try:
        agent = create_nas_agent()
    except Exception as e:
        print(f"\n❌ Error al inicializar: {e}")
        print("\nVerifica:")
        print("  - AWS credentials (para Bedrock)")
        print("  - Ollama corriendo (para Ollama)")
        print("  - export NAS_AGENT_MODEL=ollama  (para usar local)")
        sys.exit(1)

    print("🚀 Procesando...\n")
    print("-" * 50)
    result = agent(query)
    print("-" * 50)
    print("\n✅ Tarea completada.")

    return result


if __name__ == "__main__":
    main()
