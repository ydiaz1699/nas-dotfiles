# 📦 Derivación de instalación — systemd-networkd, macvlan y systemd-resolved

> **Propósito:** procedimiento para una instalación nueva o para un Debian que todavía usa `ifupdown`/`networking`.
> **Fuente de verdad:** [`networking.md`](networking.md). Esta derivación solo añade la secuencia de instalación; no reemplaza el preflight, el snapshot, la validación ni el rollback de la guía canónica.
> **Estado:** plantilla parametrizada. Los valores del NAS actual (`192.168.1.x`, `eno1`) son un perfil declarado, no valores que deban copiarse a otro equipo.

## 1. 🧭 Condiciones antes de empezar

No comenzar sin:

- consola física, KVM o un canal fuera de banda para recuperar el equipo;
- una segunda sesión SSH disponible durante la migración;
- nombre confirmado de la interfaz física, gateway, prefijo, IP estática y rango DHCP;
- conocimiento de si el host usa `networking`, NetworkManager u otro backend;
- un plan de IPs sin conflictos para el host, el shim y AdGuard;
- la guía canónica `networking.md` leída, especialmente sus secciones de snapshot y rollback.

Esta derivación configura el backend del host. La creación del servicio AdGuard debe respetar `docs/docker-entorno.md` y la configuración vigente del servicio; no copiar aquí un `compose.yaml` histórico con IPs del rango `192.168.0.x`.

## 2. ⚙️ Variables que deben confirmarse

Sustituir los valores de ejemplo después del preflight; no asumir que `eno1` ni el rango actual aplican a otro NAS:

```bash
IFACE="${IFACE:-eno1}"
HOST_IP="${HOST_IP:-192.168.1.200}"
PREFIX="${PREFIX:-24}"
GATEWAY="${GATEWAY:-192.168.1.1}"
SHIM_IP="${SHIM_IP:-192.168.1.250}"
ADGUARD_IP="${ADGUARD_IP:-192.168.1.201}"
```

Este procedimiento usa deliberadamente el nombre estable `macvlan-shim` para que el `.netdev`, el `.network`, `MACVLAN=` y las comprobaciones siempre coincidan. Si otro equipo necesita otro nombre, cambiarlo en **todos** esos lugares antes de continuar.

Confirmar los valores antes de continuar:

```bash
ip -br link
ip route
systemctl is-active systemd-networkd
systemctl is-active NetworkManager
systemctl is-active networking
```

Esta derivación cubre un host nuevo o una migración desde `ifupdown`/`networking`. Si `NetworkManager` está activo, detenerse: no iniciar networkd en paralelo. Esa migración necesita un plan específico desde consola y queda fuera de este runbook hasta documentar la retirada de NetworkManager.

```bash
if systemctl is-active --quiet NetworkManager; then
    echo "NetworkManager está activo; no iniciar systemd-networkd en paralelo."
    exit 1
fi
```

Antes de crear archivos, inventariar también el backend legacy por interfaz:

```bash
bat /etc/network/interfaces 2>/dev/null || true
find /etc/network/interfaces.d -maxdepth 2 -type f -print \
    -exec bat {} \; 2>/dev/null || true
systemctl status "ifup@$IFACE.service" --no-pager 2>&1 || true
systemctl show "ifup@$IFACE.service" \
    -p FragmentPath -p ExecStart -p SubState -p UnitFileState 2>&1 || true
pgrep -af "dhcpcd.*$IFACE|dhclient.*$IFACE" || true
```

`DHCP=no` en el archivo de networkd no desactiva ifupdown ni dhcpcd. Si se
encuentra `allow-hotplug`, `auto` o `iface $IFACE inet dhcp`, no activar aún
networkd: primero guardar snapshot y neutralizar el propietario legacy en la
sección 5. La migración solo puede continuar cuando un único backend administra
la interfaz.

Si hay dudas sobre la interfaz, no crear archivos todavía. `IFACE` debe coincidir exactamente con la interfaz física que conecta al router/switch.

## 3. 💾 Snapshot y rescate opcional

Ejecutar primero el snapshot de la sección **4. Snapshot reversible** de [`networking.md`](networking.md). El snapshot es el mecanismo de recuperación principal.

Como protección adicional, se puede programar un rescate temporal **solo si** `networking` está activo y su configuración anterior todavía puede restaurar la conectividad:

```bash
systemctl is-active --quiet networking || {
    echo "No usar este rescate: networking no está activo o no es el backend anterior."
    exit 1
}

command -v at >/dev/null || {
    echo "Falta at; instalarlo solo si se desea usar este rescate: instal at"
    exit 1
}

systemctl is-active --quiet atd || {
    echo "atd no está activo; no continuar con este método de rescate."
    exit 1
}

printf '%s\n' 'systemctl restart networking' | at now + 5 minutes
atq
```

Anotar el identificador del trabajo mostrado por `atq`. Si la migración termina correctamente, cancelarlo con:

```bash
atrm <ID_DEL_TRABAJO>
```

No usar esta protección cuando `networking` ya está deshabilitado, enmascarado o no tiene una configuración funcional. En ese caso solo la consola/OOB y el snapshot son confiables.

## 4. 🛠️ Crear los archivos de networkd antes de tocar servicios

Respetar siempre el orden `mkdir → archivos → permisos/validación → servicios`:

```bash
mkdir -p /etc/systemd/network
```

### 4.1 🖧 Interfaz física

Crear `/etc/systemd/network/10-${IFACE}.network` con los valores confirmados:

```ini
[Match]
Name=<IFACE_CONFIRMADA>

[Network]
Address=<HOST_IP>/<PREFIX>
Gateway=<GATEWAY_CONFIRMADO>
DNS=<DNS_INICIAL_CONFIRMADO>
DHCP=no
MACVLAN=macvlan-shim
ConfigureWithoutCarrier=yes
```

Notas:

- `DHCP=no` evita que networkd solicite otra dirección dinámica.
- `ConfigureWithoutCarrier=yes` permite aplicar la configuración aunque el carrier tarde en aparecer; no arregla un cable desconectado, una NIC apagada ni un fallo físico.
- `MACVLAN=macvlan-shim` debe coincidir exactamente con `Name=` del archivo `.netdev`.
- No dejar DNS públicos por enlace si la política final será que el host use AdGuard. La sección de `systemd-resolved` en la guía canónica define la fuente de DNS después de comprobar conectividad.

### 4.2 🔗 Interfaz macvlan del host

Crear `/etc/systemd/network/20-macvlan-shim.netdev`:

```ini
[NetDev]
Name=macvlan-shim
Kind=macvlan

[MACVLAN]
Mode=bridge
```

Crear `/etc/systemd/network/20-macvlan-shim.network`:

```ini
[Match]
Name=macvlan-shim

[Network]
Address=<SHIM_IP>/32

[Route]
Destination=<ADGUARD_IP>/32
Scope=link
```

La ruta `/32` limita el uso del shim al destino macvlan. No convertir el shim en un segundo gateway ni agregar una ruta por defecto.

## 5. 🧹 Neutralizar el backend legacy antes de activar networkd

No iniciar `systemd-networkd` mientras `ifupdown`, `ifup@${IFACE}.service`,
`dhcpcd`, `dhclient` o NetworkManager todavía puedan modificar la misma
interfaz. La coexistencia no es una fase segura por defecto: en el incidente
confirmado, `ifup@eno1.service` ejecutó `ifup --allow=hotplug eno1`, inició
dhcpcd y este eliminó/recreó las rutas que networkd había aplicado.

Crear el snapshot de [`networking.md`](networking.md) antes de editar. Después,
si el backend deseado es networkd, editar `/etc/network/interfaces` y comentar
solo la stanza de la interfaz física:

```text
# allow-hotplug <IFACE_CONFIRMADA>
# iface <IFACE_CONFIRMADA> inet dhcp
```

No borrar el archivo completo, no purgar todavía `ifupdown` y no tocar el
loopback. Si la stanza usa otra forma de DHCP, conservarla en el snapshot y
marcarla para revisión; no asumir que solo esas dos líneas son suficientes.

Detener la unidad instanciada y comprobar su resultado:

```bash
systemctl stop "ifup@$IFACE.service" 2>&1 || true
sleep 2
systemctl is-active "ifup@$IFACE.service" 2>&1 || true

if pgrep -af "dhcpcd.*$IFACE|dhclient.*$IFACE" >/dev/null; then
    echo "El cliente DHCP sigue gestionando $IFACE; detenerse y usar su mecanismo de control documentado."
    exit 1
fi
```

No usar `pkill`, `kill -9` ni matar PIDs encontrados por texto. Si el proceso
`dhcpcd` sigue vivo, identificar su unidad/cgroup y detener el propietario real
antes de continuar. Si `ifup@${IFACE}.service` no existe, registrar ese hecho y
comprobar que tampoco haya otro supervisor.

La compuerta para continuar es:

```bash
if grep -RnsE "^[[:space:]]*(auto|allow-hotplug)[[:space:]]+$IFACE|^[[:space:]]*iface[[:space:]]+$IFACE[[:space:]]+inet[[:space:]]+dhcp" \
    /etc/network/interfaces /etc/network/interfaces.d 2>/dev/null; then
    echo "Todavía existe una stanza ifupdown para $IFACE; no activar networkd."
    exit 1
fi

if systemctl is-active --quiet "ifup@$IFACE.service" || \
   pgrep -af "dhcpcd.*$IFACE|dhclient.*$IFACE" >/dev/null; then
    echo "Todavía existe otro propietario de $IFACE; no activar networkd."
    exit 1
fi
```

## 6. 🔌 Activar networkd después de asegurar exclusividad

Solo después de superar la compuerta anterior:

```bash
systemctl enable systemd-networkd.service
systemctl start systemd-networkd.service
networkctl reload
networkctl reconfigure "$IFACE"
```

Comprobar que la dirección y las rutas existen en el kernel, no solo que
`networkctl` diga `configured`:

```bash
networkctl status "$IFACE"
ip -4 addr show dev "$IFACE"
ip route
ip route get "$GATEWAY"
ip route get "$ADGUARD_IP"
ping -c 3 -W 2 "$GATEWAY"
ping -c 3 -W 2 1.1.1.1
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
```

El resultado esperado incluye `HOST_IP/PREFIX`, la ruta conectada de la LAN y
una ruta por defecto `proto static`. Si aparece `proto dhcp`, una dirección
dinámica o vuelve a aparecer `dhcpcd`, detenerse: todavía existe un propietario
legacy.

`systemd-networkd-wait-online.service` no configura la interfaz ni corrige
`NO-CARRIER`. Solo debe habilitarse si el sistema realmente necesita bloquear
servicios hasta tener red y después de medir el efecto sobre el arranque.

## 7. 🧩 Retirar ifupdown de forma controlada

Solo después de validar la nueva IP desde una segunda sesión:

```bash
systemctl is-active networking 2>&1 || true
systemctl is-enabled networking 2>&1 || true
pgrep -af "dhcpcd.*$IFACE|dhclient.*$IFACE" || true
systemctl is-active "ifup@$IFACE.service" 2>&1 || true
```

No es necesario ejecutar `systemctl disable --now networking` si el servicio no
es el propietario activo. Si sí está activo, detenerlo solo después de confirmar
que la configuración de ifupdown ya no administra `$IFACE`; la unidad instanciada
`ifup@${IFACE}.service` debe comprobarse por separado.

No eliminar todavía `/etc/network/interfaces` ni purgar `ifupdown`. Mantener una
ruta de vuelta hasta haber realizado un reinicio controlado y validado SSH,
gateway, Internet y DNS.

## 8. 🛡️ Verificar el shim y después desplegar AdGuard

El shim debe existir antes de desplegar el contenedor:

```bash
ip -br addr show dev macvlan-shim
ip route get "$ADGUARD_IP"
```

Cuando AdGuard esté desplegado según sus archivos actuales, comprobar:

```bash
ping -c 3 "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
```

Usar `svc` para operar el servicio; no usar `docker compose`, `docker network prune` ni rutas de compose copiadas de los borradores. La red macvlan debe conservar el mismo parent, subnet y gateway que la red física confirmada.

Después de probar el host y AdGuard, seguir la instalación de `systemd-resolved` desde la sección 5 de [`networking.md`](networking.md). No cambiar `/etc/resolv.conf` antes de comprobar el stub y la respuesta directa de AdGuard.

## 9. 🔄 Reinicio de aceptación

Antes del reinicio:

```bash
systemctl is-enabled systemd-networkd
systemctl is-active systemd-networkd
networkctl status "$IFACE"
ip route
ip -6 route
```

Mantener la consola/OOB disponible y una segunda sesión SSH. Después del reinicio validar en este orden:

1. IP del host y gateway.
2. IP/ruta del shim.
3. AdGuard directamente con `dig`.
4. Stub `127.0.0.53` y `resolvectl`.
5. IPv6, Avahi/NSS y `Nas.local`.
6. Home Assistant, Matter/Thread y un descubrimiento IoT real.
7. Contenedores bridge mediante `svc`, sin cambiar globalmente el DNS de Docker.

Si falla cualquier capa, detenerse y usar [`networking-recovery.md`](networking-recovery.md).