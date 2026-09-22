# Handoff — arranque escalonado de Docker + evolución de skills

**Fecha de registro:** 2026-09-20
**Repositorio:** `ydiaz1699/nas-dotfiles`
**Estado:** arranque escalonado COMPLETO y validado en reboot real. Trabajo en curso: mejorar el sistema de skills (router + carga condicional).

Documento autocontenido. No contiene tokens, API keys, contraseñas ni contenido de `.env`.

---

## 1. Qué se logró en esta sesión (todo mergeado a `main`)

Se implementó y validó en el NAS real un **arranque escalonado de contenedores Docker** que evita el pico de I/O al reiniciar (17+ contenedores en paralelo → `%wa` ~86%, load ~9.6). Piezas, todas en `main`:

- `shell/scripts/boot-order.sh` — arranque por capas leyendo `$dkco/scripts/layers.conf`; health gates, timeout, lock, tolerancia a `unhealthy` transitorio, pausas de estabilización de CPU, salto de `.no-boot`.
- `shell/scripts/stop-order.sh` — apagado en orden INVERSO (dependientes primero, datasql al final).
- `shell/scripts/{start-all,stop-all,restart-all}.sh` — reescritos: delegan en boot/stop-order (antes bajaban solo 3 servicios).
- `shell/scripts/{layers.conf.example,find-no-extends.sh,apply-restart-policy.sh,install-boot-service.sh}`.
- `systemd/docker-boot-staged.service.template` — unidad generada con rutas reales por `install-boot-service.sh` (placeholders `{{NAS_DOTFILES}}`/`{{DOCKER_BASE}}`).
- Comandos `svc`: `no-boot`, `boot-enable`, `boot-status` (todos en bash y python; python delega a bash). Viven en `docker/cli/lib/extras.sh`, registrados en `docker/cli/svc.sh`.
- Política `on-failure:5` (NO `unless-stopped`) en `agent/catalog/_common.yml`; jobs one-shot usan `restart: no`.
- Fix causa raíz: `flowise-worker depends_on flowise: condition: service_started` (no `service_healthy`) — `service_healthy` bloqueaba `svc up` en frío.

Guía canónica: `docs/docker-boot-staged-guide.md`.
Registro de decisiones: `docs/ideas-decisions.md` entradas #18, #20, #21.
Mapa de componentes (incluye `shell/scripts/` e índice de skills): `docs/framework-audit.md`.

## 2. Validado en reboot real

Reboot en frío del 2026-09-20: `Arranque completo` con 13 servicios healthy; los 4 en `.no-boot` (`lobehub`, `spacedrive`, `tasmoadmin`, `vaultwarden`) correctamente omitidos. El arranque en frío tarda ~11-14 min a propósito (pausas + servicios lentos como flowise). NO juzgar como fallo a mitad: usar `svc boot-status` (dice EN PROCESO / TERMINADO / FALLÓ).

## 3. Configuración del NAS (contexto)

- Hardware: Dell PowerEdge T20, 2 cores, 8GB. Debian 13. IP 192.168.1.200.
- `layers.conf` en `$dkco/scripts/layers.conf`. Capas: 1=datasql; 2=homeassistant(primero, usa PostgreSQL) n8n flowise lobehub; 3=emqx esphome; 4=iobroker node-red; 5=independientes (adguard filebrowser ntfy openwa + no-boot); 6=vscode homepage.
- `NAS_CLI=python` es el DEFAULT del usuario. Los comandos del boot corren con `NAS_CLI=bash` (systemd lo fija).
- Separación estricta: código en `$NAS_DOTFILES` (versionado), datos/estado runtime en `$dkco` (layers.conf, logs, `.no-boot`) NO versionado.

## 4. Trabajo EN CURSO — evolución de skills (continuar aquí)

Problema detectado: en otra sesión se creó `openwa` sin registrarlo en `layers.conf` → el boot falló. Causa de fondo: el LLM no sabía qué skill activar ni cuándo, y cargar todas satura tokens.

Ya hecho (mergeado):
- `dotfile-skill` convertida en **skill ROUTER/entrada**: tabla "cuándo cargar cuál skill" + sección "Carga CONDICIONAL, no por categoría" (ejemplo del usuario: crear openwa con SQLite local NO carga `datasql`; solo se carga `datasql` si el servicio usa PostgreSQL/Redis).
- `svc create`/`svc clone` → `_svc_layers_reminder()`: avisa si el servicio nuevo no está en layers.conf.
- `boot-order.sh`: error de servicio faltante ahora es accionable (da el comando de arreglo).

Skills actuales en `.kiro/skills/`: `dotfile-skill` (router/entrada), `docker-boot-order`, `datasql`, `nas-runtime-secrets`, `nas-mcp-gateway`, `documentation-evolution`, y el archivo suelto `nas-dotfiles.md`.

### Ideas/pendientes para seguir mejorando las skills
- Revisar que TODAS las skills sigan el mismo patrón: `description` con triggers claros + cuerpo breve que enlaza a la guía dueña (no duplica contenido).
- Verificar que la tabla del router en `dotfile-skill` cubra todas las skills y que la carga condicional esté bien reflejada en cada caso de uso.
- Evaluar si falta alguna skill (ej. una para operar/diagnosticar servicios existentes vs crear nuevos).
- Confirmar que `framework-audit.md` (índice de skills) y el router de `dotfile-skill` no se contradigan; uno enlaza al otro, no duplican.
- El `svc scan` detecta huecos estructurales pero NO contenido semántico desactualizado de docs/skills; tenerlo en cuenta al validar.

## 5. Pendientes operativos del NAS (no de código)
- Confirmar que `openwa` quedó añadido a `layers.conf` (Capa 5) y que `svc boot-status` da TERMINADO. Fix: `sed -i '/^ntfy$/a openwa' /docker/scripts/layers.conf` + `boot-order.sh`.
- `tasmoadmin` está `unhealthy` (en `.no-boot`): revisar su healthcheck si se quiere reactivar.
- `lobehub` en `.no-boot`: tiene el mismo patrón `service_healthy` interno (rustfs) que flowise; aplicar `service_started` cuando se reactive.

## 6. Reglas de trabajo en este entorno (importante para el próximo chat)
- Los PR se "congelan" si se hace push tras crearlos, o si el usuario mergea con commits huérfanos. Patrón repetido esta sesión: mergear el PR antes de que lleguen commits posteriores → esos commits quedan fuera de `main` y hay que abrir PR nuevo con cherry-pick. Recomendación: avisar "listo para mergear PR #N" y esperar; no seguir pusheando a una rama ya mergeada.
- Abrir PRs con `gh api repos/{owner}/{repo}/pulls` (REST). Nunca `gh pr create`.
- Antes de crear/reescribir cualquier script: consultar `docs/framework-audit.md` para no desconocer lógica existente.
- Al resolver un problema nuevo: registrar entrada en `docs/ideas-decisions.md`.
