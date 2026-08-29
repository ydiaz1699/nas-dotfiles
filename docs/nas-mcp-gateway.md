# nas-mcp-gateway

> **Estado:** preparado en código y catálogo; todavía no desplegado ni conectado
> al NAS runtime. La integración histórica `lobehub-mcp` se conserva sin cambios.

## Objetivo

`nas-mcp-gateway` es la evolución independiente del gateway MCP histórico de
LobeHub. LobeHub, Kiro y Claude pueden ser clientes; ninguno es dueño del
proceso ni de su configuración.

La arquitectura implementada separa cuatro responsabilidades:

```text
Skill/manifest ligero
        │ describe capacidades y reglas de activación
        ▼
front-door MCP
        │ responde initialize/tools/list sin iniciar operaciones Docker
        ▼  primer tools/call
worker lazy
        │ proceso temporal; idle timeout configurable
        ▼
helper systemd read-only
        │ allowlist fija; nunca acepta comandos del cliente
        ▼
svc + framework nas-dotfiles
```

## Qué está implementado

- `agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json`: fuente canónica de nombres, descripciones,
  esquemas, timeouts y política lazy.
- `agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py`: front-door MCP compatible con
  `stdio` y un modo HTTP interno opcional.
- `agent/mcp/nas_mcp_gateway/nas_mcp_worker.py`: worker cliente y helper host con allowlist fija.
- `systemd/nas-mcp-helper.service`: unidad host separada de LobeHub.
- `agent/mcp/nas_mcp_gateway/Dockerfile`: imagen mínima del front-door HTTP.
- `agent/catalog/services/nas-mcp-gateway/`: compose, ficha y ejemplo de
  entorno para un despliegue posterior.
- `.kiro/skills/nas-mcp-gateway/SKILL.md`: reglas de uso y activación del
  gateway sin copiar el manifest.

La allowlist inicial es deliberadamente pequeña:

| Herramienta | Operación fija | Mutación |
|---|---|:---:|
| `nas_services` | `svc lista` | No |
| `nas_health` | `svc health` | No |
| `nas_capabilities` | `svc capabilities` | No |
| `nas_diagnostics` | `svc doctor` sin historial persistente | No |

El diagnóstico reutiliza las comprobaciones de `svc doctor`, pero el helper fija
`SVC_DOCTOR_NO_HISTORY=1` para impedir que esa llamada cree o modifique
`doctor-history.log`; la superficie publicada sigue siendo read-only.

## Activación lazy

El front-door permanece disponible para que el cliente MCP pueda completar
`initialize` y `tools/list`. Eso es necesario porque el cliente debe conocer
las herramientas antes de decidir cuál usar.

El worker no se inicia durante `initialize` ni `tools/list`. Solo se crea al
recibir `tools/call`. Después de `NAS_MCP_IDLE_SECONDS` sin llamadas, el
front-door termina el worker. El valor predeterminado es 600 segundos y nunca
se reduce por debajo de 30 segundos.

Este diseño no pretende que una Skill ejecute Docker. La Skill aporta contexto,
selección y reglas de activación; el front-door cumple el protocolo MCP y el
helper conserva la frontera de privilegios.

## Manifest canónico y Skill

La Skill no mantiene una segunda lista manual de herramientas. El archivo
canónico es:

```text
agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json
```

La Skill lo referencia y describe cómo decidir cuándo solicitar una capacidad.
En una etapa posterior se puede generar automáticamente el bloque de
`tools/list`, documentación y catálogo desde ese manifest. Si el manifest y el
worker no coinciden, la validación debe fallar antes de desplegar.

## Transportes

### `stdio` — recomendado para Kiro/Claude locales o vía SSH

El cliente inicia el front-door bajo demanda:

```bash
NAS_DOTFILES="${NAS_DOTFILES:?carga el entorno del repositorio}"
NAS_MCP_MODE=stdio \
NAS_MCP_IDLE_SECONDS=600 \
MCP_HELPER_SOCKET=/run/nas/nas-mcp-gateway.sock \
python3 "$NAS_DOTFILES/agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py" --mode stdio
```

El proceso `stdio` necesita poder conectarse al socket del helper. Para un
cliente remoto, el proceso debe ejecutarse en el NAS o mediante un canal SSH
controlado; un cliente Web externo no puede resolver automáticamente un socket
Unix del NAS.

### HTTP — preparado para un adaptador/proxy posterior

El catálogo incluye un front-door HTTP interno en el puerto `8791`, sin
publicarlo a la LAN. El endpoint configurado sería:

```text
http://nas-mcp-gateway:8791/mcp
```

El modo HTTP requiere `MCP_SERVICE_TOKEN` y acepta `Authorization: Bearer
<token>`. El token no debe aparecer en URLs, logs ni documentación. Para acceso
remoto se necesita un proxy HTTPS con autenticación, límites y una política de
red explícita. No publicar directamente el puerto desde el NAS.

## Helper host

La unidad nueva es:

```text
systemd/nas-mcp-helper.service
```

Usa el socket independiente:

```text
/run/nas/nas-mcp-gateway.sock
```

El helper se ejecuta como `aadm` con grupos `docker nas-mcp`, elimina y recrea
el socket al iniciar, y ejecuta únicamente los argumentos constantes definidos
en `agent/mcp/nas_mcp_gateway/nas_mcp_worker.py`. El gateway no recibe Docker socket.

Antes de instalarlo en el NAS hay que crear la configuración local desde el
example y completar el GID real de `nas-mcp`; no copiar secretos al chat:

```bash
# En una instalación autorizada, respetar el orden: carpeta → archivo → permisos.
sudo install -d -o aadm -g aadm -m 0750 /etc/nas
sudo install -o root -g root -m 0644 \
  "$NAS_DOTFILES/systemd/nas-mcp-helper.service" \
  /etc/systemd/system/nas-mcp-helper.service
sudo install -o root -g root -m 0640 \
  "$NAS_DOTFILES/systemd/nas-mcp-helper.env.example" \
  /etc/nas/nas-mcp-helper.env
```

La instalación real requiere adaptar el example al GID local, recargar
systemd, comprobar el socket y solo después iniciar el helper. Esta guía no
autoriza a habilitarlo todavía: el estado del proyecto es **preparado, no
runtime-verificado**.

## Compose independiente

El compose catalogado está en:

```text
agent/catalog/services/nas-mcp-gateway/compose.yml
```

Usa `env_file: [../.env, .env]`, no publica puertos, monta únicamente el socket
read-only y pertenece a `nas_mcp_net`. El bind se configura con
`create_host_path: false`: el helper debe estar activo y el socket debe existir
antes de crear el contenedor; así Docker no puede convertir una ruta ausente en
un directorio que bloquee el socket Unix. La ruta del compose de catálogo se
normaliza a `../_common.yml` cuando se exporta a `$dkco/nas-mcp-gateway/`.

Para una futura instalación, el orden operativo será:

```bash
mkdir -p "$dkco/nas-mcp-gateway"
# copiar compose.yml y .env.example; completar .env local sin compartirlo
chmod 600 "$dkco/nas-mcp-gateway/.env"
# comprobar helper/socket y después validar/levantar mediante svc
NAS_CLI=bash svc config nas-mcp-gateway
NAS_CLI=bash svc up nas-mcp-gateway
NAS_CLI=bash svc ps nas-mcp-gateway
```

No ejecutar esta secuencia todavía como parte de esta implementación local.
El front-door `stdio` no necesita Compose.

## Seguridad y límites

- No hay Docker socket en el front-door.
- El helper no incorpora argumentos enviados por el cliente.
- Las operaciones son read-only y usan timeouts fijos.
- La salida se limita a líneas sanitizadas, truncadas y sin stderr crudo.
- Los audit logs solo contienen herramienta, resultado, duración y timestamp.
- HTTP exige Bearer token; `health` es el único endpoint sin autenticación para
  el healthcheck local.
- `MCP_ALLOWED_ORIGINS` restringe peticiones HTTP que incluyan `Origin`.
- El worker se termina tras inactividad, pero el front-door `stdio` sigue vivo
  mientras el cliente mantenga la sesión.

## Compatibilidad con el gateway histórico

No se reemplaza todavía:

```text
agent/lobehub_mcp.py
systemd/lobehub-mcp-helper.service
agent/catalog/services/lobehub/compose.yml
```

La integración histórica de LobeHub continúa siendo una superficie separada
hasta que `nas-mcp-gateway` tenga validación runtime, cliente probado y una
estrategia de migración aprobada. No conectar ambos helpers al mismo socket ni
reutilizar `LOBEHUB_MCP_TOKEN` como token del gateway nuevo.

## Validación pendiente antes del despliegue

1. Validar el protocolo `stdio` con `initialize`, `tools/list` y una llamada
   bloqueada por helper ausente.
2. Ejecutar el worker con un helper simulado y comprobar las cuatro operaciones.
3. Validar `bash -n` de los comandos documentados y `py_compile` de ambos módulos.
4. Ejecutar el scanner e índice del proyecto.
5. Probar el compose en un entorno autorizado, sin publicar `8791`.
6. Solo después decidir la conexión de LobeHub, Kiro o Claude y la política de
   socket activation/HTTP remoto.
