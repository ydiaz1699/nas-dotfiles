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
# $dkco/emqx/compose.yml (DESPUÉS — sin anchors repetidos)
services:
  emqx:
    extends:
      file: ../_common.yml
      service: _defaults
    image: emqx/emqx:5.8.3
    deploy:
      resources:
        limits:
          memory: 1g       # ← sobreescribe solo esto (deep merge)
    ...
```

## Archivos que se modifican

| Archivo | Cambio | Rollback |
|---------|--------|----------|
| `$dkco/_common.yml` | **NUEVO** — crear | Eliminar |
| `agent/catalog/_compose_base.md` | Documentar extends como estándar | Revertir git |
| `agent/catalog/services/emqx/compose.yml` | Migrar a extends (piloto) | Revertir git |
| `docs/ideas-decisions.md` | Entrada #16 | — |

## Plan de ejecución

1. ✅ Documentar este plan (este archivo)
2. Crear `$dkco/_common.yml` (template en el catálogo)
3. Migrar SOLO emqx como piloto (un servicio)
4. Verificar con `docker compose config` que resuelve correctamente
5. Si funciona → documentar en ideas-decisions.md #16
6. Si NO funciona → revertir con `git checkout -- agent/catalog/services/emqx/`

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
