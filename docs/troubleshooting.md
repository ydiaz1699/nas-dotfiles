# Troubleshooting — Diagnósticos resueltos

Problemas reales encontrados y resueltos en el desarrollo/uso de nas-dotfiles.
Cada entrada documenta síntoma, causa raíz y solución.

---

## auto_catalog() — NameError en stacks multi-servicio

**Síntoma:**
```
NameError: name 're' is not defined
```

**Causa:**
El módulo `re` no estaba importado en `discovery_tools.py`. Se agregó funcionalidad de regex para extraer variables `${VAR}` pero faltaba el import.

**Solución:**
```python
import re  # agregar al inicio de discovery_tools.py
```

**Commit:** `fix: corregir NameError en auto_catalog() para stacks multi-servicio` (PR #24)

---

## auto_catalog() — Solo leía el primer servicio del compose

**Síntoma:**
Al ejecutar `auto_catalog("datasql")`, solo se catalogaba `postgres` (el primer servicio) e ignoraba `pgadmin` y `redis` definidos en el mismo compose.

**Causa:**
El código hacía `list(services.items())[0]` para obtener solo el primer servicio en vez de iterar todos.

**Solución:**
Iterar sobre **todos** los servicios del compose y generar metadata para cada uno:
```python
for svc_name, svc_config in services.items():
    # procesar cada servicio
```

**Commit:** `fix: auto_catalog() ahora lee TODOS los servicios del compose` (PR #22)

---

## bulk_discover() — except duplicado inalcanzable

**Síntoma:**
Un bloque `except Exception` estaba duplicado, el segundo nunca se ejecutaba.

**Causa:**
Copy-paste al agregar manejo de errores. Python solo ejecuta el primer `except` que matchea.

**Solución:**
Eliminar el `except` duplicado y consolidar la lógica de error en uno solo.

**Commit:** `fix: corregir 2 bugs en auto_catalog() y bulk_discover()` (PR #25)

---

## bulk_discover() — return con variables inexistentes

**Síntoma:**
```
NameError: name 'image' is not defined
```
al finalizar `bulk_discover()`.

**Causa:**
El return final usaba nombres de variables viejas (`image`, `port_external`, `volumes`, `env_list`) que fueron renombradas a `main_image`, `first_port_external`, `all_volumes`, `all_env_list` en un refactor anterior.

**Solución:**
Actualizar el return para usar los nombres correctos de las variables.

**Commit:** `fix: corregir 2 bugs en auto_catalog() y bulk_discover()` (PR #25)

---

## Agente recuerda sesiones viejas (contexto stale)

**Síntoma:**
El agente responde con información de sesiones anteriores que ya no es relevante. Por ejemplo, sigue hablando de un servicio que ya se diagnosticó hace 3 sesiones.

**Causa:**
La sesión persistente (`FileSessionManager`) no se reseteaba al cambiar de tema. El timeout de 30 min no había vencido.

**Solución:**
```bash
agent --clear     # borrar sesión manualmente
agent --new "nueva tarea"  # forzar sesión nueva
```

El auto-reset ocurre tras 30 min de inactividad (configurable con `NAS_AGENT_SESSION_TIMEOUT`).

---

## Git — conflictos al hacer `gpl` (git pull)

**Síntoma:**
```
error: Your local changes to the following files would be overwritten by merge
```

**Causa:**
Archivos modificados localmente que también cambiaron en el remoto. Común con archivos de log o configuración generada.

**Solución:**
```bash
# Si los cambios locales NO importan:
git checkout -- archivo_conflictivo
gpl

# Si los cambios locales SÍ importan:
gst        # stash
gpl        # pull
gstp       # stash pop → resolver conflictos si los hay
```

---

## Probar tools del agente manualmente

**Síntoma:**
Quieres verificar que una tool funciona sin invocar todo el agente (sin gastar tokens).

**Solución:**
```bash
cd /nas-dotfiles

# Probar una tool directamente con Python
python3 -c "
from agent.tools.discovery_tools import auto_catalog
result = auto_catalog('emqx')
print(result)
"

# Probar list_services
python3 -c "
from agent.tools.discovery_tools import list_services
print(list_services())
"

# Probar memory_stats
python3 -c "
from agent.tools.memory_tools import memory_stats
print(memory_stats())
"
```

> **Nota:** Las tools `@tool` se pueden invocar como funciones normales pasando los argumentos directamente.

---

## svc doctor — contadores siempre en 0 (subshell bug)

**Síntoma:**
`svc doctor` reportaba 0 errores y 0 warnings incluso cuando había problemas visibles en la salida.

**Causa:**
Los contadores `issues` y `warnings` se incrementaban dentro de un pipe (`comando | while read`). Bash crea un subshell para el lado derecho del pipe, así que las variables no sobreviven al loop.

**Solución:**
Reemplazar:
```bash
# MAL — subshell pierde el contador
docker ps | while read -r line; do
    ((issues++))
done
```

Por:
```bash
# BIEN — process substitution preserva variables
while read -r line; do
    ((issues++))
done < <(docker ps)
```

---

## pipins — PEP 668 (externally-managed-environment)

**Síntoma:**
```
error: externally-managed-environment
```
al intentar `pipins rich` en Python 3.12+.

**Causa:**
Debian/Ubuntu con Python 3.12+ marcan el entorno como "externally managed" para proteger paquetes del sistema.

**Solución:**
`pipins` detecta automáticamente esta situación y agrega `--break-system-packages`. Si prefieres un entorno aislado, usa un venv:
```bash
python3 -m venv ~/.venv
source ~/.venv/bin/activate
pipins rich typer
```

---

## svc create — genera docker-compose.yml en vez de compose.yml

**Síntoma:**
El template de `svc create` generaba un archivo llamado `docker-compose.yml`, pero la convención del proyecto es `compose.yml`.

**Causa:**
El template de `svc_create()` en `extras.sh` usaba el nombre legacy.

**Solución:**
Actualizar el template para usar `compose.yml`. La función `svc_compose_file()` en `discovery.sh` busca ambos nombres por compatibilidad, pero los nuevos servicios deben usar el nombre preferido.

> **Nota:** `svc` detecta automáticamente: `compose.yml` → `compose.yaml` → `docker-compose.yml` → `docker-compose.yaml` (en ese orden de prioridad).

---

## Daemon — no arranca con systemd

**Síntoma:**
```bash
sudo systemctl status nas-agent
# Active: failed
```

**Causa común:** Falta la API key o el archivo `.env.agent`:
```bash
cat /nas-dotfiles/.env.agent
# Si está vacío o no existe → el daemon no puede inicializar el agente
```

**Solución:**
```bash
# Verificar que .env.agent tiene las variables necesarias
cat /nas-dotfiles/.env.agent

# Mínimo para Gemini:
echo "NAS_AGENT_MODEL=gemini" > /nas-dotfiles/.env.agent
echo "GOOGLE_API_KEY=tu-key" >> /nas-dotfiles/.env.agent
chmod 600 /nas-dotfiles/.env.agent

# Reiniciar
sudo systemctl restart nas-agent
journalctl -u nas-agent -f   # ver logs en vivo
```

---

## Variables de datasql — confusión entre fijas y externas

**Síntoma:**
`auto_catalog("datasql")` reportaba todas las variables como `env_required`, incluyendo las que tienen valor fijo (como `PGDATA=/var/lib/...`).

**Causa:**
El código no distinguía entre variables con valor literal fijo en el compose y variables que usan interpolación `${VAR}` (que sí requieren `.env`).

**Solución (implementada):**
Hacer una segunda pasada por todo el YAML con regex `r'\$\{([A-Z_]+)\}'` para detectar interpolaciones. Variables con valor literal → no son `env_required`. Variables con `${VAR}` → sí son `env_required`.

Las 7 variables externas reales de datasql son:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `TZ`
- `PGADMIN_EMAIL`, `PGADMIN_PASSWORD`
- `REDIS_PASSWORD`

---

## Principio general para depurar

```bash
# 1. Verificar que el módulo se importa sin errores
python3 -c "from agent.tools.discovery_tools import auto_catalog; print('OK')"

# 2. Verificar el compose del servicio
svc config nombre-servicio

# 3. Revisar logs del daemon
journalctl -u nas-agent --since "10 min ago"

# 4. Modo verbose del agente
NAS_AGENT_LOG_LEVEL=DEBUG agent "diagnostica emqx"

# 5. Dry-run (no ejecuta nada destructivo)
NAS_AGENT_DRYRUN=1 agent "reiniciar emqx"
```
