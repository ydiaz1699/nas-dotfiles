# Entorno Docker del NAS — Guía de Referencia

> Cómo están organizados los servicios Docker en este NAS.
> Leer ANTES de modificar cualquier compose o sugerir cambios.
> Actualizado: 2026-08-16

---

## Estructura de directorios

```
/docker/                            ← $dkco (raíz de datos Docker)
├── .env                            ← Variables GLOBALES (SERVER_IP, TZ)
├── adguard/
│   ├── compose.yml
│   ├── .env
│   └── ...
├── datasql/
│   ├── compose.yml
│   ├── .env
│   └── data/
├── emqx/
│   ├── compose.yml
│   ├── .env
│   └── data/
├── esphome/
│   ├── compose.yml
│   ├── .env
│   └── config/
├── filebrowser/
│   ├── compose.yml
│   ├── .env
│   └── config/
├── homeassistant/
│   ├── compose.yml
│   ├── .env                        ← HOMEASSISTANT_TOKEN
│   └── data/                       ← /config dentro del contenedor
│       ├── configuration.yaml
│       ├── includes/               ← shell_commands, tvoverlay, notify
│       └── www/snapshots/          ← imágenes de cámara
├── homepage/
│   ├── compose.yml
│   └── config/                     ← services.yaml, settings.yaml, etc.
├── ntfy/
│   ├── compose.yml
│   ├── .env
│   ├── config/server.yml
│   └── data/
├── iobroker/
│   ├── compose.yml
│   ├── .env
│   └── data/                       ← /opt/iobroker dentro del contenedor
├── spacedrive/
│   └── compose.yml
└── backups/                        ← destino de svc backup
```

---

## .env Global (`$dkco/.env`)

Archivo compartido por TODOS los servicios. Contiene variables que se repiten:

```env
SERVER_IP=192.168.1.200
TZ=America/La_Paz
```

### Cómo se hereda

Cada servicio usa `env_file:` en su compose para heredar estas variables:

```yaml
env_file:
  - ../.env    # ← $dkco/.env (SERVER_IP, TZ)
  - .env       # ← secretos locales del servicio
```

**Reglas:**
- `SERVER_IP` y `TZ` viven SOLO en `$dkco/.env` — nunca duplicar en `environment:`
- El `.env` local del servicio sobreescribe al global si hay conflicto
- Secretos (passwords, tokens) van en el `.env` local — nunca en el global

### Dónde se usa `${SERVER_IP}`

- Labels de Homepage: `homepage.href=http://${SERVER_IP}:PUERTO`
- Configuraciones que necesitan la IP del NAS en labels/environment

### Servicios que ya lo usan

| Servicio | env_file: ../.env | env_file: .env | environment: TZ |
|----------|:-----------------:|:--------------:|:----------------:|
| emqx | ✅ | ✅ | ❌ (hereda) |
| ntfy | ✅ | ✅ | ❌ (hereda) |
| filebrowser | ❌ (usa .env solo) | ✅ | ❌ |
| homeassistant | ✅ | ✅ | ❌ (hereda) |
| esphome | ❌ (network_mode:host) | ✅ | ❌ |
| datasql | ✅ | ✅ | ❌ (hereda) |
| homepage | ❌ | ❌ | inline `TZ=...` |
| adguard | ❌ (macvlan) | ✅ | ❌ |

> **Meta:** Migrar todos a `env_file: [../.env, .env]` para consistencia.

---

## Convenciones de compose.yml

### Nombre del archivo

- **SIEMPRE** `compose.yml` — nunca `docker-compose.yml`

### Estructura mínima obligatoria

```yaml
services:
  nombre-servicio:
    image: imagen:tag
    container_name: nombre-servicio
    restart: unless-stopped
    env_file:
      - ../.env          # global (SERVER_IP, TZ)
      - .env             # secretos locales
    volumes:
      - ./data:/data     # (o la ruta que corresponda)
    security_opt:
      - no-new-privileges:true
    cap_drop: [ALL]
    # cap_add: [solo las necesarias]
    healthcheck:
      test: [...]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    labels:
      - homepage.group=Grupo
      - homepage.name=Nombre
      - homepage.icon=icono
      - homepage.href=http://${SERVER_IP}:PUERTO
      - homepage.description=Descripción corta
    deploy:
      resources:
        limits:
          cpus: 'X'
          memory: XM
```

### Lo que NUNCA debe estar en un compose

| ❌ NO | ✅ SÍ |
|--------|--------|
| `TZ=America/La_Paz` en `environment:` | Heredar de `../.env` via `env_file:` |
| IP hardcodeada `192.168.1.200` en labels | `${SERVER_IP}` (interpolado desde .env) |
| Puertos de DB expuestos a la LAN (`0.0.0.0:5432`) | Consumidores Docker usan `db_net`; excepción host-only documentada: `127.0.0.1:5432:5432` para Home Assistant en `network_mode: host` |
| `docker-compose.yml` como nombre | `compose.yml` |
| Sin healthcheck | Siempre agregar healthcheck |

### Seguridad y recursos (aplicar con criterio)

| Elemento | Cuándo usar | Cuándo NO usar |
|----------|-------------|----------------|
| `security_opt: [no-new-privileges:true]` | **Siempre** — no rompe nada | Solo si da error explícito |
| `healthcheck` | **Siempre** — solo monitorea, no restringe | Nunca hay razón para no ponerlo |
| `cap_drop: [ALL]` + `cap_add:` | Servicios simples y estáticos (ntfy, filebrowser, redis) | Servicios que instalan paquetes en runtime (Node-RED), necesitan red avanzada, o acceso a hardware (HA, ESPHome) |
| `deploy: resources: limits:` | Servicios ya probados donde sabes cuánto consumen | Servicios nuevos que aún no verificaste — puede causar OOM kill |

**Regla:** No aplicar `cap_drop: [ALL]` ni resource limits ciegamente a todo servicio.
Primero levantar, verificar que funciona, medir consumo con `docker stats`, y después
agregar restricciones si se necesitan.

**Servicios que SÍ toleran cap_drop:**
- ntfy, filebrowser, redis, pgadmin, homepage, postgres

**Servicios que NO deben tener cap_drop:**
- homeassistant (privileged), esphome (USB serial), node-red (npm install en runtime)

---

## Redes Docker

> Los comandos de creación de esta sección son únicamente para el bootstrap
> inicial o recuperación controlada de una instalación sin redes externas.
> Durante la operación normal se usa `svc net`; no se eliminan redes compartidas
> para reparar un servicio y nunca se ejecuta `docker network prune` como
> solución genérica.

### Creadas manualmente

| Red | Driver | Propósito | Crear con |
|-----|--------|-----------|-----------|
| `db_net` | bridge | Apps ↔ Bases de datos (interno) | `docker network create db_net` |
| `iot_net` | bridge | IoT: EMQX ↔ ESPHome ↔ HA | `docker network create iot_net` |
| `homepage_net` | bridge | Homepage ↔ servicios (widgets) | `docker network create homepage_net` |
| `adguard_macvlan_NET` | macvlan | AdGuard con IP propia (DNS:53) | Config especial (ver networking.md) |

### Creadas automáticamente por compose

| Red | Servicio |
|-----|----------|
| `filebrowser_default` | filebrowser |
| `spacedrive_default` | spacedrive |

### Reglas de uso

1. **DBs nunca se exponen a la LAN** — los consumidores Docker usan `db_net`; la única excepción host-only documentada es PostgreSQL en `127.0.0.1:5432` para Home Assistant con `network_mode: host`
2. **No usar `ipv4_address` en redes compartidas** — Docker asigna IPs dinámicas; las aplicaciones deben comunicarse mediante `container_name`/hostname
3. **Todo IoT va a `iot_net`** — EMQX, ESPHome, (futuro HA si deja de usar host)
4. **Homepage widgets internos via `homepage_net`** — ntfy conectado aquí
5. **`network_mode: host`** — solo para servicios que necesitan mDNS/descubrimiento (HA, ESPHome)
6. **macvlan** — solo para servicios que necesitan IP propia en la LAN (AdGuard DNS:53)

### Conectar un servicio a una red existente (sin recrear)

```bash
docker network connect homepage_net ntfy
docker network connect iot_net mi-servicio
```

### En el compose (persistente)

```yaml
networks:
  - iot_net
  - db_net

# Al final del archivo:
networks:
  iot_net:
    external: true
  db_net:
    external: true
```

---

## Homepage Labels

### Filosofía: Labels en compose > services.yaml

- **Servicio Docker** → labels `homepage.*` en su compose.yml (auto-descubrimiento)
- **Servicio nativo (systemd)** → `$dkco/homepage/config/services.yaml`
- Recrear contenedor para que tome labels nuevas: `svc recreate X`

### Labels estándar

```yaml
labels:
  - homepage.group=Grupo          # Categoría en el dashboard
  - homepage.name=Nombre          # Nombre visible
  - homepage.icon=icono           # Ver https://gethomepage.dev/configs/services/icons/
  - homepage.href=http://${SERVER_IP}:PUERTO
  - homepage.description=Texto corto
  # Widget opcional:
  - homepage.widget.type=tipo
  - homepage.widget.url=http://${SERVER_IP}:PUERTO
  - homepage.widget.key=${TOKEN}  # si requiere auth
```

### Grupos actuales

| Grupo | Servicios |
|-------|-----------|
| `Redes` | AdGuard Home |
| `IoT` | Home Assistant, ESPHome, EMQX |
| `Archivos` | File Browser |
| `Bases de datos` | pgAdmin |
| `Sistema` | ntfy, USB Manager |

---

## Volúmenes y datos

### Convención de montaje

```yaml
volumes:
  - ./data:/data           # Datos persistentes
  - ./config:/config       # Configuración
  - ../.env:../.env:ro     # NO — usar env_file en su lugar
```

### Casos especiales documentados

| Servicio | Mount especial | Razón |
|----------|---------------|-------|
| filebrowser | Bind `/NAS` → `/srv` con `propagation: rshared` | Mount propagation para ver USBs en tiempo real |
| homeassistant | `./data:/config` | Todo HA vive en /config |
| homeassistant | `/run/dbus:/run/dbus:ro` | Bluetooth/dbus |
| esphome | `/dev/ttyUSB0:/dev/ttyUSB0` | Acceso a USB serial (ESP32 físico) |

### Carpetas que deben existir ANTES de levantar

| Servicio | Crear con |
|----------|-----------|
| ntfy | `mkdir -p $dkco/ntfy/{config,data/cache,data/lib,data/attachments}` |
| emqx | `mkdir -p $dkco/emqx/data/{data,log}` |
| homeassistant | `mkdir -p $dkco/homeassistant/data/www/snapshots` |
| iobroker | `mkdir -p $dkco/iobroker/data` |
| homeassistant | `mkdir -p $dkco/homeassistant/data/includes` |
| datasql | `mkdir -p $dkco/datasql/data/{postgres/pgdata,postgres/backups,pgadmin,redis}` |

> **Regla:** Siempre crear carpetas ANTES de `svc up`. Docker las crea como root
> si no existen, lo que puede causar problemas de permisos.

---

## Orden de operaciones (SIEMPRE respetar)

```
1. mkdir -p $dkco/<svc>/{data,config}     ← Crear carpetas
2. Crear compose.yml + .env               ← Crear archivos
3. chmod 600 .env                         ← Aplicar permisos
4. docker network create <red>            ← Crear red (si necesaria)
5. Agregar labels homepage.* en compose   ← Homepage auto-descubrimiento
6. dk <svc> && svc up <svc>              ← Levantar
7. svc catalog-sync <svc>                ← Generar documentación
```

**NUNCA:**
- chmod antes de mkdir
- svc up antes de crear carpetas
- Crear .env después de levantar (las variables no se cargan)

---

## Notificaciones desde servicios

### Función compartida (bash)

```bash
source $dkco/cli/lib/notifications.sh
ntfy_send "topic" "título" "mensaje" "prioridad" "tags"
```

### Desde Home Assistant

| Tipo | Método | Soporta imagen |
|------|--------|:--------------:|
| Texto | `ntfy.publish` (integración oficial) | ❌ (no aún) |
| Con imagen | `shell_command` + `curl -T` | ✅ |
| TV overlay | `rest_command.tvoverlay_notify` | ✅ |

### Priority en HA vs bash

| bash/curl | HA (ntfy.publish) |
|-----------|-------------------|
| `"min"` | `1` |
| `"low"` | `2` |
| `"default"` | `3` |
| `"high"` | `4` |
| `"urgent"` | `5` |

---

## Errores comunes (lecciones de este NAS)

| Error | Causa | Solución |
|-------|-------|----------|
| `curl: cannot open '/config/www/snapshots/...'` | Carpeta no existe | `mkdir -p $dkco/homeassistant/data/www/snapshots` |
| `allowlist_external_dirs` | HA no tiene permiso al path | Usar `/config/www/` (permitido por defecto) |
| `extra keys not allowed @ data['image']` | ntfy.publish no soporta imágenes | Usar shell_command + curl -T |
| `expected int for priority` | ntfy.publish de HA usa números | Usar 1-5, no texto |
| IP hardcodeada en labels | No usa variable global | Cambiar a `${SERVER_IP}`, agregar `env_file: ../.env` |
| TZ duplicado (global + environment) | Redundancia | Quitar de `environment:`, heredar de `../.env` |
| `endpoint already exists in network` | Ya está conectado | Ignorar — no es error real |
| Compose desactualizado en catálogo | Cambios no sincronizados | `svc catalog-sync <svc>` |
| Servicio no aparece en Homepage | Labels no se aplicaron | `svc recreate <svc>` (no basta restart) |
| Mount fantasma USB | Desconexión sin desmontar | `umount -l /path && rmdir /path` |

---

## Checklist antes de modificar un servicio

- [ ] ¿Leí la guía del servicio? (`docs/services/<svc>-guide.md`)
- [ ] ¿Leí la ficha? (`agent/catalog/services/<svc>/ficha.md`)
- [ ] ¿Uso `env_file: [../.env, .env]` (no hardcodeo IP ni TZ)?
- [ ] ¿Las carpetas de volúmenes existen?
- [ ] ¿Tiene healthcheck?
- [ ] ¿Tiene labels de Homepage?
- [ ] ¿Tiene `security_opt: [no-new-privileges:true]`?
- [ ] ¿`cap_drop: [ALL]` es apropiado para ESTE servicio? (no aplicar ciegamente)
- [ ] ¿Resource limits son apropiados? (no poner si no se sabe el consumo real)
- [ ] ¿Los puertos de DBs están cerrados a la LAN? Si Home Assistant usa `network_mode: host`, documentar y limitar PostgreSQL a `127.0.0.1:5432:5432`.
- [ ] ¿Después del cambio ejecuté `svc catalog-sync <svc>`?
