# Derivación de recuperación — red, DNS, macvlan y SSH

> **Propósito:** recuperar un NAS después de una pérdida de red, un reinicio en frío, una migración incompleta o un cambio de `systemd-resolved`.
> **Fuente de verdad:** [`networking.md`](networking.md). Esta derivación es un runbook de triage; el rollback completo del snapshot está en la sección 10 de la guía canónica.
> **Regla:** si no hay SSH, dejar de ejecutar comandos remotos y pasar a consola física, KVM o canal fuera de banda.

## 1. Antes de cambiar nada

Desde consola:

```bash
IFACE="${IFACE:-eno1}"
ADGUARD_IP="${ADGUARD_IP:-192.168.1.201}"
```

Confirmar o sustituir estos valores por los del NAS antes de ejecutar el triage. Desde consola:

```bash
ip -br link
ip -br addr
ip route
ip -6 route
systemctl is-active systemd-networkd
systemctl is-enabled systemd-networkd
systemctl is-active networking
systemctl is-active systemd-resolved
systemctl is-active avahi-daemon
```

Guardar la evidencia antes de corregir:

```bash
journalctl -u systemd-networkd -b --no-pager -n 100
journalctl -u systemd-resolved -b --no-pager -n 100
networkctl status
resolvectl status 2>&1 || true
```

No ejecutar todavía `ip addr flush`, no borrar `/etc/resolv.conf`, no purgar `ifupdown` y no aplicar `docker network prune`.

## 2. Árbol rápido de decisión

### A. `eno1` está `DOWN` o `NO-CARRIER`

1. Revisar cable, switch, puerto y luces de la NIC.
2. Confirmar que el nombre de interfaz no cambió:

```bash
ip -o link show
networkctl list
```

3. Si el cable está conectado, revisar el driver y el estado:

```bash
networkctl status $IFACE
ethtool $IFACE 2>/dev/null || true
```

`ConfigureWithoutCarrier=yes` permite aplicar una configuración estática antes de detectar carrier, pero no puede solucionar una desconexión física ni un fallo de hardware.

### B. La interfaz está `UP` pero no tiene la IP esperada

Leer los archivos antes de editarlos:

```bash
ls -la /etc/systemd/network
bat /etc/systemd/network/*.network /etc/systemd/network/*.netdev
networkctl status $IFACE
```

Si el archivo existe y fue modificado recientemente:

```bash
networkctl reload
networkctl reconfigure $IFACE
ip -br addr show dev $IFACE
ip route
```

Si la configuración actual es incorrecta y hay snapshot, seguir la restauración selectiva de la sección **5**. No reconstruir un archivo a partir de memoria ni copiar el rango histórico `192.168.0.x` sin confirmar el router.

### C. Hay una IP DHCP residual o dos IPs inesperadas

Identificar el responsable:

```bash
ip addr show dev $IFACE
pgrep -a dhclient || true
systemctl status networking --no-pager
systemctl status dhcpcd --no-pager 2>/dev/null || true
```

La coexistencia de una IP antigua y una nueva puede ser temporal durante una migración. No quitar direcciones con `flush`; detener solo el servicio DHCP confirmado y volver a aplicar networkd. La doble IP deliberada se explica en [`networking-migration.md`](networking-migration.md).

### D. SSH funciona por IP, pero no resuelven dominios

Separar red, AdGuard, resolved y el enlace:

```bash
readlink -f /etc/resolv.conf
ls -l /etc/resolv.conf
resolvectl status
resolvectl dns
ip route get "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
dig +time=2 +tries=1 @127.0.0.53 github.com
```

Interpretación:

- falla `ip route get`: problema de interfaz, gateway o ruta;
- falla `dig @$ADGUARD_IP`: problema de shim, macvlan, AdGuard o firewall;
- funciona AdGuard pero falla `@127.0.0.53`: problema de `systemd-resolved`, drop-in o stub;
- funciona el stub pero falla `getent`: revisar NSS y `nsswitch.conf`.

No sustituir el diagnóstico por `echo nameserver ... > /etc/resolv.conf`. Si el stub o el drop-in están mal, aplicar el rollback selectivo de la sección **5**.

### E. El host no llega a AdGuard macvlan

```bash
ip -br addr show dev macvlan-shim
ip route get "$ADGUARD_IP"
systemctl status systemd-networkd --no-pager
journalctl -u systemd-networkd -b --no-pager -n 100
svc ps adguard
svc health
```

Verificar que:

- `macvlan-shim` existe y tiene una dirección `/32` del rango actual;
- la ruta a la IP de AdGuard sale por el shim;
- `MACVLAN=` del archivo de la interfaz coincide con el nombre del `.netdev`;
- parent, subnet, gateway e IP del servicio pertenecen al mismo diseño vigente;
- el contenedor está operativo.

Si se modificó el rango, seguir [`networking-migration.md`](networking-migration.md). No usar `docker network prune -f` para intentar reparar una red.

### F. `Nas.local` no resuelve o desaparece el descubrimiento

```bash
systemctl status avahi-daemon --no-pager
avahi-resolve -n Nas.local
getent hosts Nas.local
grep '^hosts:' /etc/nsswitch.conf
ip -6 addr show dev $IFACE
ip -6 route
```

`avahi-resolve` prueba Avahi directamente y `getent` prueba NSS. Si Avahi funciona pero NSS no, revisar `libnss-mdns` y `nsswitch.conf`. No activar `MulticastDNS=yes` en resolved como reacción automática: Avahi sigue siendo el propietario de la publicación mDNS.

### G. Home Assistant perdió descubrimiento

Primero comprobar la red del host y luego el contenedor:

```bash
ip -6 addr show dev $IFACE
ip -6 route
systemctl status avahi-daemon --no-pager
svc ps homeassistant
svc exec homeassistant getent hosts github.com
```

No concluir que el DNS está bien porque `dig` funciona. Probar el descubrimiento real del dispositivo. Matter y Thread necesitan IPv6; no aplicar `IPv6AcceptRA=no`, `LinkLocalAddressing=ipv4` ni `use-ipv6=no` sin confirmar que no se usan.

### H. El puerto 53 está ocupado

```bash
ss -lntup | grep -E '(:53[[:space:]]|:5353[[:space:]])' || true
```

Identificar si el propietario es el stub local, AdGuard, Avahi u otro proceso antes de detenerlo. No desactivar resolved ni AdGuard por reflejo.

## 3. Recuperar la conectividad mínima

Si el problema es networkd y se está trabajando desde consola:

```bash
systemctl restart systemd-networkd
sleep 2
networkctl status $IFACE
ip -br addr
ip route
```

Si la recuperación temporal requiere el backend anterior, usarlo solo si existe una configuración conocida y respaldada:

```bash
systemctl enable --now networking
```

No ejecutar esto si `networking` fue deshabilitado porque su configuración ya no es válida. En ese caso restaurar primero el snapshot o corregir el archivo desde consola.

Cuando vuelva SSH, abrir una segunda sesión y validar todas las capas antes de reiniciar.

## 4. Recuperar solo el DNS

Si la red y AdGuard funcionan, pero resolved no:

```bash
ip route get "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
test -e /run/systemd/resolve/stub-resolv.conf
systemctl status systemd-resolved --no-pager
```

Si el stub existe, comprobar el drop-in y reiniciar solo resolved:

```bash
ls -la /etc/systemd/resolved.conf.d
resolvectl status
systemctl restart systemd-resolved
```

Después verificar el symlink de `/etc/resolv.conf`. Si el drop-in o el enlace fueron el cambio que provocó la caída, no improvisar: usar el rollback selectivo de la sección siguiente.

## 5. Rollback selectivo desde `LATEST`

Usar la sección **10. Rollback** de [`networking.md`](networking.md) como procedimiento completo. La secuencia de decisión es:

1. Recuperar `SNAPSHOT_ROOT` y validar `network-snapshots/LATEST`.
2. Si solo se instaló o configuró resolved, restaurar `resolv.conf`, drop-ins y estado de resolved; no tocar networkd ni Avahi.
3. Si también se cambiaron archivos de red, restaurar `/etc/systemd/network` desde el snapshot desde consola.
4. Si también se cambió Avahi, restaurar `/etc/avahi` solo en ese caso.
5. Recargar networkd y reiniciar únicamente los servicios modificados.
6. Validar IP, ruta, SSH, AdGuard, DNS, IPv6 y `Nas.local` antes de volver a arrancar Docker o Home Assistant.

Antes de mover cualquier archivo, comprobar que la copia existe. Si falta `resolv.conf.before-resolved`, no inventar una restauración: determinar si el enlace nunca se cambió o si la copia original se encuentra con otro nombre en el snapshot.

## 6. Validación de recuperación

```bash
networkctl status $IFACE
ip -br addr
ip route
ip -6 route
readlink -f /etc/resolv.conf
resolvectl status
getent hosts github.com
ip route get "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
dig +time=2 +tries=1 @127.0.0.53 github.com
avahi-resolve -n Nas.local
svc health
svc ps homeassistant
```

Después de una migración o rollback, reiniciar en una ventana controlada y repetir la lista. Conservar el snapshot hasta confirmar un reinicio correcto, una sesión SSH nueva, DNS, IPv6, mDNS, AdGuard y descubrimiento de Home Assistant.

## 7. Datos que registrar para mejorar la guía

Cuando se resuelva una incidencia, guardar en la documentación de la sesión:

- síntoma y momento del fallo;
- salida relevante de `networkctl`, `ip`, `resolvectl`, `journalctl` y `ss`;
- archivo y línea que causó el problema;
- si el fallo era físico, networkd, shim, Docker/macvlan, resolved, Avahi, IPv6 o HA;
- procedimiento de recuperación que funcionó;
- validaciones posteriores.

No copiar secretos ni convertir una salida puntual del NAS en una regla general sin marcarla como `verificada`, `declarada` o `pendiente`.