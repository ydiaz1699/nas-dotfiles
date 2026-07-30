---
id: "_rules"
type: "meta"
version: "1.1"
# ── Archivos del catálogo ──────────────────────────────────────────────────
catalog:
  compose_base: "_compose_base.md"    # Template base de compose (anchors, estructura)
  template: "_template.md"            # Template de ficha de servicio
  services_dir: "services/"           # Fichas individuales por servicio
# ── Configuración del NAS ──────────────────────────────────────────────────
nas:
  docker_base: "/docker"
  user: "aadm"
  home: "/home/aadm"
  timezone: "America/La_Paz"
# ── Reverse Proxy ──────────────────────────────────────────────────────────
reverse_proxy:
  enabled: false
  type: "none"           # Opciones: none | traefik | nginx-proxy-manager | caddy
  network: "proxy"       # Nombre de la red Docker cuando se habilite
  # Cuando habilites Traefik, cambia enabled: true y type: traefik
  # El agente automáticamente agregará servicios web a la red proxy
# ── Puertos ────────────────────────────────────────────────────────────────
ports:
  reserved: [22, 53, 80, 443]          # NUNCA asignar estos
  range_start: 8100                     # Rango libre para servicios nuevos
  range_end: 8999
  scan_command: "ss -tnlp | grep -oP ':\\K[0-9]+(?=\\s)' | sort -n | uniq"
---

# Reglas de Generación de Servicios

Estas reglas se aplican SIEMPRE que el agente genera o modifica un servicio,
sin importar si la información viene del catálogo local o de una búsqueda web.

## Estructura obligatoria de cada servicio

Cada servicio en /docker/ DEBE tener:

```
/docker/<nombre>/
├── docker-compose.yml    ← SIEMPRE este nombre (nunca compose.yml)
├── .env                  ← SIEMPRE (aunque esté vacío)
└── README.md             ← Mínimo: qué es, puerto, datos críticos
```

## Formato del docker-compose.yml

1. SIEMPRE consultar `_compose_base.md` para la estructura estándar de anchors
2. SIEMPRE usar `services:` como top-level (nunca `version:` — deprecated)
3. SIEMPRE incluir `container_name:` explícito (= nombre del directorio)
4. SIEMPRE `restart: unless-stopped`
5. SIEMPRE incluir los anchors base: `x-security-defaults`, `x-healthcheck-defaults`,
   `x-logging-defaults`, `x-resource-defaults` (ver `_compose_base.md`)
6. SIEMPRE aplicar `<<: [*security-defaults, *resource-defaults]` al servicio
7. SIEMPRE healthcheck si el servicio expone HTTP/API
8. NUNCA asignar puertos reservados (22, 53, 80, 443) como puerto externo
9. Puertos externos: usar rango 8100-8999 (verificar disponibilidad antes)
10. Volúmenes: preferir bind mounts en `./data/` sobre volumes nombrados
11. Variables sensibles → SIEMPRE en .env, NUNCA inline en el compose
12. SIEMPRE incluir `TZ=${TZ:-America/La_Paz}` en environment via `*common-env`

## Red y Proxy

- Si `reverse_proxy.enabled: false` → NO agregar configuración de red externa
- Si `reverse_proxy.enabled: true` → servicios web van a la red `proxy`
- Servicios internos (bases de datos, redis) NUNCA se exponen a la red proxy

## Seguridad

- Credenciales: generar placeholder con `# CAMBIAR:` como prefijo en .env
- Si el servicio tiene panel admin → desactivar signup/registro por defecto
- Si hay opción de deshabilitar registro público → activarla
- NUNCA exponer bases de datos al host (solo red interna Docker)
- Si el servicio necesita docker.sock → advertir en README.md

## Naming

- Directorio: nombre corto, minúsculas, sin espacios (ej: vaultwarden)
- container_name: igual al directorio
- Volúmenes bind mount: `./data/` para datos persistentes
- Si necesita múltiples directorios: `./data/`, `./config/`, `./logs/`

## Backup

- Indicar en README.md qué datos son críticos para backup
- Preferir datos en `./data/` (fácil de respaldar con svc backup)
- Base de datos: indicar comando de dump en README.md si aplica

## README.md del servicio

Formato mínimo:
```markdown
# <nombre>

<descripción en una línea>

## Acceso

- Puerto: <puerto_externo>
- URL: http://<ip>:<puerto>

## Datos críticos (backup)

- ./data/ — <qué contiene>

## Notas

- <configuración importante>
```

## Healthcheck

Formato estándar según protocolo:

```yaml
# HTTP
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:<puerto>/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s

# TCP (bases de datos, redis)
healthcheck:
  test: ["CMD", "nc", "-z", "localhost", "<puerto>"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Acciones destructivas — Confirmación obligatoria

El agente DEBE pedir confirmación antes de:
- `down` / `kill` / `rm` de cualquier servicio
- `restore` de un backup (sobreescribe datos)
- `prune` de imágenes/volúmenes
- Modificar un docker-compose.yml existente
- Eliminar archivos de backup

El agente PUEDE ejecutar sin confirmación:
- `start` / `restart` / `up`
- Leer logs, status, health
- Crear servicios nuevos (en directorio nuevo)
- Generar fichas de catálogo
- Escanear puertos / disco / red

## Servicios protegidos

Servicios que NUNCA se deben detener/eliminar sin confirmación EXPLÍCITA
del usuario (incluso si pide "detener todo"):
- Cualquier servicio marcado con `protected: true` en su ficha
- Por defecto: el propio nas-agent, reverse proxy (cuando exista)
