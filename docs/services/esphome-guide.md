# ESPHome — Guía Operativa Completa

> **Puerto:** 6052  
> **Imagen:** ghcr.io/esphome/esphome:latest  
> **Red:** network_mode: host  
> **Instalado por:** DebMenux (`scripts/services/esphome.sh`)  
> **Tipo:** Docker container (privileged)  
> **Dashboard:** ESPHome **Device Builder** (desde ESPHome 2026.6.0; reemplaza al
> dashboard clásico). Ver [Dashboard web](#dashboard-web-device-builder).

> **¿Organizar la configuración de los dispositivos?** Esta guía cubre la
> instalación y operación del **servicio** ESPHome. Para organizar los YAML de los
> **dispositivos** ESP32/ESP8266 de forma modular (patrón `packages`, IP fija, red,
> alta en Home Assistant) ver [`esphome-device-config.md`](esphome-device-config.md).
> Es opcional: puedes usar la configuración por defecto (un solo YAML por dispositivo).
>
> **Proyecto en curso (ESP32 `pueba` + Sonoff):** estado real, qué funciona, errores
> ya resueltos y el pendiente del estado inicial del indicador están en
> [`esphome-pueba-handoff.md`](esphome-pueba-handoff.md) (handoff autocontenido para
> retomar en un chat nuevo sin contexto).
>
> **Pendientes detectados en revisión:** ver
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas) (no aplicadas, a
> decisión del usuario).

---

## Índice

1. [Qué es ESPHome](#qué-es-esphome)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Dashboard web (Device Builder)](#dashboard-web-device-builder)
5. [Crear un nuevo dispositivo](#crear-un-nuevo-dispositivo)
6. [Flashear dispositivos](#flashear-dispositivos)
7. [Integración con EMQX (MQTT)](#integración-con-emqx-mqtt)
8. [Integración con Home Assistant](#integración-con-home-assistant)
9. [Integración con Homepage](#integración-con-homepage)
10. [Backup y recuperación](#backup-y-recuperación)
11. [Troubleshooting](#troubleshooting)
12. [Notas de operación](#notas-de-operación)
13. [Mejoras pendientes (detectadas, no aplicadas)](#mejoras-pendientes-detectadas-no-aplicadas)

---

## Qué es ESPHome

ESPHome es una plataforma para gestionar dispositivos ESP32/ESP8266 mediante
archivos de configuración YAML. Permite:

- Definir sensores, actuadores, y comunicación en YAML (sin programar en C/Arduino)
- Compilar y flashear firmware OTA (Over-The-Air) o por USB serial
- Dashboard web (Device Builder) para ver estado de dispositivos y re-flashear
- Auto-descubrimiento en Home Assistant (API nativa o MQTT)

**Casos de uso en el NAS:**
- Compilar y subir firmware a ESP32 desde cualquier PC via web
- Monitorear dispositivos ESP conectados
- Actualizar OTA todos los dispositivos desde un solo lugar
- Crear configuraciones reutilizables con packages/includes

---

## Instalación

### Prerrequisitos

```bash
# 1. Crear directorios
mkdir -p $dkco/esphome/config

# 2. Verificar acceso a USB (si vas a flashear por serial)
ls -la /dev/ttyUSB0
# Si no existe, conectar un ESP32 via USB al NAS
```

### Levantar servicio

```bash
# 3. Copiar compose.yml (del catálogo o crear)
# El compose usa network_mode: host y privileged: true

# 4. Levantar
dk esphome && svc up esphome
```

### Verificar

```bash
# Dashboard accesible
curl -s http://192.168.1.200:6052 | head -5
# Debe devolver HTML del dashboard

# Versión de ESPHome realmente en uso (anótala: es la "versión verificada")
docker exec esphome esphome version
```

> Con `image: …:latest`, la versión cambia en cada `svc update esphome`. Compara la
> salida de `esphome version` con la versión con la que se verificó el patrón de
> `packages` (2026.6.3) antes de flashear tras una actualización. Ver
> [Notas de operación](#notas-de-operación).

---

## Configuración

### Estructura de archivos

```
/docker/esphome/
├── compose.yml
└── config/                     ← montado en /config del contenedor
    ├── .esphome/               ← cache de compilación (auto-generado; fuera de git)
    ├── pueba.yaml              ← dispositivo real (solo substitutions + packages)
    ├── common/                 ← packages compartidos (ver esphome-device-config.md)
    │   ├── base.yaml
    │   ├── wifi.yaml
    │   └── diagnostics.yaml
    ├── boards/                 ← hardware de la placa
    │   └── esp32.yaml
    ├── modules/                ← bloques por responsabilidad
    │   ├── entradas.yaml
    │   └── touch_switch.yaml
    └── secrets.yaml            ← passwords WiFi, API, OTA (nunca a git)
```

> Los nombres `esp32_sala` / `esp32_cocina` que aparecen más abajo son **ejemplos
> ilustrativos** (formato clásico de un solo YAML). El dispositivo real hoy es
> `pueba`, con `packages` repartidos en `common/`, `boards/` y `modules/` (ver
> [`esphome-device-config.md`](esphome-device-config.md)). Si algún día se usa MQTT,
> se puede añadir `common/mqtt.yaml` (no existe todavía).

### compose.yml explicado

```yaml
services:
  esphome:
    image: ghcr.io/esphome/esphome:latest
    container_name: esphome
    restart: on-failure:5
    network_mode: host          # Necesario para mDNS (descubrimiento de ESPs)
    privileged: true            # Necesario para acceso a USB serial
    volumes:
      - ./config:/config:rw     # Configuraciones YAML
      - /etc/localtime:/etc/localtime:ro
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0   # USB-UART para flash serial
    command: dashboard /config
```

**¿Por qué `network_mode: host`?**
- ESPHome necesita acceso directo a la red LAN para descubrir dispositivos via mDNS
- Sin host mode, no puede detectar ESPs por nombre `.local`
- El puerto 6052 se expone directamente (no configurable via variable)
- Ojo: el mDNS **no cruza entre subredes** (ver doble NAT en
  [`esphome-device-config.md`](esphome-device-config.md#red-ip-fija-y-en-qué-subred-vive-la-placa)).

**¿Por qué `privileged: true`?**
- Acceso a `/dev/ttyUSB0` para programación serial (primer flash)
- Sin esto, el flash USB falla con "Permission denied"

**¿Y `command: dashboard /config`?**
- Desde ESPHome 2026.6.0 la imagen oficial incluye el Device Builder y lo arranca
  como dashboard con ese mismo comando (es el comando por defecto de la imagen), así
  que el compose **sigue siendo válido sin cambios**.

### secrets.yaml

```yaml
# $dkco/esphome/config/secrets.yaml   — NUNCA a git
wifi_ssid: "MI_RED_WIFI"                    # red del NAS (Huawei B622, 192.168.1.x)
wifi_password: "mi_password_wifi"
wifi_fallback: "password_ap_recuperacion"   # mínimo 8 caracteres
api_encryption_key: "generada_por_esphome"  # base64 de 32 bytes: openssl rand -base64 32
esp32_pruebas_ota_password: "password_para_ota"

# Solo si usas MQTT (ver sección EMQX):
# mqtt_user: "esphome"
# mqtt_password: "password_mqtt_en_emqx"
```

> **⚠️ NUNCA commitear secrets.yaml a git.** Debe estar en `.gitignore`, junto con
> `.esphome/`. Los nombres de los secrets deben coincidir con los que usan los YAML
> (hoy `esp32_pruebas_ota_password` en `common/base.yaml`).

---

## Dashboard web (Device Builder)

### Acceso

- URL: `http://192.168.1.200:6052`
- Sin autenticación por defecto (LAN interna)

> **Autenticación (opcional, no verificado en este NAS):** según la documentación
> del paquete `esphome-device-builder`, el Device Builder usa variables de entorno
> con prefijo `ESPHOME_` (`ESPHOME_USERNAME` / `ESPHOME_PASSWORD`), distintas de las
> variables `USERNAME`/`PASSWORD` del dashboard antiguo. Si algún día se expone fuera
> de la LAN, comprobar el nombre exacto en su documentación antes de configurarlo.

### Funcionalidades

La tabla es la del dashboard clásico; el Device Builder ofrece las mismas acciones
con otra interfaz (barra lateral de dispositivos, editor YAML con CodeMirror y
constructor visual de componentes). **Los nombres exactos de los botones pueden
variar** respecto a la tabla — no se han re-verificado en el Device Builder.

| Acción | Descripción |
|--------|-------------|
| **NEW DEVICE** | Wizard para crear config de un ESP nuevo |
| **EDIT** | Editar YAML del dispositivo |
| **INSTALL** | Compilar y flashear (OTA o serial) |
| **LOGS** | Ver output serial/WiFi en tiempo real |
| **VALIDATE** | Verificar YAML sin compilar |
| **CLEAN BUILD** | Limpiar cache de compilación |

### Indicadores de estado

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Dispositivo online (responde a ping) |
| 🔴 Rojo | Offline o sin configurar |
| 🟡 Amarillo | Compilando / Actualizando |

> El Device Builder revalida la configuración en cada guardado. Aun así, "Valid" en
> la interfaz **no sustituye** a revisar la salida resuelta con `esphome config`
> cuando se tocan varios `packages` (listas concatenadas, entidades duplicadas).

---

## Crear un nuevo dispositivo

### Método 1: Wizard del dashboard

1. Dashboard → **NEW DEVICE** → nombre (ej: `esp32_sala`)
2. Seleccionar board: `ESP32 Dev Module` o `ESP8266 (NodeMCU)`
3. Configurar WiFi (o apuntar a secrets.yaml)
4. El wizard crea un YAML básico en `config/esp32_sala.yaml`

### Método 2: YAML manual de un solo archivo

```yaml
# $dkco/esphome/config/esp32_sala.yaml   (ejemplo ilustrativo)
esphome:
  name: esp32-sala
  friendly_name: "ESP32 Sala"

esp32:
  board: esp32dev

# WiFi
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  # IP estática (opcional pero recomendado)
  manual_ip:
    static_ip: 192.168.1.50
    gateway: 192.168.1.1
    subnet: 255.255.255.0

# API para Home Assistant (conexión directa)
api:
  encryption:
    key: !secret api_encryption_key

# OTA para actualizaciones inalámbricas
ota:
  - platform: esphome
    password: !secret esp32_pruebas_ota_password

# Logger (ver logs via WiFi)
logger:
  level: INFO

# MQTT (alternativa a API directa; no hace falta usar ambas — ver tabla
# "Cuándo usar cada método")
mqtt:
  broker: 192.168.1.200
  port: 1883
  username: !secret mqtt_user
  password: !secret mqtt_password
  topic_prefix: home/sala/esp32_01
  discovery: true
  discovery_prefix: homeassistant

# Sensores
sensor:
  - platform: dht
    pin: GPIO4
    temperature:
      name: "Temperatura Sala"
    humidity:
      name: "Humedad Sala"
    update_interval: 60s

# Relé / Luz
switch:
  - platform: gpio
    pin: GPIO5
    name: "Luz Sala"
    id: luz_sala
```

> El dispositivo real `pueba` usa `variant: esp32` + `framework: esp-idf` (sin
> `board:`), validado en ESPHome 2026.6.3. Ajusta `board`/`variant` al hardware real.

### Método 3: modular con `packages` (el que usa `pueba`)

Para más de un dispositivo, o para mantener WiFi/API/OTA/diagnósticos en un solo
sitio, el YAML del dispositivo solo declara `substitutions` + `packages`. Todo el
detalle (estructura `common/`/`boards/`/`modules/`, regla de fusión, `!extend`/`!remove`,
red, alta en HA) está en
[`esphome-device-config.md`](esphome-device-config.md).

---

## Flashear dispositivos

### Primer flash (USB serial — obligatorio)

1. Conectar ESP32 al NAS via cable USB
2. Verificar que aparece: `ls /dev/ttyUSB*`
3. Dashboard → dispositivo → **INSTALL** → opción de conectar el dispositivo por
   USB/serial al equipo donde corre ESPHome (en el dashboard clásico:
   **Plug into this computer**)
4. Seleccionar puerto: `/dev/ttyUSB0`
5. Esperar compilación + upload (~2 min primera vez)

### Flash OTA (inalámbrico — después del primer flash)

1. Dashboard → dispositivo → **INSTALL** → **Wirelessly**
2. ESPHome busca el dispositivo por mDNS (`esp32-sala.local`)
3. Sube firmware por WiFi (~30 seg)

> Si el mDNS no resuelve (subredes distintas, doble NAT), el OTA por nombre falla:
> usar la IP fija del dispositivo (`--device 192.168.1.132` en CLI).

### Flash desde CLI

> `svc exec esphome esphome <subcomando> …` falla porque `svc exec` reinterpreta los
> subcomandos (probadas y fallidas tres variantes; ver
> [`esphome-device-config.md`](esphome-device-config.md#validar-antes-de-flashear)).
> Usar `docker exec` directo:

```bash
# Validar y ver la configuración resuelta (sin compilar)
docker exec esphome esphome config /config/pueba.yaml

# Compilar sin flashear
docker exec esphome esphome compile /config/pueba.yaml

# Flash OTA (preferible por IP fija)
docker exec esphome esphome upload /config/pueba.yaml --device 192.168.1.132

# Flash serial
docker exec esphome esphome upload /config/pueba.yaml --device /dev/ttyUSB0

# Ver logs del dispositivo (no confundir con "svc logs esphome", que son los del servicio)
docker exec -it esphome esphome logs /config/pueba.yaml
```

> Los logs en vivo con `esphome logs` necesitan terminal interactiva: usar
> `docker exec -it`.

---

## Integración con EMQX (MQTT)

### Configuración en el dispositivo

```yaml
# En el YAML del dispositivo
mqtt:
  broker: 192.168.1.200
  port: 1883
  username: esphome
  password: !secret mqtt_password
  topic_prefix: home/sala/esp32_01
  discovery: true
  discovery_prefix: homeassistant
```

### Temas publicados automáticamente

| Topic | Contenido |
|-------|-----------|
| `home/sala/esp32_01/sensor/temperatura_sala/state` | Valor del sensor |
| `home/sala/esp32_01/switch/luz_sala/state` | ON/OFF |
| `home/sala/esp32_01/switch/luz_sala/command` | Recibe comandos |
| `home/sala/esp32_01/status` | online/offline |
| `homeassistant/sensor/esp32_01_temperatura/config` | Discovery para HA |

### Verificar en EMQX dashboard

1. `http://192.168.1.200:18083` → **Clients**
2. Buscar client ID: `esp32-sala` (o el nombre del dispositivo)
3. Debe aparecer como "Connected"

---

## Integración con Home Assistant

### Método 1: API directa (recomendado para pocos dispositivos)

```yaml
# En el YAML del dispositivo — SIN bloque mqtt:
api:
  encryption:
    key: !secret api_encryption_key
```

HA puede descubrir el dispositivo automáticamente via mDNS **si están en la misma
subred**. Con el doble NAT del NAS (placa en `192.168.1.x`, red principal en
`192.168.0.x`) el mDNS no cruza: hacer el **alta manual por IP** (host = IP de la
placa, puerto `6053`, clave de cifrado). Pasos completos en
[`esphome-device-config.md`](esphome-device-config.md#alta-en-home-assistant).

> Si el dispositivo ejecuta acciones de HA (`homeassistant.service` /
> `homeassistant.action`, como el pulsador de `pueba`), hay que **permitirlo** en las
> opciones de la integración ESPHome para esa placa; si no, HA bloquea la acción.

### Método 2: MQTT (recomendado para muchos dispositivos)

Con el bloque `mqtt:` + `discovery: true`, HA auto-descubre sensores via MQTT.
Requiere tener la integración MQTT configurada en HA apuntando a EMQX.

### Cuándo usar cada método

| Criterio | API directa | MQTT |
|----------|:-----------:|:----:|
| Pocos dispositivos (<10) | ✅ | ⚪ |
| Muchos dispositivos (>10) | ⚪ | ✅ |
| Necesitas Node-RED intermedio | ❌ | ✅ |
| Latencia mínima | ✅ | ⚪ |
| Funciona si HA reinicia | ❌ (reconecta) | ✅ (EMQX retiene) |
| Funciona sin HA | ❌ | ✅ |

> Con API directa, las entradas físicas que controlan algo **a través de HA** (el
> pulsador de `pueba` que conmuta el Sonoff) **no funcionan si HA está caído**.

---

## Integración con Homepage

Labels en el compose (auto-descubrimiento):

```yaml
labels:
  - homepage.group=IoT
  - homepage.name=ESPHome
  - homepage.icon=esphome
  - homepage.href=http://${SERVER_IP}:6052
  - homepage.description=Gestión de dispositivos ESP32/ESP8266
  - homepage.widget.type=esphome
  - homepage.widget.url=http://${SERVER_IP}:6052
```

El widget muestra: dispositivos online / offline / total.

---

## Backup y recuperación

### Qué respaldar

| Path | Contenido | Crítico |
|------|-----------|:-------:|
| `$dkco/esphome/config/*.yaml` | Configuraciones de dispositivos | ✅ |
| `$dkco/esphome/config/secrets.yaml` | Passwords WiFi/MQTT/API | ✅ |
| `$dkco/esphome/config/common/` | Packages compartidos | ✅ |
| `$dkco/esphome/config/boards/` | Hardware de las placas | ✅ |
| `$dkco/esphome/config/modules/` | Bloques por responsabilidad | ✅ |

### Qué NO respaldar

- `$dkco/esphome/config/.esphome/` — cache de compilación (se regenera, pesa varios GB)

### Backup

```bash
svc backup esphome
```

> ⚠️ **Verificar el contenido del backup.** `svc backup` respalda **volúmenes
> nombrados**, y `./config` es un **bind mount**: puede que el `.tar.gz` no incluya
> los YAML ni `secrets.yaml`. Comprobarlo listando el archivo generado en
> `$dkco/backups/` (`tar tzf <archivo> | head`). Si no están, usar el respaldo
> manual de abajo.

Respaldo manual explícito (sin la cache):

```bash
mkdir -p $dkco/backups
tar czf $dkco/backups/esphome-config-$(date +%F).tar.gz \
    --exclude=.esphome -C $dkco/esphome config
tar tzf $dkco/backups/esphome-config-$(date +%F).tar.gz | head
```

> El `secrets.yaml` contiene credenciales: el `.tar.gz` debe guardarse con los mismos
> cuidados que el propio secrets (no subirlo a git ni a sitios compartidos).

### Recuperación

```bash
# 1. Crear directorio
mkdir -p $dkco/esphome/config

# 2. Restaurar YAMLs
svc restore esphome    # ← comando no documentado en "svc --help": verificar que existe
# Alternativa manual (con el backup manual de arriba):
# tar xzf $dkco/backups/esphome-config-<fecha>.tar.gz -C $dkco/esphome

# 3. Levantar
svc up esphome

# 4. Primera compilación será lenta (regenera cache)
```

---

## Troubleshooting

### ESPHome dashboard no carga (6052)

```bash
# Verificar que el contenedor corre
svc ps esphome

# Ver logs del servicio
svc logs esphome

# Error común: puerto 6052 ya en uso
ss -tlnp | grep 6052
# Si otro proceso lo usa: matar o cambiar el comando del compose
```

### El contenedor no arranca (y no hay `/dev/ttyUSB0` conectado)

El compose mapea `/dev/ttyUSB0`. Si el adaptador USB no está enchufado, Docker puede
negarse a crear el contenedor (con `restart: on-failure:5` reintenta y se rinde).

```bash
svc logs esphome          # buscar error de dispositivo no encontrado
ls -la /dev/ttyUSB*       # ¿existe el adaptador?
# Opción: conectar el adaptador y svc up esphome; o quitar la línea "devices:"
# del compose si no vas a flashear por USB.
```

### No detecta dispositivos (mDNS)

```bash
# Verificar que network_mode es host
docker inspect esphome --format='{{.HostConfig.NetworkMode}}'
# Debe ser: host

# Ping al dispositivo
ping esp32-sala.local

# Si no resuelve mDNS (subredes distintas / doble NAT), usar IP directa
# y configurar IP estática en el ESP
```

### Flash USB falla ("Permission denied" o "No serial port found")

```bash
# Verificar que el dispositivo USB aparece
ls -la /dev/ttyUSB*

# Si no aparece: desconectar y reconectar el cable USB
# Verificar driver:
dmesg | tail -20 | grep -i usb

# Si aparece pero sin permisos: verificar que compose tiene privileged: true
# Y que devices incluye /dev/ttyUSB0
```

### Compilación falla (out of memory)

```bash
# ESPHome consume mucha RAM al compilar (~1-2GB por dispositivo)
# Ver RAM disponible:
free -h

# Solución: compilar un dispositivo a la vez (no en paralelo)
# O agregar swap si hay poco RAM

# Limpiar cache de compilación:
rm -rf $dkco/esphome/config/.esphome/build/
```

### OTA falla ("Unable to connect")

1. Verificar que el ESP está online (ping a su IP)
2. Verificar que el password OTA coincide con `secrets.yaml`
   (`esp32_pruebas_ota_password` en `pueba`)
3. Verificar que el ESP y el NAS están en la misma subnet
4. Si el ESP cambió de IP: usar IP estática (manual_ip en el YAML) y flashear con
   `--device <IP>` en lugar del nombre `.local`

### "Configuration is valid!" pero algo no cuadra

- Entidades duplicadas en HA: comprobar que cada componente (p. ej. botones
  `restart`/`safe_mode`) está en **un solo** package.
- Nombres tipo "Prueba Prueba …" en HA: el nombre de entidad repite el
  `friendly_name` (ver Mejoras pendientes en
  [`esphome-device-config.md`](esphome-device-config.md#mejoras-pendientes-detectadas-no-aplicadas)).
- Revisar siempre la salida resuelta:
  `docker exec esphome esphome config /config/pueba.yaml`.

### El pulsador / switch no actúa sobre el Sonoff

1. En HA, opciones de la integración ESPHome de la placa: permitir que el
   dispositivo realice acciones de HA.
2. Comprobar que la API está conectada (log: "Cliente conectado a la API").
3. Comprobar que `sonoff_entity` coincide con el `entity_id` real del Sonoff en HA.

### Dispositivo se desconecta constantemente

```yaml
# Agregar al YAML del dispositivo (en pueba: en common/wifi.yaml, mapa único wifi):
wifi:
  # ...
  power_save_mode: none    # Desactivar power save (mejora estabilidad)
  fast_connect: true       # Reconexión rápida

# Si usa MQTT:
mqtt:
  # ...
  keepalive: 60s
  reboot_timeout: 5min    # Reiniciar si pierde conexión >5 min
```

> Si en los logs aparece *"Brownout detector was triggered"*, no es un problema de
> WiFi sino de **tensión**: ver `wifi: output_power: 13dB` y demás medidas en
> [`esphome-device-config.md`](esphome-device-config.md#buenas-prácticas-de-fiabilidad-y-hardware-de-la-faq-oficial).

---

## Notas de operación

- **Compilación lenta:** La primera vez que compilas un dispositivo puede tardar 3-5 min.
  Las siguientes son más rápidas (~30 seg) gracias al cache en `.esphome/`
- **Sin `cap_drop`:** ESPHome necesita privileged para USB y networking avanzado.
  No aplicar restricciones de seguridad (cap_drop, no-new-privileges)
- **Espacio en disco:** El cache de compilación (`.esphome/`) puede crecer a varios GB
  con muchos dispositivos. Limpiar periódicamente si el disco se llena
- **Actualizaciones de imagen:** ESPHome se actualiza frecuentemente y el compose usa
  `:latest`. Antes de `svc update esphome`, anota la versión actual
  (`esphome version`); después, **valida** (`esphome config`) y recompila los
  dispositivos antes de flashear. Si algo falla tras actualizar, fijar la imagen a la
  última versión verificada (2026.6.3) en el compose.
- **Cambios entre versiones:** el changelog de cada versión avisa de deprecaciones
  (p. ej. `homeassistant.service` → `homeassistant.action`, y el dashboard clásico →
  Device Builder en 2026.6.0). Revisarlo al actualizar.
- **USB hotplug:** Si conectas un ESP mientras el contenedor corre, puede no detectarlo.
  Reiniciar el contenedor: `svc restart esphome`

---

## Mejoras pendientes (detectadas, no aplicadas)

Hallazgos de la revisión. **Ninguno está aplicado en el compose ni en el sistema**:
son decisiones del usuario. Marcar cada uno como aplicado/descartado al resolverlo.

| # | Hallazgo | Dónde | Estado |
|---|---|---|---|
| 1 | `image: …:latest` sin versión fija; el patrón se verificó con 2026.6.3 | `compose.yml` | PENDIENTE (fijar `…:2026.6.3` u otra versión verificada tras `esphome version`) |
| 2 | `svc backup` puede no incluir `./config` (bind mount) | procedimiento de backup | PENDIENTE (comprobar con `tar tzf`; si falta, usar el respaldo manual) |
| 3 | `svc restore esphome` no figura en la ayuda documentada de `svc` | recuperación | PENDIENTE (verificar si existe) |
| 4 | Tabla de acciones del dashboard es la del dashboard clásico; no re-verificada en el Device Builder | sección Dashboard | PENDIENTE |
| 5 | Dashboard sin autenticación; el Device Builder usa variables `ESPHOME_USERNAME`/`ESPHOME_PASSWORD` según su documentación | `compose.yml` | PENDIENTE (solo si se expone fuera de la LAN) |
| 6 | El mapeo de `/dev/ttyUSB0` puede impedir arrancar el contenedor sin adaptador conectado | `compose.yml` | PENDIENTE (verificar comportamiento real) |
| 7 | Añadir `.esphome/` además de `secrets.yaml` a `.gitignore` | repo de `config/` | PENDIENTE |
| 8 | `esphome logs` interactivo vía `svc exec`: sin verificar (usar `docker exec -it`) | CLI | PENDIENTE |

---

## Ver también

- [`esphome-device-config.md`](esphome-device-config.md) — organización modular de los
  YAML de dispositivos (`packages`, `common/`/`boards/`/`modules/`, red, alta en HA,
  mejoras pendientes).
- [`../esphome-meta-prompt.md`](../esphome-meta-prompt.md) — meta-prompt para
  **crear o mantener/mejorar** configuraciones ESPHome con cualquier LLM.
- [`esphome-pueba-handoff.md`](esphome-pueba-handoff.md) — estado real del proyecto
  `pueba` + Sonoff.
