# PLAN: Migrar a `extends` con `_common.yml`

> **Fecha:** 2026-08-17
> **Estado:** En implementación
> **Decisión:** #16 en ideas-decisions.md
> **Rollback:** Si algo falla, volver al estado con anchors dentro de cada compose

---

## Qué se va a hacer

Crear `$dkco/_common.yml` con los defaults que hoy se repiten en cada compose
(resources, security, logging, healthcheck). Los servicios usarán `extends:` para
heredar y solo sobreescribirán lo que necesiten.

## Rutas relativas: catálogo versus NAS

El mismo compose tiene dos ubicaciones posibles y, por tanto, dos rutas válidas:

| Contexto | Archivo del servicio | `_common.yml` | Ruta `extends.file` |
|----------|----------------------|---------------|---------------------|
| Catálogo del repositorio | `agent/catalog/services/<svc>/compose.yml` | `agent/catalog/_common.yml` | `../../_common.yml` |
| NAS desplegado | `$dkco/<svc>/compose.yml` | `$dkco/_common.yml` | `../_common.yml` |

El catálogo conserva la versión portable para su propia estructura. Al copiar desde
el catálogo al NAS, el instalador debe transformar `../../_common.yml` en
`../_common.yml`. En el sentido inverso, `catalog-sync`, `export_service` y la
integración de DebMenux transforman `../_common.yml` en `../../_common.yml`.
Nunca se debe copiar el compose literalmente entre ambos contextos.

## Estado ANTES (actual — para rollback)

Cada compose tiene sus propios anchors:

```yaml
# $dkco/emqx/compose.yml (ANTES)
x-resource-defaults: &resource-defaults
  deploy:
    resources:
      limits:
        memory: 1g
      reservations:
        memory: 256m
x-security-defaults: &security-defaults
  security_opt:
    - no-new-privileges:true
  ulimits:
    nofile: {soft: 1048576, hard: 1048576}
x-logging-defaults: &logging-defaults
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

services:
  emqx:
    <<: [*security-defaults, *resource-defaults]
    logging: *logging-defaults
    ...
```

## Estado DESPUÉS (propuesto)

Un solo `_common.yml` global + extends en cada compose:

```yaml
# $dkco/_common.yml (NUEVO — único archivo global)
services:
  _defaults:
    restart: unless-stopped
    security_opt: [no-new-privileges:true]
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          memory: 512m
        reservations:
          memory: 128m
```

```yaml
# agent/catalog/services/emqx/compose.yml (catálogo)
services:
  emqx:
    extends:
      file: ../../_common.yml
      service: _defaults
    image: emqx/emqx:5.8.3
    deploy:
      resources:
        limits:
          memory: 1g       # ← sobreescribe solo esto (deep merge)
    ...
```

Al desplegar este archivo en `$dkco/emqx/compose.yml`, la ruta queda:

```yaml
extends:
  file: ../_common.yml
  service: _defaults
```

## Archivos que se modifican

| Archivo | Cambio | Rollback |
|---------|--------|----------|
| `agent/catalog/_common.yml` | **NUEVO** — defaults del catálogo, se copia a `$dkco/_common.yml` | Eliminar en rollback |
| `agent/catalog/services/emqx/compose.yml` | Migrar a extends con ruta de catálogo `../../_common.yml` (piloto) | Revertir git |
| `docker/cli/lib/catalog-sync.sh` | Transformar `../_common.yml` ↔ `../../_common.yml` al sincronizar | Revertir git |
| `agent/tools/discovery_tools.py` | Transformar la ruta al exportar desde el NAS | Revertir git |
| `DebMenux-/lib/integration.sh` | Transformar la ruta al registrar un compose en el catálogo | Revertir git |
| `docs/ideas-decisions.md` | Entrada #16 | — |

## Plan de ejecución

1. ✅ Documentar este plan (este archivo)
2. Crear `$dkco/_common.yml` desde `agent/catalog/_common.yml`
3. Migrar SOLO emqx como piloto (un servicio), conservando `db_net` y `ulimits`
4. Verificar rutas: `../../_common.yml` en catálogo y `../_common.yml` en NAS
5. Verificar con `docker compose config` en el NAS que resuelve correctamente
6. Si funciona → documentar en ideas-decisions.md #16
7. Si NO funciona → restaurar el snapshot y revertir la migración

## Procedimiento seguro en el NAS

Antes de reemplazar el compose real:

```bash
dk emqx
svc snapshot emqx
```

Después de copiar el compose corregido y confirmar que `$dkco/_common.yml` existe:

```bash
dk emqx
svc recreate emqx
svc health
```

Si `extends` falla, el rollback devuelve el compose y el `.env` del snapshot:

```bash
dk emqx
svc rollback emqx
svc health
```

El error anterior `open /_common.yml: no such file or directory` ocurre cuando el
compose desplegado usa `../../_common.yml`: desde `/docker/emqx` esa ruta sube dos
niveles y busca `/_common.yml` en la raíz del sistema. La ruta correcta en el NAS
es `../_common.yml`, que resuelve a `$dkco/_common.yml`.

## Cómo revertir si falla

```bash
# Opción 1: revertir solo emqx
nasfk
git checkout -- agent/catalog/services/emqx/compose.yml

# Opción 2: revertir todo (incluye _common.yml y _compose_base.md)
git log --oneline -5          # encontrar commit anterior
git revert <commit>           # o git reset --hard <commit> si no se pusheó

# Opción 3: en el NAS real, si ya se aplicó
dk emqx
# El compose viejo está en el snapshot:
svc rollback emqx             # restaura desde el último snapshot
```

## Servicios y sus resources (para referencia)

| Servicio | Memory limit | Memory reservation | CPU | Notas |
|----------|:------------:|:-----------------:|:---:|-------|
| _defaults | 512m | 128m | — | Base para todos |
| emqx | 1g | 256m | — | Broker MQTT, ulimits nofile |
| datasql (postgres) | 2g | 512m | 2 | Base de datos |
| datasql (pgadmin) | 512m | 128m | 1 | — |
| datasql (redis) | 256m | 64m | 0.5 | — |
| homepage | 256m | — | 0.5 | Dashboard |
| ntfy | 256m | 64m | 0.5 | Notificaciones |
| filebrowser | 256m | — | 0.5 | Archivos |
| esphome | — | — | — | host mode, sin limits |
| homeassistant | — | — | — | host mode, privileged |
| node-red | — | — | — | Sin limits definidos |

## Reglas de extends (deep merge)

- `extends` hace merge profundo: solo sobreescribes lo que necesitas
- Lo que NO declaras en el compose del servicio → se hereda de _common
- Si declaras `deploy.resources.limits.memory: 1g` → solo cambia memory,
  conserva `reservations` del default
- `security_opt`, `logging`, `restart` se heredan sin repetir
- `ulimits` es específico de EMQX → solo se pone ahí (no en _common)

## Nota sobre compatibilidad

- `extends` requiere Docker Compose v2 (ya instalado en el NAS)
- `extends` con `file:` externo funciona desde Compose v2.17+
- El NAS tiene Docker Engine + Compose v2 → compatible
