# NAS Skill — Contexto Operativo

> **Mapa canónico de arquitectura y estado:** [`docs/framework-knowledge-compilation.md`](../../docs/framework-knowledge-compilation.md). Esta skill conserva solo el contexto operativo comprimido, registry y reglas proactivas; cargar la compilación para entender ownership, gaps y criterios.

> **Auto-generado por `svc catalog-sync`.** No editar secciones marcadas [AUTO].
> Última actualización: 2026-08-15

---

## 1. Metadata & Trigger

```yaml
name: nas-homelab
version: "2.0"
trigger: >
  Activar cuando el usuario mencione CUALQUIERA de estos contextos
  (aunque no diga "NAS" explícitamente):
  - Servicios: Docker, contenedor, compose, imagen, puerto, red, volumen
  - Comandos: dk, adm, nasfk, svc, instal, pipins, gpl, gs, nas, bat
  - Servicios específicos: emqx, ntfy, adguard, filebrowser, esphome,
    homepage, datasql, aipostgres, datapostgres, datapgadmin, dataredis, pgadmin, redis, flowise, ioBroker, usb-api, spacedrive, rustfs
  - Infra: homelab, servidor, backup, cron, systemd, USB, mount
  - IoT: MQTT, broker, ESP32, Home Assistant, alarma, sensor
  - Redes: macvlan, bridge, iot_net, db_net, homepage_net, DNS
  - Red del host: systemd-networkd, systemd-resolved, resolv.conf, Avahi, mDNS, IPv6
  - Notificaciones: ntfy, push, alerta, topic
  - Operaciones: actualizar, reiniciar, logs, health, doctor
  - Almacenamiento: disco, NAS, USB, automount, /NAS/USB
  - Output pegado con prompt "root@Nas" o "aadm@Nas"
scope: encoded-preferences
  # NO caduca con modelos nuevos — son procesos únicos del usuario.
```

**Regla:** Si el usuario habla del NAS, SIEMPRE cargar esta skill antes de responder.

---

## 2. Entorno (lo justo para no improvisar)

### Máquina

| Campo | Valor |
|-------|-------|
| Equipo | Dell PowerEdge T20 |
| IP | 192.168.1.200 |
| Hostname | `Nas` (accesible via `ssh aadm@Nas.local`) |
| OS | Debian 13, kernel 6.12 |
| CPU/RAM | 2 cores @ 3GHz / 8 GB ECC |
| Disco | SSD 298 GB ext4 (8%) |

### Variables de entorno

| Variable | Valor | Atajo |
|----------|-------|-------|
| `$NAS_DOTFILES` | `/nas-dotfiles` | `nasfk` |
| `$dkco` | `/docker` | `dk` |
| `$aadm` | `/home/aadm` | `adm` |
| `$NTFY_URL` | `http://192.168.1.200:8090` | — |

---

## 3. Encoded Preferences (NUNCA/SIEMPRE)

Estas reglas son permanentes. No cambian con modelos nuevos.

```
NUNCA usar:                         SIEMPRE usar:
─────────────────────────────────────────────────────
  cd /docker/X                  →   dk X
  cd /nas-dotfiles              →   nasfk
  cd /home/aadm                 →   adm
  git pull                      →   gpl
  git status                    →   gs
  git add                       →   ga
  git commit -m "msg"           →   gc "msg"
  git push                      →   gp
  git add -A && commit && push  →   git-quick "msg"
  apt install pkg               →   instal pkg
  pip install pkg               →   pipins pkg
  docker compose up -d          →   svc up X
  docker compose down           →   svc down X
  docker compose logs           →   svc logs X
  docker restart X              →   svc restart X
  cat archivo                   →   bat archivo
  notify-send                   →   ntfy_send (headless)
  docker-compose.yml            →   compose.yml
  /path/to/...                  →   deducir o preguntar
  hardcodear rutas              →   usar $variables
```

### Notificaciones

```bash
# Función compartida (source automático)
ntfy_send "topic" "título" "mensaje" "prioridad" "tags"

# Topics: usb, docker, backups, system, alarma, nas-alerts
# Prioridades: min, low, default, high, urgent
```

### Nuevo servicio (orden obligatorio)

Para instalar un servicio nuevo, cargar primero la sección **Protocolo obligatorio
para instalar un servicio nuevo** de `docker-nas/SKILL.md`. Esta tabla es solo un
recordatorio y no autoriza a inventar configuración.

```
0. Leer docs/docker-entorno.md, references/svc.md y documentación oficial de la imagen
1. Comprobar svc lista, svc port-map y svc net
2. mkdir -p $dkco/<svc>/<carpetas-confirmadas>
3. Crear compose.yml con extends, env_file global/local, labels y healthcheck confirmados
4. Crear .env local solo si hay secretos; chmod 600 después de crearlo
5. dk <svc> && svc config <svc>
6. svc pull <svc>
7. svc up <svc>
8. Verificar svc ps, svc logs, svc health, svc stats y acceso funcional
9. svc catalog-sync <svc> && svc scan
```

Nunca afirmar "instalado" o "funcionando" si los pasos de validación no se
han ejecutado correctamente. No crear `data/`, SQLite, variables, puertos,
volúmenes ni redes conjeturadas; confirmarlos primero en la fuente oficial.

### Homepage

- **Labels en compose (auto-descubrimiento)** > services.yaml
- `services.yaml` solo para servicios nativos (systemd)
- Recrear contenedor para que tome labels nuevas: `svc recreate X`

---

## 4. Skill Registry [AUTO]

Índice ligero de servicios. **NO cargar los archivos — solo buscar cuando se necesite.**

| Servicio | Puerto | Red | Docs (cargar si se necesita) |
|----------|--------|-----|------|
| adguard | 53,80 (IP: .201) | macvlan | `agent/catalog/services/adguard/` |
| emqx | 1883,18083 | iot_net, db_net | `agent/catalog/services/emqx/ficha.md` |
| esphome | 6052 | host | `agent/catalog/services/esphome/ficha.md` |
| datasql | 5432 (loopback), 5050 | db_net | `docs/services/datasql-guide.md` (consumidores/bases) + `docs/services/aipostgres-guide.md` (instalación/operación) |
| aipostgres | alias de datasql | db_net | `docs/services/aipostgres-guide.md` (base administrativa/alias histórico) |
| flowise | 8100 | db_net | `docs/services/flowise-guide.md` |
| n8n | 5678 | db_net | compose/runtime pendiente de catalogar |
| filebrowser | 8085 | default | `docs/services/filebrowser-guide.md` |
| homeassistant | 8123 | host | `docs/services/homeassistant-guide.md` |
| homepage | 3000 | homepage_net | `docs/services/homepage-guide.md` |
| ntfy | 8090 | homepage_net | `docs/services/ntfy-guide.md` |
| node-red | 1880 | iot_net | `docs/services/node-red-guide.md` |
| iobroker | 8181 (preparado) | iot_net | `docs/services/iobroker-guide.md` |
| usb-api | 8091 | nativo (systemd) | `agent/catalog/services/usb-api/ficha.md` |

### Servicios nuevos que dependen de DataSQL

Antes de crear una aplicación que necesite PostgreSQL o Redis compartido:

1. Cargar `.kiro/skills/datasql/SKILL.md`, `docs/services/aipostgres-guide.md` para instalación/operación y `docs/services/datasql-guide.md` para consumidores y creación de bases/roles.
2. Comprobar DataSQL con `svc health` y `svc ps datasql`; `svc health` no recibe el nombre del servicio.
3. Leer `POSTGRES_USER`, `POSTGRES_DB`, `POSTGRES_PASSWORD` y `REDIS_PASSWORD` desde `$dkco/datasql/.env`; no asumir `admin/appdb` ni ejecutar `source .env`.
4. Crear una base y usuario dedicados con la Fase 5A de la guía: primero el rol, después la base, en llamadas separadas de `psql`.
5. Usar `svc exec datasql postgres env PGPASSWORD="..." psql ...` y Redis con `env REDISCLI_AUTH="..." redis-cli ping`; limpiar las variables con `unset`. Con el CLI Python, abrir `psql` interactivo y no enviar SQL por pipe porque `svc exec` conserva TTY.
6. Usar la red externa `db_net`; no publicar bases de datos a la LAN. La única
   excepción host-only es PostgreSQL en `127.0.0.1:5432` para Home Assistant;
   pgAdmin se publica como dashboard LAN en `5050` y Redis (`6379`) permanece
   interno.
7. El único stack operativo contiene `datapostgres`, `datapgadmin` y
   `dataredis`. Los consumidores Docker usan `datapostgres:5432` y
   `dataredis:6379`; `aipostgres` es la base administrativa y un alias histórico,
   no un segundo stack.
8. La instalación inicial limpia elimina el DataSQL antiguo sin backup cuando
   el usuario lo solicita; después se crean bases y roles vacíos para los
   consumidores verificados.
9. RustFS no forma parte de PostgreSQL IA. Instalarlo como servicio S3 separado
   solo cuando LobeHub u otro consumidor real necesite almacenamiento de objetos.
10. No usar `depends_on` contra una base que vive en otro compose; verificar la
    disponibilidad con `svc health` y logs.
11. El inventario confirmado es Flowise → `flowise_db` + Redis, Home Assistant →
    `homeassistant_db`, y `n8n_db` existente pendiente de auditar en el compose
    real.

### Redes

| Red | Propósito | Regla |
|-----|-----------|-------|
| `adguard_macvlan_NET` | IP dedicada AdGuard (DNS:53) | Solo macvlan |
| `db_net` | Apps ↔ DBs (interno) | No exponer bases a la LAN; PostgreSQL puede usar `127.0.0.1:5432:5432` solo para Home Assistant host-network |
| `iot_net` | EMQX ↔ ESPHome ↔ HA ↔ ioBroker | Todo IoT aquí |
| `homepage_net` | Homepage ↔ servicios (widgets) | Para APIs internas |

### USB Automount

| Campo | Valor |
|-------|-------|
| Mount base | `/NAS/USB/` |
| Formato | `/NAS/USB/<LABEL>` o `/NAS/USB/usb-<dev>` (sin label) |
| API | `GET http://192.168.1.200:8091/usb/list` |
| Desmontar | `POST http://192.168.1.200:8091/usb/unmount/<dev>` |
| Cleanup | `usb-automount.sh --cleanup` o `umount -l` + `rmdir` |

---

## 4b. Herramientas de verificación (3 tools que trabajan juntas)

```
Scanner   DETECTA   → "esto está desconectado / desactualizado"
Catalog-sync GENERA → crea o actualiza lo que falta
Dependency-map DOCUMENTA → las reglas para que el próximo LLM sepa qué cascada seguir
```

| Herramienta | Comando | Función |
|---|---|---|
| **Scanner incremental** | `svc scan` | Detecta cambios vía Git y filtra inconsistencias por servicio. **Todavía no mantiene un ledger de archivos leídos/procesados/pendientes.** |
| **Catalog-sync** | `svc catalog-sync [svc]` | Genera ficha, guía, script DebMenux en cascada |
| **Dependency-map** | `docs/dependency-map.md` | Reglas estáticas (grafos A–I) de qué conecta con qué |
| **Compare catalog** | Tool `compare_catalog("svc")` | Detecta drift: compose real vs catálogo |

### Scanner — modos de uso

```bash
svc scan              # incremental (si hay snapshot previo) o full (primera vez)
svc scan --full       # forzar scan completo + regenerar snapshot
svc scan --changed    # solo listar qué archivos cambiaron desde último scan
svc scan --verbose    # incluir issues de severidad info
svc scan --json       # output JSON (para herramientas)
```

### Cómo funciona actualmente el scanner incremental

1. **Primera ejecución:** hace un scan completo y genera `agent/cache/project-snapshot.json`.
2. **Siguientes ejecuciones:** usa `git diff` desde `last_commit` y lista archivos no trackeados.
3. Clasifica los cambios y determina servicios afectados.
4. Ejecuta detectores amplios y filtra los issues mostrados por servicio.
5. Guarda el nuevo baseline del scan.

> **Importante:** esta versión detecta deltas, pero no mantiene todavía un estado
> por archivo `processed/pending/failed`. Tampoco detecta de forma completa todos
> los cambios staged, unstaged y eliminaciones locales. No debe interpretarse como
> una cola persistente de archivos que la LLM ya leyó.

### Estado objetivo del scanner (pendiente)

La idea original requiere un ledger por archivo dentro del snapshot, con hash,
fecha y estado (`changed`, `pending`, `processing`, `processed`, `failed` o
`ignored`). Solo así el LLM podrá saber qué archivos debe leer, cuáles ya fueron
verificados y cuáles quedaron pendientes después de una interrupción.

Requisitos pendientes:

- Comparar commits, índice/staged, working tree, no trackeados y eliminados.
- Comparar hashes de archivos y no solo `last_commit`.
- Procesar únicamente archivos `changed` o `pending`.
- Persistir `pending` y `failed` entre sesiones.
- Añadir `svc scan --status` para mostrar el ledger.

### Cuándo usar cada herramienta

| Situación | Herramienta |
|-----------|-------------|
| Al inicio de sesión — "¿qué falta?" | `svc scan` o `svc scan --changed` |
| Después de modificar un compose | `svc catalog-sync <svc>` + `svc scan` |
| Detectar si el real drifteó del catálogo | Tool `compare_catalog("svc")` |
| Antes de decir "listo" | Consultar `docs/dependency-map.md` mentalmente |
| Después de crear script/herramienta nueva | `svc scan` (detecta si no está conectado) |

---

## 5. Documentación disponible (lazy loading)

**Regla: NO leer estos archivos al activar la skill.** Solo cargar cuando el usuario pregunte sobre ese tema.
**EXCEPCIÓN 1: SIEMPRE leer `docs/docker-entorno.md` ANTES de modificar cualquier compose.**
**EXCEPCIÓN 2: SIEMPRE consultar `docs/dependency-map.md` DESPUÉS de cualquier cambio para verificar la cascada.**

| Trigger | Archivo a cargar |
|---------|-----------------|
| Inicio de sesión / "revisar framework" / "qué hay" | `docs/framework-knowledge-compilation.md` → `docs/framework-audit.md` (mapa canónico primero; audit es inventario rápido) |
| Modificar/crear un compose.yml | `docs/docker-entorno.md` + `docs/dependency-map.md` (**OBLIGATORIO**) |
| Usuario copia compose de internet | `docs/docker-entorno.md` (ajustar a convenciones: env_file, ${SERVER_IP}, labels, security) |
| Crear servicio nuevo | `docs/dependency-map.md` + `docs/docker-entorno.md` + `agent/catalog/_template.md` |
| Crear script/herramienta nueva | `docs/dependency-map.md` (verificar dónde conecta con el sistema) |
| Resolver un problema nuevo | `docs/ideas-decisions.md` (agregar entrada con problema → idea → solución → aprendizaje) |
| Entender por qué algo se hizo así | `docs/ideas-decisions.md` (historial de decisiones con contexto) |
| Hay archivos en `_drafts/` | Identificar tipo → procesar según `docs/dependency-map.md` §J |
| Fragmentos dispersos a unificar | `docs/meta-prompt-unificar.md` (reglas de unificación sin perder contenido) |
| Usuario sube compose copiado | `docs/docker-entorno.md` (ajustar a convenciones) |
| Preguntan por un servicio específico | `docs/services/<svc>-guide.md` → `agent/catalog/services/<svc>/ficha.md` |
| ioBroker, adapters, MQTT, upgrades | `docs/services/iobroker-guide.md` → `agent/catalog/services/iobroker/ficha.md` |
| Troubleshooting USB / mounts | `docs/services/ntfy-guide.md` §Troubleshooting |
| Configurar Homepage | `docs/services/homepage-guide.md` |
| Home Assistant (automatizaciones, ntfy, cámara) | `docs/services/homeassistant-guide.md` |
| Pipeline de auto-docs | `docs/catalog-sync-pipeline.md` |
| Info completa del NAS | `docs/nas-manual.md` |
| Todos los comandos shell | `docker-nas/references/entorno.md` |
| Todos los comandos svc | `docker-nas/references/svc.md` |
| Seguridad y convenciones | `docker-nas/references/seguridad.md` |
| Diagnóstico paso a paso | `docker-nas/references/diagnostic.md` |
| Redes avanzadas (host/DNS/macvlan) | `docker-nas/references/networking.md` |
| Instalación futura de red | `docker-nas/references/networking-install.md` |
| Migración de backend o rango IP | `docker-nas/references/networking-migration.md` |
| Recuperación de red, DNS y SSH | `docker-nas/references/networking-recovery.md` |
| Agente IA (tools, plugins) | `docker-nas/references/agent.md` |
| Extender framework | `docker-nas/references/extend.md` |

---

## 6. Progressive Updates (self-learning)

Cuando el usuario corrige al LLM o da feedback, agregar aquí.
Formato: `[fecha] corrección`.

```
[2026-08-15] La IP real del NAS es 192.168.1.200 (no .0.200)
[2026-08-15] ntfy ya estaba en homepage_net (el compose lo incluye)
[2026-08-15] EMQX ya tiene labels Homepage en su compose (no poner en services.yaml)
[2026-08-15] ENABLE_NOTIFICATIONS estaba en "false" — siempre verificar /etc/usb-automount.conf
[2026-08-15] El script de usb-automount en /usr/local/bin/ puede ser versión vieja — verificar con grep ntfy_send
[2026-08-15] USBs ahora montan con LABEL (no usb-sdb1) — formato: /NAS/USB/<LABEL>
[2026-08-15] Mountpoints fantasma: solución = umount -l + rmdir (el timer no puede limpiarlos)
[2026-08-15] Browser push notifications requieren HTTPS — usar Chrome con --unsafely-treat-insecure-origin-as-secure flag en LAN
[2026-08-16] NUNCA decir "no necesitas modificar el compose" sin leer docs/docker-entorno.md primero
[2026-08-16] Todos los compose deben usar env_file: [../.env, .env] — NUNCA hardcodear SERVER_IP ni TZ
[2026-08-16] TZ NUNCA va en environment: si ya está en $dkco/.env (se hereda via env_file)
[2026-08-16] ntfy.publish de HA NO soporta imágenes — usar shell_command + curl -T
[2026-08-16] priority en ntfy.publish de HA es NÚMERO (4=high), no texto ("high")
[2026-08-16] Carpeta www/snapshots/ debe existir ANTES de camera.snapshot
[2026-08-16] HA config se organiza con !include en carpeta includes/ (no todo en configuration.yaml)
[2026-08-16] Home Assistant usa network_mode:host — no necesita redes Docker, accede directo a LAN
[2026-08-16] SIEMPRE consultar dependency-map.md después de cualquier cambio para no olvidar archivos conectados
[2026-08-16] Si el usuario pega un compose de internet → ajustarlo a las convenciones (env_file, ${SERVER_IP}, labels, security_opt, cap_drop)
[2026-08-16] filebrowser requiere `bind.propagation: rshared` en el bind `/NAS` → `/srv` — sin él los USBs montados después no se ven
[2026-08-16] Cuando se mejora un compose existente (ej: agregar :rshared, env_file, quitar TZ) → actualizar TAMBIÉN la guía y la ficha del catálogo
[2026-08-16] Cuando se mejora la gestión de un servicio (ej: HA con !include) → documentar el ANTES y DESPUÉS en la guía para que otros LLMs no sugieran la forma vieja
[2026-08-16] README.md debe reflejar archivos nuevos en la estructura del proyecto — si se crea docs/X.md o scripts/X.sh, actualizar el árbol en README
[2026-08-16] cap_drop:[ALL] NO aplicar ciegamente — rompe Node-RED, HA, ESPHome. Solo para servicios simples (ntfy, redis, filebrowser)
[2026-08-16] deploy:resources:limits NO poner si no se sabe el consumo real — puede causar OOM kill. Primero probar con docker stats
[2026-08-16] catalog-sync.sh CONECTADO a svc.sh (bash) y svc_py (Python). `svc catalog-sync` funciona en ambos CLIs. Scanner incremental implementado con git diff + snapshot.
[2026-08-16] Al crear una herramienta/script nueva, SIEMPRE verificar que está CONECTADA al sistema (no solo que existe el archivo). Preguntar: ¿cómo se invoca? ¿qué comando la ejecuta? ¿está registrada en svc/alias/path?
[2026-08-16] svc tiene DOS CLIs: bash (svc.sh) y Python (svc_py). Variable NAS_CLI=bash|python decide cuál se usa. Decisión: bash=verdad (toda la lógica), Python=interfaz bonita (Rich, InquirerPy). Comando nuevo → implementar SOLO en bash → Python lo hereda via bash_bridge.py (passthrough).
[2026-08-16] catalog-sync está en AMBOS CLIs (bash nativo + Python wrapper via bash_bridge.py). `svc scan` también en ambos.
[2026-08-17] Scanner incremental implementado: `svc scan` usa git diff + snapshot. Primera vez: full scan → project-snapshot.json. Siguientes: solo procesa archivos que cambiaron. Detecta: servicios sin docs, IP hardcodeada, TZ duplicado, env_file faltante, scripts no conectados.
[2026-08-17] compare_catalog(service) implementado: tool del agente que detecta drift entre compose real ($DOCKER_BASE) y catálogo (imagen, puertos, redes, volúmenes, env_file, healthcheck, security).
[2026-08-17] svc snapshot/rollback implementado: guardar compose+.env antes de cambios (liviano, rotación 10). `svc snapshot X` antes de editar, `svc rollback X` para revertir.
[2026-08-17] Catálogo pre-cargado: al arrancar, el agente inyecta resumen de todos los servicios en el prompt (sin llamar tools). El agente ya sabe qué servicios existen.
[2026-08-17] Para aplicaciones nuevas con PostgreSQL/Redis, cargar datasql-guide.md; usar db_net, usuario/DB dedicados, env_file dual, extends ../_common.yml y labels Homepage. aipostgres-guide.md queda para instalación y operación del stack. SQLite queda solo para smoke tests.
[2026-08-17] El scanner incremental actual detecta cambios con Git y filtra issues, pero todavía no registra por archivo si fue leído, procesado, falló o quedó pendiente. La idea original requiere un ledger persistente `processed/pending/failed`.
```

> **Instrucciones al LLM (comportamiento proactivo):**
>
> 1. **Cuando el usuario te corrija** → agregar una línea aquí con fecha y corrección
>
> 2. **Cuando se cree/modifique cualquier archivo** → consultar `docs/dependency-map.md`
>    y recomendar qué otros archivos actualizar (no esperar a que el usuario pregunte)
>
> 3. **Cuando el usuario copie un compose de internet** → ANTES de aceptarlo, verificar:
>    - ¿Tiene `env_file: [../.env, .env]`? Si no → agregar
>    - ¿Tiene IP hardcodeada en labels? → cambiar a `${SERVER_IP}`
>    - ¿Tiene `TZ` en environment? → quitar (se hereda)
>    - ¿Tiene `security_opt: [no-new-privileges:true]` + `cap_drop: [ALL]`? → agregar
>    - ¿Tiene healthcheck? → agregar si falta
>    - ¿Tiene labels `homepage.*`? → sugerir agregar
>    - Recomendar: `svc catalog-sync <svc>` después de levantar
>
> 4. **Cuando se cree un servicio nuevo** → recordar la cascada completa:
>    - compose + .env + carpetas
>    - `svc catalog-sync <svc>` (genera ficha, guía, script DebMenux)
>    - Verificar si falta actualizar AGENTS.md y nas-manual.md (manual)
>    - Verificar si falta actualizar README.md (estructura del proyecto)
>
> 5. **Cuando se cree un script/herramienta nueva** → preguntar:
>    - ¿Dónde vive? (nas-dotfiles o DebMenux)
>    - ¿Se conecta con algún servicio existente?
>    - ¿Necesita entry en AGENTS.md o en la skill?
>    - ¿Necesita documentación en docs/?
>    - ¿README.md refleja el nuevo archivo en su estructura?
>    - **¿Cómo se ejecuta? ¿Está conectado a svc/alias/PATH?**
>    - **Si es comando de svc → ¿se agregó el case en svc.sh + completions + GUIDE.md?**
>    - **Si NO está conectado → avisar al usuario: "el script existe pero no es ejecutable aún"**
>
> 6. **Cuando se mejore un compose o config existente** (ej: agregar :rshared, env_file,
>    migrar a !include, quitar TZ duplicado) → actualizar TAMBIÉN:
>    - La guía del servicio (`docs/services/<svc>-guide.md`) con el cambio
>    - La ficha del catálogo (`agent/catalog/services/<svc>/ficha.md`) si cambió algo
>    - El compose del catálogo (`agent/catalog/services/<svc>/compose.yml`)
>    - Documentar ANTES vs DESPUÉS en la guía para que otros LLMs no sugieran la forma vieja
>
> 7. **Antes de decir "listo" o "no necesita cambios"** → verificar:
>    - dependency-map.md: ¿olvidé algún archivo conectado?
>    - README.md: ¿refleja la estructura actual del proyecto?
>    - ¿La guía del servicio coincide con el compose real?
>
> 8. **Cuando hay archivos en `_drafts/`** → analizarlos proactivamente:
>    - Identificar qué tipo de contenido es (plan, fragmentos, compose, idea, docs de otro LLM)
>    - Consultar dependency-map.md §J para saber qué hacer con cada uno
>    - Si son fragmentos dispersos → usar `docs/meta-prompt-unificar.md` para unificar
>    - Si es un compose copiado → ajustar a convenciones antes de implementar
>    - Si ya se implementó lo que describe → sugerir eliminar o archivar
>    - Preguntar al usuario: "Encontré X en _drafts/, ¿quieres que lo procese?"
>
> 9. **Cuando el usuario suba contenido nuevo** (gist, texto, archivo) → clasificar:
>    - ¿Es implementable ahora? → implementar siguiendo dependency-map
>    - ¿Es una idea para el futuro? → agregar a TODO.md
>    - ¿Es información de referencia? → agregar a docs/ o ideas-decisions.md
>    - ¿Es output de otro LLM? → verificar contra la realidad del proyecto antes de aplicar

---

## 7. Verificación rápida (para el LLM)

Antes de sugerir CUALQUIER comando o cambio para el NAS, verificar:

- [ ] ¿Usé el alias correcto? (dk, svc, nasfk, gpl, instal...)
- [ ] ¿Usé variables de entorno, no rutas hardcodeadas?
- [ ] ¿El servicio tiene guía? → Leerla ANTES de sugerir cambios
- [ ] ¿Sugerí labels de Homepage en vez de services.yaml?
- [ ] ¿El orden es correcto? (mkdir → archivos → permisos → levantar)
- [ ] ¿Notificaciones van con ntfy_send, no notify-send?
- [ ] **¿Voy a modificar un compose? → LEÍ `docs/docker-entorno.md` PRIMERO?**
- [ ] ¿El compose usa `env_file: [../.env, .env]` (no IP/TZ hardcodeados)?
- [ ] ¿Las carpetas de volúmenes existen ANTES de levantar?
- [ ] ¿Después del cambio sugiero `svc catalog-sync <svc>`?
- [ ] **¿Consulté `docs/dependency-map.md` para ver qué más debo actualizar?**
- [ ] **¿Si es servicio nuevo: generé script DebMenux + actualicé AGENTS.md + nas-manual.md?**

### Antes de decir "listo" o "terminado"

- [ ] ¿Todos los archivos del grafo de dependencias están sincronizados?
- [ ] ¿`svc catalog-sync --status` muestra todo ✅?
- [ ] ¿Si copié compose de internet, lo ajusté a las convenciones?
- [ ] ¿Recomendé al usuario qué hacer después? (catalog-sync, recreate, gpl)



## 4c. Consistencia arquitectónica

El framework también mantiene un mapa estructural para comprobar conexiones entre `nas-dotfiles` y `DebMenux`:

| Pieza | Función |
|---|---|
| `agent/architecture/contracts.json` | Contratos verificables y niveles functional/interface/knowledge/documentation/historical |
| `agent/tools/project_index.py` | Índice de archivos, comandos, servicios y conexiones reales en ambos repos |
| `agent/cache/project-index.json` | Índice generado localmente; no es el snapshot incremental |
| `project_scanner.py` | Reporta paridad Bash/Python, contratos rotos y scripts DebMenux desincronizados |
| `docs/architecture-consistency.md` | Diseño y alcance de la arquitectura verificable |

Verificación manual:

```bash
python3 agent/tools/project_index.py --check
svc scan --full
```

`project-index.json` responde **qué existe y dónde está conectado**. `project-snapshot.json` responde **qué cambió desde el último scan**. No deben mezclarse.
