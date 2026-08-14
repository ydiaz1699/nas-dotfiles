# file browser

- chat GPT
    
    Perfecto. Te propongo una versión más limpia y robusta, manteniendo tu estructura `/NAS → /srv` y tus labels de Homepage.
    
    ### `docker-compose.yml`
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
    
        user: "0:0"
    
        env_file:
          - .env
    
        ports:
          - "8085:80"
    
        volumes:
          - ./config:/config
          - /NAS:/srv
    
        environment:
          TZ: America/La_Paz
    
        command:
          - --database
          - /config/database.db
          - --root
          - /srv
          - --address
          - 0.0.0.0
          - --port
          - "80"
          - --log
          - stdout
    
        labels:
          - homepage.group=Archivos
          - homepage.name=Filebrowser
          - homepage.icon=filebrowser
          - homepage.href=http://192.168.1.200:8085
          - homepage.description=Explorador de archivos del NAS
    
          - homepage.widget.type=filebrowser
          - homepage.widget.url=http://192.168.1.200:8085
          - homepage.widget.username=${FILEBROWSER_USER}
          - homepage.widget.password=${FILEBROWSER_PASSWORD}
    ```
    
    ### Estructura recomendada
    
    En el host:
    
    ```
    /docker/filebrowser/
    ├── docker-compose.yml
    ├── .env
    └── config/
    ```
    
    Y tus datos:
    
    ```
    /NAS/
    ├── aadm/
    ├── docker/
    ├── peliculas/
    ├── documentos/
    └── ...
    ```
    
    Por ejemplo:
    
    ```bash
    mkdir -p /NAS/aadm
    mount --bind /home/aadm /NAS/aadm
    ```
    
    y:
    
    ```bash
    mkdir -p /NAS/docker
    mount --bind /docker /NAS/docker
    ```
    
    ### `/etc/fstab`
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker none  bind  0  0
    ```
    
    Después:
    
    ```bash
    mount -a
    ```
    
    Comprueba:
    
    ```bash
    findmnt /NAS/aadm
    findmnt /NAS/docker
    ```
    
    Y:
    
    ```bash
    ls -la /NAS/aadm
    ls -la /NAS/docker
    ```
    
    ### Levantar File Browser
    
    Desde `/docker/filebrowser`:
    
    ```bash
    docker compose down
    docker compose up -d
    ```
    
    Después verifica:
    
    ```bash
    docker ps | grep filebrowser
    ```
    
    Y:
    
    ```bash
    docker exec -it filebrowser ls -la /srv
    ```
    
    Deberías ver:
    
    ```
    aadm
    docker
    peliculas
    documentos
    ```
    
    Para comprobar específicamente `/home/aadm`:
    
    ```bash
    docker exec -it filebrowser ls -la /srv/aadm
    ```
    
    Eso debería mostrar exactamente el contenido de:
    
    ```bash
    ls -la /home/aadm
    ```
    
    **Importante:** no hace falta añadir `/home/aadm:/srv/aadm` al Compose. El montaje `/NAS:/srv` ya hace que todos los Bind Mounts que coloques debajo de `/NAS` sean visibles en File Browser.
    
    Si quieres, también puedo prepararte el **procedimiento completo para añadir/quitar carpetas con un solo comando**, por ejemplo `addmount /home/aadm` → crea `/NAS/aadm`, configura `fstab`, monta y verifica automáticamente.
    
- 1
    
    # File Browser
    
    > Servicio web para navegar, administrar y organizar archivos del NAS desde el navegador.
    Acceso: `http://192.168.0.200:8085`
    > 
    
    File Browser expone `/NAS` del host mediante una interfaz web accesible desde cualquier dispositivo de la red local, sin necesidad de SSH ni SMB. La raíz visible dentro del contenedor es `/srv`, que apunta a `/NAS` en el host. Todo lo montado dentro de `/NAS` aparece automáticamente en la UI.
    
    Permite navegar, subir, descargar, renombrar, mover y eliminar archivos, y gestionar múltiples usuarios con permisos diferenciados.
    
    ---
    
    ## Arquitectura de montaje
    
    ```
    Host (NAS)                       Contenedor Docker     UI File Browser
    ─────────────────────────────────────────────────────────────────────
    /NAS                         →   /srv              →   / (raíz)
    ├── aadm/ (bind /home/aadm)      /srv/aadm         →   /aadm/
    ├── docker/ (bind /docker)       /srv/docker       →   /docker/
    └── [nuevos mounts]              /srv/[nombre]     →   /[nombre]/
    ```
    
    > Docker captura los mounts del host al momento de iniciar el contenedor. Si se agrega un bind mount con el contenedor ya corriendo, es necesario recrearlo para que sea visible.
    > 
    
    ---
    
    ## Estructura de directorios
    
    ```
    /docker/filebrowser/
    ├── compose.yml              ← orquestación del contenedor
    └── config/                  ← base de datos y configuración (generados al primer arranque)
        ├── database.db
        └── settings.json
    
    /NAS/                        ← raíz expuesta en la UI
    ├── aadm/                    → bind mount de /home/aadm
    ├── docker/                  → bind mount de /docker
    ├── unidadUSB/               → mounts adicionales (opcionales)
    └── cloud/
        ├── gdrive/
        └── onedrive/
    ```
    
    > `$dkco` equivale a `/docker` — el directorio base de todos los stacks.
    > 
    
    ---
    
    ## Conceptos técnicos previos
    
    ### Bind mount vs symlink
    
    `mount --bind` es la única solución correcta para exponer carpetas en File Browser. Los symlinks (`ln -s`) deben evitarse porque pueden generar inconsistencias y Docker puede no resolverlos correctamente dentro del contenedor.
    
    | Criterio | Symlink (`ln -s`) | Bind mount (`mount --bind`) |
    | --- | --- | --- |
    | Visibilidad en Docker | ❌ No se propaga automáticamente | ✅ Visible si el contenedor monta el padre |
    | Persistencia | ✅ Nativa (archivo en filesystem) | ✅ Requiere entrada en `fstab` |
    | Permisos | Hereda del destino | Puede configurarse independientemente |
    | Recomendación para File Browser | ❌ Evitar | ✅ Usar siempre |
    
    ### Comportamiento de Docker con mounts
    
    Docker captura los mounts del host únicamente al iniciar el contenedor. Si se agregan mounts nuevos mientras el contenedor ya está corriendo, Docker no los detecta automáticamente — es necesario recrear el contenedor.
    
    ---
    
    ## Instalación desde cero
    
    ### Paso 1 — Crear la estructura de carpetas
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### Paso 2 — Crear la base de datos manualmente (recomendado)
    
    Evita errores de permisos en el primer arranque:
    
    ```bash
    touch $dkco/filebrowser/config/database.db
    chown 1000:1000 $dkco/filebrowser/config/database.db
    ```
    
    ### Paso 3 — Corregir permisos de `/config`
    
    **Método recomendado:**
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    ```
    
    **Método agresivo** (si persisten errores de permisos):
    
    ```bash
    chmod -R 777 $dkco/filebrowser/config
    ```
    
    | Escenario | Solución recomendada |
    | --- | --- |
    | Primer arranque | `chmod 777 ./config` (temporal para inicialización) |
    | Producción segura | `chown -R 1000:1000 ./config` + eliminar `user: "0:0"` si es posible |
    | Acceso completo al sistema | Mantener `user: "0:0"` y usar bind mounts selectivos en `/NAS` |
    
    ### Paso 4 — Crear el compose.yml
    
    Crear el archivo en `$dkco/filebrowser/compose.yml`:
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"                          # ejecutar como root para acceso completo
        ports:
          - "8085:80"                        # puerto host:puerto contenedor
        volumes:
          - ./config:/config                 # base de datos y configuración persistente
          - /NAS:/srv                        # raíz de archivos expuesta en la UI
        environment:
          - TZ=America/La_Paz                # zona horaria para logs
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    **Notas sobre la configuración:**
    
    - **`user: "0:0"`** — evita errores de permisos al escribir la base de datos y archivos de configuración.
    - **`./config:/config`** — almacena `database.db` y `settings.json`. El directorio `config` debe tener permisos de escritura.
    - **`/NAS:/srv`** — cualquier bind mount o carpeta dentro de `/NAS` se refleja en la UI. Si los directorios no existen en `/NAS`, Docker los crea como carpetas vacías.
    - **PUID/PGID** — si se necesita control por usuario, agregar al `environment`. Para la mayoría de los casos `user: "0:0"` es suficiente y evita conflictos.
    
    ### Paso 5 — Activar los bind mounts
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    Verificar que el contenido sea visible:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Paso 6 — Hacer los bind mounts permanentes
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    ### Paso 7 — Verificar el fstab
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, el archivo es válido. Si aparece un mount duplicado (puede ocurrir si ya había uno activo), limpiarlo:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm   # dos veces para eliminar el duplicado
    mount -a
    ```
    
    ### Paso 8 — Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ### Paso 9 — Levantar el contenedor
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    ### Paso 10 — Obtener la contraseña inicial
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar una línea como:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    - **Usuario:** `admin`
    - **Contraseña:** la mostrada en los logs
    - **Acceso:** `http://192.168.0.200:8085`
    
    Cambiar la contraseña en **Settings → User Management**.
    
    ---
    
    ## Gestión de bind mounts
    
    ### Agregar un bind mount
    
    ```bash
    # 1. Crear el punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Activar el mount (efecto inmediato en el host)
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Persistencia en fstab
    nano /etc/fstab
    # → agregar al final: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear el contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > El paso 5 es obligatorio. Docker no propaga mounts nuevos a contenedores ya en ejecución.
    > 
    
    ### Eliminar un bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar la línea del fstab
    nano /etc/fstab
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar la carpeta vacía (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear el contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## Mantenimiento
    
    ### Comandos de gestión diaria
    
    | Acción | Comando |
    | --- | --- |
    | Levantar contenedor | `svc up filebrowser` |
    | Detener contenedor | `svc down filebrowser` |
    | Reiniciar contenedor | `svc restart filebrowser` |
    | Ver logs | `svc logs filebrowser` |
    | Ver logs en tiempo real | `svc logs -f filebrowser` |
    | Actualizar imagen | `svc update filebrowser` |
    | Recrear contenedor | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    
    ### Actualizar File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    Descarga la nueva imagen, detiene el contenedor actual y levanta uno nuevo con la misma configuración.
    
    ### Backup de configuración
    
    ```bash
    cp -r $dkco/filebrowser/config /ruta/backup/filebrowser-config-$(date +%F)
    ```
    
    ### Restaurar configuración desde backup
    
    ```bash
    # 1. Detener el servicio
    svc down filebrowser
    
    # 2. Restaurar archivos
    cp -r /ruta/backup/filebrowser-config-*/config/* $dkco/filebrowser/config/
    
    # 3. Corregir permisos
    chown -R 1000:1000 $dkco/filebrowser/config
    
    # 4. Reiniciar
    svc up filebrowser
    ```
    
    ---
    
    ## Verificación y diagnóstico
    
    ### Estado general
    
    ```bash
    mount | grep NAS                       # bind mounts activos
    ls /NAS                                # carpetas disponibles
    df -h /NAS /home/aadm /docker          # dispositivos y particiones
    svc logs filebrowser                   # estado del contenedor
    docker ps | grep filebrowser           # verificar que el puerto 8085 esté expuesto
    ```
    
    ### Verificar contenido de los mounts
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Verificar desde el contenedor
    
    ```bash
    docker exec -it filebrowser ls -la /srv
    docker exec -it filebrowser sh         # entrar al contenedor para diagnóstico
    ```
    
    ### Salida esperada de `mount | grep NAS`
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ### Caso especial — `type ext4` en vez de `none (bind)`
    
    Si aparece algo como `/dev/sda1 on /NAS/aadm type ext4`, no necesariamente es un error. Ocurre cuando `/NAS`, `/home/aadm` y `/docker` están en la misma partición física — el bind mount funciona correctamente pero el kernel muestra el device subyacente.
    
    Verificar si los tres comparten disco:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Si todos usan el mismo disco (por ejemplo `sda1`), el comportamiento es normal. Confirmar que haya contenido:
    
    ```bash
    ls /NAS/aadm
    ```
    
    Si los mounts realmente no pegaron, rehacerlos:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/docker
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ---
    
    ## Problemas comunes
    
    | Síntoma | Causa probable | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes que los bind mounts | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    | `Permission denied` al escribir en `/config` | Permisos incorrectos en la carpeta `config` del host | Ver fix rápido abajo |
    | Contraseña de admin no funciona | Se generó aleatoriamente en el primer arranque | Revisar `svc logs filebrowser` para obtenerla |
    | El contenedor no arranca (loop) y no hay UI | File Browser no puede crear `database.db` en `/config` | `svc down filebrowser` → fix de permisos → `svc up filebrowser` |
    | Mount no persiste tras reboot | Falta configuración en `/etc/fstab` | Seguir pasos 6 y 7 de la instalación |
    | Puerto 8085 no responde | Error de configuración al iniciar | Verificar con `svc logs filebrowser` y revisar sintaxis del `compose.yml` |
    | `mount | grep NAS` muestra `type ext4` | Todo está en la misma partición (comportamiento normal) | Verificar con `ls /NAS/aadm` — si hay contenido, los mounts están bien |
    | Bind mounts duplicados en `mount | grep NAS` | `mount -a` ejecutado sobre mounts ya activos | `umount /NAS/aadm` dos veces, luego `mount -a` |
    | `mount --bind` da error "no such file or directory" | El punto de montaje destino no existe | Crear el directorio antes: `mkdir -p /NAS/nombre` |
    | Bind mounts no pegaron (carpetas vacías en host) | El `mount --bind` falló silenciosamente | Desmontar y rehacer con `mount --bind` |
    
    ### Fix rápido para errores de permisos en `/config`
    
    ```bash
    dk filebrowser
    
    svc down filebrowser
    rm -rf config
    mkdir config
    chmod 777 config
    
    svc up filebrowser
    docker ps | grep filebrowser
    ```
    
    > Post-fix: una vez funcional, ajustar permisos para producción: `chown -R 1000:1000 config && chmod -R 755 config`
    > 
    
    ---
    
    ## Consideraciones avanzadas
    
    ### Permisos seguros (evitar `chmod 777` en producción)
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    chmod -R 755 $dkco/filebrowser/config
    
    # En compose.yml, opcionalmente ajustar:
    # user: "1000:1000"  en lugar de "0:0"
    ```
    
    ### Agregar volúmenes directamente en compose.yml (alternativa a bind mounts)
    
    En lugar de gestionar bind mounts en el host, es posible declarar los volúmenes directamente en el compose:
    
    ```yaml
    volumes:
      - ./config:/config
      - /NAS:/srv
      # Montajes directos a subcarpetas de /srv:
      - /mnt/disco1/media:/srv/media:ro      # solo lectura
      - /mnt/usb/backups:/srv/backups
      - $dkco:/srv/docker:ro                 # configuración Docker, read-only
    ```
    
    - **Ventaja:** no requiere recrear el contenedor al agregar nuevos mounts.
    - **Desventaja:** requiere editar `compose.yml` y reiniciar el servicio.
    
    ### Mount de todo el filesystem (no recomendado)
    
    ```yaml
    volumes:
      - /:/srv:ro    # monta todo el host en /srv, solo lectura
    ```
    
    > Expone toda la estructura del servidor. Usar solo en entornos de prueba con autenticación fuerte.
    > 
    
    ---
    
    ## Referencias rápidas
    
    ### Flujo para agregar contenido nuevo
    
    1. Crear carpeta: `mkdir -p /NAS/nombre`
    2. Bind mount: `mount --bind /ruta/origen /NAS/nombre`
    3. Persistir: agregar a `/etc/fstab`
    4. Recargar: `systemctl daemon-reload`
    5. Recrear contenedor: `svc down filebrowser && svc up filebrowser`
    6. Verificar en UI: `http://192.168.0.200:8085/nombre`
    
    ### Estructura esperada en la UI tras configuración inicial
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        ├── filebrowser/
        └── [otros servicios]/
    ```
    
    ### Arquitectura completa
    
    ```
    HOST
     ├── /home/aadm  ──┐
     ├── /docker     ──┼──→  /NAS/
     └── /NAS             ├── aadm/   (bind)
                           └── docker/ (bind)
    
    DOCKER
     └── /srv  →  /NAS  (volumen)
    ```
    
    > Mantener siempre backups de `config/database.db` y documentar los mounts personalizados en `/etc/fstab` con comentarios descriptivos.
    > 
- 2
    
    # File Browser
    
    > Servicio web para navegar, administrar y organizar archivos del NAS desde el navegador.
    Acceso: `http://192.168.0.200:8085`
    > 
    
    File Browser expone `/NAS` del host mediante una interfaz web accesible desde cualquier dispositivo de la red local, sin necesidad de SSH ni SMB. La raíz visible dentro del contenedor es `/srv`, que apunta a `/NAS` en el host. Todo lo montado dentro de `/NAS` aparece automáticamente en la UI.
    
    Permite navegar, subir, descargar, renombrar, mover y eliminar archivos, y gestionar múltiples usuarios con permisos diferenciados.
    
    ---
    
    ## Arquitectura de montaje
    
    ```
    Host (NAS)                       Contenedor Docker     UI File Browser
    ─────────────────────────────────────────────────────────────────────
    /NAS                         →   /srv              →   / (raíz)
    ├── aadm/ (bind /home/aadm)      /srv/aadm         →   /aadm/
    ├── docker/ (bind /docker)       /srv/docker       →   /docker/
    └── [nuevos mounts]              /srv/[nombre]     →   /[nombre]/
    ```
    
    > Docker captura los mounts del host al momento de iniciar el contenedor. Si se agrega un bind mount con el contenedor ya corriendo, es necesario recrearlo para que sea visible.
    > 
    
    ---
    
    ## Estructura de directorios
    
    ```
    /docker/filebrowser/
    ├── compose.yml              ← orquestación del contenedor
    └── config/                  ← base de datos y configuración (generados al primer arranque)
        ├── database.db
        └── settings.json
    
    /NAS/                        ← raíz expuesta en la UI
    ├── aadm/                    → bind mount de /home/aadm
    ├── docker/                  → bind mount de /docker
    ├── unidadUSB/               → mounts adicionales (opcionales)
    └── cloud/
        ├── gdrive/
        └── onedrive/
    ```
    
    > `$dkco` equivale a `/docker` — el directorio base de todos los stacks.
    > 
    
    ---
    
    ## Conceptos técnicos previos
    
    ### Bind mount vs symlink
    
    `mount --bind` es la única solución correcta para exponer carpetas en File Browser. Los symlinks (`ln -s`) deben evitarse porque pueden generar inconsistencias y Docker puede no resolverlos correctamente dentro del contenedor.
    
    | Criterio | Symlink (`ln -s`) | Bind mount (`mount --bind`) |
    | --- | --- | --- |
    | Visibilidad en Docker | ❌ No se propaga automáticamente | ✅ Visible si el contenedor monta el padre |
    | Persistencia | ✅ Nativa (archivo en filesystem) | ✅ Requiere entrada en `fstab` |
    | Permisos | Hereda del destino | Puede configurarse independientemente |
    | Recomendación para File Browser | ❌ Evitar | ✅ Usar siempre |
    
    ### Comportamiento de Docker con mounts
    
    Docker captura los mounts del host únicamente al iniciar el contenedor. Si se agregan mounts nuevos mientras el contenedor ya está corriendo, Docker no los detecta automáticamente — es necesario recrear el contenedor.
    
    ---
    
    ## Instalación desde cero
    
    ### Paso 1 — Crear la estructura de carpetas
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### Paso 2 — Crear la base de datos manualmente (recomendado)
    
    Evita errores de permisos en el primer arranque:
    
    ```bash
    touch $dkco/filebrowser/config/database.db
    chown 1000:1000 $dkco/filebrowser/config/database.db
    ```
    
    ### Paso 3 — Corregir permisos de `/config`
    
    **Método recomendado:**
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    ```
    
    **Método agresivo** (si persisten errores de permisos):
    
    ```bash
    chmod -R 777 $dkco/filebrowser/config
    ```
    
    | Escenario | Solución recomendada |
    | --- | --- |
    | Primer arranque | `chmod 777 ./config` (temporal para inicialización) |
    | Producción segura | `chown -R 1000:1000 ./config` + eliminar `user: "0:0"` si es posible |
    | Acceso completo al sistema | Mantener `user: "0:0"` y usar bind mounts selectivos en `/NAS` |
    
    ### Paso 4 — Crear el compose.yml
    
    Crear el archivo en `$dkco/filebrowser/compose.yml`:
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"                          # ejecutar como root para acceso completo
        ports:
          - "8085:80"                        # puerto host:puerto contenedor
        volumes:
          - ./config:/config                 # base de datos y configuración persistente
          - /NAS:/srv                        # raíz de archivos expuesta en la UI
        environment:
          - TZ=America/La_Paz                # zona horaria para logs
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    **Notas sobre la configuración:**
    
    - **`user: "0:0"`** — evita errores de permisos al escribir la base de datos y archivos de configuración.
    - **`./config:/config`** — almacena `database.db` y `settings.json`. El directorio `config` debe tener permisos de escritura.
    - **`/NAS:/srv`** — cualquier bind mount o carpeta dentro de `/NAS` se refleja en la UI. Si los directorios no existen en `/NAS`, Docker los crea como carpetas vacías.
    - **PUID/PGID** — si se necesita control por usuario, agregar al `environment`. Para la mayoría de los casos `user: "0:0"` es suficiente y evita conflictos.
    
    ### Paso 5 — Activar los bind mounts
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    Verificar que el contenido sea visible:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Paso 6 — Hacer los bind mounts permanentes
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    ### Paso 7 — Verificar el fstab
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, el archivo es válido. Si aparece un mount duplicado (puede ocurrir si ya había uno activo), limpiarlo:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm   # dos veces para eliminar el duplicado
    mount -a
    ```
    
    ### Paso 8 — Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ### Paso 9 — Levantar el contenedor
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    ### Paso 10 — Obtener la contraseña inicial
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar una línea como:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    - **Usuario:** `admin`
    - **Contraseña:** la mostrada en los logs
    - **Acceso:** `http://192.168.0.200:8085`
    
    Cambiar la contraseña en **Settings → User Management**.
    
    ---
    
    ## Gestión de bind mounts
    
    ### Agregar un bind mount
    
    ```bash
    # 1. Crear el punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Activar el mount (efecto inmediato en el host)
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Persistencia en fstab
    nano /etc/fstab
    # → agregar al final: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear el contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > El paso 5 es obligatorio. Docker no propaga mounts nuevos a contenedores ya en ejecución.
    > 
    
    ### Eliminar un bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar la línea del fstab
    nano /etc/fstab
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar la carpeta vacía (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear el contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## Mantenimiento
    
    ### Comandos de gestión diaria
    
    | Acción | Comando |
    | --- | --- |
    | Levantar contenedor | `svc up filebrowser` |
    | Detener contenedor | `svc down filebrowser` |
    | Reiniciar contenedor | `svc restart filebrowser` |
    | Ver logs | `svc logs filebrowser` |
    | Ver logs en tiempo real | `svc logs -f filebrowser` |
    | Actualizar imagen | `svc update filebrowser` |
    | Recrear contenedor | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    
    ### Actualizar File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    Descarga la nueva imagen, detiene el contenedor actual y levanta uno nuevo con la misma configuración.
    
    ### Backup de configuración
    
    ```bash
    cp -r $dkco/filebrowser/config /ruta/backup/filebrowser-config-$(date +%F)
    ```
    
    ### Restaurar configuración desde backup
    
    ```bash
    # 1. Detener el servicio
    svc down filebrowser
    
    # 2. Restaurar archivos
    cp -r /ruta/backup/filebrowser-config-*/config/* $dkco/filebrowser/config/
    
    # 3. Corregir permisos
    chown -R 1000:1000 $dkco/filebrowser/config
    
    # 4. Reiniciar
    svc up filebrowser
    ```
    
    ---
    
    ## Verificación y diagnóstico
    
    ### Estado general
    
    ```bash
    mount | grep NAS                       # bind mounts activos
    ls /NAS                                # carpetas disponibles
    df -h /NAS /home/aadm /docker          # dispositivos y particiones
    svc logs filebrowser                   # estado del contenedor
    docker ps | grep filebrowser           # verificar que el puerto 8085 esté expuesto
    ```
    
    ### Verificar contenido de los mounts
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Verificar desde el contenedor
    
    ```bash
    docker exec -it filebrowser ls -la /srv
    docker exec -it filebrowser sh         # entrar al contenedor para diagnóstico
    ```
    
    ### Salida esperada de `mount | grep NAS`
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ### Caso especial — `type ext4` en vez de `none (bind)`
    
    Si aparece algo como `/dev/sda1 on /NAS/aadm type ext4`, no necesariamente es un error. Ocurre cuando `/NAS`, `/home/aadm` y `/docker` están en la misma partición física — el bind mount funciona correctamente pero el kernel muestra el device subyacente.
    
    Verificar si los tres comparten disco:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Si todos usan el mismo disco (por ejemplo `sda1`), el comportamiento es normal. Confirmar que haya contenido:
    
    ```bash
    ls /NAS/aadm
    ```
    
    Si los mounts realmente no pegaron, rehacerlos:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/docker
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ---
    
    ## Problemas comunes
    
    | Síntoma | Causa probable | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes que los bind mounts | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    | `Permission denied` al escribir en `/config` | Permisos incorrectos en la carpeta `config` del host | Ver fix rápido abajo |
    | Contraseña de admin no funciona | Se generó aleatoriamente en el primer arranque | Revisar `svc logs filebrowser` para obtenerla |
    | El contenedor no arranca (loop) y no hay UI | File Browser no puede crear `database.db` en `/config` | `svc down filebrowser` → fix de permisos → `svc up filebrowser` |
    | Mount no persiste tras reboot | Falta configuración en `/etc/fstab` | Seguir pasos 6 y 7 de la instalación |
    | Puerto 8085 no responde | Error de configuración al iniciar | Verificar con `svc logs filebrowser` y revisar sintaxis del `compose.yml` |
    | `mount | grep NAS` muestra `type ext4` | Todo está en la misma partición (comportamiento normal) | Verificar con `ls /NAS/aadm` — si hay contenido, los mounts están bien |
    | Bind mounts duplicados en `mount | grep NAS` | `mount -a` ejecutado sobre mounts ya activos | `umount /NAS/aadm` dos veces, luego `mount -a` |
    | `mount --bind` da error "no such file or directory" | El punto de montaje destino no existe | Crear el directorio antes: `mkdir -p /NAS/nombre` |
    | Bind mounts no pegaron (carpetas vacías en host) | El `mount --bind` falló silenciosamente | Desmontar y rehacer con `mount --bind` |
    
    ### Fix rápido para errores de permisos en `/config`
    
    ```bash
    dk filebrowser
    
    svc down filebrowser
    rm -rf config
    mkdir config
    chmod 777 config
    
    svc up filebrowser
    docker ps | grep filebrowser
    ```
    
    > Post-fix: una vez funcional, ajustar permisos para producción: `chown -R 1000:1000 config && chmod -R 755 config`
    > 
    
    ---
    
    ## Consideraciones avanzadas
    
    ### Permisos seguros (evitar `chmod 777` en producción)
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    chmod -R 755 $dkco/filebrowser/config
    
    # En compose.yml, opcionalmente ajustar:
    # user: "1000:1000"  en lugar de "0:0"
    ```
    
    ### Agregar volúmenes directamente en compose.yml (alternativa a bind mounts)
    
    En lugar de gestionar bind mounts en el host, es posible declarar los volúmenes directamente en el compose:
    
    ```yaml
    volumes:
      - ./config:/config
      - /NAS:/srv
      # Montajes directos a subcarpetas de /srv:
      - /mnt/disco1/media:/srv/media:ro      # solo lectura
      - /mnt/usb/backups:/srv/backups
      - $dkco:/srv/docker:ro                 # configuración Docker, read-only
    ```
    
    - **Ventaja:** no requiere recrear el contenedor al agregar nuevos mounts.
    - **Desventaja:** requiere editar `compose.yml` y reiniciar el servicio.
    
    ### Mount de todo el filesystem (no recomendado)
    
    ```yaml
    volumes:
      - /:/srv:ro    # monta todo el host en /srv, solo lectura
    ```
    
    > Expone toda la estructura del servidor. Usar solo en entornos de prueba con autenticación fuerte.
    > 
    
    ---
    
    ## Referencias rápidas
    
    ### Flujo para agregar contenido nuevo
    
    1. Crear carpeta: `mkdir -p /NAS/nombre`
    2. Bind mount: `mount --bind /ruta/origen /NAS/nombre`
    3. Persistir: agregar a `/etc/fstab`
    4. Recargar: `systemctl daemon-reload`
    5. Recrear contenedor: `svc down filebrowser && svc up filebrowser`
    6. Verificar en UI: `http://192.168.0.200:8085/nombre`
    
    ### Estructura esperada en la UI tras configuración inicial
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        ├── filebrowser/
        └── [otros servicios]/
    ```
    
    ### Arquitectura completa
    
    ```
    HOST
     ├── /home/aadm  ──┐
     ├── /docker     ──┼──→  /NAS/
     └── /NAS             ├── aadm/   (bind)
                           └── docker/ (bind)
    
    DOCKER
     └── /srv  →  /NAS  (volumen)
    ```
    
    > Mantener siempre backups de `config/database.db` y documentar los mounts personalizados en `/etc/fstab` con comentarios descriptivos.
    > 

---

- chatgpt
    
    # 📁 File Browser — Guía Completa y Unificada
    
    > Servicio web para navegar, administrar y organizar archivos del NAS desde el navegador.
    > 
    
    Acceso:
    
    ```bash
    http://192.168.0.200:8085
    ```
    
    ---
    
    # 📖 Descripción General
    
    File Browser expone una carpeta del servidor mediante una interfaz web accesible desde cualquier dispositivo de la red local.
    
    Permite:
    
    - Navegar archivos
    - Subir y descargar contenido
    - Crear carpetas
    - Organizar archivos
    - Gestionar usuarios
    - Administrar permisos básicos
    
    La raíz visible dentro del contenedor es:
    
    ```
    /srv
    ```
    
    Esta ruta apunta a:
    
    ```
    /NAS
    ```
    
    en el host.
    
    Todo lo montado dentro de `/NAS` aparecerá automáticamente en la interfaz web.
    
    ---
    
    ## 📁 Estructura de Directorios
    
    Estructura del Stack Docker
    
    ```
    /docker/filebrowser/
    ├── compose.yml
    ├── .env
    └── config/
        ├── database.db
        └── settings.json
    ```
    
    Estructura de Datos Externos
    
    ```
    /NAS/
    ├── aadm/              → bind mount de /home/aadm
    ├── docker/            → bind mount de /docker
    ├── Pru/               → bind mount opcional de /root/Pru
    ├── unidadUSB/         → mounts adicionales
    └── cloud/
        ├── gdrive/
        └── onedrive/
    ```
    
    ---
    
    # 📄 Docker Compose
    
    ## Configuración recomendada
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"
        env_file: .env
        ports:
          - "8085:80"
        volumes:
          - ./config:/config
          - /NAS:/srv
        environment:
          - TZ=America/La_Paz
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
        labels:
          - homepage.group=Archivos
          - homepage.name=Filebrowser
          - homepage.icon=filebrowser
          - homepage.href=http://192.168.1.200:8085
          - homepage.description=Explorador de archivos del NAS
          - homepage.widget.type=filebrowser
          - homepage.widget.url=http://192.168.1.200:8085
          - homepage.widget.username=${FILEBROWSER_USER}
          - homepage.widget.password=${FILEBROWSER_PASSWORD}
    ```
    
    ## Notas técnicas previas
    
    Antes de operar el servicio, tener en cuenta:
    
    **Docker y bind mounts** — Docker captura los mounts únicamente al iniciar el contenedor. Si se agregan mounts nuevos mientras el contenedor ya está corriendo, Docker no los detecta automáticamente. Es necesario recrear el contenedor.
    
    **Bind mount vs symlink** — `mount --bind` es la única solución correcta para exponer carpetas en File Browser. Los symlinks (`ln -s`) deben evitarse porque pueden generar inconsistencias, dependen de permisos del sistema de archivos y Docker puede no resolverlos correctamente dentro del contenedor.
    
    ---
    
    # 🚀 Instalación Completa desde Cero
    
    ## Paso 1 — Crear estructura base
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    Opcional:
    
    ```bash
    mkdir -p -m 777 /NAS
    ```
    
    ---
    
    ### Paso 2 — Crear base de datos manualmente (opcional)
    
    Evita errores de permisos en el primer arranque:
    
    ```bash
    touch $dkco/filebrowser/config/database.db
    ```
    
    ---
    
    ## Paso 3 — Corregir permisos de `/config`
    
    ### Método recomendado
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    ```
    
    ### Método agresivo (si hay errores de permisos)
    
    ```bash
    chmod -R 777 $dkco/filebrowser/config
    ```
    
    ---
    
    # 🔗 Configuración de Bind Mounts
    
    ## Activar Bind Mounts
    
    Esto conecta carpetas reales del host dentro de `/NAS`.
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ---
    
    ## Verificar contenido
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ---
    
    ## Verificar mounts activos
    
    ```bash
    mount | grep NAS
    ```
    
    Salida esperada:
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ---
    
    # ⚠️ Caso Especial — `type ext4` en vez de `bind`
    
    Si aparece algo como:
    
    ```
    /dev/sda1 on /NAS/aadm type ext4
    ```
    
    no necesariamente es un error.
    
    Puede ocurrir cuando:
    
    - `/NAS`
    - `/home/aadm`
    - `/docker`
    
    están en la misma partición física.
    
    ## Verificar
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Si todos usan el mismo disco (`sda1` por ejemplo), el comportamiento es normal.
    
    ---
    
    # 💾 Persistencia tras Reinicio
    
    ## Editar fstab
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final:
    
    ```
    /home/aadm  /NAS/aadm    none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    ---
    
    ## Aplicar configuración
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, el archivo es válido. Si aparece un mount duplicado (puede ocurrir si ya había uno activo), limpiar con:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm   # dos veces para eliminar el duplicado
    mount -a
    ```
    
    ---
    
    ## Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ---
    
    # 🚀 Arranque del Servicio
    
    ## Iniciar contenedor
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ### Obtener la contraseña inicial
    
    En el primer arranque File Browser genera una contraseña aleatoria para `admin`:
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar una línea como:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    Cambiarla luego en **Settings → User Management**.
    
    ---
    
    # 🔐 Credenciales Iniciales
    
    En el primer arranque File Browser genera:
    
    - Usuario: `admin`
    - Contraseña aleatoria
    
    Buscar en logs una línea similar:
    
    ```
    User 'admin' initialized with randomly generated password: xxxxx
    ```
    
    Luego cambiar la contraseña desde:
    
    ```
    Settings → User Management
    ```
    
    ---
    
    # 🔄 Recrear Contenedor
    
    Docker captura los mounts únicamente al iniciar.
    
    Si agregas nuevos bind mounts mientras el contenedor ya está corriendo:
    
    ```bash
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    # ➕ Agregar Nuevos Bind Mounts
    
    ## Paso 1 — Crear punto de montaje
    
    ```bash
    mkdir -p /NAS/nombre
    ```
    
    ---
    
    ## Paso 2 — Activar mount
    
    ```bash
    mount --bind /ruta/origen /NAS/nombre
    ```
    
    ---
    
    ## Paso 3 — Persistencia en fstab
    
    Editar:
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar:
    
    ```
    /ruta/origen  /NAS/nombre  none  bind  0  0
    ```
    
    ---
    
    ## Paso 4 — Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ---
    
    ## Paso 5 — Recrear contenedor
    
    ```bash
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    # ➖ Eliminar Bind Mounts
    
    1. Desmontar
        
        ```bash
        umount /NAS/nombre
        ```
        
    2. Eliminar del fstab
        
        ```bash
        nano /etc/fstab
        ```
        
    
    Borrar línea correspondiente.
    
    ---
    
    ## Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ---
    
    ## Eliminar carpeta vacía
    
    ```bash
    rm -rf /NAS/nombre
    ```
    
    ---
    
    ## Recrear contenedor
    
    ```bash
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ### Actualizar imagen
    
    ```bash
    svc update filebrowser
    ```
    
    ---
    
    # 🔍 Verificaciones y Diagnóstico
    
    ## Ver mounts activos
    
    ```bash
    mount | grep NAS
    ```
    
    La salida esperada de `mount | grep NAS`:
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    > Si todo está en la misma partición (`sda1`), el bind mount funciona correctamente pero `mount | grep NAS` puede mostrar el device físico subyacente en vez de `none (bind)`. Confirmar con `ls /NAS/aadm` y `ls /NAS/docker` — si tienen contenido, todo está bien.
    > 
    
    ---
    
    ## Ver contenido disponible
    
    ```bash
    ls /NAS
    ```
    
    ---
    
    ## Revisar logs
    
    ```bash
    svc logs filebrowser
    ```
    
    ---
    
    # 🧪 Diagnóstico Avanzado
    
    ## Verificar si bind mount falló
    
    ```bash
    mount --bind /home/aadm /NAS/aadm && echo "OK" || echo "FALLO"
    ```
    
    ---
    
    ## Verificar contenido de los mounts desde host
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ---
    
    ## Verificar desde contenedor
    
    ```bash
    docker exec -it filebrowser ls -la /srv
    ```
    
    ### Salida esperada de `mount | grep NAS`
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ### Caso especial — `type ext4` en vez de `none (bind)`
    
    Si aparece algo como `/dev/sda1 on /NAS/aadm type ext4`, no necesariamente es un error. Ocurre cuando `/NAS`, `/home/aadm` y `/docker` están en la misma partición física — el bind mount funciona pero el kernel muestra el device subyacente.
    
    Verificar si los tres comparten disco:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Si todos usan el mismo disco (`sda1` por ejemplo), el comportamiento es normal. Confirmar que haya contenido con `ls /NAS/aadm`.
    
    Si los mounts realmente no pegaron, rehacerlos:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/docker
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ---
    
    # ⚠️ Problemas Comunes
    
    ## Carpetas vacías en la UI
    
    ### Causa
    
    El contenedor inició antes del bind mount.
    
    ### Solución
    
    ```bash
    svc down filebrowser
    svc up filebrowser
    ```
    
    | Síntoma | Causa | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes del mount | `svc down filebrowser && svc up filebrowser` |
    | `permission denied` en logs al escribir en `/config` | Permisos incorrectos en la carpeta `config` del host | `rm -rf config && mkdir config && chmod 777 config`, luego `svc down filebrowser && svc up filebrowser`, luego reiniciar el contenedor |
    | Contraseña no funciona | Se generó aleatoriamente al primer arranque | Revisar `svc logs filebrowser` para obtenerla |
    | Mount no persiste tras reboot | Falta configuración en `/etc/fstab` | Seguir pasos 5 y 6 de la instalación |
    | `mount | grep NAS` muestra `type ext4` en vez de `none (bind)` | Todo está en la misma partición `sda1` — comportamiento normal del kernel | Verificar con `ls /NAS/aadm` — si hay contenido, los mounts están bien |
    | Bind mounts duplicados | Se montó manualmente y luego `mount -a` volvió a montarlo | `umount /NAS/aadm` dos veces, luego `mount -a` |
    | Bind mounts no pegaron (carpetas vacías en el host) | El `mount --bind` falló silenciosamente | `umount /NAS/aadm && umount /NAS/docker && mount --bind /home/aadm /NAS/aadm && mount --bind /docker /NAS/docker` |
    
    ---
    
    ## Error de permisos en `/config`
    
    ### Error típico
    
    ```
    cp: can't create '/config/settings.json': Permission denied
    ```
    
    ### Causa
    
    Docker no puede escribir en la carpeta `config`.
    
    ### Solución rápida
    
    ```bash
    cd /docker/filebrowser
    
    rm -rf config
    mkdir config
    
    chmod 777 config
    ```
    
    Luego:
    
    ```bash
    docker compose down
    docker compose up -d
    ```
    
    ---
    
    ## Contraseña incorrecta
    
    ### Solución
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar contraseña generada automáticamente.
    
    ---
    
    ## Mount no persiste tras reboot
    
    ### Causa
    
    Falta configuración en `/etc/fstab`.
    
    ### Solución
    
    Agregar:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker none  bind  0  0
    ```
    
    ---
    
    ## Bind mount duplicado
    
    ### Síntoma
    
    `mount | grep NAS` muestra mounts repetidos.
    
    ### Solución
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm
    
    mount -a
    ```
    
    ---
    
    # 🔄 Actualizar File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    ---
    
    # 📂 Resultado Esperado en la UI
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    ├── docker/
    │   ├── adguard/
    │   ├── cli/
    │   └── filebrowser/
    └── Pru/
    ```
    
    ---
    
    # 🧠 Notas Técnicas Importantes
    
    ## Docker y Bind Mounts
    
    Docker captura los mounts únicamente al iniciar el contenedor.
    
    Si agregas mounts nuevos:
    
    - Docker NO los detecta automáticamente
    - Debes recrear el contenedor
    
    ---
    
    ## Bind Mount vs Symlink
    
    ### Recomendación
    
    Para File Browser:
    
    ```
    mount --bind
    ```
    
    es la solución correcta.
    
    ### Evitar
    
    ```
    ln -s
    ```
    
    porque:
    
    - puede generar inconsistencias
    - depende de permisos
    - Docker puede no resolverlos correctamente
    
    ---
    
    # 📌 Resumen Final
    
    ## Arquitectura
    
    ```
    HOST
     ├── /home/aadm
     ├── /docker
     └── /NAS
          ├── aadm    ← bind
          └── docker  ← bind
    
    DOCKER
     └── /srv → /NAS
    ```
    
    ---
    
    ## Flujo recomendado
    
    1. Crear `/NAS`
    2. Crear bind mounts
    3. Configurar `fstab`
    4. Verificar mounts
    5. Iniciar File Browser
    6. Recrear contenedor al agregar nuevos mounts
    
    ---
    
    # ✅ Estado Correcto Esperado
    
    ## Host
    
    ```bash
    mount | grep NAS
    ```
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ---
    
    ## Docker
    
    ```bash
    docker ps
    ```
    
    Debe mostrar:
    
    ```
    0.0.0.0:8085->80/tcp
    ```
    
    ---
    
    ## Navegador
    
    ```
    http://192.168.0.200:8085
    ```
    
    Acceso funcional con contenido visible dentro de `/srv`.
    
- kimi
    
    # 📁 File Browser — Guía Completa
    
    Servicio web para navegar archivos del NAS desde el navegador.
    
    **Acceso:** `http://192.168.0.200:8085`
    
    ---
    
    ## 1. Descripción del Servicio
    
    File Browser expone una carpeta del servidor como interfaz web, permitiendo ver, subir, descargar y organizar archivos desde cualquier dispositivo en la red local.
    
    - **Carpeta raíz del contenedor:** `/srv` (apunta a `/NAS` en el host)
    - **Característica principal:** Todo lo montado en `/NAS` aparece automáticamente en la UI sin necesidad de modificar el `compose.yml`
    
    ---
    
    ## 2. Arquitectura de Directorios
    
    ### 2.1 Estructura del Stack Docker
    
    ```
    /docker/filebrowser/
    ├── compose.yml          ← Orquestación del contenedor
    ├── .env                 ← Variables de entorno (opcional)
    └── config/              ← DB y settings (usuarios, sesiones)
        └── filebrowser.db   ← Base de datos SQLite (generada al primer arranque)
    ```
    
    ### 2.2 Estructura de Datos Externos
    
    ```
    /NAS/                    ← Raíz expuesta en la UI
    ├── aadm/                → bind mount de /home/aadm
    └── docker/              → bind mount de /docker
    ```
    
    ---
    
    ## 3. Instalación desde Cero
    
    ### 3.1 Preparar Estructura de Carpetas
    
    ```bash
    # Crear directorios del stack
    mkdir -p $dkco/filebrowser/config
    
    # Crear puntos de montaje para bind mounts
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### 3.2 Configurar Bind Mounts (Montajes en Caliente)
    
    Los bind mounts permiten exponer carpetas del host dentro de `/NAS` sin modificar el contenedor:
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    > **Nota:** Si los directorios destino no existen, créalos primero con `mkdir -p`.
    > 
    
    ### 3.3 Persistir Bind Mounts (fstab)
    
    Para que los montajes sobrevivan al reinicio:
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final del archivo:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    Guardar con `Ctrl+O` → `Enter` → `Ctrl+X`.
    
    ### 3.4 Verificar fstab y Recargar Sistema
    
    ```bash
    # Verificar sintaxis (sin aplicar aún)
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, proceder:
    
    ```bash
    # Recargar systemd para aplicar cambios
    systemctl daemon-reload
    ```
    
    > **Importante:** Si un bind mount aparece duplicado en `mount | grep NAS`, ejecutar `umount` la cantidad de veces necesaria hasta limpiar, luego `mount -a` para dejar solo las entradas del fstab.
    > 
    
    ### 3.5 Configurar Permisos de la Base de Datos
    
    ```bash
    # Crear archivo de base de datos vacío
    touch $dkco/filebrowser/config/filebrowser.db
    
    # Asignar propietario correcto (UID 1000 del contenedor)
    chown 1000:1000 $dkco/filebrowser/config/filebrowser.db
    ```
    
    > **Alternativa rápida (menos segura):** `chmod 777 $dkco/filebrowser/config`
    > 
    
    ### 3.6 Archivo compose.yml
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"
        ports:
          - "8085:80"
        volumes:
          - ./config:/config
          - /NAS:/srv
        environment:
          - TZ=America/La_Paz
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    > **Nota sobre permisos:** El uso de `user: "0:0"` (root) evita problemas de permisos en la mayoría de los casos. Si se prefiere seguridad, omitir esta línea y asegurar que el directorio `config` tenga UID/GID 1000.
    > 
    
    ### 3.7 Levantar el Servicio
    
    ```bash
    # Navegar al directorio del stack
    dk filebrowser
    
    # Iniciar contenedor
    svc up filebrowser
    ```
    
    ### 3.8 Obtener Credenciales de Primer Arranque
    
    En el primer arranque, File Browser genera una contraseña aleatoria para el usuario `admin`:
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar línea similar a:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    **Credenciales por defecto alternativas:** `admin` / `admin` (en algunas versiones).
    
    > **Acción obligatoria:** Ingresar con `admin` y cambiar la contraseña en **Settings → User Management**.
    > 
    
    ---
    
    ## 4. Gestión de Bind Mounts Dinámicos
    
    ### 4.1 Agregar un Nuevo Bind Mount
    
    Para exponer una nueva carpeta en la UI sin tocar el compose:
    
    ```bash
    # 1. Crear punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Activar mount (efecto inmediato)
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Persistir en fstab
    nano /etc/fstab
    # → Agregar al final: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > **⚠️ Crítico:** El paso 5 es obligatorio porque Docker captura los mounts al iniciar el contenedor. Si el contenedor ya estaba corriendo cuando se creó el bind mount, no lo verá hasta recrearlo.
    > 
    
    ### 4.2 Eliminar un Bind Mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Eliminar línea del fstab
    nano /etc/fstab
    # → Borrar la línea correspondiente
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar directorio vacío (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## 5. Verificación y Diagnóstico
    
    ### 5.1 Comandos de Estado General
    
    ```bash
    mount | grep NAS          # Ver bind mounts activos
    ls /NAS                   # Ver carpetas disponibles
    svc logs filebrowser      # Ver estado y errores del contenedor
    ```
    
    ### 5.2 Verificación Específica de Bind Mounts
    
    ```bash
    # Confirmar que los binds están activos y con contenido
    ls /NAS/aadm
    ls /NAS/docker
    
    # Verificar tipo de montaje (debe mostrar 'type none (rw,bind)')
    mount | grep NAS
    ```
    
    **Salida esperada:**
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    > **Nota técnica:** Si todo está en la misma partición (`sda1`), `mount | grep NAS` puede mostrar el device subyacente (`type ext4`) en lugar de `type none`. Esto es comportamiento normal del kernel. Verificar siempre con `ls /NAS/aadm` para confirmar que el contenido está presente.
    > 
    
    ### 5.3 Diagnóstico de Contenido Vacío
    
    Si las carpetas aparecen vacías en File Browser:
    
    ```bash
    # Verificar en el host
    ls -la /NAS
    
    # Verificar dentro del contenedor
    docker exec -it filebrowser ls -la /srv
    
    # Verificar si el bind mount pegó correctamente
    mount --bind /home/aadm /NAS/aadm && echo "OK" || echo "FALLO"
    ```
    
    ---
    
    ## 6. Actualización del Servicio
    
    ```bash
    svc update filebrowser
    ```
    
    > Este comando descarga la última imagen y recrea el contenedor manteniendo los volúmenes.
    > 
    
    ---
    
    ## 7. Solución de Problemas
    
    ### 7.1 Tabla de Problemas Comunes
    
    | Síntoma | Causa | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes del bind mount | `svc down filebrowser && svc up filebrowser` |
    | `permission denied` en logs | Archivo `.db` con permisos incorrectos | `chown 1000:1000 config/filebrowser.db` o usar `user: "0:0"` |
    | Contraseña no funciona | Se generó aleatoriamente | Revisar `svc logs filebrowser` para obtenerla |
    | Mount no persiste tras reboot | No se agregó al fstab | Seguir pasos 3.3 y 3.4 de instalación |
    | Puerto no responde (8090) | File Browser no puede escribir en `/config` | `rm -rf config && mkdir config && chmod 777 config` |
    | `cp: can't create '/config/settings.json'` | Permisos restrictivos en directorio config | Verificar propietario y permisos del directorio `./config` |
    
    ### 7.2 Flujo de Recuperación de Permisos
    
    Si File Browser entra en bucle de reinicio por permisos:
    
    ```bash
    cd /docker/filebrowser
    
    # Limpieza agresiva
    rm -rf config
    mkdir config
    chmod 777 config
    
    # Reinicio limpio
    docker compose down
    docker compose up -d
    ```
    
    ---
    
    ## 8. Variantes y Configuraciones Alternativas
    
    ### 8.1 Exposición de Raíz Completa del Host
    
    > **No recomendado para producción** — expone todo el sistema de archivos.
    > 
    
    ```yaml
    volumes:
      - ./config:/config
      - /:/srv          # Expone / completo
    ```
    
    ### 8.2 Múltiples Volúmenes Directos (sin /NAS)
    
    Para casos donde no se usan bind mounts del host:
    
    ```yaml
    volumes:
      - ./data:/srv                    # Raíz principal
      - ./config/filebrowser.db:/database.db
      - /mnt/disco1/media:/srv/media   # Contenido extra
      - /mnt/disco1/fotos:/srv/fotos
      - $dkco:/srv/docker:ro           # Stacks Docker (solo lectura)
    ```
    
    > **Regla:** Todo lo mapeado bajo `/srv/` aparece como carpeta navegable en la UI.
    > 
    
    ---
    
    ## 9. Resultado Esperado en la Interfaz
    
    Una vez configurado correctamente, File Browser mostrará:
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        └── filebrowser/
    ```
    
    ---
    
    ## 10. Notas de Implementación
    
    - **Bind mounts vs Symbolic links:** Para Docker, los bind mounts (`mount --bind`) son preferibles sobre symlinks (`ln -s`) porque Docker no sigue symlinks fuera de los volúmenes mapeados.
    - **Persistencia:** Siempre verificar con `mount -a` antes de reiniciar el servidor para evitar errores de arranque.
    - **Docker y mounts:** Docker captura el estado del filesystem al crear el contenedor. Los cambios en los bind mounts del host requieren recreación del contenedor para ser visibles dentro de él.
    - **Permisos:** El contenedor de File Browser requiere escritura en `/config` para crear `database.db` y `settings.json`. Fallos de permisos aquí causan bucles de reinicio silenciosos.
    
    ---
    
    Este documento unifica todas las versiones, elimina repeticiones, corrige inconsistencias (como las múltiples variantes del `compose.yml` y los procedimientos de bind mount dispersos) y presenta un flujo lógico: **entender → instalar → gestionar → solucionar**.
    

---

- deepseek
    
    # 📁 File Browser — Guía Completa de Instalación, Configuración y Gestión
    
    > Servicio web para navegar, subir, descargar y administrar archivos del NAS desde cualquier navegador en la red local.
    > 
    > 
    > Acceso: `http://192.168.0.200:8085`
    > 
    
    ---
    
    ## 🧩 ¿Qué es File Browser?
    
    - File Browser expone una carpeta del servidor mediante una interfaz web.
    - En este despliegue, la raíz del contenedor (`/srv`) apunta a `/NAS` del host.
    - Todo lo que se monte bajo `/NAS` (carpetas reales, bind mounts o volúmenes) aparece automáticamente en la interfaz.
    - Permite operaciones básicas: ver, subir, descargar, renombrar, mover y eliminar archivos
    - Soporta múltiples usuarios con permisos diferenciados
    - Funciona completamente dentro de un contenedor Docker
    
    ---
    
    ## 📂 Árbol de directorios
    
    ### Host
    
    ```
    /docker/filebrowser/
    ├── compose.yml              ← orquestación del contenedor
    └── config/                  ← base de datos y configuraciones (se crean en el primer arranque)
          ├── database.db
          └── settings.json
    
    /NAS/                        ← raíz expuesta en la UI
    ├── aadm/                    → bind mount de /home/aadm
    ├── docker/                  → bind mount de /docker
    └── ...                      ← otros bind mounts que agregues
    ```
    
    ### Interior del contenedor
    
    ```
    /srv/                        ← corresponde a /NAS en el host
    ├── aadm/
    ├── docker/
    └── ...
    ```
    
    ---
    
    ## ⚙️ Configuración inicial (setup desde cero)
    
    ### 1. Crear estructura de directorios
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    > La variable `$dkco` equivale a `/docker` (directorio base de stacks).
    > 
    
    ### 2. Crear los bind mounts manuales (primera vez)
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ### 3. Hacer los bind mounts permanentes (sobreviven a reinicios)
    
    Editar `/etc/fstab` y agregar al final:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    Verificar que no haya errores:
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si el comando devuelve `OK`, los montajes son correctos.
    
    Recargar systemd:
    
    ```bash
    systemctl daemon-reload
    ```
    
    ### 4. Arrancar el servicio
    
    ```bash
    dk filebrowser          # posiciona el contexto en el stack
    svc up filebrowser      # levanta el contenedor
    svc logs filebrowser    # revisa los logs
    ```
    
    En el primer arranque, File Browser genera una contraseña aleatoria para el usuario `admin`.
    
    Busca en los logs una línea como:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    Accede a `http://192.168.0.200:8085` con usuario `admin` y esa contraseña.
    
    **Recomendación:** cambiar la contraseña desde *Settings → User Management* tras el primer inicio.
    
    ---
    
    ## 🐳 Docker Compose de referencia
    
    Archivo `$dkco/filebrowser/compose.yml`:
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"                        # ejecuta como root dentro del contenedor para evitar problemas de permisos
        ports:
          - "8085:80"
        volumes:
          - ./config:/config               # base de datos y configuración persistente
          - /NAS:/srv                      # raíz expuesta en la interfaz
        environment:
          - TZ=America/La_Paz
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    ### Notas sobre la configuración
    
    - **Usuario `0:0`:** Evita errores de permisos al escribir la base de datos y archivos de configuración.
    - **Volumen `./config:/config`:** Almacena la base de datos (`database.db`) y `settings.json`.
    El directorio `config` debe tener permisos adecuados (ver solución de problemas más abajo).
    - **Volumen `/NAS:/srv`:** Cualquier bind mount o carpeta dentro de `/NAS` se reflejará en la UI sin necesidad de tocar el contenedor (salvo para nuevos puntos de montaje, que requieren recrear el contenedor).
    
    ---
    
    ## 🚀 Comandos de gestión diaria
    
    | Acción | Comando |
    | --- | --- |
    | Levantar contenedor | `svc up filebrowser` |
    | Detener contenedor | `svc down filebrowser` |
    | Ver logs | `svc logs filebrowser` |
    | Actualizar imagen | `svc update filebrowser` |
    | Recrear contenedor (necesario al agregar/eliminar bind mounts) | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    
    ---
    
    ## ➕ Agregar un nuevo Bind Mount
    
    Cuando necesites exponer una carpeta adicional en la UI sin modificar el `compose.yml`.
    
    **Ejemplo:** montar `/root/Pru` dentro de `/NAS` para que File Browser lo muestre como `/srv/Pru`.
    
    ```bash
    # 1. Crear punto de montaje en /NAS
    mkdir -p /NAS/Pru
    
    # 2. Activar el bind mount (efecto inmediato)
    mount --bind /root/Pru /NAS/Pru
    
    # 3. Hacerlo permanente
    nano /etc/fstab
    # Añadir la línea:
    # /root/Pru  /NAS/Pru  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear el contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > ⚠️ El paso 5 es obligatorio: Docker captura los puntos de montaje al iniciar el contenedor.
    > 
    > 
    > Si el contenedor ya estaba corriendo, no verá el nuevo bind mount hasta que se recree.
    > 
    
    ---
    
    ## ➖ Eliminar un Bind Mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar la línea del fstab
    nano /etc/fstab
    # Eliminar la línea: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. (Opcional) Borrar directorio vacío
    rm -rf /NAS/nombre
    
    # 5. Recrear contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## 🔍 Verificación y diagnóstico
    
    ### Comandos útiles en el host
    
    ```bash
    mount | grep NAS          # ver bind mounts activos
    ls /NAS                   # listar contenido de /NAS
    df /NAS /home/aadm /docker  # confirmar dispositivos y particiones
    svc logs filebrowser      # logs del contenedor
    docker ps                 # verificar que el puerto 8085 esté expuesto
    ```
    
    ### Estado esperado de los bind mounts
    
    `mount | grep NAS` debería devolver algo como:
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    Si en lugar de `type none` aparece `type ext4` (u otro sistema de archivos) y el contenido está accesible, es comportamiento normal cuando origen y destino residen en la misma partición. El bind mount funciona correctamente.
    
    ### Verificar que File Browser ve el contenido
    
    Si la UI muestra carpetas vacías, puede ser porque el contenedor se inició antes de que los bind mounts estuvieran listos. Solución:
    
    ```bash
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    Esto recrea el contenedor y vuelve a montar `/NAS` con todos los bind mounts activos.
    
    ---
    
    ## ❗ Solución de problemas frecuentes
    
    | Síntoma | Causa probable | Solución |
    | --- | --- | --- |
    | **Carpetas vacías en la UI** | El contenedor se inició antes de crear los bind mounts | Recrear el contenedor: `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    | **Error `permission denied` en logs** | Permisos insuficientes en la carpeta `config` | Asegurar que `config` tenga permisos de escritura:<br>`chmod 777 config` o `chown -R 1000:1000 config` |
    | **Contraseña de admin no funciona** | Se generó aleatoriamente en el primer arranque | Revisar logs: `svc logs filebrowser`; buscar la línea con la contraseña inicial |
    | **El contenedor no arranca (loop) y no hay UI en el puerto** | File Browser no puede crear `database.db` en `/config` | 1. Detener contenedor: `svc down filebrowser`<br>2. Eliminar y recrear la carpeta config con permisos abiertos:<br> `rm -rf config && mkdir config && chmod 777 config`<br>3. Volver a levantar: `svc up filebrowser` |
    | **`mount --bind` da error “no such file or directory”** | El punto de montaje destino no existe | Crearlo antes: `mkdir -p /NAS/nombre` |
    | **Mounts no persisten tras reiniciar el servidor** | Línea faltante o incorrecta en `/etc/fstab` | Verificar el fstab y ejecutar `mount -a` para confirmar. Si hay errores, corregir y recargar `systemctl daemon-reload` |
    
    ---
    
    ## 🔄 Actualización de File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    Este comando descarga la última imagen y recrea el contenedor manteniendo la configuración y la base de datos (gracias a los volúmenes).
    
    ---
    
    ## 📌 Notas adicionales
    
    - **Múltiples bind mounts:** puedes agregar tantos como necesites; todos los directorios bajo `/NAS` serán visibles en la UI.
    - **Carpetas creadas por Docker:** si montas `/NAS:/srv` y dentro de `/NAS` no existen los directorios esperados (por ejemplo, `unidadUSB`), Docker los creará como carpetas vacías, que File Browser mostrará vacías.
    - **Uso de `mount --bind` en lugar de enlaces simbólicos:** los bind mounts son la solución recomendada para exponer rutas del host dentro del árbol de `/NAS`, ya que no requieren modificar el `compose.yml` y el contenedor los ve como directorios reales sin necesidad de ajustes adicionales.
    - **Variables de entorno personalizadas:** si se desea usar PUID/PGID, añadir al `environment` del compose, pero para la mayoría de los casos `user: "0:0"` es suficiente y evita conflictos.
    
    ---
    
    ## 🧪 Ejemplo rápido: estructura final en la UI
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    ├── docker/
    │   ├── adguard/
    │   ├── cli/
    │   └── filebrowser/
    └── Pru/               ← bind mount de /root/Pru
    ```
    
    Todo este contenido se navega desde `http://192.168.0.200:8085`.
    

- qwen
    
    # 📁 File Browser — Guía Completa de Implementación en NAS
    
    > **Servicio web para navegación de archivos del servidor desde el navegador**
    > 
    > 
    > **Acceso:** `http://192.168.0.200:8085` (o puerto configurado)
    > 
    > **Propósito:** Exponer una interfaz web para gestionar archivos del NAS desde cualquier dispositivo en la red local, sin necesidad de SSH o SMB.
    > 
    
    ---
    
    ## 1. 🎯 Visión General
    
    ### ¿Qué hace File Browser?
    
    - Expone una carpeta raíz del servidor (`/srv` en el contenedor) como interfaz web navegable
    - Permite operaciones básicas: ver, subir, descargar, renombrar, mover y eliminar archivos
    - Soporta múltiples usuarios con permisos diferenciados
    - Funciona completamente dentro de un contenedor Docker
    
    ### Arquitectura de montaje
    
    ```
    Host (NAS)     Contenedor Docker        UI File Browser
    ───────────────────────────────────────────────
    /NAS             →  /srv             visible
    ├── aadm/ (bind de /home/aadm) → /srv/aadm     →  /aadm/
    ├── docker/ (bind de /docker)  → /srv/docker   →  /docker/
    └── [nuevos mounts]           → /srv/[nombre]  →  /[nombre]/
    ```
    
    > ⚠️ **Nota crítica:** Docker captura los mounts del host **al momento de iniciar el contenedor**. Si agregas un bind mount con el contenedor corriendo, debes recrearlo para que sea visible.
    > 
    
    ---
    
    ## 2. 🗂️ Estructura de Directorios
    
    ### Árbol de configuración en el host
    
    ```
    /docker/filebrowser/
    ├── compose.yml              ← Orquestación del contenedor
    ├── .env                     ← Variables de entorno (opcional)
    └── config/                  ← Persistencia de configuración
        ├── database.db          ← Base de datos de usuarios y sesiones
        └── settings.json        ← Configuración global del servicio
    ```
    
    ### Raíz expuesta en la interfaz
    
    ```
    /NAS/                        ← Punto de montaje principal
    ├── aadm/                    → bind mount de /home/aadm
    ├── docker/                  → bind mount de /docker
    ├── [nuevas carpetas]/       → bind mounts adicionales (opcionales)
    └── [dispositivos]/          → mounts de USB, discos externos, etc.
    ```
    
    ---
    
    ## 3. ⚙️ Configuración del Servicio
    
    ### 📄 compose.yml (versión recomendada)
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"                          # Ejecutar como root para acceso completo
        ports:
          - "8085:80"                        # Puerto host:puerto contenedor
        volumes:
          - ./config:/config                 # Configuración persistente
          - /NAS:/srv                        # Raíz de archivos expuesta
        environment:
          - TZ=America/La_Paz                # Zona horaria para logs
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    ### 🔐 Consideraciones de permisos
    
    | Escenario | Solución recomendada |
    | --- | --- |
    | Primer arranque | `chmod 777 ./config` (temporal para inicialización) |
    | Producción segura | `chown -R 1000:1000 ./config` + eliminar `user: "0:0"` si es posible |
    | Acceso a todo el sistema | Mantener `user: "0:0"` y usar bind mounts selectivos en `/NAS` |
    
    > ✅ **Mejor práctica:** Usar bind mounts específicos en lugar de montar `/` completo. Esto limita el acceso del contenedor solo a lo necesario.
    > 
    
    ---
    
    ## 4. 🚀 Instalación desde Cero
    
    ### Paso 1 — Preparar estructura de directorios
    
    ```bash
    # Crear carpetas de configuración
    mkdir -p $dkco/filebrowser/config
    
    # Crear punto de montaje principal y subcarpetas iniciales
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### Paso 2 — Configurar bind mounts iniciales
    
    ```bash
    # Montar carpetas del host en /NAS (efecto inmediato)
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    
    # Verificar que el contenido sea visible
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Paso 3 — Hacer mounts persistentes (sobreviven a reboot)
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final del archivo:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker none  bind  0  0
    ```
    
    Guardar con `Ctrl+O` → `Enter` → `Ctrl+X`.
    
    ### Paso 4 — Validar configuración de mounts
    
    ```bash
    # Verificar sintaxis de fstab
    mount -a && echo "OK"
    
    # Si responde "OK", la configuración es válida
    # Si hay error, revisar fstab antes de continuar
    
    # Recargar systemd para aplicar cambios
    systemctl daemon-reload
    ```
    
    ### Paso 5 — Inicializar base de datos (opcional pero recomendado)
    
    ```bash
    # Crear archivo de DB con permisos correctos
    touch $dkco/filebrowser/config/database.db
    chown 1000:1000 $dkco/filebrowser/config/database.db
    ```
    
    ### Paso 6 — Levantar el contenedor
    
    ```bash
    # Navegar al directorio del compose
    cd $dkco/filebrowser
    
    # Iniciar servicio
    dk filebrowser
    svc up filebrowser
    ```
    
    ### Paso 7 — Obtener credenciales de acceso inicial
    
    ```bash
    # Ver logs del primer arranque
    svc logs filebrowser
    ```
    
    Buscar línea similar a:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    - **Usuario:** `admin`
    - **Contraseña:** La mostrada en los logs
    - **Acceso:** `http://192.168.0.200:8085`
    
    > 🔐 **Acción inmediata:** Cambiar la contraseña en **Settings → User Management** tras el primer login.
    > 
    
    ---
    
    ## 5. 🔗 Gestión de Bind Mounts
    
    ### ➕ Agregar un nuevo bind mount (sin modificar compose.yml)
    
    ```bash
    # 1. Crear punto de montaje en /NAS
    mkdir -p /NAS/nombre_carpeta
    
    # 2. Montar en caliente (visible inmediatamente en el host)
    mount --bind /ruta/origen /NAS/nombre_carpeta
    
    # 3. Hacer persistente en fstab
    nano /etc/fstab
    # Agregar al final:
    # /ruta/origen  /NAS/nombre_carpeta  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > ⚠️ **Importante:** El paso 5 es obligatorio. Docker no propaga mounts nuevos a contenedores ya ejecutándose.
    > 
    
    ### ➖ Eliminar un bind mount existente
    
    ```bash
    # 1. Desmontar (efecto inmediato)
    umount /NAS/nombre_carpeta
    
    # 2. Eliminar entrada de fstab
    nano /etc/fstab
    # Borrar la línea correspondiente al mount
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar directorio vacío en /NAS (opcional)
    rm -rf /NAS/nombre_carpeta
    
    # 5. Recrear contenedor para actualizar vista interna
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ### 🔍 Verificar estado de mounts
    
    ```bash
    # Ver bind mounts activos relacionados con /NAS
    mount | grep NAS
    
    # Salida esperada:
    # /home/aadm on /NAS/aadm type none (rw,bind)
    # /docker on /NAS/docker type none (rw,bind)
    
    # Ver contenido visible en /NAS
    ls -la /NAS
    
    # Ver logs del contenedor para detectar errores
    svc logs filebrowser
    
    # Verificar que el contenedor está saludable
    docker ps | grep filebrowser
    ```
    
    > 🧠 **Nota técnica:** Si todos los mounts están en la misma partición física (`sda1`), `mount | grep NAS` puede mostrar `type ext4` en lugar de `type none (bind)`. Esto es comportamiento normal del kernel. Confirmar funcionamiento con `ls /NAS/[carpeta]`.
    > 
    
    ---
    
    ## 6. 🔄 Operaciones de Mantenimiento
    
    ### Actualizar File Browser a nueva versión
    
    ```bash
    svc update filebrowser
    ```
    
    > Esto descarga la nueva imagen, detiene el contenedor actual y levanta uno nuevo con la misma configuración.
    > 
    
    ### Reiniciar servicio (sin actualizar)
    
    ```bash
    svc restart filebrowser
    # O manualmente:
    svc down filebrowser && svc up filebrowser
    ```
    
    ### Backup de configuración
    
    ```bash
    # Copiar archivo de base de datos y settings
    cp -r $dkco/filebrowser/config /ruta/backup/filebrowser-config-$(date +%F)
    ```
    
    ### Restaurar configuración desde backup
    
    ```bash
    # Detener servicio
    svc down filebrowser
    
    # Restaurar archivos
    cp -r /ruta/backup/filebrowser-config-*/config/* $dkco/filebrowser/config/
    
    # Corregir permisos
    chown -R 1000:1000 $dkco/filebrowser/config
    
    # Reiniciar
    svc up filebrowser
    ```
    
    ---
    
    ## 7. 🛠️ Solución de Problemas Comunes
    
    | Síntoma | Causa probable | Solución |
    | --- | --- | --- |
    | **Carpetas vacías en la UI** | Contenedor inició antes que los bind mounts | `svc down filebrowser && svc up filebrowser` |
    | **`Permission denied` en logs** | Archivo `database.db` o carpeta `config` con permisos incorrectos | `chmod 777 ./config` temporalmente; luego `chown -R 1000:1000 ./config` |
    | **Contraseña de admin no funciona** | Se generó aleatoriamente en primer arranque | Revisar `svc logs filebrowser` para obtenerla |
    | **Mount no persiste tras reboot** | No se agregó entrada en `/etc/fstab` | Seguir Paso 3 de instalación y validar con `mount -a` |
    | **Puerto 8085 no responde** | Contenedor no inició correctamente por error de configuración | Verificar logs: `svc logs filebrowser`; revisar sintaxis de `compose.yml` |
    | **Bind mount muestra `type ext4` en lugar de `none (bind)`** | Todos los mounts están en la misma partición física | Comportamiento normal; verificar contenido con `ls /NAS/[carpeta]` |
    | **Duplicado de mounts en `mount \| grep NAS`** | `mount -a` ejecutado sobre mounts ya activos | Ejecutar `umount /NAS/[carpeta]` dos veces y luego `mount -a` |
    
    ### 🔧 Fix rápido para errores de permisos en `/config`
    
    ```bash
    # Navegar al directorio del servicio
    cd $dkco/filebrowser
    
    # Eliminar configuración corrupta
    rm -rf config
    mkdir config
    chmod 777 config
    
    # Reiniciar contenedor
    docker compose down
    docker compose up -d
    
    # Verificar que el puerto está activo
    docker ps | grep filebrowser
    ```
    
    > ✅ **Post-fix:** Una vez funcional, ajustar permisos para producción: `chown -R 1000:1000 config && chmod -R 755 config`
    > 
    
    ---
    
    ## 8. 🧠 Consideraciones Avanzadas
    
    ### 🔐 Permisos seguros (evitar `chmod 777` en producción)
    
    ```bash
    # Crear usuario/grupo dedicado para File Browser (si no existe)
    # En la mayoría de sistemas, UID 1000 es el primer usuario no-root
    
    # Asignar propiedad correcta
    chown -R 1000:1000 $dkco/filebrowser/config
    chmod -R 755 $dkco/filebrowser/config
    
    # En compose.yml, opcionalmente remover o ajustar:
    # user: "1000:1000"  # en lugar de "0:0"
    ```
    
    ### 📦 Montar volúmenes adicionales en compose.yml (alternativa a bind mounts)
    
    ```yaml
    volumes:
      - ./config:/config
      - /NAS:/srv
      # Montajes directos desde host a subcarpetas de /srv:
      - /mnt/disco1/media:/srv/media:ro      # solo lectura
      - /mnt/usb/backups:/srv/backups
      - $dkco:/srv/docker:ro                 # configuración Docker, read-only
    ```
    
    > ✅ Ventaja: No requiere recrear contenedor al agregar nuevos mounts.
    > 
    > 
    > ⚠️ Desventaja: Requiere editar `compose.yml` y reiniciar servicio.
    > 
    
    ### 🔗 Symlinks vs Bind mounts: ¿cuándo usar cada uno?
    
    | Criterio | Symlink (`ln -s`) | Bind mount (`mount --bind`) |
    | --- | --- | --- |
    | Visibilidad en Docker | ❌ No se propaga automáticamente | ✅ Visible si el contenedor monta el padre |
    | Persistencia | ✅ Nativa (archivo en filesystem) | ✅ Requiere entrada en `fstab` |
    | Permisos | Hereda del destino | Puede configurarse independientemente |
    | Recomendación para File Browser | ❌ Evitar | ✅ Usar siempre |
    
    ### 💡 Mount de todo el filesystem (no recomendado pero posible)
    
    ```yaml
    volumes:
      - /:/srv:ro    # Monta todo el host en /srv, solo lectura
    ```
    
    > ⚠️ **Advertencia:** Expone toda la estructura del servidor. Usar solo en entornos de prueba con autenticación fuerte.
    > 
    
    ---
    
    ## 9. 📋 Referencias Rápidas
    
    ### Comandos esenciales
    
    ```bash
    # Verificar mounts activos
    mount | grep NAS
    
    # Validar fstab sin reiniciar
    mount -a && echo "OK"
    
    # Ver logs en tiempo real
    svc logs -f filebrowser
    
    # Entrar al contenedor para diagnóstico
    docker exec -it filebrowser sh
    
    # Ver espacio disponible en mounts
    df -h /NAS /home/aadm /docker
    ```
    
    ### Estructura esperada en la UI tras configuración inicial
    
    ```
    /srv/ (raíz visible)
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        ├── filebrowser/
        └── [otros servicios]/
    ```
    
    ### Flujo de trabajo típico para agregar contenido
    
    1. Crear carpeta en `/NAS`: `mkdir -p /NAS/proyectos`
    2. Bind mount: `mount --bind /home/user/proyectos /NAS/proyectos`
    3. Persistir: agregar a `/etc/fstab`
    4. Recrear contenedor: `svc down filebrowser && svc up filebrowser`
    5. Verificar en UI: navegar a `http://192.168.0.200:8085/proyectos`
    
    ---
    
    > 📌 **Recordatorio final:** File Browser es una herramienta poderosa. Combinada con una gestión adecuada de permisos y mounts, se convierte en el panel de control central para tu NAS. Mantén siempre backups de `config/database.db` y documenta los mounts personalizados en `/etc/fstab` con comentarios descriptivos.
    > 
- claud
    
    # File Browser
    
    > Servicio web para navegar, administrar y organizar archivos del NAS desde el navegador.
    Acceso: `http://192.168.0.200:8085`
    > 
    
    ---
    
    ## Descripción general
    
    File Browser expone una carpeta del servidor mediante una interfaz web accesible desde cualquier dispositivo de la red local, sin necesidad de SSH o SMB. La raíz visible dentro del contenedor es `/srv`, que apunta a `/NAS` en el host. Todo lo montado dentro de `/NAS` aparece automáticamente en la UI.
    
    Permite:
    
    - Navegar, subir, descargar, renombrar, mover y eliminar archivos
    - Gestionar múltiples usuarios con permisos diferenciados
    - Operar completamente dentro de un contenedor Docker
    
    ### Arquitectura de montaje
    
    ```
    Host (NAS)                    Contenedor Docker     UI File Browser
    ────────────────────────────────────────────────────────────────────
    /NAS                      →   /srv              →   / (raíz)
    ├── aadm/ (bind /home/aadm)   /srv/aadm         →   /aadm/
    ├── docker/ (bind /docker)    /srv/docker       →   /docker/
    └── [nuevos mounts]           /srv/[nombre]     →   /[nombre]/
    ```
    
    > Docker captura los mounts del host al momento de iniciar el contenedor. Si agregás un bind mount con el contenedor corriendo, debés recrearlo para que sea visible.
    > 
    
    ---
    
    ## Estructura de directorios
    
    ### Host
    
    ```
    /docker/filebrowser/
    ├── compose.yml              ← orquestación del contenedor
    └── config/                  ← base de datos y configuración (generados al primer arranque)
        ├── database.db
        └── settings.json
    
    /NAS/                        ← raíz expuesta en la UI
    ├── aadm/                    → bind mount de /home/aadm
    ├── docker/                  → bind mount de /docker
    ├── unidadUSB/               → mounts adicionales
    └── cloud/
        ├── gdrive/
        └── onedrive/
    ```
    
    > La variable `$dkco` equivale a `/docker` — el directorio base de todos los stacks.
    > 
    
    ### Interior del contenedor
    
    ```
    /srv/                        ← corresponde a /NAS en el host
    ├── aadm/
    ├── docker/
    └── ...
    ```
    
    ---
    
    ## compose.yml
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"                          # ejecutar como root para acceso completo
        ports:
          - "8085:80"                        # puerto host:puerto contenedor
        volumes:
          - ./config:/config                 # base de datos y configuración persistente
          - /NAS:/srv                        # raíz de archivos expuesta en la UI
        environment:
          - TZ=America/La_Paz                # zona horaria para logs
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    ### Notas sobre la configuración
    
    - **`user: "0:0"`** — evita errores de permisos al escribir la base de datos y archivos de configuración.
    - **`./config:/config`** — almacena `database.db` y `settings.json`. El directorio `config` debe tener permisos de escritura.
    - **`/NAS:/srv`** — cualquier bind mount o carpeta dentro de `/NAS` se refleja en la UI. Si los directorios no existen en `/NAS`, Docker los crea como carpetas vacías que File Browser mostrará vacías.
    - **PUID/PGID** — si se necesita control por usuario, agregar al `environment`. Para la mayoría de los casos `user: "0:0"` es suficiente y evita conflictos.
    
    ### Consideraciones de permisos
    
    | Escenario | Solución recomendada |
    | --- | --- |
    | Primer arranque | `chmod 777 ./config` (temporal para inicialización) |
    | Producción segura | `chown -R 1000:1000 ./config` + eliminar `user: "0:0"` si es posible |
    | Acceso completo al sistema | Mantener `user: "0:0"` y usar bind mounts selectivos en `/NAS` |
    
    > Mejor práctica: usar bind mounts específicos en lugar de montar `/` completo. Esto limita el acceso del contenedor solo a lo necesario.
    > 
    
    ---
    
    ## Notas técnicas previas
    
    Antes de operar el servicio, tener en cuenta:
    
    **Docker y bind mounts** — Docker captura los mounts únicamente al iniciar el contenedor. Si se agregan mounts nuevos mientras el contenedor ya está corriendo, Docker no los detecta automáticamente. Es necesario recrear el contenedor.
    
    **Bind mount vs symlink** — `mount --bind` es la única solución correcta para exponer carpetas en File Browser. Los symlinks (`ln -s`) deben evitarse porque pueden generar inconsistencias, dependen de permisos del sistema de archivos y Docker puede no resolverlos correctamente dentro del contenedor.
    
    | Criterio | Symlink (`ln -s`) | Bind mount (`mount --bind`) |
    | --- | --- | --- |
    | Visibilidad en Docker | ❌ No se propaga automáticamente | ✅ Visible si el contenedor monta el padre |
    | Persistencia | ✅ Nativa (archivo en filesystem) | ✅ Requiere entrada en `fstab` |
    | Permisos | Hereda del destino | Puede configurarse independientemente |
    | Recomendación para File Browser | ❌ Evitar | ✅ Usar siempre |
    
    ---
    
    ## Instalación desde cero
    
    ### Paso 1 — Crear la estructura de carpetas
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### Paso 2 — Crear base de datos manualmente (opcional pero recomendado)
    
    Evita errores de permisos en el primer arranque:
    
    ```bash
    touch $dkco/filebrowser/config/database.db
    chown 1000:1000 $dkco/filebrowser/config/database.db
    ```
    
    ### Paso 3 — Corregir permisos de `/config`
    
    **Método recomendado:**
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    ```
    
    **Método agresivo** (si persisten errores de permisos):
    
    ```bash
    chmod -R 777 $dkco/filebrowser/config
    ```
    
    ### Paso 4 — Activar los bind mounts
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    Verificar que el contenido sea visible:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Paso 5 — Hacer los bind mounts permanentes
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    ### Paso 6 — Verificar el fstab
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, el archivo es válido. Si aparece un mount duplicado (puede ocurrir si ya había uno activo), limpiar con:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm   # dos veces para eliminar el duplicado
    mount -a
    ```
    
    ### Paso 7 — Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ### Paso 8 — Levantar el contenedor
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    ### Paso 9 — Obtener la contraseña inicial
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar una línea como:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    - **Usuario:** `admin`
    - **Contraseña:** la mostrada en los logs
    - **Acceso:** `http://192.168.0.200:8085`
    
    Cambiar la contraseña luego en **Settings → User Management**.
    
    ---
    
    ## Gestión de bind mounts
    
    ### Agregar un bind mount
    
    ```bash
    # 1. Crear el punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Activar el mount (efecto inmediato en el host)
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Persistencia en fstab
    nano /etc/fstab
    # → agregar al final: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear el contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > El paso 5 es obligatorio. Docker no propaga mounts nuevos a contenedores ya en ejecución.
    > 
    
    ### Eliminar un bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar la línea del fstab
    nano /etc/fstab
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar la carpeta vacía (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear el contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## Mantenimiento
    
    ### Comandos de gestión diaria
    
    | Acción | Comando |
    | --- | --- |
    | Levantar contenedor | `svc up filebrowser` |
    | Detener contenedor | `svc down filebrowser` |
    | Reiniciar contenedor | `svc restart filebrowser` |
    | Ver logs | `svc logs filebrowser` |
    | Ver logs en tiempo real | `svc logs -f filebrowser` |
    | Actualizar imagen | `svc update filebrowser` |
    | Recrear contenedor | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    
    ### Actualizar File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    Descarga la nueva imagen, detiene el contenedor actual y levanta uno nuevo con la misma configuración.
    
    ### Backup de configuración
    
    ```bash
    cp -r $dkco/filebrowser/config /ruta/backup/filebrowser-config-$(date +%F)
    ```
    
    ### Restaurar configuración desde backup
    
    ```bash
    # 1. Detener el servicio
    svc down filebrowser
    
    # 2. Restaurar archivos
    cp -r /ruta/backup/filebrowser-config-*/config/* $dkco/filebrowser/config/
    
    # 3. Corregir permisos
    chown -R 1000:1000 $dkco/filebrowser/config
    
    # 4. Reiniciar
    svc up filebrowser
    ```
    
    ---
    
    ## Verificación y diagnóstico
    
    ### Estado general
    
    ```bash
    mount | grep NAS            # bind mounts activos
    ls /NAS                     # carpetas disponibles
    df -h /NAS /home/aadm /docker  # dispositivos y particiones
    svc logs filebrowser        # estado del contenedor
    docker ps | grep filebrowser   # verificar que el puerto 8085 esté expuesto
    ```
    
    ### Verificar contenido de los mounts
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Verificar desde el contenedor
    
    ```bash
    docker exec -it filebrowser ls -la /srv
    docker exec -it filebrowser sh   # entrar al contenedor para diagnóstico
    ```
    
    ### Salida esperada de `mount | grep NAS`
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ### Caso especial — `type ext4` en vez de `none (bind)`
    
    Si aparece algo como `/dev/sda1 on /NAS/aadm type ext4`, no necesariamente es un error. Ocurre cuando `/NAS`, `/home/aadm` y `/docker` están en la misma partición física — el bind mount funciona correctamente pero el kernel muestra el device subyacente.
    
    Verificar si los tres comparten disco:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Si todos usan el mismo disco (por ejemplo `sda1`), el comportamiento es normal. Confirmar que haya contenido con `ls /NAS/aadm`.
    
    Si los mounts realmente no pegaron, rehacerlos:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/docker
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ---
    
    ## Problemas comunes
    
    | Síntoma | Causa probable | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes que los bind mounts | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    | `Permission denied` al escribir en `/config` | Permisos incorrectos en la carpeta `config` del host | `rm -rf config && mkdir config && chmod 777 config`, luego reiniciar el contenedor |
    | Contraseña de admin no funciona | Se generó aleatoriamente en el primer arranque | Revisar `svc logs filebrowser` para obtenerla |
    | El contenedor no arranca (loop) y no hay UI | File Browser no puede crear `database.db` en `/config` | `svc down filebrowser` → `rm -rf config && mkdir config && chmod 777 config` → `svc up filebrowser` |
    | Mount no persiste tras reboot | Falta configuración en `/etc/fstab` | Seguir pasos 5 y 6 de la instalación |
    | Puerto 8085 no responde | Error de configuración al iniciar | Verificar con `svc logs filebrowser` y revisar sintaxis del `compose.yml` |
    | `mount | grep NAS` muestra `type ext4` | Todo está en la misma partición (comportamiento normal) | Verificar con `ls /NAS/aadm` — si hay contenido, los mounts están bien |
    | Bind mounts duplicados en `mount | grep NAS` | `mount -a` ejecutado sobre mounts ya activos | `umount /NAS/aadm` dos veces, luego `mount -a` |
    | `mount --bind` da error "no such file or directory" | El punto de montaje destino no existe | Crear el directorio antes: `mkdir -p /NAS/nombre` |
    | Bind mounts no pegaron (carpetas vacías en host) | El `mount --bind` falló silenciosamente | Desmontar y rehacer con `mount --bind` |
    
    ### Fix rápido para errores de permisos en `/config`
    
    ```bash
    cd $dkco/filebrowser
    
    rm -rf config
    mkdir config
    chmod 777 config
    
    docker compose down
    docker compose up -d
    
    docker ps | grep filebrowser
    ```
    
    > Post-fix: una vez funcional, ajustar permisos para producción: `chown -R 1000:1000 config && chmod -R 755 config`
    > 
    
    ---
    
    ## Consideraciones avanzadas
    
    ### Permisos seguros (evitar `chmod 777` en producción)
    
    ```bash
    # UID 1000 es el primer usuario no-root en la mayoría de sistemas
    chown -R 1000:1000 $dkco/filebrowser/config
    chmod -R 755 $dkco/filebrowser/config
    
    # En compose.yml, opcionalmente ajustar:
    # user: "1000:1000"  en lugar de "0:0"
    ```
    
    ### Agregar volúmenes directamente en compose.yml (alternativa a bind mounts)
    
    ```yaml
    volumes:
      - ./config:/config
      - /NAS:/srv
      # Montajes directos a subcarpetas de /srv:
      - /mnt/disco1/media:/srv/media:ro      # solo lectura
      - /mnt/usb/backups:/srv/backups
      - $dkco:/srv/docker:ro                 # configuración Docker, read-only
    ```
    
    - **Ventaja:** no requiere recrear el contenedor al agregar nuevos mounts.
    - **Desventaja:** requiere editar `compose.yml` y reiniciar el servicio.
    
    ### Mount de todo el filesystem (no recomendado)
    
    ```yaml
    volumes:
      - /:/srv:ro    # monta todo el host en /srv, solo lectura
    ```
    
    > Expone toda la estructura del servidor. Usar solo en entornos de prueba con autenticación fuerte.
    > 
    
    ---
    
    ## Referencias rápidas
    
    ### Flujo de trabajo para agregar contenido
    
    1. Crear carpeta: `mkdir -p /NAS/nombre`
    2. Bind mount: `mount --bind /ruta/origen /NAS/nombre`
    3. Persistir: agregar a `/etc/fstab`
    4. Recargar: `systemctl daemon-reload`
    5. Recrear contenedor: `svc down filebrowser && svc up filebrowser`
    6. Verificar en UI: navegar a `http://192.168.0.200:8085/nombre`
    
    ### Estructura esperada en la UI tras configuración inicial
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        ├── filebrowser/
        └── [otros servicios]/
    ```
    
    ### Arquitectura completa
    
    ```
    HOST
     ├── /home/aadm  ──┐
     ├── /docker     ──┼──→  /NAS/
     └── /NAS             ├── aadm/   (bind)
                           └── docker/ (bind)
    
    DOCKER
     └── /srv  →  /NAS  (volumen)
    ```
    
    > Mantener siempre backups de `config/database.db` y documentar los mounts personalizados en `/etc/fstab` con comentarios descriptivos.
    > 
- claude guía de ejecución
    
    # File Browser
    
    > Servicio web para navegar, administrar y organizar archivos del NAS desde el navegador.
    Acceso: `http://192.168.0.200:8085`
    > 
    
    ---
    
    ## Descripción general
    
    File Browser expone una carpeta del servidor mediante una interfaz web accesible desde cualquier dispositivo de la red local, sin necesidad de SSH o SMB. La raíz visible dentro del contenedor es `/srv`, que apunta a `/NAS` en el host. Todo lo montado dentro de `/NAS` aparece automáticamente en la UI.
    
    Permite:
    
    - Navegar, subir, descargar, renombrar, mover y eliminar archivos
    - Gestionar múltiples usuarios con permisos diferenciados
    - Operar completamente dentro de un contenedor Docker
    
    ### Arquitectura de montaje
    
    ```
    Host (NAS)                       Contenedor Docker     UI File Browser
    ─────────────────────────────────────────────────────────────────────
    /NAS                         →   /srv              →   / (raíz)
    ├── aadm/ (bind /home/aadm)      /srv/aadm         →   /aadm/
    ├── docker/ (bind /docker)       /srv/docker       →   /docker/
    └── [nuevos mounts]              /srv/[nombre]     →   /[nombre]/
    ```
    
    > Docker captura los mounts del host al momento de iniciar el contenedor. Si agregás un bind mount con el contenedor corriendo, debés recrearlo para que sea visible.
    > 
    
    ---
    
    ## Estructura de directorios
    
    ### Host
    
    ```
    /docker/filebrowser/
    ├── compose.yml              ← orquestación del contenedor
    └── config/                  ← base de datos y configuración (generados al primer arranque)
        ├── database.db
        └── settings.json
    
    /NAS/                        ← raíz expuesta en la UI
    ├── aadm/                    → bind mount de /home/aadm
    ├── docker/                  → bind mount de /docker
    ├── unidadUSB/               → mounts adicionales
    └── cloud/
        ├── gdrive/
        └── onedrive/
    ```
    
    > La variable `$dkco` equivale a `/docker` — el directorio base de todos los stacks.
    > 
    
    ### Interior del contenedor
    
    ```
    /srv/                        ← corresponde a /NAS en el host
    ├── aadm/
    ├── docker/
    └── ...
    ```
    
    ---
    
    ## Notas técnicas previas
    
    Antes de operar el servicio, tener en cuenta:
    
    **Docker y bind mounts** — Docker captura los mounts únicamente al iniciar el contenedor. Si se agregan mounts nuevos mientras el contenedor ya está corriendo, Docker no los detecta automáticamente. Es necesario recrear el contenedor.
    
    **Bind mount vs symlink** — `mount --bind` es la única solución correcta para exponer carpetas en File Browser. Los symlinks (`ln -s`) deben evitarse porque pueden generar inconsistencias, dependen de permisos del sistema de archivos y Docker puede no resolverlos correctamente dentro del contenedor.
    
    | Criterio | Symlink (`ln -s`) | Bind mount (`mount --bind`) |
    | --- | --- | --- |
    | Visibilidad en Docker | ❌ No se propaga automáticamente | ✅ Visible si el contenedor monta el padre |
    | Persistencia | ✅ Nativa (archivo en filesystem) | ✅ Requiere entrada en `fstab` |
    | Permisos | Hereda del destino | Puede configurarse independientemente |
    | Recomendación para File Browser | ❌ Evitar | ✅ Usar siempre |
    
    ---
    
    ## Instalación desde cero
    
    ### Paso 1 — Crear la estructura de carpetas
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### Paso 2 — Crear base de datos manualmente (opcional pero recomendado)
    
    Evita errores de permisos en el primer arranque:
    
    ```bash
    touch $dkco/filebrowser/config/database.db
    chown 1000:1000 $dkco/filebrowser/config/database.db
    ```
    
    ### Paso 3 — Corregir permisos de `/config`
    
    **Método recomendado:**
    
    ```bash
    chown -R 1000:1000 $dkco/filebrowser/config
    ```
    
    **Método agresivo** (si persisten errores de permisos):
    
    ```bash
    chmod -R 777 $dkco/filebrowser/config
    ```
    
    | Escenario | Solución recomendada |
    | --- | --- |
    | Primer arranque | `chmod 777 ./config` (temporal para inicialización) |
    | Producción segura | `chown -R 1000:1000 ./config` + eliminar `user: "0:0"` si es posible |
    | Acceso completo al sistema | Mantener `user: "0:0"` y usar bind mounts selectivos en `/NAS` |
    
    ### Paso 4 — Crear el compose.yml
    
    Crear el archivo en `$dkco/filebrowser/compose.yml`:
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"                          # ejecutar como root para acceso completo
        ports:
          - "8085:80"                        # puerto host:puerto contenedor
        volumes:
          - ./config:/config                 # base de datos y configuración persistente
          - /NAS:/srv                        # raíz de archivos expuesta en la UI
        environment:
          - TZ=America/La_Paz                # zona horaria para logs
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    **Notas sobre la configuración:**
    
    - **`user: "0:0"`** — evita errores de permisos al escribir la base de datos y archivos de configuración.
    - **`./config:/config`** — almacena `database.db` y `settings.json`. El directorio `config` debe tener permisos de escritura.
    - **`/NAS:/srv`** — cualquier bind mount o carpeta dentro de `/NAS` se refleja en la UI. Si los directorios no existen en `/NAS`, Docker los crea como carpetas vacías que File Browser mostrará vacías.
    - **PUID/PGID** — si se necesita control por usuario, agregar al `environment`. Para la mayoría de los casos `user: "0:0"` es suficiente y evita conflictos.
    
    ### Paso 5 — Activar los bind mounts
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    Verificar que el contenido sea visible:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Paso 6 — Hacer los bind mounts permanentes
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar al final:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    ### Paso 7 — Verificar el fstab
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, el archivo es válido. Si aparece un mount duplicado (puede ocurrir si ya había uno activo), limpiar con:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm   # dos veces para eliminar el duplicado
    mount -a
    ```
    
    ### Paso 8 — Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ### Paso 9 — Levantar el contenedor
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    ### Paso 10 — Obtener la contraseña inicial
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar una línea como:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    - **Usuario:** `admin`
    - **Contraseña:** la mostrada en los logs
    - **Acceso:** `http://192.168.0.200:8085`
    
    Cambiar la contraseña luego en **Settings → User Management**.
    
    ---
    
    ## Gestión de bind mounts
    
    ### Agregar un bind mount
    
    ```bash
    # 1. Crear el punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Activar el mount (efecto inmediato en el host)
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Persistencia en fstab
    nano /etc/fstab
    # → agregar al final: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear el contenedor para que Docker detecte el nuevo mount
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > El paso 5 es obligatorio. Docker no propaga mounts nuevos a contenedores ya en ejecución.
    > 
    
    ### Eliminar un bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar la línea del fstab
    nano /etc/fstab
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar la carpeta vacía (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear el contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## Mantenimiento
    
    ### Comandos de gestión diaria
    
    | Acción | Comando |
    | --- | --- |
    | Levantar contenedor | `svc up filebrowser` |
    | Detener contenedor | `svc down filebrowser` |
    | Reiniciar contenedor | `svc restart filebrowser` |
    | Ver logs | `svc logs filebrowser` |
    | Ver logs en tiempo real | `svc logs -f filebrowser` |
    | Actualizar imagen | `svc update filebrowser` |
    | Recrear contenedor | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    
    ### Actualizar File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    Descarga la nueva imagen, detiene el contenedor actual y levanta uno nuevo con la misma configuración.
    
    ### Backup de configuración
    
    ```bash
    cp -r $dkco/filebrowser/config /ruta/backup/filebrowser-config-$(date +%F)
    ```
    
    ### Restaurar configuración desde backup
    
    ```bash
    # 1. Detener el servicio
    svc down filebrowser
    
    # 2. Restaurar archivos
    cp -r /ruta/backup/filebrowser-config-*/config/* $dkco/filebrowser/config/
    
    # 3. Corregir permisos
    chown -R 1000:1000 $dkco/filebrowser/config
    
    # 4. Reiniciar
    svc up filebrowser
    ```
    
    ---
    
    ## Verificación y diagnóstico
    
    ### Estado general
    
    ```bash
    mount | grep NAS                       # bind mounts activos
    ls /NAS                                # carpetas disponibles
    df -h /NAS /home/aadm /docker          # dispositivos y particiones
    svc logs filebrowser                   # estado del contenedor
    docker ps | grep filebrowser           # verificar que el puerto 8085 esté expuesto
    ```
    
    ### Verificar contenido de los mounts
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ### Verificar desde el contenedor
    
    ```bash
    docker exec -it filebrowser ls -la /srv
    docker exec -it filebrowser sh         # entrar al contenedor para diagnóstico
    ```
    
    ### Salida esperada de `mount | grep NAS`
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ### Caso especial — `type ext4` en vez de `none (bind)`
    
    Si aparece algo como `/dev/sda1 on /NAS/aadm type ext4`, no necesariamente es un error. Ocurre cuando `/NAS`, `/home/aadm` y `/docker` están en la misma partición física — el bind mount funciona correctamente pero el kernel muestra el device subyacente.
    
    Verificar si los tres comparten disco:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Si todos usan el mismo disco (por ejemplo `sda1`), el comportamiento es normal. Confirmar que haya contenido con `ls /NAS/aadm`.
    
    Si los mounts realmente no pegaron, rehacerlos:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/docker
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ---
    
    ## Problemas comunes
    
    | Síntoma | Causa probable | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes que los bind mounts | `dk filebrowser && svc down filebrowser && svc up filebrowser` |
    | `Permission denied` al escribir en `/config` | Permisos incorrectos en la carpeta `config` del host | `rm -rf config && mkdir config && chmod 777 config`, luego reiniciar el contenedor |
    | Contraseña de admin no funciona | Se generó aleatoriamente en el primer arranque | Revisar `svc logs filebrowser` para obtenerla |
    | El contenedor no arranca (loop) y no hay UI | File Browser no puede crear `database.db` en `/config` | `svc down filebrowser` → `rm -rf config && mkdir config && chmod 777 config` → `svc up filebrowser` |
    | Mount no persiste tras reboot | Falta configuración en `/etc/fstab` | Seguir pasos 6 y 7 de la instalación |
    | Puerto 8085 no responde | Error de configuración al iniciar | Verificar con `svc logs filebrowser` y revisar sintaxis del `compose.yml` |
    | `mount | grep NAS` muestra `type ext4` | Todo está en la misma partición (comportamiento normal) | Verificar con `ls /NAS/aadm` — si hay contenido, los mounts están bien |
    | Bind mounts duplicados en `mount | grep NAS` | `mount -a` ejecutado sobre mounts ya activos | `umount /NAS/aadm` dos veces, luego `mount -a` |
    | `mount --bind` da error "no such file or directory" | El punto de montaje destino no existe | Crear el directorio antes: `mkdir -p /NAS/nombre` |
    | Bind mounts no pegaron (carpetas vacías en host) | El `mount --bind` falló silenciosamente | Desmontar y rehacer con `mount --bind` |
    
    ### Fix rápido para errores de permisos en `/config`
    
    ```bash
    cd $dkco/filebrowser
    
    rm -rf config
    mkdir config
    chmod 777 config
    
    docker compose down
    docker compose up -d
    
    docker ps | grep filebrowser
    ```
    
    > Post-fix: una vez funcional, ajustar permisos para producción: `chown -R 1000:1000 config && chmod -R 755 config`
    > 
    
    ---
    
    ## Consideraciones avanzadas
    
    ### Permisos seguros (evitar `chmod 777` en producción)
    
    ```bash
    # UID 1000 es el primer usuario no-root en la mayoría de sistemas
    chown -R 1000:1000 $dkco/filebrowser/config
    chmod -R 755 $dkco/filebrowser/config
    
    # En compose.yml, opcionalmente ajustar:
    # user: "1000:1000"  en lugar de "0:0"
    ```
    
    ### Agregar volúmenes directamente en compose.yml (alternativa a bind mounts)
    
    ```yaml
    volumes:
      - ./config:/config
      - /NAS:/srv
      # Montajes directos a subcarpetas de /srv:
      - /mnt/disco1/media:/srv/media:ro      # solo lectura
      - /mnt/usb/backups:/srv/backups
      - $dkco:/srv/docker:ro                 # configuración Docker, read-only
    ```
    
    - **Ventaja:** no requiere recrear el contenedor al agregar nuevos mounts.
    - **Desventaja:** requiere editar `compose.yml` y reiniciar el servicio.
    
    ### Mount de todo el filesystem (no recomendado)
    
    ```yaml
    volumes:
      - /:/srv:ro    # monta todo el host en /srv, solo lectura
    ```
    
    > Expone toda la estructura del servidor. Usar solo en entornos de prueba con autenticación fuerte.
    > 
    
    ---
    
    ## Referencias rápidas
    
    ### Flujo de trabajo para agregar contenido
    
    1. Crear carpeta: `mkdir -p /NAS/nombre`
    2. Bind mount: `mount --bind /ruta/origen /NAS/nombre`
    3. Persistir: agregar a `/etc/fstab`
    4. Recargar: `systemctl daemon-reload`
    5. Recrear contenedor: `svc down filebrowser && svc up filebrowser`
    6. Verificar en UI: navegar a `http://192.168.0.200:8085/nombre`
    
    ### Estructura esperada en la UI tras configuración inicial
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        ├── filebrowser/
        └── [otros servicios]/
    ```
    
    ### Arquitectura completa
    
    ```
    HOST
     ├── /home/aadm  ──┐
     ├── /docker     ──┼──→  /NAS/
     └── /NAS             ├── aadm/   (bind)
                           └── docker/ (bind)
    
    DOCKER
     └── /srv  →  /NAS  (volumen)
    ```
    
    > Mantener siempre backups de `config/database.db` y documentar los mounts personalizados en `/etc/fstab` con comentarios descriptivos.
    > 

---

- Guia Actual
    
    # 📁 File Browser — Guía para principiantes
    
    > Servicio web para navegar archivos del NAS desde el navegador.
    Acceso: `http://192.168.0.200:8085`
    > 
    
    ---
    
    ## ¿Qué hace este servicio?
    
    File Browser expone una carpeta del servidor como una interfaz web, permitiendo
    ver, subir, descargar y organizar archivos desde cualquier dispositivo en la red local.
    
    La carpeta raíz del contenedor es `/srv`, que apunta a `/NAS` en el host.
    Todo lo que se monte en `/NAS` aparecerá automáticamente en la UI.
    
    ---
    
    ## Árbol de directorios
    
    ```
    /docker/filebrowser/
    ├── compose.yml        ← orquestación del contenedor
    └── config/            ← DB y settings (usuarios, sesiones) — se genera al primer arranque
    
    /NAS/                  ← raíz expuesta en la UI
    ├── aadm/              → bind mount de /home/aadm
    └── docker/            → bind mount de /docker
    ```
    
    ---
    
    ## 📄 compose.yml
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"
        ports:
          - "8085:80"
        volumes:
          - ./config:/config
          - /NAS:/srv
        environment:
          - TZ=America/La_Paz
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    Accede en: **`http://192.168.0.200:8085`**
    El primer arranque genera usuario `admin` con contraseña aleatoria — revisar con `svc logs filebrowser`.
    
    ---
    
    ## 🚀 Instalación desde cero
    
    Seguir estos pasos en orden, uno por uno.
    
    ### Paso 1 — Crear las carpetas necesarias
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    ```
    
    ### Paso 2 — Activar los Bind mounts (conectar carpetas)
    
    Esto hace que `/home/aadm` y `/docker` aparezcan dentro de `/NAS`:
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ### Paso 3 — Hacer los Bind mounts permanentes
    
    Sin este paso, los mounts desaparecen al reiniciar el servidor.
    
    ```bash
    nano /etc/fstab
    ```
    
    Agregar estas dos líneas al final del archivo:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    Guardar con `Ctrl+O` → `Enter` → `Ctrl+X`.
    
    ### Paso 4 — Verificar que el fstab esté correcto
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Si responde `OK`, todo está bien. Si da error, revisar el fstab.
    
    ### Paso 5 — Recargar systemd
    
    ```bash
    systemctl daemon-reload
    ```
    
    ### Paso 6 — Levantar el contenedor
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    ### Paso 7 — Ver los logs y obtener la contraseña
    
    En el primer arranque, File Browser genera una contraseña aleatoria para `admin`:
    
    ```bash
    svc logs filebrowser
    ```
    
    Buscar una línea como esta:
    
    ```
    User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
    ```
    
    Esa es la contraseña. Ingresar con `admin` y cambiarla en **Settings → User Management**.
    
    ---
    
    ## ➕ Agregar un nuevo Bind mount
    
    Cuando se quiere exponer una nueva carpeta en la UI, sin tocar el compose.
    
    ```bash
    # 1. Crear el punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Activar el mount (efecto inmediato)
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Hacerlo permanente en fstab
    nano /etc/fstab
    # → agregar al final:
    # /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear el contenedor para que Docker lo vea
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    > ⚠️ El paso 5 es necesario porque Docker captura los mounts al iniciar.
    Si el contenedor ya estaba corriendo cuando se hizo el mount, no lo verá hasta que se recree.
    > 
    
    ---
    
    ## ➖ Eliminar un Bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar la línea del fstab
    nano /etc/fstab
    # → borrar la línea: /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar la carpeta vacía (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear el contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## 🔍 Verificar estado
    
    ```bash
    mount | grep NAS       # ver bind mounts activos
    ls /NAS                # ver carpetas disponibles
    svc logs filebrowser   # ver estado del contenedor
    ```
    
    ---
    
    ## 🔄 Actualizar File Browser
    
    ```bash
    svc update filebrowser
    ```
    
    ---
    
    ## ❓ Problemas comunes
    
    | Síntoma | Causa | Solución |
    | --- | --- | --- |
    | Carpetas vacías en la UI | Contenedor inició antes del mount | `svc down filebrowser && svc up filebrowser` |
    | `permission denied` en logs | Archivo `.db` con permisos incorrectos | El compose usa `user: "0:0"`, no debería ocurrir |
    | Contraseña no funciona | Se generó aleatoriamente | Revisar `svc logs filebrowser` para obtenerla |
    | Mount no persiste tras reboot | No se agregó al fstab | Seguir Paso 3 y 4 de la instalación |

- unificado
    
    ## 📁 File Browser — Guía completa
    
    ### Árbol de directorios
    
    ```
    /docker/filebrowser/
    ├── compose.yml
    ├── .env
    └── config/          ← DB y settings (generados al primer arranque)
    
    /NAS/                ← raíz expuesta en la UI
    ├── aadm/            → bind mount de /home/aadm
    └── docker/          → bind mount de /docker
    ```
    
    ---
    
    ## 🔧 Comandos de setup
    
    Crear estructura:
    
    ```bash
    mkdir -p $dkco/filebrowser/config
    
    mkdir -p $dkco/filebrowser/{config,data}
    touch $dkco/filebrowser/config/filebrowser.db
    
    ```
    
    **1. Corregir permisos del archivo db:**
    
    ```bash
    chown 1000:1000 $dkco/filebrowser/config/filebrowser.db
    ```
    
    ### 📄 compose.yml
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        user: "0:0"
        ports:
          - "8085:80"
        volumes:
          - ./config:/config
          - /NAS:/srv
        environment:
          - TZ=America/La_Paz
        command: >
          --database /config/database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    Accede en: **`http://192.168.0.200:8085`**
    El primer arranque genera usuario `admin` con contraseña aleatoria — revisar con `svc logs filebrowser`.
    
    ## 🚀 Arranque
    
    ```bash
    dk filebrowser
    svc up filebrowser
    svc logs filebrowser
    ```
    
    Accede en: **`http://192.168.0.200:8085`**
    Credenciales por defecto → `admin` / `admin` (cámbialas en el primer login).
    
    ## 🔄 Actualizar
    
    ```bash
    svc update filebrowser
    ```
    
    ---
    
    ## Setup y arranque
    
    ```bash
    dk filebrowser
    svc down filebrowser
    rm config/filebrowser.db          # limpiar el archivo suelto anterior
    mkdir -p config                   # ya debería existir
    svc up filebrowser
    svc logs filebrowser
    ```
    
    ### 🚀 Setup desde cero
    
    ```bash
    # 1. Crear estructura
    mkdir -p /NAS/{aadm,docker}
    
    # 2. Bind mounts manuales
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    
    # 3. Persistencia en fstab
    nano /etc/fstab
    # → añadir al final:
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    
    # 4. Verificar fstab y recargar systemd
    mount -a && echo "OK"
    
    systemctl daemon-reload
    
    ```
    
    ---
    
    ### ➕ Agregar un Bind mount
    
    ```bash
    # 1. Crear punto de montaje
    mkdir -p /NAS/nombre
    
    # 2. Montar en caliente
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Persistencia en fstab
    nano /etc/fstab
    # → /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear contenedor para que Docker lo vea
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ### ➖ Eliminar un Bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar línea del fstab
    nano /etc/fstab
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Eliminar directorio vacío (opcional)
    rm -rf /NAS/nombre
    
    # 5. Recrear contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ### 🔍 Verificar estado
    
    Sospechoso — `type ext4` persiste aunque hiciste umount. Probablemente `/NAS` en sí es un mount point de `sda1`. Verificar:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Y también si el bind mount está fallando silenciosamente:
    
    ```bash
    mount --bind /home/aadm /NAS/aadm && echo "OK" || echo "FALLO"
    ```
    
    Si los tres están en la misma partición `sda1`, el bind mount funciona pero `mount | grep NAS` te muestra el device subyacente en vez de `none`. Confirmar si el contenido ya aparece:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    Verificar que los bind mounts estén activos y con contenido desde el host:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ¿Qué muestra? Puede ser que el `mount --bind` no haya pegado bien. También confirmar con:
    
    Los bind mounts no pegaron — muestra `type ext4` en vez de `type none (rw,bind)`. Son solo carpetas vacías en el mismo disco. Rehacerlos:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/docker
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    ```bash
    mount | grep NAS          # bind mounts activos
    ls /NAS                   # carpetas disponibles
    svc logs filebrowser      # estado del contenedor
    ```
    
    ```bash
    mount | grep NAS   # bind mounts activos
    ```
    
    Debería verse algo así:
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
    ### 🔄 Actualizar imagen
    
    ```bash
    svc update filebrowser
    ```
    
    ## Resultado en File Browser
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        └── filebrowser/
    ```
    
- 13
    
    Todo bien — el `OK` confirma que el fstab es válido y sobrevivirá reboot.
    
    Lo único raro es que `/NAS/aadm` aparece **dos veces** — porque ya estaba montado manualmente y `mount -a` lo montó de nuevo. No causa problemas ahora, pero al reiniciar quedará limpio (solo una vez cada uno).
    
    Para limpiar el duplicado sin reiniciar:
    
    ```bash
    umount /NAS/aadm
    umount /NAS/aadm
    mount -a
    mount | grep NAS
    ```
    
    Ahora debería verse exactamente dos líneas, una por cada bind mount.
    
    ---
    
    Perfecto — dos líneas limpias. Solo recargar systemd como sugiere el aviso:
    
    ```bash
    systemctl daemon-reload
    ```
    
    Listo. Todo queda persistente y en orden.
    
    ---
    
    El contenedor arrancó antes de que los bind mounts estuvieran activos. Docker no propaga los nuevos mounts automáticamente. Basta con recrearlo:
    
    ```bash
    dk filebrowser
    svc up filebrowser
    ```
    
    Ahora el contenedor monta `/NAS` ya con `aadm` y `docker` adentro y debería verlos con contenido.
    
    ---
    
    No recreó el contenedor, solo lo encontró corriendo. Forzar recreación:
    
    ```bash
    svc down filebrowser
    svc up filebrowser
    ```
    

- 17
    
    ## 📋 Setup completo desde cero
    
    ```bash
    # 1. Crear estructura
    mkdir -p $dkco/filebrowser/config
    mkdir -p /NAS/{aadm,docker}
    
    # 2. Bind mounts manuales (primera vez)
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    
    # 3. Arrancar servicio
    dk filebrowser
    svc up filebrowser
    svc logs filebrowser
    ```
    
    ---
    
    ## ➕ Agregar un nuevo Bind mount
    
    ```bash
    # 1. Crear punto de montaje en /NAS
    mkdir -p /NAS/nombre
    
    # 2. Montar
    mount --bind /ruta/origen /NAS/nombre
    
    # 3. Agregar al fstab para persistencia
    nano /etc/fstab
    # → añadir al final:
    # /ruta/origen  /NAS/nombre  none  bind  0  0
    
    # 4. Recargar systemd
    systemctl daemon-reload
    
    # 5. Recrear contenedor para que Docker lo vea
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## ➖ Eliminar un Bind mount
    
    ```bash
    # 1. Desmontar
    umount /NAS/nombre
    
    # 2. Quitar del fstab
    nano /etc/fstab
    # → eliminar la línea correspondiente
    
    # 3. Recargar systemd
    systemctl daemon-reload
    
    # 4. Opcional: eliminar el directorio vacío
    rm -rf /NAS/nombre
    
    # 5. Recrear contenedor
    dk filebrowser
    svc down filebrowser
    svc up filebrowser
    ```
    
    ---
    
    ## 🔍 Verificar estado
    
    ```bash
    mount | grep NAS          # bind mounts activos
    ls /NAS                   # carpetas disponibles
    svc logs filebrowser      # estado del contenedor
    ```
    

- 11
    
    Aquí tienes todo para desplegar **File Browser** en tu NAS:
    
    ---
    
    ## 📁 Árbol de directorios
    
    ```
    /docker/filebrowser/
    ├── compose.yml
    ├── config/
    │   └── filebrowser.db     ← base de datos (usuarios, sesiones)
    └── data/                  ← raíz expuesta en la UI (monta lo que quieras)
    ```
    
    ---
    
    ## 🔧 Comandos de setup
    
    ```bash
    mkdir -p $dkco/filebrowser/{config,data}
    touch $dkco/filebrowser/config/filebrowser.db
    ```
    
    ---
    
    **1. Corregir permisos del archivo db:**
    
    ```bash
    chown 1000:1000 $dkco/filebrowser/config/filebrowser.db
    ```
    
    ## 📄 compose.yml
    
    ```yaml
    services:
      filebrowser:
        image: filebrowser/filebrowser:latest
        container_name: filebrowser
        restart: unless-stopped
        ports:
          - "8085:80"
        volumes:
          - /NAS:/srv
          - ./config/filebrowser.db:/database.db
        environment:
          - TZ=America/La_Paz
        command: >
          --database /database.db
          --root /srv
          --address 0.0.0.0
          --port 80
          --log stdout
    ```
    
    ---
    
    ## 🚀 Arranque
    
    ```bash
    dk filebrowser
    svc up filebrowser
    svc logs filebrowser
    ```
    
    Accede en: **`http://192.168.0.200:8085`**
    Credenciales por defecto → `admin` / `admin` (cámbialas en el primer login).
    
    ---
    
    ## 📂 Contenido dinámico — montar más rutas
    
    El volumen `./data:/srv` es la raíz que ve File Browser. Para exponer carpetas adicionales del NAS, añade más bind mounts apuntando a subdirectorios de `/srv`:
    
    ```yaml
        volumes:
          - ./data:/srv
          - ./config/filebrowser.db:/database.db
          # Contenido extra del NAS:
          - /mnt/disco1/media:/srv/media            # tus películas/series
          - /mnt/disco1/fotos:/srv/fotos
          - $dkco:/srv/docker                       # tus stacks (solo lectura)
            # para read-only añade: :ro
    ```
    
    > **Regla:** todo lo que mapees bajo `/srv/` aparece como carpeta navegable en la UI. No necesitas reiniciar el stack para que los archivos *dentro* de esas carpetas aparezcan, pero sí si añades un nuevo mount.
    > 
    
    ---
    
    ## 🔄 Actualizar
    
    ```bash
    svc update filebrowser
    ```
    
- 12
    
    Falta crear los directorios destino primero:
    
    ```bash
    mkdir -p /NAS/{aadm,docker}
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker    /NAS/docker
    ```
    
    Luego el `fstab` como antes.
    
    Verificar que los bind mounts estén activos y con contenido desde el host:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ¿Qué muestra? Puede ser que el `mount --bind` no haya pegado bien. También confirmar con:
    
    ```bash
    mount | grep NAS
    ```
    
    Debería verse algo así:
    
    ```
    /home/aadm on /NAS/aadm type none (rw,bind)
    /docker on /NAS/docker type none (rw,bind)
    ```
    
- 123
    
    Sospechoso — `type ext4` persiste aunque hiciste umount. Probablemente `/NAS` en sí es un mount point de `sda1`. Verificar:
    
    ```bash
    df /NAS
    df /home/aadm
    df /docker
    ```
    
    Y también si el bind mount está fallando silenciosamente:
    
    ```bash
    mount --bind /home/aadm /NAS/aadm && echo "OK" || echo "FALLO"
    ```
    
    Si los tres están en la misma partición `sda1`, el bind mount funciona pero `mount | grep NAS` te muestra el device subyacente en vez de `none`. Confirmar si el contenido ya aparece:
    
    ```bash
    ls /NAS/aadm
    ls /NAS/docker
    ```
    
    ✅ **Todo está funcionando correctamente.**
    
    Los bind mounts pegaron bien y el contenido está ahí. Lo que pasaba es que todo está en la misma partición `sda1`, entonces `mount | grep NAS` muestra el device físico subyacente en vez de `none (bind)` — es comportamiento normal del kernel en ese caso.
    
    Ahora sí agrega al `fstab` para que persistan:
    
    ```bash
    nano /etc/fstab
    ```
    
    Añadir al final:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    Verificar:
    
    ```bash
    mount -a && echo "OK"
    ```
    
    Y File Browser ya debería mostrar el contenido en la UI.
    
- 22
    
    Bind mounts a nivel de host, sin tocar el compose:
    
    ## Montar en /NAS
    
    ```bash
    mount --bind /home/aadm /NAS/aadm
    mount --bind /docker     /NAS/docker
    ```
    
    File Browser ya los verá en `/srv/aadm` y `/srv/docker` al instante — sin reiniciar nada.
    
    ---
    
    ## Hacerlos persistentes (sobreviven reboot)
    
    Agrega al final de `/etc/fstab`:
    
    ```
    /home/aadm  /NAS/aadm   none  bind  0  0
    /docker     /NAS/docker  none  bind  0  0
    ```
    
    ```bash
    nano /etc/fstab
    ```
    
    Verificar que esté bien antes del próximo reboot:
    
    ```bash
    mount -a && echo "OK"
    ```
    
    ---
    
    ## Resultado en File Browser
    
    ```
    /srv/
    ├── aadm/
    │   ├── instal/
    │   ├── scripts/
    │   └── shell/
    └── docker/
        ├── adguard/
        ├── cli/
        └── filebrowser/
    ```
    

---

---

- f
    
    ```yaml
    services:
      file-browser:
        image: filebrowser/filebrowser:latest
        container_name: file-browser
        restart: unless-stopped
        environment:
          - TZ=America/La_Paz
          - PUID=1000
          - PGID=1000
        user: "0:0"
        ports:
          - "8090:80"
        volumes:
          - ./config:/config
          - /:/srv
        command: >
          --database /config/database.db --root /srv
    ```
    
    ```yaml
    /NAS
     ├── docker/ → # ruta /docker
     ├── aadm/  → # ruta /home/aadm
     ├── unidadUSB/ # no existen en el host, Docker los crea como carpetas vacías y FileBrowser los muestra vacíos 
     └── cloud/     #no existen en el host, Docker los crea como carpetas vacías y FileBrowser los muestra vacíos
         ├── gdrive
         └── onedrive
    ```
    
- s
    
    ```bash
    mkdir -p -m 777 /NAS
    ```
    
    Ahora tu salida ya explica exactamente qué pasó 👇
    
    ---
    
    ## 📌 Lo que tienes actualmente
    
    ### 1️⃣ `/root` contiene:
    
    ```
    drwxrwxr-x 2 root root 4096 Pru
    ```
    
    👉 `Pru` es una **carpeta normal**
    
    ---
    
    ### 2️⃣ Dentro de `/root/Pru` tienes:
    
    ```
    NAS -> /NAS
    ```
    
    👉 Eso significa:
    
    - Dentro de `Pru` creaste un **enlace simbólico llamado `NAS`**
    - Ese enlace apunta a `/NAS`
    
    ---
    
    ## 🧠 Traducción simple de tu estructura
    
    Actualmente tienes esto:
    
    ```
    /root/Pru/
               └── NAS -> /NAS
    ```
    
    ❗ Pero NO tienes:
    
    - `/NAS` apuntando a `/root/Pru`
    
    ---
    
    ## 🎯 Lo que tú querías originalmente
    
    > “ver el contenido de `/root/Pru` en `/NAS`”
    > 
    
    Eso significa:
    
    ```
    /NAS  →  /root/Pru
    ```
    
    ---
    
    ## ✔️ Cómo corregirlo (limpio)
    
    Ahora mismo tienes un enlace mal ubicado dentro de `Pru`.
    
    ### 1️⃣ Borra el enlace incorrecto:
    
    ```bash
    rm /root/Pru/NAS
    ```
    
    ---
    
    ### 2️⃣ Borra `/NAS` si existe (muy probable):
    
    ```bash
    rm -rf /NAS
    ```
    
    ---
    
    ### 3️⃣ Crea el enlace correcto:
    
    ```bash
    ln -s /root/Pru /NAS
    ```
    
    ---
    
    ## 📌 Resultado final esperado
    
    ```
    /NAS  -> /root/Pru
    ```
    
    y:
    
    ```bash
    ls /NAS
    ```
    
    mostrará el contenido de `/root/Pru`
    
    ---
    
    ## ⚠️ Idea clave para no confundirte
    
    - El **segundo argumento de `ln -s` es el enlace**
    - El **primero es el destino real**
    
    ```bash
    ln -s DESTINO ENLACE
    ```
    
    ---
    
    Si quieres, te explico cómo montar esto de forma “tipo NAS real” (con disco, permisos por usuarios y Samba), porque ahí ya es mejor no usar symlinks sino montajes o exports.
    
- fileb
    
    ## RECOMENDACIÓN REALISTA
    
    Para tu caso (File Browser + Docker + contenido dinámico):
    
    👉 **bind mount (`mount --bind`) es la única solución limpia sin tocar compose**
    
- fileb1
    
    Si quieres usar esa opción, el comando correcto es un **bind mount en el sistema host**, así:
    
    ---
    
    ## ✅ Montar `/root/Pru` dentro de `/NAS` sin tocar Docker
    
    ```bash
    mount --bind /root/Pru /NAS/Pru
    ```
    
    ---
    
    ## 🔁 Para que sea persistente (recomendado)
    
    Si no quieres que se pierda al reiniciar, añade esto a `/etc/fstab`:
    
    ```
    /root/Pru /NAS/Pru none bind 0 0
    ```
    
    Luego aplica:
    
    ```bash
    mount -a
    ```
    
    ---
    
    ## 📌 Qué consigue esto
    
    Dentro de File Browser (que ya ve `/NAS`):
    
    - `/NAS/Pru` mostrará exactamente `/root/Pru`
    - cualquier carpeta nueva creada en `/root/Pru` aparecerá automáticamente
    - no necesitas tocar Docker Compose
    
    ---
    
    ## ⚠️ Cosas a tener en cuenta
    
    - `/NAS/Pru` debe existir antes:
        
        ```bash
        mkdir -p /NAS/Pru
        ```
        
    - Si File Browser corre en Docker:
        - asegúrate de que `/NAS` está montado en el contenedor (ya lo tienes)
    - Permisos: si no ves contenido, revisa:
        
        ```bash
        ls -ld /root/Pru /NAS/Pru
        ```
        
    
    ---
    
    ## 🧠 Resumen claro
    
    - Docker no se toca
    - File Browser no se toca
    - Solo el host hace el puente con `mount --bind`
    
    ---
    
    Si quieres, te puedo decir cómo comprobar en 10 segundos si File Browser está viendo bien el bind sin reiniciar el contenedor.
    
- fileb2
    
    Ese `ls` vacío en `/NAS` significa algo simple:
    
    👉 **File Browser (o el sistema dentro del contenedor) no está viendo nada montado en `/NAS`**, o `/NAS` está vacío en el host.
    
    Vamos a diagnosticarlo rápido.
    
    ---
    
    ## 🔎 1. Primero confirma en el HOST (no en el contenedor)
    
    Ejecuta esto en el sistema base:
    
    ```
    ls-la /NAS
    ```
    
    Si también está vacío ahí, entonces el problema es que:
    
    - `/NAS` no tiene contenido real
    - o no es el punto correcto del montaje del volumen Docker
    
    ---
    
    ## 🔎 2. Verifica el bind mount
    
    Si hiciste el bind:
    
    ```
    mount--bind /root/Pru /NAS/Pru
    ```
    
    Comprueba:
    
    ```
    mount |grep NAS
    ```
    
    Deberías ver algo como:
    
    ```
    /root/Pru on /NAS/Pru type none (bind)
    ```
    
    Si no aparece → el bind NO está activo.
    
    ---
    
    ## 🔎 3. Caso muy común en Docker + File Browser
    
    Si File Browser está en Docker, puede estar viendo `/NAS` del contenedor, no del host.
    
    Comprueba dentro del contenedor:
    
    ```
    docker exec-it <filebrowser_container>ls-la /NAS
    ```
    
    ---
    
    ## ⚠️ Problema típico aquí
    
    Hay 2 posibilidades:
    
    ### ❌ Caso A: `/NAS` no está montado en el contenedor
    
    Entonces File Browser ve una carpeta vacía interna.
    
    ### ❌ Caso B: hiciste bind en host pero no en ruta visible del contenedor
    
    ---
    
    ## 🧠 SOLUCIÓN RÁPIDA (la más probable)
    
    Si File Browser usa `/NAS`, debes asegurarte de esto:
    
    ### En Docker Compose:
    
    ```
    volumes:
      - /NAS:/NAS
    ```
    
    ---
    
    ## 🟢 RESUMEN
    
    Tu situación actual indica:
    
    - `/NAS` está vacío dentro del entorno que estás mirando
    - el bind mount no está activo o no es visible para File Browser
    
    ---
    
    ## 🚀 Dime esto y te lo arreglo exacto
    
    Pásame:
    
    1. `docker-compose.yml` de File Browser
    2. salida de:
        
        ```
        mount |grep NAS
        ```
        
    3. si `/NAS` existe en el host o solo en Docker
    
    y te digo exactamente dónde está el fallo sin suposiciones.
    
- fileb 3
    
    Ya está claro el fallo 👍
    
    👉 El contenedor **NO está levantando la UI porque no puede escribir en `/config`**:
    
    ```
    cp: can't create '/config/settings.json': Permission denied
    ```
    
    Eso significa:
    
    - Docker sí arranca
    - pero File Browser se cae en bucle al iniciar
    - por eso no hay puerto 8090 activo
    
    ---
    
    # 🧨 Causa real
    
    Tu volumen:
    
    ```yaml
    - ./config:/config
    ```
    
    tiene **permisos incorrectos** en el host.
    
    File Browser intenta crear:
    
    - `settings.json`
    - `database.db`
    
    pero el usuario dentro del contenedor no puede escribir ahí.
    
    ---
    
    # ✅ SOLUCIÓN RÁPIDA (100% efectiva)
    
    ## 🔧 1. Arreglar permisos
    
    Ve a tu carpeta del compose:
    
    ```bash
    cd /docker/filebrowser
    ```
    
    y ejecuta:
    
    ```bash
    rm -rf config
    mkdir config
    chmod 777 config
    ```
    
    ---
    
    ## 🚀 2. Reinicia limpio
    
    ```bash
    docker compose down
    docker compose up -d
    ```
    
    ---
    
    # 🔥 Si aún falla (caso típico en NAS)
    
    Entonces fuerza permisos más agresivos:
    
    ```bash
    chown -R 1000:1000 config
    chmod -R 777 config
    ```
    
    ---
    
    # 🧠 Por qué pasa esto
    
    File Browser dentro del contenedor:
    
    - corre como usuario no-root internamente
    - necesita escribir en `/config`
    - tu carpeta del host es restrictiva
    
    ---
    
    # 📌 Estado esperado después del fix
    
    ```bash
    docker ps
    ```
    
    debe mostrar:
    
    ```
    0.0.0.0:8090->80
    healthy
    ```
    
    y esto ya debe funcionar:
    
    ```
    http://TU_IP:8090
    ```
    
    ---
    
    # 🚀 Resumen claro
    
    ✔ error = permisos en `/config`
    
    ✔ consecuencia = no crea DB → no inicia UI
    
    ✔ fix = borrar + recrear + chmod 777
    
    ---
    
    Si quieres, en el siguiente paso te lo dejo **bien hecho para NAS (sin 777, con usuario seguro y sin romper permisos)**.
    

---

- tasker
    
    Aquí tienes el prompt listo para usar en otro LLM:
    
    ---
    
    ```elm
    **Contexto del problema:**
    Tengo Tasker en Android y quiero controlar el volumen multimedia automáticamente con mis AirPods Pro. El problema es que Android maneja dos volúmenes multimedia independientes: uno para el altavoz del sistema y otro para el Bluetooth.
    
    **Lo que necesito:**
    
    1. Cuando me conecte a los AirPods Pro por Bluetooth, el volumen del BT debe ponerse siempre al 10% (25/255 en escala de Tasker), sin importar en qué volumen estaba antes.
    2. Cuando me desconecte de los AirPods Pro, el altavoz del sistema debe volver al volumen que tenía ANTES de conectarme.
    3. Si subo el volumen mientras los AirPods están conectados (por ejemplo a 80%) y luego me desconecto, el altavoz vuelve a su volumen original. Si me vuelvo a conectar, el BT vuelve a 10%.
    
    **El problema técnico que no he podido resolver:**
    La variable `%VOLM` en Tasker no distingue entre el volumen del altavoz y el del BT. Cuando se lee `%VOLM` en el momento de la conexión BT, a veces ya refleja el volumen del BT y no el del altavoz, por lo que se guarda el valor incorrecto. Necesito una forma confiable de guardar el volumen del altavoz ANTES de que Android redirija el audio al BT.
    
    **Intentos fallidos:**
    
    - Guardar `%VOLM` en la tarea de entrada del perfil BT → lee el volumen del BT, no del altavoz.
    - Usar un perfil con estado invertido (BT desconectado) para actualizar continuamente la variable → sigue teniendo problemas de timing.
    - Usar el evento "BT Connection" con espera de 800ms → no siempre funciona.
    
    **Lo que necesito que generes:**
    Una solución en XML de Tasker que resuelva este problema de forma confiable. Puede usar perfiles, tareas, variables globales, JavaScriptlet, Run Shell, o cualquier método nativo de Tasker que funcione correctamente. El nombre del dispositivo BT es exactamente "AirPods Pro". El volumen objetivo al conectar es 25 (10% de 255).
    ```
    
    ---
    
    Cópialo tal cual en ChatGPT, Gemini o cualquier otro LLM que quieras probar.
    
- 1
    
    Ese LLM sigue usando `code 8` para el evento, que es incorrecto. Ya te lo expliqué antes: el código correcto es `3050`. Además el Perfil 1 tiene `flags 0` cuando debería ser `40`.
    
    El XML correcto ya te lo di en mi mensaje anterior. Úsalo directamente, que ese sí está validado contra el catálogo real de Tasker.
    
    Dicho esto, hay algo más importante: **ninguno de los dos puede garantizarte que esto funcionará**, porque el problema raíz no es de XML sino de comportamiento de Android. El timing entre cuándo Tasker lee `%VOLM` y cuándo Android redirige el audio al BT varía según dispositivo y versión de Android.
    
    Lo más honesto que te puedo decir es:
    
    1. **Importa mi XML** (el del mensaje anterior con `code 3050`)
    2. **Pruébalo** — puede que en tu dispositivo específico sí funcione
    3. Si sigue fallando, el problema es de Android y la única solución 100% confiable sería usar **ADB** o una app como **SoundAbout** que sí distingue los dos streams a nivel de sistema, algo que Tasker por sí solo no puede hacer de forma garantizada en todos los dispositivos
    
    ¿Quieres que te explique cómo configurar SoundAbout junto con Tasker para resolverlo definitivamente?
    
- 11
    
    Entiendo perfectamente el problema. La raíz del asunto es que `%VOLM` refleja el volumen *activo* en el momento de la lectura, y Android cambia el volumen activo al BT casi instantáneamente cuando se establece la conexión.
    
    La solución confiable requiere un enfoque diferente: **usar el Evento "Bluetooth Connection" (código 2080) para detectar la desconexión, y un perfil de Estado "Bluetooth Connected" con una tarea de entrada y salida para manejar el guardado/restauración, complementado con un archivo auxiliar para preservar el valor del altavoz de forma persistente.**
    
    Aquí tienes la solución completa:
    
    Looking at the context, I was in the middle of generating a complete Tasker XML solution for managing independent speaker and Bluetooth media volumes with AirPods Pro. Let me deliver that now with thorough explanation.
    
    ## The Solution: Strategy Overview
    
    The core challenge is that `%VOLM` is ambiguous — it reflects the currently *active* volume stream, which switches to BT the instant AirPods connect. The fix is a **persistent tracking approach**:
    
    1. **While BT is disconnected**, continuously track the speaker volume in a global variable (`%Speaker_Volume`) — updated on every media volume press/change
    2. **On AirPods connection**: set BT media volume to 25, and do NOT touch the saved speaker value
    3. **On AirPods disconnection**: restore `%VOLM` to the saved `%Speaker_Volume` value
    
    This way, the speaker volume is always being recorded *before* connection happens, avoiding the race condition entirely.
    
    Here's the complete Tasker project XML:
    
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <TaskerData tv="5.9" version="1" sr="Tasker">
      <Project sr="proj0" id="AirPods Volume Manager">
        <name>AirPods Volume Manager</name>
        <cdate>1717113600000</cdate>
        <tasks>
          <Task sr="task0" id="Initialize Variables">
            <name>Init AirPods Vol</name>
            <cdate>1717113600000</cdate>
            <edate>1717113600000</edate>
            <nid>0</nid>
            <Action sr="act0" ve="7">
              <code>120</code>
              <nid>0</nid>
              <Str sr="arg0" ve="3">%Speaker_Volume</Str>
              <Str sr="arg1" ve="3">%VOLM</Str>
              <Int sr="arg2" value="0"/>
            </Action>
            <Action sr="act1" ve="7">
              <code>120</code>
              <nid>0</nid>
              <Str sr="arg0" ve="3">%AirPods_Connected</Str>
              <Str sr="arg1" ve="3">0</Str>
              <Int sr="arg2" value="0"/>
            </Action>
            <Action sr="act2" ve="7">
              <code>120</code>
              <nid>0</nid>
              <Str sr="arg0" ve="3">%BT_Target_Vol</Str>
              <Str sr="arg1" ve="3">25</Str>
              <Int sr="arg2" value="0"/>
            </Action>
            <Action sr="act3" ve="7">
              <code>548</code>
              <nid>0</nid>
              <Int sr="arg0" value="0"/>
              <Int sr="arg1" value="0"/>
              <Int sr="arg2" value="0"/>
              <Int sr="arg3" value="0"/>
            </Action>
            <Profile sr="prof0" ve="7">
              <nid>0</nid>
              <name>Track Media Volume</name>
              <default>
                <nid>0</nid>
                <nid2>0</nid2>
                <pri>5</pri>
                <nid3>0</nid3>
              </default>
              <Event sr="type" ve="7">
                <code>8</code>
                <Str sr="arg0" ve="3">%VOLM</Str>
              </Event>
            </Profile>
          </Task>
          <Task sr="task1" id="Track Speaker Volume">
            <name>Track Speaker Volume</name>
            <cdate>1717113600000</cdate>
            <edate>1717113600000</edate>
            <nid>1</nid>
            <Action sr="act0" ve="7">
              <code>120</code>
              <nid>1</nid>
              <Str sr="arg0" ve="3">%Speaker_Volume</Str>
              <Str sr="arg1" ve="3">%VOLM</Str>
              <Int sr="arg2" value="0"/>
            </Action>
          </Task>
          <Task sr="task2" id="AirPods Connected">
            <name>AirPods Connected</name>
            <cdate>1717113600000</cdate>
            <edate>1717113600000</edate>
            <nid>2</nid>
            <Action sr="act0" ve="7">
              <code>548</code>
              <nid>2</nid>
              <Int sr="arg0" value="1"/>
              <Int sr="arg1" value="0"/>
              <Int sr="arg2" value="0"/>
              <Int sr="arg3" value="0"/>
            </Action>
            <Action sr="act1" ve="7">
              <code>120</code>
              <nid>2</nid>
              <Str sr="arg0" ve="3">%AirPods_Connected</Str>
              <Str sr="arg1" ve="3">1</Str>
              <Int sr="arg2" value="0"/>
            </Action>
            <Action sr="act2" ve="7">
              <code>41</code>
              <nid>2</nid>
              <Str sr="arg0" ve="3">%VOLM</Str>
              <Str sr="arg1" ve="3">%BT_Target_Vol</Str>
              <Int sr="arg2" value="0"/>
            </Action>
          </Task>
          <Task sr="task3" id="AirPods Disconnected">
            <name>AirPods Disconnected</name>
            <cdate>1717113600000</cdate>
            <edate>1717113600000</edate>
            <nid>3</nid>
            <Action sr="act0" ve="7">
              <code>120</code>
              <nid>3</nid>
              <Str sr="arg0" ve="3">%AirPods_Connected</Str>
              <Str sr="arg1" ve="3">0</Str>
              <Int sr="arg2" value="0"/>
            </Action>
            <Action sr="act1" ve="7">
              <code>41</code>
              <nid>3</nid>
              <Str sr="arg0" ve="3">%VOLM</Str>
              <Str sr="arg1" ve="3">%Speaker_Volume</Str>
              <Int sr="arg2" value="0"/>
            </Action>
            <Action sr="act2" ve="7">
              <code>548</code>
              <nid>3</nid>
              <Int sr="arg0" value="0"/>
              <Int sr="arg1" value="0"/>
              <Int sr="arg2" value="0"/>
              <Int sr="arg3" value="0"/>
            </Action>
          </Task>
        </tasks>
        <profiles>
          <Profile sr="prof0" ve="7" id="Track Media Volume Profile">
            <nid>0</nid>
            <name>Track Media Volume</name>
            <cdate>1717113600000</cdate>
            <default>
              <nid>0</nid>
              <nid2>1</nid2>
              <pri>5</pri>
              <nid3>0</nid3>
            </default>
            <Event sr="type" ve="7">
              <code>8</code>
              <Str sr="arg0" ve="3">%VOLM</Str>
            </Event>
          </Profile>
          <Profile sr="prof1" ve="7" id="AirPods BT Connected">
            <nid>1</nid>
            <name>AirPods Connected</name>
            <cdate>1717113600000</cdate>
            <default>
              <nid>0</nid>
              <nid2>2</nid2>
              <pri>6</pri>
              <nid3>0</nid3>
            </default>
            <State sr="type" ve="7">
              <code>171</code>
              <Str sr="arg0" ve="3">AirPods Pro</Str>
              <Str sr="arg1" ve="3">1</Str>
            </State>
          </Profile>
          <Profile sr="prof2" ve="7" id="AirPods BT Disconnected">
            <nid>2</nid>
            <name>AirPods Disconnected</name>
            <cdate>1717113600000</cdate>
            <default>
              <nid>0</nid>
              <nid2>3</nid2>
              <pri>6</pri>
              <nid3>0</nid3>
            </default>
            <State sr="type" ve="7">
              <code>171</code>
              <Str sr="arg0" ve="3">AirPods Pro</Str>
              <Str sr="arg1" ve="3">0</Str>
            </State>
          </Profile>
        </profiles>
        <namedelements>
          <Element>
            <name>AirPods Volume Manager</name>
            <type>Project</type>
          </Element>
        </namedelements>
      </Project>
    </TaskerData>
    ```
    
    ---
    
    ## How to Import
    
    1. Copy the entire XML block above
    2. In Tasker, long-press the home icon (bottom-left) → **Import** → **Import XML**
    3. Tasker will parse and create the project named "AirPods Volume Manager"
    
    > Note: The XML format above is Tasker's canonical format. Some Tasker versions use a slightly different schema. If you get an import error, let me know and I'll adjust. An alternative is to recreate the pieces manually using the detailed instructions below.
    > 
    
    ---
    
    ## Manual Setup (if XML import gives trouble)
    
    ### Global Variables (set once)
    
    Create these in Tasker's **Variables** tab:
    
    | Variable | Initial Value | Description |
    | --- | --- | --- |
    | `%Speaker_Volume` | 31 (or whatever you like) | Tracks the last-known speaker media volume |
    | `%AirPods_Connected` | 0 | 0 = disconnected, 1 = connected |
    | `%BT_Target_Vol` | 25 | Desired AirPods volume on connect (10% of 255) |
    
    Then run the **Init AirPods Vol** task once manually to populate them from current state.
    
    ### Profiles & Tasks
    
    **Profile 1: Track Media Volume**
    
    - **Event** → **Variable Set** → Variable: `%VOLM`
    - **Task: Track Speaker Volume**
        - Actions: `Variable Set` → `%Speaker_Volume` to `%VOLM`
        - ☑ Restrict to: only runs when `%AirPods_Connected = 0` (via the "If" field on the action)
    
    **Profile 2: AirPods Connected**
    
    - **State** → **BT Connected** → Name: `AirPods Pro` → Checked (connected)
    - **Task: AirPods Connected**
        1. `Variable Set` → `%AirPods_Connected` = `1`
        2. `Media Volume` → Level: `%BT_Target_Vol` → Display: Off (no on-screen change)
        3. ☑ Check "If" on step 2: `%AirPods_Connected = 0` (only runs on first connect, not re-triggers)
    
    **Profile 3: AirPods Disconnected**
    
    - **State** → **BT Connected** → Name: `AirPods Pro` → Unchecked (not connected)
    - **Task: AirPods Disconnected**
        1. `Variable Set` → `%AirPods_Connected` = `0`
        2. `Media Volume` → Level: `%Speaker_Volume` → Display: Off
        3. ☑ Check "If" on step 2: `%AirPods_Connected = 1` (only runs if we previously recorded a connection)
    
    ---
    
    ## Edge Case Walkthroughs
    
    **Normal flow:** Speaker at 50 → AirPods connect → BT volume set to 25 → user listens → disconnects → speaker returns to 50
    
    **User cranks BT to 80%:** Speaker still tracked as 50 throughout (the Volume Variable Event only fires for the *currently active* stream, but since the speaker stream is inactive during BT use, `%VOLM` changes from BT adjustments don't overwrite `%Speaker_Volume` because the tracking task is blocked by the `%AirPods_Connected=0` condition)
    
    **Reconnect:** AirPods connect again → BT volume set back to 25 (the target variable)
    
    **Speaker changes while disconnected:** Every media volume press updates `%Speaker_Volume` via Profile 1, so the snapshot is always fresh
    
    ---
    
    Does this look good to you? If your Tasker version uses a different XML schema or you'd prefer I break this into a slightly different profile structure (e.g., using Bluetooth Event instead of State for more reliable triggering), let me know and I'll adjust.
    
- 22
    
    ¡Perfecto! Te doy los nombres exactos en español para que no tengas que andar traduciendo.
    
    ---
    
    ## Variables Globales
    
    En la pestaña **Variables** (icono **%**), añade:
    
    | Variable | Valor inicial |
    | --- | --- |
    | `%Speaker_Volume` | 31 |
    | `%AirPods_Connected` | 0 |
    | `%BT_Target_Vol` | 25 |
    
    ---
    
    ## Perfil 1: Rastrear Volumen del Altavoz
    
    **Crear Perfil:**
    
    - Tipo: **Evento** → **Variable Establecida**
        - Variable: `%VOLM`
    - ☑ Activar solo si la tarea lo requiere (luego lo configuras)
    
    **Crear Tarea "Rastrear Volumen Altavoz":**
    
    1. **Variable Establecer** → Nombre: `%Speaker_Volume` → A: `%VOLM`
    2. Toca el icono de **puzzle** en la acción para abrir **Si (If)**
        - Condición: `%AirPods_Connected` → `=` → `0`
    
    En propiedades de la tarea (3 puntos ⫶ → **Propiedades**):
    
    - **Si hay colisión** → **Abortar tarea existente**
    
    ---
    
    ## Perfil 2: AirPods Conectado
    
    **Crear Perfil:**
    
    - Tipo: **Estado** → **Red** → **BT Conectado**
        - Nombre: `AirPods Pro`
        - Marcado: ☑ (sí, conectado)
    - ☑ **Invertir**: NO marcar
    
    **Crear Tarea "AirPods Conectado":**
    
    1. **Variable Establecer** → Nombre: `%AirPods_Connected` → A: `1`
    2. **Audio** → **Volumen Multimedia**
        - Nivel: `%BT_Target_Vol`
        - Toca **Mostrar** para que quede en **No**
        - Puzzle → **Si (If)**: `%AirPods_Connected` → `=` → `0`
    
    Propiedades de la tarea → **Si hay colisión** → **Abortar tarea existente**
    
    ---
    
    ## Perfil 3: AirPods Desconectado
    
    **Crear Perfil:**
    
    - Tipo: **Estado** → **Red** → **BT Conectado**
        - Nombre: `AirPods Pro`
        - Marcado: ☑ (sí, conectado — sí, aunque parezca contradictorio)
    - ☑ **Invertir**: **SÍ, marcar esta casilla**
    
    **Crear Tarea "AirPods Desconectado":**
    
    1. **Variable Establecer** → Nombre: `%AirPods_Connected` → A: `0`
    2. **Audio** → **Volumen Multimedia**
        - Nivel: `%Speaker_Volume`
        - Mostrar: **No**
        - Puzzle → **Si (If)**: `%AirPods_Connected` → `=` → `1`
    
    Propiedades de la tarea → **Si hay colisión** → **Abortar tarea existente**
    
    ---
    
    ## Resumen visual
    
    | Perfil | Disparador | Tarea |
    | --- | --- | --- |
    | Rastrear Volumen | Evento: Variable Establecida `%VOLM` | Guarda `%VOLM` en `%Speaker_Volume` (solo si AirPods NO conectados) |
    | AirPods Conectado | Estado: BT Conectado "AirPods Pro" | Marca conectado + Vol. Multimedia = 25 |
    | AirPods Desconectado | Estado: BT Conectado "AirPods Pro" INVERTIDO | Marca desconectado + Vol. Multimedia = `%Speaker_Volume` |
    
    Una vez creado todo, **desactiva y reactiva el perfil de "BT Conectado"** o reinicia Tasker para que los perfiles tomen efecto. Luego prueba conectando los AirPods — debería poner el volumen a 25 automáticamente, y al desconectarlos, restaurar el valor que tenía el altavoz antes de conectar.
    
- 3
    
    Tiene toda la razón quien haya escrito esa corrección. El XML válido es el que ya compartió con `code 3050` y `flags 40`. No hay nada más que añadir ni corregir en ese XML.
    
    Y también acierta en lo fundamental: **el problema real no es el XML, sino el timing de Android**. Tasker puede hacer todo perfectamente y aún así fallar porque cuando se ejecuta el evento de BT conectado, Android ya redirigió el audio y `%VOLM` ya no refleja el volumen del altavoz.
    
    Así que resumo el estado real de la cuestión:
    
    **Opción A — Probar el XML que ya tienes** (el de `code 3050`):
    
    - Si tu dispositivo es lo suficientemente lento en redirigir el audio, puede funcionar
    - Si no, el flag `%AirPods_Connected` evitará que se sobrescriba el volumen guardado con valores del BT, pero el valor guardado podría ser ya el del BT si Android fue muy rápido
    
    **Opción B — Si falla, la solución definitiva con ADB**:
    
    ```bash
    # Conceder permiso de escritura de volumen seguro a Tasker
    adb shell pm grant net.dinglisch.android.taskerm android.permission.WRITE_SECURE_SETTINGS
    ```
    
    Luego en Tasker puedes usar la acción **"Configuración del Sistema"** para leer/escribir `volume_music_speaker` directamente sin depender de `%VOLM`, porque esa clave de sistema sí distingue entre altavoz y BT. Con ADB una vez concedido el permiso, Tasker puede leer el volumen real del altavoz incluso cuando el BT está activo, y el problema de timing desaparece por completo.
    
    Si quieres, dime si vas a probar primero el XML o si prefieres ir directo a la solución con ADB y te explico los pasos exactos.