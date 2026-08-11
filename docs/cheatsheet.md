# Cheatsheet — operaciones manuales del NAS

> Referencia rápida para uso diario desde la terminal SSH.
> Variables: `$aadm` → `/home/aadm` · `$dkco` → `/docker` · `$NAS_DOTFILES` → `/nas-dotfiles`

---

## Navegar

```bash
dk                    # ir a /docker
dk traefik            # ir a /docker/traefik
dk traefik ll         # ir + listar contenido
adm                   # ir a /home/aadm
adm scripts           # ir a /home/aadm/scripts
up                    # subir 1 nivel
up 3                  # subir 3 niveles
dkf                   # fuzzy finder en /docker (fzf)
admf                  # fuzzy finder en /home/aadm (fzf)
```

---

## Crear

```bash
# Nuevo servicio Docker (estructura mínima)
mkdir -p $dkco/jellyfin/{config,data}
nano $dkco/jellyfin/compose.yml
dk jellyfin
svc up jellyfin

# Servicio con secretos
mkdir -p $dkco/vaultwarden/data
touch $dkco/vaultwarden/.env
nano $dkco/vaultwarden/compose.yml

# Carpeta personal
mkdir -p $aadm/proyectos/nuevo
```

---

## Mover

```bash
mv $dkco/servicio_viejo/config $dkco/servicio_nuevo/
mv $aadm/scripts/test.sh $aadm/scripts/produccion/
mv $dkco/app/docker-compose.yml $dkco/app/compose.yml   # renombrar al preferido
```

---

## Borrar

```bash
# Borrar servicio Docker completo (primero bajar)
svc down servicio
rm -r $dkco/servicio/

# Borrar archivo suelto
rm $aadm/scripts/viejo.sh

# Borrar contenedores huérfanos + imágenes sin usar
dprune
```

---

## Ver / Editar

```bash
bat $dkco/traefik/compose.yml        # ver con colores (solo lectura)
nano $dkco/traefik/compose.yml       # editar compose
nano $dkco/nextcloud/.env            # editar secretos

ll $dkco/grafana/                    # listar detallado
lt $dkco/                            # listar por fecha (reciente abajo)
```

---

## Operar servicios Docker

```bash
# Ciclo de vida
svc up jellyfin             # levantar (docker compose up -d)
svc down jellyfin           # bajar y eliminar contenedores
svc restart traefik         # reiniciar
svc start homeassistant     # iniciar detenido
svc stop plex              # detener sin eliminar

# Actualizar
svc update emqx            # pull + recrear
svc update-all             # actualizar todos (con confirmación)

# Inspeccionar
svc logs emqx              # logs en vivo (últimas 200 líneas)
svc logs emqx -n 50        # últimas 50 líneas
svc ps nextcloud           # contenedores del servicio
svc stats grafana          # CPU/RAM en tiempo real
svc exec emqx sh           # shell dentro del contenedor

# Diagnóstico
svc health                 # dashboard de todos los servicios
svc doctor                 # chequeo 6 puntos del NAS
svc port-map               # mapa de puertos + conflictos
svc net                    # mapa de redes Docker

# Backup
svc backup nextcloud       # exportar volúmenes a tar.gz
svc restore nextcloud      # restaurar (selector interactivo)

# Extras
svc lista                  # servicios con estado ●/○
svc size                   # disco por servicio
svc open grafana           # mostrar URL + QR
svc menu                   # TUI interactivo (fzf)
svc depends homeassistant  # ver dependencias
svc env emqx               # ver variables de entorno
svc env emqx edit          # editar .env del servicio
```

---

## Instalar paquetes

```bash
# Sistema (apt) — con verificación y log automático
instal htop ncdu lm-sensors
instal bat                  # si ya está: "Ya instalado: bat"

# Python (pip) — con verificación y log automático
pipins rich typer pyyaml
pipins -u rich              # upgrade
```

Logs guardados en:
- `$NAS_DOTFILES/logs/packages.txt` (apt)
- `$NAS_DOTFILES/logs/pip_packages.txt` (pip)

---

## Info del sistema

```bash
nas                   # dashboard: uptime, RAM, disco, red, Docker, temp
disk                  # uso de disco (sin tmpfs)
ports                 # puertos en escucha (ss -tulnp)
netinfo               # interfaces + puertos TCP
myip                  # IP pública
free                  # memoria RAM
```

---

## Logs del sistema

```bash
logs                  # journald, últimas 50 líneas
logs -f               # journald en vivo (follow)
logs syslog           # /var/log/syslog
logs -f auth          # follow de auth.log
logs kern             # kernel
```

---

## Git

```bash
gs                    # git status -sb
ga .                  # git add
gcm "fix: algo"      # git commit -m "..."
gp                    # git push
gpl                   # git pull
gl                    # log --oneline (últimos 20)
glg                   # log --graph --decorate
gd                    # git diff
gds                   # git diff --staged
gst                   # git stash
gstp                  # git stash pop
git-quick "msg"       # add -A + commit + push (todo en uno)
git-clean-branches    # eliminar ramas mergeadas locales
```

---

## Prompt — qué significa cada parte

```
aadm@Nas ~/docker/cli (main*) 4↑ 71% $
```

| Parte | Significado |
|-------|-------------|
| `aadm` | usuario (azul; rojo si root) |
| `Nas` | hostname (cyan) |
| `~/docker/cli` | directorio actual (bold) |
| `(main*)` | rama git + `*` si hay cambios (magenta) |
| `4↑` | contenedores Docker corriendo (verde) |
| `71%` | disco raíz usado (verde <75%, amarillo <90%, rojo ≥90%) |
| `$` / `#` | verde si último OK, rojo si falló |

---

## Regla de oro

| Quieres... | Usa... | Nunca... |
|------------|--------|----------|
| Ir a /docker/X | `dk X` | `cd /docker/X` |
| Ir a /home/aadm/X | `adm X` | `cd /home/aadm/X` |
| Operar Docker | `svc <acción> <svc>` | `docker compose ...` |
| Instalar apt | `instal pkg` | `apt install pkg` |
| Instalar pip | `pipins pkg` | `pip install pkg` |
| Referir rutas | `$dkco/...`, `$aadm/...` | `/docker/...`, `/home/aadm/...` |

---

## Agente IA (cuando necesitas razonamiento)

```bash
agent "¿Qué servicios están caídos?"
agent "Quiero instalar Jellyfin"
agent "Diagnostica nextcloud"
agent chat                           # modo conversacional
agent --model                        # cambiar modelo
```

Regla: si sabes el comando exacto → hazlo manual con `svc`.
Si necesitas pensar/buscar/decidir → `agent`.
