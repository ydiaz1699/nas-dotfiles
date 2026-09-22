# Ideas y Decisiones — Registro de Problemas → Soluciones

> Documento vivo que captura: qué problema surgió, qué idea tuvo el usuario,
> cómo se resolvió, y qué aprendimos. Sirve como contexto para futuros LLMs
> y como historial de decisiones arquitecturales del proyecto.
>
> Formato: cada entrada es un ciclo completo de pensamiento.

---

## Índice

> El historial conserva el razonamiento de cada decisión. Para el mapa actual de arquitectura, estado, gaps y criterios de aceptación, consultar [`docs/framework-knowledge-compilation.md`](framework-knowledge-compilation.md).

1. [ntfy reemplaza notify-send](#1-ntfy-reemplaza-notify-send)
2. [usb-api como systemd nativo](#2-usb-api-como-systemd-nativo)
3. [USB monta con LABEL](#3-usb-monta-con-label)
4. [Homepage: labels > services.yaml](#4-homepage-labels--servicesyaml)
5. [Pipeline auto-docs en cascada](#5-pipeline-auto-docs-en-cascada)
6. [Skill 2.0: nas-context.md compacto](#6-skill-20-nas-contextmd-compacto)
7. [AGENTS.md formato abierto](#7-agentsmd-formato-abierto)
8. [env_file global + ${SERVER_IP}](#8-env_file-global--server_ip)
9. [HA config con !include](#9-ha-config-con-include)
10. [ntfy.publish no soporta imágenes](#10-ntfypublish-no-soporta-imágenes)
11. [Dependency map para no olvidar cascadas](#11-dependency-map-para-no-olvidar-cascadas)
12. [Skill proactiva con progressive updates](#12-skill-proactiva-con-progressive-updates)
13. [Script creado pero no conectado al sistema](#13-script-creado-pero-no-conectado-al-sistema)
14. [Dual CLI: bash = verdad, Python = interfaz](#14-dual-cli-bash--verdad-python--interfaz)
15. [El LLM no auto-documenta lo que crea](#15-el-llm-no-auto-documenta-lo-que-crea-validación-cruzada)
17. [Flowise como prueba de integración con DataSQL](#17-flowise-como-prueba-de-integración-con-datasql)
18. [Arranque escalonado de Docker en el boot (saga completa)](#18-arranque-escalonado-de-docker-en-el-boot-saga-completa)
19. [OpenWA: gateway WhatsApp desde chat LLM (saga de verificación)](#19-openwa-gateway-whatsapp-desde-chat-llm-saga-de-verificación)
20. [Servicio nuevo sin registrar en layers.conf rompe el boot](#20-servicio-nuevo-sin-registrar-en-layersconf-rompe-el-boot)
21. [OpenWA → n8n: el guard anti-SSRF bloquea el webhook](#21-openwa--n8n-el-guard-anti-ssrf-bloquea-el-webhook)
21. [Skill router: carga condicional de skills para no gastar tokens](#21-skill-router-carga-condicional-de-skills-para-no-gastar-tokens)
22. [OpenWA: whatsapp-web.js rompe el media → cambiar a baileys](#22-openwa-whatsapp-webjs-rompe-el-media--cambiar-a-baileys)
---

## 1. ntfy reemplaza notify-send

**Problema:**
`notify-send` en usb-automount.sh no servía — el NAS es headless, no tiene GUI.
Las notificaciones de USB se perdían silenciosamente.

**Idea del usuario:**
Implementar ntfy (servidor push HTTP self-hosted) que envía al celular Android.

**Proceso de solución:**
1. Crear `lib/notifications.sh` con función `ntfy_send()` + wrappers de conveniencia
2. Instalar ntfy como Docker container (puerto 8090, compose con healthcheck)
3. Reemplazar `notify-send` → `ntfy_send` en usb-automount.sh con fallback inline
4. Configurar `ENABLE_NOTIFICATIONS="true"` + `NTFY_URL` en usb-automount.conf
5. Verificar que el script en `/usr/local/bin/` sea la versión nueva (no la vieja)

**Aprendizaje:**
- El script en `/usr/local/bin/` puede ser versión vieja si no se copia explícitamente
- `ENABLE_NOTIFICATIONS` estaba en "false" por defecto — verificar siempre
- Topics separados (usb, docker, system) permiten configurar prioridades diferentes en la app

---

## 2. usb-api como systemd nativo

**Problema:**
Querer desmontar USBs desde el navegador (Homepage widget con botón ⏏️).
Un contenedor Docker no puede ejecutar `umount` en el host real.

**Idea del usuario:**
Mini API REST como servicio systemd nativo (no Docker).

**Proceso de solución:**
1. Python script con `http.server` (stdlib, sin pip) — 3 endpoints
2. `findmnt -J` para listar USBs montados → JSON
3. Sanitizar device names (solo [a-zA-Z0-9_-]) antes de desmontar
4. Verificar que mountpoint está bajo MOUNT_BASE (seguridad)
5. Unit file systemd con `ProtectHome=true`, `PrivateTmp=true`
6. Enviar notificación ntfy al desmontar exitosamente

**Aprendizaje:**
- El filtro inicial `startswith(MOUNT_BASE)` incluía el propio disco del sistema → cambiar a `startswith(MOUNT_BASE + "/")` y excluir MOUNT_BASE exacto
- Después al agregar LABEL mount, cambiar filtro a solo subdirectorios (no pattern específico)

---

## 3. USB monta con LABEL

**Problema:**
Los USBs se montaban como `/NAS/USB/usb-sdb1` — nombre críptico del kernel.
En File Browser aparecía "usb-sdb1" sin saber qué USB es.

**Idea del usuario:**
Montar con el nombre de la etiqueta del filesystem (ej: `/NAS/USB/MI_PENDRIVE`).

**Proceso de solución:**
1. `blkid -o value -s LABEL /dev/sdb1` para obtener label
2. Sanitizar: espacios → `_`, solo [alnum._-], max 64 chars
3. Si hay conflicto (otro USB con mismo label montado), fallback a `usb-<dev>`
4. Si no tiene label, mantener formato clásico `usb-<dev>`
5. Actualizar usb-api para reconocer ambos patrones

**Aprendizaje:**
- `fatlabel` para poner nombre a FAT32, `ntfslabel` para NTFS, `e2label` para ext4
- El filtro del usb-api necesitó actualizarse 2 veces: primero para excluir MOUNT_BASE, después para aceptar ambos formatos

---

## 4. Homepage: labels > services.yaml

**Problema:**
El LLM puso servicios en `services.yaml` que ya tenían labels en su compose.
Resultado: duplicados y errores de widget (EMQX pedía auth que no se configuró).

**Idea del usuario:**
Preferir siempre labels en el compose (auto-descubrimiento). services.yaml solo para nativos.

**Proceso de solución:**
1. Verificar qué servicios ya tienen labels (AdGuard, EMQX, ESPHome, File Browser, pgAdmin, ntfy)
2. Quitar duplicados de services.yaml
3. Dejar solo usb-api (nativo, no tiene compose)
4. Documentar filosofía: "labels first, services.yaml solo si no se puede"
5. Para tomar labels nuevas: `svc recreate X` (no basta restart)

**Aprendizaje:**
- Homepage auto-descubre via Docker socket + labels — no necesita config centralizada
- Widget type `emqx` necesita credenciales — si no las configuras, da "Not found"
- Si un servicio ya tiene labels, ponerlo TAMBIÉN en services.yaml causa conflicto

---

## 5. Pipeline auto-docs en cascada

**Problema:**
Al crear un servicio manualmente, se olvidaba crear la ficha, la guía, el script
DebMenux, actualizar SKILL.md. Todo era manual y se perdía.

**Idea del usuario:**
Un sistema automático: al detectar compose nuevo, generar TODO en cascada.
Bidireccional (DebMenux → nas-dotfiles Y viceversa). Con hook de Kiro.

**Proceso de solución:**
1. `catalog-sync.sh` — script bash que escanea $dkco/ y genera lo que falta
2. `register_to_catalog()` en DebMenux — se ejecuta al final de cada install
3. Hook Kiro `PostFileSave` en compose.yml — dispara al guardar
4. Cada generador verifica si el archivo ya existe (nunca sobreescribe)
5. Notifica via ntfy al completar

**Aprendizaje:**
- Nunca sobreescribir documentación existente — solo generar placeholders
- El compose del catálogo SÍ se actualiza si el source es más nuevo (única excepción)
- `--dry-run` y `--status` son esenciales para verificar sin romper nada

---

## 6. Skill 2.0: nas-context.md compacto

**Problema:**
El SKILL.md era muy largo (~300 líneas). Los LLMs cargaban todo pero no usaban
la mitad. Además, no tenían "memoria" de errores pasados (repetían los mismos).

**Idea del usuario:**
Skill compacta basada en conceptos de Skills 2.0 (Anthropic): registry ligero,
lazy loading, self-learning, trigger pushy. Video de referencia en _drafts/.

**Proceso de solución:**
1. Crear `references/nas-context.md` — solo hechos, no prosa
2. Skill Registry = tabla de servicios + path a docs (índice, no biblioteca)
3. Lazy loading = solo cargar guías cuando el usuario pregunta por ese servicio
4. Progressive Updates = sección donde se acumulan correcciones del usuario
5. Trigger pushy = 50+ palabras clave para que se active incluso sin decir "NAS"
6. Checklist de verificación antes de responder

**Aprendizaje:**
- "Lo justo y necesario" > "cuanto más contexto mejor" (del video)
- Encoded preferences (aliases, rutas, convenciones) nunca caducan con modelos nuevos
- El self-learning loop es lo más valioso — errores no se repiten si se registran
- SKILL.md apunta a nas-context.md, no duplica contenido

---

## 7. AGENTS.md formato abierto

**Problema:**
La skill solo funcionaba en Kiro. Si el usuario usaba Claude Code, Cursor, u otro
agente, no tenía contexto del NAS (como pasó con el LLM que configuró HA sin saber).

**Idea del usuario:**
AGENTS.md — formato abierto (60k+ repos, Linux Foundation) que cualquier agente lee.

**Proceso de solución:**
1. Crear `AGENTS.md` en raíz de ambos repos (nas-dotfiles + DebMenux)
2. Contenido: versión compacta de las reglas más importantes
3. Compatible con: Claude Code, Codex, Cursor, Gemini CLI, Aider, Jules

**Aprendizaje:**
- Es complementario a la skill de Kiro (no la reemplaza)
- Cualquier agente que abra el repo ya sabe los aliases y convenciones
- Mantener sincronizado con nas-context.md (son la misma info en diferente formato)

---

## 8. env_file global + ${SERVER_IP}

**Problema:**
IPs hardcodeadas en labels de Homepage. TZ duplicado en environment + .env global.
El LLM dijo "no necesitas modificar el compose" pero estaba mal.

**Idea del usuario:**
$dkco/.env como fuente única de verdad para SERVER_IP y TZ. Todo servicio hereda.

**Proceso de solución:**
1. Todos los compose usan `env_file: [../.env, .env]`
2. Labels usan `${SERVER_IP}` (interpolado por Docker Compose al levantar)
3. TZ se quita de `environment:` (se hereda del global)
4. Documentar en `docs/docker-entorno.md` como regla obligatoria
5. Agregar a la skill como corrección permanente

**Aprendizaje:**
- NUNCA decir "no necesitas cambios" sin leer docker-entorno.md primero
- Docker Compose interpola variables de env_file en labels al hacer `up`
- `svc recreate X` necesario para que las labels se regeneren con la IP nueva

---

## 9. HA config con !include

**Problema:**
`configuration.yaml` de HA se volvería enorme con shell_commands, rest_commands,
notify platforms, etc. Todo mezclado en un solo archivo.

**Idea del usuario:**
Organizar con `!include` en carpeta `includes/` — un archivo por tema.

**Proceso de solución:**
1. Crear `$dkco/homeassistant/data/includes/` con archivos separados
2. `shell_commands.yaml` — ntfy_camara y futuros
3. `tvoverlay_commands.yaml` — toda la config de TvOverlay (8 endpoints)
4. `notify.yaml` — plataformas de notificación (tvoverlay_sala)
5. En configuration.yaml: `shell_command: !include includes/shell_commands.yaml`
6. Documentar con comandos `cat >` para crear desde terminal

**Aprendizaje:**
- No pueden coexistir `shell_command:` directo Y como `!include` — error de duplicado
- Recargar: "YAML → Recargar Shell Commands" o reiniciar HA completo
- Documentar siempre la estructura de carpetas para que otro LLM no sugiera meter todo en configuration.yaml

---

## 10. ntfy.publish no soporta imágenes

**Problema:**
La integración oficial de ntfy en HA (`ntfy.publish`) no acepta el campo `image`.
Error: "extra keys not allowed @ data['image']". Feature request pendiente.

**Idea del usuario:**
Usar `shell_command` + `curl -T` como workaround para enviar imágenes.

**Proceso de solución:**
1. `camera.snapshot` guarda en `/config/www/snapshots/alarma.jpg` (ruta fija)
2. `shell_command.ntfy_camara` envía con `curl -T /config/www/snapshots/alarma.jpg`
3. `delay: { seconds: 2 }` entre snapshot y envío (esperar escritura)
4. Verificar que la carpeta www/snapshots/ existe (`mkdir -p`)
5. `ntfy.publish` se usa solo para notificaciones de texto (sin imagen)

**Aprendizaje:**
- `priority` en ntfy.publish es NÚMERO (1-5), no texto ("high")
- La carpeta debe existir ANTES del primer snapshot
- `$(date...)` en shell_command NO coincide con el timestamp del snapshot — usar nombre fijo
- `/config/www/` es accesible como `http://IP:8123/local/` (no necesita allowlist)
- `/tmp/` sí necesita allowlist — mejor usar `/config/www/snapshots/`

---

## 11. Dependency map para no olvidar cascadas

**Problema:**
El LLM modificaba un compose pero olvidaba actualizar: guía, ficha, AGENTS.md,
nas-context, script DebMenux, README. Cada vez había que recordarle.

**Idea del usuario:**
Un mapa que muestre las conexiones entre archivos — "si tocas X, actualiza Y y Z".

**Proceso de solución:**
1. Grafo visual: compose.yml → 9 archivos dependientes
2. Tabla de impacto por tipo de cambio
3. Distinción automático (catalog-sync) vs manual (AGENTS.md, README)
4. Comandos de verificación (`grep` IP hardcodeada, `svc catalog-sync --status`)
5. Integrar en la skill como lectura OBLIGATORIA después de cambios

**Aprendizaje:**
- El mapa no es solo documentación — es una instrucción al LLM
- "Antes de decir listo" → verificar dependency-map
- Lo automático (catalog-sync) cubre ~60% pero AGENTS.md/README/nas-manual son manuales

---

## 12. Skill proactiva con progressive updates

**Problema:**
El LLM era reactivo — solo hacía lo que le pedían. No anticipaba problemas
ni recomendaba actualizaciones de documentación. El usuario tenía que recordarle
cada paso de la cascada.

**Idea del usuario:**
Que la skill instruya al LLM a ser PROACTIVO: recomendar sin que le pidan,
verificar antes de decir "listo", ajustar composes copiados de internet,
y registrar aprendizajes automáticamente.

**Proceso de solución:**
1. 7 instrucciones proactivas en la sección Progressive Updates
2. Checklist expandido con "¿consulté dependency-map?" y "¿README refleja?"
3. Triggers nuevos: "usuario copia compose de internet" → auto-verificar convenciones
4. "Nuevo script/herramienta" → preguntar dónde conecta con el sistema
5. "Mejora a compose existente" → actualizar guía con ANTES/DESPUÉS

**Aprendizaje:**
- Un LLM sin instrucciones proactivas repite errores de sesiones anteriores
- El self-learning loop (progressive updates) + dependency-map + comportamiento proactivo = sistema que mejora con cada uso
- La skill no es estática — evoluciona con cada sesión

---

## Plantilla para nuevas entradas

```markdown
## N. Título corto

**Problema:**
(Qué salió mal o qué faltaba)

**Idea del usuario:**
(Qué sugirió o qué quería lograr)

**Proceso de solución:**
1. Paso 1
2. Paso 2
3. ...

**Aprendizaje:**
- Lección 1
- Lección 2
```

> **Instrucción al LLM:** Cuando se resuelva un problema nuevo en una sesión,
> agregar una entrada aquí siguiendo la plantilla. Esto permite que futuros
> LLMs entiendan no solo QUÉ se hizo, sino POR QUÉ y CÓMO se llegó a esa decisión.



---

## 13. Script creado pero no conectado al sistema

**Problema:**
Se creó `docker/cli/lib/catalog-sync.sh` con la función `catalog_sync()`, se documentó
como `svc catalog-sync`, pero NUNCA se conectó al CLI `svc`. Al ejecutar el comando
en el NAS: "No such command 'catalog-sync'".

**Idea del usuario:**
Detectar esto antes — al crear una herramienta, verificar que esté CONECTADA
al sistema (no solo que exista el archivo). El dependency-map y la skill proactiva
deberían atrapar este tipo de errores.

**Proceso de solución:**
1. El script existe en `docker/cli/lib/catalog-sync.sh`
2. Falta: agregar `catalog-sync` como comando en `svc.sh` (bash CLI) o `svc_py` (Python CLI)
3. Mientras no se conecte, el LLM ejecuta la cascada manualmente

**Pendiente de implementar:**
- En `docker/cli/svc.sh`: agregar case `catalog-sync)` que haga `source` del script y llame a `catalog_sync "$@"`
- O en `svc_py/`: agregar comando Typer que invoque el mismo script

**Aprendizaje:**
- Crear un archivo ≠ conectarlo al sistema. SIEMPRE verificar:
  - ¿Cómo se invoca? (¿qué comando lo ejecuta?)
  - ¿Está registrado en svc/alias/PATH?
  - ¿Se puede probar desde terminal?
- Agregar a la checklist del LLM: "Si creé un script, ¿está accesible para el usuario?"
- El dependency-map debería tener una sección de "herramientas CLI" que liste qué scripts están conectados a qué comandos

---

## 14. Dual CLI: bash = verdad, Python = interfaz

**Problema:**
El NAS tiene 2 CLIs (`svc.sh` en bash y `svc_py/` en Python). Al crear un comando
nuevo (catalog-sync, scan), se implementó solo en bash. El usuario usa Python por
defecto (`NAS_CLI=python`) → el comando no existía para él. Se duplicó la lógica
manualmente, con riesgo de divergencia.

**Idea del usuario:**
Bash como ÚNICA fuente de verdad para la lógica. Python solo como interfaz bonita
que ejecuta bash por detrás (`subprocess`). Un comando nuevo solo se implementa
en bash y Python lo hereda automáticamente.

**Proceso de solución:**
1. Crear `svc_py/core/bash_bridge.py` — helper genérico para invocar `svc.sh`
2. Comandos simples: Python → `subprocess.run(["bash", svc.sh, cmd, svc])`
3. Comandos con output tabular: Python ejecuta bash, parsea output, embellece con Rich
4. Comandos interactivos (menu, update-all): Python usa InquirerPy para selección,
   luego invoca bash para la acción real
5. Un comando nuevo en bash se expone automáticamente en Python sin código adicional
   (passthrough genérico para comandos no registrados explícitamente)

**Arquitectura:**

```
┌───────────────────────────────────────────┐
│  Python CLI (svc_py/)                     │
│  • Rich tables, colores, spinners         │
│  • InquirerPy multi-select               │
│  • Parsea + embellece output de bash      │
│  • NUNCA reimplementa lógica de negocio   │
│                                           │
│         ↓ bash_bridge.svc() ↓             │
│                                           │
│  Bash CLI (docker/cli/svc.sh)             │
│  • TODA la lógica real                    │
│  • Funciona sin Python (0 dependencias)   │
│  • Fuente de verdad única                 │
└───────────────────────────────────────────┘
```

**Reglas de implementación:**
- Comando nuevo → implementar SOLO en bash (`svc.sh` + lib correspondiente)
- Python obtiene el comando gratis via passthrough del bridge
- Si el comando se beneficia de UI elaborada (tabla, progreso, interactividad)
  → agregar wrapper explícito en `svc_py/commands/` que invoca bash y embellece
- Si Python falla (deps rotas, venv corrupto) → bash siempre funciona como fallback

**Aprendizaje:**
- "Una sola fuente de verdad" elimina la divergencia entre CLIs
- El Python CLI agrega VALOR (UX) sin duplicar LÓGICA
- La selección de CLI (`NAS_CLI=bash|python`) solo afecta la presentación, no el comportamiento
- Futuros LLMs: al crear un comando nuevo, solo tocar bash — Python lo hereda


---

## 15. El LLM no auto-documenta lo que crea (validación cruzada)

**Problema:**
En sesión 2026-08-17 (Kiro Web), un LLM implementó: scanner incremental, svc snapshot/rollback,
compare_catalog, completions, agent prompt. Pero al auditar después, se descubrió que:
- `dependency-map.md` tabla CLI no se actualizó (seguía marcando catalog-sync como "PENDIENTE")
- La skill (nas-context.md) no mencionaba las 3 tools nuevas
- No se generó SESSION-*.md al cerrar

El LLM creó código correcto pero no aplicó el sistema de auto-documentación que él mismo
ayudó a diseñar.

**Idea del usuario:**
Comparar la auditoría del LLM contra las ideas/decisiones documentadas para detectar
exactamente qué se quedó sin sincronizar. El scanner detecta servicios desconectados,
pero NO detecta documentos desactualizados (como la tabla CLI del dependency-map).

**Proceso de solución:**
1. Usuario comparó output del scanner vs docs manualmente → encontró 3 gaps
2. Se corrigió dependency-map.md (tabla CLI de 15 → 26 comandos con estado real)
3. Se documentó esta lección como entry #15

**Aprendizaje:**
- El scanner detecta archivos desconectados, pero NO verifica contenido semántico de docs
- Para eso se necesita: después de cualquier cambio, el LLM DEBE consultar dependency-map.md
- La skill ya tiene esta regla (sección 7 checklist), pero el LLM la ignoró por falta de contexto
- **Futuro:** el scanner podría verificar que la tabla CLI tiene la misma cantidad de comandos
  que `_SVC_GLOBAL_CMDS` en `shell/lib/docker.sh` — detección automática de desincronización

**Regla nueva:**
Al cerrar una sesión que implementó features nuevas, SIEMPRE correr mentalmente:
1. ¿dependency-map tabla CLI refleja los comandos nuevos?
2. ¿nas-context.md Progressive Updates tiene la fecha de hoy?
3. ¿PENDIENTES-proxima-sesion.md tiene registro de esta sesión?


---

## 16. Centralizar defaults con `extends` + `_common.yml`

**Problema:**
Cada compose repetía los mismos bloques (resource limits, security_opt, logging)
como anchors YAML. Con 10+ servicios, un cambio en los defaults requería editar
10 archivos. Además, `<<: *anchor` hace shallow merge (si sobreescribes un sub-campo,
pierdes el resto del bloque).

**Idea del usuario:**
Tener un archivo global con los defaults para no repetirlos en cada compose.
Similar a `<<: *common-env` pero para resources, security, logging.

**Opciones evaluadas:**

| Opción | Cómo funciona | Pro | Contra |
|--------|---------------|-----|--------|
| A: include | Importa servicios | — | No importa anchors sueltos |
| B: extends | Deep merge desde archivo externo | ✅ Estándar Docker, sobreescribe parcial | Necesita _common.yml accesible |
| C: multi-file (-f) | svc pasa -f _anchors.yml automático | Mantiene estilo anchors | Requiere parchar svc.sh, no funciona con docker compose directo |

**Decisión: Opción B (`extends`)**

Razones:
1. **Deep merge** — cambias `memory: 1g` sin perder `reservations`
2. **No requiere parchar svc.sh** — funciona con `docker compose` directo
3. **Estándar Docker** — cualquier persona/LLM entiende `extends`
4. **Un cambio en _common.yml se propaga a todos** sin tocar cada compose

**Implementación:**
- `$dkco/_common.yml` (o `agent/catalog/_common.yml` en el repo) con servicio `_defaults`
- En el catálogo: `agent/catalog/services/<svc>/compose.yml` usa `file: ../../_common.yml`
- En el NAS: `$dkco/<svc>/compose.yml` usa `file: ../_common.yml`
- `catalog-sync`, `export_service` y DebMenux transforman la ruta al copiar entre contextos
- Solo declarar lo que DIFIERE del default (memory, ulimits, etc.)

**Migración gradual:**
- Piloto: EMQX (migrado en catálogo)
- Después: migrar uno por uno cuando se toque cada servicio
- NO migrar todos de golpe (riesgo innecesario)

**Rollback:**
- Si falla: `git checkout -- agent/catalog/services/<svc>/compose.yml`
- En el NAS: `svc rollback <svc>` (restaura snapshot anterior)
- Plan completo en `docs/PLAN-extends-common.md`

**Aprendizaje:**
- `<<:` (YAML merge key) es shallow — no sirve para sobreescribir sub-campos
- `extends` es deep merge — Docker lo resuelve internamente
- `x-common-env` con TZ no se necesita si ya hay `env_file: [../.env, .env]`
- Migrar gradualmente (1 servicio piloto) reduce riesgo


## 17. Flowise como prueba de integración con DataSQL

**Problema:**
Se necesitaba una aplicación real para probar si las reglas de integración con DataSQL funcionan fuera del propio stack de bases de datos: usuario y base dedicados, `db_net`, secretos locales, persistencia, healthcheck y documentación en cascada.

**Idea del usuario:**
Instalar Flowise como prueba, conectándolo a PostgreSQL de DataSQL en lugar de crear otra base de datos dentro de su compose.

**Decisión:**
1. Mantener Flowise en un compose separado en `$dkco/flowise/`.
2. Crear `flowise_db` y `flowise_user` dentro de DataSQL.
3. Conectar mediante `db_net` usando el hostname `datapostgres`.
4. No usar `depends_on` contra DataSQL porque está en otro compose.
5. Persistir `/home/node/.flowise` en `./data` y conservar `FLOWISE_SECRETKEY_OVERWRITE`.
6. Exponer temporalmente el dashboard en el puerto `8100` para la prueba LAN.
7. Registrar la configuración en ficha, compose de catálogo, `.env.example`, guía, DebMenux y los inventarios relevantes.

**Alternativas descartadas:**
- SQLite como configuración de integración real: solo sirve como smoke test aislado.
- Un PostgreSQL dentro del compose de Flowise: duplica DataSQL y rompe la arquitectura compartida.
- Usar la IP fija del contenedor PostgreSQL: el nombre DNS de Docker reduce acoplamiento.
- `depends_on` entre proyectos Compose: no controla servicios definidos en otro proyecto.

**Aprendizaje:**
- Una skill externa puede aportar variables oficiales, pero debe auditarse contra `docs/docker-entorno.md`, la guía DataSQL y el compose real antes de incorporarla.
- La configuración oficial de Flowise usa `DATABASE_TYPE=postgres`, puerto interno `3000`, `/home/node/.flowise` para persistencia y `/api/v1/ping` para healthcheck.
- La instalación real requiere primero validar DataSQL, la red y el puerto; el sandbox solo puede preparar y validar archivos, no operar el NAS.



---

## 18. Arranque escalonado de Docker en el boot (saga completa)

**Problema:**
Al reiniciar el NAS, los 17 contenedores arrancaban en paralelo (por `restart: unless-stopped`), saturando un hardware de 2 cores: pico de `%wa` ~86% y `load average` ~9.6. Se necesitaba arrancarlos en orden, esperando que las dependencias (sobre todo la DB) estuvieran realmente listas.

**Idea del usuario:**
Escalonar el arranque por capas con systemd + un script que lea una lista editable de servicios, sin tener que tocar systemd al agregar/quitar servicios. Más adelante: arranque secuencial dentro de cada capa, y respetar servicios detenidos a propósito.

**Proceso de solución (varias iteraciones, cada reboot en frío reveló una capa distinta del problema):**
1. `shell/scripts/boot-order.sh` lee `$dkco/scripts/layers.conf` (capas separadas por línea en blanco) y arranca por capas con health gates. Una sola unidad `docker-boot-staged.service` (generada con rutas reales por `install-boot-service.sh`), NO 3 unidades hardcodeadas.
2. Policy `unless-stopped` → `on-failure:5` (Docker no revive todo al iniciar el daemon; systemd controla el orden). Jobs one-shot conservan `no`. `apply-restart-policy.sh` migra contenedores vivos con `docker update` sin arranque masivo.
3. Arranque **secuencial** por defecto dentro de capa (`BOOT_ORDER_SERIAL=1`).
4. `svc no-boot`/`boot-enable` (marcador `$dkco/<svc>/.no-boot`): saltar-con-aviso servicios detenidos a propósito, sin bloquear la capa. Paridad en CLI Python (delega a bash).
5. Timeouts para arranque en frío: Postgres `start_period` 30→120s; `BOOT_ORDER_HEALTH_TIMEOUT` 120→480s; `TimeoutStartSec` systemd → 2400s.
6. `unhealthy` transitorio ya no aborta: se espera hasta agotar el timeout (los primeros health checks fallan mientras el servicio inicializa).
7. Pausas de estabilización de CPU: `BOOT_ORDER_INITIAL_DELAY` (30s antes de la 1ª capa) y `BOOT_ORDER_SETTLE_DELAY` (10s entre servicios/capas). Ambas `0` en arranque manual.
8. **Causa raíz final:** `flowise-worker` tenía `depends_on: flowise condition: service_healthy`. `docker compose up` bloqueaba esperando ese health y en frío fallaba con `dependency failed to start` ANTES de que boot-order pudiera actuar. Fix: `condition: service_started` (el health lo vigila boot-order). Mismo patrón pendiente en lobehub→rustfs.
9. `stop-order.sh` + `stop-all.sh`/`restart-all.sh` reescritos: apagado escalonado en orden INVERSO (los viejos solo bajaban 3 servicios y mataban el resto con poweroff).

**Decisión:**
Home Assistant primero en la Capa 2 (usa PostgreSQL). `flowise-worker` NO va en `layers.conf` (interno del compose flowise). El arranque en frío tarda ~11 min a propósito (pausas + servicios lentos): NO juzgar como fallo hasta que `systemctl is-active docker-boot-staged.service` diga `failed` o el log muestre `ERROR: se aborta`.

**Alternativas descartadas:**
- 3 unidades systemd (`docker-layer1/2/3.service`) con servicios hardcodeados: frágil, hay que tocar systemd al cambiar servicios. Se usó 1 unidad + `layers.conf`.
- `restart: "no"` global: pierde la recuperación en runtime. Se usó `on-failure:5`.
- `--no-deps` en `svc up` para saltar el wait interno: riesgo de dejar contenedores sin arrancar. Mejor `service_started` + pausas.
- Relajar el gate de boot-order a "tolerante siempre": ocultaría fallos reales. Se mantiene estricto pero con timeout amplio.

**Aprendizaje:**
- El arranque en frío de hardware modesto solo se diagnostica en el reboot REAL; ni tests ni teoría lo capturan del todo.
- `docker compose up` respeta `depends_on: service_healthy` INTERNO y bloquea; para orquestación externa usar `service_started` y dejar el health al orquestador.
- Separar código (`$NAS_DOTFILES`) de config/estado runtime (`$dkco`): `layers.conf`, logs y `.no-boot` viven en `$dkco`.
- Regla de verificación: el arranque escalonado es lento a propósito; usar `systemctl is-active` / `grep "Arranque completo"`, no juzgar a mitad.
- Al reescribir scripts de sistema (stop/restart), revisar si ya existían con lógica vieja (los originales bajaban solo 3 servicios). El mapa `framework-audit.md` ahora lista `shell/scripts/` para que el LLM no los desconozca.


---

## 19. OpenWA: gateway WhatsApp desde chat LLM (saga de verificación)

**Problema:**
El usuario pidió instalar un gateway self-hosted de WhatsApp (`rmyndharis/OpenWA`)
en el NAS e integrarlo con n8n. El punto de partida era una guía previa de un
chat que mezclaba datos correctos con inventados (endpoints, header de API,
nombre del repo), y no estaba adaptada al framework nas-dotfiles.

**Idea del usuario:**
No clonar el repo ni construir la imagen: usar la imagen publicada y empaquetar
el servicio siguiendo las convenciones del NAS (catálogo + guía + skill + boot).
Verificar todo contra la fuente real antes de afirmar nada.

**Proceso de solución:**
1. Verificar el repo real por API: existe, MIT, 14.4k estrellas. Comparado
   contra una alternativa (`MultiWA`): OpenWA gana por madurez, nodo oficial de
   n8n y Baileys estable.
2. Leer fuentes reales: `openapi.json` (header `X-API-Key`, endpoints de
   sesión/mensajes), `Dockerfile` (root FS read-only + tmpfs + caps mínimas),
   `docker-compose.dev.yml` (puerto 2785, red), `docs/22-n8n-integration.md`
   (nodo oficial), y la doc oficial `docs.open-wa.org` (v0.23.5).
3. Crear el servicio en el catálogo: `compose.yml` (imagen pineada
   `ghcr.io/rmyndharis/openwa:0.23.5`, `db_net`, hardening de Chromium),
   `.env.example`, `ficha.md`, guía `docs/services/openwa-guide.md`, y registro
   en `layers.conf`.
4. Runtime en el NAS reveló varios fallos que la teoría no capturó, corregidos
   en cascada (código → guía → doc del entorno):
   - `pids_limit` a nivel servicio choca con `deploy.resources` heredado de
     `_common.yml` (`can't set distinct values on 'pids_limit'...`). Fix:
     `deploy.resources.limits.pids`.
   - Dashboard en blanco por HTTP → `CSP_UPGRADE_INSECURE_REQUESTS=false` +
     `CORS_ORIGINS`.
   - `Invalid API key` tras añadir `API_KEY_PEPPER`: el pepper invalida el hash
     de las keys ya sembradas. Fix: re-sembrar `data/main.sqlite` (sin perder
     sesiones, que viven en `data/openwa.sqlite` y `data/sessions/`).
   - `Validation failed (uuid is expected)` / `Session is not active`: la API
     usa el `id` (UUID) de la sesión en las URLs, NO el `name`.
   - El mensaje no llegaba: el número de ejemplo (`34600111222`) era ficticio y
     se resolvía a un `@lid`. Con un número real y `@c.us`, envío OK
     (`messageId` con sufijo `_out`).
5. Crear `wa-send.sh` para enviar desde terminal resolviendo el UUID solo.

**Decisión:**
SQLite local (single-tenant), motor `whatsapp-web.js`, red `db_net` (n8n llega
por `http://openwa:2785`), imagen pineada. Excepción de seguridad documentada:
Chromium necesita `read_only`+`tmpfs`+caps mínimas (no `cap_drop:[ALL]` a secas).

**Alternativas descartadas:**
- Clonar el repo y `docker compose up` (la guía vieja): innecesario, hay imagen
  en GHCR. Se pinea el tag en vez de `latest`.
- MultiWA: proyecto mucho más joven (33 estrellas) y Baileys experimental.
- PostgreSQL de DataSQL para OpenWA: se dejó SQLite por simplicidad; migrable.

**Aprendizaje:**
- **Verificar contra la fuente real, no contra guías heredadas.** La guía previa
  tenía endpoints y detalles inventados; la única verdad es el repo + doc oficial.
- **La API de OpenWA opera por UUID, no por name** — un LLM lo adivinaría mal.
- **`API_KEY_PEPPER` es destructivo para las keys existentes**: ponerlo desde el
  principio o re-sembrar tras cambiarlo.
- **Chromium rompe el patrón de hardening estándar del NAS**: excepción
  documentada en ficha y guía.
- **Nunca dejar valores de ejemplo que parezcan reales** (como un número de
  teléfono) sin marcarlos claramente como CAMBIAR: el usuario ejecutó el comando
  tal cual y el mensaje no llegaba porque el número era ficticio. En adelante,
  usar `TUNUMERO`/`<CAMBIAR>` bien visible en los comandos.
- **En este entorno los PR se "congelan" si se hace push justo tras crearlos**:
  tras cada merge, rebasar la rama sobre `main` y abrir un PR limpio.



---

## 20. Servicio nuevo sin registrar en layers.conf rompe el boot

**Problema:**
Se creó el servicio `openwa` en otra sesión LLM. Al reiniciar, el arranque escalonado abortó: `svc boot-status` mostró `✗ FALLÓ — openwa existe en /docker pero no está en layers.conf`. El servicio nuevo no se añadió a `$dkco/scripts/layers.conf`, y con `BOOT_ORDER_REQUIRE_ALL=1` el boot falla a propósito para avisar.

**Idea del usuario:**
Automatizar el registro y que el LLM no dependa de "recordar" la skill: (A) que `svc create` avise/ayude a añadir a layers.conf, (B) que el error del boot dé el comando exacto para arreglarlo, y (C) que `dotfile-skill` sea una skill router que cargue `docker-boot-order` solo cuando se crea/elimina un servicio, sin saturar tokens cargando todas las skills.

**Proceso de solución:**
1. Fix inmediato del NAS: añadir `openwa` a la Capa 5 de `layers.conf` (usa `db_net` pero SQLite local → independiente, no consumidor de datasql healthy).
2. (A) `svc create`/`svc clone` llaman a `_svc_layers_reminder`: si el servicio no está en layers.conf, muestran el comando exacto para añadirlo o `svc no-boot`.
3. (B) `boot-order.sh`: cuando un servicio descubierto falta en layers.conf, el error ahora incluye las 2 opciones de arreglo y el comando de reintento (antes solo decía "no está en layers.conf").
4. (C) `dotfile-skill` convertida en router: tabla "cuándo cargar cuál skill" y regla de cargar `docker-boot-order` ANTES de terminar de crear un servicio.

**Decisión:**
El comportamiento de fallar el boot NO se relaja (es la protección correcta: mejor fallar visible que arrancar dejando un servicio fuera en silencio). Lo que se mejora es la GUÍA hacia la solución (recordatorio + error accionable + router de skills).

**Alternativas descartadas:**
- Poner `BOOT_ORDER_REQUIRE_ALL=0` por defecto: ocultaría servicios olvidados; se pierde la red de seguridad.
- Que `svc create` edite `layers.conf` automáticamente sin preguntar: no sabe en qué capa va (depende de las dependencias del servicio); mejor recordar + mostrar el comando.

**Aprendizaje:**
- Crear un servicio SIEMPRE incluye registrarlo en `layers.conf` (o `svc no-boot`). Ahora el propio `svc create` lo recuerda.
- El error del boot debe ser accionable: decir QUÉ hacer, no solo qué falló.
- Las skills deben tener una de ENTRADA (`dotfile-skill`) que enrute a las específicas; no cargar todas siempre (satura tokens) ni depender de que el LLM adivine cuál activar.
- `svc boot-status` fue clave para diagnosticar rápido (dijo exactamente qué servicio faltaba).



---

## 21. Skill router: carga condicional de skills para no gastar tokens

**Problema:**
De dónde surge: en otra sesión se creó `openwa` sin registrarlo en `layers.conf` y el boot falló (ver #20). La causa de fondo no fue solo el olvido, sino que **el LLM no sabía qué skill activar ni cuándo**: la skill correcta (`docker-boot-order`) solo servía si el LLM la cargaba, y nada lo garantizaba. Además, cargar TODAS las skills siempre satura el contexto (tokens) de cualquier LLM.

**Idea del usuario:**
1. Que exista una skill principal que actúe como **router**: se activa siempre para tareas del NAS y desde ella se cargan las específicas solo cuando hacen falta, sin que el LLM tenga que adivinar.
2. Refinamiento: la carga debe ser **condicional según la tarea concreta**, no por categoría. Ejemplo textual del usuario: *"cuando te pido que me crees un nuevo servicio no es necesario cargar la skill de base de datos"* — solo se carga `datasql` si ESE servicio usa PostgreSQL/Redis.

**Proceso de solución:**
1. `dotfile-skill` convertida en skill de ENTRADA/router: su `description` lo declara y su cuerpo tiene una tabla "cuándo cargar cuál skill".
2. Se añadió la sección "Carga CONDICIONAL, no por categoría": al crear un servicio se carga siempre `docker-boot-order` (todo servicio va a `layers.conf`), pero `datasql` solo si usa DB, `nas-runtime-secrets` solo si tiene secretos. Ejemplo openwa (SQLite local) → NO cargar `datasql`.
3. Refuerzo con el auto-recordatorio de `svc create` (#20) para que el paso de `layers.conf` no dependa solo de la memoria del LLM.

**Decisión:**
Una sola skill router (`dotfile-skill`), no una skill nueva "índice". La carga de skills específicas es condicional a la necesidad real de la tarea. El inventario completo de componentes vive en `docs/framework-audit.md` (que también tiene el índice de skills), no duplicado en la router.

**Alternativas descartadas:**
- Cargar todas las skills en cada sesión: satura tokens, justo lo que se quiere evitar.
- Crear una skill "índice de skills" separada: duplicaría el índice que ya está en `framework-audit.md`; la router enlaza, no copia.
- Cargar por categoría amplia (ej. "cualquier servicio → datasql"): carga skills innecesarias (openwa no usa DB).

**Aprendizaje:**
- Regla de carga de skills: **condicional a la tarea concreta**, no por categoría ni "por si acaso". Menos tokens, más preciso.
- Una skill router de entrada evita que el LLM adivine o cargue todo; le dice explícitamente qué activar y cuándo.
- El ejemplo del usuario (crear servicio ≠ cargar datasql) es el patrón general: cargar solo lo que la acción realmente toca.


---

## 21. OpenWA → n8n: el guard anti-SSRF bloquea el webhook

**Problema:**
Al activar el nodo OpenWA Trigger en n8n para recibir mensajes de WhatsApp, el
registro del webhook fallaba con `400 Bad Request — Destination address is not
allowed`. Se perdió tiempo persiguiendo pistas falsas: el campo Filters (que
quedaba en un estado inválido al importar el JSON), el modo Fixed/Expression, la
selección de sesión. El error real solo apareció al abrir "Show Details".

**Idea del usuario:**
Exigir el mensaje de error exacto en vez de seguir adivinando, y verificar la
documentación oficial para que el compose salga válido a la primera.

**Proceso de solución:**
1. "Show Details" reveló el error real: `Destination address is not allowed`.
2. Diagnóstico: OpenWA tiene un guard anti-SSRF que valida la URL del webhook
   **al registrarla** (no solo al entregar) y rechaza direcciones
   privadas/internas por defecto.
3. n8n construye la URL desde su `WEBHOOK_URL` = `http://${SERVER_IP}:5678`
   (IP privada de la LAN) → OpenWA la bloquea.
4. Fix: añadir `SSRF_ALLOWED_HOSTS: ${SERVER_IP}` al `environment:` del compose
   de OpenWA y `svc recreate openwa`. Confirmado en runtime: el Trigger recibe
   eventos.
5. Verificado contra la doc oficial `docs/06-api-specification.md`: la
   validación en registro y las variables `WEBHOOK_SSRF_PROTECT` /
   `SSRF_ALLOWED_HOSTS` estaban documentadas.

**Decisión:**
Permitir la IP del NAS en `SSRF_ALLOWED_HOSTS` (cambio mínimo, no toca n8n).

**Alternativas descartadas:**
- Cambiar `WEBHOOK_URL` de n8n a `http://n8n:5678` (red interna): afecta a TODOS
  los webhooks de n8n, incluidos los que se llaman desde fuera de la LAN.
- Desactivar el SSRF por completo (`WEBHOOK_SSRF_PROTECT=false`): baja la
  seguridad sin necesidad; el allowlist es más quirúrgico.

**Aprendizaje:**
- **Leer la doc NO basta: hay que APLICARLA al caso concreto.** La variable
  `SSRF_ALLOWED_HOSTS` y el guard SSRF estaban en la doc que se exploró al armar
  el compose, pero no se conectó "OpenWA entrega webhooks a n8n en IP privada" +
  "OpenWA bloquea IPs privadas por SSRF" = "hay que permitir esa IP". El compose
  inicial se entregó incompleto por no razonar esa implicación. Al preparar
  archivos que deben funcionar a la primera, revisar las variables de seguridad
  (SSRF, CORS, CSP) contra el escenario real de despliegue, no solo listarlas.
- **Pedir el error exacto antes que adivinar.** Se dieron varias vueltas con el
  campo Filters cuando el error real era otro; "Show Details" lo resolvió en un
  paso. Ante un `Bad request` genérico, exigir el detalle antes de proponer fixes.
- Un `chatId` entrante puede ser `@lid` (id de privacidad). Para responder sirve
  tal cual; para iniciar un envío nuevo se necesita `@c.us`.
- `message.received` solo se dispara con mensajes de OTROS (`fromMe:false`):
  probar desde otro número, no desde el propio vinculado.


---

## 22. OpenWA: whatsapp-web.js rompe el media → cambiar a baileys

**Problema:**
Con OpenWA en el motor `whatsapp-web.js`, enviar **texto** funcionaba pero enviar
**imágenes** (para mandar cámaras de Home Assistant a WhatsApp) fallaba con
`500 Internal server error`. El objetivo del usuario era controlar el NAS y
recibir domótica por WhatsApp (flujo "pide cámara → recibe foto").

**Idea del usuario:**
Usar WhatsApp (OpenWA) + n8n + el nodo Home Assistant (Camera Proxy) para el
flujo. Exigir el error real y no adivinar.

**Proceso de solución:**
1. Se aisló el fallo probando la API directamente (no solo n8n).
2. `docker logs --tail 300 openwa | grep -iE "error|media"` reveló el error real:
   `Data passed to getter must include an id property (it's how we memoize) but
   got undefined` en `Client.sendMessage → sendMediaMessage → sendImage`. Es un
   bug de `whatsapp-web.js` con la versión actual de WhatsApp Web (OpenWA pineaba
   una `2.3000...-alpha`).
3. Se comprobó la matriz: texto a otro número → llega; imagen a otro número →
   falla; imagen al propio número → falla. Conclusión: el media está roto en
   wweb.js, no era el destino.
4. Fix: `ENGINE_TYPE=baileys` + `svc recreate openwa` + re-escanear QR (cada
   motor guarda su sesión aparte). Con baileys, el envío de imagen base64 a un
   número real **funcionó** (`messageId` sin `_lid`).
5. Hallazgos colaterales verificados: (a) enviar media al propio número
   (self-chat) falla; usar un destino distinto. (b) `send-image` por URL externa
   se bloquea por el SSRF guard (`Destination address is not allowed`) con
   `SSRF_ALLOWED_HOSTS` restringido; usar binario/base64. (c) `svc logs` hace
   follow y OpenWA loguea ~200 rutas al arrancar → usar
   `docker logs --tail N openwa | grep ... | tail` para ver solo lo importante.

**Decisión:**
Motor por defecto `baileys` en el compose del catálogo. `whatsapp-web.js` queda
como alternativa documentada pero con el media roto. Envío de cámaras HA por
binario (no URL). Flujo `n8n-flows/pide-camara.json` con Send Image binario.

**Alternativas descartadas:**
- Quedarse en whatsapp-web.js y pinear otra versión de WA Web: frágil, depende de
  que exista un build sin el bug; baileys lo evita de raíz y es más ligero.
- Enviar la cámara por URL (HA camera proxy URL): choca con el SSRF guard; el
  binario es más simple y no expone la URL interna.

**Aprendizaje:**
- **whatsapp-web.js puede tener el media roto según la versión de WA Web**; para
  enviar imágenes fiablemente en OpenWA, usar **baileys** (además más ligero,
  mejor para el NAS de 8GB).
- **No enviarse media a uno mismo**: el self-chat con media falla. Para "que ME
  llegue la foto" hace falta un número destino distinto del vinculado (idealmente
  un número dedicado para el bot y el personal como destino).
- **El SSRF guard también afecta al envío de media por URL**, no solo a webhooks.
- **Para leer logs de OpenWA sin colgarse**, no usar `svc logs` (follow) sino
  `docker logs --tail N | grep`. Documentado en la guía §13/§14.
- Regla reforzada de toda la saga: **pedir el error exacto y aislar (API directa
  vs n8n) antes de proponer fixes**; ahorró varias vueltas.



---

## 23. Skill nueva `nas-diagnostics` — operar/diagnosticar servicios existentes

**Problema:**
El sistema de skills tenía entrada (`dotfile-skill` router), creación/arranque
(`docker-boot-order`), datos (`datasql`), secretos (`nas-runtime-secrets`), MCP
(`nas-mcp-gateway`) y evolución documental (`documentation-evolution`), pero
**no había una skill específica para diagnosticar/operar un servicio que YA
existe** cuando falla, va lento, queda `unhealthy` o el arranque escalonado se
quedó a medias. El conocimiento existía disperso en `references/diagnostic.md`
(recetas) y `docs/troubleshooting.md` (casos resueltos), pero sin un punto de
entrada que el router pudiera activar por sus triggers. Caso vivo: `tasmoadmin`
`unhealthy` en `.no-boot`.

**Idea del usuario:**
Seguir la evolución de skills del handoff `SESSION-2026-09-20`; empezar por el
hueco #1 (skill de operar/diagnosticar servicios existentes).

**Proceso de solución:**
1. Se verificó el estado real: las 6 skills + `nas-dotfiles.md` siguen el patrón
   (`description` con triggers + cuerpo que enlaza a la guía dueña) y el router
   de `dotfile-skill` no se contradice con el índice de `framework-audit.md`.
2. Se leyeron las guías dueñas candidatas (`references/diagnostic.md` y
   `docs/troubleshooting.md`) para NO duplicar contenido: la skill nueva solo
   aporta el flujo de decisión y enlaza.
3. Se creó `.kiro/skills/nas-diagnostics/SKILL.md` con: regla de arranque
   (distinguir "boot en proceso" de fallo real con `svc boot-status`), flujo de
   decisión (health → boot-status → ps → logs → doctor), tabla síntoma→receta,
   `svc` vs `agent`, reglas seguras (no `network prune`, `down/up` recrea red,
   `NAS_CLI=bash` fallback, rate limit ≠ problema del NAS) y casos abiertos.
4. Se conectó a las tres capas de índice sin duplicar: router de `dotfile-skill`
   (fila en la tabla + sección "Diagnóstico" ahora delega a la skill), índice de
   `docs/framework-audit.md`, y el overview suelto `nas-dotfiles.md`.

**Decisión:**
`nas-diagnostics` = skill de entrada para diagnosticar/operar servicios
EXISTENTES. Frontera explícita: NO crear/eliminar/reordenar (eso es
`docker-boot-order`) ni configurar bases/secretos (`datasql` /
`nas-runtime-secrets`). Las guías dueñas siguen siendo `references/diagnostic.md`
y `docs/troubleshooting.md`; la skill nunca copia su contenido.

**Alternativas descartadas:**
- Ampliar la sección "Diagnóstico" de `dotfile-skill` en vez de crear skill:
  rompía el patrón router (una skill específica por dominio) y no daba triggers
  propios para autoactivarse cuando el usuario reporta un fallo.
- Meter el flujo en `docker-boot-order`: mezcla dos intenciones opuestas (crear
  vs diagnosticar) y satura esa skill.

**Aprendizaje:**
- Una skill nueva debe conectarse a TODAS las capas de índice a la vez (router,
  framework-audit, overview suelto) o el índice queda desincronizado.
- Frontera clara en la `description` (qué NO cubre, con la skill alternativa)
  evita solapes de activación entre skills vecinas.
- El diagnóstico debe empezar por `svc boot-status`: en frío el boot tarda
  ~11–14 min y "aún no arriba" no es fallo.
