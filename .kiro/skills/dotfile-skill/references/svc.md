# svc — CLI Docker referencia completa

## Archivos

```
docker/cli/
├── svc.sh            ← entrypoint
└── lib/
    ├── discovery.sh  ← detección de servicios
    ├── docker.sh     ← update-all
    ├── health.sh     ← health, lista
    ├── backup.sh     ← backup, restore
    ├── extras.sh     ← port-map, size, net, doctor, diff, watch, create, env
    ├── menu.sh       ← TUI fzf
    └── help.sh       ← ayuda
```

## Detección de servicios

Busca en `/docker/*/` estos archivos (en orden):
`compose.yml` · `compose.yaml` · `docker-compose.yml` · `docker-compose.yaml`

## CLI dual

```bash
NAS_CLI=bash    # default — usa docker/cli/svc.sh
NAS_CLI=python  # alternativo — usa svc_py/ (Rich + InquirerPy)
```

## Comandos globales (sin servicio)

| Comando | Acción |
|---------|--------|
| `svc lista` | servicios con estado ●/○ |
| `svc health` | tabla: estado, uptime, restarts |
| `svc doctor` | chequeo 6 puntos: disco, memoria, servicios, puertos, restarts, storage |
| `svc update-all` | pull + recrear todos |
| `svc port-map` | mapa global de puertos |
| `svc size` | disco por servicio |
| `svc net` | redes Docker con contenedores |
| `svc watch` | monitoreo continuo (5s refresh) |
| `svc create <nombre>` | scaffolding nuevo servicio |
| `svc menu` | TUI interactivo (fzf) |
| `svc diff <svc>` | compose disco vs resuelta |

## Comandos con servicio

| Comando | Acción |
|---------|--------|
| `svc up <svc>` | crear e iniciar (detached) |
| `svc down <svc>` | detener y eliminar |
| `svc restart <svc>` | reiniciar |
| `svc start/stop/kill <svc>` | control básico |
| `svc update <svc>` | pull + recrear |
| `svc logs <svc>` | follow, tail 200 |
| `svc ps <svc>` | contenedores |
| `svc stats <svc>` | CPU/RAM en vivo |
| `svc top <svc>` | procesos internos |
| `svc exec <svc> <cmd>` | ejecutar en contenedor |
| `svc backup <svc>` | volúmenes → tar.gz (rotación: 5) |
| `svc restore <svc>` | restaurar (fzf + confirmación) |
| `svc depends <svc>` | ver dependencias |
| `svc open <svc>` | abrir URL (auto-detecta puerto) |
| `svc env <svc>` | ver/editar variables |
| `svc config <svc>` | configuración resuelta |
| Cualquier otro | passthrough a `docker compose` |

## Autocompletado TAB

```bash
svc <TAB>          # todos los comandos
svc up <TAB>       # servicios detectados
```

## Plantilla compose.yml (con anchors obligatorios)

Todo compose nuevo DEBE incluir los anchors base del catálogo
(definidos en `agent/catalog/_compose_base.md`):

```yaml
# ── Anchors base (obligatorios) ────────────────────────────────
x-common-env: &common-env
  TZ: America/La_Paz

x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 5
  start_period: 40s

x-security-defaults: &security-defaults
  no-new-privileges: true

x-logging-defaults: &logging-defaults
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"

x-resource-defaults: &resource-defaults
  limits:
    memory: 512m
  reservations:
    memory: 128m

# ── Servicio ───────────────────────────────────────────────────
services:
  <nombre>:
    image: <imagen>:<tag>
    container_name: <nombre>
    restart: unless-stopped
    security_opt:
      - <<: *security-defaults
    deploy:
      resources:
        <<: *resource-defaults
    logging:
      <<: *logging-defaults
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:XXXX/health"]
    environment:
      <<: *common-env
    volumes:
      - ./data:/data
      - ./config:/config
    ports:
      - "XXXX:XXXX"
    networks:
      - iot_net       # elegir según tipo de servicio

# ── Redes (externas compartidas) ──────────────────────────────
networks:
  iot_net:
    external: true
```

## Redes compartidas — convención

El NAS usa redes externas compartidas (NO bridge por servicio):

| Red | Uso |
|-----|-----|
| `iot_net` | IoT: MQTT, ESPHome, Home Assistant, Node-RED |
| `db_net` | Acceso interno a bases de datos |
| `proxy` | Servicios expuestos via reverse proxy (si habilitado) |

Reglas:
- Servicios IoT → `iot_net`
- Bases de datos internas → `db_net`, NUNCA en `proxy`
- Si `reverse_proxy.enabled: false` → no agregar red `proxy`
- Crear red si no existe: `docker network create <nombre>`

## Plantilla con secretos

```yaml
services:
  <nombre>:
    image: <imagen>:<tag>
    container_name: <nombre>
    restart: unless-stopped
    env_file: .env
    environment:
      <<: *common-env
```

`.env` (solo secretos reales):
```env
API_KEY=tu_clave
DB_PASSWORD=contraseña
```

## Carpetas disponibles

| Carpeta | Cuándo crearla |
|---------|---------------|
| `config/` | archivos de configuración |
| `data/` | datos persistentes |
| `log/` | logs fuera del contenedor |
| `.env` | secretos reales |

## Flujo completo — nuevo servicio

```bash
mkdir -p $dkco/<svc>/{config,data}
nano $dkco/<svc>/compose.yml
# (opcional) nano $dkco/<svc>/.env
dk <svc>
svc up <svc>
svc ps <svc>
svc logs <svc>
svc health
```
