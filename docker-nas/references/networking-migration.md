# Derivación de migración — cambio de backend o de rango IP

> **Propósito:** migrar un NAS existente sin perder SSH, sin dejar DHCP residual y sin romper el shim macvlan, AdGuard, IPv6 o Home Assistant.
> **Fuente de verdad:** [`networking.md`](networking.md). Esta derivación contiene decisiones propias de una migración; el snapshot, el rollback y la validación completa siguen siendo los de la guía canónica.
> **No es una receta de cambio de rango específica:** las redes `192.168.0.x` de los drafts son históricas. El rango real debe obtenerse del preflight y del router actual.

## 1. Cuándo usar este procedimiento

Usar esta derivación si ya existe una instalación y se va a:

- sustituir `ifupdown`/`networking` por `systemd-networkd`;
- cambiar la IP, gateway o prefijo del host;
- cambiar la subred donde vive AdGuard macvlan;
- corregir un shim macvlan existente;
- conservar temporalmente acceso por la red antigua mientras se prueba la nueva.

Si solo se va a instalar `systemd-resolved` y `systemd-networkd` ya está verificado, seguir [`networking.md`](networking.md) y no cambiar los archivos `.network` sin necesidad.

Variables de la instalación actual; confirmar o sustituirlas antes de ejecutar pruebas:

```bash
IFACE="${IFACE:-eno1}"
ADGUARD_IP="${ADGUARD_IP:-192.168.1.201}"
```

Esta derivación cubre la migración desde `ifupdown`/`networking`. Si `NetworkManager` está activo, no iniciar `systemd-networkd` en paralelo ni ejecutar el flujo de retirada de `networking`:

```bash
if systemctl is-active --quiet NetworkManager; then
    echo "NetworkManager está activo; esta migración requiere un plan específico desde consola."
    exit 1
fi
```

## 2. Guardarraíles

1. Trabajar desde consola física/KVM o con una sesión SSH secundaria abierta.
2. Crear el snapshot de [`networking.md`](networking.md) antes de editar `/etc`.
3. Confirmar interfaz física, IP/gateway actuales y destino con comandos de solo lectura.
4. Mantener un único gateway por defecto durante la transición, salvo que exista un diseño explícito de enrutamiento.
5. No usar `ip addr flush`, `docker network prune`, `rm /etc/resolv.conf` ni `systemctl mask networking` como atajos.
6. No desactivar IPv6 para resolver un problema de DHCPv6 o de descubrimiento.
7. No retirar la configuración antigua hasta validar el nuevo SSH, la ruta a AdGuard, DNS, Avahi, IPv6 y Home Assistant.

## 3. Inventario previo

```bash
ip -br addr
ip route
ip -6 addr
ip -6 route
networkctl status
systemctl is-active systemd-networkd
systemctl is-active networking
systemctl is-active NetworkManager
readlink -f /etc/resolv.conf
resolvectl status 2>&1 || true
```

Revisar los archivos existentes sin modificarlos:

```bash
ls -la /etc/systemd/network
bat /etc/systemd/network/*.network /etc/systemd/network/*.netdev
```

Si la migración afecta AdGuard, comprobar antes la ruta y la respuesta directa:

```bash
ip route get "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
```

Registrar también todos los valores fijos relacionados con el rango antiguo en la configuración Docker real. Operar los servicios con `svc`; no reconstruir redes con comandos Docker directos.

## 4. Estrategia de cambio de rango

### 4.1 Opción preferida: ventana controlada

Si se dispone de consola y el cambio puede causar un corte breve:

1. Guardar snapshot.
2. Cambiar la IP, gateway y DNS del archivo de la interfaz física.
3. Cambiar IP/ruta del shim.
4. Recargar networkd desde consola.
5. Reconectar por la IP nueva.
6. Actualizar y recrear la red macvlan de AdGuard mediante el flujo documentado del servicio.
7. Probar DNS directo, stub, IPv6, Avahi y HA.

Esta opción evita mantener dos redes lógicas en la interfaz durante más tiempo del necesario.

### 4.2 Opción puente: doble IP temporal

Si se necesita mantener SSH por la red antigua mientras se activa el router nuevo, se pueden declarar temporalmente dos líneas `Address=` en el mismo `.network`:

```ini
[Network]
Address=<IP_ANTIGUA>/<PREFIJO>
Address=<IP_NUEVA>/<PREFIJO>
Gateway=<GATEWAY_NUEVO>
DNS=<DNS_PROVISIONAL>
DHCP=no
MACVLAN=macvlan-shim
ConfigureWithoutCarrier=yes
```

Esta técnica solo es válida si ambas subredes comparten el mismo enlace de capa 2 y las rutas son conocidas. No crea conectividad entre routers aislados, VLANs distintas o cables desconectados. Mantener una sola ruta por defecto y no asumir que las dos gateways son intercambiables.

Después de validar la nueva red, eliminar la línea antigua y volver a aplicar networkd. La doble IP es un puente de migración, no un estado final.

## 5. Orden de modificación

### 5.1 Interfaz física

Editar el archivo `.network` que realmente coincide con la interfaz. Conservar `DHCP=no`, `MACVLAN=` y `ConfigureWithoutCarrier=yes` si forman parte del diseño confirmado:

```ini
[Match]
Name=<INTERFAZ_REAL>

[Network]
Address=<IP_NUEVA>/<PREFIJO>
Gateway=<GATEWAY_NUEVO>
DNS=<DNS_PROVISIONAL>
DHCP=no
MACVLAN=macvlan-shim
ConfigureWithoutCarrier=yes
```

Si se usa la opción de doble IP, conservar temporalmente también `Address=<IP_ANTIGUA>/<PREFIJO>`.

### 5.2 Shim macvlan

El archivo `.netdev` normalmente no cambia si el parent físico sigue siendo el mismo. El `.network` sí debe apuntar al rango nuevo:

```ini
[Match]
Name=macvlan-shim

[Network]
Address=<SHIM_NUEVO>/32

[Route]
Destination=<ADGUARD_NUEVO>/32
Scope=link
```

Si se necesita una transición sin corte y se ha verificado que ambas redes están disponibles, se pueden conservar temporalmente dos direcciones del shim y dos rutas de destino. Retirar la pareja antigua después de validar AdGuard; no dejar rutas históricas indefinidamente.

### 5.3 Aplicar y comprobar networkd

```bash
networkctl reload
networkctl reconfigure <INTERFAZ_REAL>
sleep 2
networkctl status <INTERFAZ_REAL>
ip -br addr show dev <INTERFAZ_REAL>
ip -br addr show dev macvlan-shim
ip route
ip route get <GATEWAY_NUEVO>
```

Si la sesión SSH se corta, no insistir con comandos remotos: usar [`networking-recovery.md`](networking-recovery.md).

## 6. Actualizar AdGuard y redes macvlan

Si cambia la subred macvlan, deben cambiar juntos:

- `ipv4_address` del contenedor AdGuard;
- `subnet` y `gateway` de la red macvlan;
- parent físico, si también cambió la interfaz;
- IP/ruta del shim;
- cualquier otro servicio con IP fija en la misma subred.

El cambio de un archivo Compose no se aplica con un simple restart de contenedor: la definición de red se conserva hasta recrearla. Antes de tocar la configuración, guardar el estado del servicio y revisar la configuración resuelta:

```bash
svc snapshot adguard
svc config adguard
svc ps adguard
```

La configuración que se edite debe conservar el contrato macvlan vigente: nombre de red `adguard_macvlan_NET`, parent físico confirmado, subnet/gateway del rango nuevo e IP fija de AdGuard. En este repositorio no hay un compose catalogado de AdGuard; por eso no se inventa uno en esta guía. Si la fuente operativa del servicio no está disponible en el NAS, detenerse y recuperarla antes de recrear nada.

Después de actualizar esa fuente operativa y verificarla, recrear solo el servicio:

```bash
svc down adguard
svc up adguard
svc ps adguard
svc health
```

No ejecutar `docker network prune -f`: puede borrar redes no relacionadas. Si `svc up` no puede recrear la red macvlan, detenerse; no sustituirla por una red bridge ni crear una red manual con parámetros adivinados.

## 7. Cambiar DNS después de la red

No modificar el enlace de `/etc/resolv.conf` durante la primera fase. Primero demostrar:

```bash
ip route get "$ADGUARD_IP"
dig +time=2 +tries=1 "@$ADGUARD_IP" github.com
```

Después de actualizar la IP de AdGuard, revisar también el drop-in persistente de resolved. Cambiar `DNS=` al destino nuevo **antes** de retirar el destino antiguo:

```bash
ls -l /etc/systemd/resolved.conf.d/10-nas.conf
bat /etc/systemd/resolved.conf.d/10-nas.conf
nano /etc/systemd/resolved.conf.d/10-nas.conf
```

Luego recargar y validar el upstream real:

```bash
systemctl restart systemd-resolved
resolvectl dns
resolvectl query github.com
dig +time=2 +tries=1 @127.0.0.53 github.com
```

No retirar la dirección/ruta antigua ni cerrar la ventana de mantenimiento hasta que el DNS nuevo responda por AdGuard directo y por el stub.


## 8. Cierre de la migración

Solo retirar la IP/ruta antigua o purgar componentes antiguos después de verificar:

```bash
systemctl is-enabled systemd-networkd
systemctl is-active systemd-networkd
systemctl is-active networking
ip -br addr
ip route
ip -6 route
resolvectl status
getent hosts github.com
avahi-resolve -n Nas.local
```

Además:

- abrir una nueva sesión SSH por la IP nueva;
- probar `dig` directamente contra AdGuard y contra `127.0.0.53`;
- comprobar el contenedor Home Assistant en `network_mode: host`;
- probar un descubrimiento IoT real, no solo DNS;
- reiniciar el NAS en una ventana controlada y repetir la validación;
- cancelar el trabajo de `at` si se programó un rescate;
- conservar el snapshot hasta terminar la validación post-reinicio.

Si la migración fue de `192.168.0.x` a `192.168.1.x`, no asumir que el cambio terminó al ver SSH: el shim, AdGuard, DNS, Homepage, labels, rutas y otros compose con IPs fijas deben quedar en el mismo modelo de red confirmado.