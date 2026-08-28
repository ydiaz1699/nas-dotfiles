---
name: docker-nas
description: >
  Skill para administrar un NAS Dell PowerEdge T20 con Debian 13 + Docker.
  Tres capas: Shell personalizado (aliases, navegación), CLI Docker (svc),
  y Agente IA Python (28 tools, plugins, MQTT).

  ACTIVAR esta skill cuando el usuario mencione CUALQUIERA de estos contextos
  (aunque no diga "NAS" explícitamente):
  - Servicios: Docker, contenedor, compose, imagen, puerto, red, volumen
  - Comandos del entorno: dk, adm, nasfk, svc, instal, pipins, gpl, gs, nas
  - Servicios específicos: emqx, ntfy, adguard, filebrowser, esphome, homepage,
    datasql, aipostgres, datapostgres, datapgadmin, dataredis, pgadmin, redis, flowise, n8n, ioBroker, usb-api, spacedrive, vaultwarden, RustFS
  - Infraestructura: homelab, servidor, backup, cron, systemd, USB, mount
  - IoT/domótica: MQTT, broker, ESP32, Home Assistant, alarma, sensor
  - Redes: macvlan, bridge, iot_net, db_net, homepage_net, DNS, proxy
  - Red del host: systemd-networkd, systemd-resolved, resolv.conf, Avahi, mDNS, IPv6
  - Notificaciones: ntfy, push, alerta, topic, notificación
  - Operaciones: actualizar, reiniciar, logs, health, doctor, port-map
  - Almacenamiento: disco, NAS, USB, automount, filebrowser, /NAS/USB
  - El usuario pega output de terminal con prompt "root@Nas" o "aadm@Nas"

  ANTES de responder: cargar references/nas-context.md para conocer aliases,
  servicios, puertos, redes y reglas. NUNCA improvisar rutas ni comandos.
---

# docker-nas skill

Framework completo de administración para NAS Debian con Docker.
Tres capas: **Shell** · **CLI Docker (svc)** · **Agente IA**.

---

## Servidor

| Campo | Valor |
|-------|-------|
| `$NAS_DOTFILES` | `/nas-dotfiles` (código, ruta fija) |
| `$<NAV_VAR>` | Configurable: home del usuario (ej: `$aadm` → `/home/aadm`) |
| `$dkco` | `/docker` (datos de servicios) |
| `$DOCKER_BASE` | `/docker` (alias de $dkco para scripts) |
| Shell | Bash 4.2+ con eza, fzf, batcat |
| Docker | Docker Engine + Compose v2 |
| Agente | Python 3.10+, Strands Agents SDK |

Código (`/nas-dotfiles/`) y datos (`/docker/`) NUNCA se mezclan.

---

## Reglas estrictas

Estas reglas son de libertad baja: no hay alternativa válida.

```
NUNCA:                              SIEMPRE:
  /docker/...                   →   $dkco/...
  /nas-dotfiles/...             →   $NAS_DOTFILES/...
  /home/aadm/...                →   $aadm/... (o la variable NAV_VAR configurada)
  /path/to/...                  →   deducir del contexto o preguntar
  cd /docker/<svc>              →   dk <svc>
  cd /home/aadm/<dir>           →   adm <dir>
  docker compose <cmd>          →   svc <cmd> <svc>
  docker restart/logs/exec      →   svc restart/logs/exec <svc>
  apt install                   →   instal
  pip install                   →   pipins
  cat archivo                   →   bat archivo
  docker-compose.yml            →   compose.yml
  subprocess.run(...)           →   safe_run() de _shell.py
```

- Si el prompt muestra la ruta → usar rutas relativas.
- Responder en el idioma del usuario.
- Nunca sugerir rutas genéricas como `/path/to/...` — deducir o preguntar.

---

## Nuevo servicio Docker

Entrega siempre en este orden exacto:

1. Árbol Unicode de directorios
2. `mkdir -p $dkco/<svc>/{carpetas}`
3. Crear `.env` local si hay secretos y aplicar `chmod 600 .env`
4. Crear `compose.yml` completo usando `extends` desde `$dkco/_common.yml`, `env_file: [../.env, .env]` y labels `homepage.*`
5. `dk <svc> && svc config <svc>` para validar antes de levantar
6. `svc up <svc>` y verificar salud, logs y consumo
7. `svc catalog-sync <svc>` después de confirmar que funciona

### Protocolo obligatorio para instalar un servicio nuevo

Estas reglas evitan que el agente entregue un compose plausible pero incorrecto.
Se aplican especialmente cuando el servicio no existe todavía en el catálogo.

#### 0. Distinguir propuesta de instalación real

- Si no se ejecutaron los comandos en el NAS, decir **"propuesta"** o
  **"archivos preparados"**, nunca **"instalado"**, **"funcionando"** o
  **"setup completo"**.
- No afirmar que una imagen, variable, puerto, ruta interna, motor de base de
  datos o volumen es compatible sin evidencia de la documentación oficial de la
  imagen/proyecto o de una comprobación en el contenedor.
- Si falta información crítica, detenerse y preguntar; no rellenar con valores
  inventados solo para producir un compose.

#### 1. Investigar antes de escribir archivos

1. Leer obligatoriamente `docs/docker-entorno.md` y `references/svc.md`.
2. Si el servicio ya existe, leer en este orden: `docs/services/<svc>-guide.md`,
   `agent/catalog/services/<svc>/ficha.md` y
   `agent/catalog/services/<svc>/compose.yml`. La guía tiene prioridad.
3. Comprobar el estado actual antes de reservar recursos:
   `svc lista`, `svc port-map`, `svc net` y, si tiene dependencias, `svc health`.
4. Para un servicio nuevo, confirmar en fuente oficial la imagen, una etiqueta
   versionada (no usar `latest` por defecto), variables admitidas, puerto
   interno, ruta de persistencia, mecanismo de autenticación, healthcheck y
   requisitos de CPU/RAM/red. `OPENAI_API_KEY`, `ACCESS_CODE`, `./data:/app/data`
   y cualquier otra variable o volumen son inválidos hasta estar confirmados.
5. No confundir el nombre del proyecto con la imagen oficial: documentar la
   fuente consultada y, si hay varias imágenes, justificar la elegida.

#### 2. Ajustar el servicio a la arquitectura del NAS

- El compose real debe usar `extends.file: ../_common.yml` y
  `env_file: [../.env, .env]`. El compose copiado al catálogo usa
  `../../_common.yml` y no se ejecuta directamente desde allí.
- `SERVER_IP` y `TZ` se heredan del `.env` global. Nunca repetir `TZ` en
  `environment:` ni hardcodear la IP en labels; usar `${SERVER_IP}`.
- Los secretos reales van únicamente en el `.env` local, con `chmod 600`; los
  ejemplos usan placeholders (`__pega_aqui__`) y nunca claves ficticias que
  parezcan listas para producción.
- No crear una red `bridge` aislada con el nombre del producto solo por
  costumbre. Usar una red externa existente según la función (`iot_net`,
  `db_net`, `homepage_net`, `proxy` si está habilitada), o documentar por qué
  no necesita una red adicional. La comunicación entre contenedores usa
  hostnames Docker, nunca IPs fijas.
- Los labels `homepage.*` van en `compose.yml`. `services.yaml` se reserva para
  servicios nativos de systemd.
- Verificar conflictos con `svc port-map` y respetar el rango de servicios
  nuevos `8100-8999`, salvo una excepción explícita y documentada. El puerto
  interno debe provenir de la documentación de la imagen; no asumir que el
  puerto externo debe ser igual.
- Un panel web no se expone automáticamente a toda la LAN: definir el alcance
  de acceso, aplicar el bind apropiado y documentar en la ficha cualquier
  excepción de exposición LAN.

#### 3. Persistencia, bases de datos y seguridad

- No crear `data/`, un bind mount o una base SQLite solo porque el servicio
  parece necesitarlos. Crear únicamente las carpetas y mounts confirmados por
  la imagen; si no hay persistencia confirmada, declararlo como pendiente.
- SQLite solo se permite para smoke tests aislados y temporales. Para una
  integración persistente del NAS, preferir DataSQL y cargar además
  `.kiro/skills/datasql/SKILL.md` y `docs/services/datasql-guide.md`.
- No inventar credenciales, nombres de variables ni promesas como "SQLite +
  almacenamiento local". Confirmar también qué datos deben respaldarse y cómo
  se recuperan.
- Añadir `healthcheck` específico al protocolo real de la aplicación; no usar
  `curl /health` ni una ruta inventada. Mantener los defaults de seguridad y
  recursos del compose base, ajustándolos solo con evidencia.

#### 4. Verificar en el orden real

Después de crear directorios, archivos y permisos, y antes de declarar éxito:

```bash
# La ubicación ya debe existir antes de aplicar permisos o levantar
mkdir -p $dkco/<svc>/<carpetas-confirmadas>
# Crear .env solo si hay secretos; después aplicar permisos:
chmod 600 $dkco/<svc>/.env  # solo si el servicio tiene .env local

dk <svc> && svc config <svc>
svc port-map
svc pull <svc>
svc up <svc>
svc ps <svc>
svc logs <svc>
svc health
svc stats <svc>
```

- Si `svc config`, `svc pull`, el healthcheck, los logs o la prueba de acceso
  fallan, no continuar como si estuviera instalado: diagnosticar, corregir y
  volver a verificar.
- `svc pull` comprueba disponibilidad de la imagen, pero no demuestra que la
  configuración sea correcta. La afirmación de éxito requiere configuración
  resuelta, contenedor estable, healthcheck aprobado y acceso funcional.
- No usar `svc down`, `rm`, `kill`, `prune` ni modificar un servicio existente
  sin la confirmación requerida por las reglas de seguridad.

#### 5. Documentar después de verificar

Solo tras una instalación comprobada ejecutar:

```bash
svc catalog-sync <svc>
svc catalog-sync --status
svc scan
```

Revisar y completar manualmente `docs/services/<svc>-guide.md`: el placeholder
no es una guía operativa terminada. Confirmar también la ficha, el compose
portable, `.env.example`, los datos críticos de backup y, si aplica, la entrada
DebMenux. No afirmar que la documentación está completa si solo se generó el
placeholder automático.

### .env global (`$dkco/.env`)

Variables compartidas por TODOS los servicios. Cambiar aquí = aplica a todos al reiniciar:

```env
SERVER_IP=192.168.1.200
TZ=America/La_Paz
```

Cada servicio hereda con:
```yaml
env_file:
  - ../.env      # global (SERVER_IP, TZ)
  - .env         # secretos locales del servicio
```

El `.env` local sobreescribe al global si hay conflicto.
Template en: `agent/catalog/.env.global.example`

### Servicios que necesitan una base de datos existente

Antes de crear un servicio que use PostgreSQL, Redis u otra base compartida:

1. Activar/cargar `.kiro/skills/datasql/SKILL.md` y leer `docs/services/datasql-guide.md` para el stack, la base/rol del consumidor y la ficha de DataSQL.
2. Confirmar que el servicio realmente usa DB: `db_net` por sí sola solo permite comunicación; revisar compose, configuración y runtime.
3. Usar la red externa `db_net`; no publicar bases de datos a la LAN. Para Home Assistant host-network, PostgreSQL usa `127.0.0.1:5432`; pgAdmin `datasql` usa la excepción documentada de dashboard LAN en `5050`; Redis (`6379`) permanece interno.
4. Crear una base y un usuario dedicados dentro del clúster activo; no reutilizar el usuario administrador. Crear el rol y la base en llamadas separadas de `psql`. Los consumidores Docker usan `datapostgres`/`dataredis`.
5. Leer los secretos reales desde `$dkco/datasql/.env`; no asumir `admin/appdb`, no hacer `source .env` y pasar `PGPASSWORD`/`REDISCLI_AUTH` explícitamente a `svc exec`.
6. Configurar `env_file: [../.env, .env]`, `extends.file: ../_common.yml` cuando no exista una incompatibilidad documentada, y labels `homepage.*`.
7. No usar `depends_on` para un contenedor que pertenece a otro compose; verificar la disponibilidad con `svc health` y logs.
8. Documentar el host de conexión como el nombre del contenedor/servicio en `db_net`, no como una IP fija. La excepción de Home Assistant es loopback porque usa `network_mode: host`.
9. Estado confirmado: Flowise usa `flowise_db` + `dataredis`; Home Assistant usa `homeassistant_db`; n8n usa `n8n_db` con `n8n_user` por `datapostgres:5432` en `db_net`. La guía n8n separa runtime confirmado de hardening/pin pendiente.
10. El único stack operativo es `datasql`: ParadeDB PostgreSQL 17 con pgvector/pg_search/pg_cron, pgAdmin y Redis; sus contenedores son `datapostgres`, `datapgadmin` y `dataredis`. `aipostgres` es la base administrativa y un alias histórico. La instalación limpia puede eliminar el DataSQL anterior cuando el usuario lo confirma; después se verifica y se crean consumidores vacíos.
11. RustFS no pertenece al stack PostgreSQL. Instalarlo como servicio S3 separado solo cuando LobeHub u otro consumidor real necesite objetos.

SQLite puede usarse solo para una prueba aislada y temporal. En un servidor nuevo
sin datos, un único clúster PostgreSQL compatible con `pgvector` y `pg_search`
puede ser DataSQL común; habilitar las extensiones solo en las bases que las
necesiten. Preparar ese clúster no obliga a instalar LobeHub, Hermes ni el agente.


---

## Comandos esenciales

```bash
# Navegación
dk <svc>             # ir a /docker/<svc>
adm <dir>            # ir a $HOME/<dir>
up [n]               # subir n niveles
dkf / admf           # fuzzy finder con fzf

# Docker (siempre vía svc)
svc lista            # servicios con estado ●/○
svc up/down/restart/logs/update <svc>
svc health           # dashboard (health, uptime, restarts)
svc doctor           # chequeo 6 puntos del NAS
svc backup <svc>     # exportar volúmenes + bind mounts
svc restore <svc>    # restaurar desde backup
svc update-all       # actualizar todos los servicios
svc port-map         # mapa de puertos + conflictos
svc menu             # TUI interactivo con fzf

# Sistema
nas                  # dashboard (uptime, RAM, disco, red, Docker, temp)
disk / netinfo       # uso de disco / interfaces + puertos
logs [-f] [target]   # journald o /var/log/<target>
instal pkg           # apt + log en logs/packages.txt
pipins pkg           # pip + log en logs/pip_packages.txt

# Git
gs / ga / gc / gp    # status/add/commit/push
git-quick "msg"      # add -A + commit + push en un paso

# Agente IA
agent "query"        # consulta puntual
agent chat           # modo REPL conversacional
agent --new "q"      # nueva sesión limpia
agent --model        # cambiar modelo (menú interactivo)
agent --status       # info de sesión actual
```

Para referencia completa del shell, ver `references/entorno.md`.
Para referencia completa de svc, ver `references/svc.md`.

---

## Cuándo usar svc vs agent

| Situación | Usar |
|-----------|------|
| Acción puntual y clara (restart, logs, update, backup) | `svc` directo |
| Operación batch ya conocida (update-all, backup-all) | `svc` directo |
| Diagnóstico que requiere interpretar logs + contexto | `agent` |
| Crear servicio nuevo (buscar config, generar compose) | `agent` |
| Pregunta abierta ("¿qué está fallando?", "¿cómo optimizo X?") | `agent` |
| Operación multi-paso con dependencias | `agent` |

Regla simple: si sabes exactamente qué comando correr → `svc`.
Si necesitas razonamiento, búsqueda o decisión → `agent`.

---

## Diagnóstico

Cuando algo falla, seguir un orden de investigación estructurado:

1. `svc health` → estado global
2. `svc logs <svc>` → errores recientes
3. `svc ps <svc>` → contenedores + health status
4. `svc stats <svc>` → CPU/RAM en tiempo real
5. Si necesita razonamiento profundo → `agent "diagnosticar <svc>"`

Para recetas completas (OOM, crash loop, conflicto de puerto, servicio
lento, healthcheck, red), ver `references/diagnostic.md`.

---

## Agente IA

28 tools · 3 providers (Gemini default, Bedrock, Ollama) · memoria
persistente · plugins dinámicos · daemon systemd · prompt modular por bloques.

Para tools, memoria, plugins y configuración, ver `references/agent.md`.

---

## Seguridad

`safe_run(list, shell=False)` obligatorio · `validate_service_name()` ·
`readonly_guard()` · audit log JSON Lines · dual dry-run.

Para mecanismos completos y variables de entorno, ver `references/seguridad.md`.

---

## Extender

Para agregar comandos svc, tools del agente, plugins, o módulos shell,
ver `references/extend.md`.

---

## Redes avanzadas (systemd-networkd / systemd-resolved / Avahi / macvlan)

Configuración de la red del host, DNS local, resolución mDNS, IPv4/IPv6,
shim macvlan y AdGuard con IP propia en la LAN.

Para el procedimiento completo, instalación reversible y rollback, ver
`references/networking.md`. Para escenarios concretos, cargar además:

- `references/networking-install.md` — instalación futura de networkd, shim macvlan y resolved.
- `references/networking-migration.md` — migración de backend, gateway, subred o IP.
- `references/networking-recovery.md` — recuperación desde consola tras perder SSH, DNS, macvlan, Avahi o descubrimiento.

---

## Prompt del servidor

```
aadm@Nas ~/docker/cli (main*) 4↑ 71% #
```

| Elemento | Significado |
|----------|-------------|
| `(main*)` | rama git + dirty flag (magenta) |
| `4↑` | contenedores corriendo (verde >0, gris =0) — cache 5s |
| `71%` | disco raíz (verde <75%, amarillo <90%, rojo ≥90%) — cache 10s |
| `$` / `#` | rojo si último comando falló |

---

## Dependencias del sistema

| Herramienta | Para qué | Instalar |
|-------------|----------|----------|
| `eza` | Reemplazo de ls (aliases) | `instal eza` |
| `fzf` | Menú, admf, dkf, svc menu | `instal fzf` |
| `batcat` | cat con syntax highlighting | `instal bat` |
| `bash-completion` | Autocompletado TAB | `instal bash-completion` |
| `lm-sensors` | Temperatura en `nas` | `instal lm-sensors` |
| `qrencode` | QR en `svc open` | `instal qrencode` |
| `apt-fast` | instal más rápido | `instal apt-fast` |
| Python 3.10+ | Agente IA | pre-instalado |

---

## Referencias adicionales

Leer cuando se necesite detalle completo de un componente:

- `references/entorno.md` — Shell framework: módulos, aliases, funciones, prompt
- `references/svc.md` — CLI svc: comandos, anchors, redes compartidas, plantillas
- `references/agent.md` — Agente IA: providers, tools, memoria, plugins, daemon
- `references/seguridad.md` — Mecanismos de seguridad, variables, convenciones
- `references/diagnostic.md` — Recetas de diagnóstico paso a paso
- `references/extend.md` — Cómo agregar comandos, tools, plugins, módulos shell
- `references/networking.md` — Red host y DNS: systemd-networkd, systemd-resolved, Avahi, IPv6, macvlan y rollback

---

## ⚠️ Regla: consultar guía ANTES de modificar un servicio

**OBLIGATORIO:** Antes de sugerir cambios a un servicio (compose, config, volumes,
redes, permisos), LEER su guía operativa si existe. La guía contiene decisiones
reales, errores ya resueltos, y configuración específica que NO puede adivinarse.

Orden de consulta:
1. `docs/services/<svc>-guide.md` — guía completa (prioridad máxima)
2. `agent/catalog/services/<svc>/ficha.md` — metadatos y notas
3. `agent/catalog/services/<svc>/compose.yml` — config actual

**NUNCA sugerir una solución genérica si existe una guía documentada.**

---

## 📚 Guías de servicios disponibles

| Servicio | Guía | Temas clave documentados |
|----------|------|--------------------------|
| **datasql** | `docs/services/datasql-guide.md` + `.kiro/skills/datasql/SKILL.md` | PostgreSQL+pgvector+pg_search+pg_cron, consumidores, creación de roles/bases, Redis compartido, instalación, permisos y db_net |
| **filebrowser** | `docs/services/filebrowser-guide.md` | Bind mounts, `:rshared` para USB, fstab, permisos, mount propagation |
| **ntfy** | `docs/services/ntfy-guide.md` | Notificaciones push, topics, clientes Android/PWA, alarma+cámara, Homepage |
| **usb-api** | `docs/services/ntfy-guide.md#usb-api` | API REST para USBs, systemd nativo, Homepage widget, desmontaje seguro |
| **homeassistant** | `docs/services/homeassistant-guide.md` | Automatización, cámara→ntfy, includes, TvOverlay, shell_commands |
| **node-red** | `docs/services/node-red-guide.md` | Flujos IoT, conexión EMQX/MQTT, no usar cap_drop, backup flows.json |
| **emqx** | `agent/catalog/services/emqx/ficha.md` | Puertos WS 8083/8084, ulimits, dashboard LAN, iot_net |
| **ioBroker** | `docs/services/iobroker-guide.md` | Puerto 8181, `/opt/iobroker`, iot_net, MQTT con `emqx:1883`, backup y escalado stateful |
| **esphome** | `agent/catalog/services/esphome/ficha.md` | Puerto 6052, iot_net |

### Hechos críticos que NO deben adivinarse:

- **File Browser**: usa un bind `/NAS` → `/srv` con `bind.propagation: rshared` — sin `rshared` los USBs montados después no son visibles
- **DataSQL**: PostgreSQL no se expone a la LAN; `127.0.0.1:5432:5432` solo se usa para el Recorder de Home Assistant con `network_mode: host`; los consumidores Docker usan `db_net`
- **EMQX**: requiere ulimits nofile 1048576, dashboard en LAN (excepción documentada)
- **USB Automount**: monta en `/NAS/USB/usb-<dev>` — File Browser lo ve por `bind.propagation: rshared`
- **Bind mounts**: siempre usar `mount --bind` + fstab, nunca symlinks (Docker no los propaga)
- **ntfy**: puerto 8090, stateless (cache 24h), auth abierto en LAN, attachments para snapshots de cámaras
- **usb-api**: puerto 8091, servicio systemd NATIVO (no Docker) — necesita umount real en el host
- **ioBroker**: una sola instancia stateful con `/opt/iobroker` persistente; usar `emqx:1883` dentro de `iot_net`; no añadir réplicas, `privileged` ni `network_mode: host` sin requerimiento de un adapter
- **Notificaciones**: usar `ntfy_send()` de `docker/cli/lib/notifications.sh` — nunca `notify-send` (inútil en headless)

### Herramientas disponibles:

| Herramienta | Ubicación | Para qué |
|-------------|-----------|----------|
| Meta-prompt de unificación | `docs/meta-prompt-unificar.md` | Unificar fragmentos dispersos en guía coherente |
| DebMenux (toolkit) | `/debmenux` | Instalar servicios, USB automount, post-install |
| Catálogo del agente | `agent/catalog/services/` | Fichas + compose + .env.example por servicio |
| Troubleshooting | `docs/troubleshooting.md` | Diagnósticos resueltos y soluciones |
| Notificaciones (lib) | `docker/cli/lib/notifications.sh` | Función ntfy_send() para scripts svc |
| Notificaciones (plugin) | `agent/plugins/notification_plugin.py` | Plugin del agente para alertas automáticas |
