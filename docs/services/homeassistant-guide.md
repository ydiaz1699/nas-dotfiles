# Home Assistant — Guía Operativa

> **Puerto:** 8123  
> **Imagen:** ghcr.io/home-assistant/home-assistant:stable  
> **Red:** host (acceso directo al stack de red del NAS)  
> **Tipo:** Docker container (privileged)
> **Base de datos:** `homeassistant_db` en PostgreSQL de DataSQL, mediante `127.0.0.1:<puerto-host>`; el valor final documentado del NAS es `127.0.0.1:5432`

Esta guía incorpora la configuración real compartida en la [guía de Home Assistant del usuario](https://gist.github.com/ydiaz1699/ad4f9c92edd8669d720b8865c82a73ed), adaptada a las reglas actuales de `nas-dotfiles`: operaciones Docker mediante `svc`, credenciales leídas sin `source .env`, acceso LAN mediante `${SERVER_IP}` y publicación PostgreSQL limitada al loopback. La guía compartida mostraba `192.168.0.200` en algunos ejemplos; no se copia esa IP porque el NAS documentado usa `SERVER_IP` (`192.168.1.200` en la configuración actual).

---

## Índice

1. [Estructura de archivos](#estructura-de-archivos)
2. [Compose](#compose)
3. [Primer inicio y onboarding](#primer-inicio-y-onboarding)
4. [Conectar Home Assistant a DataSQL](#conectar-home-assistant-a-datasql--procedimiento-completo)
5. [Verificación y operación diaria](#verificación-y-operación-diaria)
6. [Organización con includes](#organización-con-includes)
7. [Integración con ntfy (notificaciones push)](#integración-con-ntfy)
8. [Automatización: Cámara → snapshot → ntfy](#automatización-cámara--snapshot--ntfy)
9. [TvOverlay (notificaciones en TV)](#tvoverlay)
10. [Troubleshooting](#troubleshooting)

---

## Estructura de archivos

```
$dkco/homeassistant/
├── compose.yml
├── .env                            ← HOMEASSISTANT_TOKEN (para Homepage widget)
└── data/                           ← montado como /config dentro del contenedor
    ├── configuration.yaml          ← config principal (con !includes)
    ├── automations.yaml            ← automatizaciones
    ├── scripts.yaml
    ├── scenes.yaml
    ├── includes/                   ← configs separadas por tema
    │   ├── shell_commands.yaml     ← ntfy, utilidades
    │   ├── tvoverlay_commands.yaml ← TvOverlay (rest_command)
    │   └── notify.yaml            ← plataformas de notificación
    └── www/
        └── snapshots/              ← imágenes de cámara (temporales)
            └── alarma.jpg          ← se sobreescribe en cada detección
```

**Ruta del contenedor → Host:**
- `/config` dentro de HA = `$dkco/homeassistant/data/` en el NAS
- `/config/www/` = `$dkco/homeassistant/data/www/` = accesible como `http://IP:8123/local/`

---

## Compose

```yaml
# $dkco/homeassistant/compose.yml
services:
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    network_mode: host
    stop_grace_period: 60s
    dns:
      - 190.104.12.42
      - 200.73.96.146
      - 8.8.8.8
    privileged: true
    env_file:
      - ../.env
      - .env
    volumes:
      - ./data:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    labels:
      - homepage.group=IoT
      - homepage.name=Home Assistant
      - homepage.icon=home-assistant
      - homepage.href=http://${SERVER_IP}:8123
      - homepage.description=Automatización del hogar
      - homepage.widget.type=homeassistant
      - homepage.widget.url=http://${SERVER_IP}:8123
      - homepage.widget.key=${HOMEASSISTANT_TOKEN}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

**Notas del compose:**
- `env_file: [../.env, .env]` — hereda SERVER_IP y TZ del global, secretos del local
- `network_mode: host` — HA accede directo a la LAN (necesario para mDNS, descubrimiento IoT)
- `privileged: true` — acceso a USB, Bluetooth, dbus (necesario para integraciones hardware)
- `dns` personalizado — evita depender de AdGuard para resolver (si AdGuard cae, HA sigue)
- La relación entre este DNS explícito, `systemd-resolved`, IPv6, Avahi y descubrimiento se documenta en [`docker-nas/references/networking.md`](../../docker-nas/references/networking.md); no asumir que `network_mode: host` hace que HA use automáticamente el stub del host
- `stop_grace_period: 60s` — tiempo para guardar estado al apagar
- Homepage labels — usa `${SERVER_IP}` (nunca IP hardcodeada)
- **NO** tiene `environment: TZ` — se hereda del `.env` global

---

## Primer inicio y onboarding

DataSQL debe estar disponible antes de iniciar Home Assistant. Como los Compose
son independientes, `depends_on` no puede ordenar esta dependencia.

Primero comprueba el stack, pero **no levantes HA desde esta sección**:

```bash
svc health
svc ps datasql
```

Continúa en la sección `Conectar Home Assistant a DataSQL — procedimiento
completo`. Su orden canónico es: comprobar DataSQL, crear y verificar
`homeassistant_db`/`ha_user`, iniciar HA, completar el onboarding, configurar el
Recorder y reiniciar para verificarlo. Así se evita iniciar HA con una base
inexistente o configurar el Recorder antes de que HA cree su configuración.

La configuración canónica usa `dns` explícitos, `stop_grace_period: 60s`,
`privileged: true`, el bind `./data:/config`, healthcheck HTTP y labels de
Homepage con `${SERVER_IP}`. `network_mode: host` hace innecesario declarar
`networks`; también explica por qué HA accede al Recorder mediante el loopback
del NAS y no mediante el hostname Docker `datapostgres`.

---

## Conectar Home Assistant a DataSQL — procedimiento completo

Esta sección une la información de Home Assistant y DataSQL en un único flujo.
No es necesario usar pgAdmin para crear la base ni el usuario: la ruta
principal es la terminal del NAS con `svc exec`.

### 1. Contexto de conexión

Home Assistant usa `network_mode: host`. Por eso:

- No pertenece a `db_net`.
- No puede usar `datapostgres` como hostname Docker.
- No debe usar la IP histórica `172.20.0.4`.
- Debe usar `127.0.0.1` y el puerto publicado realmente por DataSQL.

El puerto interno de PostgreSQL es `5432`. El puerto del host se controla con
`AIPG_POSTGRES_HOST_PORT`; el `.env` y el compose instalados en el NAS son la
autoridad. El valor predeterminado actual es `5432`, pero se comprueba antes de
construir la URI:

```bash
dk datasql

if [[ ! -f "$dkco/datasql/.env" ]]; then
  printf 'No existe %s/.env\n' "$dkco/datasql" >&2
  exit 1
fi

HA_PG_PORT="$(awk -F= '$1=="AIPG_POSTGRES_HOST_PORT"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
HA_PG_PORT="${HA_PG_PORT:-5432}"
printf 'Puerto PostgreSQL para Home Assistant: 127.0.0.1:%s\n' "$HA_PG_PORT"

if ! ss -ltn | grep -Eq "127\\.0\\.0\\.1:${HA_PG_PORT}([[:space:]]|:)"; then
  printf 'No se detecta PostgreSQL escuchando en 127.0.0.1:%s.\n' "$HA_PG_PORT" >&2
  unset HA_PG_PORT
  exit 1
fi
```

Si el resultado es `5432`, la URI usará `127.0.0.1:5432`. No uses `5433` por
memoria histórica: solo usa otro puerto si el `.env` y `ss` muestran ese mismo
valor.

**Checkpoint 0 — endpoint listo:** `127.0.0.1:$HA_PG_PORT` escucha en el NAS.
No continúes si la comprobación de `ss` falla.

### 2. Comprobar DataSQL

```bash
svc health
svc ps datasql
svc net
```

Continúa solamente si:

- `datapostgres` aparece `Up (healthy)`.
- `dataredis` aparece `Up (healthy)`.
- La red externa `db_net` existe y contiene `datapostgres`.
- `svc ps datasql` muestra el bind de PostgreSQL como
  `127.0.0.1:<puerto>->5432/tcp`.

Si PostgreSQL no está saludable, detente. No levantes Home Assistant ni crees
roles o bases mientras DataSQL no esté disponible.

**Checkpoint 1 — DataSQL listo:** PostgreSQL está saludable y accesible solo
por loopback. `svc health` no recibe `datasql` como argumento; se ejecuta sin
argumentos.

### 3. Cargar las credenciales administrativas

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1)}' "$dkco/datasql/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" ]]; then
  printf 'Falta una variable administrativa en %s/.env.\n' "$dkco/datasql" >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_PG_PORT
  exit 1
fi
```

No ejecutes `source .env`, no uses `docker exec` y no pegues estas variables en
el chat.

**Checkpoint 2 — credenciales administrativas cargadas:** las tres variables
existen en la sesión actual. No las imprimas ni las guardes en el checkpoint.

### 4. Comprobar y crear el rol dedicado de Home Assistant

Genera una contraseña hexadecimal en el terminal y consérvala localmente para
introducirla en `\password` y después en `data/secrets.yaml`:

```bash
openssl rand -hex 32
```

No pegues ese valor en el chat, en el repositorio ni en el historial. Si
`openssl` no está disponible, detente y usa tu gestor de secretos habitual para
generar una contraseña hexadecimal equivalente.

El CLI `svc exec` del NAS puede interpretar opciones como `-U`, `-d` y `-c`
como opciones propias. Por eso esta guía **no pasa esas opciones directamente**:
usa `PGUSER` y `PGDATABASE` mediante `env`, y ejecuta SQL dentro de `psql`.

Abre una sesión administrativa:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`, primero comprueba si el rol existe:

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'ha_user';
```

Si la consulta no devuelve filas, crea el rol y establece su contraseña:

```sql
CREATE ROLE ha_user LOGIN;
\password ha_user
```

Introduce dos veces la contraseña hexadecimal generada anteriormente. La salida
esperada de la creación es:

```text
CREATE ROLE
```

Si la consulta ya mostró `ha_user` con `rolcanlogin = t`, no ejecutes `CREATE ROLE`
otra vez. Si mostró `rolcanlogin = f`, habilita el login:

```sql
ALTER ROLE ha_user LOGIN;
```

Si no conoces la contraseña que usa Home Assistant, ejecuta únicamente:

```sql
\password ha_user
```

para establecer una contraseña nueva y usa esa misma contraseña en
`data/secrets.yaml`. Después de cualquier creación o cambio, verifica el
estado final dentro de `psql`:

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'ha_user';
```

Debe devolver `ha_user` con `rolcanlogin = t`.

Sal siempre de `psql` antes de continuar:

```text
\q
```

`\password` evita escribir la contraseña dentro de una sentencia SQL o de
los argumentos del comando. Si el rol no se puede crear o no se puede cambiar
su contraseña, detente: no continúes con la base.

**Checkpoint 3 — rol listo:** `ha_user` existe y tiene `rolcanlogin = true`.
No repitas este paso después de confirmarlo.

### 5. Comprobar y crear la base dedicada

Abre una nueva sesión administrativa para comprobar si la base existe:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql` ejecuta:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

Si la consulta no devuelve filas, sal de esa sesión:

```text
\q
```

Abre otra sesión administrativa y crea la base. `CREATE DATABASE` se ejecuta
separadamente porque no debe ejecutarse dentro de una transacción:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`:

```sql
CREATE DATABASE homeassistant_db OWNER ha_user;
```

La salida esperada es:

```text
CREATE DATABASE
```

Sin salir de esa sesión, verifica inmediatamente el propietario:

```sql
SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'homeassistant_db';
```

La salida debe mostrar:

```text
homeassistant_db | ha_user
```

Después sal:

```text
\q
```

Si la consulta inicial ya devolvió una fila, **no ejecutes `CREATE DATABASE`**.
Confirma únicamente que el propietario sea `ha_user` y sal con `\q`. Si el
propietario es diferente, detente antes de modificarlo.

**Checkpoint 4 — base lista:** `homeassistant_db` existe y su propietario es
`ha_user`. No repitas `CREATE DATABASE` después de confirmarlo.

### 6. Verificar el login del usuario dedicado

Introduce temporalmente la contraseña dedicada sin mostrarla:

```bash
read -r -s -p 'Contraseña de ha_user para verificar: ' HA_DB_PASSWORD
printf '\n'
```

Abre `psql` usando el rol y la base de Home Assistant:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$HA_DB_PASSWORD" \
      PGUSER=ha_user \
      PGDATABASE=homeassistant_db \
  psql
```

Dentro de `psql` ejecuta:

```sql
SELECT current_user, current_database();
```

El resultado esperado es:

```text
 current_user | current_database
--------------+------------------
 ha_user      | homeassistant_db
```

Después sal:

```text
\q
```

Si esta prueba falla, no levantes Home Assistant ni configures el Recorder. El
problema debe resolverse primero en PostgreSQL, el rol, la contraseña o el
propietario de la base.

Conserva `HA_DB_PASSWORD` solo hasta completar el secreto local de HA. No lo
copies a este documento, al repositorio ni al chat.

**Checkpoint 5 — login listo:** `ha_user` puede conectarse a
`homeassistant_db`. Solo después de este checkpoint se puede iniciar HA.

### 7. Iniciar Home Assistant y completar el onboarding

Solo ejecuta este paso después de confirmar los tres checkpoints de PostgreSQL.
Si el onboarding ya estaba completado, no lo repitas: verifica el servicio y
continúa con el paso 8.

Si es el primer inicio o el onboarding todavía no existe:

```bash
dk homeassistant
svc config homeassistant
```

Revisa localmente la configuración resuelta. No pegues su salida en el chat si
incluye variables interpoladas o secretos. Después inicia el servicio:

```bash
svc up homeassistant
svc ps homeassistant
svc logs homeassistant
```

`svc logs homeassistant` muestra los logs en seguimiento. Pulsa `Ctrl-C` para
salir de la vista de logs; no detiene ni reinicia el contenedor.

Abre desde la LAN:

```text
http://${SERVER_IP}:8123
```

Completa el onboarding de Home Assistant. No edites `data/configuration.yaml`
ni configures el Recorder antes de terminarlo.

Después del onboarding, confirma que el servicio continúa activo:

```bash
svc ps homeassistant
```

**Checkpoint 6 — onboarding listo:** HA está `Up` y la configuración inicial
existe en `$dkco/homeassistant/data/`. Solo después continúa con el Recorder.

### 8. Configurar el Recorder después del onboarding

Permanece en el directorio del servicio y crea/protege el archivo de secretos
antes de editarlo:

```bash
dk homeassistant
mkdir -p data
touch data/secrets.yaml
chmod 600 data/secrets.yaml
```

Edita el archivo:

```bash
nano data/secrets.yaml
```

Agrega esta línea, sustituyendo localmente `CONTRASEÑA_HEX` por la contraseña
que estableciste para `ha_user` y `PUERTO_HOST` por el valor real de
`HA_PG_PORT`:

```yaml
recorder_db_url: "postgresql://ha_user:CONTRASEÑA_HEX@127.0.0.1:PUERTO_HOST/homeassistant_db"
```

Con el puerto confirmado en este chat, el ejemplo concreto sería:

```yaml
recorder_db_url: "postgresql://ha_user:CONTRASEÑA_HEX@127.0.0.1:5432/homeassistant_db"
```

La contraseña hexadecimal evita caracteres reservados en la URI. Si usaste
otra contraseña con caracteres como `@`, `:`, `/`, `#` o `%`, debes codificarla
para URL antes de guardarla en `secrets.yaml`. No pegues la contraseña real en
este archivo del repositorio ni en el chat.

Confirma que la configuración principal fue creada por el onboarding:

```bash
if [[ ! -f data/configuration.yaml ]]; then
  printf 'No existe data/configuration.yaml; completa primero el onboarding de Home Assistant.\n' >&2
  exit 1
fi
```

Comprueba si ya existe una sección `recorder:`:

```bash
grep -n '^recorder:' data/configuration.yaml || true
```

Si no aparece ninguna línea, edita el archivo:

```bash
nano data/configuration.yaml
```

Agrega una sola sección:

```yaml
recorder:
  db_url: !secret recorder_db_url
  purge_keep_days: 10
  auto_purge: true
  commit_interval: 1
```

Si `grep` ya mostró una sección `recorder:`, no agregues otra. Edita el bloque
existente con:

```bash
nano data/configuration.yaml
```

E incorpora solamente esta clave dentro de la sección existente:

```yaml
db_url: !secret recorder_db_url
```

Conserva las demás opciones del Recorder. La configuración final debe contener
una sola clave de nivel superior `recorder:` y una sola `db_url` dentro de ella.

**Checkpoint 7 — Recorder configurado:** `data/secrets.yaml` existe con modo
`600`, `data/configuration.yaml` contiene una única sección `recorder:` y la URI
apunta a `127.0.0.1:$HA_PG_PORT/homeassistant_db` usando `ha_user`.

Después de guardar ambos archivos, elimina las credenciales temporales y
reinicia Home Assistant:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB HA_DB_PASSWORD HA_PG_PORT
svc restart homeassistant
svc ps homeassistant
svc logs homeassistant
```

`svc logs homeassistant` queda siguiendo los logs. Pulsa `Ctrl-C` para volver al
shell; no detiene el contenedor.

No instales paquetes dentro del contenedor inicialmente. Si los logs muestran
un error explícito del driver PostgreSQL, conserva el mensaje exacto y deténte
antes de realizar cambios adicionales.

### 9. Verificar Home Assistant y la escritura del Recorder

Después del reinicio, comprueba la interfaz y los logs:

```bash
curl -s -o /dev/null -w '%{http_code}\n' "http://${SERVER_IP}:8123"
svc ps homeassistant
svc logs homeassistant
```

Un código HTTP exitoso confirma que la interfaz responde. `svc logs` queda en
seguimiento; pulsa `Ctrl-C` para salir sin detener HA. Revisa especialmente
mensajes de `recorder`, `postgres`, `database`, `connection refused` o
`authentication failed`.

La interfaz web y el healthcheck HTTP no demuestran por sí solos que el
Recorder esté escribiendo en PostgreSQL. Espera a que Home Assistant genere
algunos estados y carga nuevamente solo las credenciales administrativas:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" ]]; then
  printf 'No se pudieron cargar las credenciales administrativas.\n' >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER
  exit 1
fi
```

Abre una sesión administrativa apuntando a `homeassistant_db`:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE=homeassistant_db \
  psql
```

Dentro de `psql` ejecuta:

```sql
SELECT COUNT(*) AS states_count FROM states;
```

Después sal:

```text
\q
```

Limpia las variables:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER
```

Un resultado `states_count` mayor que cero confirma que el Recorder está
escribiendo estados en `homeassistant_db`. Si el conteo es cero, revisa los
logs del Recorder y espera a que HA genere estados; no cambies la base ni crees
otro usuario.

**Checkpoint 8 — conexión funcional:** HA responde por HTTP, los logs no
muestran errores de conexión y `states_count > 0`.

---

### Detalles técnicos del Recorder

Home Assistant conserva `network_mode: host` para mDNS, descubrimiento IoT,
USB y Bluetooth. Por eso no pertenece a `db_net` y debe usar el puerto loopback
real de DataSQL. Los consumidores Docker sí usan `datapostgres:5432` dentro de
`db_net`.

Los Compose son independientes: no uses `depends_on` para ordenar HA respecto a
DataSQL. El orden operativo es DataSQL saludable → base/rol dedicados →
onboarding de HA → Recorder → reinicio y verificación funcional.

---

## Continuidad entre chats y checkpoints

Esta guía se ejecuta como un flujo secuencial. No repitas una mutación ya
confirmada (`CREATE ROLE`, `CREATE DATABASE`, cambio de contraseña o edición del
Recorder) solo porque cambies de chat.

El checkpoint operativo está en:

```text
_drafts/SESSION-HA-DATASQL.md
```

Cuando pauses, indica en el siguiente chat que quieres continuar la guía
`HA-DataSQL` y pega la última salida del NAS. El agente debe leer el checkpoint,
comparar la última postcondición confirmada y darte una sola acción siguiente.
Los checkpoints de esta guía son:

0. Endpoint loopback detectado y PostgreSQL escuchando.
1. DataSQL saludable y `db_net` disponible.
2. Variables administrativas cargadas.
3. Rol `ha_user` creado o verificado con `rolcanlogin = t`.
4. `homeassistant_db` creada o verificada con propietario `ha_user`.
5. Login de `ha_user` confirmado dentro de `homeassistant_db`.
6. Home Assistant levantado y onboarding completado.
7. `secrets.yaml` y una única sección `recorder:` configuradas.
8. HA reiniciado, responde por HTTP y `states_count > 0` confirmado en
   PostgreSQL.

Una pregunta lateral no cambia el checkpoint ni autoriza a saltar pasos. No
continúes al Recorder hasta completar los checkpoints de PostgreSQL y el
onboarding.

---

## Verificación y operación diaria

Después de reiniciar HA y esperar aproximadamente 30 segundos:

```bash
svc ps homeassistant
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8123
svc logs homeassistant
```

El healthcheck HTTP confirma que la interfaz responde, pero no confirma por sí
solo la conexión del Recorder. La verificación funcional de PostgreSQL está en
la sección `9. Verificar Home Assistant y la escritura del Recorder`, donde se
consulta
`states` usando `svc exec` con `PGUSER` y `PGDATABASE` para que el CLI no
interprete `-U`, `-d` o `-c` como opciones propias.

Las operaciones habituales son:

```bash
svc ps homeassistant
svc logs homeassistant
svc restart homeassistant
svc update homeassistant
svc stop homeassistant
```

El acceso LAN es `http://${SERVER_IP}:8123`; el acceso local para pruebas es
`http://127.0.0.1:8123`. Si HA reinicia en bucle y los logs no muestran el
motivo actual, deténlo con `svc stop homeassistant` y después consulta
`svc logs homeassistant` para aislar el arranque completo.

---

## Organización con includes

En vez de meter todo en `configuration.yaml` (que se vuelve enorme), usar `!include`:

### configuration.yaml (limpio)

```yaml
# Solo lo esencial + includes
homeassistant:
  name: Home
  unit_system: metric
  time_zone: America/La_Paz

# Includes organizados
shell_command: !include includes/shell_commands.yaml
rest_command: !include includes/tvoverlay_commands.yaml
notify: !include includes/notify.yaml

# Estos ya los genera HA automáticamente
automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml
```

### Crear archivos includes

Desde el NAS (la ruta `$dkco/homeassistant/data/` es `/config` dentro de HA):

```bash
# Crear carpeta
mkdir -p $dkco/homeassistant/data/includes

# Crear shell_commands.yaml
cat > $dkco/homeassistant/data/includes/shell_commands.yaml << 'EOF'
# Shell Commands — ntfy + utilidades
ntfy_camara: >
  curl -s -H "Title: 🚨 Movimiento detectado"
  -H "Priority: 4"
  -H "Tags: warning,camera"
  -H "Filename: alarma.jpg"
  -T /config/www/snapshots/alarma.jpg
  http://192.168.1.200:8090/nas-alerts
EOF

# Crear tvoverlay_commands.yaml
cat > $dkco/homeassistant/data/includes/tvoverlay_commands.yaml << 'EOF'
tvoverlay_notify:
  url: "http://192.168.0.7:5001/notify"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "id": "{{ id | default('') }}",
      "title": "{{ title | default('') }}",
      "message": "{{ message | default('') }}",
      "appTitle": "{{ appTitle | default('') }}",
      "smallIcon": "{{ smallIcon | default('mdi:bell') }}",
      "largeIcon": "{{ largeIcon | default('') }}",
      "color": "{{ color | default('#03A9F4') }}",
      "corner": "{{ corner | default('') }}",
      "duration": {{ duration | default(10) }},
      "image": "{{ image | default('') }}",
      "video": "{{ video | default('') }}"
    }

tvoverlay_notify_fixed:
  url: "http://192.168.1.50:5001/notify_fixed"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "id": "{{ id | default('') }}",
      "visible": {{ visible | default(true) | lower }},
      "icon": "{{ icon | default('') }}",
      "message": "{{ message | default('') }}",
      "messageColor": "{{ messageColor | default('#FFFFFF') }}",
      "iconColor": "{{ iconColor | default('#FFFFFF') }}",
      "borderColor": "{{ borderColor | default('#FFFFFF') }}",
      "backgroundColor": "{{ backgroundColor | default('#66000000') }}",
      "shape": "{{ shape | default('rounded') }}",
      "expiration": "{{ expiration | default('') }}"
    }

tvoverlay_set_overlay:
  url: "http://192.168.1.50:5001/set/overlay"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "overlayVisibility": {{ overlayVisibility | default(0) }},
      "clockOverlayVisibility": {{ clockOverlayVisibility | default(0) }},
      "hotCorner": "{{ hotCorner | default('') }}"
    }

tvoverlay_set_notifications:
  url: "http://192.168.1.50:5001/set/notifications"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "displayNotifications": {{ displayNotifications | default(true) | lower }},
      "displayFixedNotifications": {{ displayFixedNotifications | default(true) | lower }},
      "notificationLayoutName": "{{ notificationLayoutName | default('Default') }}",
      "notificationDuration": {{ notificationDuration | default(7) }},
      "fixedNotificationsVisibility": {{ fixedNotificationsVisibility | default(-1) }}
    }

tvoverlay_set_settings:
  url: "http://192.168.1.50:5001/set/settings"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "deviceName": "{{ deviceName | default('') }}",
      "remotePort": "{{ remotePort | default('') }}",
      "displayDebug": {{ displayDebug | default(false) | lower }},
      "pixelShift": {{ pixelShift | default(false) | lower }}
    }

tvoverlay_set_mqtt:
  url: "http://192.168.1.50:5001/set/mqtt"
  method: POST
  headers:
    Content-Type: "application/json"
  payload: >-
    {
      "displayMqttStatusChange": {{ displayMqttStatusChange | default(false) | lower }},
      "mqttConfig": {
        "broker": "{{ broker }}",
        "port": {{ port | default(1883) }},
        "user": "{{ user | default('') }}",
        "password": "{{ password | default('') }}"
      }
    }

tvoverlay_get_status:
  url: "http://192.168.1.50:5001/get"
  method: GET

tvoverlay_restart:
  url: "http://192.168.1.50:5001/set/restart_service"
  method: POST
EOF

# Crear notify.yaml
cat > $dkco/homeassistant/data/includes/notify.yaml << 'EOF'
- name: tvoverlay_sala
  platform: rest
  method: POST_JSON
  resource: http://192.168.1.50:5001/notify
  verify_ssl: false
  title_param_name: title
  data:
    id: "{{ data.id | default('') }}"
    appTitle: "{{ data.appTitle | default('') }}"
    color: "{{ data.color | default('#03A9F4') }}"
    image: "{{ data.image | default(null) }}"
    video: "{{ data.video | default(null) }}"
    smallIcon: "{{ data.smallIcon | default('mdi:home-assistant') }}"
    largeIcon: "{{ data.largeIcon | default(null) }}"
    corner: "{{ data.corner | default(null) }}"
    duration: "{{ data.duration | default(7) }}"
EOF

# Crear carpeta de snapshots
mkdir -p $dkco/homeassistant/data/www/snapshots
```

### Agregar includes a configuration.yaml

```bash
# Agregar al final de configuration.yaml (si no están ya)
cat >> $dkco/homeassistant/data/configuration.yaml << 'EOF'

# ================================================================
# Includes organizados (ver carpeta includes/)
# ================================================================
shell_command: !include includes/shell_commands.yaml
rest_command: !include includes/tvoverlay_commands.yaml
notify: !include includes/notify.yaml
EOF
```

> ⚠️ **IMPORTANTE:** Si ya tienes `shell_command:`, `rest_command:` o `notify:` 
> definidos directamente en `configuration.yaml`, **borrar esas secciones** antes
> de agregar los includes. No pueden coexistir ambos.

### Aplicar cambios

```bash
# Reiniciar HA para que cargue los includes
svc restart homeassistant

# O desde HA: Herramientas para desarrolladores → YAML → Recargar todo
```

---

## Integración con ntfy

### Paso 1: Instalar integración oficial ntfy en HA

1. **Settings → Devices & Services → Add Integration → ntfy**
2. Service URL: `http://192.168.1.200:8090`
3. Sin autenticación (dejar vacío — auth abierto en LAN)
4. Verify SSL: desactivar
5. Add Topic → escribir: `nas-alerts`

Esto crea la entidad `notify.nas_alerts` para notificaciones de texto.

### Paso 2: Notificaciones con imagen (shell_command)

La integración oficial de ntfy en HA **aún no soporta adjuntar imágenes** (feature
request pendiente). Para enviar imágenes se usa `shell_command` + `curl -T`:

El archivo `includes/shell_commands.yaml` ya contiene `ntfy_camara` que hace esto.

### Probar desde terminal del NAS

```bash
# 1. Capturar snapshot via API de HA (requiere Long-Lived Access Token)
curl -s -o /tmp/camara-test.jpg \
  -H "Authorization: Bearer TU_TOKEN_HA_LARGO" \
  "http://192.168.1.200:8123/api/camera_proxy/camera.camara_profile_000"

# 2. Enviar a ntfy
curl -H "Title: 🧪 Test cámara" \
     -H "Priority: 4" \
     -H "Tags: camera" \
     -H "Filename: camara-test.jpg" \
     -T /tmp/camara-test.jpg \
     http://192.168.1.200:8090/nas-alerts

# 3. Limpiar
rm /tmp/camara-test.jpg
```

### Probar desde HA (Herramientas para desarrolladores → Acciones)

**Primero** capturar snapshot:
```yaml
action: camera.snapshot
target:
  entity_id: camera.camara_profile_000
data:
  filename: "/config/www/snapshots/alarma.jpg"
```

**Después** enviar (esperar 2 segundos):
```yaml
action: shell_command.ntfy_camara
```

---

## Automatización: Cámara → snapshot → ntfy

### Automatización completa (crear en Settings → Automations)

```yaml
alias: "Movimiento cámara → ntfy con imagen"
description: "Captura snapshot y envía push al celular al detectar movimiento"
mode: single
trigger:
  - platform: state
    entity_id: binary_sensor.camara_cell_motion_detection
    to: "on"
    for:
      seconds: 5
action:
  - action: camera.snapshot
    target:
      entity_id: camera.camara_profile_000
    data:
      filename: "/config/www/snapshots/alarma.jpg"
  - delay:
      seconds: 2
  - action: shell_command.ntfy_camara
```

### Cómo funciona

```
Cámara detecta movimiento (5s filtro)
    │
    ├─→ camera.snapshot → guarda /config/www/snapshots/alarma.jpg
    │
    ├─→ delay 2s (esperar escritura)
    │
    └─→ shell_command.ntfy_camara → curl envía imagen a ntfy → celular
```

### Notificación sin imagen (solo texto, más simple)

```yaml
alias: "Movimiento cámara → ntfy texto"
trigger:
  - platform: state
    entity_id: binary_sensor.camara_cell_motion_detection
    to: "on"
    for:
      seconds: 5
action:
  - action: ntfy.publish
    target:
      entity_id: notify.nas_alerts
    data:
      title: "🚨 Movimiento detectado"
      message: "Cámara detectó movimiento"
      priority: 4
      tags: "warning,camera"
```

> **Nota:** `priority` en `ntfy.publish` de HA usa **números**: 1=min, 2=low, 3=default, 4=high, 5=urgent.
> En curl/bash se usa texto ("high"), pero en HA se usa número.

---

## TvOverlay

TvOverlay envía notificaciones overlay a una Android TV/Fire TV.

### Entidades disponibles

| Acción | Uso |
|--------|-----|
| `rest_command.tvoverlay_notify` | Notificación emergente (texto, imagen, video) |
| `rest_command.tvoverlay_notify_fixed` | Icono fijo en esquina |
| `rest_command.tvoverlay_set_overlay` | Fondo oscuro, reloj |
| `rest_command.tvoverlay_set_notifications` | Config general |
| `rest_command.tvoverlay_set_mqtt` | Configurar MQTT remoto |
| `rest_command.tvoverlay_restart` | Reiniciar servicio |
| `notify.tvoverlay_sala` | Notificación rápida (sintaxis corta) |

### Ejemplo: enviar a TV cuando la cámara detecta

```yaml
action:
  - action: rest_command.tvoverlay_notify
    data:
      title: "🚨 Movimiento"
      message: "Cámara detectó movimiento"
      smallIcon: "mdi:cctv"
      color: "#FF0000"
      duration: 15
```

### IPs de dispositivos TvOverlay

| Dispositivo | IP | Puerto |
|-------------|-----|--------|
| TV principal | 192.168.0.7 | 5001 |
| TV secundaria | 192.168.1.50 | 5001 |

---

## Troubleshooting

### DataSQL no arranca con `Address already in use`

Si el error completo es `failed to set up container networking: Address already
in use`, no cambies primero el puerto de pgAdmin o PostgreSQL: en este entorno
la causa fue una IP estática (`ipv4_address`) ocupada en la red compartida
`db_net`. `svc restart datasql` tampoco recrea esa red ni cambia las IPs.

Mantener `db_net`, retirar las IPs estáticas del Compose y aplicar la versión
canónica de DataSQL con asignación dinámica. El procedimiento completo de
instalación, diagnóstico y migración está en
[`docs/services/datasql-guide.md`](datasql-guide.md) y en el
[troubleshooting general](../troubleshooting.md). Después de corregir DataSQL,
seguir este orden:

```bash
svc config datasql
svc down datasql
svc up datasql
svc ps datasql
# continuar solo cuando datapostgres y dataredis estén healthy
svc up homeassistant
svc ps homeassistant
```

No ejecutar `docker network prune` ni cambiar el Recorder a un PostgreSQL
expuesto en la LAN. HA debe conservar `network_mode: host` y usar
`127.0.0.1:5432`.

### `svc snapshot` no existe en el CLI Python

Si `svc snapshot datasql` muestra `No such command 'snapshot'`, usar mientras
se actualiza el NAS:

```bash
NAS_CLI=bash svc snapshot datasql
```

Después de actualizar el checkout con `nasfk` + `gpl`, Python registra
`snapshot` pero delega al mismo Bash. Para rollback, el fallback explícito es:

```bash
NAS_CLI=bash svc rollback datasql
```

### `connection refused` del Recorder con `localhost`

Si PostgreSQL está escuchando en `127.0.0.1:5432` pero el Recorder falla con
`localhost`, cambiar el `db_url` a `127.0.0.1`. En este entorno el cliente puede
intentar IPv6 primero; `localhost` no es equivalente a la publicación loopback
IPv4 usada por DataSQL.

### `psql` pide contraseña o `source .env` rompe la shell

No ejecutar `source $dkco/datasql/.env`: los secretos pueden contener caracteres
especiales. Tampoco usar el ejemplo `admin/appdb` de la guía compartida. Leer las
variables necesarias con `grep` y pasarlas como `env PGPASSWORD=...` dentro de
`svc exec datasql postgres`, siguiendo la receta de DataSQL.

### Aviso de reverse proxy

Un mensaje como `A request from a reverse proxy was received` puede aparecer si
un proxy de la red llega directamente a HA. No impide el funcionamiento inicial;
si se va a usar proxy, declarar después sus rangos autorizados en
`trusted_proxies` y validar la configuración antes de reiniciar.

### Home Assistant reinicia en bucle y no aparecen logs nuevos

Aislar el arranque con los comandos del NAS, sin usar Docker directamente:

```bash
svc stop homeassistant
svc logs homeassistant
```

Revisar primero `configuration.yaml`, la URL del Recorder, la disponibilidad de
DataSQL y los permisos del bind `./data:/config`.

### `curl: cannot open '/config/www/snapshots/alarma.jpg'`

La carpeta no existe. Crear desde el NAS:
```bash
mkdir -p $dkco/homeassistant/data/www/snapshots
```

### `Cannot write /tmp/alarma.jpg, allowlist_external_dirs`

HA no tiene permiso para escribir en `/tmp/`. Usar `/config/www/snapshots/` en vez de `/tmp/`.

### `extra keys not allowed @ data['image']` en ntfy.publish

La integración oficial de ntfy en HA **no soporta imágenes adjuntas** (aún).
Usar `shell_command` + `curl -T` para enviar imágenes.

### `extra keys not allowed @ data['priority']` / `expected int`

`priority` en `ntfy.publish` debe ser **número** (no texto):
- 1=min, 2=low, 3=default, 4=high, 5=urgent

### Shell commands no aparecen después de crear el archivo

Recargar: **Herramientas para desarrolladores → YAML → Recargar Shell Commands**
O reiniciar HA: `svc restart homeassistant`

### `!include` da error de duplicado

No pueden coexistir `shell_command:` definido directamente en `configuration.yaml`
Y también como `!include`. Borrar la definición directa y dejar solo el include.

### Snapshot se ejecuta pero shell_command falla

El snapshot tarda en escribirse. Asegurar `delay: { seconds: 2 }` entre ambas acciones.

---

## Entidades clave de este setup

| Entidad | Tipo | Uso |
|---------|------|-----|
| `camera.camara_profile_000` | Cámara | Snapshot, stream |
| `binary_sensor.camara_cell_motion_detection` | Sensor | Trigger de movimiento |
| `notify.nas_alerts` | Notificación | ntfy (solo texto) |
| `shell_command.ntfy_camara` | Shell | ntfy con imagen |
| `rest_command.tvoverlay_notify` | REST | Overlay en TV |
| `notify.tvoverlay_sala` | Notificación | TV (sintaxis corta) |
