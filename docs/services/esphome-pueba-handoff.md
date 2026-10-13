# ESPHome `pueba` — Handoff de sesión (estado real, para retomar en frío)

> **Propósito:** que un chat/LLM NUEVO sin contexto previo pueda continuar este
> proyecto sin repetir el trabajo ni los errores. Autocontenido.
> **Fecha:** 2026-10-13 · **Dispositivo:** ESP32 `pueba` · **ESPHome:** 2026.6.3
> **Estado global:** FUNCIONAL con **un** límite conocido (estado inicial del
> indicador tras reinicio — ver §6). Documentos relacionados:
> [`esphome-device-config.md`](esphome-device-config.md) (patrón packages),
> [`../esphome-meta-prompt.md`](../esphome-meta-prompt.md) (meta-prompt),
> [`../../docker-nas/references/networking.md`](../../docker-nas/references/networking.md) (doble NAT).

---

## 1. Qué es este proyecto

ESP32 (`pueba`, friendly_name "Prueba") con ESPHome, integrado a Home Assistant,
que acompaña a un **relé Sonoff MINIR4** (entidad HA `switch.minir4_sonoff_1002a2995b_1`,
integración eWeLink en modo auto). El ESP:

- **Controla** el Sonoff desde un **pulsador físico GPIO23** y desde un **switch en HA**.
- **Muestra** el estado del Sonoff con un **indicador** (binary_sensor).
- Tiene un **TTP223 táctil en GPIO22** reservado para **uso futuro** (sin acción).
- Expone diagnósticos (señal WiFi, uptime, memoria, motivo de reinicio) y botones
  de mantenimiento (reiniciar / modo seguro).

**Fuente de verdad del estado = el Sonoff** (no el ESP). Decisión del usuario:
"ESPHome inteligente", es decir, la lógica vive en el ESP, **sin** automatización
de sincronización en HA (ver §6 para el único punto donde esto no alcanza).

---

## 2. Arquitectura de archivos (en `$dkco/esphome/config/` del NAS)

Modular con `packages` (ver `esphome-device-config.md`). **No** meter mapas únicos
inline en el device — viven en sus packages:

```
pueba.yaml                  ← SOLO substitutions + packages
common/
├── base.yaml               ← esphome, esp32, logger, api, ota, safe_mode
├── wifi.yaml               ← wifi + manual_ip + captive_portal
├── diagnostics.yaml        ← debug, sensores diagnóstico, text_sensor, botones restart/safe_mode
├── entradas.yaml           ← pulsador GPIO23 (→Sonoff) + TTP223 GPIO22 (sin acción)
└── touch_switch.yaml       ← binary_sensor "Indicador Sonoff" + switch "Interruptor Pulsador"
secrets.yaml                ← wifi_ssid, wifi_password, wifi_fallback, api_encryption_key, esp32_pruebas_ota_password
```

> Los botones de mantenimiento viven en `diagnostics.yaml`. **NO** crear `boton.yaml`
> (hubo ese error: duplica los botones porque `button:` es lista y se concatena).

### Datos de red (ver doble NAT en networking.md)
- IP fija del ESP: `static_ip: 192.168.1.132`, `gateway: 192.168.1.1` (en `wifi.yaml`).
- La placa debe conectarse al SSID del **Huawei B622** (red `192.168.1.x`, la del NAS),
  no al router principal (`192.168.0.x`). Si cae en `.0.x`, HA no la alcanza bien.

---

## 3. Contenido verificado de los packages

### `common/entradas.yaml`
```yaml
# Pulsador GPIO23 → conmuta el Sonoff vía HA (sin bucle).
# TTP223 GPIO22 → activo-HIGH, sin pull-up, SIN acción (uso futuro).
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

### `common/touch_switch.yaml`
```yaml
# Control del Sonoff + indicador de su estado (fuente de verdad = Sonoff).
binary_sensor:
  - platform: homeassistant
    name: "Indicador Sonoff"
    id: indicador_sonoff
    entity_id: ${sonoff_entity}
    # OJO: NO poner internal: true (lo oculta en HA — bug cometido y corregido).
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

> `substitutions` relevantes en `pueba.yaml`: `sonoff_entity: switch.minir4_sonoff_1002a2995b_1`,
> `boton_pin: GPIO23`, `ttp_pin: GPIO22`, `static_ip: 192.168.1.132`, `gateway: 192.168.1.1`,
> `switch_name: "Interruptor Pulsador"`, `debounce_time: 20ms`.

---

## 4. Qué FUNCIONA (verificado en runtime)

- ✅ `esphome config /config/pueba.yaml` → **Configuration is valid!**
- ✅ **Pulsador GPIO23** conmuta el relé del Sonoff.
- ✅ **Switch "Interruptor Pulsador"** (en HA) conmuta el Sonoff.
- ✅ **Indicador Sonoff** refleja los **cambios** del Sonoff (ON/OFF en caliente).
- ✅ IP fija `192.168.1.132`, 2 botones de mantenimiento (sin duplicados), TTP223 declarado.

### Requisito en HA (imprescindible)
En HA → Ajustes → Dispositivos y servicios → **ESPHome → "Prueba" → Configurar**:
- ☑ **Allow the device to perform Home Assistant actions** (sin esto, ni el pulsador
  ni el switch pueden mover el Sonoff → error "Prueba is not permitted to perform
  Home Assistant actions").
- (La casilla "Subscribe to logs" es solo para ver logs; NO afecta a la lógica.)

---

## 5. Errores ya resueltos (no repetirlos)

| Error | Causa | Fix |
|---|---|---|
| `restore_mode: DISABLE` inválido | Valor incorrecto | Es `DISABLED` (y para el switch actual se omite; ESPHome pone `ALWAYS_OFF` por defecto, OK) |
| 4 botones (restart/safe_mode duplicados) | Se creó `boton.yaml` con botones que ya estaban en `diagnostics.yaml` (listas se concatenan) | NO crear `boton.yaml`; los botones viven solo en `diagnostics.yaml` |
| Indicador no aparecía en HA | `binary_sensor homeassistant` tenía `internal: true` | Quitar `internal: true` |
| Nada de lo flasheado tomaba efecto | **OTA rollback**: el firmware nuevo no marcaba el boot como exitoso y revertía al viejo (`OTA rollback detected` en logs) | **Flashear por USB** (`/dev/ttyUSB0`), no por OTA, para romper el ciclo |
| Device "retrocedía" a inline | Se devolvieron mapas únicos (esphome/wifi/api…) al device en vez de respetar `base.yaml`/`wifi.yaml` | Device = solo substitutions + packages (regla anti-regresión en el meta-prompt) |
| "Interruptor Pulsador" no hacía nada / se apagaba solo | Era `optimistic` espejo sin control real / luego `optimistic:false` sin recibir confirmación | Switch con `turn_on_action`/`turn_off_action` al Sonoff + `on_state` del indicador refleja |

---

## 6. ⚠️ PROBLEMA ABIERTO (único pendiente) — estado inicial al arrancar

**Síntoma:** si cambias el Sonoff **mientras el ESP está apagado/reiniciando**, al
arrancar el ESP el **indicador NO toma el estado actual** del Sonoff. Solo se
sincroniza en el **primer cambio** posterior (desde el Sonoff o el ESP).

**Causa (verificada, es un bug de plataforma, NO del YAML):** el componente
`binary_sensor platform: homeassistant` se **suscribe a cambios**, pero HA **no le
reenvía el estado actual** al conectar. Confirmado en los logs: al arrancar el ESP
NO aparece `'Indicador Sonoff' >> ...` (solo aparece cuando el Sonoff cambia
después). Documentado en el issue oficial
[home-assistant/core #184371](https://github.com/home-assistant/core/issues/184371)
(condición de carrera: el ESP se suscribe antes de que HA publique el estado).

**Lo que se intentó y por qué NO resolvió:**
- `on_client_connected` + `delay` + leer el indicador → falla porque el indicador
  aún no tiene estado (HA no lo mandó).
- Automatización en HA que "reaplica" el estado al Sonoff
  (`action: switch.turn_{{ states(...) }}`) → **el `action:` con template dinámico
  NO es válido en HA** ("Acción desconocida seleccionada"). Además, reaplicar el
  mismo estado puede no generar un `state_changed`, así que el ESP no recibiría nada.

**Impacto real:** bajo. El ESP no se reinicia a diario y, tras el primer cambio,
todo sincroniza. El estado "de verdad" siempre está en la entidad nativa del Sonoff
en HA (el indicador del ESP es redundante con ella).

### Caminos para cerrarlo (elegir en el próximo chat)

**Camino A — resolverlo del todo (más trabajo):**
Rediseñar para que **HA empuje** el estado inicial al ESP (porque el ESP no puede
importarlo al arrancar). Opciones a evaluar, verificando en runtime:
1. Automatización en HA disparada al pasar `binary_sensor.<estado_online_del_ESP>`
   a `on`, usando **servicios fijos** (`choose` con `switch.turn_on`/`turn_off`, NO
   template en el nombre del servicio) o `homeassistant.update_entity` sobre el
   Sonoff (con un `delay` de ~3 s para que el ESP termine de suscribirse).
   - Antes: confirmar el **nombre exacto** del binary_sensor "Estado Online" del ESP
     (Herramientas de desarrollo → Estados) y que `homeassistant.update_entity`
     funcione con un Sonoff cloud (eWeLink puede no reenviar).
2. Si lo anterior no basta: exponer en el ESP un componente **escribible** desde HA
   (p. ej. un `template switch`/`number` que una acción de HA fije) y que la
   automatización escriba el estado inicial ahí. Más maquinaria.

**Camino B — aceptar el límite (pragmático, recomendado si no molesta):**
Dejarlo como está. Documentar que el indicador sincroniza tras el primer cambio y
que el estado real se consulta en la entidad del Sonoff. Cero mantenimiento, sin
automatización en HA (coherente con "ESPHome inteligente"). El usuario pidió
"documentar todo" sin elegir A/B todavía → **queda PENDIENTE la decisión**.

---

## 7. Comandos útiles (en `$dkco/esphome/config` del NAS, por SSH)

```bash
# Validar (resuelve packages + substitutions, sin flashear)
docker exec esphome esphome config /config/pueba.yaml
# OJO parsing: 'svc exec esphome esphome config ...' falla con
# 'exec: config not found'; usar docker exec directo o
# 'svc exec esphome sh -c "esphome config /config/pueba.yaml"'.

# Logs (ver si el indicador recibe estado al arrancar / al cambiar el Sonoff)
docker exec esphome esphome logs /config/pueba.yaml

# Flashear: por USB (rompe el OTA rollback) desde el dashboard
#   http://192.168.1.200:6052 → pueba → INSTALL → Plug into this computer → /dev/ttyUSB0
# (OTA solo cuando el boot se marque exitoso; si hay rollback, USB.)
```

Permiso en HA (acciones) ya descrito en §4. El dashboard ESPHome corre en el
servicio Docker `esphome` (puerto 6052, `network_mode: host`, privileged, acceso a
`/dev` para USB) — ver [`esphome-guide.md`](esphome-guide.md).

---

## 8. Qué NO volver a intentar (callejones sin salida verificados)

- ❌ Esperar que `binary_sensor/text_sensor platform: homeassistant` reciba el
  **estado inicial** al arrancar — NO lo hace (bug de plataforma).
- ❌ `action: switch.turn_{{ states(...) }}` (template en el nombre del servicio) —
  HA lo rechaza como "acción desconocida".
- ❌ `internal: true` en el indicador — lo oculta de HA.
- ❌ Crear `boton.yaml` — duplica los botones de `diagnostics.yaml`.
- ❌ Flashear por OTA mientras haya rollback — usar USB.
- ❌ Devolver mapas únicos al device inline — romper la arquitectura modular.
