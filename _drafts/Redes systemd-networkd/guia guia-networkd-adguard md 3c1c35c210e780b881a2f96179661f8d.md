# guia guia-networkd-adguard.md

# Guía completa: Debian + systemd-networkd + Docker Compose + AdGuard (macvlan)

---

## 📌 Historial de migración de red

| Fecha aprox. | Cambio | Motivo |
| --- | --- | --- |
| Config. original | Rango `192.168.0.X` | Router original `192.168.0.1/24` |
| Migración actual | Rango `192.168.1.X` | Cambio de router — el nuevo reparte en `192.168.1.1/24` |

**Qué hacer en el futuro si el router vuelve a cambiar de rango:**

1. Identificar el nuevo rango y gateway del router (`ipconfig` en Windows, o revisar la config del router).
2. Actualizar `Address` y `Gateway` en `/etc/systemd/network/10-eno1.network`.
3. Actualizar `Address` y `Route/Destination` en `/etc/systemd/network/20-macvlan-shim.network`.
4. Actualizar `ipv4_address`, `subnet` y `gateway` en **cada** `compose.yaml` que use la red `macvlan_NET` (o cualquier red Docker con IP fija).
5. Revisar **todos** los demás servicios en `/docker/<servicio>/compose.yaml` por si tienen IPs, gateways o subredes hardcodeadas del rango viejo — no solo AdGuard.
6. `systemctl restart systemd-networkd` para la red del host.
7. Para redes Docker macvlan: `docker compose down` + `docker network prune -f` + `docker compose up -d` (un `restart` simple no recrea la red).
8. Reconectar SSH con la IP nueva y verificar `ping` + `curl` a cada contenedor migrado.

> ⚠️ **Importante**: un simple `restart` de systemd-networkd alcanza para la red del host, pero **no** para redes Docker macvlan — esas necesitan recrearse (`down` + `up`), porque Docker cachea la definición de subred/gateway al crear la red.
> 

---

## Mapa de IPs (actualizado — rango `192.168.1.X`)

| Dispositivo | IP |
| --- | --- |
| Tu servidor (eno1) | `192.168.1.200` |
| Host shim (macvlan-shim) | `192.168.1.250` |
| AdGuard (contenedor) | `192.168.1.201` |
| Router | `192.168.1.1` |

> ⚠️ Ajusta estas IPs a tu red si es necesario. Mantenelas fuera del rango DHCP del router para evitar conflictos.
> 

---

## PARTE 1 — Instalación de Debian

Durante el instalador:

1. Selecciona **"Debian GNU/Linux"** sin entorno gráfico
2. En selección de software marca **solo esto**:
    - ✅ `SSH server`
    - ✅ `standard system utilities`
    - ❌ Todo lo demás desmarcado
3. Configura la red con **DHCP** por ahora (la ponemos estática después)
4. Completa la instalación y haz el primer boot

---

## PARTE 2 — Migración segura a systemd-networkd (sin perder SSH)

> 🔴 **Este es el paso más crítico.** Si deshabilitas `networking` antes de tener
`systemd-networkd` configurado y funcionando, perderás la conexión SSH.
Sigue el orden exacto de estos pasos.
> 

### Paso 2.1 — Red de seguridad (imprescindible)

Instala `at` y programa un rescate automático. Si algo sale mal, en 3 minutos
la red vuelve sola:

```bash
apt install -y at
echo "systemctl restart networking" | at now + 3 minutes
```

> Esta red de seguridad conviene usarla **cada vez** que se edite la config de red, no solo en la instalación inicial — incluida cualquier migración futura de rango de IP.
> 

### Paso 2.2 — Identifica tu interfaz actual

```bash
ip a
cat /etc/network/interfaces
```

Anota el nombre exacto de la interfaz (ej: `eno1`, `eth0`, `ens18`).

### Paso 2.3 — Crea/edita la config de networkd

```bash
nano /etc/systemd/network/10-eno1.network
```

Contenido (IP estática — rango actual `192.168.1.X`):

```
[Match]
Name=eno1

[Network]
Address=192.168.1.200/24
Gateway=192.168.1.1
DNS=1.1.1.1
DNS=8.8.8.8
DHCP=no
MACVLAN=macvlan-shim
ConfigureWithoutCarrier=yes
```

> ⚠️ Ojo con los nombres de clave: `DHCP` (no `DCHP`) y el nombre del shim debe matchear **exacto** con el definido en `20-macvlan-shim.netdev` (ej. `macvlan-shim`, no `macvlan-shin`). Un typo acá no da error visible — simplemente no aplica el efecto esperado.
> 

### Paso 2.4 — Arranca networkd SIN apagar nada todavía

```bash
systemctl enable systemd-networkd
systemctl start systemd-networkd
```

> En este punto los dos sistemas (ifupdown + networkd) coexisten.
No deberías perder conexión.
> 

### Paso 2.5 — Verifica que networkd tiene IP

```bash
networkctl status
ip addr show eno1
```

Deberías ver la IP nueva (`192.168.1.200`) activa en `eno1`.

### Paso 2.6 — Apaga ifupdown (solo en instalación inicial, no en cada migración de rango)

Programa otro rescate y luego apaga el sistema viejo:

```bash
echo "systemctl restart networking" | at now + 3 minutes
systemctl disable --now networking
```

Puede haber un microcorte de 1-2 segundos. Reconéctate a la nueva IP:

```bash
ssh root@192.168.1.200
```

### Paso 2.7 — Verificación final de red

```bash
ping -c 3 1.1.1.1
ip addr show eno1
```

---

## PARTE 3 — El truco del macvlan: shim para el host

> 🔑 **Este paso es crítico.** Con macvlan, el host (`eno1`) y el contenedor
(`192.168.1.201`) **no pueden comunicarse directamente** por diseño del
kernel. Para que el host pueda llegar a AdGuard necesitas crear una interfaz
macvlan también en el host.
> 

### Paso 3.1 — Crea la interfaz shim

```bash
nano /etc/systemd/network/20-macvlan-shim.netdev
```

Contenido:

```
[NetDev]
Name=macvlan-shim
Kind=macvlan

[MACVLAN]
Mode=bridge
```

### Paso 3.2 — Configura la red del shim (rango actual `192.168.1.X`)

```bash
nano /etc/systemd/network/20-macvlan-shim.network
```

Contenido:

```
[Match]
Name=macvlan-shim

[Network]
Address=192.168.1.250/32

[Route]
Destination=192.168.1.201/32
```

### Paso 3.3 — Enlaza el shim a eno1

Ya incluido en el `10-eno1.network` del Paso 2.3 (línea `MACVLAN=macvlan-shim`).

### Paso 3.4 — Aplica los cambios

```bash
systemctl restart systemd-networkd

# Verifica que la interfaz shim existe con la IP nueva
ip addr show macvlan-shim
```

---

## PARTE 4 — Desplegar AdGuard con Docker Compose

### Paso 4.1 — Crea la estructura de carpetas

```bash
mkdir -p /docker/adguard/{work,conf}
```

### Paso 4.2 — Crea/edita el compose (rango actual `192.168.1.X`)

```bash
nano /docker/adguard/compose.yaml
```

Contenido:

```yaml
services:
  adguard:
    container_name: adguard
    image: adguard/adguardhome:latest
    cap_add:
      - NET_ADMIN
    networks:
      macvlan_NET:
        ipv4_address: 192.168.1.201
    volumes:
      - /docker/adguard/work:/opt/adguardhome/work
      - /docker/adguard/conf:/opt/adguardhome/conf
    restart: unless-stopped

networks:
  macvlan_NET:
    driver: macvlan
    driver_opts:
      parent: eno1
    ipam:
      config:
        - subnet: 192.168.1.0/24
          gateway: 192.168.1.1
```

### Paso 4.3 — Levanta el contenedor

> ⚠️ Si estás migrando de rango (no instalación nueva), un `restart` **no alcanza**. Hay que recrear la red:
> 

```bash
cd /docker/adguard
docker compose down
docker network prune -f
docker compose up -d

# Verificar estado
docker compose ps
docker compose logs -f
```

---

## PARTE 5 — Verificación final

```bash
# El servidor llega a AdGuard
ping 192.168.1.201

# AdGuard responde por HTTP (setup wizard)
curl http://192.168.1.201:3000
```

Desde cualquier PC en tu red, abre:

```
http://192.168.1.201:3000
```

Ahí aparece el asistente de configuración inicial de AdGuard.

---

## PARTE 6 — Checklist para futuras migraciones de rango de IP

Si el router vuelve a cambiar de subred, revisar **en este orden**:

- [ ]  `/etc/systemd/network/10-eno1.network` → `Address`, `Gateway`
- [ ]  `/etc/systemd/network/20-macvlan-shim.network` → `Address`, `Route/Destination`
- [ ]  `/docker/adguard/compose.yaml` → `ipv4_address`, `subnet`, `gateway`
- [ ]  **Cualquier otro** `/docker/<servicio>/compose.yaml` con red macvlan o IP fija hardcodeada
- [ ]  `docker network ls` → revisar si hay más redes con subred fija del rango viejo
- [ ]  Reiniciar `systemd-networkd` (host) y recrear (`down`/`up`) las redes Docker macvlan afectadas

---

## Resumen de archivos que dependen del rango de IP

| Archivo | Propósito | Valores que cambian si migra el router |
| --- | --- | --- |
| `/etc/systemd/network/10-eno1.network` | IP estática en eno1 + enlace al shim | `Address`, `Gateway` |
| `/etc/systemd/network/20-macvlan-shim.netdev` | Define la interfaz macvlan del host | (sin IP, no cambia) |
| `/etc/systemd/network/20-macvlan-shim.network` | Configura la IP y ruta del shim | `Address`, `Route/Destination` |
| `/docker/adguard/compose.yaml` | Compose de AdGuard con red macvlan | `ipv4_address`, `subnet`, `gateway` |

---

## Convención de rutas para nuevos servicios

Todos los servicios Docker siguen esta estructura:

```
/docker/<servicio>/
├── compose.yaml
├── conf/          # configuración persistente
└── work/          # datos de trabajo
```

Para levantar cualquier servicio:

```bash
cd /docker/<servicio>
docker compose up -d
```