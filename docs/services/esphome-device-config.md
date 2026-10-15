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
4. [Cómo fusiona `packages` (`!extend` / `!remove`, plantillas, git)](#cómo-fusiona-packages-lo-que-debes-saber-para-no-chocar)
5. [Estructura de archivos](#estructura-de-archivos)
6. [Archivos de `common/`](#archivos-de-common)
7. [El dispositivo (solo `substitutions` + `packages`)](#el-dispositivo-solo-substitutions--packages)
8. [`substitutions` — más allá de reemplazar texto](#substitutions--más-allá-de-reemplazar-texto)
9. [`secrets.yaml`](#secretsyaml)
10. [Red: IP fija y en qué subred vive la placa](#red-ip-fija-y-en-qué-subred-vive-la-placa)
11. [Alta en Home Assistant](#alta-en-home-assistant)
12. [Escalar a varias placas](#escalar-a-varias-placas)
13. [Buenas prácticas de fiabilidad y hardware (de la FAQ oficial)](#buenas-prácticas-de-fiabilidad-y-hardware-de-la-faq-oficial)

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

Por eso tener `binary_sensor:` en `diagnostics.yaml` **y** en `entradas.yaml` **no es
un duplicado problemático**: son listas, se concatenan. Lo único que sería un error
real es repetir el mismo `id:` o la **misma entidad** (p. ej. definir los botones
`restart`/`safe_mode` en dos packages a la vez → aparecen duplicados en HA); eso hay
que evitarlo poniendo cada componente en **un solo** package.

> **Matiz de la doc oficial (importante):** las listas de componentes **con `id`** no
> se limitan a concatenarse — ESPHome las **fusiona por `id`**. Es decir, si un
> package define un `sensor` con `id: uptime_sensor` y el device vuelve a declarar un
> `sensor` con el **mismo** `id`, no salen dos: se fusionan en uno. Las listas **sin
> `id`** sí se concatenan sin más. Esto es justo lo que habilita `!extend`/`!remove`
> (abajo): referenciar por `id` un componente que vino de un package. Fuente:
> [ESPHome — Packages](https://new.esphome.io/components/packages/) (parafraseado).

### Packages con nombres (estructura anidada)

Cada package se declara con un **nombre** bajo `packages:`. El nombre es solo una
etiqueta organizativa (no cambia la fusión); sirve para identificar de dónde viene
cada bloque y para poder sobreescribirlo:

```yaml
packages:
  base: !include common/base.yaml
  wifi: !include common/wifi.yaml
  diagnostics: !include common/diagnostics.yaml
  entradas: !include common/entradas.yaml
  touch_switch: !include common/touch_switch.yaml
```

> ⚠️ **No retroceder la arquitectura:** si ya existen `base.yaml`/`wifi.yaml`, los
> mapas únicos (`esphome`, `esp32`, `api`, `ota`, `wifi`, `captive_portal`…) viven
> en esos packages — **nunca** se devuelven al device inline. El device = solo
> `substitutions` + `packages`. Y cada componente (p. ej. botones de mantenimiento,
> que van en `diagnostics.yaml`) se define en **un solo** package.

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

### Packages como plantillas (`vars:` + `defaults:`)

Como un package se incorpora con `!include`, se le pueden pasar **variables** con
`vars:` y reutilizar el **mismo** archivo varias veces con valores distintos. El
package puede traer un bloque `defaults:` con valores por defecto para las variables
que el `!include` no proporcione. Es el patrón ideal cuando una placa tiene **N cosas
iguales** (p. ej. tres puertas de garaje, cuatro relés):

```yaml
# En el device:
packages:
  rele_salon: !include { file: common/rele.yaml, vars: { rele_name: "Salón", rele_pin: GPIO16 } }
  rele_cocina: !include { file: common/rele.yaml, vars: { rele_name: "Cocina", rele_pin: GPIO17 } }

# En common/rele.yaml:
defaults:
  rele_pin: GPIO23          # usado si el !include no pasa rele_pin
switch:
  - platform: gpio
    name: "${rele_name}"
    pin: ${rele_pin}
```

> Diferencia con los packages "normales" de `common/` (base, wifi, diagnostics): esos
> se incluyen **una vez** y aportan lo común a toda la placa. Un package-plantilla se
> incluye **varias veces** con `vars:` distintos para generar componentes repetidos
> sin copiar/pegar. Fuente:
> [ESPHome — Packages (Templates)](https://new.esphome.io/components/packages/).

### Remote / Git packages (compartir `common/` entre repos o placas)

Un package puede cargarse desde un **repositorio Git**, no solo desde un archivo
local. Útil si en el futuro quieres un `common/` versionado y compartido entre varias
instalaciones ESPHome:

```yaml
packages:
  # forma corta: github://usuario/repo/[carpeta/]archivo.yml[@rama-o-tag]
  base_remoto: github://ydiaz1699/ESPHome_ESP-NOW/common/base.yaml@main

  # forma larga con opciones
  comun:
    url: https://github.com/ydiaz1699/ESPHome_ESP-NOW
    files: [common/wifi.yaml, common/diagnostics.yaml]   # opcional; sin esto, todos
    ref: main          # opcional (rama/tag/commit)
    refresh: 1d        # opcional (cada cuánto refresca el contenido)
```

> ⚠️ **Regla oficial clave:** los **remote packages NO pueden usar `!secret`**.
> Deben exponer `substitutions` (con un `defaults:` opcional) que el YAML **local**
> rellena con sus propios secretos. Es decir: el `common/` remoto se parametriza, y
> cada NAS/placa inyecta sus credenciales localmente. Fuente:
> [ESPHome — Packages (Remote/Git)](https://new.esphome.io/components/packages/).

> **Para este NAS hoy:** usamos packages **locales** (`!include common/*.yaml`). Los
> git packages se documentan como camino de escalado si algún día el `common/` se
> comparte entre instalaciones. El repo `ESPHome_ESP-NOW` del ecosistema es
> justamente el pensado para alojar plantillas base reutilizables.

### `packages:` como lista o como mapa

`packages:` admite dos formas equivalentes (las claves del mapa son solo etiquetas
organizativas, no afectan a la fusión). Un único package puede ir directo sin lista:

```yaml
# como mapa con nombres (lo que usa este NAS — recomendado por legibilidad)
packages:
  base: !include common/base.yaml
  wifi: !include common/wifi.yaml

# como lista (válido; sin etiquetas)
packages:
  - !include common/base.yaml
  - !include common/wifi.yaml

# un solo package, forma directa
packages: !include common/base.yaml
```

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

## `substitutions` — más allá de reemplazar texto

Las `substitutions` no son solo "buscar y reemplazar": ESPHome resuelve dentro de
`${...}` **expresiones Jinja**, valores estructurados y operaciones matemáticas. Esto
permite que un mismo `common/` sirva para placas distintas cambiando solo unas pocas
claves. (Capacidades y sintaxis según la
[documentación oficial de ESPHome — Substitutions](https://esphome.io/components/substitutions/);
contenido reescrito y resumido para esta guía.)

### Tipos de valor (no solo cadenas)

Una substitution puede ser cualquier tipo YAML válido: cadena, número, booleano,
lista o **diccionario anidado**. Con diccionarios se agrupan parámetros relacionados:

```yaml
substitutions:
  color: "yellow"
  unused_pins: [12, 23, 27]
  sensor_pin:
    number: 23
    inverted: true
```

A un diccionario se accede con **notación de punto** `${sensor_pin.number}` o
indexada `${sensor_pin["number"]}`; a una lista por índice `${unused_pins[2]}`. Un
diccionario completo también se puede inyectar entero como valor de una clave
(`pin: ${sensor_pin}`).

### Expresiones Jinja y operaciones matemáticas

Dentro de `${ ... }` caben expresiones Jinja (condicionales, filtros) y operadores
matemáticos, además del módulo `math` de Python:

```yaml
substitutions:
  high_dpi: true
  native_width: 480
  scale: 1.5

display:
  - platform: ili9xxx
    dimensions:
      # condicional: duplica el ancho solo si high_dpi
      width: ${native_width * 2 if high_dpi else native_width}
      # filtros Jinja encadenados
      height: ${ (240 * scale) | round | int }
```

> ⚠️ **Ojo con la sintaxis:** en Jinja "normal" las expresiones van entre `{{ }}`.
> ESPHome las configura con `${ ... }` (igual que las substitutions) para no chocar
> con el Jinja de Home Assistant. Dentro de nuestros YAML, **siempre `${ ... }`**.

Funciones integradas disponibles además de Jinja: `ord("A")` → `65`, `chr(65)` →
`"A"`, `len("Hola")` → `4`.

### `!literal` — desactivar la sustitución en un valor concreto

Si un valor debe contener literalmente `${...}` (sin que ESPHome lo interprete), se
antepone `!literal`:

```yaml
substitutions:
  value: "prueba"
text: !literal "Esto es un ${value}"   # queda tal cual: "Esto es un ${value}"
```

### `!include` con `vars:` — plantillas de fragmentos

El `!include` de ESPHome acepta una lista de **variables** que se sustituyen dentro
del archivo incluido; incluso el **nombre del archivo** puede llevar substitutions
para elegir dinámicamente qué fichero cargar. Útil para repetir un bloque idéntico
cambiando un par de valores:

```yaml
binary_sensor:
  - platform: gpio
    id: boton1
    pin: GPIO23
    on_multi_click: !include { file: on-multi-click.yaml, vars: { id: 1 } }
  - platform: gpio
    id: boton2
    pin: GPIO22
    on_multi_click: !include
      file: on-multi-click.yaml
      vars: { id: 2 }
```

> Esto es el mismo mecanismo `vars:` que usan los **packages como plantillas** (ver
> la sección de packages más abajo): un package es, en el fondo, un `!include` al que
> se le pasan variables.

### Substitutions por línea de comandos (`-s`)

Se puede **definir o sobreescribir** una substitution desde la CLI con `-s KEY VALUE`
(tiene prioridad sobre la del archivo). Permite un YAML "plantilla" que varias placas
reutilizan cambiando solo el nombre:

```bash
# dentro del contenedor esphome
esphome -s device_name cocina config /config/plantilla.yaml
```

### `<<: !include` — operador de inserción YAML (alternativa a `packages`)

ESPHome también soporta el operador de inserción YAML `<<: !include common.yaml`,
heredando de un archivo base. **Para este NAS preferimos `packages:`** (fusión más
clara y es el mecanismo nativo recomendado para reutilizar entre placas); `<<:`
se documenta aquí solo para reconocerlo si aparece en ejemplos de terceros.

> ⚠️ Usar substitutions en el nombre de archivo de un `<<: !include` **no está
> soportado** (sí lo está en `!include` normal y en packages).

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

## Buenas prácticas de fiabilidad y hardware (de la FAQ oficial)

Opciones de la [FAQ de ESPHome](https://esphome.io/guides/faq/) que mejoran la
robustez de los `common/` sin añadir complejidad (parafraseadas y resumidas):

### Reconexiones aleatorias / WiFi inestable
Si una placa se reconecta sola o se queda sin red:
- **IP fija** (ya lo hacemos con `manual_ip` en `wifi.yaml`) — es la primera
  recomendación oficial.
- `fast_connect: true` en `wifi:` ayuda sobre todo con **redes ocultas** (y a veces
  también con visibles).
- `power_save_mode: light` en `wifi:` puede ayudar (pero a veces empeora; probar).
- Para **desactivar** el reinicio automático por pérdida de WiFi/API/MQTT, poner
  `reboot_timeout: 0s` en el componente correspondiente. En este proyecto hacemos lo
  contrario a propósito (`reboot_timeout: 15min` en `wifi.yaml`) para que una placa
  colgada se recupere sola; dejar `0s` solo si un reinicio es indeseable.
- Mantener el `logger` en un nivel moderado en producción: `VERY_VERBOSE` puede
  **provocar** desconexiones en placas de un solo núcleo.

### "Brownout detector was triggered" (caídas de tensión)
Si en los logs aparece *brownout*, el ESP32 se queda sin voltaje en los picos de
transmisión WiFi. La medida más efectiva es **bajar la potencia de transmisión**:

```yaml
wifi:
  output_power: 13dB        # por defecto 20dB; bajarlo reduce el pico de corriente
```

Otras: bajar `cpu_frequency: 160MHz` en `esp32:`, usar una fuente 5V/2A con cable
corto y grueso, o añadir un condensador de 100-1000 µF entre 3V3 y GND.

### No usar `_` (guion bajo) en `name:`
El `name:` del dispositivo es el hostname en la red. Según RFC1912 el guion bajo no
es válido en hostnames y rompe resolución DNS/mDNS en algunos routers. **Usar guion
`-`** (p. ej. `esp32-cocina`, no `esp32_cocina`). Al renombrar una placa viva, usar
`use_address` con el nombre antiguo hasta completar el cambio.

### Pines de strapping
Algunos GPIO son "strapping pins" (se leen al arrancar y deciden el modo de boot).
Si un componente externo cambia su estado en el arranque, el boot puede fallar.
Evitarlos salvo que sepas el estado esperado; si estás seguro, se puede silenciar el
aviso con `ignore_strapping_warning: true` en ese pin.

### Ocultar los archivos base del dashboard
El dashboard de ESPHome solo lista los YAML del **directorio raíz** de `config/`. Los
packages de `common/` ya quedan ocultos por estar en subcarpeta. Si algún archivo
base tuviera que vivir en la raíz, se oculta anteponiendo un punto al nombre
(`.base.yaml`). Por eso nuestro `common/` no ensucia el dashboard: solo aparecen los
dispositivos (`pueba.yaml`, etc.).

### Restaurar estado tras reinicio / NVS lleno
Componentes como `switch`/`climate` pueden restaurar su estado tras un reinicio. Si
no se restaura o aparece `ESP_ERR_NVS_NOT_ENOUGH_SPACE` en los logs, la partición NVS
está llena; se puede limpiar reescribiéndola por USB (ver la FAQ para el comando
`esptool` exacto). En `pueba` no dependemos de restore (la fuente de verdad es el
Sonoff), así que esto no aplica hoy — queda documentado por si una placa futura usa
`restore_mode`.

---

## Ver también

- [`esphome-guide.md`](esphome-guide.md) — instalación y operación del **servicio**
  ESPHome (contenedor, dashboard, flasheo, backups, troubleshooting).
- [`../esphome-meta-prompt.md`](../esphome-meta-prompt.md) — meta-prompt para
  **crear o mantener/mejorar** configuraciones ESPHome con cualquier LLM (niveles,
  `packages`/`!extend`/`!remove`, fusión no-destructiva).
- [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md)
  — topología de red del NAS, doble NAT y subredes.
