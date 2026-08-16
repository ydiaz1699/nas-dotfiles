# NAS Skill — Contexto Operativo

> **Auto-generado por `svc catalog-sync`.** No editar secciones marcadas [AUTO].  
> Última actualización: 2026-08-15

---

## 1. Metadata & Trigger

```yaml
name: nas-homelab
version: "2.0"
trigger: >
  Activar cuando el usuario mencione CUALQUIERA de estos contextos
  (aunque no diga "NAS" explícitamente):
  - Servicios: Docker, contenedor, compose, imagen, puerto, red, volumen
  - Comandos: dk, adm, nasfk, svc, instal, pipins, gpl, gs, nas, bat
  - Servicios específicos: emqx, ntfy, adguard, filebrowser, esphome,
    homepage, datasql, pgadmin, redis, usb-api, spacedrive
  - Infra: homelab, servidor, backup, cron, systemd, USB, mount
  - IoT: MQTT, broker, ESP32, Home Assistant, alarma, sensor
  - Redes: macvlan, bridge, iot_net, db_net, homepage_net, DNS
  - Notificaciones: ntfy, push, alerta, topic
  - Operaciones: actualizar, reiniciar, logs, health, doctor
  - Almacenamiento: disco, NAS, USB, automount, /NAS/USB
  - Output pegado con prompt "root@Nas" o "aadm@Nas"
scope: encoded-preferences
  # NO caduca con modelos nuevos — son procesos únicos del usuario.
```

**Regla:** Si el usuario habla del NAS, SIEMPRE cargar esta skill antes de responder.

---

## 2. Entorno (lo justo para no improvisar)

### Máquina

| Campo | Valor |
|-------|-------|
| Equipo | Dell PowerEdge T20 |
| IP | 192.168.1.200 |
| Hostname | `Nas` (accesible via `ssh aadm@Nas.local`) |
| OS | Debian 13, kernel 6.12 |
| CPU/RAM | 2 cores @ 3GHz / 8 GB ECC |
| Disco | SSD 298 GB ext4 (8%) |

### Variables de entorno

| Variable | Valor | Atajo |
|----------|-------|-------|
| `$NAS_DOTFILES` | `/nas-dotfiles` | `nasfk` |
| `$dkco` | `/docker` | `dk` |
| `$aadm` | `/home/aadm` | `adm` |
| `$NTFY_URL` | `http://192.168.1.200:8090` | — |

---

## 3. Encoded Preferences (NUNCA/SIEMPRE)

Estas reglas son permanentes. No cambian con modelos nuevos.

```
NUNCA usar:                         SIEMPRE usar:
─────────────────────────────────────────────────────
  cd /docker/X                  →   dk X
  cd /nas-dotfiles              →   nasfk
  cd /home/aadm                 →   adm
  git pull                      →   gpl
  git status                    →   gs
  git add                       →   ga
  git commit -m "msg"           →   gc "msg"
  git push                      →   gp
  git add -A && commit && push  →   git-quick "msg"
  apt install pkg               →   instal pkg
  pip install pkg               →   pipins pkg
  docker compose up -d          →   svc up X
  docker compose down           →   svc down X
  docker compose logs           →   svc logs X
  docker restart X              →   svc restart X
  cat archivo                   →   bat archivo
  notify-send                   →   ntfy_send (headless)
  docker-compose.yml            →   compose.yml
  /path/to/...                  →   deducir o preguntar
  hardcodear rutas              →   usar $variables
```

### Notificaciones

```bash
# Función compartida (source automático)
ntfy_send "topic" "título" "mensaje" "prioridad" "tags"

# Topics: usb, docker, backups, system, alarma, nas-alerts
# Prioridades: min, low, default, high, urgent
```

### Nuevo servicio (orden obligatorio)

```
1. mkdir -p $dkco/<svc>/data
2. Crear compose.yml + .env
3. chmod 600 .env
4. Agregar labels homepage.* en compose
5. dk <svc> && svc up <svc>
6. svc catalog-sync <svc>  → genera toda la documentación
```

### Homepage

- **Labels en compose (auto-descubrimiento)** > services.yaml
- `services.yaml` solo para servicios nativos (systemd)
- Recrear contenedor para que tome labels nuevas: `svc recreate X`

---

## 4. Skill Registry [AUTO]

Índice ligero de servicios. **NO cargar los archivos — solo buscar cuando se necesite.**

| Servicio | Puerto | Red | Docs (cargar si se necesita) |
|----------|--------|-----|------|
| adguard | 53,80 (IP: .201) | macvlan | `agent/catalog/services/adguard/` |
| emqx | 1883,18083 | iot_net, db_net | `agent/catalog/services/emqx/ficha.md` |
| esphome | 6052 | host | `agent/catalog/services/esphome/ficha.md` |
| datasql | 5050 | db_net | `docs/services/datasql-guide.md` |
| filebrowser | 8085 | default | `docs/services/filebrowser-guide.md` |
| homepage | 3000 | homepage_net | `docs/services/homepage-guide.md` |
| ntfy | 8090 | homepage_net | `docs/services/ntfy-guide.md` |
| usb-api | 8091 | nativo (systemd) | `agent/catalog/services/usb-api/ficha.md` |

### Redes

| Red | Propósito | Regla |
|-----|-----------|-------|
| `adguard_macvlan_NET` | IP dedicada AdGuard (DNS:53) | Solo macvlan |
| `db_net` | Apps ↔ DBs (interno) | Nunca exponer puertos al host |
| `iot_net` | EMQX ↔ ESPHome ↔ HA | Todo IoT aquí |
| `homepage_net` | Homepage ↔ servicios (widgets) | Para APIs internas |

### USB Automount

| Campo | Valor |
|-------|-------|
| Mount base | `/NAS/USB/` |
| Formato | `/NAS/USB/<LABEL>` o `/NAS/USB/usb-<dev>` (sin label) |
| API | `GET http://192.168.1.200:8091/usb/list` |
| Desmontar | `POST http://192.168.1.200:8091/usb/unmount/<dev>` |
| Cleanup | `usb-automount.sh --cleanup` o `umount -l` + `rmdir` |

---

## 5. Documentación disponible (lazy loading)

**Regla: NO leer estos archivos al activar la skill.** Solo cargar cuando el usuario pregunte sobre ese tema.

| Trigger | Archivo a cargar |
|---------|-----------------|
| Preguntan por un servicio específico | `docs/services/<svc>-guide.md` → `agent/catalog/services/<svc>/ficha.md` |
| Quieren crear servicio nuevo | `agent/catalog/_template.md` + `agent/catalog/_compose_base.md` |
| Troubleshooting USB / mounts | `docs/services/ntfy-guide.md` §Troubleshooting |
| Configurar Homepage | `docs/services/homepage-guide.md` |
| Pipeline de auto-docs | `docs/catalog-sync-pipeline.md` |
| Info completa del NAS | `docs/nas-manual.md` |
| Todos los comandos shell | `docker-nas/references/entorno.md` |
| Todos los comandos svc | `docker-nas/references/svc.md` |
| Seguridad y convenciones | `docker-nas/references/seguridad.md` |
| Diagnóstico paso a paso | `docker-nas/references/diagnostic.md` |
| Redes avanzadas (macvlan) | `docker-nas/references/networking.md` |
| Agente IA (tools, plugins) | `docker-nas/references/agent.md` |
| Extender framework | `docker-nas/references/extend.md` |

---

## 6. Progressive Updates (self-learning)

Cuando el usuario corrige al LLM o da feedback, agregar aquí.
Formato: `[fecha] corrección`.

```
[2026-08-15] La IP real del NAS es 192.168.1.200 (no .0.200)
[2026-08-15] ntfy ya estaba en homepage_net (el compose lo incluye)
[2026-08-15] EMQX ya tiene labels Homepage en su compose (no poner en services.yaml)
[2026-08-15] ENABLE_NOTIFICATIONS estaba en "false" — siempre verificar /etc/usb-automount.conf
[2026-08-15] El script de usb-automount en /usr/local/bin/ puede ser versión vieja — verificar con grep ntfy_send
[2026-08-15] USBs ahora montan con LABEL (no usb-sdb1) — formato: /NAS/USB/<LABEL>
[2026-08-15] Mountpoints fantasma: solución = umount -l + rmdir (el timer no puede limpiarlos)
[2026-08-15] Browser push notifications requieren HTTPS — usar Chrome con --unsafely-treat-insecure-origin-as-secure flag en LAN
```

> **Instrucción al LLM:** Cuando el usuario te corrija algo sobre el NAS
> (ruta, IP, alias, comportamiento de un servicio), agregar una línea aquí
> con la fecha y la corrección. Esto evita repetir el mismo error.

---

## 7. Verificación rápida (para el LLM)

Antes de sugerir CUALQUIER comando para el NAS, verificar:

- [ ] ¿Usé el alias correcto? (dk, svc, nasfk, gpl, instal...)
- [ ] ¿Usé variables de entorno, no rutas hardcodeadas?
- [ ] ¿El servicio tiene guía? → Leerla ANTES de sugerir cambios
- [ ] ¿Sugerí labels de Homepage en vez de services.yaml?
- [ ] ¿El orden es correcto? (mkdir → archivos → permisos → levantar)
- [ ] ¿Notificaciones van con ntfy_send, no notify-send?
