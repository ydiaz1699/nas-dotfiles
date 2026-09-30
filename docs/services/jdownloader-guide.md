# JDownloader 2 — Guía de instalación y operación

> Gestor de descargas JDownloader 2 en contenedor, controlable por el MCP propio
> `proyec_jdw2` a través de My.JDownloader.
> GUI web (noVNC): `http://$SERVER_IP:5800`

JDownloader 2 corre headless dentro del contenedor `jlesage/jdownloader-2`, que
expone su interfaz gráfica de escritorio como una página web en el puerto `5800`
(noVNC). El control automatizado se hace con el MCP `proyec_jdw2`
(github.com/ydiaz1699/proyec_jdw2), que **no** habla con el contenedor por la red
local: habla con la **nube My.JDownloader**, y el contenedor se conecta a esa misma
nube con las credenciales que vinculas una vez por la GUI.

---

## Arquitectura de control

```
[contenedor jlesage/jdownloader-2 :5800]  ─┐
   (logueado en tu cuenta My.JDownloader)   │
[tu móvil / otros devices JD]  ─────────────┼──► nube My.JDownloader ◄── [MCP proyec_jdw2]
                                            │        (relay)              (en kiro-cli)
```

> **Consecuencia:** el MCP funciona desde cualquier sitio con salida a internet
> (incluido Kiro CLI en el NAS), siempre que el contenedor esté logueado en la
> misma cuenta My.JDownloader. No hay dependencia de la LAN privada.

### Modos de conexión de My.JDownloader

| Modo | Cómo | Puerto | Cuándo |
|------|------|--------|--------|
| **Relay** (nube) | email + password de la cuenta | — (usa la nube) | **Por defecto**; lo que usa `proyec_jdw2` |
| Direct Connection (LAN) | RemoteAPI local | `3129` (host=3129 obligatorio) | Solo si quieres control puramente local sin nube |

Esta guía usa **relay**. El puerto `3129` queda comentado en el `compose.yml`.

---

## Dos destinos de descarga

Dentro del contenedor hay dos rutas de salida montadas desde el host:

```
Host (NAS)              Contenedor        Uso
───────────────────────────────────────────────────────────────
/NAS/Descargas      →   /output           destino FIJO permanente en el NAS
/NAS/USB (:rshared) →   /usb              destino en USB, para cosas a mover
```

- **`/output`** (`/NAS/Descargas`) — carpeta normal, sin propagación de montajes.
- **`/usb`** (`/NAS/USB`) — usa **`bind.propagation: rshared`** para que un USB
  montado por el automount *después* de arrancar el contenedor sea visible al
  instante, sin recrear el contenedor.

El destino de cada descarga se elige desde el MCP:

```
jd_add_links(links, download_path="/output/pelis")     # al añadir
jd_add_links(links, download_path="/usb/usb-sdb1/tmp")
jd_set_download_directory(package_ids, "/output/serie") # cambiar después
```

---

## Estructura de directorios

```
$dkco/jdownloader/
├── compose.yml              ← orquestación del contenedor
├── .env                     ← JD_USER_ID / JD_GROUP_ID (y auth web opcional)
└── config/                  ← generado al primer arranque
    ├── ...                  ← estado y config de JDownloader
    └── ...                  ← SESIÓN My.JDownloader (persistente)

/NAS/Descargas/              ← destino fijo (crear antes, chown al UID del contenedor)
/NAS/USB/                    ← ya existe por el automount
```

---

## Instalación (orden de ejecución real)

```bash
# 1. Carpetas: config del servicio + destino fijo en el NAS
mkdir -p $dkco/jdownloader/config
mkdir -p /NAS/Descargas
# /NAS/USB ya existe por el automount; si no: mkdir -p /NAS/USB

# 2. Archivos: copiar compose y .env desde el repo
cp $NAS_DOTFILES/agent/catalog/services/jdownloader/compose.yml $dkco/jdownloader/compose.yml
cp $NAS_DOTFILES/agent/catalog/services/jdownloader/.env.example $dkco/jdownloader/.env
nano $dkco/jdownloader/.env      # ajustar JD_USER_ID / JD_GROUP_ID (ver con: id -u / id -g)

# 3. Permisos: .env con 600 y destino fijo escribible por el UID del contenedor
chmod 600 $dkco/jdownloader/.env
chown 1000:1000 /NAS/Descargas   # usar el JD_USER_ID:JD_GROUP_ID que pusiste

# 4. Registrar en el arranque escalonado REAL ($dkco/scripts/layers.conf, NO versionado).
#    OBLIGATORIO con BOOT_ORDER_REQUIRE_ALL=1: sin esta línea el PRÓXIMO REBOOT FALLA
#    ("servicio 'jdownloader' sin registrar en layers.conf"). Se añade en la Capa 5,
#    junto a filebrowser. (Editar la plantilla del repo NO basta: el boot lee el real.)
sed -i '/^filebrowser/a jdownloader' /docker/scripts/layers.conf
grep -n jdownloader /docker/scripts/layers.conf     # verificar que quedó en la Capa 5
#    Alternativa si NO quieres que arranque en el boot (bajo demanda):
#      svc no-boot jdownloader

# 5. Levantar
dk jdownloader
svc up jdownloader
svc logs jdownloader
```

> **Nota (hueco conocido):** desplegar con `cp` manual (como aquí) NO dispara el
> recordatorio `_svc_layers_reminder` que sí muestra `svc create`/`svc clone`. Por eso
> el paso 4 es explícito. Ver `docs/ideas-decisions.md` #27.

---

## Vincular My.JDownloader (manual, una sola vez)

Este paso es lo que habilita al MCP a controlar el contenedor.

1. Abre `http://$SERVER_IP:5800` en el navegador → verás el escritorio de JDownloader.
2. Acepta la licencia si aparece.
3. **Settings → My.JDownloader** → introduce el **email** y **contraseña** de tu
   cuenta My.JDownloader (la de jdownloader.org; créala en my.jdownloader.org si no
   la tienes).
4. Pon un **Device Name** reconocible, p.ej. `JD-NAS`. **Apúntalo**: ese nombre
   exacto es el `JD_DEVICE_NAME` que usará el MCP `proyec_jdw2`.
5. Verifica que el estado quede en **conectado** (icono verde).

---

## Arranque escalonado (layers.conf)

JDownloader se declara en la **Capa 5** de `layers.conf` (servicios de archivos,
junto a filebrowser). No depende de DataSQL ni de MQTT, y no bloquea capas
posteriores.

```
# Capa 5 — Servicios de archivos y notificaciones
filebrowser
jdownloader
ntfy
```

- Para dejarlo fuera del boot sin borrarlo: `svc no-boot jdownloader`.
- Para reactivarlo: `svc boot-enable jdownloader`.

---

## Operación

```bash
svc ps jdownloader        # estado
svc logs jdownloader      # logs
svc restart jdownloader   # reiniciar
svc update jdownloader    # actualizar imagen (pull + recrear)
svc open jdownloader      # abrir la GUI web
```

---

## Notas y gotchas

- **Control por MCP:** el MCP propio `proyec_jdw2` (78 tools + auto-solver de
  captchas) es la vía recomendada. Montarlo en Kiro CLI se documenta en
  `Varios_tools/kiro-cli-nas/jdownloader-mcp.md` (verificado en runtime).
- **Portapapeles en la GUI (noVNC):** pegar directo desde tu PC (Host Clipboard Sync)
  requiere **HTTPS + navegador Chromium**; por HTTP plano el navegador bloquea el
  portapapeles. Alternativas: usar el **panel de clipboard lateral** de noVNC (pestaña
  en el borde izquierdo → cuadro Clipboard → pegar ahí → Ctrl+V en la app), o activar
  `SECURE_CONNECTION=1`. Para añadir enlaces sin GUI: el MCP, `my.jdownloader.org` o la
  extensión de navegador MyJDownloader.
- **Rutas heredadas de Windows:** al restaurar un `.jd2backup` de un JDownloader de
  Windows, la carpeta de descargas queda como `C:\...` (no existe en el contenedor).
  Corregir en **Settings → General → Standard download folder → `/output`** (o `/usb`).
- **`DARK_MODE`:** `0` = tema claro (por defecto en este compose), `1` = oscuro.
- **`KEEP_APP_RUNNING=1`** relanza JDownloader si el proceso se cae dentro del
  contenedor (recomendado para uso headless controlado por MCP).
- **RAM:** `memory: 2g` sobreescribe el default de `_common.yml`; JD2 puede consumir
  bastante en el NAS de 8GB.
- **Healthcheck:** las imágenes de jlesage **no** traen un `healthcheck.sh`; se usa
  `nc -z 127.0.0.1 5800` (netcat viene en la imagen Alpine).
- **Auth web:** si expones el `:5800` en tu LAN, activa `WEB_AUTHENTICATION` +
  `WEB_AUTHENTICATION_ALLOW_INSECURE` (para HTTP plano) y define usuario/contraseña
  en el `.env` local.
- **`/NAS/Descargas` debe existir y ser escribible** por `JD_USER_ID:JD_GROUP_ID`
  antes de arrancar, o las descargas fallarán con error de permisos.

---

## Referencias

- Imagen: https://github.com/jlesage/docker-jdownloader-2 (tag `v26.09.1`)
- MCP de control: https://github.com/ydiaz1699/proyec_jdw2
- My.JDownloader: https://my.jdownloader.org
