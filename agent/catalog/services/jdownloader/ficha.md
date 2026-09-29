---
id: "jdownloader"
name: "JDownloader 2"
description: "Gestor de descargas JDownloader 2, controlable por MCP (proyec_jdw2) vía My.JDownloader"
image: "jlesage/jdownloader-2:v26.09.1"
category: "descargas"
port_internal: 5800
port_default: 5800
protocol: "http"
needs_proxy: false
needs_db: false
db_type: ""
volumes:
  - "./config:/config"
  - "/NAS/Descargas:/output"
  - "/NAS/USB:/usb"
env_required: []
env_optional:
  - JD_USER_ID=1000
  - JD_GROUP_ID=1000
  - JD_WEB_USER
  - JD_WEB_PASSWORD
healthcheck: '["CMD-SHELL", "nc -z 127.0.0.1 5800 || exit 1"]'
backup_critical: false
backup_paths:
  - "./config"
protected: false
docs_url: "docs/services/jdownloader-guide.md"
aliases:
  - jdownloader
  - jd
  - jd2
  - descargas
  - downloader
notes: "Control por MCP propio proyec_jdw2 (habla con la nube My.JDownloader, no con el contenedor por LAN). Requiere vincular la cuenta My.JDownloader una vez por la GUI web (:5800) y apuntar el Device Name (= JD_DEVICE_NAME del MCP). Dos destinos: /output (fijo, /NAS/Descargas) y /usb (/NAS/USB, con bind propagation rshared para ver USBs del automount). jlesage NO trae healthcheck.sh → se usa nc al 5800. memory 2g sobreescribe el default de _common.yml. Puerto 3129 (Direct Connection LAN) comentado; no necesario en modo relay/nube. Usa env_file: [../.env, .env] para heredar SERVER_IP y TZ."
networks: []
ports:
  web: 5800
resources:
  memory_limit: "2g"
volume_propagation:
  "/usb": "rshared"
---

# JDownloader 2

## Qué es

Gestor de descargas JDownloader 2 en contenedor (`jlesage/jdownloader-2`), con GUI
web por noVNC en el puerto 5800. Se controla de forma automatizada con el MCP propio
`proyec_jdw2` (github.com/ydiaz1699/proyec_jdw2, 78 tools + auto-solver de captchas)
a través de la nube My.JDownloader.

## Estructura

```
/docker/jdownloader/
├── compose.yml
├── .env                    ← JD_USER_ID/JD_GROUP_ID (permisos 600)
└── config/                 ← estado, config y SESIÓN My.JDownloader

/NAS/Descargas/             ← destino fijo (crear antes; chown al UID del contenedor)
/NAS/USB/                   ← destino en USB (ya existe por el automount)
```

Hereda variables globales de `$dkco/.env` (SERVER_IP, TZ) via:
```yaml
env_file:
  - ../.env      # global
  - .env         # locales
```

## Arquitectura de control

El MCP `proyec_jdw2` habla con la **nube My.JDownloader** (modo relay), NO con el
contenedor por la red local. El contenedor y el MCP se conectan a la misma cuenta.
Por eso el MCP funciona desde cualquier sitio con internet (incluido Kiro CLI en el
NAS) sin depender de la LAN privada.

## Dos destinos de descarga

| Host | Contenedor | Propagación | Uso |
|------|-----------|-------------|-----|
| `/NAS/Descargas` | `/output` | — | destino FIJO permanente |
| `/NAS/USB` | `/usb` | **rshared** | destino en USB, para mover |

El destino por descarga se elige desde el MCP con `download_path` en `jd_add_links`
o con `jd_set_download_directory`.

## Setup inicial

```bash
mkdir -p $dkco/jdownloader/config
mkdir -p /NAS/Descargas
```

Luego vincular My.JDownloader una vez por la GUI (`http://${SERVER_IP}:5800` →
Settings → My.JDownloader → email/pass → apuntar Device Name).

## Puertos

| Puerto | Protocolo | Descripción |
|--------|-----------|-------------|
| 5800   | HTTP      | GUI web (noVNC) |
| 3129   | TCP       | (comentado) MyJDownloader Direct Connection LAN — solo si se usa modo directo |

## .env

```bash
JD_USER_ID=1000
JD_GROUP_ID=1000
# JD_WEB_USER=__pega_aqui__
# JD_WEB_PASSWORD=__pega_aqui__
```

## Notas

- `KEEP_APP_RUNNING=1` relanza JDownloader si se cae (uso headless/MCP).
- `/NAS/Descargas` debe existir y ser escribible por `JD_USER_ID:JD_GROUP_ID`.
- Healthcheck con `nc` al 5800 (jlesage no trae healthcheck.sh).
- Auth web opcional: `WEB_AUTHENTICATION` + `WEB_AUTHENTICATION_ALLOW_INSECURE` si se
  expone el :5800 en LAN por HTTP plano.
- Arranque escalonado: Capa 5 de layers.conf (junto a filebrowser).
