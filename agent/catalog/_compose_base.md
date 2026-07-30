---
id: "_compose_base"
type: "meta"
version: "1.1"
description: "Template base de compose para todos los servicios del NAS"
---

# Compose Base — Template Reutilizable

Este archivo define la **estructura estándar** de compose que TODOS los servicios
del NAS deben seguir. Cuando el agente genera o modifica un compose, DEBE aplicar
estos bloques base.

## Estructura de directorio

```
/docker/<servicio>/
├── compose.yml (o docker-compose.yml)  ← ambos nombres son válidos
├── .env                    ← permisos 600
└── data/
    └── ...                 ← datos persistentes del servicio
```

## Bloques base (anchors YAML)

Cada compose DEBE incluir estos anchors al inicio y referenciarlos en el servicio:

```yaml
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

## Uso en el servicio

```yaml
services:
  nombre:
    image: imagen:tag
    container_name: nombre
    restart: unless-stopped
    <<: [*security-defaults, *resource-defaults]
    environment:
      <<: *common-env
      # Variables específicas del servicio...
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "..."]
    logging: *logging-defaults
    volumes:
      - ./data:/path/interno
    ports:
      - "${PUERTO_EXTERNO}:puerto_interno"
```

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

Todos los `.env` DEBEN incluir como mínimo:

```bash
TZ=America/La_Paz
```

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
