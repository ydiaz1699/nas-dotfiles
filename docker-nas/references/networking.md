# Redes avanzadas del NAS — systemd-networkd, systemd-resolved, Avahi y macvlan

> **Estado:** guía de instalación y recuperación; la configuración efectiva debe verificarse en el NAS antes de aplicar cambios.
> **Alcance:** DNS del host, `systemd-networkd`, IPv4/IPv6, Avahi/mDNS, AdGuard en macvlan, Docker y Home Assistant.
> **Regla crítica:** no desactivar IPv6 ni borrar `/etc/resolv.conf` sin confirmar antes el impacto en Matter, Thread, Home Assistant y Avahi.

Esta guía amplía la antigua referencia de macvlan. No sustituye la configuración real del NAS: los archivos de `/etc` no están versionados en `nas-dotfiles`, por lo que el preflight y el snapshot son obligatorios.

## 1. Arquitectura que debe conservarse

En el NAS actual, la topología declarada es:

```text
LAN                         192.168.1.0/24
Host eno1                   192.168.1.200/24
Gateway                     192.168.1.1
AdGuard macvlan              192.168.1.201
Host macvlan-shim            192.168.1.250/32 → ruta a 192.168.1.201/32
Backend de red              systemd-networkd
Hostname mDNS               Nas.local (avahi-daemon)
```

La tabla anterior usa los valores actualmente declarados para este NAS. Antes de ejecutar cualquier comando, confirmar la interfaz, prefijo, gateway e IP de AdGuard con el preflight; si alguno difiere, detenerse y adaptar las variables del procedimiento. No usar estos valores como plantilla para otro servidor.

Para los comandos de prueba se puede definir la IP de AdGuard una sola vez:

```bash
ADGUARD_IP="${ADGUARD_IP:-192.168.1.201}"
```

Home Assistant usa `network_mode: host`, por lo que comparte la red del host. Si se desactiva IPv6 en `eno1`, también se elimina IPv6 para Home Assistant. Matter y Thread requieren IPv6; ESPHome, MQTT y muchas integraciones HTTP pueden funcionar con IPv4.

## 2. Qué hace systemd-resolved

`systemd-resolved` es el resolvedor local del host. Puede proporcionar:

- Caché DNS.
- Stub local en `127.0.0.53`.
- DNS upstream IPv4 e IPv6.
- Integración con DNS entregado por `systemd-networkd`.
- Resolución LLMNR/mDNS si se habilita.
- Consulta mediante `resolvectl`.

En este NAS, `avahi-daemon` debe seguir siendo el propietario de la publicación de `Nas.local`. No se debe activar una segunda implementación mDNS sin probarla: `systemd-resolved` puede resolver mDNS, pero Avahi ya publica servicios y hostname.

La instalación recomendada usa:

```text
aplicaciones del host → /etc/resolv.conf → 127.0.0.53
                                      ↓
                          systemd-resolved
                                      ↓
                       AdGuard o DNS upstream
```

AdGuard continúa siendo un servidor DNS independiente en `192.168.1.201:53`; no se debe publicar otro DNS con `0.0.0.0:53` en el host si el stub local o el modelo macvlan ya ocupa ese puerto.

## 3. Preflight obligatorio — solo lectura

Ejecutar antes de instalar o cambiar nada. No hacerlo desde la única sesión SSH disponible.

```bash
systemctl is-active systemd-networkd
systemctl is-active systemd-resolved
systemctl is-active avahi-daemon
systemctl is-active NetworkManager
systemctl is-active networking
```

```bash
networkctl status eno1
ip -br addr
ip route
ip -6 addr show dev eno1
ip -6 route
```

```bash
readlink -f /etc/resolv.conf
bat /etc/resolv.conf
resolvectl status 2>&1 || true
```

```bash
ss -lntup | grep -E '(:53[[:space:]]|:5353[[:space:]])' || true
```

```bash
svc net
svc ps adguard
svc health
```

```bash
command -v dig >/dev/null || {
    echo "Falta dig. Instalar dnsutils antes de continuar: instal dnsutils"
    exit 1
}

ip route get "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
```

Estas dos comprobaciones son una compuerta obligatoria: no mover `resolv.conf`
si el host no puede llegar directamente a AdGuard y obtener una respuesta DNS.


El resultado esperado para IPv4 es una ruta similar a:

```text
1.1.1.1 via 192.168.1.1 dev eno1 src 192.168.1.200
```

Si Home Assistant utiliza Matter, Thread o dispositivos IPv6, verificarlo antes de tocar `IPv6AcceptRA` o `LinkLocalAddressing`.

## 4. Snapshot reversible

El snapshot debe existir antes de instalar el paquete o cambiar el enlace de `resolv.conf`. Se guarda en `$aadm`, no dentro del repositorio ni de un servicio Docker.

### 4.1 Crear la carpeta del snapshot

```bash
SNAPSHOT_ROOT="${aadm:-}"
if [ -z "$SNAPSHOT_ROOT" ]; then
    SNAPSHOT_ROOT="$(getent passwd aadm | cut -d: -f6)"
fi
SNAPSHOT_ROOT="${SNAPSHOT_ROOT:-$HOME}"
test -d "$SNAPSHOT_ROOT" && test -w "$SNAPSHOT_ROOT" || {
    echo "No hay un directorio escribible para el snapshot: $SNAPSHOT_ROOT"
    exit 1
}
SNAPSHOT="$SNAPSHOT_ROOT/network-snapshots/$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$SNAPSHOT"
printf '%s\n' "$SNAPSHOT" > "$SNAPSHOT_ROOT/network-snapshots/LATEST"
printf '%s\n' "$SNAPSHOT"
```

### 4.2 Guardar archivos y estado

```bash
cp -a /etc/systemd/network "$SNAPSHOT/"
cp -a /etc/avahi "$SNAPSHOT/"
cp -a /etc/systemd/resolved.conf.d "$SNAPSHOT/" 2>/dev/null || touch "$SNAPSHOT/resolved.conf.d.absent"
cp -a /etc/resolv.conf "$SNAPSHOT/resolv.conf.original" 2>/dev/null || true
cp -a /etc/systemd/resolved.conf "$SNAPSHOT/resolved.conf.original" 2>/dev/null || true
cp -a /etc/nsswitch.conf "$SNAPSHOT/nsswitch.conf.original" 2>/dev/null || true
```

```bash
systemctl is-enabled systemd-networkd > "$SNAPSHOT/services.state" 2>&1 || true
systemctl is-enabled systemd-resolved >> "$SNAPSHOT/services.state" 2>&1 || true
systemctl is-enabled avahi-daemon >> "$SNAPSHOT/services.state" 2>&1 || true
systemctl is-enabled systemd-resolved > "$SNAPSHOT/resolved.enabled" 2>&1 || true
systemctl is-active systemd-resolved > "$SNAPSHOT/resolved.active" 2>&1 || true
networkctl status > "$SNAPSHOT/networkctl.status" 2>&1 || true
resolvectl status > "$SNAPSHOT/resolvectl.status" 2>&1 || true
ip route > "$SNAPSHOT/ip-route" 2>&1 || true
ip -6 route > "$SNAPSHOT/ip6-route" 2>&1 || true
```

Anotar el valor de `SNAPSHOT`. Si se pierde SSH, se necesita la consola local o un canal fuera de banda para ejecutar el rollback.

## 5. Instalar el paquete sin borrar la configuración actual

En Debian, `systemd-resolved` puede estar separado del paquete base de systemd. Instalarlo con el alias del NAS:

```bash
instal systemd-resolved
```

Comprobar que la unidad existe antes de activarla:

```bash
systemctl list-unit-files systemd-resolved.service
```

Activar y arrancar el servicio:

```bash
systemctl enable systemd-resolved.service
systemctl start systemd-resolved.service
```

Validar antes de modificar `resolv.conf`:

```bash
systemctl status systemd-resolved --no-pager
resolvectl status
```

Si el servicio no inicia, detenerse y revisar `journalctl -u systemd-resolved`; no cambiar el enlace de `resolv.conf` todavía.

## 6. Configuración recomendada mediante drop-in

No editar el archivo principal si no es necesario. Crear primero el directorio y después el archivo:

```bash
mkdir -p /etc/systemd/resolved.conf.d
nano /etc/systemd/resolved.conf.d/10-nas.conf
```

Perfil inicial conservador:

```ini
[Resolve]
# Perfil estricto: el host usa AdGuard y no salta el filtrado.
DNS=192.168.1.201

# FallbackDNS no sustituye automáticamente a un DNS configurado que está caído;
# mantenerlo documentado solo como respaldo si no hay DNS por enlace.
# FallbackDNS=1.1.1.1 8.8.8.8

# Enrutar todas las consultas unicast hacia la política anterior.
Domains=~.

# Mantener compatibilidad durante la prueba; endurecer DNSSEC después.
DNSSEC=allow-downgrade
DNSOverTLS=no

# Avahi publica Nas.local; evitar dos propietarios mDNS/LLMNR sin probarlos.
LLMNR=no
MulticastDNS=no
DNSStubListener=yes
```

El perfil estricto usa únicamente AdGuard y conserva el filtrado local. Si se
prefiere disponibilidad sobre filtrado, se puede configurar una lista con
`DNS=192.168.1.201 1.1.1.1 8.8.8.8`, pero eso es un bypass deliberado y debe
probarse/documentarse como tal. `FallbackDNS` solo entra cuando no se conoce
ningún DNS por enlace o configuración; no debe presentarse como garantía de
failover cuando AdGuard está caído.

No duplicar políticas contradictorias en `10-eno1.network`. Si el archivo `.network` mantiene `DNS=1.1.1.1` y `DNS=8.8.8.8`, esos DNS por enlace pueden prevalecer sobre la intención de usar AdGuard. Elegir una única fuente de verdad y comprobarla con `resolvectl dns`.

## 7. Configurar el enlace `resolv.conf` sin destruirlo

Primero comprobar que existe el stub creado por el servicio:

```bash
test -e /run/systemd/resolve/stub-resolv.conf \
  && echo "Stub disponible" \
  || echo "Falta el stub de systemd-resolved"
```

Solo cuando el stub exista y `resolvectl status` sea correcto, sustituir el enlace o archivo mediante un movimiento reversible:

```bash
if [ -e /etc/resolv.conf ] || [ -L /etc/resolv.conf ]; then
    mv /etc/resolv.conf "$SNAPSHOT/resolv.conf.before-resolved"
fi
ln -s /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
```

No ejecutar como procedimiento normal:

```bash
rm /etc/resolv.conf
```

Ese comando puede dejar al host sin DNS y destruye información necesaria para el rollback.

Reiniciar el servicio para cargar el drop-in:

```bash
systemctl restart systemd-resolved
```

## 8. Validación por capas

### Host y stub local

```bash
readlink -f /etc/resolv.conf
resolvectl status
resolvectl dns
resolvectl query github.com
getent hosts github.com
```

```bash
ss -lntup | grep -E '127\.0\.0\.53:53|127\.0\.0\.54:53' || true
```

### AdGuard y red macvlan

```bash
ping -c 3 192.168.1.201
svc health
```

Si está disponible `dig`, probar directamente:

```bash
dig @192.168.1.201 github.com
dig @127.0.0.53 github.com
```

La segunda consulta debe pasar por `systemd-resolved`; la primera prueba directamente AdGuard.

### IPv6

```bash
ip -6 addr show dev eno1
ip -6 route
resolvectl query github.com
curl -6 --connect-timeout 10 https://github.com
```

No aplicar `IPv6AcceptRA=no` ni `LinkLocalAddressing=ipv4` si Home Assistant usa Matter, Thread o descubrimiento IPv6. Si solo se quiere detener el cliente DHCPv6, estudiar antes esta opción en el archivo de networkd:

```ini
[IPv6AcceptRA]
DHCPv6Client=no
```

Debe usarse solo si la LAN no entrega configuración IPv6 necesaria mediante DHCPv6. No es equivalente a desactivar IPv6 completo.

### Avahi y Home Assistant

```bash
systemctl status avahi-daemon --no-pager
avahi-resolve -n Nas.local
getent hosts Nas.local
grep '^hosts:' /etc/nsswitch.conf
```

`avahi-resolve` prueba Avahi directamente; `getent` prueba el camino NSS que
normalmente usa SSH y las aplicaciones. Si Avahi resuelve pero `getent` no,
revisar `libnss-mdns` y la línea `hosts:` de `nsswitch.conf` antes de culpar a
systemd-resolved.

Home Assistant usa `network_mode: host`, así que debe probarse desde el contenedor
si está instalado:

```bash
svc ps homeassistant
svc exec homeassistant getent hosts github.com
```

El compose catalogado de Home Assistant declara actualmente DNS públicos propios;
eso es una excepción y significa que `systemd-resolved` no gobierna
necesariamente el DNS interno de ese contenedor. Si se quiere que HA use AdGuard
o el stub del host, hay que revisar esa sección `dns:` en una tarea separada y
validar el `resolv.conf` real del contenedor. Si HA no está instalado, omitir
estas dos comprobaciones.

Probar además un descubrimiento real de un dispositivo IoT. Una resolución DNS correcta no garantiza que mDNS, SSDP, Matter o Thread funcionen.

### Docker bridge

Los contenedores bridge normalmente usan el DNS embebido de Docker (`127.0.0.11`). No cambiar `daemon.json` ni forzar el DNS del host sin comprobar primero la configuración Docker real:

```bash
svc config filebrowser
svc config homepage
```

## 9. IPv6, Avahi y reglas para Home Assistant

- Mantener IPv6 activo mientras se utilicen Matter, Thread o dispositivos que dependan de IPv6.
- No copiar la antigua configuración de Avahi con `use-ipv6=no` como receta general.
- Avahi debe conservar `use-ipv6=yes` cuando la LAN tenga IPv6 habilitado.
- `systemd-resolved` puede mantener `MulticastDNS=no` si Avahi es el propietario de mDNS; esto no desactiva IPv6 del kernel.
- El stub DNS no reemplaza el descubrimiento multicast de Home Assistant.
- Home Assistant con `network_mode: host` no debe tratarse como un contenedor bridge normal.

## 10. Rollback

Usar la consola local si se perdió SSH. El rollback es reanudable desde una
sesión nueva porque la ruta del snapshot queda guardada en `LATEST`.

### 10.1 Recuperar y validar el snapshot

```bash
SNAPSHOT_ROOT="${aadm:-}"
if [ -z "$SNAPSHOT_ROOT" ]; then
    SNAPSHOT_ROOT="$(getent passwd aadm | cut -d: -f6)"
fi
SNAPSHOT_ROOT="${SNAPSHOT_ROOT:-$HOME}"
SNAPSHOT_FILE="$SNAPSHOT_ROOT/network-snapshots/LATEST"
test -r "$SNAPSHOT_FILE" || {
    echo "No existe la ruta persistida del snapshot: $SNAPSHOT_FILE"
    exit 1
}
SNAPSHOT="$(< "$SNAPSHOT_FILE")"
test -d "$SNAPSHOT" || {
    echo "El snapshot no existe: $SNAPSHOT"
    exit 1
}
test -e "$SNAPSHOT/resolv.conf.before-resolved" || test -L "$SNAPSHOT/resolv.conf.before-resolved" || {
    echo "Falta la copia segura de resolv.conf; no se modifica el archivo activo"
    exit 1
}
```

### 10.2 Restaurar resolved y `resolv.conf`

```bash
systemctl stop systemd-resolved

if [ -e /etc/resolv.conf ] || [ -L /etc/resolv.conf ]; then
    mv /etc/resolv.conf "$SNAPSHOT/resolv.conf.failed-rollback"
fi
mv "$SNAPSHOT/resolv.conf.before-resolved" /etc/resolv.conf
```

Restaurar el directorio de drop-ins que pudo crear la instalación:

```bash
if [ -f "$SNAPSHOT/resolved.conf.d.absent" ]; then
    if [ -d /etc/systemd/resolved.conf.d ]; then
        mv /etc/systemd/resolved.conf.d "$SNAPSHOT/resolved.conf.d.after"
    fi
elif [ -d "$SNAPSHOT/resolved.conf.d" ]; then
    if [ -d /etc/systemd/resolved.conf.d ]; then
        mv /etc/systemd/resolved.conf.d "$SNAPSHOT/resolved.conf.d.after"
    fi
    mkdir -p /etc/systemd/resolved.conf.d
    cp -a "$SNAPSHOT/resolved.conf.d/." /etc/systemd/resolved.conf.d/
fi
```

Restaurar el estado inicial del servicio:

```bash
if grep -qx enabled "$SNAPSHOT/resolved.enabled" 2>/dev/null; then
    systemctl enable systemd-resolved
else
    systemctl disable systemd-resolved
fi

if grep -qx active "$SNAPSHOT/resolved.active" 2>/dev/null; then
    systemctl start systemd-resolved
else
    systemctl stop systemd-resolved
fi
```

### 10.3 Restaurar networkd o Avahi solo si fueron modificados

No restaurar estos directorios si solo se instaló resolved. Si también se
cambiaron archivos de red, hacerlo desde la consola y antes de recargar networkd:

```bash
mv /etc/systemd/network "$SNAPSHOT/network.after-rollback"
mkdir -p /etc/systemd/network
cp -a "$SNAPSHOT/network/." /etc/systemd/network/

mv /etc/avahi "$SNAPSHOT/avahi.after-rollback"
mkdir -p /etc/avahi
cp -a "$SNAPSHOT/avahi/." /etc/avahi/
```

```bash
systemctl reload systemd-networkd
systemctl restart avahi-daemon
```

Comprobar recuperación:

```bash
networkctl status eno1
ip route
getent hosts github.com
avahi-resolve -n Nas.local
```

No borrar el snapshot hasta haber reiniciado el NAS y validado SSH, DNS, IPv6,
Avahi, AdGuard y Home Assistant.

## 11. Diagnóstico rápido

| Síntoma | Causa probable | Acción segura |
|---|---|---|
| No hay SSH por IP ni `Nas.local` | `eno1`, gateway o networkd | Usar consola; restaurar `.network`; recargar networkd |
| SSH funciona pero no hay dominios | `resolv.conf`, stub o upstream | `resolvectl status`; revisar symlink y `DNS=` |
| AdGuard no recibe consultas | shim, macvlan o IP incorrecta | Probar `ping 192.168.1.201` y `dig @192.168.1.201` |
| `Nas.local` no resuelve | Avahi o mDNS | Revisar `avahi-daemon`, `avahi-resolve` y firewall |
| HA deja de descubrir dispositivos | IPv6/mDNS/Matter/Thread | Restaurar IPv6; no usar `LinkLocalAddressing=ipv4` |
| Puerto 53 ocupado | stub, AdGuard bridge o otro DNS | Identificar TCP y UDP antes de cambiar servicios |
| GitHub no responde | ruta, DNS o salida TCP 443 | `ip route get 1.1.1.1`, `resolvectl query`, `curl -4` |

## Referencias oficiales

- [systemd-resolved](https://www.freedesktop.org/software/systemd/man/devel/systemd-resolved.service.html)
- [resolved.conf](https://www.freedesktop.org/software/systemd/man/devel/resolved.conf.html)
- [systemd.network](https://www.freedesktop.org/software/systemd/man/devel/systemd.network.html)
- [Avahi documentation](https://avahi.org/documentation/)

Estas referencias se consultaron para describir el stub local, `DNS=`, `FallbackDNS=`, dominios route-only, integración con `systemd-networkd` y la separación entre DNS unicast y descubrimiento mDNS.
