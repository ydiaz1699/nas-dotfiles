# ESPHome — Organización de la configuración de dispositivos

> **Alcance:** cómo organizar los archivos YAML de los **dispositivos** ESP32/ESP8266
> (no el servicio Docker; eso está en [`esphome-guide.md`](esphome-guide.md)).
> **Mecanismo:** `substitutions` + `packages` de ESPHome.
> **Estado del patrón modular:** ✅ **verificado en runtime** (ESPHome 2026.6.3,
> `esphome config /config/pueba.yaml` → *"Configuration is valid!"*). `pueba` usa
> `packages` repartidos en `common/`, `boards/` y `modules/` (ver
> [Estructura de archivos](#estructura-de-archivos)). La reorganización desde la
> estructura anterior (todo en `common/`) se comprobó comparando la configuración
> resuelta antes y después: **mismo contenido** (ver
> [Reorganizar sin romper](#reorganizar-sin-romper)).
> **Pendientes detectados en revisión:** ver
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas) (no aplicadas, a
> decisión del usuario).

---

## Índice

1. [Dos formas de configurar un dispositivo](#dos-formas-de-configurar-un-dispositivo)
2. [Forma A — Config por defecto (un solo YAML)](#forma-a--config-por-defecto-un-solo-yaml)
3. [Forma B — Organización modular con `packages`](#forma-b--organización-modular-con-packages)
4. [Cómo fusiona `packages` (`!extend` / `!remove`, plantillas, git)](#cómo-fusiona-packages-lo-que-debes-saber-para-no-chocar)
5. [Estructura de archivos](#estructura-de-archivos)
6. [Archivos de `common/`, `boards/` y `modules/`](#archivos-de-common-boards-y-modules)
7. [El dispositivo (solo `substitutions` + `packages`)](#el-dispositivo-solo-substitutions--packages)
8. [`substitutions` — más allá de reemplazar texto](#substitutions--más-allá-de-reemplazar-texto)
9. [`secrets.yaml`](#secretsyaml)
10. [Red: IP fija y en qué subred vive la placa](#red-ip-fija-y-en-qué-subred-vive-la-placa)
11. [Alta en Home Assistant](#alta-en-home-assistant)
12. [Escalar a varias placas](#escalar-a-varias-placas)
13. [Validar antes de flashear](#validar-antes-de-flashear)
14. [Buenas prácticas de fiabilidad y hardware (de la FAQ oficial)](#buenas-prácticas-de-fiabilidad-y-hardware-de-la-faq-oficial)
15. [Reorganizar sin romper](#reorganizar-sin-romper)
16. [Mejoras pendientes (detectadas, no aplicadas)](#mejoras-pendientes-detectadas-no-aplicadas)

---

## Dos formas de configurar un dispositivo

ESPHome permite dos estilos. **Ninguno es obligatorio** — elige según prefieras:

| | Forma A: un solo YAML | Forma B: modular con `packages` |
|---|---|---|
| **Qué es** | Todo el dispositivo en un único `<nombre>.yaml` | El dispositivo solo declara `substitutions` + `packages`; el resto vive en subcarpetas |
| **Para quién** | Pocos dispositivos; configuración por defecto; empezar rápido | Varios dispositivos que comparten WiFi/API/diagnósticos o bloques funcionales |
| **Ventaja** | Simple, todo a la vista | No repites WiFi/OTA/diagnósticos en cada placa; cambias lo común una vez |
| **Costo** | Repites bloques en cada placa | Un poco más de estructura inicial |

> Si solo vas a tener un dispositivo o quieres lo más simple, usa la **Forma A** y
> sáltate el resto de este documento. La **Forma B** es para quien quiera modularizar.
> `pueba` usa la Forma B.

---

## Forma A — Config por defecto (un solo YAML)

Un único archivo `$dkco/esphome/config/<nombre>.yaml` con todo dentro:
`esphome:`, `esp32:`, `logger:`, `api:`, `ota:`, `wifi:`, sensores, etc. Es el
estilo que genera el wizard **NEW DEVICE** del dashboard. Funciona perfectamente;
la única desventaja es que, con varias placas, repites los mismos bloques.

Para obtener la Forma A a partir de `pueba` basta con juntar los archivos de
`common/`, `boards/` y `modules/` + el `substitutions` del dispositivo en un solo
archivo (los mapas únicos una sola vez; las listas, concatenadas).

---

## Forma B — Organización modular con `packages`

Igual que en Home Assistant se parte `configuration.yaml` en `core/` + `includes/`
con `!include`, en ESPHome se parte el YAML del dispositivo con **`packages`**.

> **Diferencia con Home Assistant:** HA usa `!include` directamente sobre cada
> clave. ESPHome usa la clave `packages:`, que fusiona configuraciones completas y
> es el mecanismo **nativo recomendado** para reutilizar bloques entre dispositivos.
> Dentro de un package se sigue usando `!include` para apuntar al archivo.

La idea: cada archivo vive según **qué es**, no según quién lo usa hoy:

- lo que es **igual en todas las placas** (WiFi, API, OTA, diagnósticos) → `common/`;
- lo que depende del **hardware de la placa** (variante, flash, framework) → `boards/`;
- los **bloques funcionales por responsabilidad**, reutilizables entre proyectos
  (entradas físicas, control de un actuador…) → `modules/`.

---

## Cómo fusiona `packages` (lo que debes saber para no chocar)

`packages` **no es un `!include` plano**: fusiona las configuraciones de cada
package con la del dispositivo. La regla de fusión depende del **tipo** de cada
clave de nivel superior. **La carpeta donde esté el archivo no influye en la fusión.**

| Clave de nivel superior | Tipo | Al estar en varios packages |
|---|---|---|
| `sensor:`, `binary_sensor:`, `switch:`, `button:`, `text_sensor:`, `number:`, `light:`… | **Lista** | ✅ **Se concatenan** — todos los elementos conviven. No hay conflicto. |
| `ota:` (en este proyecto: lista de plataformas, `- platform: esphome`) | **Lista** | ✅ Se concatenan por plataforma. ⚠️ *No verificado* con dos packages distintos aportando `ota`: hoy solo `base.yaml` lo define. |
| `esphome:`, `esp32:`, `wifi:`, `logger:`, `api:`, `web_server:`, `safe_mode:`, `captive_portal:`, `debug:` | **Mapa único** | ⚠️ **Se fusionan las claves internas**; si dos packages ponen la MISMA clave interna con distinto valor → **conflicto**. |
| `substitutions:` | **Mapa** | ✅ Se fusionan; el archivo que **incluye** gana sobre el package (permite sobreescribir por placa). |

**Regla de mapas únicos** (la que aplica este proyecto):

- Cada **mapa único** vive **una sola vez**, en su **package dueño**:

  | Mapa único | Package dueño |
  |---|---|
  | `esphome`, `logger`, `api`, `ota` | `common/base.yaml` |
  | `esp32` | `boards/esp32.yaml` |
  | `wifi` (con `manual_ip`), `captive_portal` | `common/wifi.yaml` |
  | `debug` | `common/diagnostics.yaml` |

- El **dispositivo** (`pueba.yaml`) lleva **solo** `substitutions` + `packages`.
  **Nunca** devuelvas los mapas únicos al device inline: es un retroceso de la
  arquitectura.
- Los demás packages (`modules/…`) aportan **solo listas** (`binary_sensor`,
  `switch`), que se concatenan sin pisarse.
- Nunca repartas el mismo mapa único entre dos packages.

Por eso tener `binary_sensor:` en `diagnostics.yaml`, `entradas.yaml` **y**
`touch_switch.yaml` **no es un duplicado problemático**: son listas, se concatenan.
Lo único que sería un error real es repetir el mismo `id:` o la **misma entidad**
(p. ej. definir los botones `restart`/`safe_mode` en dos packages a la vez →
aparecen duplicados en HA); hay que poner cada componente en **un solo** package.

> **Matiz de la doc oficial (importante):** las listas de componentes **con `id`** no
> se limitan a concatenarse — ESPHome las **fusiona por `id`**. Es decir, si un
> package define un `sensor` con `id: uptime_sensor` y el device vuelve a declarar un
> `sensor` con el **mismo** `id`, no salen dos: se fusionan en uno. Las listas **sin
> `id`** sí se concatenan sin más. Esto es justo lo que habilita `!extend`/`!remove`:
> referenciar por `id` un componente que vino de un package. Fuente:
> [ESPHome — Packages](https://new.esphome.io/components/packages/) (parafraseado).

### Packages con nombres (estructura anidada)

Cada package se declara con un **nombre** bajo `packages:`. El nombre es solo una
etiqueta organizativa (no cambia la fusión); sirve para identificar de dónde viene
cada bloque y para poder sobreescribirlo:

```yaml
packages:
  base: !include common/base.yaml
  placa: !include boards/esp32.yaml
  wifi: !include common/wifi.yaml
  diagnostics: !include common/diagnostics.yaml
  entradas: !include modules/entradas.yaml
  touch_switch: !include modules/touch_switch.yaml
```

> ⚠️ **No retroceder la arquitectura:** si ya existen `base.yaml`/`wifi.yaml`/…, los
> mapas únicos (`esphome`, `esp32`, `api`, `ota`, `wifi`, `captive_portal`…) viven
> en sus packages dueños — **nunca** se devuelven al device inline. El device = solo
> `substitutions` + `packages`. Y cada componente (p. ej. los botones de
> mantenimiento, que van en `diagnostics.yaml`) se define en **un solo** package.
> Antes de generar o reescribir un package, haz `ls common boards modules` y lee
> dónde vive cada cosa.

### `!extend` — modificar algo definido en otro package

Para **cambiar una propiedad** de un componente que ya definió un package (sin
reescribirlo entero), se referencia por su `id` con `!extend`:

```yaml
# El package de diagnóstico define:
#   sensor:
#     - platform: wifi_signal
#       id: wifi_rssi
#       update_interval: ${wifi_update_interval}
#
# En el dispositivo (o en otro package) se ajusta solo una propiedad:
sensor:
  - id: !extend wifi_rssi
    update_interval: 10s        # sobreescribe solo esto; lo demás se conserva
```

Útil para tener un `common/` genérico y afinar un parámetro por placa sin duplicar
el componente completo. (En `pueba` esto se resuelve más simple con la substitution
`wifi_update_interval`.)

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
  rele_salon: !include { file: modules/rele.yaml, vars: { rele_name: "Salón", rele_pin: GPIO16 } }
  rele_cocina: !include { file: modules/rele.yaml, vars: { rele_name: "Cocina", rele_pin: GPIO17 } }

# En modules/rele.yaml:
defaults:
  rele_pin: GPIO23          # usado si el !include no pasa rele_pin
switch:
  - platform: gpio
    name: "${rele_name}"
    pin: ${rele_pin}
```

> Diferencia con los packages "normales" de `common/`/`boards/` (base, wifi, placa):
> esos se incluyen **una vez** y aportan lo común a toda la placa. Un
> package-plantilla se incluye **varias veces** con `vars:` distintos para generar
> componentes repetidos sin copiar/pegar. Fuente:
> [ESPHome — Packages (Templates)](https://new.esphome.io/components/packages/).
>
> ⚠️ Ojo con los `id` fijos: `modules/entradas.yaml` de `pueba` NO es plantilla (usa
> `id` fijos → solo puede incluirse una vez por dispositivo). Para repetir un módulo
> N veces, parametriza también sus `id` con una substitution (ver
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas) #12).

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

> **Para este NAS hoy:** usamos packages **locales** (`!include common/*.yaml`,
> `boards/…`, `modules/…`). Los git packages se documentan como camino de escalado si
> algún día el `common/` se comparte entre instalaciones. El repo `ESPHome_ESP-NOW`
> del ecosistema es justamente el pensado para alojar plantillas base reutilizables.

### `packages:` como lista o como mapa

`packages:` admite dos formas equivalentes (las claves del mapa son solo etiquetas
organizativas, no afectan a la fusión). Un único package puede ir directo sin lista:

```yaml
# como mapa con nombres (lo que usa este NAS — recomendado por legibilidad)
packages:
  base: !include common/base.yaml
  placa: !include boards/esp32.yaml

# como lista (válido; sin etiquetas)
packages:
  - !include common/base.yaml
  - !include boards/esp32.yaml

# un solo package, forma directa
packages: !include common/base.yaml
```

---

## Estructura de archivos

```
/docker/esphome/config/
├── pueba.yaml                  ← dispositivo (lo lista el dashboard): substitutions + packages
├── secrets.yaml                ← contraseñas y claves (nunca a git)
├── common/                     ← igual en TODAS las placas, sin importar el hardware
│   ├── base.yaml               ← esphome, logger, api, ota
│   ├── wifi.yaml               ← wifi + manual_ip + captive_portal
│   └── diagnostics.yaml        ← debug, sensores/text_sensor de diagnóstico, estado online, botones restart/safe_mode
├── boards/                     ← hardware de la placa
│   └── esp32.yaml              ← esp32: variant, flash_size, framework
├── modules/                    ← bloques por responsabilidad, reutilizables entre proyectos
│   ├── entradas.yaml           ← pulsador GPIO23 + TTP223 GPIO22
│   └── touch_switch.yaml       ← switch template + indicador del Sonoff (fuente de verdad)
└── .esphome/                   ← cache de compilación (auto-generado; fuera de git)
```

**Criterio para decidir dónde va cada archivo:**

| Pregunta | Carpeta |
|---|---|
| ¿Es un dispositivo que el dashboard debe listar? | **Raíz** de `config/` |
| ¿Es igual en todas las placas, sin depender del hardware? | `common/` |
| ¿Depende del hardware de la placa (variante, flash, framework)? | `boards/` |
| ¿Es un bloque funcional por responsabilidad, reutilizable entre proyectos? | `modules/` |

**Por qué los dispositivos van en la raíz:** el wizard **NEW DEVICE** crea el YAML en
la raíz de `config/` y no conozco ninguna opción para cambiarlo. Además, según la
documentación oficial de ESPHome (*Configuration types*), el dashboard solo muestra
los YAML del nivel superior y recomienda dejar los archivos base en subdirectorios
para ocultarlos. Por eso **todo lo que está en una subcarpeta es un package** y la raíz
es la "carpeta de dispositivos"; no hace falta (ni conviene) una carpeta `devices/`.

> ⚠️ *No verificado en el Device Builder:* esa documentación describe el dashboard
> clásico. Tras mover archivos a subcarpetas, comprobar en
> `http://<IP_NAS>:6052` que la lista solo muestra `pueba` (ver
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas)).

**Cómo crecer:**

- **Placa con otro hardware** (ESP32-C3, ESP8266…): un nuevo `boards/<placa>.yaml` con
  su bloque propio (`esp32:` o `esp8266:`). Revisar que `common/diagnostics.yaml`
  sea compatible con esa plataforma (*no verificado*).
- **Un módulo que otra placa también necesita:** ya está en `modules/`, se incluye
  desde el otro dispositivo. No hay que mover nada.
- **Un bloque que solo usa una placa y no se prevé reutilizar:** puede quedarse en
  `modules/` igualmente; la carpeta responde a "qué es", no a "cuántos lo usan".

Crear las carpetas **antes** de mover o editar los YAML (orden: carpetas → archivos):

```bash
# desde /docker/esphome/config
cd $dkco/esphome/config
mkdir -p common boards modules
```

---

## Archivos de `common/`, `boards/` y `modules/`

> Son **mapas YAML** (pares `clave: valor`). Las `substitutions` (`${device_name}`,
> `${friendly_name}`, pines, intervalos…) las define el dispositivo que incluye el
> package. Cada módulo depende de substitutions concretas (ver el comentario
> "Requiere" de cada uno).

### `common/base.yaml`

```yaml
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

logger:
  level: INFO

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

ota:
  - platform: esphome
    password: !secret esp32_pruebas_ota_password
```

> El bloque `esp32:` **ya no está aquí**: vive en `boards/esp32.yaml`. El `comment`
> y el secret de OTA siguen siendo específicos de `pueba` (ver
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas)).

### `common/wifi.yaml`

```yaml
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

  # IP fija para que HA no pierda el dispositivo al reasignar DHCP.
  manual_ip:
    static_ip: ${static_ip}
    gateway: ${gateway}
    subnet: 255.255.255.0
    dns1: ${gateway}

  reboot_timeout: 15min

  ap:
    ssid: "${friendly_name} Recovery"
    password: !secret wifi_fallback

captive_portal:
```

> **IMPORTANTE:** `static_ip`/`gateway` deben corresponder a la MISMA subred del SSID.
> Ver la sección [Red](#red-ip-fija-y-en-qué-subred-vive-la-placa) antes de cambiar la IP.

### `common/diagnostics.yaml`

```yaml
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

> Los botones `restart`/`safe_mode` viven **solo aquí**. No crear otro package con
> ellos (entidades duplicadas en HA).

### `boards/esp32.yaml`

```yaml
# Placa: ESP32 genérico, 4MB, ESP-IDF
esp32:
  variant: esp32
  flash_size: 4MB
  framework:
    type: esp-idf
```

> Único dueño del mapa `esp32`. Para otro hardware, crear otro archivo en `boards/`
> (no editar este).

### `modules/entradas.yaml`

```yaml
# ------------------------------------------------------------
# ENTRADAS FÍSICAS
#  - Pulsador GPIO23 → conmuta el Sonoff vía HA (sin bucle).
#  - TTP223 GPIO22   → activo-HIGH; expuesto a HA, SIN acción (uso futuro).
# ------------------------------------------------------------
binary_sensor:
  - platform: gpio
    name: ${boton_name}
    id: boton_pulsador
    pin:
      number: ${boton_pin}
      mode:
        input: true
        pullup: true
      inverted: true
    filters:
      - delayed_on: ${debounce_time}
      - delayed_off: ${debounce_time}
    on_press:
      - homeassistant.service:
          service: switch.toggle
          data:
            entity_id: ${sonoff_entity}

  # TTP223 (VCC, GND, I/O): activo-HIGH, sin pull-up. TODO: definir función.
  - platform: gpio
    name: ${ttp_name}
    id: touch_ttp223
    pin:
      number: ${ttp_pin}
      mode:
        input: true
      inverted: false
    filters:
      - delayed_on: ${debounce_time}
      - delayed_off: ${debounce_time}
```

> **Requiere** (substitutions del dispositivo): `boton_name`, `boton_pin`,
> `debounce_time`, `sonoff_entity`, `ttp_name`, `ttp_pin`.
> El pulsador **depende de que la API esté conectada a HA**: sin HA no conmuta nada.
> Además, HA debe permitir al dispositivo ejecutar acciones (ver
> [Alta en Home Assistant](#alta-en-home-assistant)).
> `homeassistant.service` sigue siendo válido; ESPHome lo renombró a
> `homeassistant.action` (ver Mejoras pendientes).
> Este módulo mezcla **dos responsabilidades** (pulsador→HA y TTP223) con `id` fijos:
> solo puede incluirse **una vez por dispositivo** (ver Mejoras pendientes).

### `modules/touch_switch.yaml`

```yaml
# Control del Sonoff + indicador de su estado (fuente de verdad = Sonoff).
binary_sensor:
  - platform: homeassistant
    name: "Indicador Sonoff"
    id: indicador_sonoff
    entity_id: ${sonoff_entity}
    # Reflejar el estado del Sonoff en el switch (sin rebote).
    on_state:
      - lambda: |-
          id(interruptor_virtual).publish_state(x);

switch:
  - platform: template
    name: ${switch_name}
    id: interruptor_virtual
    icon: mdi:toggle-switch
    optimistic: false
    turn_on_action:
      - homeassistant.service:
          service: switch.turn_on
          data:
            entity_id: ${sonoff_entity}
    turn_off_action:
      - homeassistant.service:
          service: switch.turn_off
          data:
            entity_id: ${sonoff_entity}
```

> **Requiere** (substitutions del dispositivo): `sonoff_entity`, `switch_name`.
> **Fuente de verdad = Sonoff.** El switch no decide su estado: lo refleja desde el
> indicador (`publish_state`). Revisar el estado inicial (`restore_mode`) está en
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas).
> **Límite conocido ASUMIDO (Camino B):** el "Indicador Sonoff"
> (`platform: homeassistant`) no toma el estado inicial al arrancar el ESP (HA no
> reenvía el estado actual al suscribirse; bug de plataforma HA core #184371). Solo
> sincroniza tras el primer cambio. Decisión del usuario: aceptar el límite (impacto
> bajo; la fuente de verdad es la entidad nativa del Sonoff). Detalle en
> [`esphome-pueba-handoff.md`](esphome-pueba-handoff.md) §6.

---

## El dispositivo (solo `substitutions` + `packages`)

El YAML del dispositivo queda **limpio** — igual que `configuration.yaml` de Home
Assistant quedó "solo includes". Solo define sus substitutions (incluida la IP fija
que le toca) y la lista de packages. Todo lo demás vive en las subcarpetas:

```yaml
# $dkco/esphome/config/pueba.yaml
substitutions:
  device_name: pueba
  friendly_name: "Prueba"
  device_comment: "ESP32 con pulsador GPIO23 (Sonoff) + TTP223 GPIO22"
  log_level: "INFO"

  # Red (IP fija en la subred del NAS)
  static_ip: "192.168.1.132"
  gateway: "192.168.1.1"

  # Sonoff en Home Assistant
  sonoff_entity: "switch.minir4_sonoff_1002a2995b_1"

  # Pulsador físico (controla el Sonoff)
  boton_pin: "GPIO23"
  boton_name: "Pulsador GPIO23"

  # Sensor táctil TTP223 (uso futuro, sin acción por ahora)
  ttp_pin: "GPIO22"
  ttp_name: "Touch TTP223"

  switch_name: "Interruptor Pulsador"
  restart_name: "Reiniciar Dispositivo"
  safe_restart_name: "Reiniciar en Modo Seguro"
  debounce_time: "20ms"

  wifi_update_interval: 60s
  uptime_update_interval: 300s
  debug_update_interval: 60s

packages:
  base: !include common/base.yaml
  placa: !include boards/esp32.yaml
  wifi: !include common/wifi.yaml
  diagnostics: !include common/diagnostics.yaml
  entradas: !include modules/entradas.yaml
  touch_switch: !include modules/touch_switch.yaml
```

> **Nota sobre fusión de `binary_sensor`:** `diagnostics.yaml` (Estado Online),
> `entradas.yaml` (Pulsador y TTP223) y `touch_switch.yaml` (Indicador Sonoff)
> definen cada uno un `binary_sensor`. `packages` **fusiona listas**, así que los
> cuatro conviven sin pisarse. Esto es justo lo que no permite un `!include` plano.

> **Substitutions sin uso hoy:** `device_comment`, `log_level`, `restart_name` y
> `safe_restart_name` están definidas pero `base.yaml` y `diagnostics.yaml` usan
> valores fijos. Ver [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas).

> **Nombre del dispositivo:** `device_name` es el hostname y la identidad en HA.
> ESPHome lo limita (minúsculas, números y guiones; máximo 31 caracteres; **sin
> guion bajo** `_`, ver [Buenas prácticas](#buenas-prácticas-de-fiabilidad-y-hardware-de-la-faq-oficial)).
> Un buen nombre dice *dónde* y *qué* (p. ej. `taller-pulsador`). Renombrar un
> dispositivo ya dado de alta crea un dispositivo nuevo en HA y cambia sus `entity_id`.

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
> [Packages como plantillas](#cómo-fusiona-packages-lo-que-debes-saber-para-no-chocar)):
> un package es, en el fondo, un `!include` al que se le pasan variables.

### Substitutions por línea de comandos (`-s`)

Se puede **definir o sobreescribir** una substitution desde la CLI con `-s KEY VALUE`
(tiene prioridad sobre la del archivo). Permite un YAML "plantilla" que varias placas
reutilizan cambiando solo el nombre:

```bash
# dentro del contenedor esphome
docker exec esphome esphome -s device_name cocina config /config/plantilla.yaml
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

Todas las referencias `!secret` del dispositivo y de los packages deben existir en
`$dkco/esphome/config/secrets.yaml` o la compilación falla:

```yaml
# $dkco/esphome/config/secrets.yaml   — NUNCA a git
wifi_ssid: "SSID_DEL_HUAWEI_B622"            # ← CAMBIAR: WiFi de la red del NAS (.1.x)
wifi_password: "PASSWORD_WIFI"               # ← CAMBIAR
wifi_fallback: "PASSWORD_AP_RECUPERACION"    # ← CAMBIAR (mínimo 8 caracteres)
api_encryption_key: "CLAVE_BASE64_API"       # ← 32 bytes en base64 (p. ej. la que genera ESPHome)
esp32_pruebas_ota_password: "PASSWORD_OTA"   # ← CAMBIAR
```

> Los valores en MAYÚSCULAS son placeholders — reemplazar por los reales. El
> `secrets.yaml` va en `.gitignore`; no se versiona. Para generar una clave de API
> propia: `openssl rand -base64 32`.
>
> ✔ *Verificado en este repo:* `.gitignore` ya cubre `secrets.yaml`, `.esphome/` y
> `.device-builder*` (`git check-ignore -v`).

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
> fija y SIN fallback a otra red. Es el caso de `pueba` (`192.168.1.132`). El detalle
> completo de la topología, por qué el mDNS no cruza entre subredes y las opciones
> para unificar la red (modo AP del Huawei) están en
> [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md)
> (sección "Topología física real: doble NAT").

Elegir una `static_ip` **fuera del rango DHCP** del router para que no se la asigne
a otro dispositivo. Si no se conoce el rango, usar una alta (ej. `192.168.1.200`) y
comprobar que no choca con otro equipo.

---

## Alta en Home Assistant

La integración ESPHome de HA se conecta a **cada placa** (no al dashboard del
servicio). Tras flashear la placa con IP fija:

1. HA → **Ajustes → Integraciones → Agregar integración → ESPHome**
2. **Host:** la IP de la **placa** (ej. `192.168.1.132`) — **no** la IP del NAS
3. **Port:** `6053` (API nativa de la placa, no el `6052` del dashboard)
4. **Encryption key:** la de `api: encryption: key:` (el valor de `api_encryption_key`)
5. **Permitir acciones del dispositivo:** en la integración ESPHome → la placa →
   **Configurar (opciones)** → activar la opción que permite al dispositivo realizar
   acciones/servicios de Home Assistant. **Sin esto, el pulsador GPIO23 y el switch
   (`homeassistant.service`) no hacen nada** y HA lo registra como acción bloqueada.

> Si HA y la placa están en la misma subred, HA puede autodescubrirla por mDNS y
> aparecer sola en Integraciones. Entre subredes distintas el mDNS no cruza → usar
> alta manual por IP (por eso la IP fija es importante).

> **Renombrar entidades o `device_name` después del alta** cambia los `entity_id`
> y/o crea un dispositivo nuevo en HA, rompiendo automatizaciones y dashboards. Por
> eso conviene decidir los nombres antes del alta definitiva.

Flashear por OTA desde el dashboard (`http://<IP_NAS>:6052` → dispositivo →
**INSTALL → Wirelessly**) una vez hecho el primer flash por USB.

---

## Escalar a varias placas

Para una segunda placa, no se repite WiFi/API/OTA/diagnósticos: se crea otro YAML
**en la raíz** que reusa lo común, elige su archivo de `boards/` y los `modules/` que
necesite:

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
  placa: !include boards/esp32.yaml
  wifi: !include common/wifi.yaml
  diagnostics: !include common/diagnostics.yaml
  # modules/…: solo los que esta placa necesite (y sus substitutions)

# ---- Específico de la cocina (sus sensores/actuadores) ----
# sensor: ...
# switch: ...
```

> **Antes de reusar `common/` en otra placa**, hoy hay dos cosas atadas a `pueba`:
> `base.yaml` lleva un `comment` fijo ("Primera prueba de desarrollo ESP32") y el
> secret de OTA se llama `esp32_pruebas_ota_password`. Ver
> [Mejoras pendientes](#mejoras-pendientes-detectadas-no-aplicadas).
> `modules/entradas.yaml` y `modules/touch_switch.yaml` solo se incluyen si la placa
> tiene ese hardware y define las substitutions que declaran en su "Requiere". Con
> `id` fijos, un módulo solo puede incluirse **una vez por dispositivo**.

Cambiar algo común (ej. añadir un sensor de diagnóstico a todas las placas) se hace
**una vez** en `common/` y afecta a todas tras recompilar cada una.

---

## Validar antes de flashear

Tras crear o modificar `common/`, `boards/`, `modules/` o el dispositivo, validar que
compila **sin flashear** (resuelve substitutions + packages y verifica el YAML):

```bash
# Dashboard: http://<IP_NAS>:6052 → <dispositivo> → VALIDATE  ("Configuration is valid!")
# O por terminal:
docker exec esphome esphome config /config/pueba.yaml
```

> **Por qué `docker exec` y no `svc exec`:** `svc exec` no pasa bien los argumentos a
> `esphome`. Probado en este NAS (ESPHome 2026.6.3), las tres variantes fallan:
>
> | Comando | Resultado |
> |---|---|
> | `svc exec esphome esphome config …` | `exec: "config": executable file not found` |
> | `svc exec esphome sh -c '…'` | `No such option: -c` |
> | `svc exec esphome -- sh -c '…'` | `service "sh" is not running` |
>
> Usar `docker exec esphome esphome <subcomando> …` es la excepción puntual a la
> convención `svc` para este caso. Para ver los logs del **servicio**, `svc logs
> esphome` sí funciona.

**Verificación de la fusión de `packages`:** no basta con ver
*"Configuration is valid!"*. Revisar la salida resuelta y confirmar que:

- las listas se **concatenan** (los `binary_sensor` de `diagnostics`, `entradas` y
  `touch_switch` aparecen **todos**);
- **no hay entidades duplicadas** (p. ej. dos pares de botones restart/safe_mode);
- las substitutions están **resueltas** (sin `${...}` sin sustituir).

Después de flashear, revisar el arranque: `svc logs esphome` (logs del servicio) o,
para los del dispositivo, `docker exec -it esphome esphome logs /config/pueba.yaml`.

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

Otras: bajar `cpu_frequency: 160MHz` en `esp32:` (en este proyecto, `boards/esp32.yaml`),
usar una fuente 5V/2A con cable corto y grueso, o añadir un condensador de 100-1000 µF
entre 3V3 y GND.

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
packages de `common/`, `boards/` y `modules/` ya quedan ocultos por estar en
subcarpetas. Si algún archivo base tuviera que vivir en la raíz, se oculta
anteponiendo un punto al nombre (`.base.yaml`). Por eso nuestras subcarpetas no
ensucian el dashboard: solo aparecen los dispositivos (`pueba.yaml`, etc.).

### Restaurar estado tras reinicio / NVS lleno
Componentes como `switch`/`climate` pueden restaurar su estado tras un reinicio. Si
no se restaura o aparece `ESP_ERR_NVS_NOT_ENOUGH_SPACE` en los logs, la partición NVS
está llena; se puede limpiar reescribiéndola por USB (ver la FAQ para el comando
`esptool` exacto). En `pueba` no dependemos de restore (la fuente de verdad es el
Sonoff), así que esto no aplica hoy — queda documentado por si una placa futura usa
`restore_mode`.

---

## Reorganizar sin romper

Mover archivos entre carpetas, o separar un package en dos, **no cambia ningún `id`
ni entidad** si la configuración resuelta no cambia. Este procedimiento lo
demuestra. Se verificó en `pueba` al pasar de "todo en `common/`" a
`common/` + `boards/` + `modules/`.

**1. Respaldo y foto del estado actual** (desde `$dkco/esphome/config`):

```bash
tar czf /root/esphome-config-pre.tar.gz --exclude=.esphome -C $dkco/esphome config
chmod 600 /root/esphome-config-pre.tar.gz
docker exec esphome esphome config /config/pueba.yaml > /tmp/antes.txt 2>&1
wc -l /tmp/antes.txt; head -3 /tmp/antes.txt
```

> ⚠️ **Git no es una red de seguridad completa:** los archivos **sin seguimiento**
> (en este repo, `common/` entero no estaba versionado hasta el commit de la
> reorganización) no se restauran con `git reset --hard`. Por eso el respaldo con
> `tar`. Y contiene `secrets.yaml`: hay que **borrarlo al terminar**.

**2. Mover y editar**, comprobando cada cambio con `diff` (o `git diff`).

**3. Validar y comparar sin depender del orden:**

```bash
docker exec esphome esphome config /config/pueba.yaml > /tmp/despues.txt 2>&1
diff <(sort /tmp/antes.txt) <(sort /tmp/despues.txt) && echo "MISMO CONTENIDO"
```

> **Usar `sort`:** la salida de `esphome config` **no mantiene un orden estable**. Un
> `diff` directo da falsos positivos: en `pueba` movió 4 líneas de sitio (tres
> `args: []` y el mensaje `Configuration is valid!`, que pasó de la línea 3 a la
> 355) sin cambiar el contenido. Hipótesis (*no verificada*): ese mensaje sale por un
> canal distinto del YAML.

**4. Comprobar el dashboard** (solo debe listar los dispositivos de la raíz) y, si
todo está bien, guardar en git **solo los archivos concretos**:

```bash
git add pueba.yaml common boards modules
git status --short        # NO debe aparecer secrets.yaml ni .device-builder*
git commit -m "<mensaje>"
```

> **Ojo con los commits automáticos:** el Device Builder commitea por su cuenta los
> cambios en `pueba.yaml` (mensajes `Edit pueba.yaml`, autor `ESPHome Device
> Builder`), incluso si se editan con `sed`. Al reorganizar, `pueba.yaml` puede
> quedar commiteado **antes** que los packages nuevos. Comprobar con
> `git log -4 --format='%h  %an  %s'` y `git status --short` antes de asumir qué
> falta por versionar.

**5. Si algo falla, volver atrás y limpiar:**

```bash
tar xzf /root/esphome-config-pre.tar.gz -C $dkco/esphome   # restaura lo respaldado
# …al terminar (contiene secrets.yaml):
rm -rf /root/esphome-config-pre.tar.gz /tmp/antes.txt /tmp/despues.txt
```

> Al restaurar con `tar`, los archivos movidos **vuelven a su sitio antiguo, pero las
> carpetas nuevas con archivos se quedan**: hay que borrarlas a mano. Y **no hace
> falta reflashear** tras una reorganización equivalente: el firmware es el mismo
> mientras la configuración resuelta no cambie.

---

## Mejoras pendientes (detectadas, no aplicadas)

Hallazgos de la revisión de la config actual. **Ninguno está aplicado**: son
decisiones del usuario. Marcar cada uno como aplicado/descartado cuando se resuelva.

| # | Hallazgo | Archivo | Impacto en HA | Estado |
|---|---|---|---|---|
| 1 | Los `name:` repiten `${friendly_name}`; HA ya antepone el nombre del dispositivo → entidades tipo "Prueba Prueba Señal Wi-Fi" | `common/diagnostics.yaml` | Cambia los `entity_id` | PENDIENTE |
| 2 | `device_name: pueba` parece typo de `prueba` (o elegir un nombre real) | `pueba.yaml` | Si ya está dado de alta, HA crea un dispositivo nuevo | PENDIENTE |
| 3 | Substitutions sin uso: `device_comment`, `log_level`, `restart_name`, `safe_restart_name` (hay valores fijos en `base.yaml`/`diagnostics.yaml`) | `pueba.yaml`, `common/base.yaml`, `common/diagnostics.yaml` | Ninguno | PENDIENTE |
| 4 | Switch template sin `restore_mode` explícito: según versión puede restaurar y lanzar su acción al arrancar. Con "Sonoff = fuente de verdad" conviene `restore_mode: DISABLED` | `modules/touch_switch.yaml` | Ninguno si se hace bien | PENDIENTE |
| 5 | `Indicador Sonoff` solo sirve para reflejar estado en el switch; podría ser `internal: true` y no duplicar entidad en HA | `modules/touch_switch.yaml` | Desaparece esa entidad de HA | PENDIENTE |
| 6 | `homeassistant.service` → renombrado a `homeassistant.action` (la forma antigua sigue soportada) | `modules/entradas.yaml`, `modules/touch_switch.yaml` | Ninguno | PENDIENTE |
| 7 | `base.yaml` lleva `comment` y secret OTA específicos de `pueba`; parametrizar antes de reusar `common/` | `common/base.yaml` | Ninguno | PENDIENTE |
| 8 | Mover substitutions genéricas (intervalos, `debounce_time`, `log_level`) a un bloque `substitutions:` dentro de los packages como valores por defecto (el device las sobrescribe) | `common/*.yaml` | Ninguno | PENDIENTE |
| 9 | Unidades (`dBm`, `B`, `ms`) y `reboot_timeout: 15min` ya son valores por defecto (redundantes) | `common/diagnostics.yaml`, `common/wifi.yaml` | Ninguno | PENDIENTE (opcional) |
| 10 | Una `api_encryption_key` distinta por dispositivo (hoy se comparte el nombre de secret) | `common/base.yaml`, `secrets.yaml` | Reconfigurar clave en HA | PENDIENTE |
| 11 | Añadir a cada módulo una cabecera `# Requiere: <substitutions>` (hoy solo está documentado aquí) | `modules/*.yaml` | Ninguno | PENDIENTE |
| 12 | `modules/entradas.yaml` mezcla dos responsabilidades (pulsador→HA y TTP223) con `id` fijos (`boton_pulsador`, `touch_ttp223`): partirlo en dos módulos y/o parametrizar los `id` (patrón plantilla `vars:`) si se necesitan varias instancias por placa | `modules/entradas.yaml` | Mantener los `id` actuales evita cambios en HA | PENDIENTE |
| 13 | Comprobar que el dashboard (Device Builder) lista solo `pueba` y no los archivos de `common/`, `boards/` ni `modules/` | — | Ninguno | PENDIENTE de verificar |
| 14 | Identidad de git: el commit de la reorganización quedó con el autor literal `TU NOMBRE <tu@correo>` (marcadores de ejemplo usados por error). ✔ Corregido: se volvió a la identidad automática (`root <root@Nas>`) con `git config --unset user.name`, `git config --unset user.email` y `git commit --amend --reset-author --no-edit` (commit `4fa1cfe`) | repo `config/` | Ninguno | APLICADO |
| 15 | El Device Builder hace **commits automáticos** `Edit <dispositivo>.yaml` (autor `ESPHome Device Builder <device-builder@esphome.io>`) de los YAML de dispositivo, también cuando se editan con `sed` fuera de la UI. ✔ Observado en este repo (`git log`). *No verificado:* que **no** versione los packages de las subcarpetas (en este repo `common/` estaba sin versionar). Consecuencia: puede haber commits intermedios de `pueba.yaml` que apunten a archivos aún sin versionar | repo `config/` | Ninguno | PENDIENTE de verificar el alcance |

---

## Ver también

- [`esphome-guide.md`](esphome-guide.md) — instalación y operación del **servicio**
  ESPHome (contenedor, dashboard, flasheo, backups, troubleshooting).
- [`../esphome-meta-prompt.md`](../esphome-meta-prompt.md) — meta-prompt para
  **crear o mantener/mejorar** configuraciones ESPHome con cualquier LLM (niveles,
  `packages`/`!extend`/`!remove`, fusión no-destructiva).
- [`esphome-pueba-handoff.md`](esphome-pueba-handoff.md) — estado real del proyecto
  `pueba` + Sonoff.
- [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md)
  — topología de red del NAS, doble NAT y subredes.

### Fuentes oficiales (verificar contra ellas, no de memoria)

- [Substitutions](https://esphome.io/components/substitutions/) — Jinja, tipos
  estructurados, `!literal`, `!include` con `vars:`, CLI `-s`, `<<: !include`.
- [Packages](https://new.esphome.io/components/packages/) — fusión por `id`,
  plantillas (`vars:`/`defaults:`), remote/git packages, `!extend`/`!remove`.
- [FAQ](https://esphome.io/guides/faq/) — fiabilidad WiFi, brownout/`output_power`,
  naming, strapping pins, mDNS/subredes, restaurar estado/NVS.

> Contenido de estas fuentes reescrito y resumido para cumplir las restricciones de
> licencia; consultar los enlaces para el detalle completo.
