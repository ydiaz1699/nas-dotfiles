---
id: "_compose_base"
type: "meta"
version: "1.1"
description: "Template base de compose para todos los servicios del NAS"
---

# Compose Base — Defaults reutilizables

Este archivo documenta la estructura estándar de compose. Los defaults compartidos
(restart, seguridad, logging y recursos) viven en `$dkco/_common.yml` y se heredan
con `extends`. Los anchors YAML locales son una técnica legacy; no deben declararse
como requisito para servicios nuevos.

## Estructura de directorio

```
/docker/<servicio>/
├── compose.yml             ← nombre obligatorio
├── .env                    ← permisos 600
└── data/
    └── ...                 ← datos persistentes del servicio
```

## Formato legacy (anchors YAML)

Estos anchors pertenecen al formato anterior. No son obligatorios para servicios
nuevos: los defaults actuales se heredan desde `$dkco/_common.yml` con `extends`.

```yaml
# ── OPCIONAL: x-common-env ─────────────────────────────────────────────────
# Solo necesario si el servicio NO usa env_file: [../.env, .env]
# Si ya tiene env_file apuntando al global → TZ se hereda automáticamente
# y este anchor es REDUNDANTE. No usar en ese caso.
#
# Usar cuando:
#   - El servicio no soporta env_file (raro)
#   - Quieres inyectar variables compartidas distintas a TZ (ej: PUID, PGID)
#   - Stack multi-servicio donde quieres DRY sin repetir en cada bloque
#
x-common-env: &common-env
  TZ: ${TZ}
x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 40s
x-security-defaults: &security-defaults
  security_opt:
    - no-new-privileges:true
x-logging-defaults: &logging-defaults
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
x-resource-defaults: &resource-defaults
  deploy:
    resources:
      limits:
        memory: 512m
      reservations:
        memory: 128m
```

## Herencia actual con `extends`

En el NAS, el compose debe usar:

```yaml
services:
  nombre:
    extends:
      file: ../_common.yml
      service: _defaults
    env_file:
      - ../.env
      - .env
    labels:
      - homepage.group=Grupo
      - homepage.name=Nombre
      - homepage.href=http://${SERVER_IP}:8100
```

En el catálogo la ruta es `../../_common.yml`; el pipeline la convierte a
`../_common.yml` al desplegar. Cada servicio debe declarar su healthcheck,
volúmenes, puertos y redes. Si usa PostgreSQL o Redis, leer DataSQL y conectar
por `db_net` sin exponer puertos.

## Uso legacy en el servicio

```yaml
services:
  nombre:
    image: imagen:tag
    container_name: nombre
    restart: unless-stopped
    <<: [*security-defaults, *resource-defaults]
    env_file:
      - ../.env          # ← global: SERVER_IP, TZ (SIEMPRE)
      - .env             # ← local: secretos del servicio
    environment:
      # Solo variables específicas del servicio (NO TZ, ya viene del global)
      VARIABLE_PROPIA: valor
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "..."]
    logging: *logging-defaults
    volumes:
      - ./data:/path/interno
    ports:
      - "${PUERTO_EXTERNO}:puerto_interno"
```

> **Regla:** `env_file: [../.env, .env]` reemplaza a `<<: *common-env`.
> Si un compose tiene `env_file` apuntando al global, NO agregar
> `<<: *common-env` en environment (es redundante).

## Variaciones por servicio

### Servicios con alta concurrencia (brokers, proxies)

Agregar ulimits al security block:

```yaml
x-security-defaults: &security-defaults
  security_opt:
    - no-new-privileges:true
  ulimits:
    nofile:
      soft: 1048576
      hard: 1048576
```

### Servicios con múltiples puertos

Usar anchor de puertos:

```yaml
x-common-ports: &common-ports
  - "${PORT_A}:interno_a"
  - "${PORT_B}:interno_b"
  - "127.0.0.1:${PORT_ADMIN}:interno_admin"

services:
  nombre:
    ports: *common-ports
```

### Servicios pesados (bases de datos, media)

Ajustar recursos:

```yaml
x-resource-defaults: &resource-defaults
  deploy:
    resources:
      limits:
        memory: 2g
      reservations:
        memory: 512m
```

### Servicios con dashboard admin

**Regla por defecto: bind a localhost.**

```yaml
ports:
  - "127.0.0.1:${PORT_DASHBOARD}:puerto_interno"
```

**Excepción documentada:** si el dashboard necesita accederse desde la LAN
(ej. panel de administración de uso frecuente, como el de EMQX), se puede
exponer sin bind a localhost — pero esta decisión:

1. Debe ser explícita, no accidental (en `create_service()`: pasar
   `is_dashboard=True, expose_lan=True`)
2. Debe documentarse en la ficha de catálogo del servicio (`notes:`) y en
   su `README.md`, indicando por qué se optó por LAN en vez de localhost
3. Idealmente va detrás de reverse proxy con auth si se expone más allá
   de la LAN local (fuera del NAS)

```yaml
# Excepción: dashboard expuesto en LAN, documentado en notes/README
ports:
  - "${PORT_DASHBOARD}:puerto_interno"
```

`validate_compose()` advierte (no bloquea) cuando detecta un puerto de
dashboard sin bind a `127.0.0.1`, para forzar la revisión de esta decisión.

## .env base

El `.env` local del servicio contiene SOLO secretos. TZ y SERVER_IP vienen del global (`$dkco/.env`).

```bash
# $dkco/.env (global — compartido por todos los servicios)
SERVER_IP=192.168.1.200
TZ=America/La_Paz
```

```bash
# $dkco/<servicio>/.env (local — solo secretos)
MI_PASSWORD=__pega_aqui__
API_KEY=__pega_aqui__
```

> **NUNCA** poner TZ en el .env local — ya viene del global via `env_file: [../.env, .env]`.

### Generación de secretos

Para variables sensibles, usar placeholders `__pega_aqui__` y generar con:

```bash
SECRET=$(openssl rand -base64 18 | tr -d '/+=')
sed -i "0,/__pega_aqui__/s//${SECRET}/" "$dkco/<servicio>/.env"
chmod 600 "$dkco/<servicio>/.env"
```

## Redes

Las redes disponibles en el NAS:

| Red | Uso |
|-----|-----|
| `iot_net` | Dispositivos IoT (MQTT, ESPHome, HA, Node-RED) |
| `db_net` | Acceso a bases de datos internas |
| `proxy` | Servicios expuestos via reverse proxy (cuando se habilite) |

Declarar como externas:

```yaml
networks:
  iot_net:
    external: true
```

## Reglas del agente

Cuando el agente genera un compose:

1. SIEMPRE incluir todos los anchors base de este template
2. SIEMPRE referenciar `*security-defaults` y `*resource-defaults` en el servicio
3. SIEMPRE incluir healthcheck con `*healthcheck-defaults`
4. SIEMPRE incluir `*logging-defaults`
5. SIEMPRE poner variables sensibles en `.env`, nunca inline
6. Ajustar `memory` en `*resource-defaults` según el servicio
7. Dashboards: bind a localhost por defecto; exponer en LAN solo con
   decisión explícita y documentada (ver sección "Servicios con dashboard admin")
8. Validar con `svc config <servicio>` (o `docker compose config`) antes de levantar
9. El merge de anchors `<<: [*a, *b]` funciona en YAML puro pero
   validar porque Docker Compose puede ser más estricto
