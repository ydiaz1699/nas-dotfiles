# Homepage — Guía Operativa

> **Puerto:** 3000  
> **Imagen:** ghcr.io/gethomepage/homepage:latest  
> **Red:** homepage_net  
> **Tipo:** Docker container

---

## Qué es

Dashboard web que muestra todos los servicios del NAS en una sola página con
widgets de estado, métricas y links rápidos.

---

## Filosofía de configuración

```
┌─────────────────────────────────────────────────────────────────┐
│  REGLA: Labels en el compose primero. services.yaml solo si     │
│         no se puede (servicios nativos o sin compose).           │
└─────────────────────────────────────────────────────────────────┘
```

### Prioridad 1: Docker labels (auto-descubrimiento)

Agregar labels `homepage.*` en el `compose.yml` de cada servicio.
Homepage los descubre automáticamente via Docker socket (read-only).

**Ventajas:**
- La config viaja con el servicio (si borras el servicio, desaparece del dashboard)
- No hay archivo centralizado que mantener sincronizado
- Un solo lugar para editar (el compose del servicio)

**Ejemplo (en cualquier compose.yml):**
```yaml
services:
  mi-servicio:
    image: ...
    labels:
      - homepage.group=Categoría
      - homepage.name=Mi Servicio
      - homepage.icon=nombre-icono
      - homepage.href=http://${SERVER_IP}:PUERTO
      - homepage.description=Descripción corta
      # Widget opcional:
      - homepage.widget.type=tipo-widget
      - homepage.widget.url=http://${SERVER_IP}:PUERTO
      - homepage.widget.username=${USER_VAR}
      - homepage.widget.password=${PASS_VAR}
```

### Prioridad 2: services.yaml (fallback)

Usar SOLO para:
- **Servicios nativos (systemd)** → no tienen compose.yml (ej: usb-api)
- **Servicios Docker sin compose en el catálogo** → temporalmente (ej: EMQX hasta que se le agreguen labels)

**Ubicación:** `$dkco/homepage/config/services.yaml`

---

## Labels disponibles

| Label | Requerido | Descripción |
|-------|-----------|-------------|
| `homepage.group` | ✅ | Categoría/grupo en el dashboard |
| `homepage.name` | ✅ | Nombre visible |
| `homepage.icon` | ✅ | Icono (ver [icons](https://gethomepage.dev/configs/services/icons/)) |
| `homepage.href` | ✅ | URL al hacer clic |
| `homepage.description` | ❌ | Texto debajo del nombre |
| `homepage.widget.type` | ❌ | Tipo de widget (métricas) |
| `homepage.widget.url` | ❌ | URL interna para el widget |
| `homepage.widget.username` | ❌ | Auth del widget |
| `homepage.widget.password` | ❌ | Auth del widget |

### Grupos configurados

| Grupo | Servicios |
|-------|-----------|
| `Redes` | AdGuard Home |
| `IoT` | ESPHome, EMQX |
| `Archivos` | File Browser |
| `Bases de datos` | pgAdmin |
| `Sistema` | ntfy, USB Manager, Homepage |

---

## Servicios con labels (ya configurados)

| Servicio | Compose | Grupo | Widget |
|----------|---------|-------|--------|
| AdGuard Home | `$dkco/adguard/compose.yml` | Redes | adguard-home |
| ESPHome | `$dkco/esphome/compose.yml` | IoT | esphome |
| File Browser | `$dkco/filebrowser/compose.yml` | Archivos | filebrowser |
| pgAdmin | `$dkco/datasql/compose.yml` | Bases de datos | — |
| ntfy | `$dkco/ntfy/compose.yml` | Sistema | — |

## Servicios en services.yaml (sin compose)

| Servicio | Tipo | Grupo | Widget |
|----------|------|-------|--------|
| USB Manager | systemd nativo | Sistema | customapi |
| EMQX | Docker (sin labels aún) | IoT | emqx |

---

## Agregar un nuevo servicio al dashboard

### Si es Docker (tiene compose.yml):

```bash
# Agregar labels al compose.yml del servicio
nano $dkco/MI_SERVICIO/compose.yml
```

Agregar dentro del servicio principal:
```yaml
    labels:
      - homepage.group=MiGrupo
      - homepage.name=Mi Servicio
      - homepage.icon=icono
      - homepage.href=http://${SERVER_IP}:PUERTO
      - homepage.description=Lo que hace
```

Recrear el contenedor para que tome las labels:
```bash
svc recreate MI_SERVICIO
```

> **No necesitas tocar services.yaml ni reiniciar Homepage.**

### Si es servicio nativo (systemd):

Editar `$dkco/homepage/config/services.yaml` y agregar:

```yaml
- MiGrupo:
    - Mi Servicio:
        icon: icono
        href: http://192.168.1.200:PUERTO
        description: Lo que hace
        widget:
          type: customapi
          url: http://192.168.1.200:PUERTO/api/endpoint
          mappings:
            - field: campo_json
              label: Etiqueta
              format: number
```

> Homepage lee los YAML en caliente — no necesita reiniciar.

---

## Estructura de archivos

```
$dkco/homepage/
├── compose.yml                 ← Docker compose
└── config/
    ├── services.yaml           ← SOLO servicios sin compose (nativos)
    ├── settings.yaml           ← Layout, tema, idioma
    ├── widgets.yaml            ← Barra superior (CPU, RAM, disco)
    ├── docker.yaml             ← Conexión al Docker socket
    ├── bookmarks.yaml          ← Links rápidos
    ├── custom.css              ← Estilos
    └── custom.js               ← JS custom
```

---

## Widgets globales (barra superior)

En `$dkco/homepage/config/widgets.yaml`:

```yaml
- resources:
    cpu: true
    memory: true
    disk: /
    label: NAS

- search:
    provider: duckduckgo
    target: _blank

- datetime:
    text_size: xl
    format:
      dateStyle: short
      timeStyle: short
      hour12: false
```

---

## Docker socket

En `$dkco/homepage/config/docker.yaml`:

```yaml
my-docker:
  socket: /var/run/docker.sock
```

Y en `compose.yml`:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

---

## Red homepage_net

Homepage necesita comunicarse con algunos servicios internamente (para widgets
que consultan APIs internas). Los servicios que expongan métricas internas
deben conectarse a `homepage_net`.

```bash
# Crear red (si no existe)
docker network create homepage_net

# Conectar un servicio existente sin reiniciar
docker network connect homepage_net NOMBRE_CONTENEDOR
```

O en el compose del servicio:
```yaml
networks:
  - homepage_net
```

---

## Troubleshooting

### Servicio no aparece en el dashboard

1. Verificar labels: `docker inspect CONTENEDOR | grep homepage`
2. Verificar que Homepage puede ver el socket: `docker.yaml` → `socket: /var/run/docker.sock`
3. Recrear contenedor: `svc recreate SERVICIO` (las labels se leen al crear)

### Widget muestra error / no carga datos

1. Verificar conectividad interna: `docker exec homepage wget -qO- http://CONTENEDOR:PUERTO/`
2. Si el servicio no está en `homepage_net`, conectarlo: `docker network connect homepage_net CONTENEDOR`
3. Para servicios nativos: el widget usa la IP del host, no nombre de contenedor

### Cambios en services.yaml no se ven

Homepage lee YAML en caliente (sin reiniciar). Si no aparece:
- Verificar sintaxis YAML válida: `python3 -c "import yaml; yaml.safe_load(open('services.yaml'))"`
- Ver logs: `svc logs homepage`

### Layout/grupos desordenados

Definir orden en `settings.yaml`:
```yaml
layout:
  Redes:
    style: row
    columns: 2
  IoT:
    style: row
    columns: 2
```

Los grupos que no están en `layout` aparecen al final en orden alfabético.
