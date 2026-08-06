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

## Plantilla compose.yml

```yaml
services:
  <nombre>:
    image: <imagen>:<tag>
    container_name: <nombre>
    restart: unless-stopped
    environment:
      - TZ=America/La_Paz
    volumes:
      - ./data:/data
      - ./config:/config
    ports:
      - "XXXX:XXXX"
    networks:
      - <nombre>_net

networks:
  <nombre>_net:
    driver: bridge
```

## Plantilla con secretos

```yaml
services:
  <nombre>:
    image: <imagen>:<tag>
    container_name: <nombre>
    restart: unless-stopped
    env_file: .env
    environment:
      - TZ=America/La_Paz
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
