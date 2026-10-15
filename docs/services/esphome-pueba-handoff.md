# ESPHome `pueba` — Handoff de sesión (estado real, para retomar en frío)

> **Propósito:** que un chat/LLM NUEVO sin contexto previo pueda continuar este
> proyecto sin repetir el trabajo ni los errores. Autocontenido.
> **Fecha:** 2026-10-13 (actualizado 2026-10-15) · **Dispositivo:** ESP32 `pueba` · **ESPHome:** 2026.6.3
> **Estado global:** ✅ **CERRADO y FUNCIONAL** con **un** límite conocido ASUMIDO
> (estado inicial del indicador tras reinicio — ver §6; decisión final = **Camino B,
> aceptar el límite**). Documentos relacionados:
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

## 6. ✅ LÍMITE CONOCIDO ASUMIDO (decisión: Camino B) — estado inicial al arrancar

> **Decisión final (2026-10-15): Camino B — aceptar el límite.** Ya **no es un
> pendiente**. El usuario decidió no añadir automatización en HA para empujar el
> estado inicial: el impacto es bajo y la fuente de verdad siempre está en la entidad
> nativa del Sonoff. El Camino A se conserva abajo solo como opción archivada por si
> el impacto cambiara en el futuro.

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

### Caminos considerados (decisión tomada: **B**)

> ✅ **Elegido: Camino B.** Lo de abajo queda como registro de la decisión; el
> Camino A es la alternativa archivada (no implementada).

**Camino A — resolverlo del todo (más trabajo) [ARCHIVADO, no elegido]:**
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

**Camino B — aceptar el límite (ELEGIDO ✅):**
Se deja como está. El indicador sincroniza tras el primer cambio y el estado real se
consulta en la entidad del Sonoff. Cero mantenimiento, sin automatización en HA
(coherente con "ESPHome inteligente"). **Decisión tomada el 2026-10-15.** El proyecto
`pueba` queda cerrado; este punto deja de ser un pendiente y pasa a ser un límite
conocido documentado.

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

---

## 9. Migración a remote packages desde GitHub (repo `esphome-common`)

> **Estado:** repo **creado y publicado** (`github.com/ydiaz1699/esphome-common`,
> público, tag `v1.0.0`). El `pueba.yaml` nuevo está **preparado** abajo pero
> **PENDIENTE de aplicar y validar en el NAS** (requiere SSH + compilación real; no se
> puede verificar desde Kiro Web por el doble NAT).

### Qué cambia y por qué

Hasta ahora `pueba.yaml` incluía su `common/`/`boards/`/`modules/` como archivos
**locales** (`!include common/base.yaml`). Se migra a cargarlos desde el repo
**`esphome-common`** vía git/remote packages (`github://…`), para tener las plantillas
base **versionadas y reutilizables** entre placas, editando en un solo sitio.

**Regla crítica (oficial):** un remote package **NO puede usar `!secret`**. Por eso en
`esphome-common` los secretos son `substitutions` (`${wifi_ssid}`,
`${api_encryption_key}`…) y `pueba.yaml` los inyecta con el patrón
**secret → substitution** (el `!secret` se asigna a una substitution). Ver
[`esphome-device-config.md` §Pasar secretos a los packages](esphome-device-config.md#pasar-secretos-a-los-packages-secret--substitution).

### `pueba.yaml` nuevo (reemplaza al actual en `$dkco/esphome/config/pueba.yaml`)

```yaml
# $dkco/esphome/config/pueba.yaml  — consume esphome-common por git packages
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
  debounce_time: "20ms"

  wifi_update_interval: 60s
  uptime_update_interval: 300s
  debug_update_interval: 60s

  # --- Secretos: !secret -> substitution (los packages remotos NO leen !secret) ---
  wifi_ssid: !secret wifi_ssid
  wifi_password: !secret wifi_password
  wifi_fallback: !secret wifi_fallback
  api_encryption_key: !secret api_encryption_key
  ota_password: !secret esp32_pruebas_ota_password

packages:
  remoto:
    url: https://github.com/ydiaz1699/esphome-common
    ref: v1.0.0          # tag fijo, NO main (controlas cuándo actualizas)
    refresh: 1d
    files:
      - common/base.yaml
      - boards/esp32.yaml
      - common/wifi.yaml
      - common/diagnostics.yaml
      - modules/entradas.yaml
      - modules/touch_switch.yaml
```

> `secrets.yaml` **no cambia** y sigue viviendo solo en el NAS (sus claves:
> `wifi_ssid`, `wifi_password`, `wifi_fallback`, `api_encryption_key`,
> `esp32_pruebas_ota_password`). Las carpetas locales `common/`/`boards/`/`modules/`
> del NAS pueden **quedarse** (dejan de usarse) o moverse a un respaldo; no borrarlas
> hasta validar que el remoto compila.

### Pasos en el NAS (por SSH) — orden real

```bash
dk esphome && cd config          # (o: cd $dkco/esphome/config)

# 1) Respaldo del pueba.yaml actual (y de las carpetas locales, por si acaso)
cp pueba.yaml /root/pueba.yaml.bak
tar czf /root/esphome-local-pre.tar.gz --exclude=.esphome common boards modules
chmod 600 /root/esphome-local-pre.tar.gz

# 2) Reemplazar pueba.yaml por la versión de arriba (editar con nano / subirlo)
#    nano pueba.yaml   → pegar el bloque de la sección 9

# 3) VALIDAR (descarga el package de GitHub; CONFIRMA que el doble NAT deja salir)
docker exec esphome esphome config /config/pueba.yaml
#    Debe decir "Configuration is valid!" y, en la salida resuelta, verse las
#    entidades (Señal Wi-Fi, Pulsador, Indicador Sonoff, botones) igual que antes.

# 4) Comparar que la config resuelta NO cambió respecto a la local (opcional pero
#    recomendado): usar el método de 'Reorganizar sin romper' (diff con sort).

# 5) Si valida: flashear (OTA por IP, o USB si hubo rollback) y comprobar en HA.
```

> ⚠️ **Lo que hay que confirmar en el NAS (no verificable desde aquí):**
> 1. Que ESPHome **descarga** `esphome-common@v1.0.0` al compilar (salida a internet a
>    través del doble NAT). Si fallara la descarga, el `esphome config` lo dirá.
> 2. Que la configuración resuelta es **equivalente** a la local (mismas entidades,
>    mismos `id`) → entonces **no hace falta reflashear** salvo que cambie algo.
> 3. El Device Builder puede volver a commitear `pueba.yaml` por su cuenta; es normal.

### Cómo actualizar las plantillas en el futuro

Editar en el repo `esphome-common`, publicar un tag nuevo (`v1.1.0`, …) y **subir el
`ref`** en `pueba.yaml` cuando quieras adoptarlo (si sigues en `v1.0.0`, nada cambia
en tus placas aunque el repo evolucione). `refresh: 1d` solo controla la caché del
mismo `ref`.

### Reversión

Si algo falla, restaurar el `pueba.yaml` local:

```bash
cp /root/pueba.yaml.bak $dkco/esphome/config/pueba.yaml
docker exec esphome esphome config /config/pueba.yaml   # vuelve a usar common/ local
# limpiar respaldos al terminar (el tar NO lleva secrets.yaml, pero por higiene):
rm -f /root/pueba.yaml.bak /root/esphome-local-pre.tar.gz
```
