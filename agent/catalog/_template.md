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
healthcheck: "curl -f http://localhost:PORT/health"
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "https://enlace-a-docs-oficiales"
notes: ""
---

# Nombre del Servicio

## Qué es

(Descripción breve de qué hace y por qué es útil)

## Configuración importante

- VARIABLE: para qué sirve y cómo configurarla

## Volúmenes y datos

- `./data/` — qué almacena aquí (base de datos, config, uploads, etc.)

## Notas

- Requisitos especiales (RAM mínima, GPU, etc.)
- Servicios dependientes (necesita PostgreSQL, Redis, etc.)
- Advertencias de seguridad
