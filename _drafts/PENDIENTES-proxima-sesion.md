# Pendientes para próxima sesión

> Contexto: sesión larga del 2026-08-15/16 donde se implementó ntfy, usb-api,
> Homepage, HA, pipeline auto-docs, skill 2.0, AGENTS.md, dependency-map.
> Todo lo de abajo quedó pendiente.

---

## 1. Servicios sin documentación completa

Estado actual (`svc catalog-sync --status`):

| Servicio | Falta |
|----------|-------|
| **n8n** | ficha ❌, guía ❌, DebMenux script ❌ |
| **vaultwarden** | ficha ❌, guía ❌, DebMenux script ❌, Homepage labels ❌ |
| **emqx** | guía ❌ (tiene ficha y compose) |
| **esphome** | guía ❌, DebMenux script ❌ |
| **datasql** | DebMenux script ❌ |
| **node-red** | DebMenux script ❌ |
| **homepage** | DebMenux script ❌ |

**Acción:** Ejecutar `NAS_CLI=bash svc catalog-sync` para generar todo lo automático.
Después completar manualmente guías y scripts DebMenux de los servicios importantes.

---

## 2. catalog-sync en Python CLI

**Problema:** `catalog-sync` solo está en bash CLI (`svc.sh`). El usuario usa
`NAS_CLI=python` por defecto. Resultado: `svc catalog-sync` da error.

**Workaround actual:** `NAS_CLI=bash svc catalog-sync --status`

**Solución:** Agregar comando `catalog-sync` a `svc_py/` (Python CLI con Typer).
Puede ser un wrapper que invoca el bash script o reimplementación en Python.

**Archivos a modificar:**
- `svc_py/__init__.py` o `svc_py/main.py` — agregar comando Typer
- Decidir: ¿wrapper (`subprocess.run(svc.sh catalog-sync)`) o reimplementar?

---

## 3. Dual CLI (bash vs Python) — documentar en dependency-map

**Ya documentado:** El dependency-map ahora tiene sección de arquitectura dual
con tabla de qué comandos están en cuál CLI.

**Pendiente:** Decidir estrategia a futuro:
- ¿Todos los comandos nuevos van a ambos CLIs?
- ¿O el Python CLI es la versión "bonita" y el bash la "completa"?
- ¿Los comandos que solo existen en bash deberían tener un passthrough en Python?

---

## 4. Guías de servicios importantes que faltan

### emqx-guide.md
- Ya tiene ficha completa y compose con anchors
- La guía debería documentar: setup inicial, temas MQTT, ACLs, clustering (si aplica)
- Referencia: `agent/catalog/services/emqx/ficha.md` ya tiene mucho detalle

### esphome-guide.md
- Cómo flashear ESP32 desde el NAS
- Conexión con EMQX
- Configuración de dispositivos

---

## 5. _drafts/ que ya se pueden limpiar

| Archivo | Estado | Acción |
|---------|--------|--------|
| `PLAN-ntfy-usb-api.md` | ✅ Implementado completamente | Eliminar o archivar |
| `Skills_2.0.md` | ✅ Ideas extraídas y aplicadas | Eliminar o archivar |

---

## 6. Correcciones pendientes al catálogo (de learnings anteriores)

- [ ] datasql/ficha.md: quitar PGDATA de env_required
- [ ] datasql/compose.yml: quitar ports "5432:5432" de postgres
- [ ] Regenerar catalog.json con `python3 -m agent.catalog._index`
- [ ] Crear $dkco/.env global (¿ya existe? verificar)

---

## 7. Homepage labels faltantes

| Servicio | Tiene labels | Acción |
|----------|:------------:|--------|
| vaultwarden | ❌ | Agregar al compose |
| homepage | ❌ | No necesita (es el propio dashboard) |

---

## 8. Verificaciones rápidas para empezar la próxima sesión

```bash
# Estado de docs
NAS_CLI=bash svc catalog-sync --status

# IP hardcodeada (debería ser 0)
grep -r "192.168.1.200" $dkco/*/compose.yml

# TZ duplicado (debería ser 0)
grep -rn "TZ=America" $dkco/*/compose.yml | grep "environment"

# env_file faltante
for f in $dkco/*/compose.yml; do
  grep -qL "env_file" "$f" && echo "⚠️  Falta env_file: $f"
done

# Servicios sin labels Homepage
for f in $dkco/*/compose.yml; do
  grep -qL "homepage\." "$f" && echo "⚠️  Sin labels: $f"
done
```

---

## Cómo retomar sin contexto

1. Leer `AGENTS.md` (se inyecta automáticamente en Kiro)
2. Si la skill se activa: leer `docker-nas/references/nas-context.md`
3. Antes de tocar compose: leer `docs/docker-entorno.md`
4. Para saber qué actualizar: leer `docs/dependency-map.md`
5. Para entender decisiones pasadas: leer `docs/ideas-decisions.md`
6. Para estado de docs: `NAS_CLI=bash svc catalog-sync --status`
