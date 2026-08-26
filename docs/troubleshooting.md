# Troubleshooting — Diagnósticos resueltos

Problemas reales encontrados y resueltos en el desarrollo/uso de nas-dotfiles.
Cada entrada documenta síntoma, causa raíz y solución.

---

## DataSQL — `failed to set up container networking: Address already in use`

**Síntoma:**

```text
failed to set up container networking: Address already in use
```

**Causa raíz:** el Compose legacy fijaba `ipv4_address` para PostgreSQL,
pgAdmin y Redis (`172.20.0.4`, `172.20.0.3` y `172.20.0.5`) dentro de la red
externa y compartida `db_net`. El conflicto era de direccionamiento interno de
Docker, no de un listener TCP del host.

**Por qué cambiar puertos o ejecutar `restart` no lo resolvió:** cambiar
`5050` o `5432` solo cambia una publicación host↔contenedor; no libera una IP
estática dentro de `db_net`. Además, `svc restart datasql` reinicia los
contenedores existentes, pero no recrea la red ni reemplaza sus IPs fijas.

**Diagnóstico seguro:**

```bash
svc config datasql
svc ps datasql
svc port-map
ss -ltnp | grep -E ':(5432|5050)\b' || true
svc net
```

Si el error es `bind: address already in use` y `ss` muestra otro proceso,
es un conflicto de puerto del host. Si los puertos están libres pero el Compose
resuelto conserva `ipv4_address`, es el conflicto de IP interna descrito aquí.

**Solución canónica:** quitar todos los bloques `ipv4_address` y dejar que
Docker asigne IPs dinámicas. Mantener `db_net`; no eliminarla ni ejecutar
`docker network prune`, porque otros servicios pueden usarla. Para aplicar el
Compose corregido:

```bash
svc snapshot datasql
# Si Python todavía responde "No such command 'snapshot'":
NAS_CLI=bash svc snapshot datasql

cp "$NAS_DOTFILES/agent/catalog/services/datasql/compose.yml" \
   "$dkco/datasql/compose.yml"
svc config datasql
# DETENERSE si la salida muestra `ipv4_address`.
# Continuar solo si conserva `db_net` como external y PostgreSQL aparece
# publicado en loopback (`127.0.0.1:5432:5432`), nunca en 0.0.0.0/LAN.
svc down datasql
svc up datasql
svc ps datasql
svc net
svc port-map
```

La configuración final conserva PostgreSQL publicado solo en
`127.0.0.1:5432:5432` para el Recorder de Home Assistant, y usa
`datapostgres:5432` para consumidores que sí están en `db_net`. No cambiarlo a
`0.0.0.0:5432:5432` ni eliminar la publicación loopback.

La guía completa y el Compose canónico están en
[`docs/services/aipostgres-guide.md`](services/aipostgres-guide.md). Home Assistant
se debe levantar después de que DataSQL esté saludable:

```bash
svc up datasql
svc ps datasql
svc up homeassistant
svc ps homeassistant
```

---

## `svc snapshot` — CLI Python sin el comando registrado

**Síntoma:**

```text
No such command 'snapshot'.
```

**Causa:** el NAS estaba ejecutando una versión anterior del CLI Python que no
registraba el subcomando. La implementación de snapshot vive en Bash y guarda
solo la configuración ligera del servicio (Compose y `.env`), no los datos
pesados.

**Workaround inmediato, antes de actualizar el checkout del NAS:**

```bash
NAS_CLI=bash svc snapshot datasql
```

Para volver atrás desde ese mismo checkout:

```bash
NAS_CLI=bash svc rollback datasql
```

**Solución permanente:** actualizar el checkout del NAS con el fix ya integrado
en `main`:

```bash
nasfk
gs
# Esta secuencia asume que el checkout está en `main` y el árbol está limpio.
gpl
NAS_CLI=bash svc --help | grep -E 'snapshot|rollback'
NAS_CLI=python svc --help | grep snapshot
svc snapshot datasql
```

El Python CLI actual registra `snapshot` y delega mediante `bash_bridge.py` a la
misma implementación Bash; no se debe duplicar `svc_snapshot` en Python.
`rollback` continúa siendo un comando Bash, por lo que el fallback explícito
`NAS_CLI=bash svc rollback <servicio>` sigue siendo válido.

---

## Variables globales y locales — bucle de verificación correcto

No usar `for var in for var in ...`: la repetición accidental del encabezado
convierte el comando en una construcción inválida o hace que se compruebe una
variable llamada `for`. La forma correcta, sin imprimir secretos, es:

```bash
for var in SERVER_IP TZ; do
  if ! grep -q "^${var}=" "$dkco/.env"; then
    echo "Falta $var en $dkco/.env"
  fi
done

for var in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD \
           PGADMIN_EMAIL PGADMIN_PASSWORD REDIS_PASSWORD; do
  if ! grep -q "^${var}=" "$dkco/datasql/.env"; then
    echo "Falta $var en $dkco/datasql/.env"
  fi
done
```

Si falta una variable, crear primero el archivo/directorio correspondiente,
completarlo y aplicar permisos; no ejecutar `source .env`, porque las
contraseñas pueden contener caracteres especiales.

---

## API/LLM — `Too many requests, please wait before trying again`

**Síntoma:**

```text
Error: Too many requests, please wait before trying again.
Request ID: <id>
```

**Causa:**

Es un límite temporal del proveedor de la API/LLM (rate limit). No lo provoca
Docker, EMQX, el NAS, la red local ni un `compose.yml` incorrecto. El `Request ID`
identifica el intento rechazado y debe conservarse si hay que reportar el incidente.

**Prevención durante sesiones largas:**

1. No enviar repetidamente `continuar`, la misma pregunta o el mismo comando
   mientras una solicitud anterior todavía está procesándose.
2. Esperar a que termine cada respuesta antes de iniciar la siguiente acción.
3. Agrupar preguntas relacionadas en un solo mensaje, evitando reintentos
   idénticos consecutivos.
4. Pedir al agente que trabaje por etapas y que valide varias cosas juntas cuando
   sea seguro, en vez de lanzar muchas solicitudes pequeñas sin pausa.
5. Para una sesión larga, guardar el contexto en `_drafts/SESSION-<fecha>-<tema>.md`
   usando `docs/session-handoff.md`; así no es necesario reconstruir todo el
   contexto con varios mensajes al abrir una nueva sesión.
6. Si el agente ya indicó que está bloqueado por rate limit, no repetir la misma
   solicitud inmediatamente: esperar y luego hacer un único reintento.

**Recuperación:**

1. Detener los reintentos durante unos minutos; el tiempo exacto depende del
   proveedor y no se puede determinar desde el NAS.
2. Conservar el mensaje completo y su `Request ID`.
3. Reintentar una sola vez con una solicitud más compacta, incluyendo solo el
   objetivo pendiente y el contexto imprescindible.
4. Si vuelve a ocurrir, esperar más tiempo o cambiar temporalmente de sesión/modelo
   si la plataforma lo permite. No modificar Docker, reiniciar servicios ni cambiar
   credenciales del NAS para resolver este error.
5. Si persiste, reportar el `Request ID` al proveedor de la API/plataforma.

**Diagnóstico rápido:**

| Pregunta | Interpretación |
|----------|----------------|
| ¿El mensaje dice `Too many requests`? | Rate limit del proveedor/LLM |
| ¿Aparecen `docker`, `compose`, `EMQX` o `connection refused`? | Posible problema del NAS/servicio; diagnosticar aparte |
| ¿Solo falla una solicitud del agente y los comandos locales funcionan? | No tocar la configuración del NAS |

**Lección:**

Un rate limit no se corrige con `svc restart`, `svc recreate`, cambios en `.env` ni
reiniciando EMQX. Se resuelve reduciendo la frecuencia de solicitudes y esperando la
ventana de recuperación del proveedor.

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
nasfk

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


---

## WARN "variable is not set" en svc up/down

**Síntoma:**
```
WARN[0000] The "SERVER_IP" variable is not set. Defaulting to a blank string.
```

**Causa:**
Docker Compose interpola `${VAR}` en el compose.yml (labels, ports, etc.) buscando en:
1. Variables del shell (prioridad más alta)
2. `--env-file` pasado en la línea de comandos
3. `.env` del directorio del compose

Si la variable no está en el shell al momento de ejecutar, Docker da el warning aunque `--env-file` la tenga.

**Solución:**
`init.sh` exporta automáticamente las variables de `$dkco/.env` al shell. Si ves el warning, es porque no recargaste el shell después de crear `$dkco/.env`:

```bash
# Forzar recarga (el reload normal no funciona por protección anti-doble-carga)
_SHELL_RELOAD=1 source ~/.bashrc

# Verificar
echo $SERVER_IP    # debe mostrar tu IP
```

Si no existe `$dkco/.env`, crearlo:
```bash
cat > $dkco/.env << 'EOF'
SERVER_IP=192.168.1.200
TZ=America/La_Paz
EOF
chmod 600 $dkco/.env
_SHELL_RELOAD=1 source ~/.bashrc
```

---

## env_file en compose NO sirve para interpolar labels

**Síntoma:**
Tienes `env_file: .env` en el compose con `FILEBROWSER_USER=admin`, pero en los labels `${FILEBROWSER_USER}` sigue dando warning.

**Causa:**
`env_file:` en el compose solo inyecta variables **dentro del contenedor**. NO sirve para interpolar el YAML (`labels:`, `ports:`, etc.).

Para interpolar el YAML, Docker Compose necesita que la variable esté en:
- El shell (exportada)
- Un `--env-file` pasado en la línea de comandos (lo que hace `svc`)
- Un archivo `.env` en el directorio del compose

**Solución:**
`svc` ya pasa automáticamente `--env-file $dkco/.env` (global) y `--env-file $dkco/<servicio>/.env` (local). Ambos se usan para interpolación del YAML. No necesitas hacer nada extra.
