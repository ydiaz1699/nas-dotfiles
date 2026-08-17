# Node-RED — Guía Operativa

> **Puerto:** 1880  
> **Imagen:** nodered/node-red:latest  
> **Red:** iot_net  
> **Tipo:** Docker container

---

## Qué es

Plataforma visual de automatización basada en flujos. Permite conectar
MQTT (EMQX), Home Assistant, APIs REST, bases de datos y servicios
con drag & drop.

---

## Instalación

```bash
mkdir -p $dkco/node-red/data
touch $dkco/node-red/.env
dk node-red && svc up node-red
```

---

## Configuración

- Flujos se editan en la web UI: `http://192.168.1.200:1880`
- Se guardan automáticamente en `/data/flows.json`
- Paquetes npm se instalan desde la UI (Manage Palette)

---

## Conexión con EMQX (MQTT)

Node-RED y EMQX están en la misma red (`iot_net`), se comunican internamente:

- Broker: `mqtt://emqx:1883` (por nombre de contenedor, no IP)
- Sin auth si `EMQX_ALLOW_ANONYMOUS=true`, o con usuario MQTT si auth habilitada

---

## Backup y recuperación

```bash
svc backup node-red
```

Lo importante: `data/flows.json` + `data/flows_cred.json` + `data/settings.js`

---

## Troubleshooting

### No puede instalar paquetes npm

NO usar `cap_drop: [ALL]` — Node-RED necesita permisos para npm install en runtime.

### No conecta a EMQX

Verificar que ambos están en `iot_net`:
```bash
docker network inspect iot_net | grep -E "node-red|emqx"
```

---

> **Nota:** Guía generada al crear el servicio. Completar con experiencia real.
> Generado: 2026-08-16
