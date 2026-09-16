# VS Code Server (code-server) — Guía operativa

> **Servicio:** `vscode`
> **Imagen:** `ghcr.io/coder/code-server:4.135.0-39`
> **Acceso:** `http://${SERVER_IP}:8443`
> **Puerto interno:** `8080`
> **Tipo:** contenedor Docker no-root
> **Estado de la documentación:** la corrección del arranque `fixuid` está confirmada en runtime; la ACL de Home Assistant debe aplicarse y verificarse en cada NAS antes de declararla confirmada.

Esta guía documenta una instalación NAS-only mediante Compose. No requiere PowerShell, VS Code Desktop, Remote SSH ni copiar credenciales de Windows al NAS. code-server mantiene su propia autenticación por contraseña; esa contraseña no es la contraseña de Windows y no se sincroniza con ella.

El compose catalogado evita el entrypoint oficial que ejecuta `fixuid`/`sudo`: el contenedor se inicia directamente con `/usr/bin/code-server` y con el UID/GID de `aadm`. Esto permite conservar `no-new-privileges:true` sin usar `user: root`.

## Índice

1. [Arquitectura y límites](#arquitectura-y-límites)
2. [Estructura de archivos](#estructura-de-archivos)
3. [Prerrequisitos y variables](#prerrequisitos-y-variables)
4. [Instalación en orden real](#instalación-en-orden-real)
5. [Permisos para editar Home Assistant](#permisos-para-editar-home-assistant)
6. [Verificación completa](#verificación-completa)
7. [Uso desde el navegador](#uso-desde-el-navegador)
8. [Operación diaria y actualización](#operación-diaria-y-actualización)
9. [Troubleshooting](#troubleshooting)
10. [Backup y recuperación](#backup-y-recuperación)
11. [Seguridad y secretos](#seguridad-y-secretos)

## Arquitectura y límites

El servicio monta únicamente los directorios necesarios:

| Host | Contenedor | Propósito |
|---|---|---|
| `./config` | `/home/coder/.config` | configuración de code-server y contraseña |
| `./local` | `/home/coder/.local` | extensiones y estado local del usuario |
| `./workspace` | `/home/coder/project/workspace` | workspace propio de code-server |
| `${NAS_DOTFILES}` | `/home/coder/project/nas-dotfiles` | checkout del repositorio `nas-dotfiles` |
| `../homeassistant/data` | `/home/coder/project/homeassistant` | configuración editable de Home Assistant |

No se monta todo `$dkco`, `$aadm`, `/` ni `/var/run/docker.sock`. code-server tampoco se ejecuta como `root`. El acceso al servicio se publica en la LAN mediante `8443:8080`; no debe exponerse directamente a Internet sin una capa adicional de autenticación, TLS y control de acceso.

La contraseña vive en `config/code-server/config.yaml`, porque code-server lee ese archivo de forma nativa. Un `CODE_SERVER_PASSWORD` escrito solamente en `.env` no cambia la contraseña: code-server no consume arbitrariamente esa variable con este entrypoint directo.

## Estructura de archivos

Después de completar la instalación, la estructura del servicio en el NAS es:

```text
$dkco/vscode/
├── compose.yml
├── .env                         ← variables de interpolación local, modo 600
├── config/
│   └── code-server/
│       └── config.yaml          ← contraseña local, modo 600; nunca publicar
├── local/                       ← extensiones y estado local
└── workspace/                   ← workspace persistente de code-server
```

Los artefactos versionados en este repositorio son la guía, la ficha, el compose de catálogo y `.env.example`. El `.env` real y `config.yaml` real permanecen en `$dkco/vscode/` del NAS y no se copian al repositorio.

## Prerrequisitos y variables

Ejecutar los siguientes comandos en el NAS con el entorno de `nas-dotfiles` cargado. No continuar si alguna comprobación falla:

```bash
: "${NAS_DOTFILES:?Falta NAS_DOTFILES; carga el entorno de nas-dotfiles antes de continuar}"
: "${dkco:?Falta dkco; carga el entorno Docker del NAS antes de continuar}"
: "${aadm:?Falta aadm; carga el entorno del usuario administrativo antes de continuar}"

test -d "$NAS_DOTFILES" || { echo "NAS_DOTFILES no existe: $NAS_DOTFILES" >&2; exit 1; }
test -d "$dkco" || { echo "dkco no existe: $dkco" >&2; exit 1; }
test -d "$dkco/homeassistant/data" || {
  echo "Primero debe existir la configuración de Home Assistant: $dkco/homeassistant/data" >&2
  exit 1
}
getent passwd aadm >/dev/null || { echo "No existe el usuario aadm" >&2; exit 1; }
test -r "$dkco/.env" || { echo "No se puede leer el .env global" >&2; exit 1; }
grep -q '^SERVER_IP=' "$dkco/.env" || { echo "Falta SERVER_IP en el .env global" >&2; exit 1; }
grep -q '^TZ=' "$dkco/.env" || { echo "Falta TZ en el .env global" >&2; exit 1; }
```

### Verificar el puerto antes de crear archivos

El puerto externo elegido es `8443`. Si ya está ocupado, detenerse y decidir el conflicto; no cambiar el puerto silenciosamente en un solo paso de la guía:

```bash
if ss -ltnH | awk '{print $4}' | grep -q ':8443$'; then
  echo "ERROR: el puerto 8443 ya está ocupado" >&2
  ss -ltnH | grep ':8443$' >&2 || true
  exit 1
fi
```

`VSCODE_UID` y `VSCODE_GID` deben corresponder al usuario `aadm`, que es el usuario efectivo que ejecutará code-server:

```bash
id -u aadm
id -g aadm
```

## Instalación en orden real

La secuencia es intencional: crear carpetas, crear archivos, aplicar permisos, validar Compose y solo después levantar el servicio.

### 1. Crear las carpetas

```bash
mkdir -p "$dkco/vscode/config/code-server" \
         "$dkco/vscode/local" \
         "$dkco/vscode/workspace"
```

### 2. Crear el `.env` local

Este `.env` no contiene la contraseña de code-server. Contiene valores que Compose necesita para interpolar el bind del checkout y el UID/GID. `SERVER_IP` y `TZ` se heredan del `.env` global mediante `env_file`.

```bash
dk vscode
umask 077
cat > .env <<EOF
NAS_DOTFILES=$NAS_DOTFILES
VSCODE_UID=$(id -u aadm)
VSCODE_GID=$(id -g aadm)
EOF
```

### 3. Generar la contraseña de code-server y crear `config.yaml`

Generar la contraseña una sola vez y escribirla directamente en el archivo local. El comando no la imprime ni la deja en una variable después de terminar:

```bash
umask 077
CODE_SERVER_PASSWORD="$(openssl rand -hex 32)"
cat > config/code-server/config.yaml <<EOF
bind-addr: 0.0.0.0:8080
auth: password
password: "$CODE_SERVER_PASSWORD"
cert: false
disable-telemetry: true
EOF
unset CODE_SERVER_PASSWORD
```

No usar `CODE_SERVER_PASSWORD` en el `.env`: con el entrypoint de esta guía la fuente efectiva es `config/code-server/config.yaml`. No regenerar la contraseña en cada reinicio, porque invalidaría el acceso anterior.

### 4. Crear `compose.yml`

Crear el archivo completo antes de aplicar permisos o levantar el servicio:

```bash
cat > compose.yml <<'EOF'
services:
  vscode:
    extends:
      file: ../_common.yml
      service: _defaults
    image: ghcr.io/coder/code-server:4.135.0-39
    container_name: vscode
    user: "${VSCODE_UID}:${VSCODE_GID}"
    env_file:
      - ../.env
      - .env
    ports:
      - "8443:8080"
    volumes:
      - type: bind
        source: ./config
        target: /home/coder/.config
        read_only: false
      - type: bind
        source: ./local
        target: /home/coder/.local
        read_only: false
      - type: bind
        source: ./workspace
        target: /home/coder/project/workspace
        read_only: false
      - type: bind
        source: ${NAS_DOTFILES}
        target: /home/coder/project/nas-dotfiles
        read_only: false
      - type: bind
        source: ../homeassistant/data
        target: /home/coder/project/homeassistant
        read_only: false
    entrypoint:
      - /usr/bin/code-server
    command:
      - --config
      - /home/coder/.config/code-server/config.yaml
      - --bind-addr
      - 0.0.0.0:8080
      - --disable-telemetry
      - /home/coder/project
    healthcheck:
      test:
        - CMD
        - curl
        - -fsS
        - http://127.0.0.1:8080/healthz
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s
    labels:
      - homepage.group=Herramientas
      - homepage.name=VS Code Server
      - homepage.icon=code-server
      - homepage.href=http://${SERVER_IP}:8443
      - homepage.description=Editor VS Code en el navegador
EOF
```

Detalles importantes del compose:

- `entrypoint: /usr/bin/code-server` evita `/usr/bin/entrypoint.sh`, que intenta ejecutar `fixuid` y `sudo`.
- `user: "${VSCODE_UID}:${VSCODE_GID}"` mantiene el proceso como `aadm`; nunca sustituirlo por `root`.
- `extends` hereda `restart: on-failure:5`, `no-new-privileges:true`, logging y el límite de recursos común del NAS.
- No se declara `DOCKER_USER`, porque esa variable solo era útil para el entrypoint que se ha omitido.
- Las labels de Homepage usan `${SERVER_IP}` y se aplican al recrear el contenedor.

### 5. Aplicar propietario y permisos

Aplicar permisos solo después de que las carpetas y archivos existan:

```bash
chown -R "$(id -u aadm):$(id -g aadm)" config local workspace
chmod 700 config config/code-server local workspace
chmod 600 .env config/code-server/config.yaml
```

Comprobar sin mostrar el contenido de la contraseña:

```bash
stat -c '%A %U:%G %n' .env config/code-server/config.yaml
```

El resultado esperado para los dos archivos es modo `600` y propietario `aadm:aadm`. Si `config.yaml` contiene una contraseña real, no ejecutar `cat`, `bat`, `grep password` ni copiarlo al chat.

### 6. Validar y levantar

```bash
svc config vscode
svc pull vscode
svc up vscode
```

Si ya existía un contenedor creado con el entrypoint antiguo, `svc up` puede conservarlo según el estado del Compose. Después de corregir el archivo, usar explícitamente:

```bash
svc recreate vscode
```

No declarar el servicio operativo hasta completar la [verificación completa](#verificación-completa).

## Permisos para editar Home Assistant

El bind `/home/coder/project/homeassistant` corresponde a `$dkco/homeassistant/data`. code-server corre como `aadm`; por eso el propietario de Home Assistant o sus permisos pueden impedir guardar `configuration.yaml` aunque el contenedor esté healthy.

La solución no es cambiar todo el árbol a `aadm`, usar `chmod 777` ni dar acceso a secretos. Se concede una ACL puntual para los archivos editables y para los directorios donde se deben crear o editar módulos.

### Aplicar ACL después de instalar `acl`

Primero crear las carpetas que se necesiten; después aplicar la ACL:

```bash
command -v setfacl >/dev/null || instal acl

dk homeassistant
setfacl -m u:aadm:rw data/configuration.yaml

for file in \
  data/automations.yaml \
  data/scripts.yaml \
  data/scenes.yaml; do
  if [[ -f "$file" ]]; then
    setfacl -m u:aadm:rw "$file"
  fi
done

for dir in data/core data/includes data/themes; do
  if [[ -d "$dir" ]]; then
    setfacl -R -m u:aadm:rwX "$dir"
    find "$dir" -type d -exec setfacl -m d:u:aadm:rwx {} +
  fi
done
```

Si alguno de los archivos opcionales todavía no existe, no se crea artificialmente solo para aplicar permisos. La secuencia correcta para uno nuevo es `mkdir -p`, crear el archivo y después `setfacl`.

No conceder escritura automáticamente a:

- `data/secrets.yaml`
- `data/.storage/`
- bases de datos, tokens o archivos de credenciales
- cualquier directorio que no sea necesario editar desde VS Code Server

### Verificar la ACL sin modificarla

Ejecutar la prueba desde el directorio del servicio Home Assistant:

```bash
sudo -u aadm test -w data/configuration.yaml \
  && echo "OK: aadm puede escribir configuration.yaml" \
  || echo "ERROR: aadm no puede escribir configuration.yaml"

getfacl -p data/configuration.yaml
```

La salida de `getfacl` debe mostrar una entrada `user:aadm:rw-` y la prueba debe devolver `OK`. Esta comprobación es la evidencia de runtime que falta si todavía no se ha aplicado la ACL en el NAS.

Para probar un directorio editable:

```bash
sudo -u aadm test -w data/core \
  && echo "OK: aadm puede escribir data/core" \
  || echo "ERROR: aadm no puede escribir data/core"
```

## Verificación completa

Ejecutar todos los comandos siguientes y conservar solo las salidas no sensibles:

```bash
dk vscode
svc ps vscode
svc logs vscode
svc health
curl -fsS http://127.0.0.1:8443/healthz
ss -ltnH | grep ':8443$'
svc stats vscode
```

Criterios de aceptación:

1. `svc ps vscode` muestra el contenedor `Up` y no un bucle `Restarting`.
2. El estado de healthcheck es `healthy` después del `start_period`.
3. `curl /healthz` devuelve éxito desde el NAS.
4. `ss` muestra el puerto `8443` escuchando.
5. `svc logs vscode` no contiene `fixuid is not running as root`, errores de `sudo`, `EACCES` sobre `config.yaml` ni reinicios repetidos.
6. `svc stats vscode` permite observar el consumo antes de decidir si el límite heredado del stack necesita ajuste.

Después de confirmar el servicio, abrir desde el navegador de Windows:

```text
http://${SERVER_IP}:8443
```

Usar la contraseña generada para code-server. No pegar una contraseña de Windows en el NAS ni esperar que code-server la acepte automáticamente: son credenciales independientes.

Una vez que el servicio y sus permisos estén confirmados en runtime, sincronizar el catálogo:

```bash
svc catalog-sync vscode
```

Si el pipeline modifica la ficha o el compose, revisar el diff antes de aceptar cualquier cambio y conservar esta guía como fuente narrativa de los errores y correcciones reales.

## Uso desde el navegador

El workspace raíz es `/home/coder/project`. Dentro de él se muestran:

- `workspace/` — archivos de trabajo propios de code-server.
- `nas-dotfiles/` — el checkout de `$NAS_DOTFILES`.
- `homeassistant/` — el contenido de `$dkco/homeassistant/data`.

Para editar Home Assistant, abrir `homeassistant/configuration.yaml`. Si VS Code muestra `EACCES`, no cambiar el usuario del contenedor a root: repetir la sección [Permisos para editar Home Assistant](#permisos-para-editar-home-assistant) y verificar la ACL con `sudo -u aadm test -w`.

Los linters YAML genéricos pueden marcar `!include`, `!secret` o `!include_dir_merge_named` como etiquetas desconocidas. Esas etiquetas pertenecen a Home Assistant; la validación real de su configuración se hace con `svc config homeassistant`, no con el linter genérico de VS Code.

## Operación diaria y actualización

```bash
dk vscode
svc ps vscode
svc health
svc logs vscode
svc restart vscode
svc stats vscode
```

Para actualizar la imagen, revisar primero el cambio de versión y conservar el pin hasta probarlo:

```bash
svc snapshot vscode
svc pull vscode
svc recreate vscode
svc ps vscode
svc health
```

No ejecutar `svc update vscode` como acción automática si todavía no se ha decidido el nuevo pin de imagen. La imagen está fijada deliberadamente en `4.135.0-39` para que una actualización no cambie el runtime sin revisión.

## Troubleshooting

### `fixuid: fixuid is not running as root` o `sudo: The "no new privileges" flag is set`

**Causa:** el entrypoint oficial `/usr/bin/entrypoint.sh` intenta ejecutar `fixuid` y `sudo`, pero el compose ya proporciona un UID/GID explícito y hereda `no-new-privileges:true`.

**Corrección:** conservar estas tres decisiones juntas:

```yaml
user: "${VSCODE_UID}:${VSCODE_GID}"
entrypoint:
  - /usr/bin/code-server
command:
  - --config
  - /home/coder/.config/code-server/config.yaml
  - --bind-addr
  - 0.0.0.0:8080
  - --disable-telemetry
  - /home/coder/project
```

Eliminar `DOCKER_USER` y recrear:

```bash
dk vscode
svc config vscode
svc recreate vscode
svc logs vscode
```

No resolverlo agregando `user: root` ni quitando `no-new-privileges`.

### `EACCES` al guardar `homeassistant/configuration.yaml`

**Causa:** el proceso corre como `aadm`, pero el archivo de Home Assistant no concede escritura a ese usuario.

Aplicar solo la ACL necesaria y verificarla:

```bash
dk homeassistant
setfacl -m u:aadm:rw data/configuration.yaml
sudo -u aadm test -w data/configuration.yaml
```

Para archivos de módulos y carpetas editables, usar el bloque completo de ACL de esta guía. No cambiar el propietario de todo `data`, no usar `chmod 777` y no incluir `secrets.yaml` ni `.storage`.

### El navegador no conecta

Comprobar primero el servicio, el healthcheck y el puerto antes de cambiar el compose:

```bash
dk vscode
svc ps vscode
svc health
ss -ltnH | grep ':8443$'
curl -fsS http://127.0.0.1:8443/healthz
```

Si `ss` no muestra `8443`, revisar `svc logs vscode`. Si el puerto está ocupado, volver a la verificación previa de puertos y resolver el conflicto explícitamente.

### El contenedor queda `unhealthy`

Comprobar que el proceso interno escucha en `8080` y que el healthcheck usa ese puerto; el puerto `8443` solo existe en el host:

```bash
dk vscode
svc logs vscode
svc exec vscode curl -fsS http://127.0.0.1:8080/healthz
```

No cambiar el healthcheck a `8443` dentro del contenedor: esa es la publicación externa.

### El cambio del compose no se aplica

`restart` no siempre recrea un contenedor cuando cambia `entrypoint`, `command`, volúmenes o labels. Validar y recrear:

```bash
dk vscode
svc config vscode
svc recreate vscode
svc ps vscode
```

### `NAS_DOTFILES` no existe o el volumen apunta a otra ruta

El bind se resuelve desde `.env` y debe apuntar al checkout real del NAS. Comprobarlo sin imprimir secretos:

```bash
dk vscode
test -d "$NAS_DOTFILES"
printf 'NAS_DOTFILES existe y es un directorio\n'
svc config vscode
```

Revisar que el origen resuelto del bind corresponda a `$NAS_DOTFILES` y no montar todo `$dkco` como sustituto.

### Se olvidó la contraseña

La contraseña actual está únicamente en `config/code-server/config.yaml`. No regenerarla automáticamente en cada arranque. Para rotarla de forma controlada, guardar una copia segura local del archivo, generar otra contraseña con `openssl rand -hex 32`, reemplazar solo el valor `password`, mantener `chmod 600` y ejecutar `svc recreate vscode`. Nunca mostrar el valor, añadirlo al `.env` ni publicarlo en GitHub.

## Backup y recuperación

Los datos importantes de code-server son:

- `config/`, especialmente `config/code-server/config.yaml`.
- `local/`, si se desea conservar extensiones y estado local.
- `workspace/`, si contiene trabajo que no está en otro repositorio.

El checkout `nas-dotfiles` y la configuración de Home Assistant tienen sus propios ciclos de backup; el montaje en code-server no los convierte en copias de seguridad.

Antes de una modificación importante:

```bash
dk vscode
svc snapshot vscode
```

Para recuperación, restaurar primero las carpetas locales con sus propietarios y permisos, comprobar que `config/code-server/config.yaml` sigue en modo `600`, validar Compose y recrear:

```bash
dk vscode
chown -R "$(id -u aadm):$(id -g aadm)" config local workspace
chmod 700 config config/code-server local workspace
chmod 600 .env config/code-server/config.yaml
svc config vscode
svc recreate vscode
svc ps vscode
```

Si se pierde la contraseña, la recuperación requiere una rotación manual controlada; no se debe insertar una contraseña real en un issue, PR, log o mensaje de soporte.

## Seguridad y secretos

- `config/code-server/config.yaml` contiene un secreto real: modo `600`, solo en el NAS y fuera de Git.
- `.env` local debe tener modo `600`; no contiene la contraseña de code-server en esta arquitectura.
- `SERVER_IP` y `TZ` se heredan de `$dkco/.env`; no se duplican en `environment:`.
- No usar `user: root`, `DOCKER_USER`, `chmod 777` ni `/var/run/docker.sock`.
- No montar todo `$dkco`, `$aadm` o el sistema de archivos raíz.
- No conceder ACL de escritura a `secrets.yaml`, `.storage` ni otros secretos de Home Assistant.
- Las labels publican el panel en la LAN. No es una autorización para exponerlo a Internet.

## Fuentes

- [Paquete oficial de code-server en GitHub Container Registry](https://github.com/coder/code-server/pkgs/container/code-server)
- [FAQ y configuración oficial de code-server](https://coder.com/docs/code-server/FAQ)
- [Dockerfile oficial de la imagen de release](https://github.com/coder/code-server/blob/main/ci/release-image/Dockerfile)
- [Entrypoint oficial de la imagen de release](https://github.com/coder/code-server/blob/main/ci/release-image/entrypoint.sh)
- [`docs/docker-entorno.md`](../docker-entorno.md) — convenciones Docker del NAS
- [`docs/services/homeassistant-guide.md`](homeassistant-guide.md) — estructura y permisos operativos de Home Assistant
