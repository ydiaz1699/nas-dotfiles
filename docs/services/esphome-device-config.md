# ESPHome — Organización de la configuración de dispositivos

> **Alcance:** cómo organizar los archivos YAML de los **dispositivos** ESP32/ESP8266
> (no el servicio Docker; eso está en [`esphome-guide.md`](esphome-guide.md)).
> **Mecanismo:** `substitutions` + `packages` de ESPHome.
> **Estado del patrón modular:** ✅ **verificado en runtime** (ESPHome 2026.6.3,
> `esphome config /config/pueba.yaml` → *"Configuration is valid!"*). El refactor
> de `pueba` a `packages` + `common/{base,wifi,diagnostics}.yaml` fusiona correctamente
> las listas (p. ej. ambos `binary_sensor`: Estado Online + Pulsador GPIO23 conviven)
> y resuelve bien `substitutions` y `manual_ip` (`static_ip: 192.168.1.132`).

---

## Índice

1. [Dos formas de configurar un dispositivo](#dos-formas-de-configurar-un-dispositivo)
2. [Forma A — Config por defecto (un solo YAML)](#forma-a--config-por-defecto-un-solo-yaml)
3. [Forma B — Organización modular con `packages`](#forma-b--organización-modular-con-packages)
4. [Cómo fusiona `packages` (`!extend` / `!remove`)](#cómo-fusiona-packages-lo-que-debes-saber-para-no-chocar)
5. [Estructura de archivos](#estructura-de-archivos)
6. [Archivos de `common/`](#archivos-de-common)
7. [El dispositivo (solo `substitutions` + `packages`)](#el-dispositivo-solo-substitutions--packages)
8. [`secrets.yaml`](#secretsyaml)
9. [Red: IP fija y en qué subred vive la placa](#red-ip-fija-y-en-qué-subred-vive-la-placa)
10. [Alta en Home Assistant](#alta-en-home-assistant)
11. [Escalar a varias placas](#escalar-a-varias-placas)

---

## Dos formas de configurar un dispositivo

ESPHome permite dos estilos. **Ninguno es obligatorio** — elige según prefieras:

| | Forma A: un solo YAML | Forma B: modular con `packages` |
|---|---|---|
| **Qué es** | Todo el dispositivo en un único `<nombre>.yaml` | El dispositivo solo declara `substitutions` + `packages`; lo común vive en `common/` |
| **Para quién** | Pocos dispositivos; configuración por defecto; empezar rápido | Varios dispositivos que comparten WiFi/API/diagnósticos |
| **Ventaja** | Simple, todo a la vista | No repites WiFi/OTA/diagnósticos en cada placa; cambias `common/` una vez |
| **Costo** | Repites bloques en cada placa | Un poco más de estructura inicial |

> Si solo vas a tener un dispositivo o quieres lo más simple, usa la **Forma A** y
> sáltate el resto de este documento. La **Forma B** es para quien quiera modularizar.

---

## Forma A — Config por defecto (un solo YAML)

Un único archivo `$dkco/esphome/config/<nombre>.yaml` con todo dentro:
`esphome:`, `esp32:`, `logger:`, `api:`, `ota:`, `wifi:`, sensores, etc. Es el
estilo que genera el wizard **NEW DEVICE** del dashboard. Funciona perfectamente;
la única desventaja es que, con varias placas, repites los mismos bloques.

La plantilla completa de un dispositivo de ejemplo (`pueba`, ESP32 con diagnósticos,
OTA y AP de recuperación) está en la [Forma B](#el-dispositivo-solo-substitutions--packages)
ya descompuesta; para la Forma A basta con juntar los tres `common/*.yaml` + el
cuerpo del dispositivo en un solo archivo.

---

## Forma B — Organización modular con `packages`

Igual que en Home Assistant se parte `configuration.yaml` en `core/` + `includes/`
con `!include`, en ESPHome se parte el YAML del dispositivo con **`packages`**.

> **Diferencia con Home Assistant:** HA usa `!include` directamente sobre cada
> clave. ESPHome usa la clave `packages:`, que fusiona configuraciones completas y
> es el mecanismo **nativo recomendado** para reutilizar bloques entre dispositivos.
> Dentro de un package se sigue usando `!include` para apuntar al archivo.

La idea: lo que es **igual en todas las placas** (WiFi, API, OTA, diagnósticos) vive
en `common/`; cada placa solo pone sus `substitutions` y lo que le es propio.

---

## Cómo fusiona `packages` (lo que debes saber para no chocar)

`packages` **no es un `!include` plano**: fusiona las configuraciones de cada
package con la del dispositivo. La regla de fusión depende del **tipo** de cada
clave de nivel superior:

| Clave de nivel superior | Tipo | Al estar en varios packages |
|---|---|---|
| `sensor:`, `binary_sensor:`, `switch:`, `button:`, `text_sensor:`, `number:`, `light:`… | **Lista** | ✅ **Se concatenan** — todos los elementos conviven. No hay conflicto. |
| `wifi:`, `logger:`, `api:`, `ota:`, `esp32:`, `web_server:`… | **Mapa único** | ⚠️ **Se fusionan las claves internas**; si dos packages ponen la MISMA clave interna con distinto valor → **conflicto**. |
| `substitutions:` | **Mapa** | ✅ Se fusionan; el archivo que **incluye** gana sobre el package (permite sobreescribir por placa). |

**Regla de oro para no tener conflictos** (la que ya aplica este proyecto):

- Los **mapas únicos** (`wifi`, `api`, `ota`, `esp32`, `logger`, `safe_mode`,
  `captive_portal`) van **una sola vez**, en el archivo principal del dispositivo
  (`pueba.yaml`). No se reparten entre packages.
- Los packages de `common/` aportan **solo listas** (`sensor`, `binary_sensor`,
  `switch`, `button`, `text_sensor`), que se concatenan sin pisarse.

Por eso tener `binary_sensor:` en `diagnostics.yaml` **y** en `boton.yaml` **no es
un duplicado problemático**: son listas, se concatenan. Lo único que sería un error
real es repetir el mismo `id:` o la misma entidad; eso ESPHome sí lo rechaza.

### Packages con nombres (estructura anidada)

Cada package se declara con un **nombre** bajo `packages:`. El nombre es solo una
etiqueta organizativa (no cambia la fusión); sirve para identificar de dónde viene
cada bloque y para poder sobreescribirlo:

```yaml
packages:
  diagnostics: !include common/diagnostics.yaml
  boton: !include common/boton.yaml
  touch_switch: !include common/touch_switch.yaml
```

### `!extend` — modificar algo definido en otro package

Para **cambiar una propiedad** de un componente que ya definió un package (sin
reescribirlo entero), se referencia por su `id` con `!extend`:

```yaml
# El package de diagnóstico define:
#   sensor:
#     - platform: wifi_signal
#       id: wifi_rssi
#       update_interval: 60s
#
# En el dispositivo (o en otro package) se ajusta solo una propiedad:
sensor:
  - id: !extend wifi_rssi
    update_interval: 10s        # sobreescribe solo esto; lo demás se conserva
```

Útil para tener un `common/` genérico y afinar un parámetro por placa sin duplicar
el componente completo.

### `!remove` — quitar algo que trae un package

Para **eliminar** un componente o propiedad heredado de un package base:

```yaml
# Quitar por completo un componente que trae el package, por su id:
sensor:
  - id: !remove wifi_rssi

# O quitar solo una propiedad de un componente:
sensor:
  - id: !extend uptime_seconds
    icon: !remove
```

> **Cuándo usar `!extend`/`!remove`:** solo cuando tengas un `common/` compartido
> por varias placas y una placa concreta necesite **ajustar o quitar** algo del
> común. Para una sola placa (como `pueba`) **no hacen falta** — se edita el
> package directamente. Son herramientas para escalar, no para el caso simple.

> ⚠️ `!extend` y `!remove` requieren que el componente objetivo tenga un `id:`
> explícito. Sin `id`, no hay forma de referenciarlo entre packages.

---

## Estructura de archivos

```
/docker/esphome/config/
├── pueba.yaml                  ← dispositivo (solo substitutions + packages + lo propio)
├── common/                     ← equivalente a core/ + includes/ de Home Assistant
│   ├── base.yaml               ← esphome, esp32, logger, api, ota
│   ├── wifi.yaml               ← wifi + manual_ip + captive_portal
│   └── diagnostics.yaml        ← debug, sensores de diagnóstico, text_sensor, botones
├── secrets.yaml                ← contraseñas y claves (nunca a git)
└── .esphome/                   ← cache de compilación (auto-generado)
```

Crear la carpeta `common/` **antes** de editar los YAML (orden: carpetas → archivos):

```bash
# ya dentro de /docker/esphome/config  (dk esphome && cd config)
mkdir -p common
```

---

## Archivos de `common/`

> Estos tres archivos son el refactor del dispositivo de ejemplo `pueba`. Son
> **mapas YAML** (pares `clave: valor`). Las `substitutions` (`${device_name}`,
> `${friendly_name}`, intervalos) las define el dispositivo que incluye el package.

### `common/base.yaml`

```yaml
# Núcleo del dispositivo: identidad, placa, logger, API y OTA.
esphome:
  name: ${device_name}
  friendly_name: ${friendly_name}
  comment: "Primera prueba de desarrollo ESP32"
  on_boot:
    - priority: -100
      then:
        - logger.log:
            level: INFO
            format: "ESP32 iniciado correctamente"

esp32:
  variant: esp32
  flash_size: 4MB
  framework:
    type: esp-idf

logger:
  level: INFO

# API para Home Assistant (conexión nativa, puerto 6053 en la placa)
api:
  encryption:
    key: !secret api_encryption_key
  on_client_connected:
    - logger.log:
        level: INFO
        format: "Cliente conectado a la API"
  on_client_disconnected:
    - logger.log:
        level: INFO
        format: "Cliente desconectado de la API"

# Actualizaciones OTA con contraseña
ota:
  - platform: esphome
    password: !secret esp32_pruebas_ota_password
```

### `common/wifi.yaml`

```yaml
# WiFi + IP fija + portal de recuperación.
# IMPORTANTE: el static_ip/gateway deben corresponder a la MISMA subred del SSID.
# Ver la sección "Red" de este documento antes de cambiar la IP.
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

  # IP fija para que Home Assistant no pierda el dispositivo al reasignar DHCP.
  manual_ip:
    static_ip: ${static_ip}
    gateway: ${gateway}
    subnet: 255.255.255.0
    dns1: ${gateway}

  # Reinicia si no logra recuperar la conexión.
  reboot_timeout: 15min

  # Punto de acceso para recuperación si no conecta al WiFi.
  ap:
    ssid: "${friendly_name} Recovery"
    password: !secret wifi_fallback

# Portal de recuperación de WiFi.
captive_portal:
```

### `common/diagnostics.yaml`

```yaml
# Sensores de diagnóstico interno, info del sistema, interruptor demo y botones.
debug:
  update_interval: ${debug_update_interval}

sensor:
  - platform: wifi_signal
    name: "${friendly_name} Señal Wi-Fi"
    id: wifi_rssi
    update_interval: ${wifi_update_interval}
    entity_category: diagnostic
    device_class: signal_strength
    state_class: measurement
    unit_of_measurement: "dBm"
    accuracy_decimals: 0

  - platform: uptime
    name: "${friendly_name} Tiempo Encendido"
    id: uptime_seconds
    type: seconds
    update_interval: ${uptime_update_interval}
    entity_category: diagnostic
    device_class: duration
    state_class: total_increasing
    accuracy_decimals: 0

  - platform: debug
    free:
      name: "${friendly_name} Memoria Libre"
      entity_category: diagnostic
      state_class: measurement
      unit_of_measurement: "B"
      accuracy_decimals: 0
    block:
      name: "${friendly_name} Bloque Libre Mayor"
      entity_category: diagnostic
      state_class: measurement
      unit_of_measurement: "B"
      accuracy_decimals: 0
    loop_time:
      name: "${friendly_name} Tiempo del Bucle"
      entity_category: diagnostic
      state_class: measurement
      unit_of_measurement: "ms"
      accuracy_decimals: 0

text_sensor:
  - platform: wifi_info
    ip_address:
      name: "${friendly_name} Dirección IP"
      entity_category: diagnostic
    ssid:
      name: "${friendly_name} SSID Conectado"
      entity_category: diagnostic

  - platform: version
    name: "${friendly_name} Versión ESPHome"
    entity_category: diagnostic

  - platform: debug
    device:
      name: "${friendly_name} Información del Dispositivo"
      entity_category: diagnostic
    reset_reason:
      name: "${friendly_name} Motivo del Reinicio"
      entity_category: diagnostic

binary_sensor:
  - platform: status
    name: "${friendly_name} Estado Online"
    entity_category: diagnostic

button:
  - platform: restart
    name: "${friendly_name} Reiniciar"
    entity_category: config
  - platform: safe_mode
    name: "${friendly_name} Reiniciar en Modo Seguro"
    entity_category: config
```

---

## El dispositivo (solo `substitutions` + `packages`)

Con los tres `common/*.yaml` creados, el YAML del dispositivo queda **limpio** —
igual que `configuration.yaml` de Home Assistant quedó "solo includes". Solo define
sus substitutions (incluida la IP fija que le toca) y lo que sea **propio** de esa
placa (aquí, el pulsador GPIO23 + interruptor virtual):

```yaml
# $dkco/esphome/config/pueba.yaml
substitutions:
  device_name: pueba
  friendly_name: "pruea"
  # IP fija de ESTA placa (misma subred que el SSID — ver sección Red)
  static_ip: 192.168.1.132
  gateway: 192.168.1.1
  # Intervalos de diagnóstico
  wifi_update_interval: 60s
  uptime_update_interval: 300s
  debug_update_interval: 60s

packages:
  base: !include common/base.yaml
  wifi: !include common/wifi.yaml
  diagnostics: !include common/diagnostics.yaml

# ---- Específico de esta placa ----
switch:
  - platform: template
    name: "${friendly_name} Interruptor Virtual"
    id: interruptor_virtual
    optimistic: true
    restore_mode: ALWAYS_OFF
    icon: mdi:toggle-switch

binary_sensor:
  # Pulsador físico GPIO23 (entre GPIO23 y GND).
  - platform: gpio
    name: "${friendly_name} Pulsador GPIO23"
    id: boton_gpio23
    pin:
      number: GPIO23
      mode:
        input: true
        pullup: true
      inverted: true
    filters:
      - delayed_on: 20ms
      - delayed_off: 20ms
    on_press:
      - switch.toggle: interruptor_virtual
```

> **Nota sobre fusión de `binary_sensor`:** `common/diagnostics.yaml` ya define un
> `binary_sensor` (Estado Online) y el dispositivo añade otro (Pulsador GPIO23).
> `packages` **fusiona listas**, así que ambos conviven sin pisarse. Igual pasaría
> con `sensor`, `switch`, etc. Esto es justo lo que no permite un `!include` plano.

---

## `secrets.yaml`

Todas las referencias `!secret` del dispositivo y de `common/` deben existir en
`$dkco/esphome/config/secrets.yaml` o la compilación falla:

```yaml
# $dkco/esphome/config/secrets.yaml   — NUNCA a git
wifi_ssid: "SSID_DEL_HUAWEI_B622"            # ← CAMBIAR: WiFi de la red del NAS (.1.x)
wifi_password: "PASSWORD_WIFI"               # ← CAMBIAR
wifi_fallback: "PASSWORD_AP_RECUPERACION"    # ← CAMBIAR (mínimo 8 caracteres)
api_encryption_key: "CLAVE_BASE64_API"       # ← la que genera ESPHome (Noise encryption)
esp32_pruebas_ota_password: "PASSWORD_OTA"   # ← CAMBIAR
```

> Los valores en MAYÚSCULAS son placeholders — reemplazar por los reales. El
> `secrets.yaml` va en `.gitignore`; no se versiona.

---

## Red: IP fija y en qué subred vive la placa

El `manual_ip` **no decide la red** — eso lo decide el SSID al que se conecta la
placa. El `manual_ip` solo **congela la IP** para que Home Assistant no pierda el
dispositivo cuando el DHCP la reasigne.

**Regla de oro:** `static_ip`, `gateway` y el SSID deben ser de la **misma subred**.

| Si `wifi_ssid` es el del… | `static_ip` | `gateway` |
|---|---|---|
| Huawei B622 (red del NAS) | `192.168.1.X` | `192.168.1.1` |
| Router Principal de la casa | `192.168.0.X` | `192.168.0.1` |

> **Contexto crítico — doble NAT:** la red del NAS (`192.168.1.x`) está detrás de un
> doble NAT y **no es** la red principal de la casa (`192.168.0.x`). Para que Home
> Assistant (que corre en el NAS, `192.168.1.x`) encuentre la placa de forma estable,
> lo más simple es **anclar la placa a `192.168.1.x`** (misma red que HA), con IP
> fija y SIN fallback a otra red. El detalle completo de la topología, por qué el
> mDNS no cruza entre subredes y las opciones para unificar la red (modo AP del
> Huawei) están en
> [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md)
> (sección "Topología física real: doble NAT").

Elegir una `static_ip` **fuera del rango DHCP** del router para que no se la asigne
a otro dispositivo. Si no se conoce el rango, usar una alta (ej. `192.168.1.200`).

---

## Alta en Home Assistant

La integración ESPHome de HA se conecta a **cada placa** (no al dashboard del
servicio). Tras flashear la placa con IP fija:

1. HA → **Ajustes → Integraciones → Agregar integración → ESPHome**
2. **Host:** la IP de la **placa** (ej. `192.168.1.132`) — **no** la IP del NAS
3. **Port:** `6053` (API nativa de la placa, no el `6052` del dashboard)
4. **Encryption key:** la de `api: encryption: key:` (el valor de `api_encryption_key`)

> Si HA y la placa están en la misma subred, HA puede autodescubrirla por mDNS y
> aparecer sola en Integraciones. Entre subredes distintas el mDNS no cruza → usar
> alta manual por IP (por eso la IP fija es importante).

Flashear por OTA desde el dashboard (`http://<IP_NAS>:6052` → dispositivo →
**INSTALL → Wirelessly**) una vez hecho el primer flash por USB.

---

## Escalar a varias placas

Para una segunda placa, no se repite WiFi/API/OTA/diagnósticos: se crea otro YAML
que reusa el mismo `common/`:

```yaml
# $dkco/esphome/config/esp32_cocina.yaml
substitutions:
  device_name: esp32-cocina
  friendly_name: "ESP32 Cocina"
  static_ip: 192.168.1.133         # IP fija distinta, misma subred
  gateway: 192.168.1.1
  wifi_update_interval: 60s
  uptime_update_interval: 300s
  debug_update_interval: 60s

packages:
  base: !include common/base.yaml
  wifi: !include common/wifi.yaml
  diagnostics: !include common/diagnostics.yaml

# ---- Específico de la cocina (sus sensores/actuadores) ----
# sensor: ...
# switch: ...
```

Cambiar algo común (ej. añadir un sensor de diagnóstico a todas las placas) se hace
**una vez** en `common/` y afecta a todas tras recompilar cada una.

---

## Validar el refactor antes de flashear

Tras crear `common/` y el dispositivo con `packages`, validar que compila **sin
flashear** (resuelve substitutions + packages y verifica el YAML):

```bash
# Dashboard: http://<IP_NAS>:6052 → <dispositivo> → VALIDATE  ("Configuration is valid!")
# O por terminal:
docker exec esphome esphome config /config/<dispositivo>.yaml
```

> Nota de parsing: `svc exec esphome esphome config ...` puede fallar con
> `exec: "config": executable file not found` porque `svc exec` reinterpreta los
> subcomandos. Usar `svc exec esphome sh -c 'esphome config /config/<dispositivo>.yaml'`
> o `docker exec` directo para este diagnóstico puntual.

**Verificación de la fusión de `packages`:** en la salida resuelta, confirmar que
las listas se **fusionan** (p. ej. el `binary_sensor` de `common/diagnostics.yaml`
y el del dispositivo aparecen **ambos**). Esto es lo que `packages` hace y un
`!include` plano no: por eso ESPHome usa `packages` y no `!include` a secas.

---

## Ver también

- [`esphome-guide.md`](esphome-guide.md) — instalación y operación del **servicio**
  ESPHome (contenedor, dashboard, flasheo, backups, troubleshooting).
- [`../esphome-meta-prompt.md`](../esphome-meta-prompt.md) — meta-prompt para
  **crear o mantener/mejorar** configuraciones ESPHome con cualquier LLM (niveles,
  `packages`/`!extend`/`!remove`, fusión no-destructiva).
- [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md)
  — topología de red del NAS, doble NAT y subredes.
