---
id: "nombre-del-servicio"
name: "Nombre Legible"
description: "Descripción corta de qué hace el servicio"
image: "imagen/oficial:tag"
category: "categoria"
# Categorías: media | seguridad | productividad | monitoreo | red |
#             almacenamiento | desarrollo | base-datos | domótica | otro
port_internal: 8080
port_default: 8100
protocol: "http"
needs_proxy: true
needs_db: false
db_type: ""                  # postgres | mysql | mariadb | sqlite | redis
volumes:
  - "./data:/data"
env_required:
  - VARIABLE_REQUERIDA
env_optional:
  - VARIABLE_OPCIONAL=valor_default
healthcheck: '["CMD", "curl", "-f", "http://localhost:8080/health"]'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "https://enlace-a-docs-oficiales"
notes: ""
networks:
  - nombre_red                # ej. iot_net, db_net, proxy (si reverse_proxy.enabled)
ports:
  http: 8100                  # nombrar cada puerto expuesto, no solo el principal
resources:
  memory_limit: "512m"
  memory_reservation: "128m"
security_extra:
  ulimits: {}                 # solo si el servicio necesita alta concurrencia (ver _compose_base.md)
---

# Nombre del Servicio

## Qué es

(Descripción breve de qué hace y por qué es útil)

## Estructura

```
/docker/<nombre>/
├── compose.yml (o docker-compose.yml)
├── .env                    ← permisos 600
└── data/
    └── ...
```

## Configuración importante

- VARIABLE: para qué sirve y cómo configurarla

## Puertos

| Puerto | Protocolo | Descripción |
|--------|-----------|-------------|

## Redes

- `nombre_red`: para qué se usa

## Volúmenes y datos

- `./data/` — qué almacena aquí (base de datos, config, uploads, etc.)

## Notas

- Requisitos especiales (RAM mínima, GPU, etc.)
- Servicios dependientes (necesita PostgreSQL, Redis, etc.)
- Advertencias de seguridad
- Si el dashboard/panel admin se expone en LAN en vez de localhost,
  documentar la justificación aquí explícitamente
