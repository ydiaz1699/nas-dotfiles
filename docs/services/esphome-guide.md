# ESPHome — Guía Operativa Completa

> **Puerto:** 6052  
> **Imagen:** ghcr.io/esphome/esphome:latest  
> **Red:** network_mode: host  
> **Instalado por:** DebMenux (`scripts/services/esphome.sh`)  
> **Tipo:** Docker container (privileged)

---

## Índice

1. [Qué es ESPHome](#qué-es-esphome)
2. [Instalación](#instalación)
3. [Configuración](#configuración)
4. [Dashboard web](#dashboard-web)
5. [Crear un nuevo dispositivo](#crear-un-nuevo-dispositivo)
6. [Flashear dispositivos](#flashear-dispositivos)
7. [Integración con EMQX (MQTT)](#integración-con-emqx-mqtt)
8. [Integración con Home Assistant](#integración-con-home-assistant)
9. [Integración con Homepage](#integración-con-homepage)
10. [Backup y recuperación](#backup-y-recuperación)
11. [Troubleshooting](#troubleshooting)

---

## Qué es ESPHome

ESPHome es una plataforma para gestionar dispositivos ESP32/ESP8266 mediante
archivos de configuración YAML. Permite:

- Definir sensores, actuadores, y comunicación en YAML (sin programar en C/Arduino)
- Compilar y flashear firmware OTA (Over-The-Air) o por USB serial
- Dashboard web para ver estado de dispositivos y re-flashear
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
```

---

## Configuración

### Estructura de archivos

```
/docker/esphome/
├── compose.yml
└── config/                     ← montado en /config del contenedor
    ├── .esphome/               ← cache de compilación (auto-generado)
    ├── esp32_sala.yaml         ← configuración de dispositivo
    ├── esp32_cocina.yaml       ← otro dispositivo
    ├── common/                 ← includes compartidos (opcional)
    │   ├── wifi.yaml
    │   ├── mqtt.yaml
    │   └── base.yaml
    └── secrets.yaml            ← passwords WiFi, MQTT, API keys
```

### compose.yml explicado

```yaml
services:
  esphome:
    image: ghcr.io/esphome/esphome:latest
    container_name: esphome
    restart: unless-stopped
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

**¿Por qué `privileged: true`?**
- Acceso a `/dev/ttyUSB0` para programación serial (primer flash)
- Sin esto, el flash USB falla con "Permission denied"

### secrets.yaml

```yaml
# $dkco/esphome/config/secrets.yaml
wifi_ssid: "MI_RED_WIFI"
wifi_password: "mi_password_wifi"
mqtt_user: "esphome"
mqtt_password: "password_mqtt_en_emqx"
api_encryption_key: "generada_por_esphome"
ota_password: "password_para_ota"
```

> **⚠️ NUNCA commitear secrets.yaml a git.** Está en `.gitignore`.

---

## Dashboard web

### Acceso

- URL: `http://192.168.1.200:6052`
- Sin autenticación (LAN interna)

### Funcionalidades

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

---

## Crear un nuevo dispositivo

### Método 1: Wizard del dashboard

1. Dashboard → **NEW DEVICE** → nombre (ej: `esp32_sala`)
2. Seleccionar board: `ESP32 Dev Module` o `ESP8266 (NodeMCU)`
3. Configurar WiFi (o apuntar a secrets.yaml)
4. El wizard crea un YAML básico en `config/esp32_sala.yaml`

### Método 2: YAML manual (recomendado)

```yaml
# $dkco/esphome/config/esp32_sala.yaml
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
    password: !secret ota_password

# Logger (ver logs via WiFi)
logger:
  level: INFO

# MQTT (alternativa a API directa)
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

---

## Flashear dispositivos

### Primer flash (USB serial — obligatorio)

1. Conectar ESP32 al NAS via cable USB
2. Verificar que aparece: `ls /dev/ttyUSB*`
3. Dashboard → dispositivo → **INSTALL** → **Plug into this computer**
4. Seleccionar puerto: `/dev/ttyUSB0`
5. Esperar compilación + upload (~2 min primera vez)

### Flash OTA (inalámbrico — después del primer flash)

1. Dashboard → dispositivo → **INSTALL** → **Wirelessly**
2. ESPHome busca el dispositivo por mDNS (`esp32-sala.local`)
3. Sube firmware por WiFi (~30 seg)

### Flash desde CLI

```bash
# Compilar sin flashear
docker exec esphome esphome compile /config/esp32_sala.yaml

# Flash OTA
docker exec esphome esphome upload /config/esp32_sala.yaml --device esp32-sala.local

# Flash serial
docker exec esphome esphome upload /config/esp32_sala.yaml --device /dev/ttyUSB0

# Ver logs
docker exec esphome esphome logs /config/esp32_sala.yaml
```

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

HA descubre el dispositivo automáticamente via mDNS y se conecta por API nativa.

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
| `$dkco/esphome/config/common/` | Includes compartidos | ✅ |

### Qué NO respaldar

- `$dkco/esphome/config/.esphome/` — cache de compilación (se regenera, pesa varios GB)

### Backup

```bash
svc backup esphome
# Nota: excluir .esphome/ del backup (es cache pesado)
```

### Recuperación

```bash
# 1. Crear directorio
mkdir -p $dkco/esphome/config

# 2. Restaurar YAMLs
svc restore esphome

# 3. Levantar
svc up esphome

# 4. Primera compilación será lenta (regenera cache)
```

---

## Troubleshooting

### ESPHome dashboard no carga (6052)

```bash
# Verificar que el contenedor corre
docker ps | grep esphome

# Ver logs
svc logs esphome

# Error común: puerto 6052 ya en uso
ss -tlnp | grep 6052
# Si otro proceso lo usa: matar o cambiar el comando del compose
```

### No detecta dispositivos (mDNS)

```bash
# Verificar que network_mode es host
docker inspect esphome --format='{{.HostConfig.NetworkMode}}'
# Debe ser: host

# Ping al dispositivo
ping esp32-sala.local

# Si no resuelve mDNS, usar IP directa en el dashboard
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
3. Verificar que el ESP y el NAS están en la misma subnet
4. Si el ESP cambió de IP: usar IP estática (manual_ip en el YAML)

### Dispositivo se desconecta constantemente

```yaml
# Agregar al YAML del dispositivo:
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

---

## Notas de operación

- **Compilación lenta:** La primera vez que compilas un dispositivo puede tardar 3-5 min.
  Las siguientes son más rápidas (~30 seg) gracias al cache en `.esphome/`
- **Sin `cap_drop`:** ESPHome necesita privileged para USB y networking avanzado.
  No aplicar restricciones de seguridad (cap_drop, no-new-privileges)
- **Espacio en disco:** El cache de compilación (`.esphome/`) puede crecer a varios GB
  con muchos dispositivos. Limpiar periódicamente si el disco se llena
- **Actualizaciones de imagen:** ESPHome se actualiza frecuentemente. Después de
  `svc update esphome`, recompilar los dispositivos para usar las nuevas features
- **USB hotplug:** Si conectas un ESP mientras el contenedor corre, puede no detectarlo.
  Reiniciar el contenedor: `svc restart esphome`
