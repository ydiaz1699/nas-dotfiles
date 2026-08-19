# Errores de red

- error de red
    
    ```bash
    aadn@Nas:~$ su -
    Contraseña:
    root@Nas:~# ip a
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN grup default qlen 1000
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
        inet 127.0.0.1/8 scope host lo
           valid_lft forever preferred_lft forever
        inet6 ::1/128 scope host noprefixroute
           valid_lft forever preferred_lft forever
    2: eno1: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc fq_codel state DOWN group default qlen 1000
        link/ether f8:b1:56:9c:69:8f brd ff:ff:ff:ff:ff:ff
        altname enp0s25
        altname enxf8b1569c698f
    3: macvlan-shim@eno1: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state LOWERLAYERDOWN group default qlen 1000
        link/ether 1e:1d:84:5b:d1:84 brd ff:ff:ff:ff:ff:ff
        inet6 fe80::1c1d:84ff:fe5b:d184/64 scope link proto kernel_ll
           valid_lft forever preferred_lft forever
    4: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
        link/ether 82:ac:6c:5f:23:10 brd ff:ff:ff:ff:ff:ff
        inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
           valid_lft forever preferred_lft forever
    root@Nas:~# _
    ```
    
    ## El problema: `eno1` tiene `NO-CARRIER` y sin IP
    
    Mirando tu `ip a`, el problema es claro: `eno1` no tiene ninguna dirección IPv4 (debería tener `192.168.0.200`) y muestra `NO-CARRIER`. Hay dos causas posibles:
    
    ---
    
    ### Diagnóstico rápido
    
    Conectado físicamente al servidor (teclado+monitor), ejecuta:
    
    ```bash
    # 1. ¿Está corriendo systemd-networkd?
    systemctl status systemd-networkd
    
    # 2. ¿Existe el archivo de configuración?
    cat /etc/systemd/network/10-eno1.network
    
    # 3. Estado detallado de la interfaz
    networkctl status eno1
    ```
    
    ---
    
    ### Causa más probable: systemd-networkd no está habilitado para arrancar
    
    ```bash
    systemctl enable systemd-networkd
    systemctl start systemd-networkd
    ```
    
    Luego verifica:
    
    ```bash
    ip addr show eno1
    # Debe aparecer 192.168.0.200
    ```
    
    ---
    
    ### Segunda causa: el archivo .network no sobrevivió el reinicio
    
    Si `cat /etc/systemd/network/10-eno1.network` no muestra nada, recréalo:
    
    ```bash
    nano /etc/systemd/network/10-eno1.network
    ```
    
    Con este contenido:
    
    ```
    [Match]
    Name=eno1
    
    [Network]
    Address=192.168.0.200/24
    Gateway=192.168.0.1
    DNS=1.1.1.1
    DNS=8.8.8.8
    MACVLAN=macvlan-shim
    ```
    
    Luego:
    
    ```bash
    systemctl restart systemd-networkd
    ```
    
    ---
    
    ### Nota sobre el cable
    
    El `NO-CARRIER` también puede ser simplemente que **el cable de red está desconectado o flojo**. Antes de todo lo anterior, revisa físicamente que el cable esté bien enchufado tanto en el servidor como en el switch/router.
    
    ¿Qué te muestra el `systemctl status systemd-networkd`?
    
    1
    
    Simplemente agrégala al final del archivo:
    
    ```bash
    echo 'ConfigureWithoutCarrier=yes' >> /etc/systemd/network/10-eno1.network
    ```
    
    Verifica:
    
    ```bash
    cat /etc/systemd/network/10-eno1.network
    ```
    
    Y aplica:
    
    ```bash
    systemctl restart systemd-networkd
    reboot
    ```
    
    Con `sed`, buscas la última línea de `[Network]` antes de que empiece la siguiente sección:
    
    ```bash
    sed -i '/^\[Route\]/i ConfigureWithoutCarrier=yes' /etc/systemd/network/10-eno1.network
    ```
    
    Eso inserta la línea **justo antes de `[Route]`**, que es lo mismo que al final de `[Network]`.
    
    Si la siguiente sección fuera `[Link]` en vez de `[Route]`:
    
    ```bash
    sed -i '/^\[Link\]/i ConfigureWithoutCarrier=yes' /etc/systemd/network/10-eno1.network
    ```
    
    Básicamente cambias `[Route]` por el nombre de la sección que venga después.
    
    Sí, eso que planteas está **correcto y bien entendido** 👍
    
    Solo te dejo un par de ajustes finos para evitar problemas reales en producción:
    
    ---
    
    ## 🔎 Detalle importante sobre `sed`
    
    Tu comando:
    
    ```bash
    sed -i '/\[Network\]/a ConfigureWithoutCarrier=yes' /etc/systemd/network/10-eno1.network
    ```
    
    ✔️ Inserta justo después de `[Network]` (como dices)
    
    ✔️ El orden **no importa** para systemd-networkd
    
    👉 Pero cuidado con esto:
    
    - Si ejecutas el comando varias veces, vas a terminar con **líneas duplicadas**.
    
    ---
    
    ## 🛡️ Versión más segura (evita duplicados)
    
    ```bash
    grep -q '^ConfigureWithoutCarrier=yes' /etc/systemd/network/10-eno1.network || \
    sed -i '/\[Network\]/a ConfigureWithoutCarrier=yes' /etc/systemd/network/10-eno1.network
    ```
    
    Esto:
    
    - Verifica si ya existe la línea
    - Solo la agrega si no está
    
    ---
    
    ## 🔁 Secuencia final (limpia)
    
    ```bash
    sudo systemctl restart systemd-networkd
    reboot
    ```
    
    Aunque, siendo estrictos:
    
    👉 Si vas a hacer `reboot`, el restart previo es innecesario.
    
    ---
    
    ## ✅ Resultado esperado
    
    Con esto, systemd-networkd:
    
    - Configurará `eno1` incluso sin carrier
    - Evitará el problema típico de arranque en frío
    - No dependerás de `wait-online`
    
    ---
    
    Si después de esto aún falla en frío (corte de energía), ahí ya entraríamos a revisar cosas más específicas como:
    
    - drivers de la NIC
    - tiempos de inicialización del hardware
    - o incluso firmware/BIOS
    
    Si quieres, podemos hacer ese diagnóstico más profundo.
    
- vlan
    
    ## Con tu hardware actual: VLANs no son posibles
    
    Un router ISP básico no soporta VLANs. Sin managed switch tampoco puedes hacerlo por hardware. No hay forma de engañar eso con software.
    
    ---
    
    ## Qué puedes hacer AHORA sin comprar nada
    
    Estas medidas resuelven el 90% de los casos reales de robo de video:
    
    **1. Bloquear el acceso a internet de las cámaras desde el router**
    La mayoría de robos de video ocurren porque la cámara sube video a la nube del fabricante (China). Si bloqueas internet a las cámaras, el video solo queda en tu red local.
    
    En AdGuard (que ya tienes) puedes bloquear por IP de cámara:
    
    ```
    Filtros → Lista de bloqueo personalizada → agregar IP de la cámara
    ```
    
    **2. Cambiar contraseñas por defecto**
    El 80% de hackeos de cámaras es por contraseñas `admin/admin`. Cambia usuario y contraseña en cada cámara.
    
    **3. Nunca abrir puertos al exterior (port forwarding)**
    Si tu router tiene reglas de port forwarding para las cámaras, elimínalas. Usa tu servidor como intermediario.
    
    ---
    
    ## La solución real: un switch managed barato
    
    Un **TP-Link TL-SG108E** cuesta ~$20 USD y permite VLANs reales:
    
    ```
    Internet → Router ISP → Switch TP-Link
                                  ├── Puerto 1-4: VLAN 10 (red principal - PCs)
                                  ├── Puerto 5-6: VLAN 20 (cámaras - sin internet)
                                  └── Puerto 7-8: VLAN 30 (IoT - Tasmota, sensores)
    ```
    
    Con esto las cámaras físicamente no pueden hablar con tus PCs aunque quieran.
    
    ---
    
    ## ¿Qué quieres hacer?
    
    ¿Implementamos lo que se puede hacer ahora con AdGuard + iptables en tu servidor, o prefieres que te haga la guía completa para cuando consigas el switch TP-Link?
    
- s
    
    Perfecto, `networking` ya está deshabilitado. La IP `192.168.0.14` es solo el lease viejo que quedó en memoria — quítala manualmente:
    
    ```bash
    ip addr del 192.168.0.14/24 dev eno1
    ip addr show eno1
    ```
    
    Ahora solo debe aparecer `192.168.0.200`. Verifica internet:
    
    ```bash
    ping -c 3 1.1.1.1
    ```
    
    Si todo está bien, continuamos con **instalar Docker** y desplegar AdGuard.
    
- error
    
    Aquí están todos los comandos para cuando vuelva a pasar:
    
    ```bash
    # 1. Ver qué IPs tienes
    ip addr show eno1
    
    # 2. Ver si dhclient está corriendo
    ps aux | grep dhclient
    
    # 3. Matar dhclient
    kill $(ps aux | grep dhclient | grep -v grep | awk '{print $2}')
    
    # 4. Quitar la IP extra (cambia la IP por la que aparezca)
    ip addr del 192.168.0.14/24 dev eno1
    
    # 5. Confirmar que networking está deshabilitado
    systemctl is-enabled networking
    systemctl is-active networking
    
    # 6. Si sigue enabled/active, deshabilitarlo
    systemctl disable --now networking
    
    # 7. Verificar que solo queda 192.168.0.200
    ip addr show eno1
    
    # 8. Verificar internet
    ping -c 3 1.1.1.1
    ```
    
    **Causa raíz:** Si esto vuelve a pasar después de un reinicio, significa que `networking` o `dhclient` se reactivó solo. Para diagnosticar:
    
    ```bash
    # Ver qué servicio está levantando dhclient
    systemctl status networking
    journalctl -u networking --no-pager -n 30
    ```
    
    Seguimos con Docker y AdGuard cuando quieras.