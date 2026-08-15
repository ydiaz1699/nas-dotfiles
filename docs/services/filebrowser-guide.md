# File Browser — Guía de instalación y operación

> Servicio web para navegar, administrar y organizar archivos del NAS desde el navegador.
> Acceso: `http://$SERVER_IP:8085`

File Browser expone `/NAS` del host como interfaz web accesible desde cualquier dispositivo de la red local. La raíz visible dentro del contenedor es `/srv`, que apunta a `/NAS` en el host. Todo lo montado dentro de `/NAS` aparece automáticamente en la UI.

---

## Arquitectura de montaje

```
Host (NAS)                       Contenedor Docker     UI File Browser
─────────────────────────────────────────────────────────────────────
/NAS (:rshared)              →   /srv              →   / (raíz)
├── aadm/ (bind /home/aadm)     /srv/aadm         →   /aadm/
├── docker/ (bind /docker)       /srv/docker       →   /docker/
├── USB/                         /srv/USB          →   /USB/
│   ├── usb-sdb1/ (automount)   /srv/USB/usb-sdb1 →   /USB/usb-sdb1/
│   └── usb-sdc1/ (automount)   /srv/USB/usb-sdc1 →   /USB/usb-sdc1/
└── [nuevos mounts]              /srv/[nombre]     →   /[nombre]/
```

> **`:rshared`** permite que mounts creados dentro de `/NAS` DESPUÉS de iniciar el contenedor sean visibles inmediatamente — sin recrear el contenedor. Esto es esencial para el USB automount.

> Docker captura los mounts del host al momento de iniciar el contenedor. Sin `:rshared`, mounts nuevos requieren recrear (`svc down` + `svc up`). Con `:rshared` se propagan en tiempo real.

---

## Estructura de directorios

```
$dkco/filebrowser/
├── compose.yml              ← orquestación del contenedor
├── .env                     ← secretos (FILEBROWSER_USER, FILEBROWSER_PASSWORD)
└── config/                  ← generados al primer arranque
    ├── database.db          ← SQLite (usuarios, sesiones, preferencias)
    └── settings.json

/NAS/                        ← raíz expuesta en la UI
├── aadm/                    → bind mount de /home/aadm
├── docker/                  → bind mount de /docker
└── [carpetas adicionales]   → bind mounts opcionales
```

---

## Conceptos previos

### Bind mount vs symlink

| Criterio | Symlink (`ln -s`) | Bind mount (`mount --bind`) |
|----------|-------------------|----------------------------|
| Visibilidad en Docker | ❌ No se propaga | ✅ Visible si el contenedor monta el padre |
| Persistencia | ✅ Nativa | ✅ Requiere entrada en `fstab` |
| Recomendación | ❌ Evitar | ✅ Usar siempre |

### Docker y mounts

Docker captura los mounts únicamente al iniciar el contenedor. Mounts nuevos mientras el contenedor corre → recrear obligatorio.

---

## Instalación desde cero

### Paso 1 — Crear estructura de carpetas

```bash
mkdir -p $dkco/filebrowser/config
mkdir -p /NAS/{aadm,docker}
```

### Paso 2 — Crear base de datos (evita errores de permisos)

```bash
touch $dkco/filebrowser/config/database.db
chown 1000:1000 $dkco/filebrowser/config/database.db
```

### Paso 3 — Permisos de /config

```bash
chown -R 1000:1000 $dkco/filebrowser/config
```

Si persisten errores:

```bash
chmod -R 777 $dkco/filebrowser/config
```

### Paso 4 — Crear compose.yml

```bash
nano $dkco/filebrowser/compose.yml
```

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
      - /NAS:/srv:rshared
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
      - homepage.href=http://${SERVER_IP}:8085
      - homepage.description=Explorador de archivos del NAS
      - homepage.widget.type=filebrowser
      - homepage.widget.url=http://${SERVER_IP}:8085
      - homepage.widget.username=${FILEBROWSER_USER}
      - homepage.widget.password=${FILEBROWSER_PASSWORD}
```

> ⚠️ **`:rshared` es obligatorio.** Sin él, los USBs que se montan dentro de `/NAS/USB/` después de iniciar el contenedor NO son visibles. Con `:rshared` el kernel propaga mounts nuevos al contenedor en tiempo real.

### Paso 5 — Crear .env (secretos locales)

```bash
cat > $dkco/filebrowser/.env << 'EOF'
FILEBROWSER_USER=admin
FILEBROWSER_PASSWORD=tu_contraseña_aqui
EOF
chmod 600 $dkco/filebrowser/.env
```

### Paso 6 — Activar bind mounts

```bash
mount --bind /home/aadm /NAS/aadm
mount --bind /docker    /NAS/docker
```

Verificar:

```bash
ls /NAS/aadm
ls /NAS/docker
```

### Paso 7 — Persistir en fstab

```bash
nano /etc/fstab
```

Agregar al final:

```
/home/aadm  /NAS/aadm   none  bind  0  0
/docker     /NAS/docker  none  bind  0  0
```

### Paso 8 — Verificar y recargar

```bash
mount -a && echo "OK"
systemctl daemon-reload
```

### Paso 9 — Levantar servicio

```bash
dk filebrowser
svc up filebrowser
```

### Paso 10 — Obtener contraseña inicial

```bash
svc logs filebrowser
```

Buscar línea:

```
User 'admin' initialized with randomly generated password: yG-JGN3s-A-DCzOG
```

Cambiar en **Settings → User Management**.

---

## Gestión de bind mounts

### Integración con USB Automount (DebMenux)

Si tienes DebMenux instalado con USB automount configurado a `MOUNT_BASE="/NAS/USB"`:

1. Los USBs se montan automáticamente en `/NAS/USB/usb-sdb1`, `/NAS/USB/usb-sdc1`, etc.
2. Gracias a `:rshared`, File Browser los muestra **inmediatamente** sin recrear el contenedor.
3. Al desconectar el USB, desaparecen automáticamente de la UI.

**Setup (una sola vez):**

```bash
# Crear directorio USB dentro de /NAS
mkdir -p /NAS/USB

# Configurar automount para montar en /NAS/USB
nano /etc/usb-automount.conf
# Cambiar: MOUNT_BASE="/NAS/USB"

# Reiniciar File Browser con :rshared (si no lo tiene ya)
dk filebrowser
svc down filebrowser && svc up filebrowser
```

> No necesitas bind mount en fstab para USB — el automount se encarga. Solo asegúrate que el compose tiene `:rshared`.

### Agregar un bind mount

```bash
mkdir -p /NAS/nombre
mount --bind /ruta/origen /NAS/nombre
nano /etc/fstab
# agregar: /ruta/origen  /NAS/nombre  none  bind  0  0
systemctl daemon-reload
svc down filebrowser && svc up filebrowser
```

> Recrear el contenedor es obligatorio — Docker no detecta mounts nuevos en caliente.

### Eliminar un bind mount

```bash
umount /NAS/nombre
nano /etc/fstab        # quitar la línea
systemctl daemon-reload
rm -rf /NAS/nombre     # opcional
svc down filebrowser && svc up filebrowser
```

---

## Mantenimiento

| Acción | Comando |
|--------|---------|
| Levantar | `svc up filebrowser` |
| Detener | `svc down filebrowser` |
| Reiniciar | `svc restart filebrowser` |
| Ver logs | `svc logs filebrowser` |
| Actualizar imagen | `svc update filebrowser` |
| Recrear (tras nuevo mount) | `svc down filebrowser && svc up filebrowser` |

### Backup

```bash
svc backup filebrowser
```

O manual:

```bash
cp -r $dkco/filebrowser/config $dkco/backups/filebrowser-config-$(date +%F)
```

### Restaurar

```bash
svc down filebrowser
cp -r $dkco/backups/filebrowser-config-FECHA/* $dkco/filebrowser/config/
chown -R 1000:1000 $dkco/filebrowser/config
svc up filebrowser
```

---

## Verificación y diagnóstico

```bash
mount | grep NAS                          # bind mounts activos
ls /NAS                                   # carpetas disponibles
svc logs filebrowser                      # logs del contenedor
docker exec -it filebrowser ls -la /srv   # verificar desde dentro
```

### Salida esperada de `mount | grep NAS`

```
/home/aadm on /NAS/aadm type none (rw,bind)
/docker on /NAS/docker type none (rw,bind)
```

> Si muestra `type ext4` en vez de `none (bind)`: es normal cuando todo está en la misma partición. Verificar con `ls /NAS/aadm` — si hay contenido, funciona.

---

## Problemas comunes

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Carpetas USB aparecen vacías | Falta `:rshared` en compose | Agregar `/NAS:/srv:rshared` y recrear |
| Carpetas vacías en la UI | Contenedor inició antes del bind mount | Con `:rshared` ya no pasa. Sin él: `svc down && svc up` |
| `Permission denied` en /config | Permisos incorrectos | `chmod -R 777 $dkco/filebrowser/config` → luego ajustar |
| Contraseña no funciona | Se generó aleatoriamente | `svc logs filebrowser` para obtenerla |
| Mount no persiste tras reboot | Falta en `/etc/fstab` | Agregar línea y `systemctl daemon-reload` |
| Puerto 8085 no responde | Contenedor crasheó | `svc logs filebrowser` para ver el error |
| Mounts duplicados | `mount -a` sobre mounts ya activos | `umount /NAS/aadm` (2 veces) → `mount -a` |
| `mount --bind` error "no such file" | Punto de montaje no existe | `mkdir -p /NAS/nombre` primero |
| USB visible pero sin contenido | Docker no propaga mounts anidados sin :rshared | Agregar `:rshared` al volume de /NAS |

### Fix rápido para permisos

```bash
dk filebrowser
svc down filebrowser
rm -rf config && mkdir config && chmod 777 config
svc up filebrowser
```

> Post-fix: `chown -R 1000:1000 config && chmod -R 755 config`

---

## Notas técnicas

- **`user: "0:0"`** — ejecuta como root para acceso completo a `/NAS`. Necesario si los archivos tienen distintos propietarios.
- **`/NAS:/srv:rshared`** — cualquier contenido dentro de `/NAS` se refleja en la UI. El flag `:rshared` propaga mounts nuevos (como USBs) al contenedor en tiempo real, sin recrear.
- **`${SERVER_IP}`** — viene del `.env` global (`$dkco/.env`). `svc` lo pasa automáticamente.
- **`${FILEBROWSER_USER/PASSWORD}`** — vienen del `.env` local (`$dkco/filebrowser/.env`). Se usan en los labels de Homepage.
- **Base de datos** — SQLite en `config/database.db`. Contiene usuarios, permisos, sesiones. Hacer backup periódico.
- **Mount propagation** — `:rshared` es equivalente a `--mount type=bind,source=/NAS,target=/srv,bind-propagation=rshared`. Requiere que el host tenga el mount como `shared` (default en systemd-based systems).
