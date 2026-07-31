# Guia completa — nas-dotfiles

Framework completo para administrar un servidor Linux/NAS con Docker. Convierte la terminal en una consola de administracion con tres capas: shell personalizado, CLI de Docker, y un agente de IA que entiende lenguaje natural.

---

Este proyecto no es una aplicacion. Es un **entorno de administracion** que se instala en el NAS y queda disponible en cualquier terminal. Tiene tres componentes principales:

1. **Shell framework** — Personaliza Bash con aliases, prompt informativo, navegacion rapida.
2. **CLI Docker (`svc`)** — Administra servicios Docker con un solo comando.
3. **Agente IA (`agent`)** — Administra el NAS con lenguaje natural (Python + Strands SDK).

---

# Filosofia

Todo el codigo vive exclusivamente en `/nas-dotfiles/`. Ruta fija, independiente del usuario. No se crean symlinks. El unico rastro fuera son 2 lineas en cada `.bashrc`.

Borrar el proyecto:

```
./uninstall.sh && sudo rm -rf /nas-dotfiles/
```

---

# Arquitectura

```
/nas-dotfiles/          <-- TODO el codigo (ruta fija)
    shell/              <-- Shell framework (aliases, prompt, navegacion)
    docker/cli/         <-- CLI bash para Docker (comando svc)
    agent/              <-- Agente IA con tools (Python, Strands SDK)

/docker/                <-- SOLO datos de servicios Docker (no codigo)
    nextcloud/compose.yml
    plex/compose.yml
    backups/
    ...
```

Principio: El codigo vive en `/nas-dotfiles/`. Los datos de servicios viven en `/docker/`. No se mezclan.

---

# Estructura de archivos

```
nas-dotfiles/
    setup                       Entry point universal
    install.sh                  Bash interactivo (fallback sin Python)
    uninstall.sh                Revertir instalacion
    requirements.txt            Dependencias Python del agente
    pyproject.toml              Config: ruff, pytest, mypy
    shell/
        init.sh                 Loader principal
        scripts/
            start-all.sh        Levantar servicios en orden
            stop-all.sh         Detener + apagar NAS
            restart-all.sh      Detener + reiniciar NAS
            install_docker.sh   Instalar Docker Engine en Debian
        lib/
            aliases.sh          Aliases del sistema
            nav.sh              Navegacion rapida
            docker.sh           Autocompletado de svc
            system.sh           Dashboard, disk, netinfo, logs
            instal.sh           Wrapper inteligente de apt
            prompt.sh           Prompt con docker + disco + git
            git.sh              Aliases de git
            completions.sh      Completions adicionales
    docker/cli/
        svc.sh                  CLI principal de servicios Docker
        lib/
            discovery.sh        Descubrimiento automatico
            health.sh           Dashboard de salud
            backup.sh           Backup y restore de volumenes
            docker.sh           update-all
            extras.sh           port-map, size, net, doctor, diff, watch, create
            menu.sh             TUI interactivo con fzf
            help.sh             Ayuda
    agent/
        nas_agent.py            Entry point (sesion + Rich UI)
        config/
            defaults.yml        Configuracion centralizada
        core/                   Logica de negocio
        tools/                  23 herramientas @tool
        plugins/                Sistema de plugins dinamicos
        events/                 Event bus + MQTT listener
        scheduler/              Tareas periodicas
        cache/                  Cache KV con TTL
        catalog/                Catalogo de servicios
    tests/
    logs/
        packages.txt            Historial de paquetes instalados
    ui/
        setup.py                Instalador TUI (Rich + InquirerPy)
```

---

# 1. Shell Framework

Cuando se abre una terminal, `init.sh` carga todos los modulos:

```
aliases  nav  docker  system  instal  git  completions  prompt
```

Ademas agrega al PATH:

```
/nas-dotfiles/shell/scripts
~/.cargo/bin
```

Y define dos alias globales:

```
svc     -->  el CLI de Docker
agent   -->  el agente IA
```

Por eso ambos quedan disponibles desde cualquier carpeta.

---

# 2. Aliases

Define atajos para las operaciones mas comunes.

Por ejemplo:

```
ll
```

equivale a

```
eza -lah
```

---

```
dps
```

equivale a

```
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

```
bat archivo.sh
```

equivale a

```
batcat --style=header,grid --paging=never archivo.sh
```

---

Tambien redefine operaciones de archivos para pedir confirmacion en terminal interactiva:

```
rm archivo.txt    -->  rm -iv archivo.txt (solo en TTY)
cp a b            -->  cp -iv a b
mv a b            -->  mv -iv a b
```

En pipes y scripts se comportan normal sin preguntar.

---

# 3. Navegacion inteligente

```
adm
```

Lleva a `/home/aadm`.

---

```
dk emqx
```

Lleva a `/docker/emqx`.

---

```
up 3
```

Sube 3 niveles de directorio.

---

```
dkf
```

Abre un buscador fuzzy (fzf) en `/docker/` para navegar visualmente.

---

```
admf
```

Igual pero en `/home/aadm`.

---

Todos tienen autocompletado con TAB.

---

# 4. Prompt dinamico

En vez del prompt clasico:

```
usuario@host:~$
```

Muestra:

```
aadm@Nas /docker/emqx (main*) 12↑ 71% $
```

Donde:

```
12↑     = 12 contenedores Docker corriendo
71%     = uso del disco raiz
(main*) = rama git + cambios sin commitear
```

Cambia de color si:
- Un comando fallo (simbolo rojo)
- El disco esta casi lleno (amarillo >75%, rojo >90%)
- Eres root (nombre en rojo)

El conteo de Docker se cachea 5 segundos y el disco 10 para no generar latencia.

---

# 5. Funcion instal()

En vez de usar:

```
apt install
```

Se usa:

```
instal nginx git vim
```

La funcion:
- Comprueba si ya esta instalado
- Comprueba si existe en los repos
- Instala unicamente los faltantes
- Usa `apt-fast` (mas rapido que apt)
- Guarda un historial en `logs/packages.txt`

Resultado:

```
✔ Ya instalado: git
✔ Instalados:   nginx vim
```

El log viaja con el framework para saber que herramientas hay disponibles en el NAS.

---

# 6. Dashboard del servidor

```
nas
```

Muestra un panel de monitoreo rapido:

```
--- NAS ------------------------------------------------
  uptime       3 days, 4 hours
  load         0.12 0.08 0.05
  memoria      2048 MB / 8192 MB (25%)

  discos
    12%   /                  24G / 200G
    67%   /mnt/datos         2.1T / 3.6T

  red
    eth0         192.168.1.100/24
    docker0      172.17.0.1/16

  docker
    12 corriendo   2 detenidos

  temperatura
    CPU:  +42.0°C
--------------------------------------------------------
```

Tambien hay:

```
disk        -->  uso de disco rapido
netinfo     -->  interfaces + puertos TCP en uso
logs        -->  tail del journal (ultimas 50 lineas)
logs -f     -->  follow en vivo
logs auth   -->  /var/log/auth.log
```

---

# 7. Administracion de Docker (svc)

Todo gira alrededor del comando:

```
svc
```

En lugar de escribir:

```
docker compose -f /docker/nextcloud/compose.yml up -d
```

Simplemente:

```
svc up nextcloud
```

---

# 8. Descubrimiento automatico

No hay lista fija de servicios. Busca automaticamente:

```
/docker/*/compose.yml
/docker/*/compose.yaml
/docker/*/docker-compose.yml
/docker/*/docker-compose.yaml
```

Cualquier carpeta dentro de `/docker/` con un archivo compose se convierte en un servicio.

```
svc lista
```

Los encuentra y muestra su estado con puntos de color:

```
  ● activo     adguard
  ● activo     emqx
  ● activo     homeassistant
  ○ detenido   spacedrive
  ○ detenido   vaultwarden
```

---

# 9. Comandos de svc

## Comandos globales (sin servicio)

```
svc lista           Lista servicios con estado (punto verde/rojo)
svc health          Dashboard de salud de todos los servicios
svc doctor          Chequeo de 6 puntos (disco, memoria, puertos, restarts)
svc update-all      Pull + recrear TODOS los servicios
svc port-map        Mapa global de puertos asignados
svc size            Consumo de disco por servicio
svc net             Mapa de redes Docker con contenedores
svc watch           Monitoreo continuo (refresh cada 5s)
svc create nombre   Scaffolding de nuevo servicio
svc menu            TUI interactivo con fzf
```

## Comandos con servicio

```
svc up nextcloud         Levantar
svc down nextcloud       Bajar y eliminar contenedores
svc restart nextcloud    Reiniciar
svc stop nextcloud       Detener
svc start nextcloud      Iniciar detenido
svc kill nextcloud       Forzar parada
svc update nextcloud     Pull + recrear (actualizar imagen)
svc logs nextcloud       Ver logs (follow, tail 200)
svc backup nextcloud     Exportar volumenes a tar.gz
svc restore nextcloud    Restaurar desde backup
svc depends nextcloud    Ver servicios y dependencias
svc open nextcloud       Abrir URL del servicio
svc env nextcloud        Ver/editar variables de entorno
svc diff nextcloud       Comparar compose en disco vs config resuelta
```

Cualquier comando nuevo de `docker compose` funciona automaticamente como passthrough.

---

# 10. Actualizacion

```
svc update emqx
```

Ejecuta:

```
docker compose pull
docker compose up -d --remove-orphans
```

Para actualizar todo de golpe:

```
svc update-all
```

---

# 11. Backup

```
svc backup nextcloud
```

1. Lee el compose
2. Obtiene los volumenes nombrados
3. Los monta en un contenedor Alpine
4. Los comprime a tar.gz
5. Guarda en `/docker/backups/`

Resultado:

```
  nextcloud_db_20260731_120000.tar.gz     ✓ 45M
  nextcloud_data_20260731_120000.tar.gz   ✓ 1.2G
```

---

# 12. Health

```
svc health
```

Produce una tabla con estado real de cada servicio:

```
  SERVICIO               ESTADO              DETALLE
  ● adguard              activo (1/1)        Up 3 days (healthy)
  ● emqx                 activo (1/1)        Up 3 days
  ● homeassistant        activo (1/1)        Up 2 days (healthy)
  ○ spacedrive           detenido
  ○ vaultwarden          detenido
```

---

# 13. Doctor

```
svc doctor
```

Chequeo de 6 puntos:
1. Disco (alerta si >80%)
2. Memoria (alerta si >80%)
3. Servicios detenidos
4. Conflictos de puertos
5. Contenedores con muchos restarts
6. Docker storage driver

---

# 14. Menu interactivo (fzf)

```
svc menu
```

Abre un menu TUI donde puedes:
- Elegir un servicio con preview en vivo (contenedores + imagenes)
- Seleccionar una accion (up, down, restart, logs, backup, etc.)
- Ejecutar sin escribir nada

Requiere `fzf` instalado.

---

# 15. Apertura automatica

```
svc open grafana
```

Detecta el puerto publicado y abre automaticamente:

```
http://localhost:3000
```

---

# 16. Autocompletado

```
svc <TAB>          -->  lista todos los comandos
svc up <TAB>       -->  lista servicios detectados
svc logs <TAB>     -->  lista servicios
svc health <TAB>   -->  nada (comando global)
```

---

# 17. Agente IA

El tercer componente — y el mas potente. Un agente Python que administra el NAS con lenguaje natural.

```
agent "que servicios estan caidos"
agent "revisar tasmoadmin"
agent "instalar vaultwarden"
agent "exportar todos los servicios al catalogo"
agent "que tengo en /home/aadm/scripts"
```

## Proveedores de IA

| Provider | Modelo | Costo | Setup |
|----------|--------|-------|-------|
| **Gemini** (default) | gemini-3.1-flash-lite | ~$0.08/1M tokens | Solo `GOOGLE_API_KEY` |
| **Bedrock** | Claude Sonnet 4 | ~$3/1M tokens | AWS credentials |
| **Ollama** | llama3.1 | Gratis | Ollama local |

## 23 herramientas

El agente tiene acceso a 23 tools que ejecuta autonomamente:

**Descubrimiento:** list_services, scan_compose, auto_catalog, bulk_discover, export_service

**Sistema:** scan_ports, disk_usage, memory_info, network_info, list_files, read_file_content

**Docker:** service_start, service_stop, service_restart, service_update, service_logs

**Compose:** create_service, validate_compose, read_compose

**Backup:** backup_service, restore_service, list_backups

**Diagnostico:** service_health, port_conflicts, troubleshoot

**Busqueda:** search_service_info (web fallback)

## Sesion persistente

El agente recuerda el contexto entre invocaciones:

```
agent "revisar tasmoadmin"      # Diagnostica
agent "si reiniciar"            # Sabe que te refieres a tasmoadmin
agent --status                  # Ver sesion actual
agent --new "instalar X"        # Forzar sesion nueva
agent --clear                   # Borrar memoria
```

Auto-reset tras 30 min de inactividad.

## Interfaz Rich

Output formateado con paneles coloreados, Markdown renderizado, indicadores de estado. Si Rich no esta instalado, degrada a texto plano.

## Sistema de plugins

Plugins se cargan dinamicamente y registran tools, eventos y tareas periodicas:

| Plugin | Funcion |
|--------|---------|
| docker | Health check cada 5 min |
| backup | Backup diario automatico |
| network | Escaneo de puertos cada 15 min |

## Event Bus + MQTT

Un bus interno pub/sub con matching exacto, wildcard y global. Se puede conectar a un broker MQTT (EMQX) para recibir comandos de Home Assistant o Node-RED:

```
mosquitto_pub -t "nas-agent/command/backup" -m '{"service":"emqx"}'
```

El agente ejecuta el backup automaticamente sin intervencion humana.

## Scheduler

Tareas periodicas estilo cron ejecutadas en hilos separados. Cada plugin puede registrar las suyas.

## Cache

Cache key-value en memoria con TTL (5 min default). Thread-safe con persistencia opcional a disco.

## Catalogo de servicios

Cada servicio se puede exportar al catalogo para ser portable:

```
agent "exportar emqx al catalogo"
```

Genera:
```
agent/catalog/services/emqx/
    ficha.md         Metadata (imagen, puertos, vars, redes)
    compose.yml      Config real copiada
    .env.example     Sin secretos (reemplazados por __pega_aqui__)
```

En una reinstalacion:
```
agent "recrear emqx desde el catalogo"
```

---

# 18. Seguridad

| Mecanismo | Que protege |
|-----------|-------------|
| `validate_service_name()` | Path traversal, inyeccion |
| `safe_run(shell=False)` | Inyeccion shell |
| `validated_service_path()` | Escape de DOCKER_BASE |
| `readonly_guard()` | Acciones destructivas del LLM |
| Dual dry-run | Ejecucion accidental |
| Audit log | Trazabilidad de todas las acciones |
| Sanitizacion de .env | Credenciales nunca llegan al LLM |
| Confirmacion para stop/restore | Acciones destructivas |

Credenciales nunca salen del NAS:
- `export_service` → `.env.example` con `__pega_aqui__`
- `read_file_content` → `***REDACTED***`
- `scan_compose` → variables sensibles redactadas

---

# 19. Variables de entorno

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `NAS_DOTFILES` | `/nas-dotfiles` | Ruta al proyecto |
| `DOCKER_BASE` | `/docker` | Ruta a datos de servicios |
| `NAS_AGENT_MODEL` | `gemini` | Provider: gemini, bedrock, ollama |
| `NAS_AGENT_MODEL_ID` | `gemini-3.1-flash-lite` | Override del modelo |
| `GOOGLE_API_KEY` | — | API key Gemini |
| `NAS_AGENT_SESSION_TIMEOUT` | `30` | Minutos para auto-reset |
| `NAS_AGENT_DRYRUN` | `0` | Solo mostrar plan |
| `NAS_AGENT_READONLY` | `0` | Bloquear acciones destructivas |
| `NAS_AGENT_AUDIT` | `1` | Habilitar audit log |
| `NAS_MQTT_HOST` | `localhost` | Host broker MQTT |
| `NAS_MQTT_PORT` | `1883` | Puerto MQTT |
| `NAS_MQTT_TOPICS` | `nas-agent/#` | Topics a suscribir |

---

# 20. Instalacion

```bash
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
sudo chown -R $(whoami):$(whoami) /nas-dotfiles
./setup
source ~/.bashrc
```

---

# 21. Requisitos

- Debian/Ubuntu (o derivado)
- Bash 4.2+
- Docker + Docker Compose v2
- Python 3.9+ (solo para el agente)
- `eza` (reemplazo de ls)
- Opcional: `fzf`, `bat`, `paho-mqtt`, `lm-sensors`

```bash
pip install -r requirements.txt
```

---

# 22. Uso resumido

```bash
# Shell
adm              cd /home/aadm
dk emqx          cd /docker/emqx
nas              dashboard del NAS
instal htop      instalar paquete (loguea automaticamente)
off              apagar NAS (detiene servicios primero)
restart          reiniciar NAS

# Docker CLI
svc lista        ver servicios con estado
svc up emqx      levantar servicio
svc logs emqx    ver logs
svc health       dashboard de salud
svc update emqx  actualizar imagen
svc backup emqx  backup de volumenes
svc doctor       chequeo de 6 puntos
svc menu         TUI interactivo

# Agente IA
agent "que servicios estan caidos"
agent "diagnostica homeassistant"
agent "instalar vaultwarden"
agent "exportar emqx al catalogo"
agent --status
```

---

# Licencia

MIT
