# Cómo extender el framework

## Nuevo comando svc (bash)

1. Crear función `svc_nombre()` en `docker/cli/lib/<módulo>.sh`
2. Registrar en `svc.sh` (case statement en sección global o con-servicio)
3. Agregar a autocompletado en `shell/lib/docker.sh`
4. Documentar en `docker/cli/lib/help.sh`

## Nueva tool del agente (Python)

1. Función decorada con `@tool` en `agent/tools/<módulo>.py`
2. Usar `safe_run()` de `agent/tools/_shell.py` (nunca subprocess)
3. Exportar en `agent/tools/__init__.py` → lista `ALL_TOOLS`
4. Si destructiva: agregar a `_DESTRUCTIVE_TOOLS` en `_shell.py`
5. Documentar en bloques del system prompt en `nas_agent.py`

Ejemplo:
```python
from strands.tools import tool
from agent.tools._shell import safe_run, validate_service_name

@tool
def mi_tool(service: str) -> str:
    """Descripción para el LLM."""
    validate_service_name(service)
    result = safe_run(["docker", "inspect", service])
    return result.stdout
```

## Nuevo plugin del agente

1. Crear clase en `agent/plugins/<nombre>_plugin.py`
2. Heredar de `BasePlugin`
3. Definir `meta = PluginMeta(name="...", description="...")`
4. Implementar `setup()`:
   - `self.register_tool(func)` — tool adicional
   - `self.register_event(EventHandler(...))` — listener
   - `self.register_schedule(ScheduleConfig(...))` — tarea periódica
5. Se auto-descubre por `loader.py` al arrancar daemon

Ejemplo:
```python
from agent.plugins.base import BasePlugin, PluginMeta, ScheduleConfig, EventHandler

class MiPlugin(BasePlugin):
    meta = PluginMeta(name="mi_plugin", description="Descripción corta")

    def setup(self):
        self.register_schedule(ScheduleConfig(
            name="hourly-check",
            handler=self._hourly_check,
            interval_minutes=60,
        ))
        self.register_event(EventHandler(
            event_type="docker.unhealthy",
            handler=self._on_unhealthy,
            description="Reaccionar a contenedor unhealthy",
        ))

    def _hourly_check(self):
        pass

    def _on_unhealthy(self, event: dict):
        pass
```

## Nuevo módulo del shell

1. Crear archivo en `shell/lib/<nombre>.sh`
2. Agregar al array de módulos en `shell/init.sh`:
   ```bash
   for _mod in aliases nav docker system instal pipins git completions prompt <nombre>
   ```
3. Si necesita completions: agregar función en `shell/lib/completions.sh`
4. Si necesita variable global: exportar en `shell/init.sh` después de cargar user.conf

## Nuevo destino de navegación

```bash
# En shell/lib/nav.sh o un módulo nuevo:
sc()  { _nav "$HOME/scripts" "$@"; }
scf() { _nav_fzf "$HOME/scripts" "sc›"; }
_sc_completions() { _nav_complete "$HOME/scripts"; }
complete -F _sc_completions sc
```
