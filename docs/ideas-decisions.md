# Ideas y Decisiones — Registro de Problemas → Soluciones

> Documento vivo que captura: qué problema surgió, qué idea tuvo el usuario,
> cómo se resolvió, y qué aprendimos. Sirve como contexto para futuros LLMs
> y como historial de decisiones arquitecturales del proyecto.
>
> Formato: cada entrada es un ciclo completo de pensamiento.

---

## Índice

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
