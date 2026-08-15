---
id: "homepage"
name: "Homepage"
description: "Dashboard de servicios del NAS con widgets personalizados"
image: "ghcr.io/gethomepage/homepage:latest"
category: "sistema"
port_internal: 3000
port_default: 3000
protocol: "http"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./config:/app/config"
  - "/var/run/docker.sock:/var/run/docker.sock:ro"
env_required:
  - TZ
env_optional:
  - HOMEPAGE_ALLOWED_HOSTS=*
healthcheck: "GET http://localhost:3000"
backup_critical: true
backup_paths:
  - "./config"
protected: false
docs_url: "docs/services/homepage-guide.md"
notes: "Usa Docker socket (read-only) para auto-descubrir contenedores via labels. Los servicios que quieran aparecer automáticamente deben estar en homepage_net y tener labels homepage.*. La config YAML en ./config/ se edita en caliente (no requiere reiniciar). Para servicios nativos (usb-api) usar widget customapi con IP del host."
networks:
  - homepage_net
ports:
  http: 3000
resources:
  memory_limit: "256m"
  memory_reservation: "64m"
aliases:
  - homepage
  - dashboard
  - panel
---

# Homepage

## Qué es

Dashboard web que muestra todos los servicios del NAS en una sola página.
Soporta widgets de estado, bookmarks, búsqueda, y auto-descubrimiento de
contenedores Docker via labels.

## Estructura

```
$dkco/homepage/
├── compose.yml
└── config/
    ├── services.yaml      ← Servicios y widgets
    ├── settings.yaml      ← Layout, tema, idioma
    ├── widgets.yaml       ← Widgets globales (CPU, RAM, disco, búsqueda)
    ├── docker.yaml        ← Conexión al Docker socket
    ├── bookmarks.yaml     ← Links rápidos
    ├── custom.css         ← Estilos personalizados
    └── custom.js          ← JS personalizado
```

## Redes

- `homepage_net`: Red compartida con servicios que Homepage consulta internamente

## Acceso

- URL: `http://192.168.1.200:3000`

## docs_url

docs/services/homepage-guide.md
