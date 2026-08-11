# Cheatsheet — operaciones manuales del NAS

Variables: `$aadm` = `/home/aadm` · `$dkco` = `/docker` · `$NAS_DOTFILES` = `/nas-dotfiles`

---

## 📂 Navegar

```bash
dk                    # ir a /docker
dk traefik            # ir a /docker/traefik
dk traefik ll         # ir a /docker/traefik + listar
dkf                   # fuzzy finder en /docker (fzf)
adm                   # ir a /home/aadm
adm scripts           # ir a /home/aadm/scripts
adm scripts ll        # ir + listar
admf                  # fuzzy finder en /home/aadm (fzf)
up                    # subir 1 nivel
up 3                  # subir 3 niveles
..                    # cd ..
...                   # cd ../..
....                  # cd ../../..
~                     # cd ~
```

---

## ➕ Crear

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

# Scaffolding automático (genera compose + .env + README + data/)
svc create mi-servicio
```

---

## 🚚 Mover

```bash
mv $dkco/servicio_viejo/config $dkco/servicio_nuevo/
mv $aadm/scripts/test.sh $aadm/scripts/produccion/
mv $dkco/app/docker-compose.yml $dkco/app/compose.yml
```

---

## 🗑️ Borrar

```bash
# Borrar servicio Docker completo (primero bajar)
svc down servicio
rm -r $dkco/servicio/

# Borrar archivo suelto
rm $aadm/scripts/viejo.sh

# Limpiar Docker (imágenes + volúmenes sin usar)
dprune
```

---

## ✏️ Ver y editar

```bash
bat $dkco/traefik/compose.yml        # ver con colores (syntax highlight)
nano $dkco/traefik/compose.yml       # editar compose
nano $dkco/nextcloud/.env            # editar secretos
svc config traefik                   # ver compose resuelto (variables expandidas)
svc env emqx                         # ver variables de entorno del servicio
svc env emqx edit                    # editar .env del servicio
```

`bat` = `batcat --style=header,grid --paging=never`

---

## 📋 Listar

```bash
ls                    # eza (listado básico con colores)
ll                    # eza -lah (detallado con ocultos)
la                    # eza -a (todos sin . y ..)
lt                    # eza -lah --sort=modified (por fecha, reciente abajo)
lsd                   # eza -lD (solo directorios)
```

---

## 🐳 Operar servicios Docker

```bash
# Ciclo de vida
svc up jellyfin              # levantar (docker compose up -d)
svc down jellyfin            # bajar y eliminar contenedores
svc restart traefik          # reiniciar
svc start homeassistant      # iniciar detenido
svc stop plex               # detener sin eliminar
svc kill servicio            # forzar parada
svc pause servicio           # pausar
svc unpause servicio         # reanudar pausado

# Actualizar
svc update emqx              # pull + recrear
svc update-all               # actualizar todos (con confirmación)
svc update-all -y            # actualizar todos sin preguntar

# Inspeccionar
svc logs emqx                # logs en vivo (últimas 200 líneas)
svc logs emqx -n 50          # últimas 50 líneas
svc ps nextcloud             # contenedores del servicio
svc stats grafana            # CPU/RAM en tiempo real
svc top emqx                 # procesos dentro del contenedor
svc exec emqx sh             # shell dentro del contenedor
svc images traefik           # imágenes del servicio
svc volumes nextcloud        # volúmenes del servicio
svc events traefik           # eventos en tiempo real
svc port emqx 1883           # ver puerto público asignado

# Diagnóstico
svc health                   # dashboard (health, uptime, restarts)
svc doctor                   # chequeo 6 puntos del NAS
svc port-map                 # mapa de puertos + conflictos
svc net                      # mapa de redes Docker con IPs
svc size                     # disco por servicio
svc watch                    # monitoreo en vivo (Ctrl+C para salir)
svc watch 10                 # refresh cada 10 seg
svc diff traefik             # compare compose vs config resuelta
svc depends homeassistant    # ver dependencias

# Backup y restore
svc backup nextcloud         # exportar volúmenes + bind mounts a tar.gz
svc restore nextcloud        # restaurar (selector interactivo con fzf)

# Extras
svc lista                    # servicios con estado ●/○
svc open grafana             # mostrar URL + QR + clipboard
svc menu                     # TUI interactivo con fzf

# Compose passthrough (cualquier comando de docker compose)
svc build servicio           # construir imagen
svc pull servicio            # descargar imagen
svc rm servicio              # eliminar contenedores detenidos
svc cp servicio src dst      # copiar archivos al/del contenedor
svc scale servicio s=3       # escalar a 3 réplicas
svc run servicio <cmd>       # ejecutar comando one-off
svc wait servicio            # esperar a que paren
```

---

## 📦 Instalar paquetes

```bash
# Sistema (apt) — con verificación previa y log automático
instal htop ncdu lm-sensors       # instala los 3
instal bat                         # si ya está: "Ya instalado: bat"
instal -y paquete                  # auto-yes (ya incluido por defecto)

# Python (pip) — con verificación previa y log automático
pipins rich typer pyyaml          # instala los 3
pipins -u rich                     # upgrade
pipins docker                      # si ya está: "Ya instalado: docker (x.x)"
```

Logs:
- `$NAS_DOTFILES/logs/packages.txt` — historial apt
- `$NAS_DOTFILES/logs/pip_packages.txt` — historial pip

---

## 🔍 Info del sistema

```bash
nas                   # dashboard: uptime, load, RAM, disco, red, Docker, temp
disk                  # uso de disco (sin tmpfs/loop)
ports                 # puertos en escucha (ss -tulnp)
netinfo               # interfaces activas + puertos TCP
myip                  # IP pública (curl ifconfig.me)
free                  # memoria RAM (-h automático)
df                    # discos (-h automático)
dus                   # du -sh del directorio actual
```

---

## 📜 Logs del sistema

```bash
logs                  # journald, últimas 50 líneas
logs -f               # journald en vivo (follow)
logs syslog           # /var/log/syslog (últimas 50)
logs -f syslog        # follow de syslog
logs auth             # /var/log/auth.log
logs -f auth          # follow de auth.log
logs kern             # /var/log/kern.log
```

---

## 🐋 Docker rápido (sin svc)

```bash
dps                   # docker ps formateado (nombre/estado/puertos)
dpa                   # docker ps -a formateado (incluye detenidos)
dim                   # docker images formateado (repo/tag/size)
dnet                  # docker network ls
dvol                  # docker volume ls
dprune                # docker system prune + volume prune
```

---

## 📁 Archivos (con confirmación interactiva)

```bash
rm archivo            # rm -iv (pide confirmación en terminal)
cp origen destino     # cp -iv (pide confirmación en terminal)
mv origen destino     # mv -iv (pide confirmación en terminal)
mkdir carpeta         # mkdir -pv (crea padres + verbose)
```

En pipes/scripts se comportan normal (sin -i), no rompen automatización.

---

## 🔎 Buscar y filtrar

```bash
grep "patron" archivo         # grep --color=auto
egrep "regex" archivo         # egrep --color=auto
fgrep "literal" archivo       # fgrep --color=auto
```

---

## ✍️ Editar

```bash
nano archivo          # nano -i (autoindent activado)
bat archivo           # batcat --style=header,grid --paging=never (solo ver)
```

---

## 🌿 Git

```bash
# Estado
gs                    # git status -sb
gd                    # git diff
gds                   # git diff --staged
gl                    # git log --oneline -20
glg                   # git log --oneline --graph --decorate -20

# Staging y commit
ga .                  # git add
ga archivo            # git add archivo
gc                    # git commit (abre editor)
gcm "fix: algo"      # git commit -m "..."
gca                   # git commit --amend

# Push / pull
gp                    # git push
gpl                   # git pull
gf                    # git fetch --all --prune

# Ramas
gb                    # git branch
gco rama             # git checkout rama
gsw rama             # git switch rama
gsc nueva-rama       # git switch -c nueva-rama

# Stash
gst                   # git stash
gstp                  # git stash pop

# Atajos
git-quick "msg"       # add -A + commit + push (todo en uno)
git-clean-branches    # eliminar ramas mergeadas locales
```

---

## 🤖 Agente IA

```bash
agent "query"                    # consulta puntual (Gemini default)
agent chat                       # modo REPL conversacional
agent --new "query"              # nueva sesión limpia
agent --model                    # cambiar modelo (menú interactivo)
agent --model gemini-2.5-flash   # cambiar directamente
agent --status                   # info de sesión actual
agent --clear                    # borrar sesión
```

---

## 🖥️ Prompt — qué significa

```
aadm@Nas ~/docker/cli (main*) 4↑ 71% $
```

| Parte | Significado |
|-------|-------------|
| `aadm` | usuario (azul; rojo si root) |
| `Nas` | hostname (cyan) |
| `~/docker/cli` | directorio actual (bold) |
| `(main*)` | rama git + `*` si hay cambios (magenta) |
| `4↑` | contenedores Docker corriendo (verde >0, gris =0) |
| `71%` | disco raíz (verde <75%, amarillo <90%, rojo ≥90%) |
| `$`/`#` | verde si último OK, rojo si falló |

---

## ⌨️ Autocompletado TAB

```bash
svc <TAB>             # todos los comandos svc
svc up <TAB>          # servicios en /docker/
svc logs <TAB>        # servicios en /docker/
dk <TAB>              # carpetas en /docker/
adm <TAB>             # carpetas en /home/aadm/
instal <TAB>          # paquetes apt (después de 2+ chars)
logs <TAB>            # syslog, auth, kern, archivos en /var/log
```

---

## 🔄 Recargar shell

```bash
reload                # source ~/.bashrc (sin cerrar terminal)
```

---

## 🧩 Extender — nuevo destino de navegación

```bash
# Agregar en shell/lib/nav.sh:
sc()  { _nav "/mi/ruta" "$@"; }
scf() { _nav_fzf "/mi/ruta" "sc>"; }
_sc_completions() { _nav_complete "/mi/ruta"; }
complete -F _sc_completions sc
```

---

## ⚡ Regla de oro

| Quieres... | Usa | Nunca |
|------------|-----|-------|
| Ir a /docker/X | `dk X` | `cd /docker/X` |
| Ir a /home/aadm/X | `adm X` | `cd /home/aadm/X` |
| Operar Docker | `svc <acción> <svc>` | `docker compose ...` |
| Instalar apt | `instal pkg` | `apt install pkg` |
| Instalar pip | `pipins pkg` | `pip install pkg` |
| Referir rutas | `$dkco/...` · `$aadm/...` | `/docker/...` · `/home/aadm/...` |
| Ver archivos | `bat archivo` | `cat archivo` |
| Compose file | `compose.yml` | `docker-compose.yml` |

Tu entorno envuelve todo con log, verificación, colores, y autocompletado TAB.
