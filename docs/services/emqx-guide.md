# EMQX — Guía Operativa Completa

> **Puerto MQTT:** 1883  
> **Puerto Dashboard:** 18083  
> **Imagen:** emqx/emqx:5.8.3  
> **Red:** iot_net, db_net  
> **Instalado por:** DebMenux (`scripts/services/emqx.sh`)  
> **Tipo:** Docker container

---

## Índice

1. [Qué es EMQX](#qué-es-emqx)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Puertos y protocolos](#puertos-y-protocolos)
5. [Dashboard web](#dashboard-web)
6. [Temas MQTT y estructura](#temas-mqtt-y-estructura)
7. [Clientes MQTT](#clientes-mqtt)
8. [Autenticación y ACLs](#autenticación-y-acls)
9. [Integración con ESPHome](#integración-con-esphome)
10. [Integración con Home Assistant](#integración-con-home-assistant)
11. [Integración con Node-RED](#integración-con-node-red)
12. [Integración con Homepage](#integración-con-homepage)
13. [Backup y recuperación](#backup-y-recuperación)
14. [Troubleshooting](#troubleshooting)

---

## Qué es EMQX

EMQX es un broker MQTT distribuido de alto rendimiento diseñado para IoT.
Soporta MQTT 5.0, MQTT sobre WebSocket, SSL/TLS, y un dashboard web para
monitorear dispositivos y conexiones en tiempo real.

**Casos de uso en el NAS:**
- Hub central de mensajería MQTT para dispositivos ESP32/ESP8266 (via ESPHome)
- Integración bidireccional con Home Assistant para automatizaciones
- Orquestación de flujos IoT con Node-RED
- Dashboard de monitoreo de dispositivos conectados

**Por qué EMQX y no Mosquitto:**
- Dashboard web integrado (no necesita plugin externo)
- Soporte nativo de clustering (escalabilidad futura)
- Mejor manejo de sesiones persistentes y QoS 2
- Reglas de enrutamiento integradas (sin necesidad de Node-RED para cosas simples)

---

## Instalación

### Prerrequisitos

```bash
# 1. Crear directorios
mkdir -p $dkco/emqx/data/{data,log}

# 2. Crear redes (si no existen)
docker network create iot_net 2>/dev/null || true
docker network create db_net 2>/dev/null || true
```

### Generar secretos

```bash
# 3. Crear .env con secretos
cat > $dkco/emqx/.env <<'EOF'
EMQX_NODE_COOKIE=__pega_aqui__
EMQX_DASHBOARD_USER=admin
EMQX_DASHBOARD_PASSWORD=__pega_aqui__
EMQX_ALLOW_ANONYMOUS=false
EMQX_PORT_MQTT=1883
EMQX_PORT_MQTTS=8883
EMQX_PORT_WS=8083
EMQX_PORT_WSS=8084
EMQX_PORT_DASHBOARD=18083
EOF

# 4. Generar valores reales para los secretos
COOKIE=$(openssl rand -hex 32)
PASS=$(openssl rand -base64 18 | tr -d '/+=')
sed -i "0,/__pega_aqui__/{s/__pega_aqui__/${COOKIE}/}" $dkco/emqx/.env
sed -i "0,/__pega_aqui__/{s/__pega_aqui__/${PASS}/}" $dkco/emqx/.env

# 5. Asegurar permisos
chmod 600 $dkco/emqx/.env
```

### Levantar servicio

```bash
# 6. Copiar compose.yml (del catálogo o crear manualmente)
dk emqx && svc up emqx
```

### Verificar

```bash
# Healthcheck
docker exec emqx emqx ctl status
# Debe responder: Node 'emqx@emqx.iot_net' 5.8.3 is started

# Dashboard accesible
curl -s http://192.168.1.200:18083/api/v5/status
```

---

## Configuración

### Estructura de archivos

```
/docker/emqx/
├── compose.yml
├── .env                    ← secretos (permisos 600)
└── data/
    ├── data/               ← BD interna (mnesia), sesiones, reglas, auth
    └── log/                ← logs del broker (json-file via Docker)
```

### Variables de entorno

#### Requeridas (.env local)

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `EMQX_NODE_COOKIE` | `a1b2c3...` (hex 64 chars) | Token para clustering |
| `EMQX_DASHBOARD_USER` | `admin` | Usuario del dashboard web |
| `EMQX_DASHBOARD_PASSWORD` | `s3cr3t` | Password del dashboard |
| `EMQX_ALLOW_ANONYMOUS` | `false` | Conexiones sin auth |
| `EMQX_PORT_MQTT` | `1883` | Puerto MQTT principal |
| `EMQX_PORT_MQTTS` | `8883` | Puerto MQTT + TLS |
| `EMQX_PORT_WS` | `8083` | Puerto WebSocket MQTT |
| `EMQX_PORT_WSS` | `8084` | Puerto WebSocket + TLS |
| `EMQX_PORT_DASHBOARD` | `18083` | Puerto dashboard admin |

#### Heredadas del global (../.env)

- `SERVER_IP` — usado en labels de Homepage
- `TZ` — timezone

#### Configuración en el compose (no requieren .env)

| Variable compose | Valor | Descripción |
|-----------------|-------|-------------|
| `EMQX_NODE__NAME` | `emqx@emqx.iot_net` | Nombre del nodo Erlang |
| `EMQX_NODE__ROLE` | `core` | Rol (core o replicant) |
| `EMQX_CLUSTER__DISCOVERY_STRATEGY` | `manual` | Sin auto-discovery (nodo único) |
| `EMQX_LOG__CONSOLE_HANDLER__LEVEL` | `warning` | Nivel de log (reducir ruido) |
| `EMQX_MQTT__SESSION_EXPIRY_INTERVAL` | `1h` | Cuánto duran las sesiones offline |
| `EMQX_MQTT__MAX_TOPIC_LEVELS` | `7` | Máx niveles en topic (home/piso1/sala/luz/1/status/json) |

### Anchors del compose

El compose usa anchors YAML para estandarización:

- `x-common-env` — TZ compartido
- `x-common-ports` — todos los puertos con variables
- `x-healthcheck-defaults` — healthcheck base (30s interval, 5 retries)
- `x-security-defaults` — no-new-privileges + ulimits nofile
- `x-logging-defaults` — json-file, 10m × 3 rotaciones
- `x-resource-defaults` — memory: 1g limit, 256m reservation

---

## Puertos y protocolos

| Puerto | Protocolo | Descripción | Expuesto a |
|--------|-----------|-------------|------------|
| 1883 | MQTT | Conexiones MQTT sin TLS | LAN |
| 8883 | MQTTS | MQTT con TLS (certificado) | LAN (futuro: WAN) |
| 8083 | WS | MQTT sobre WebSocket | LAN |
| 8084 | WSS | WebSocket + TLS | LAN |
| 18083 | HTTP | Dashboard de administración | LAN |

**Nota:** Todos los puertos se exponen al host. El dashboard (18083) está
expuesto en LAN intencionalmente — no restringido a localhost — porque se
accede frecuentemente desde otros equipos para monitoreo.

---

## Dashboard web

### Acceso

- URL: `http://192.168.1.200:18083`
- Usuario: valor de `EMQX_DASHBOARD_USER` (default: `admin`)
- Password: valor de `EMQX_DASHBOARD_PASSWORD`

### Funcionalidades principales

| Sección | Para qué |
|---------|----------|
| **Overview** | Conexiones activas, mensajes/s, subscripciones |
| **Clients** | Lista de dispositivos conectados con ID, IP, protocolo |
| **Topics** | Temas activos con métricas de publicación/suscripción |
| **Subscriptions** | Quién está suscrito a qué |
| **Authentication** | Gestionar bases de datos de auth |
| **Authorization** | ACLs y reglas de autorización |
| **Rule Engine** | Reglas de enrutamiento (SQL-like) |
| **Alarms** | Alertas del sistema (memoria, conexiones) |

### Cambiar password del dashboard

```bash
docker exec -it emqx emqx ctl admins passwd admin NUEVO_PASSWORD
```

---

## Temas MQTT y estructura

### Convención de topics para el NAS

```
home/<ubicación>/<dispositivo>/<tipo>/<acción>

Ejemplos:
  home/sala/esp32_01/temperature/state       ← sensor reporta temp
  home/sala/esp32_01/light/command            ← HA envía comando
  home/sala/esp32_01/light/state              ← dispositivo reporta estado
  home/cocina/sensor_gas/alarm/state          ← alerta de gas
  home/entrada/timbre/button/state            ← timbre presionado
```

### Topics del sistema

| Topic | Quién publica | Quién suscribe |
|-------|---------------|----------------|
| `$SYS/brokers/emqx@emqx.iot_net/#` | EMQX (interno) | Dashboard, monitoreo |
| `home/+/+/+/state` | Dispositivos ESP | Home Assistant |
| `home/+/+/+/command` | Home Assistant | Dispositivos ESP |
| `homeassistant/+/+/config` | ESPHome (discovery) | Home Assistant |

### Wildcard MQTT

- `+` = un nivel: `home/+/temperature` → cualquier ubicación
- `#` = todos los niveles: `home/#` → todo bajo home

---

## Clientes MQTT

### Probar desde CLI (mosquitto_pub/sub)

```bash
# Instalar herramientas (en el NAS o cualquier PC)
apt install mosquitto-clients

# Publicar un mensaje
mosquitto_pub -h 192.168.1.200 -p 1883 \
    -t "home/test/hello" -m "Hola desde CLI"

# Suscribirse (escuchar)
mosquitto_sub -h 192.168.1.200 -p 1883 -t "home/#" -v
```

### Probar desde el dashboard

Dashboard → **Topics** → sección "Publish" → escribir topic + payload → Send.

### MQTT Explorer (GUI)

App de escritorio para explorar topics visualmente:
- Descargar: https://mqtt-explorer.com/
- Conectar a `192.168.1.200:1883`
- Ver árbol de topics en tiempo real

---

## Autenticación y ACLs

### Estado actual: anonymous = false

Con `EMQX_ALLOW_ANONYMOUS=false`, todos los clientes necesitan autenticación.

### Crear usuarios MQTT (via dashboard)

1. Dashboard → **Access Control** → **Authentication**
2. Crear base de datos: "Built-in Database"
3. Agregar usuarios:

| Username | Para qué | Permisos |
|----------|----------|----------|
| `esphome` | Dispositivos ESP32 | pub/sub `home/#` |
| `homeassistant` | HA MQTT integration | pub/sub `home/#`, `homeassistant/#` |
| `nodered` | Node-RED flows | pub/sub `#` (administrador) |

### Crear usuarios via CLI

```bash
docker exec -it emqx emqx ctl users add esphome PASSWORD_ESP
docker exec -it emqx emqx ctl users add homeassistant PASSWORD_HA
```

### ACLs (Authorization)

Dashboard → **Access Control** → **Authorization** → Built-in Database:

```
# ESPHome: solo topics de dispositivos
{allow, {user, "esphome"}, publish, "home/+/+/+/state"}.
{allow, {user, "esphome"}, subscribe, "home/+/+/+/command"}.

# Home Assistant: todo
{allow, {user, "homeassistant"}, all, "#"}.
```

---

## Integración con ESPHome

### En la configuración del dispositivo ESP (esphome YAML)

```yaml
# device.yaml (en $dkco/esphome/config/)
mqtt:
  broker: 192.168.1.200
  port: 1883
  username: esphome
  password: !secret mqtt_password
  topic_prefix: home/sala/esp32_01
  discovery: true    # Auto-descubrimiento en HA
  discovery_prefix: homeassistant
```

### Cómo funciona el discovery

1. ESPHome publica config en `homeassistant/sensor/esp32_01_temperature/config`
2. Home Assistant (suscrito a `homeassistant/#`) detecta el dispositivo automáticamente
3. El sensor aparece en HA sin configuración manual

---

## Integración con Home Assistant

### Configurar integración MQTT en HA

1. Settings → Devices & Services → Add Integration → **MQTT**
2. Broker: `192.168.1.200`
3. Port: `1883`
4. Username: `homeassistant`
5. Password: (el que configuraste en EMQX)
6. Discovery: ✅ Enable

### Verificar conexión

Developer Tools → MQTT → Listen to topic → `#` → Start Listening

### Publicar desde HA (automatización)

```yaml
- action: mqtt.publish
  data:
    topic: "home/sala/esp32_01/light/command"
    payload: "ON"
    qos: 1
```

---

## Integración con Node-RED

### Nodo MQTT en Node-RED

1. Agregar nodo **mqtt in** o **mqtt out**
2. Server: `emqx` (nombre del contenedor — ambos en `iot_net`)
3. Port: `1883`
4. Username: `nodered`
5. Password: (la configurada)

> **Nota:** Usar el nombre del contenedor (`emqx`) como host, NO la IP.
> Ambos servicios están en `iot_net` y se resuelven por DNS interno de Docker.

### Ejemplo de flujo

```
[mqtt in: home/+/+/temperature/state] → [function: filtrar >40°C] → [mqtt out: home/alerts/temperature]
```

---

## Integración con Homepage

Labels en el compose (auto-descubrimiento):

```yaml
labels:
  - homepage.group=IoT
  - homepage.name=EMQX
  - homepage.icon=emqx
  - homepage.href=http://${SERVER_IP}:${EMQX_PORT_DASHBOARD}
  - homepage.description=Broker MQTT para IoT
```

---

## Backup y recuperación

### Qué respaldar

| Path | Contenido | Crítico |
|------|-----------|:-------:|
| `$dkco/emqx/data/data/` | BD interna (users, ACLs, reglas, sesiones) | ✅ |
| `$dkco/emqx/.env` | Secretos (cookie, passwords) | ✅ |
| `$dkco/emqx/compose.yml` | Configuración del servicio | ✅ |

### Qué NO respaldar

- `$dkco/emqx/data/log/` — logs rotativos, se regeneran

### Backup

```bash
svc backup emqx
```

### Recuperación

```bash
# 1. Crear directorios
mkdir -p $dkco/emqx/data/{data,log}

# 2. Restaurar backup
svc restore emqx

# 3. Verificar .env tiene los secretos correctos
cat $dkco/emqx/.env

# 4. Levantar
svc up emqx

# 5. Verificar
docker exec emqx emqx ctl status
```

### Exportar configuración (portable)

```bash
# Exportar usuarios y ACLs del dashboard
docker exec emqx emqx ctl data export /opt/emqx/data/export.json
docker cp emqx:/opt/emqx/data/export.json ./emqx-export.json
```

---

## Troubleshooting

### EMQX no arranca

```bash
# Ver logs
svc logs emqx

# Error común: "unable to start distribution"
# Causa: EMQX_NODE_COOKIE cambió entre reinicios
# Solución: borrar datos viejos y reiniciar limpio
rm -rf $dkco/emqx/data/data/mnesia
svc restart emqx
```

### Dashboard no carga (18083)

```bash
# Verificar que el contenedor está healthy
docker inspect emqx --format='{{.State.Health.Status}}'

# Si está "starting" por mucho tiempo:
docker logs emqx --tail=50

# Error de ulimits:
# "Too many open files" → verificar que compose tiene ulimits nofile: 1048576
```

### Dispositivo ESP no conecta

1. Verificar que `EMQX_ALLOW_ANONYMOUS=false` y el dispositivo tiene credenciales
2. Verificar que el ESP puede alcanzar `192.168.1.200:1883` (no bloqueado por firewall)
3. En el dashboard: **Clients** → ver si aparece el client ID del ESP
4. Si aparece y se desconecta inmediatamente: credenciales incorrectas

### Mensajes no llegan a HA

1. Verificar que HA está conectado: Settings → Integrations → MQTT → "Connected"
2. Verificar topic: Developer Tools → MQTT → Listen → `home/#`
3. Si discovery no funciona: verificar que ESPHome publica en `homeassistant/` prefix

### Alta memoria / muchas conexiones

```bash
# Ver conexiones activas
docker exec emqx emqx ctl broker stats | grep connections

# Ver uso de memoria
docker exec emqx emqx ctl broker stats | grep memory

# Si hay leak: reiniciar sesiones expiradas
docker exec emqx emqx ctl sessions clean
```

### Error "mnesia: already running"

```bash
# Causa: datos corruptos después de kill forzado
docker stop emqx
rm -rf $dkco/emqx/data/data/mnesia/emqx@emqx.iot_net
svc up emqx
# ⚠️ Esto borra usuarios/ACLs — reimportar con data import
```

---

## Notas de operación

- **ulimits:** El compose requiere `nofile: 1048576` para manejar miles de conexiones MQTT
- **Clustering:** Configurado como nodo único (`discovery_strategy: manual`). Para clustering
  futuro: cambiar a `static` y agregar nodos con `EMQX_CLUSTER__STATIC__SEEDS`
- **TLS:** Los puertos 8883/8084 están expuestos pero sin certificados configurados aún.
  Para habilitarlos: montar certificados en `/opt/emqx/etc/certs/` y configurar listeners
- **Session expiry:** Las sesiones de dispositivos offline se mantienen 1h. Si un ESP se
  desconecta, EMQX guarda sus mensajes QoS 1/2 durante 1 hora
- **Log level:** Configurado en `warning` para reducir ruido. Cambiar a `info` o `debug`
  para troubleshooting temporal: `docker exec emqx emqx ctl log primary-level info`
