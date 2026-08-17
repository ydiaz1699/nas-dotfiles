# Mapa de Dependencias — nas-dotfiles + DebMenux

> Cuando modificas un archivo, ¿qué otros deben actualizarse?
> Este mapa evita que se queden archivos desincronizados.

---

## Grafo de dependencias por servicio

```
$dkco/<svc>/compose.yml  (FUENTE DE VERDAD)
    │
    ├──→ agent/catalog/services/<svc>/compose.yml    (copia en catálogo)
    ├──→ agent/catalog/services/<svc>/ficha.md       (metadatos extraídos)
    ├──→ agent/catalog/services/<svc>/.env.example   (sanitizado de .env)
    ├──→ docs/services/<svc>-guide.md                (guía operativa)
    ├──→ /debmenux/scripts/services/<svc>.sh         (instalador DebMenux)
    ├──→ docker-nas/SKILL.md                         (tabla de guías)
    ├──→ docker-nas/references/nas-context.md        (skill registry table)
    ├──→ AGENTS.md                                   (tabla de servicios)
    └──→ docs/nas-manual.md                          (tabla servicios + puertos)
```

---

## Tabla de impacto: "Si modifico X, debo actualizar..."

| Si modifico... | Debo actualizar... | Automatizable |
|----------------|-------------------|:-------------:|
| **compose.yml de un servicio** | catálogo (ficha+compose), guía, SKILL.md, nas-context.md, AGENTS.md, nas-manual.md, script DebMenux | ✅ `svc catalog-sync <svc>` |
| **Mejoro un compose existente** (env_file, :rshared, labels, security) | guía del servicio (ANTES vs DESPUÉS), ficha, compose catálogo | Manual |
| **Mejoro gestión de un servicio** (ej: HA !include, nueva carpeta) | guía del servicio, estructura en README si cambia el árbol | Manual |
| **Puerto de un servicio** | compose, ficha, guía, AGENTS.md, nas-manual.md (tabla puertos), nas-context.md | Parcial (catalog-sync + manual) |
| **Red de un servicio** | compose, ficha, guía, AGENTS.md, nas-manual.md (tabla redes), nas-context.md, docker-entorno.md | Parcial |
| **Variables .env de un servicio** | .env, .env.example en catálogo, ficha (env_required), guía | ✅ `svc catalog-sync <svc>` |
| **$dkco/.env (global)** | Todos los compose que lo heredan, docker-entorno.md | Manual |
| **Labels de Homepage** | compose, homepage-guide.md (tabla de grupos) | Manual |
| **usb-automount.sh (template)** | Copiar a /usr/local/bin/, ntfy-guide.md troubleshooting | Manual |
| **lib/notifications.sh (DebMenux)** | docker/cli/lib/notifications.sh (nas-dotfiles), ntfy-guide.md | Manual |
| **SKILL.md** | nas-context.md (si cambia la tabla de guías) | Manual |
| **Creo archivo nuevo en docs/ o scripts/** | README.md (árbol de estructura), AGENTS.md si relevante | Manual |
| **Agregar servicio nuevo** | TODO lo del grafo de arriba + README.md estructura | ✅ `svc catalog-sync <svc>` + manual |
| **Eliminar servicio** | Quitar de: catálogo, SKILL.md, nas-context.md, AGENTS.md, nas-manual.md, services.json, README.md | Manual |
| **Cambiar IP del NAS** | $dkco/.env, AGENTS.md, nas-context.md, nas-manual.md, ntfy-guide.md, usb-automount.conf | Manual (grep -r "IP_VIEJA") |

---

## Archivos espejo entre repos

Archivos que existen en AMBOS repos y deben estar sincronizados:

| nas-dotfiles | DebMenux | Relación |
|---|---|---|
| `docker/cli/lib/notifications.sh` | `lib/notifications.sh` | Misma función `ntfy_send()` |
| `agent/catalog/services/<svc>/compose.yml` | `$dkco/<svc>/compose.yml` | Catálogo = copia del real |
| `docs/services/<svc>-guide.md` | — | Solo en nas-dotfiles |
| — | `scripts/services/<svc>.sh` | Solo en DebMenux |
| `AGENTS.md` | `AGENTS.md` | Independientes pero complementarios |

**Regla:** Cuando DebMenux instala un servicio (`register_to_catalog`), genera automáticamente los archivos en nas-dotfiles. Cuando nas-dotfiles detecta un compose sin script (`svc catalog-sync`), genera el placeholder en DebMenux.

---

## Dependencias por archivo clave

### compose.yml (de cualquier servicio)

```
compose.yml DEPENDE DE:
  ← $dkco/.env (SERVER_IP, TZ via env_file)
  ← .env local (secretos del servicio)
  ← Red Docker existente (docker network create)
  ← Carpetas de volúmenes creadas (mkdir -p)

compose.yml ES DEPENDENCIA DE:
  → agent/catalog/services/<svc>/compose.yml (copia)
  → agent/catalog/services/<svc>/ficha.md (extrae datos)
  → docs/services/<svc>-guide.md (documenta)
  → /debmenux/scripts/services/<svc>.sh (instala)
  → Homepage (auto-descubre via labels)
  → docker-nas/references/nas-context.md (registry)
  → AGENTS.md (tabla de servicios)
```

### AGENTS.md

```
AGENTS.md DEPENDE DE:
  ← Todos los compose.yml (tabla de servicios)
  ← docker-nas/references/nas-context.md (hechos operativos)
  ← docs/docker-entorno.md (convenciones)

AGENTS.md ES LEÍDO POR:
  → Kiro Web (inyectado automáticamente)
  → Claude Code (lee automáticamente)
  → Cursor, Codex, Gemini CLI, Aider
```

### docker-nas/references/nas-context.md

```
nas-context.md DEPENDE DE:
  ← Todos los compose.yml (registry table)
  ← docs/docker-entorno.md (reglas)
  ← docs/services/*-guide.md (lazy loading index)
  ← Progressive updates (feedback del usuario)

nas-context.md ES LEÍDO POR:
  → Kiro Web (via SKILL.md trigger)
  → Cualquier LLM que use la skill
```

### docs/docker-entorno.md

```
docker-entorno.md DEPENDE DE:
  ← $dkco/.env (variables globales)
  ← Todos los compose.yml (convenciones verificadas)
  ← Redes Docker reales (docker network ls)
  ← Errores resueltos (progressive updates)

docker-entorno.md ES DEPENDENCIA DE:
  → nas-context.md (referencia obligatoria)
  → Cualquier LLM que modifique un compose (DEBE leerlo)
```

---

## Flujo de sincronización automática

```
┌─ Trigger ─────────────────────┐
│                                │
│  compose.yml modificado        │
│         │                      │
│         ▼                      │
│  ┌─────────────────────┐      │
│  │ svc catalog-sync    │      │     ┌─ Genera automáticamente ─┐
│  │ (o hook Kiro)       │──────┼────▶│ ficha.md                 │
│  │ (o debmenu install) │      │     │ compose.yml (catálogo)   │
│  └─────────────────────┘      │     │ .env.example             │
│                                │     │ guía placeholder         │
│                                │     │ script DebMenux          │
│                                │     │ SKILL.md (tabla)         │
│                                │     │ ntfy notification        │
│                                │     └──────────────────────────┘
│                                │
│  ┌─ NO automático (manual) ─┐ │
│  │ AGENTS.md                 │ │
│  │ nas-manual.md (puertos)   │ │
│  │ docker-entorno.md         │ │
│  │ nas-context.md (registry) │ │
│  └───────────────────────────┘ │
└────────────────────────────────┘
```

---

## Checklist: ¿Terminé de verdad?

Después de cualquier cambio a un servicio, verificar:

```bash
svc catalog-sync --status
```

Si muestra ❌ en alguna columna → ejecutar `svc catalog-sync <svc>`.

Para lo que NO es automático, revisar manualmente:

- [ ] ¿AGENTS.md tiene el servicio en la tabla?
- [ ] ¿nas-manual.md tiene el puerto en la tabla?
- [ ] ¿docker-entorno.md refleja las convenciones usadas?
- [ ] ¿nas-context.md tiene el servicio en el registry?
- [ ] Si es servicio nuevo: ¿services.json de DebMenux lo tiene?

---

## Comando rápido: verificar sincronización total

```bash
# Ver estado de TODOS los servicios (auto-docs)
svc catalog-sync --status

# Buscar IP hardcodeada (debería ser 0 resultados)
grep -r "192.168.1.200" $dkco/*/compose.yml

# Buscar TZ duplicado en environment (debería ser 0)
grep -rn "TZ=America" $dkco/*/compose.yml | grep -v "^.*:#"

# Verificar que todos tienen env_file
for f in $dkco/*/compose.yml; do
  grep -qL "env_file" "$f" && echo "⚠️  Falta env_file: $f"
done
```



---

## Herramientas CLI — ¿Qué scripts están conectados a qué comandos?

> Si creaste un script, ¿se puede ejecutar? Verificar aquí.

| Script | Comando que lo invoca | Estado |
|--------|----------------------|--------|
| `docker/cli/svc.sh` | `svc` (alias en shell) | ✅ Conectado |
| `docker/cli/lib/discovery.sh` | Cargado por svc.sh | ✅ Conectado |
| `docker/cli/lib/health.sh` | `svc health` | ✅ Conectado |
| `docker/cli/lib/backup.sh` | `svc backup` | ✅ Conectado |
| `docker/cli/lib/menu.sh` | `svc menu` | ✅ Conectado |
| `docker/cli/lib/notifications.sh` | `source` manual o desde svc | ✅ Conectado |
| `docker/cli/lib/catalog-sync.sh` | `svc catalog-sync` | ❌ **NO CONECTADO** — pendiente integrar en svc.sh |

### Regla para el LLM:

**Al crear un script nuevo, SIEMPRE verificar:**
1. ¿Qué comando lo ejecuta? (¿svc X? ¿alias? ¿directo?)
2. ¿Está registrado en svc.sh (case statement) o en un alias?
3. ¿Se puede probar con `svc <comando>` desde terminal?
4. Si NO está conectado → **documentar como pendiente** y avisar al usuario
