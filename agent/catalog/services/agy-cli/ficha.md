---
id: "agy-cli"
name: "Antigravity CLI (contenedor bajo demanda)"
description: "Google Antigravity CLI (agy) en contenedor aislado para consumir MCPs (rclone, nextdns, n8n, jdownloader, karakeep) desde el NAS"
image: "agy-cli-nas:local"
category: "desarrollo"
port_internal: 0
port_default: 0
protocol: "stdio"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./data:/home/agy"
env_required: []
env_optional: []
healthcheck: 'ninguno (contenedor interactivo, no servicio de red)'
backup_critical: false
backup_paths:
  - "./data"
protected: false
runtime_status: runtime-verified
target_status: cataloged
docs_url: "docs/services/agy-cli-guide.md"
notes: >
  SERVICIO BAJO DEMANDA — NO arranca en el boot. Es un contenedor INTERACTIVO
  (stdin_open + tty), se lanza con `docker run -it` vía el wrapper
  $aadm/.local/bin/agy-nas (network_mode: host, inyecta secretos desde .env
  con --env-file: nextdns.env, n8n.env, jdownloader.env, karakeep.env, gemini.env).
  Marcado con $dkco/agy-cli/.no-boot y NO debe ir en layers.conf.
  El binario de agy vive en /opt/agy/bin y los venvs en /opt/nextdns-venv y
  /opt/jdownloader-venv (fuera de /home/agy porque el volumen data/ lo taparía).
  data/ debe ser chown 1000:1000. Guía completa en docs/services/agy-cli-guide.md.
networks: []
ports: {}
resources:
  memory_limit: "1g"
  memory_reservation: "128m"
security_extra: {}
---

# Antigravity CLI (contenedor bajo demanda)

## Qué es

Contenedor aislado que corre **Google Antigravity CLI (`agy`)** para operar y administrar
el NAS por lenguaje natural con servidores **MCP**: control total de rclone
(`rclone-rcd`), NextDNS multi-cuenta, gestión de workflows de **n8n**,
gestión de descargas con **JDownloader** y marcadores con **Karakeep**.
Se ejecuta en Docker por aislamiento total: arranque bajo demanda y cero residuos en el host.

## Estructura

```
/docker/agy-cli/
├── Dockerfile              ← Debian + Node + Antigravity CLI (/opt/agy) + uv + venvs Python 3.14
├── compose.yml             ← network_mode: host, stdin_open/tty, volumen ./data
├── .no-boot                ← marcador: excluido del arranque escalonado
├── nextdns.env             ← secretos NextDNS (chmod 600)
├── n8n.env                 ← N8N_API_URL + N8N_API_KEY para n8n (chmod 600)
├── jdownloader.env         ← Credenciales My.JDownloader y NopeCHA (chmod 600)
├── karakeep.env            ← KARAKEEP_API_ADDR + KARAKEEP_API_KEY (chmod 600)
├── gemini.env              ← GEMINI_API_KEY opcional para auth headless (chmod 600)
├── bin/                    ← Scripts del servicio (agy-nas, mcp-build)
│   ├── agy-nas
│   └── mcp-build
└── data/                   ← $HOME del contenedor (uid 1000: agy):
    └── .gemini/
        └── antigravity-cli/
            ├── settings.json   ← Generado por mcp-build con todos los MCPs
            └── mcp_tools/      ← Trozos modulares
```

## Configuración importante

- **NO es un servicio de red** — los MCPs se comunican por stdio o HTTP LAN directo.
- Se lanza con el wrapper `$aadm/.local/bin/agy-nas` (inyecta contraseñas vía `.env`).
- Red `network_mode: host` para alcanzar `127.0.0.1:5572` (rclone), `192.168.1.200:5678` (n8n)
  y `192.168.1.200:3400` (karakeep) sin Docker socket.
- Ensamblado automático de configuración MCP con `mcp-build`.
- Guía operativa completa en `docs/services/agy-cli-guide.md`.
