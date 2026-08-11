# svc — referencia completa

## Estructura de archivos

```
$NAS_DOTFILES/docker/cli/
├── svc.sh               ← entrypoint (función svc en init.sh)
└── lib/
    ├── discovery.sh     ← svc_list(), svc_compose_file()
    ├── docker.sh        ← svc_update_all()
    ├── health.sh        ← svc_health(), svc_lista()
    ├── backup.sh        ← svc_backup(), svc_restore()
    ├── extras.sh        ← port-map, size, net, env, create, watch, doctor, open, depends
    ├── menu.sh          ← svc_menu() TUI con fzf
    └── help.sh          ← _svc_ayuda()
```

## Detección de servicios

`svc_list()` busca en `$DOCKER_BASE/*/` archivos compose (depth 2).
`svc_compose_file()` retorna el path del compose file encontrado.

Orden de búsqueda:
1. `docker-compose.yml`
2. `docker-compose.yaml`
3. `compose.yml`
4. `compose.yaml`

---

## Uso general

```bash
svc <comando> [<servicio>] [argumentos]
```

---

## Comandos globales (sin servicio)

| Comando | Acción |
|---------|--------|
| `svc lista` | Lista servicios con estado ●/○ |
| `svc health` | Dashboard: health, uptime, restart count |
| `svc update-all [-y]` | Pull + recrear todos (con confirmación) |
| `svc port-map` | Mapa de puertos + detecta conflictos |
| `svc size` | Disco por servicio (imágenes, volúmenes, dir) |
| `svc net` | Mapa de redes Docker con contenedores + IPs |
| `svc watch [N]` | Monitoreo en vivo (CPU/RAM/uptime, cada N seg) |
| `svc create <nombre>` | Scaffolding: compose + .env + README + data/ |
| `svc doctor` | Chequeo 6 puntos: disco, RAM, servicios, puertos, restarts, Docker storage |
| `svc diff <servicio>` | Comparar compose en disco vs config resuelta |
| `svc menu` | TUI interactivo con preview (requiere fzf) |
| `svc --help` | Ayuda completa |

---

## Comandos propios (requieren servicio)

| Comando | Acción |
|---------|--------|
| `svc update <svc>` | Pull + recrear contenedores |
| `svc backup <svc>` | Backup volúmenes + bind mounts a tar.gz |
| `svc restore <svc> [f]` | Restaurar desde backup (interactivo) |
| `svc depends <svc>` | Ver servicios definidos + depends_on |
| `svc env <svc> [edit]` | Ver/editar variables de entorno |
| `svc open <svc>` | Mostrar URL + QR + clipboard |

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
| `svc ps <svc>` | Listar contenedores |
| `svc stats <svc>` | CPU/RAM en tiempo real |
| `svc top <svc>` | Procesos corriendo |
| `svc exec <svc> <cmd>` | Ejecutar en contenedor |
| `svc build <svc>` | Construir imagen |
| `svc pull <svc>` | Descargar imagen |
| `svc images <svc>` | Listar imágenes |
| `svc rm <svc>` | Eliminar contenedores detenidos |
| `svc config <svc>` | Config resuelta |
| `svc cp <svc> src dst` | Copiar archivos |
| `svc events <svc>` | Eventos en tiempo real |
| `svc port <svc> <p>` | Ver puerto público |
| `svc volumes <svc>` | Listar volúmenes |
| `svc scale <svc> s=N` | Escalar réplicas |
| `svc run <svc> <cmd>` | Comando one-off |
| `svc wait <svc>` | Esperar a que paren |

---

## Autocompletado TAB

```bash
svc <TAB>          # todos los comandos
svc up <TAB>       # servicios en $DOCKER_BASE/
svc logs <TAB>     # idem
```

---

## Flujos típicos

### Nuevo servicio
```bash
mkdir -p $dkco/<svc>/{config,data}
nano $dkco/<svc>/compose.yml
dk <svc>
svc up <svc>
svc logs <svc>
svc health
```

### Actualización
```bash
svc update <svc>       # uno
svc update-all         # todos
```

### Diagnóstico
```bash
svc health             # estado global
svc doctor             # chequeo 6 puntos
svc ps <svc>           # contenedores
svc logs <svc>         # errores
svc stats <svc>        # recursos
svc top <svc>          # procesos
```

### Backup y restore
```bash
svc backup <svc>       # exportar a $dkco/backups/
svc restore <svc>      # selector interactivo con fzf
```

---

## Notas

- Backups se rotan automáticamente (default: últimos 5, configurable con `$BACKUP_KEEP`)
- `svc open` genera QR code si `qrencode` está instalado
- `svc menu` requiere `fzf` para funcionar
- `svc watch` corre en loop — Ctrl+C para salir
