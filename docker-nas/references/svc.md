# svc — CLI Docker referencia completa

## Archivos

```
$NAS_DOTFILES/docker/cli/
├── svc.sh               ← entrypoint (función svc en init.sh)
└── lib/
    ├── discovery.sh     ← svc_list(), svc_compose_file()
    ├── docker.sh        ← svc_update_all()
    ├── health.sh        ← svc_health(), svc_lista()
    ├── backup.sh        ← svc_backup(), svc_restore()
    ├── extras.sh        ← port-map, size, net, doctor, diff, watch, create, env, open, depends
    ├── menu.sh          ← svc_menu() TUI con fzf
    └── help.sh          ← _svc_ayuda()
```

## CLI dual

```bash
NAS_CLI=bash    # default — usa docker/cli/svc.sh
NAS_CLI=python  # alternativo — usa svc_py/ (Rich + InquirerPy)
```

`svc snapshot` está disponible en las dos entradas: el comando Python lo
registra y delega al Bash CLI mediante `bash_bridge.py`, que es la fuente única
de la lógica. `rollback` sigue siendo Bash-only. Si el NAS todavía tiene un
checkout anterior y Python responde `No such command 'snapshot'`, usar el
fallback temporal:

```bash
NAS_CLI=bash svc snapshot <svc>
NAS_CLI=bash svc rollback <svc>
```

Después de actualizar el checkout del framework con `nasfk` + `gpl`, comprobar
el comando antes de usarlo. No implementar una segunda versión de la lógica de
snapshots en Python.

## Detección de servicios

`svc_list()` busca en `$DOCKER_BASE/*/` archivos compose (depth 2).
`svc_compose_file()` retorna el path del compose file encontrado.

Orden de búsqueda:
1. `compose.yml` (canónico del proyecto)
2. `compose.yaml`
3. `docker-compose.yml`
4. `docker-compose.yaml`

Si existen varios en el mismo servicio, se usa el primero según este orden y
se debe eliminar o renombrar el resto para evitar ambigüedad.

---

## Comandos globales (sin servicio)

| Comando | Acción |
|---------|--------|
| `svc lista` | Lista servicios con estado ●/○ |
| `svc health` | Dashboard: health, uptime, restart count por servicio |
| `svc doctor` | Chequeo 8 puntos: disco, memoria, servicios, puertos reservados, restarts, Docker storage, secretos y permisos .env |
| `svc update-all [-y]` | Pull + recrear todos (con confirmación, -y para skip) |
| `svc port-map` | Mapa global de puertos + detecta conflictos |
| `svc size` | Disco por servicio (imágenes, volúmenes, dir) |
| `svc net` | Mapa de redes Docker con contenedores + IPs |
| `svc watch [N]` | Monitoreo en vivo (CPU/RAM/uptime, cada N seg) |
| `svc create <nombre>` | Scaffolding: compose + .env + README + data/ |
| `svc diff <servicio>` | Comparar compose en disco vs config resuelta |
| `svc diff --all` | Comparar todos los compose locales contra el catálogo, sin entrar en carpetas |
| `svc menu` | TUI interactivo con preview (requiere fzf) |
| `svc --help` | Ayuda completa |

---

## Comandos propios (requieren servicio)

| Comando | Acción |
|---------|--------|
| `svc update <svc>` | Pull + recrear contenedores (--remove-orphans) |
| `svc backup <svc>` | Backup volúmenes nombrados + bind mounts a tar.gz |
| `svc restore <svc> [f]` | Restaurar desde backup (selector interactivo con fzf) |
| `svc snapshot <svc>` | Guardar solo `compose.yml` y `.env` en `.snapshots/` (rotación 10) |
| `svc rollback <svc>` | Restaurar una configuración snapshot (selector + confirmación) |
| `svc depends <svc>` | Ver servicios definidos + depends_on |
| `svc env <svc> [edit]` | Ver/editar variables de entorno (.env + inline) |
| `svc open <svc>` | Mostrar URL + QR + clipboard (auto-detecta puerto) |

---

## Docker Compose passthrough

Cualquier subcomando de `docker compose` funciona automáticamente:

| Comando | Acción |
|---------|--------|
| `svc up <svc>` | Crear e iniciar (detached) |
| `svc down <svc>` | Detener y eliminar contenedores |
| `svc restart <svc>` | Reiniciar |
| `svc start/stop <svc>` | Iniciar detenido / detener |
| `svc kill <svc>` | Forzar parada |
| `svc pause/unpause <svc>` | Pausar / reanudar |
| `svc logs <svc>` | Logs en vivo (últimas 200 líneas) |
| `svc logs <svc> -n 50` | Últimas 50 líneas |
| `svc ps <svc>` | Listar contenedores |
| `svc stats <svc>` | CPU/RAM en tiempo real |
| `svc top <svc>` | Procesos corriendo |
| `svc exec <svc> <cmd>` | Ejecutar en contenedor |
| `svc build <svc>` | Construir imagen |
| `svc pull <svc>` | Descargar imagen |
| `svc images <svc>` | Listar imágenes |
| `svc rm <svc>` | Eliminar contenedores detenidos |
| `svc config <svc>` | Config resuelta (variables expandidas) |
| `svc cp <svc> src dst` | Copiar archivos al/del contenedor |
| `svc events <svc>` | Eventos en tiempo real |
| `svc port <svc> <p>` | Ver puerto público asignado |
| `svc volumes <svc>` | Listar volúmenes |
| `svc scale <svc> s=N` | Escalar réplicas |
| `svc run <svc> <cmd>` | Comando one-off |
| `svc wait <svc>` | Esperar a que paren |

---

## Autocompletado TAB

```bash
svc <TAB>          # todos los comandos (globales + servicio)
svc up <TAB>       # servicios detectados en $DOCKER_BASE/
svc logs <TAB>     # idem
svc restart <TAB>  # idem
```

---

## Plantilla compose.yml (estándar actual con `extends`)

Los defaults compartidos viven en `$dkco/_common.yml`. Todo compose nuevo debe
heredarlos con `extends`; no debe copiar anchors locales de seguridad, logging y
recursos. El servicio todavía declara sus propios valores específicos: imagen,
`env_file`, puertos, volúmenes, healthcheck y redes.

```yaml
services:
  <nombre>:
    extends:
      file: ../_common.yml
      service: _defaults
    image: <imagen>:<tag>
    container_name: <nombre>
    env_file:
      - ../.env          # global: SERVER_IP, TZ
      - .env             # secretos locales
    environment:
      VARIABLE_PROPIA: valor
    volumes:
      - ./data:/data
    ports:
      - "8100:XXXX"
    labels:
      - homepage.group=Grupo
      - homepage.name=Nombre
      - homepage.icon=mdi-application
      - homepage.href=http://${SERVER_IP}:8100
      - homepage.description=Descripción corta
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:XXXX/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
    networks:
      - homepage_net       # elegir según tipo de servicio

networks:
  homepage_net:
    external: true
```

`env_file: [../.env, .env]` reemplaza el antiguo `<<: *common-env` para `TZ`.
No duplicar `TZ` en `environment:`. Si el compose se guarda en el catálogo,
`agent/catalog/services/<svc>/compose.yml`, su ruta equivalente es
`../../_common.yml`; el pipeline la transforma al desplegar al NAS.

Para una aplicación que usa DataSQL, leer antes `docs/services/datasql-guide.md`,
usar `db_net`, crear una DB/usuario dedicados y no publicar bases a la LAN.
La instalación y operación del stack están en `docs/services/aipostgres-guide.md`.
Home Assistant es una excepción: al usar `network_mode: host`, su Recorder necesita
PostgreSQL limitado a `127.0.0.1:5432:5432`. No usar `depends_on` contra
`datapostgres` si DataSQL está en otro compose.

---

## Redes compartidas — convención

El NAS usa redes externas compartidas (NO bridge aislada por servicio):

| Red | Uso |
|-----|-----|
| `iot_net` | IoT: MQTT, ESPHome, Home Assistant, Node-RED |
| `db_net` | Acceso interno a bases de datos |
| `proxy` | Servicios expuestos via reverse proxy (si habilitado) |

Reglas:
- Servicios IoT → `iot_net`
- Bases de datos internas → `db_net`, NUNCA en `proxy`
- Si `reverse_proxy.enabled: false` → no agregar red `proxy`
- Las redes externas compartidas se verifican con `svc net`. Para una
  instalación nueva, seguir el procedimiento de bootstrap de networking; no
  borrar/recrear `db_net` durante una reparación de DataSQL.
- Comunicación entre servicios: usar `container_name` como hostname (no IP)

---

## Plantilla con secretos (.env)

**compose.yml: mínimo para un servicio con secretos**
```yaml
services:
  <nombre>:
    extends:
      file: ../_common.yml
      service: _defaults
    image: <imagen>:<tag>
    container_name: <nombre>
    env_file:
      - ../.env
      - .env
    environment:
      DB_PASSWORD: "${DB_PASSWORD}"
```

**.env** (solo secretos reales):
```env
API_KEY=tu_clave_secreta
DB_PASSWORD=contraseña_segura
```

---

## Carpetas disponibles

| Carpeta | Cuándo crearla |
|---------|----------------|
| `config/` | el servicio tiene archivos de configuración |
| `data/` | el servicio persiste datos |
| `log/` | el servicio escribe logs fuera del contenedor |
| `.env` | hay secretos reales que no deben estar en el compose |

---

## Ejemplos por tipo de servicio

### Simple (solo datos)
```
$dkco/grafana/
├── compose.yml
└── data/
```
```bash
mkdir -p $dkco/grafana/data
```

### Con configuración separada
```
$dkco/nginx/
├── compose.yml
├── config/
│   └── nginx.conf
└── data/
```
```bash
mkdir -p $dkco/nginx/{config,data}
```

### Con secretos
```
$dkco/nextcloud/
├── compose.yml
├── .env
├── config/
└── data/
```
```bash
mkdir -p $dkco/nextcloud/{config,data}
touch $dkco/nextcloud/.env
```

### Con logs externos
```
$dkco/traefik/
├── compose.yml
├── config/
├── data/
└── log/
```
```bash
mkdir -p $dkco/traefik/{config,data,log}
```

### Stack complejo (múltiples contenedores)
```
$dkco/monitoring/
├── compose.yml
├── grafana/
│   ├── config/
│   └── data/
└── prometheus/
    ├── config/
    │   └── prometheus.yml
    └── data/
```
```bash
mkdir -p $dkco/monitoring/{grafana/{config,data},prometheus/{config,data}}
```

---

## Flujo completo — nuevo servicio

```bash
# 1. Crear estructura
mkdir -p $dkco/<svc>/{config,data}

# 2. Crear compose (con anchors base)
nano $dkco/<svc>/compose.yml

# 3. (Opcional) .env si hay secretos
nano $dkco/<svc>/.env

# 4. Navegar y levantar
dk <svc>
svc up <svc>

# 5. Verificar
svc ps <svc>
svc logs <svc>
svc health
```

---

## Backup y restauración

```bash
# Backup (volúmenes nombrados + bind mounts → tar.gz)
svc backup <svc>
# → $dkco/backups/<svc>_vol_<vol>_<timestamp>.tar.gz
# → $dkco/backups/<svc>_bind_<mount>_<timestamp>.tar.gz

# Restaurar (interactivo con fzf si disponible)
svc restore <svc>
# Detiene servicio → restaura → ofrece reiniciar

# Rotación automática: conserva últimos $BACKUP_KEEP (default: 5)
```

### Snapshot y rollback de configuración

`svc snapshot <svc>` no reemplaza a `svc backup`: guarda un tar.gz pequeño con
el `compose.yml`, `.env` y archivos YAML de configuración en
`$dkco/backups/.snapshots/`. Sirve para volver atrás rápidamente antes de
cambiar un Compose o una variable. Se conservan los últimos 10 snapshots por
servicio.

```bash
svc snapshot datasql
# editar/aplicar cambios y validar
svc config datasql
svc rollback datasql
```

`rollback` es interactivo y requiere confirmar la instantánea elegida. No
restaura los datos persistentes; para eso se usa `svc backup`/`svc restore` o el
backup específico de PostgreSQL. Si el CLI Python no reconoce `snapshot`, usar
`NAS_CLI=bash svc snapshot <svc>` hasta actualizar el checkout del NAS.


---

## Convenciones de puertos

| Rango | Uso |
|-------|-----|
| 22, 53, 80, 443 | RESERVADOS — nunca asignar |
| 8100-8999 | Servicios nuevos del usuario |
| 1883, 8883 | MQTT (EMQX) |
| 1880 | Node-RED |
| 8123 | Home Assistant |
| 9090 | Prometheus |
| 3000 | Grafana |

---

## Notas

- Backups se rotan automáticamente (default: últimos 5, configurable con `$BACKUP_KEEP`)
- `svc open` genera QR code si `qrencode` está instalado
- `svc menu` requiere `fzf` para funcionar
- `svc watch` corre en loop — Ctrl+C para salir
- `svc diff` detecta variables sin resolver en el compose
- `svc doctor` revisa puertos reservados en uso por servicios Docker
