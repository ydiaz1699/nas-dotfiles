---
id: "kiro-cli"
name: "Kiro CLI (contenedor bajo demanda)"
description: "Kiro CLI en contenedor aislado para consumir MCPs (rclone, nextdns) desde el NAS por lenguaje natural"
image: "kiro-cli-nas:local"
category: "desarrollo"
port_internal: 0
port_default: 0
protocol: "stdio"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./data:/home/kiro"
env_required: []
env_optional: []
healthcheck: 'ninguno (contenedor interactivo, no servicio de red)'
backup_critical: false
backup_paths:
  - "./data"
protected: false
runtime_status: runtime-verified
target_status: cataloged
docs_url: "https://github.com/ydiaz1699/Varios_tools/tree/main/kiro-cli-nas"
notes: >
  SERVICIO BAJO DEMANDA — NO arranca en el boot. Es un contenedor INTERACTIVO
  (stdin_open + tty), se lanza con `docker run -it` vía el wrapper
  $aadm/.local/bin/kiro (network_mode: host, --v3, inyecta secretos desde .env).
  Está marcado con $dkco/kiro-cli/.no-boot y NO debe ir en layers.conf. Se
  construyó a mano (no con `svc create`), por eso no disparó el recordatorio de
  layers.conf y provocó el fallo de boot documentado en docs/ideas-decisions.md
  entrada #23 (fix: boot-order.sh ahora respeta .no-boot en la validación
  REQUIRE_ALL). El binario de Kiro CLI vive en /opt/kiro y nextdns-mcp en
  /opt/nextdns-venv (fuera de /home/kiro porque el volumen data/ lo taparía).
  data/ debe ser chown 1000:1000. Guías completas en el repo Varios_tools:
  kiro-cli-nas/ (instalación) y rclone-mcp-control-total/ (MCP + permisos V3).
networks: []
ports: {}
resources:
  memory_limit: "1g"
  memory_reservation: "128m"
security_extra: {}
---

# Kiro CLI (contenedor bajo demanda)

## Qué es

Contenedor aislado que corre **Kiro CLI** (agente de IA en terminal) para consumir
servidores **MCP** desde el NAS por lenguaje natural: control total de rclone
(`rclone-rcd`) y NextDNS multi-cuenta. Se eligió Docker por aislamiento total:
borrado sin residuos y arranque **bajo demanda** (no permanente).

## Estructura

```
/docker/kiro-cli/
├── Dockerfile              ← Debian + Node + Kiro CLI (/opt/kiro) + uv + nextdns-mcp (/opt/nextdns-venv)
├── compose.yml             ← network_mode: host, stdin_open/tty, volumen ./data
├── .no-boot                ← marcador: excluido del arranque escalonado
├── nextdns.env             ← secretos NextDNS (chmod 600)
└── data/                   ← $HOME del contenedor (uid 1000): login, .kiro/settings, steering
```

## Configuración importante

- **NO es un servicio de red** — no expone puertos; los MCP hablan por stdio.
- Se lanza con el wrapper `$aadm/.local/bin/kiro` (fuerza `--v3`, inyecta la pass de
  rclone desde `$dkco/rclone-rcd/.env` y las keys de NextDNS desde `nextdns.env`).
- Permisos V3 en `data/.kiro/settings/permissions.yaml` (allow/ask por capacidad MCP).
- Config MCP en `data/.kiro/settings/mcp_tools/*.json` ensamblada con `mcp-build`.

## Redes

- `network_mode: host` — para alcanzar `127.0.0.1:5572` (rclone-rcd) sin socket Docker.

## Volúmenes y datos

- `./data/` — `$HOME` del contenedor: sesión/login de Kiro CLI, `.kiro/settings`
  (mcp.json, permissions.yaml), `.kiro/steering`. Debe ser `chown 1000:1000`.

## Notas

- **NO añadir a `layers.conf`** — es bajo demanda; está en `.no-boot`.
- Depende de `rclone-rcd` (ese SÍ está en layers.conf, Capa 5) para el MCP de rclone.
- Construido a mano; si se re-crea, recordar `chown 1000:1000 data/` y que el
  binario va en `/opt/kiro` (el volumen tapa `/home/kiro/.local/bin`).
- Guía operativa completa (no inferible del compose) en el repo Varios_tools:
  `kiro-cli-nas/README.md` y `rclone-mcp-control-total/README.md`.
