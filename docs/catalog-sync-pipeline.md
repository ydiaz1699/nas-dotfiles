# Pipeline de Auto-Documentación en Cascada

> El pipeline detecta y genera artefactos faltantes. La experiencia runtime y las
> correcciones manuales deben alimentar la guía dueña mediante la skill de
> evolución documental; la existencia de archivos no demuestra sincronización semántica.

---

## Problema que resuelve

Antes:
```
Crear servicio → ¿ficha? ¿guía? ¿skill? ¿DebMenux? → TODO MANUAL → se olvida
```

Ahora:
```
Nuevo compose.yml
    │
    ├─→ ficha.md (catálogo del agente)
    ├─→ compose.yml (copia en catálogo)
    ├─→ .env.example (sanitizado)
    ├─→ guía placeholder (docs/services/)
    ├─→ script DebMenux placeholder (scripts/services/)
    ├─→ SKILL.md actualizado (tabla de guías)
    └─→ Notificación ntfy (topic: docker)
```

---

## Tres puntos de entrada

El pipeline se puede disparar desde tres lugares distintos. Todos generan lo mismo.

### 1. Desde el NAS: `svc catalog-sync`

```bash
# Sincronizar TODOS los servicios (detecta lo que falta)
svc catalog-sync

# Sincronizar uno específico
svc catalog-sync emqx

# Ver qué haría sin ejecutar
svc catalog-sync --dry-run

# Ver estado de documentación de todos los servicios
svc catalog-sync --status
```

**Cuándo usarlo:**
- Después de crear un servicio manualmente (sin DebMenux)
- Para verificar que todo está documentado (`--status`)
- Después de restaurar desde backup o migrar servicios

**Ubicación:** `$NAS_DOTFILES/docker/cli/lib/catalog-sync.sh`

### 2. Desde DebMenux: `debmenu install <svc>`

Al instalar un servicio con DebMenux, `register_to_catalog()` se ejecuta
automáticamente al final de cada `install_service()` y genera:

- ✅ ficha.md
- ✅ compose.yml (copia)
- ✅ .env.example (sanitizado)
- ✅ guía placeholder
- ✅ notificación ntfy

**Cuándo se dispara:** Automático al final de cada instalación (si la integración
con nas-dotfiles está habilitada via `debmenux.conf`).

**Ubicación:** `/debmenux/lib/integration.sh`

**Requisito:** Archivo de integración en alguna de estas rutas:
```
/etc/debmenux/debmenux.conf
~/.config/debmenux/debmenux.conf
$DEBMENUX_CONF (variable de entorno)
```

Contenido mínimo:
```ini
DOTFILES_DIR=/nas-dotfiles
DOCKER_DIR=/docker
```

### 3. Desde Kiro Web: Hook automático al guardar compose.yml

Cuando trabajas en Kiro Web y guardas un `compose.yml`, el hook
`catalog-sync-on-compose` se dispara y:

1. Lee el compose guardado
2. Identifica el servicio
3. Verifica qué documentación falta
4. Genera lo que no existe (ficha, guía, .env.example)
5. Sugiere agregar Homepage labels si no los tiene
6. Actualiza SKILL.md

**Cuándo se dispara:** Automático al guardar cualquier archivo que termine en `compose.yml`

**Ubicación:** `.kiro/hooks/catalog-sync-on-compose.json`

---

## Qué se genera (detalle)

### ficha.md (catálogo del agente)

```
agent/catalog/services/<svc>/ficha.md
```

Contiene metadatos YAML frontmatter + descripción. Lo que lee el agente Python
para buscar servicios por alias, saber puertos, redes, variables.

**Se genera desde:** compose.yml (imagen, puertos, redes, variables ${}, healthcheck)

**Nunca se sobreescribe** si ya existe — la idea es que se enriquezca manualmente.

### compose.yml (copia en catálogo)

```
agent/catalog/services/<svc>/compose.yml
```

Copia el compose real al catálogo y adapta únicamente las rutas de archivos
externos que dependen de la ubicación. Para `extends`:

- NAS: `$dkco/<svc>/compose.yml` usa `../_common.yml`.
- Catálogo: `agent/catalog/services/<svc>/compose.yml` usa `../../_common.yml`.

No se debe copiar literalmente entre ambos contextos. `catalog-sync` y
`export_service` hacen la conversión NAS → catálogo; los scripts de instalación
hacen la conversión catálogo → NAS. El catálogo contiene la versión portable para
su propia estructura, no una ruta que se pueda ejecutar desde cualquier directorio.

### .env.example

```
agent/catalog/services/<svc>/.env.example
```

Copia del .env real con secretos reemplazados por `__pega_aqui__`.
Patrones detectados: `PASSWORD`, `SECRET`, `TOKEN`, `COOKIE`, `KEY`, `PASS`.

### Guía placeholder

```
docs/services/<svc>-guide.md
```

Plantilla con secciones a completar manualmente:
- Qué es
- Instalación
- Configuración
- Backup y recuperación
- Troubleshooting

**Solo se genera si NO existe.** La guía se completa con experiencia real.

### Script DebMenux placeholder

```
/debmenux/scripts/services/<svc>.sh
```

Script de instalación funcional que:
- Copia el compose.yml desde el catálogo
- Copia .env.example como .env
- Levanta el servicio
- Registra en el catálogo

**Solo se genera si DebMenux está instalado Y no existe el script.**

### SKILL.md (tabla actualizada)

```
docker-nas/SKILL.md
```

Se actualiza la tabla de "Guías de servicios disponibles" cuando se crea
una guía nueva. No se tocan otras secciones.

---

## Flujo bidireccional

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ┌─── DebMenux ───────────────┐     ┌─── nas-dotfiles ───────────┐ │
│  │                             │     │                             │ │
│  │  debmenu install X          │────▶│  agent/catalog/services/X/  │ │
│  │  scripts/services/X.sh      │     │    ficha.md                 │ │
│  │  lib/integration.sh         │     │    compose.yml              │ │
│  │    register_to_catalog()    │     │    .env.example             │ │
│  │                             │     │  docs/services/X-guide.md   │ │
│  │                             │     │  docker-nas/SKILL.md        │ │
│  │                             │     │                             │ │
│  │                             │◀────│  svc catalog-sync           │ │
│  │  (genera script placeholder │     │  docker/cli/lib/            │ │
│  │   si no existe)             │     │    catalog-sync.sh          │ │
│  └─────────────────────────────┘     └─────────────────────────────┘ │
│                                                                      │
│  ┌─── Kiro Web ───────────────────────────────────────────────────┐ │
│  │  Hook: PostFileSave compose.yml                                 │ │
│  │  → Lee compose → Genera docs faltantes → Actualiza SKILL.md    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌─── ntfy ───────────────────────────────────────────────────────┐ │
│  │  Notificación al celular: "📋 Servicio X registrado"           │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Reglas del pipeline

1. **Nunca sobreescribir documentación existente** — solo generar lo que falta
2. **Ficha y guía se generan como placeholder** — completar manualmente con experiencia real
3. **compose.yml se actualiza** si el source es más nuevo (única excepción a la regla 1)
4. **Labels de Homepage van en el compose** (no en services.yaml) — el pipeline verifica y avisa
5. **El agente siempre consulta el catálogo** — al documentar un servicio, el agente lo "aprende"
6. **Notificación ntfy** al completar (topic: docker, tags: books)

---

## Verificar estado

Para ver qué servicios tienen/faltan documentación:

```bash
svc catalog-sync --status
```

Salida ejemplo:
```
  SERVICIO         COMPOSE  FICHA    GUÍA     DEBMENU  HOMEPAGE
  ──────────────────────────────────────────────────────────────
  adguard          ✅       ✅       ❌       ✅       ✅
  datasql          ✅       ✅       ✅       ❌       ✅
  emqx             ✅       ✅       ❌       ✅       ✅
  esphome          ✅       ✅       ❌       ✅       ✅
  filebrowser      ✅       ✅       ✅       ❌       ✅
  homepage         ✅       ✅       ✅       ❌       —
  ntfy             ✅       ✅       ✅       ✅       ✅
```

Después ejecutar `svc catalog-sync` genera lo que falta.

---

## Ejemplo: Agregar un servicio nuevo completo

```bash
# 1. Crear el servicio (cualquier método)
mkdir -p $dkco/vaultwarden/data
nano $dkco/vaultwarden/compose.yml   # escribir compose
nano $dkco/vaultwarden/.env          # secretos

# 2. Levantar
dk vaultwarden && svc up vaultwarden

# 3. Generar TODA la documentación automáticamente
svc catalog-sync vaultwarden

# Resultado:
#   ✅ agent/catalog/services/vaultwarden/ficha.md
#   ✅ agent/catalog/services/vaultwarden/compose.yml
#   ✅ agent/catalog/services/vaultwarden/.env.example
#   ✅ docs/services/vaultwarden-guide.md (placeholder)
#   ✅ /debmenux/scripts/services/vaultwarden.sh (placeholder)
#   ✅ SKILL.md actualizado
#   ✅ Notificación: "📋 vaultwarden documentado"

# 4. Completar la guía con info real cuando tengas experiencia
nano $NAS_DOTFILES/docs/services/vaultwarden-guide.md
```

---

## Autoalimentación y límites reales

`catalog-sync` cubre la generación y conversión de artefactos; no sustituye la
reconciliación de conocimiento operativo. Cuando una sesión del NAS descubre un
problema o una corrección, el flujo correcto es:

```text
salida sanitizada del NAS
  → docs/services/<svc>-guide.md (fuente de conocimiento operativo)
  → agent/catalog/services/<svc>/compose.yml (si cambió la configuración)
  → ficha.md y .env.example (si cambió el contrato)
  → nas-context.md (si el aprendizaje es reutilizable)
  → skill/contrato/hook (solo si cambió el proceso)
  → project_index.py + project_scanner.py + diff check
```

El registro debe conservar síntoma, causa, comando completo sin secretos,
backup, verificación, postcondición y clasificación (`INTEGRADO`, `REEMPLAZADO`,
`RECHAZADO`, `PENDIENTE` o `BLOQUEADO`). La guía no debe guardar contraseñas,
tokens, `.env` real ni una salida completa de `svc config`.

El hook Kiro informa faltantes y drift estático, pero no ejecuta comandos runtime
del NAS. El scanner actual tampoco mantiene un ledger persistente de archivos
`processed/pending/failed` ni un productor demostrado de eventos de memoria. Por
eso esta fase se denomina **autoalimentación asistida por la skill**: el LLM
extrae el aprendizaje y propone/realiza la actualización autorizada, pero no se
debe afirmar automatización completa hasta implementar y validar el entrypoint,
el ledger y sus consumidores.

Para iniciar el siguiente servicio, conservar un handoff breve con:

```text
COMPLETADO: <servicio>
EVIDENCIA: <healthy/pong/PONG/etc., sin secretos>
CAMBIOS: <archivos y runtime>
PENDIENTE: <discrepancias o riesgos>
NO_REPETIR: <operaciones ya realizadas>
SIGUIENTE: auditar <servicio siguiente> desde guía, ficha, compose y .env.example
```

---

## Archivos del pipeline

| Archivo | Repo | Función |
|---------|------|---------|
| `docker/cli/lib/catalog-sync.sh` | nas-dotfiles | Script principal (`svc catalog-sync`) |
| `lib/integration.sh` | DebMenux | `register_to_catalog()` + cascada |
| `.kiro/hooks/catalog-sync-on-compose.json` | nas-dotfiles | Hook Kiro Web |
| `agent/catalog/_template.md` | nas-dotfiles | Template de ficha |
| `docs/catalog-sync-pipeline.md` | nas-dotfiles | Esta documentación |
