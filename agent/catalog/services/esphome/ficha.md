# esphome

## Metadata

| Campo | Valor |
|-------|-------|
| **nombre** | esphome |
| **imagen** | ghcr.io/esphome/esphome:latest |
| **descripción** | Dashboard para gestionar dispositivos ESP32/ESP8266 (OTA, YAML configs) |
| **puerto** | 6052 (host network) |
| **protocolo** | http |
| **categoría** | IoT |
| **aliases** | esphome, esp, esp32 |

## Servicios

| Servicio | Imagen | Puerto |
|----------|--------|--------|
| esphome | ghcr.io/esphome/esphome:latest | 6052 (network_mode: host) |

## Volúmenes

| Host | Contenedor | Tipo |
|------|-----------|------|
| `./config` | `/config` | bind (configuraciones YAML de dispositivos) |
| `/etc/localtime` | `/etc/localtime` | bind (read-only, sincronizar hora) |

## Dispositivos

| Host | Contenedor | Nota |
|------|-----------|------|
| `/dev/ttyUSB0` | `/dev/ttyUSB0` | Programación serial (USB-UART) |

## Variables de entorno

### Globales ($dkco/.env)

| Variable | Descripción |
|----------|-------------|
| `SERVER_IP` | IP del NAS (para labels de Homepage) |
| `TZ` | Timezone |

### Locales (.env)

Sin secretos locales requeridos.

## Redes

`network_mode: host` — acceso directo a la red del NAS (necesario para mDNS/discovery de dispositivos ESP).

## Notas

- Corre como **privileged** (acceso a USB y red completa)
- `network_mode: host` es necesario para descubrir dispositivos en la LAN vía mDNS
- El dispositivo `/dev/ttyUSB0` solo es necesario para programación serial (si solo usas OTA, se puede quitar)
- El dashboard escucha en puerto 6052 (no configurable vía variable, es el default de ESPHome)
- Las configuraciones YAML de cada dispositivo se guardan en `./config/`

## docs_url

docs/services/esphome-guide.md
