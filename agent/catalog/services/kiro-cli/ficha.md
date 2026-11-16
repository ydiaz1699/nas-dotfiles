---
id: "kiro-cli"
name: "Kiro CLI (contenedor bajo demanda)"
description: "Kiro CLI en contenedor aislado para consumir MCPs (rclone, nextdns, n8n, jdownloader, karakeep) desde el NAS por lenguaje natural"
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
docs_url: "docs/services/kiro-cli-guide.md"
notes: >
  SERVICIO BAJO DEMANDA — NO arranca en el boot. Es un contenedor INTERACTIVO
  (stdin_open + tty), se lanza con `docker run -it` vía el wrapper
  $aadm/.local/bin/kiro (network_mode: host, --v3, inyecta secretos desde .env
  con --env-file: nextdns.env, n8n.env, jdownloader.env, karakeep.env).
  Está marcado con $dkco/kiro-cli/.no-boot y NO debe ir en layers.conf.
  El binario de Kiro CLI vive en /opt/kiro y los venvs en /opt/nextdns-venv y
  /opt/jdownloader-venv (fuera de /home/kiro porque el volumen data/ lo taparía).
  data/ debe ser chown 1000:1000. Guía completa en docs/services/kiro-cli-guide.md.
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
(`rclone-rcd`), NextDNS multi-cuenta, gestión de workflows de **n8n**
(`czlonkowski/n8n-mcp`), control de descargas con **JDownloader** (`proyec_jdw2`)
y gestión de bookmarks con **Karakeep** (`@karakeep/mcp`). Se eligió Docker por
aislamiento total: borrado sin residuos y arranque **bajo demanda** (no permanente).

## Estructura

```
/docker/kiro-cli/
├── Dockerfile              ← Debian + Node + Kiro CLI (/opt/kiro) + uv + venvs Python 3.14
├── compose.yml             ← network_mode: host, stdin_open/tty, volumen ./data
├── .no-boot                ← marcador: excluido del arranque escalonado
├── nextdns.env             ← secretos NextDNS (chmod 600)
├── n8n.env                 ← N8N_API_URL + N8N_API_KEY para el MCP de n8n (chmod 600)
├── jdownloader.env         ← Credenciales My.JDownloader y NopeCHA (chmod 600)
├── karakeep.env            ← KARAKEEP_API_ADDR + KARAKEEP_API_KEY (chmod 600)
├── bin/                    ← Scripts del servicio (kiro, mcp-build)
│   ├── kiro
│   └── mcp-build
└── data/                   ← $HOME del contenedor (uid 1000): login, .kiro/settings, steering
    └── .kiro/
        ├── settings/
        │   ├── mcp_tools/  ← Trozos JSON individuales por MCP
        │   ├── mcp.json    ← Combinado generado por mcp-build
        │   └── permissions.yaml
        └── steering/
```

## Configuración importante

- **NO es un servicio de red** — no expone puertos; los MCP hablan por stdio.
- Se lanza con el wrapper `$aadm/.local/bin/kiro` (fuerza `--v3`, inyecta la pass de
  rclone desde `$dkco/rclone-rcd/.env` y las credenciales desde sus respectivos `.env`).
- Permisos V3 en `data/.kiro/settings/permissions.yaml` (allow/ask por capacidad MCP).
- Config MCP en `data/.kiro/settings/mcp_tools/*.json` ensamblada con `mcp-build`.
- Red `network_mode: host` para alcanzar `127.0.0.1:5572` (rclone-rcd), `192.168.1.200:5678` (n8n)
  y `192.168.1.200:3400` (karakeep) sin socket Docker.
- Guía operativa completa en `docs/services/kiro-cli-guide.md`.
