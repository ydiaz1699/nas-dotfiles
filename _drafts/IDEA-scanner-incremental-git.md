# IDEA: Scanner Incremental basado en Git

> Propuesta del usuario para hacer el project scanner inteligente:
> usar git diff para detectar solo lo que cambió, no releer todo cada vez.

---

## Problema que resuelve

Un scanner que lee TODO el proyecto cada vez:
- Satura el contexto del LLM (muchos tokens)
- Es lento
- Repite trabajo (archivos que no cambiaron siguen igual)

## Idea del usuario

Usar `git` como detector de cambios:
- Primera vez: escanea TODO → genera un mapa base (snapshot)
- Siguientes veces: `git diff` detecta solo lo que cambió → procesa solo eso
- El scanner ya SABE el estado anterior y solo ve los deltas

## Cómo funcionaría

```
┌─────────────────────────────────────────────────────────────────┐
│                     Scanner Incremental                           │
│                                                                   │
│  1ª ejecución (mapeo completo):                                  │
│     git ls-files → leer cada archivo → clasificar → generar      │
│     snapshot (JSON/YAML con: tipo, conexiones, estado)            │
│     Guardar en: agent/cache/project-snapshot.json                 │
│                                                                   │
│  Ejecuciones siguientes (incremental):                           │
│     git diff --name-only HEAD~1          (o desde última fecha)  │
│     → solo los archivos que cambiaron                            │
│     → para cada archivo modificado:                              │
│         - ¿qué tipo es? (compose, script, doc, plugin)           │
│         - ¿qué conecta con? (dependency-map rules)               │
│         - ¿los archivos conectados están actualizados?            │
│     → generar reporte de inconsistencias                         │
│                                                                   │
│  Resultado: reporte CORTO que dice qué falta actualizar          │
└─────────────────────────────────────────────────────────────────┘
```

## Ejemplo real (lo que pasó hoy)

```bash
# Alguien modificó homeassistant/compose.yml (agregó env_file)
$ git diff --name-only HEAD~1
agent/catalog/services/homeassistant/compose.yml

# Scanner detecta:
#   Archivo: compose.yml de homeassistant
#   Tipo: compose de servicio
#   Reglas (de dependency-map grafo A):
#     → ¿La guía refleja el compose actual?
#     → ¿La ficha tiene los mismos env_required?
#     → ¿AGENTS.md tiene el servicio?
#     → ¿nas-context.md está actualizado?
#
# Resultado:
#   ⚠️  docs/services/homeassistant-guide.md → compose section desactualizada
#   ✅  agent/catalog/services/homeassistant/ficha.md → OK
#   ✅  AGENTS.md → tiene el servicio
```

## Componentes del scanner

### 1. Detector de cambios (git-based)

```bash
# Qué cambió desde el último scan (o desde ayer, o último commit)
git diff --name-only HEAD~N
git diff --name-only --since="yesterday"
git log --oneline --name-only --since="2026-08-16"

# Archivos nuevos (no trackeados)
git ls-files --others --exclude-standard
```

### 2. Clasificador de archivos

Para cada archivo modificado, identificar qué tipo es:

| Patrón del path | Tipo | Reglas a verificar |
|-----------------|------|-------------------|
| `$dkco/*/compose.yml` | Servicio Docker | dependency-map grafo A |
| `docker/cli/lib/*.sh` | Script svc | dependency-map grafo B |
| `shell/lib/*.sh` | Módulo shell | dependency-map grafo C |
| `agent/plugins/*.py` | Plugin agente | dependency-map grafo D |
| `agent/tools/*.py` | Tool agente | dependency-map grafo E |
| `docs/services/*-guide.md` | Guía servicio | Verificar vs compose real |
| `agent/catalog/services/*/ficha.md` | Ficha catálogo | Verificar vs compose real |
| `/debmenux/scripts/services/*.sh` | Script DebMenux | dependency-map grafo G |
| `/debmenux/templates/*` | Template | dependency-map grafo F |

### 3. Verificador de conexiones

Para cada archivo modificado, verificar que los archivos dependientes están sincronizados:

```python
# Pseudo-código
def check_connections(modified_file):
    file_type = classify(modified_file)
    rules = dependency_map[file_type]  # qué debería estar conectado
    
    issues = []
    for dependent_file in rules.dependents:
        if not exists(dependent_file):
            issues.append(f"❌ {dependent_file} no existe")
        elif is_outdated(dependent_file, modified_file):
            issues.append(f"⚠️  {dependent_file} posiblemente desactualizado")
    
    return issues
```

### 4. Verificador de estado "outdated" (heurísticas)

¿Cómo saber si un archivo dependiente está desactualizado sin leer todo?

| Heurística | Cómo verificar |
|------------|----------------|
| Compose cambió pero guía no | `git log --since` de ambos → guía más vieja |
| Puerto cambió en compose | `grep` puerto en compose vs ficha/AGENTS |
| IP hardcodeada | `grep -r "192.168" compose` (debería ser 0) |
| env_file faltante | `grep -L "env_file" compose` |
| Labels Homepage faltantes | `grep -L "homepage\." compose` |
| Script existe pero no en svc.sh | `grep "caso)" svc.sh` vs `ls lib/*.sh` |
| Comando en bash pero no python | comparar cases de svc.sh vs comandos de svc_py |

### 5. Snapshot (estado guardado)

```json
// agent/cache/project-snapshot.json
{
  "last_scan": "2026-08-16T20:00:00Z",
  "last_commit": "e149574",
  "services": {
    "homeassistant": {
      "compose_hash": "abc123",
      "has_ficha": true,
      "has_guide": true,
      "has_debmenux": true,
      "has_homepage_labels": true,
      "has_env_file": true,
      "ports": [8123],
      "networks": ["host"]
    },
    "n8n": {
      "compose_hash": "def456",
      "has_ficha": false,
      "has_guide": false,
      "has_debmenux": false,
      "has_homepage_labels": true,
      "has_env_file": false,
      "ports": [5678],
      "networks": ["default"]
    }
  },
  "scripts": {
    "catalog-sync": {
      "file": "docker/cli/lib/catalog-sync.sh",
      "in_bash_cli": true,
      "in_python_cli": false,
      "in_completions": true,
      "in_guide": true,
      "in_agent_prompt": false
    }
  }
}
```

## Cómo lo usaría un LLM

### Al inicio de sesión:

```
1. Leer AGENTS.md (inyectado automático)
2. Si la skill se activa → leer nas-context.md
3. Ejecutar scanner incremental:
   git diff --name-only (desde último scan)
   → "3 archivos cambiaron desde tu último scan"
   → "⚠️  2 inconsistencias detectadas"
   → Mostrar reporte corto al usuario
```

### Después de un cambio:

```
LLM modifica compose.yml
   → scanner detecta: tipo=compose, servicio=X
   → verifica: ¿guía actualizada? ¿ficha? ¿AGENTS? ¿script DebMenux?
   → muestra: "Falta actualizar: guía y AGENTS.md"
```

## Dónde viviría

```
nas-dotfiles/
├── agent/
│   ├── tools/
│   │   └── project_scanner.py     ← Tool del agente (puede invocarse con agent "scan")
│   └── cache/
│       └── project-snapshot.json   ← Estado guardado del último scan
├── docker/cli/lib/
│   └── project-scan.sh            ← Versión bash (para svc project-scan)
```

## Posible invocación

```bash
# Scan completo (primera vez o forzar)
svc project-scan --full

# Scan incremental (solo cambios desde último commit/scan)
svc project-scan

# Solo ver qué cambió sin verificar conexiones
svc project-scan --changes-only

# Scan específico de un archivo
svc project-scan homeassistant/compose.yml
```

## Relación con otras herramientas

```
dependency-map.md  = REGLAS (qué debería conectar con qué)
project-scanner    = VERIFICACIÓN (¿las reglas se cumplen en la realidad?)
catalog-sync       = GENERADOR (crea lo que falta para servicios)
                     
Scanner DETECTA → Catalog-sync GENERA → Dependency-map DOCUMENTA
```

## Mejora adicional sugerida por el usuario

> "Hacer otra herramienta que mejore mi idea para que el LLM devuelva el mejor resultado"

Esto podría ser un **meta-analyzer**: antes de que el LLM actúe, el scanner le dice
exactamente qué archivos necesita leer y qué no. Así el LLM:
- No lee archivos innecesarios (ahorra tokens)
- Sabe exactamente qué está desactualizado
- Puede dar resultados precisos en vez de genéricos

```
Usuario pide: "revisa homeassistant"
   │
   ├─ Sin scanner: LLM carga TODO (guía, ficha, compose, skill...) = muchos tokens
   │
   └─ Con scanner: 
       Scanner dice: "compose cambió ayer, guía desactualizada"
       LLM solo carga: compose + guía (lo mínimo para resolver)
       = menos tokens, respuesta más precisa
```

---

## Para implementar en próxima sesión

### Prioridad 1: Versión mínima (bash)
- `git diff --name-only` + clasificador + verificador básico
- Output: reporte de inconsistencias
- Tiempo estimado: 1-2 horas

### Prioridad 2: Snapshot + incremental
- Guardar estado en JSON
- Solo procesar deltas
- Tiempo estimado: 1 hora adicional

### Prioridad 3: Integración con LLM
- El scanner alimenta al LLM con contexto preciso
- "Lee solo estos 3 archivos, ignora el resto"
- Tiempo estimado: diseño + implementación
