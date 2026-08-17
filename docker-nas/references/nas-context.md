# NAS Skill — Contexto Operativo

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
    homepage, datasql, pgadmin, redis, usb-api, spacedrive
  - Infra: homelab, servidor, backup, cron, systemd, USB, mount
  - IoT: MQTT, broker, ESP32, Home Assistant, alarma, sensor
  - Redes: macvlan, bridge, iot_net, db_net, homepage_net, DNS
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

```
1. mkdir -p $dkco/<svc>/data
2. Crear compose.yml + .env
3. chmod 600 .env
4. Agregar labels homepage.* en compose
5. dk <svc> && svc up <svc>
6. svc catalog-sync <svc>  → genera toda la documentación
```

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
| datasql | 5050 | db_net | `docs/services/datasql-guide.md` |
| filebrowser | 8085 | default | `docs/services/filebrowser-guide.md` |
| homeassistant | 8123 | host | `docs/services/homeassistant-guide.md` |
| homepage | 3000 | homepage_net | `docs/services/homepage-guide.md` |
| ntfy | 8090 | homepage_net | `docs/services/ntfy-guide.md` |
| node-red | 1880 | iot_net | `docs/services/node-red-guide.md` |
| usb-api | 8091 | nativo (systemd) | `agent/catalog/services/usb-api/ficha.md` |

### Redes

| Red | Propósito | Regla |
|-----|-----------|-------|
| `adguard_macvlan_NET` | IP dedicada AdGuard (DNS:53) | Solo macvlan |
| `db_net` | Apps ↔ DBs (interno) | Nunca exponer puertos al host |
| `iot_net` | EMQX ↔ ESPHome ↔ HA | Todo IoT aquí |
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

## 5. Documentación disponible (lazy loading)

**Regla: NO leer estos archivos al activar la skill.** Solo cargar cuando el usuario pregunte sobre ese tema.
**EXCEPCIÓN 1: SIEMPRE leer `docs/docker-entorno.md` ANTES de modificar cualquier compose.**
**EXCEPCIÓN 2: SIEMPRE consultar `docs/dependency-map.md` DESPUÉS de cualquier cambio para verificar la cascada.**

| Trigger | Archivo a cargar |
|---------|-----------------|
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
| Troubleshooting USB / mounts | `docs/services/ntfy-guide.md` §Troubleshooting |
| Configurar Homepage | `docs/services/homepage-guide.md` |
| Home Assistant (automatizaciones, ntfy, cámara) | `docs/services/homeassistant-guide.md` |
| Pipeline de auto-docs | `docs/catalog-sync-pipeline.md` |
| Info completa del NAS | `docs/nas-manual.md` |
| Todos los comandos shell | `docker-nas/references/entorno.md` |
| Todos los comandos svc | `docker-nas/references/svc.md` |
| Seguridad y convenciones | `docker-nas/references/seguridad.md` |
| Diagnóstico paso a paso | `docker-nas/references/diagnostic.md` |
| Redes avanzadas (macvlan) | `docker-nas/references/networking.md` |
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
[2026-08-16] filebrowser requiere :rshared en el bind mount /NAS:/srv:rshared — sin él los USBs montados después no se ven
[2026-08-16] Cuando se mejora un compose existente (ej: agregar :rshared, env_file, quitar TZ) → actualizar TAMBIÉN la guía y la ficha del catálogo
[2026-08-16] Cuando se mejora la gestión de un servicio (ej: HA con !include) → documentar el ANTES y DESPUÉS en la guía para que otros LLMs no sugieran la forma vieja
[2026-08-16] README.md debe reflejar archivos nuevos en la estructura del proyecto — si se crea docs/X.md o scripts/X.sh, actualizar el árbol en README
[2026-08-16] cap_drop:[ALL] NO aplicar ciegamente — rompe Node-RED, HA, ESPHome. Solo para servicios simples (ntfy, redis, filebrowser)
[2026-08-16] deploy:resources:limits NO poner si no se sabe el consumo real — puede causar OOM kill. Primero probar con docker stats
[2026-08-16] catalog-sync.sh EXISTE pero NO está conectado al CLI svc — el comando 'svc catalog-sync' no funciona. Pendiente: integrar en svc.sh o svc_py. Por ahora el LLM ejecuta la cascada manualmente.
[2026-08-16] Al crear una herramienta/script nueva, SIEMPRE verificar que está CONECTADA al sistema (no solo que existe el archivo). Preguntar: ¿cómo se invoca? ¿qué comando la ejecuta? ¿está registrada en svc/alias/path?
[2026-08-16] svc tiene DOS CLIs: bash (svc.sh) y Python (svc_py). Variable NAS_CLI=bash|python decide cuál se usa. Si el usuario tiene NAS_CLI=python, los comandos nuevos agregados a svc.sh NO funcionan hasta que también se agreguen al Python CLI. SIEMPRE verificar en CUÁL CLI se agregó el comando.
[2026-08-16] catalog-sync está en bash CLI pero NO en Python CLI — el usuario usa Python. Pendiente: agregar comando a svc_py/ (Typer)
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
