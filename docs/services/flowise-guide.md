# Guía: Flowise con PostgreSQL, Redis y workers en modo queue

## Estado: válida para el NAS — una instancia main y un worker
## Fecha: 2026-08-21
## Resumen

Esta guía instala Flowise como un compose independiente en `$dkco/flowise/`, usando
la infraestructura existente de DataSQL (`datapostgres`, `dataredis` y `db_net`).
El servidor web/API recibe las peticiones y Redis distribuye las ejecuciones al
worker. PostgreSQL no se expone a la LAN: el binding `127.0.0.1:5432` existe
únicamente para Home Assistant en `network_mode: host`; Redis no publica `6379`.
La persistencia de Flowise queda en un bind mount respaldable.

> **Alcance real:** esta configuración deja un main y un worker funcionando en el
> mismo NAS. Flowise soporta varios workers en queue mode, pero el wrapper `svc`
> de este repositorio todavía no implementa `svc scale`; por eso esta guía no
> promete un comando de escalado que no existe. El `container_name` fijo del worker
> también debe resolverse antes de habilitar réplicas.

---

## 1. Arquitectura final

```text
                                LAN
                                 │
                   http://${SERVER_IP}:8100
                                 │
                       flowise :3000 (main)
                         │              │
                         │              └── $dkco/flowise/data
                         │
                 db_net (red externa existente)
                    │                         │
        datapostgres:5432              dataredis:6379
        flowise_db                    flowise-queue
                    │                         │
                    └──────── flowise-worker
                               :5566 healthz
                               $dkco/flowise/data
```

### Decisiones finales

- **Base de datos:** PostgreSQL dedicado `flowise_db` dentro de DataSQL.
- **Cola:** Redis de DataSQL, con `QUEUE_NAME=flowise-queue`.
- **Procesamiento:** `MODE=queue` en main y worker; el proceso worker se inicia
  con `entrypoint: /bin/sh -c "sleep 3; flowise worker"`, variante reportada como
  funcional en el NAS.
- **Persistencia:** `$dkco/flowise/data` montado en `/home/node/.flowise` en ambos
  contenedores. Se usa bind mount para que el backup pueda localizar los datos.
- **Acceso:** `8100:3000` en la LAN durante esta fase.
- **Seguridad:** secretos locales con permisos `600`, JWT propios, clave de
  cifrado persistente, `no-new-privileges` heredado y `cap_drop: [ALL]`.
- **Fuera de esta guía:** PostgreSQL/Redis propios, Nginx, Certbot, dominio
  público, TLS y réplicas del main.

La documentación oficial de Flowise recomienda PostgreSQL cuando se trabaja a
escala y describe queue mode con Redis, main y workers separados:

- [Queue mode de Flowise](https://docs.flowiseai.com/configuration/running-flowise-using-queue)
- [Ejecución en producción](https://docs.flowiseai.com/configuration/running-in-production)
- [Bases de datos](https://docs.flowiseai.com/configuration/databases)
- [Autorización de aplicación](https://docs.flowiseai.com/configuration/authorization/app-level)

Contenido externo consultado y reescrito de forma resumida para esta guía; no se
copian bloques extensos de las fuentes originales.

---

## 2. Requisitos y comprobaciones previas

Antes de crear archivos:

1. DataSQL debe estar instalado y saludable.
2. La red externa `db_net` debe existir.
3. `$dkco/.env` debe contener `SERVER_IP` y `TZ`.
4. `$dkco/_common.yml` debe existir en el NAS.
5. El puerto `8100` debe estar libre.
6. El valor de `REDIS_PASSWORD` de Flowise debe ser exactamente el mismo que usa
   DataSQL.

Comprobar DataSQL y confirmar la excepción loopback de PostgreSQL:

```bash
svc health
svc ps datasql
svc port datasql 5432
```

`svc port datasql 5432` debe mostrar únicamente el binding `127.0.0.1:5432`;
no debe mostrar una publicación en `0.0.0.0` ni `[::]`. La conectividad de
Flowise será interna por `db_net`. El healthcheck del compose de DataSQL valida
Redis con su propia contraseña; no se debe crear un segundo Redis.

---

## 3. Paso 1 — Crear directorios

### Artefactos

- Tipo: directorio
- Identificador: `$dkco/flowise/data`
- Estado inicial: puede no existir
- Estado esperado: existe antes de crear o levantar el compose

Crear primero la carpeta persistente:

```bash
mkdir -p $dkco/flowise/data
```

No ejecutar todavía `chown`, `chmod` ni `svc up`: esos pasos dependen de que la
carpeta exista y de que el archivo `.env` haya sido creado.

---

## 4. Paso 2 — Preparar la integración con DataSQL

Flowise usará la base dedicada `flowise_db`, el rol `flowise_user`,
`datapostgres`, `dataredis` y `db_net`. No se crea otro PostgreSQL ni otro
Redis. La base y el rol se crean **después** de guardar el password de Flowise
en su `.env`, usando la receta canónica de la Fase 5A de
`docs/services/datasql-guide.md`. La instalación y recuperación del stack están en
`docs/services/aipostgres-guide.md`.

No asumir `admin/appdb`, no ejecutar `source $dkco/datasql/.env` y no combinar
`CREATE ROLE`/`CREATE USER` con `CREATE DATABASE`.

---

## 5. Paso 3 — Crear el `.env` local

### Artefactos

- Tipo: archivo de secretos
- Identificador: `$dkco/flowise/.env`
- Estado inicial: no existe
- Estado esperado: contiene los valores reales y después tendrá permisos `600`

Crear el archivo después de haber creado `$dkco/flowise/data`:

```bash
touch $dkco/flowise/.env
```

Editar `$dkco/flowise/.env` y colocar este contenido, sustituyendo todos los
marcadores `__pega_aqui__`:

```env
# DataSQL: no crear otro PostgreSQL ni otro Redis
FLOWISE_DB_NAME=flowise_db
FLOWISE_DB_USER=flowise_user
FLOWISE_DB_PASSWORD=__pega_aqui__
REDIS_PASSWORD=__pega_aqui__

# Compatibilidad con el acceso inicial legacy de Flowise.
# Desde Flowise 3.0.1 la autenticación email/password es el mecanismo preferido.
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=__pega_aqui__

# Debe permanecer estable para descifrar credenciales existentes.
FLOWISE_SECRETKEY_OVERWRITE=__pega_aqui__

# Secretos de JWT y sesión. Usar valores diferentes entre sí.
JWT_AUTH_TOKEN_SECRET=__pega_aqui__
JWT_REFRESH_TOKEN_SECRET=__pega_aqui__
JWT_ISSUER=flowise
JWT_AUDIENCE=flowise
JWT_TOKEN_EXPIRY_IN_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES=129600
EXPRESS_SESSION_SECRET=__pega_aqui__
TOKEN_HASH_SECRET=__pega_aqui__

TRUST_PROXY=false
SECURE_COOKIES=false
NUMBER_OF_PROXIES=0
```

`FLOWISE_DB_PASSWORD` será la contraseña del rol PostgreSQL. `REDIS_PASSWORD`
debe copiarse exactamente del secreto de DataSQL; no se genera otra contraseña
para Redis. `SERVER_IP` y `TZ` vienen del `$dkco/.env` global mediante
`env_file`; no se duplican en este archivo.

Aplicar permisos solamente después de crear y editar el archivo:

```bash
chmod 600 $dkco/flowise/.env
```

---

## 6. Paso 4 — Crear el rol y la base dedicados

Con `$dkco/flowise/.env` ya creado, ejecutar la receta de `docs/services/datasql-guide.md` con estos valores:

```text
APP_DB_USER=flowise_user
APP_DB_NAME=flowise_db
APP_DB_PASSWORD=FLOWISE_DB_PASSWORD del .env de Flowise
```

La receta lee `POSTGRES_USER`, `POSTGRES_DB` y `POSTGRES_PASSWORD` desde
`$dkco/datasql/.env`, usa `svc exec` con `PGPASSWORD`, crea el rol primero y la
base después. Verifica también el propietario y prueba la conexión como
`flowise_user`. No pegar contraseñas en el chat ni en GitHub.

---

## 7. Paso 5 — Crear el compose final

### Artefactos

- Tipo: archivo de configuración
- Identificador: `$dkco/flowise/compose.yml`
- Estado inicial: no existe o contiene la variante anterior
- Estado esperado: main + worker, sin bases de datos propias

En el NAS, crear `$dkco/flowise/compose.yml` con el contenido completo siguiente.
La única diferencia respecto al compose del catálogo es la ruta de `extends`:
en el NAS es `../_common.yml`; en `agent/catalog/services/flowise/compose.yml`
es `../../_common.yml`.

```yaml
# Flowise — main + worker en modo queue
services:
  flowise:
    extends:
      file: ../_common.yml
      service: _defaults
    image: flowiseai/flowise:latest
    container_name: flowise
    env_file:
      - ../.env
      - .env
    environment:
      PORT: "3000"
      MODE: queue
      QUEUE_NAME: flowise-queue
      QUEUE_REDIS_EVENT_STREAM_MAX_LEN: "1000"
      DATABASE_TYPE: postgres
      DATABASE_PORT: "5432"
      DATABASE_HOST: datapostgres
      DATABASE_NAME: ${FLOWISE_DB_NAME}
      DATABASE_USER: ${FLOWISE_DB_USER}
      DATABASE_PASSWORD: ${FLOWISE_DB_PASSWORD}
      DATABASE_SSL: "false"
      REDIS_HOST: dataredis
      REDIS_PORT: "6379"
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      SECRETKEY_PATH: /home/node/.flowise
      LOG_PATH: /home/node/.flowise/logs
      BLOB_STORAGE_PATH: /home/node/.flowise/storage
      LOG_LEVEL: info
      DISABLE_FLOWISE_TELEMETRY: "true"
      HTTP_SECURITY_CHECK: "true"
      PATH_TRAVERSAL_SAFETY: "true"
      OAUTH2_SECURITY_CHECK: "true"
      CUSTOM_MCP_SECURITY_CHECK: "true"
      FLOWISE_USERNAME: ${FLOWISE_USERNAME}
      FLOWISE_PASSWORD: ${FLOWISE_PASSWORD}
      APP_URL: http://${SERVER_IP}:8100
      JWT_AUTH_TOKEN_SECRET: ${JWT_AUTH_TOKEN_SECRET}
      JWT_REFRESH_TOKEN_SECRET: ${JWT_REFRESH_TOKEN_SECRET}
      JWT_ISSUER: ${JWT_ISSUER}
      JWT_AUDIENCE: ${JWT_AUDIENCE}
      JWT_TOKEN_EXPIRY_IN_MINUTES: ${JWT_TOKEN_EXPIRY_IN_MINUTES}
      JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES: ${JWT_REFRESH_TOKEN_EXPIRY_IN_MINUTES}
      EXPRESS_SESSION_SECRET: ${EXPRESS_SESSION_SECRET}
      TOKEN_HASH_SECRET: ${TOKEN_HASH_SECRET}
      FLOWISE_SECRETKEY_OVERWRITE: ${FLOWISE_SECRETKEY_OVERWRITE}
    ports:
      - "8100:3000"
    volumes:
      - type: bind
        source: ./data
        target: /home/node/.flowise
        read_only: false
    networks:
      - db_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/ping"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 45s
    cap_drop: [ALL]
    labels:
      - homepage.group=IA y Automatización
      - homepage.name=Flowise
      - homepage.icon=flowise
      - homepage.href=http://${SERVER_IP}:8100
      - homepage.description=Constructor visual de agentes y flujos LLM
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    entrypoint: /bin/sh -c "sleep 3; flowise start"

  flowise-worker:
    extends:
      file: ../_common.yml
      service: _defaults
    image: flowiseai/flowise:latest
    container_name: flowise-worker
    env_file:
      - ../.env
      - .env
    environment:
      # Ajuste validado en el NAS para evitar OOM durante el procesamiento de jobs.
      NODE_OPTIONS: "--max-old-space-size=768"
      # Main y worker comparten MODE, cola, DB, Redis y clave de cifrado.
      PORT: "3000"
      WORKER_PORT: "5566"
      MODE: queue
      QUEUE_NAME: flowise-queue
      WORKER_CONCURRENCY: "5"
      QUEUE_REDIS_EVENT_STREAM_MAX_LEN: "1000"
      DATABASE_TYPE: postgres
      DATABASE_PORT: "5432"
      DATABASE_HOST: datapostgres
      DATABASE_NAME: ${FLOWISE_DB_NAME}
      DATABASE_USER: ${FLOWISE_DB_USER}
      DATABASE_PASSWORD: ${FLOWISE_DB_PASSWORD}
      DATABASE_SSL: "false"
      REDIS_HOST: dataredis
      REDIS_PORT: "6379"
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      SECRETKEY_PATH: /home/node/.flowise
      LOG_PATH: /home/node/.flowise/logs
      BLOB_STORAGE_PATH: /home/node/.flowise/storage
      LOG_LEVEL: info
      DISABLE_FLOWISE_TELEMETRY: "true"
      HTTP_SECURITY_CHECK: "true"
      PATH_TRAVERSAL_SAFETY: "true"
      CUSTOM_MCP_SECURITY_CHECK: "true"
      FLOWISE_SECRETKEY_OVERWRITE: ${FLOWISE_SECRETKEY_OVERWRITE}
    volumes:
      - type: bind
        source: ./data
        target: /home/node/.flowise
        read_only: false
    networks:
      - db_net
    depends_on:
      flowise:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5566/healthz"]
      interval: 15s
      timeout: 5s
      retries: 5
      start_period: 30s
    cap_drop: [ALL]
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    entrypoint: /bin/sh -c "sleep 3; flowise worker"

networks:
  db_net:
    external: true
```

### Motivos de las decisiones del compose

- `MODE=queue` se conserva tanto en main como en worker porque la documentación
  oficial indica compartir la configuración. En el NAS, el worker operativo usa
  `entrypoint: /bin/sh -c "sleep 3; flowise worker"`, que deja unos segundos para
  que el main saludable complete su inicialización antes de procesar trabajos.
- `NODE_OPTIONS=--max-old-space-size=768` y los límites de `1G`/`256M` del worker
  son ajustes operativos reportados como funcionales en el NAS para evitar los
  reinicios por memoria observados durante el procesamiento.
- `REDIS_HOST`, `REDIS_PORT` y `REDIS_PASSWORD` son variables documentadas por
  Flowise. No se usa `REDIS_USE_ICOMPRESSION`, porque los drafts no demostraban
  que fuese una variable válida para la versión instalada.
- `WORKER_CONCURRENCY=5` es un punto de partida conservador tomado de la
  configuración de queue documentada oficialmente; no es una medición del NAS.
- El worker usa el mismo bind mount para que vea la clave de cifrado, logs y
  almacenamiento local. Esta configuración escala únicamente dentro del mismo
  host; no es un almacenamiento distribuido.
- `depends_on` solo relaciona al worker con el main del mismo compose y conserva
  `condition: service_healthy`. No se declara dependencia contra DataSQL, porque
  DataSQL vive en otro compose.
- El puerto `5566` solo se usa dentro del contenedor para el healthcheck del
  worker; no se publica al host.
- No se añadió `rshared`: Flowise no consume montajes anidados como File Browser.

---

## 7. Paso 5 — Validar y levantar

### Verificación de sintaxis y configuración

Desde la carpeta del servicio:

```bash
dk flowise
svc config flowise
```

`svc config` debe resolver las variables y mostrar un compose válido. Si aparecen
variables vacías, detenerse y completar `$dkco/flowise/.env`; no levantar el
servicio con secretos faltantes.

### Levantar

```bash
svc up flowise
```

### Verificar en orden

```bash
svc ps flowise
svc logs flowise
svc health
svc stats flowise
```

Estados esperados:

- `flowise` alcanza `healthy` mediante
  `http://localhost:3000/api/v1/ping`.
- `flowise-worker` alcanza `healthy` mediante
  `http://localhost:5566/healthz`.
- La aplicación responde en `http://${SERVER_IP}:8100`.
- PostgreSQL no está expuesto a la LAN; el binding `127.0.0.1:5432` existe únicamente para Home Assistant en `network_mode: host`. Redis no publica `6379` en el host.

No considerar suficiente que los contenedores estén `running`: el estado
`healthy`, los logs y la conexión real con PostgreSQL/Redis forman parte de la
verificación.

---

## 8. Persistencia, permisos y recuperación

La estructura final es:

```text
$dkco/flowise/
├── compose.yml
├── .env                    # permisos 600
└── data/                   # /home/node/.flowise en main y worker
    ├── logs/
    └── storage/
```

Si Flowise informa `permission denied`, crear primero la carpeta (ya se hace en
el paso 3) y después aplicar el propietario de la imagen:

```bash
chown -R 1000:1000 $dkco/flowise/data
```

Después de cambiar permisos, recrear los contenedores:

```bash
svc recreate flowise
svc ps flowise
```

### Backup

El backup tiene dos artefactos distintos y ambos son necesarios:

1. Datos locales de Flowise:

   ```bash
   svc backup flowise
   ```

2. Dump de la base `flowise_db`, usando el procedimiento de backup de DataSQL y
   conservándolo en `$dkco/datasql/data/postgres/backups/`.

No tratar `svc backup flowise` como sustituto del dump PostgreSQL. Antes de una
actualización o una operación destructiva, comprobar que existen ambos backups.

### Recuperación

Orden de recuperación:

1. Detener Flowise:

   ```bash
   svc down flowise
   ```

2. Restaurar `flowise_db` mediante el procedimiento de DataSQL.
3. Restaurar el contenido de `$dkco/flowise/data`.
4. Comprobar que `.env` conserva exactamente `FLOWISE_SECRETKEY_OVERWRITE`.
5. Levantar:

   ```bash
   svc up flowise
   ```

6. Verificar salud y logs:

   ```bash
   svc ps flowise
   svc logs flowise
   ```

La restauración debe probarse primero en una base temporal; no reemplazar la base
real sin comprobar que el dump puede restaurarse.

---

## 9. Operación habitual

```bash
svc restart flowise
svc logs flowise
svc update flowise
svc backup flowise
svc recreate flowise
svc catalog-sync flowise
```

Después de cambiar labels, recrear el servicio para que Homepage vuelva a leerlos:

```bash
svc recreate flowise
```

No usar `docker compose`, `docker restart` ni `docker exec` directamente en las
operaciones documentadas para este NAS; los wrappers del proyecto son la interfaz
operativa válida.

### Escalado futuro

La documentación oficial de Flowise permite uno o más workers, pero este repo no
contiene todavía `svc scale` y el compose usa `container_name: flowise-worker`.
Por tanto, no ejecutar `svc scale flowise-worker s=3`: ese comando no existe.
Antes de habilitar réplicas se deben completar, como tarea separada:

1. eliminar o parametrizar el `container_name` fijo del worker;
2. implementar soporte de escalado en el wrapper `svc`;
3. definir cómo se nombran los workers y cómo se muestran en Homepage;
4. probar que el bind mount local y Redis soportan la carga;
5. medir CPU, memoria y `WORKER_CONCURRENCY` con `svc stats flowise`.

---

## 10. Diagnóstico

| Síntoma | Revisión y acción |
|---|---|
| `flowise` reinicia | `svc logs flowise`; revisar primero DB, Redis y variables requeridas |
| `flowise-worker` queda `unhealthy` | `svc logs flowise`; confirmar `entrypoint: /bin/sh -c "sleep 3; flowise worker"`, `NODE_OPTIONS=--max-old-space-size=768`, `WORKER_PORT=5566` y `/healthz` |
| Error de PostgreSQL | `svc health`, `svc ps datasql`, red `db_net`, host `datapostgres`, base y usuario |
| Error de Redis | confirmar que `REDIS_PASSWORD` local coincide con DataSQL y que el host es `dataredis` |
| Worker no procesa trabajos | comprobar que main y worker usan `MODE=queue`, `QUEUE_NAME` y `FLOWISE_SECRETKEY_OVERWRITE` iguales |
| `permission denied` en `/home/node/.flowise` | crear `$dkco/flowise/data`, aplicar `chown -R 1000:1000` y ejecutar `svc recreate flowise` |
| Se pierden credenciales | restaurar la clave exacta `FLOWISE_SECRETKEY_OVERWRITE` y el bind mount `data` |
| Reinicios por memoria | revisar `svc stats flowise`; no elevar concurrencia sin mediciones |
| No aparece en Homepage | verificar labels y ejecutar `svc recreate flowise` |
| Cookies no funcionan detrás de HTTPS | revisar `SECURE_COOKIES`, `TRUST_PROXY`, `NUMBER_OF_PROXIES`, `APP_URL` y el proxy |
| Se quiere publicar en Internet | detener la exposición directa; esta guía no incluye reverse proxy ni TLS |

---

## 11. Hechos, inferencias y decisiones

### Hechos confirmados

1. Flowise soporta PostgreSQL y Redis; su documentación recomienda PostgreSQL
   para despliegues a escala.
2. Queue mode usa un servidor main que publica trabajos y uno o más workers que
   los procesan mediante Redis.
3. Las variables oficiales de queue incluyen `MODE`, `QUEUE_NAME`,
   `WORKER_CONCURRENCY`, `REDIS_HOST`, `REDIS_PORT` y `REDIS_PASSWORD`.
4. La documentación oficial muestra `pnpm run start-worker` para iniciar el
   worker y `http://localhost:5566/healthz` para comprobarlo; el runtime del NAS
   reportó como funcional la variante `sleep 3; flowise worker`, que es la que
   queda en el compose canónico.
5. DataSQL del NAS ya define `datapostgres`, `dataredis` y la red externa `db_net`.
6. El compose de Flowise no publica PostgreSQL ni Redis a la LAN; el binding
   `127.0.0.1:5432` del compose de DataSQL existe únicamente para Home Assistant
   con `network_mode: host`.
7. El entorno del NAS exige `compose.yml`, `env_file: [../.env, .env]`, labels de
   Homepage en el compose y operaciones mediante `svc`.
8. El repositorio no contiene una implementación de `svc scale`.

### Inferencias seguras

1. Unir Flowise a `db_net` permite resolver `datapostgres` y `dataredis` desde el
   compose de Flowise sin recrear esos contenedores.
2. Main y worker deben compartir `FLOWISE_SECRETKEY_OVERWRITE` porque ambos
   participan en el mismo despliegue y la clave protege credenciales cifradas.
3. El bind mount debe existir antes de levantar el servicio para evitar que Docker
   lo cree con propietario inesperado.

### Inferencias no confirmadas

1. `QUEUE_NAME=flowise-queue` probablemente evita colisiones lógicas entre colas,
   pero los drafts no demostraban cómo inspecciona las claves la versión exacta
   instalada; se conserva un nombre dedicado y se deja la validación operacional
   en los logs y pruebas del servicio.
2. `WORKER_CONCURRENCY=5` es un punto inicial conservador, no un valor óptimo para
   este NAS; debe medirse.
3. `cap_drop: [ALL]` debería funcionar con la imagen actual, pero si Flowise falla
   por una capability concreta, se debe registrar la evidencia antes de ajustar
   el hardening.

---

## 12. Auditoría de fuentes y variantes

La siguiente matriz conserva las ideas relevantes de los siete drafts después de
compararlas con la configuración del NAS y la documentación oficial. `INTEGRADO`
significa que la decisión aparece en esta guía y en el compose del catálogo.

| Fuente | Idea/configuración relevante | Tipo | Confianza | Decisión final | Clasificación |
|---|---|---|---|---|---|
| `cla1.md` | PostgreSQL dedicado `flowise_db` en DataSQL | Hecho de fuente | Alta | Se adopta `datapostgres` + DB dedicada | INTEGRADO |
| `cla1.md` | Redis compartido `dataredis` y `MODE=queue` | Hecho de fuente, confirmado por docs oficiales | Alta | Se adopta con variables oficiales | INTEGRADO |
| `cla1.md` | Main + worker y storage compartido | Hecho de fuente, compatible con docs | Alta | Se adopta con `/home/node/.flowise` | INTEGRADO |
| `cla1.md` | `127.0.0.1:3000` | Hecho de fuente | Alta | Se sustituye por `8100:3000` LAN documentado | REEMPLAZADO |
| `cla1.md` | `depends_on: datapostgres` | Hecho de fuente | Alta | No válido entre composes separados | RECHAZADO |
| `cla1.md` + reporte runtime NAS | `flowise worker` y `MODE=queue` en el worker | Hecho de fuente y reporte runtime NAS | Alta | Se conserva `MODE=queue` y el runtime usa `entrypoint` con `sleep 3; flowise worker` | INTEGRADO |
| `cla1.md` | `svc scale flowise-worker s=3` | Hecho de fuente | Alta | `svc` no implementa ese comando | RECHAZADO |
| `cla1.md` | `/root/.flowise` | Hecho de fuente | Alta | No coincide con imagen/configuración canónica del NAS | RECHAZADO |
| `cla1.md` | `FLOWISE_USERNAME/PASSWORD` y clave persistente | Hecho de fuente | Media | Se integra como compatibilidad legacy y secreto estable | INTEGRADO |
| `cla2.md` | `QUEUE_NAME` funciona como prefijo aislante de Redis | Inferencia no confirmada | Baja | Se usa nombre dedicado, pero no se afirma aislamiento probado | PENDIENTE |
| `cla2.md` | Reutilizar la contraseña de Redis de DataSQL | Hecho de fuente | Alta | Flowise usa el mismo secreto de `dataredis` | INTEGRADO |
| `cla3.md` | `_common.yml`, env global/local y labels Homepage | Hecho de fuente y regla del NAS | Alta | Se conserva | INTEGRADO |
| `cla3.md` | Healthcheck main en `/api/v1/ping` | Hecho de fuente | Alta | Se conserva y se añade healthcheck oficial del worker | INTEGRADO |
| `cla3.md` | Worker con `container_name` fijo | Hecho de fuente | Alta | Se conserva una sola réplica; queda escalado pendiente | INTEGRADO / PENDIENTE |
| `cla3.md` | `depends_on: flowise` plano | Hecho de fuente | Alta | Se mejora a `condition: service_healthy` | REEMPLAZADO |
| `cla3.md` | Worker con `WORKER_CONCURRENCY=5` | Hecho de fuente | Media | Punto de partida conservador | INTEGRADO |
| `cla4.md` | JWT, sesión, issuer, audience y token hash | Hecho de fuente, confirmado por docs de autorización | Alta | Se integran los secretos soportados | INTEGRADO |
| `cla4.md` | CORS/iframe wildcard | Hecho de fuente | Alta | No se integra por ampliar exposición sin necesidad | RECHAZADO |
| `cla4.md` | `MODE=worker` | Hecho de fuente | Media | Se mantiene `MODE=queue` en main y worker; el modo `worker` no se usa | REEMPLAZADO |
| `cla4.md` | Volumen Docker nombrado `flowise_data` | Hecho de fuente | Alta | Se usa bind mount por backup y visibilidad del NAS | REEMPLAZADO |
| reporte runtime NAS | `NODE_OPTIONS=--max-old-space-size=768`, worker con límite `1G` y reserva `256M` | Reporte operativo | Alta | Se incorpora al compose y se deja explícito que es una configuración validada en el runtime, no una variable secreta | INTEGRADO |
| `cla4.md` | Hardening, limits y labels | Hecho de fuente y regla del NAS | Alta | Se integran con límites adaptados al NAS | INTEGRADO |
| `hac1.md` | PostgreSQL y Redis propios | Hecho de fuente | Alta | Duplica DataSQL y contradice la topología del NAS | RECHAZADO |
| `hac1.md` | Nginx, Certbot, dominio, TLS y rate limiting | Hecho de fuente | Alta | Es una posible fase futura, no parte de esta instalación LAN | FUERA_DE_ALCANCE |
| `hac1.md` | `WORKER_CONCURRENCY=100000` | Hecho de fuente | Alta | Sin medición y desproporcionado para el NAS | RECHAZADO |
| `hac1.md` | Healthcheck con `<http://localhost>` | Hecho de fuente | Alta | URL inválida; se sustituye por healthchecks oficiales | RECHAZADO |
| `hac1.md` | Volúmenes propios para Postgres, Redis, Flowise y Certbot | Hecho de fuente | Alta | No corresponden a la infraestructura centralizada | FUERA_DE_ALCANCE |
| `hac2.md` | Stack propio sin proxy | Hecho de fuente | Alta | Sigue duplicando PostgreSQL/Redis | RECHAZADO |
| `hac2.md` | `CORS_ORIGINS=*`, `IFRAME_ORIGINS=*`, cookies inseguras | Hecho de fuente | Alta | No se integra en una guía presentada como segura | RECHAZADO |
| `hac2.md` | `docker compose` directo y `docker-compose.yml` | Hecho de fuente | Alta | Se sustituyen por `svc` y `compose.yml` del NAS | REEMPLAZADO |
| `hac2.md` | Escalado con `--scale` | Hecho de fuente | Alta | No se documenta mientras `svc` no lo soporte | PENDIENTE |
| `metaso.md` | PostgreSQL propio sin Redis/queue | Hecho de fuente | Alta | Se reemplaza por DataSQL + queue, que reúne las mejoras verificadas | REEMPLAZADO |
| `metaso.md` | `/root/.flowise` y `./data/flowise` | Hecho de fuente | Alta | Se conserva la idea de persistencia, no la ruta incompatible | REEMPLAZADO |
| `metaso.md` | Autenticación y `FLOWISE_SECRETKEY_OVERWRITE` | Hecho de fuente | Media | Se conservan los secretos; JWT se añade con documentación oficial | INTEGRADO |
| `metaso.md` | Escalar el main horizontalmente contra PostgreSQL | Inferencia no confirmada | Baja | Requiere proxy/load balancer y no forma parte de esta fase | FUERA_DE_ALCANCE |

### Contenido descartado explícitamente

- No se borra la idea de Nginx/TLS: queda registrada como futura guía de proxy,
  pero no se mezcla con una instalación LAN que no tiene dominio ni certificados.
- No se borra la idea de PostgreSQL/Redis propios: queda rechazada porque DataSQL
  ya proporciona ambos servicios y duplicarlos aumenta mantenimiento y backups.
- No se borra la idea de escalado: queda pendiente porque el código de `svc` no
  implementa `scale` y el worker mantiene un `container_name` fijo.
- No se conserva `REDIS_USE_ICOMPRESSION`, JWTs sin evidencia de soporte ni
  `WORKER_CONCURRENCY=100000`, porque no fueron validados o son inseguros para el
  hardware conocido.

---

## 13. Checklist final

- [ ] `$dkco/flowise/data` existe antes de levantar.
- [ ] `flowise_user` y `flowise_db` existen en DataSQL.
- [ ] `$dkco/flowise/.env` existe y tiene permisos `600`.
- [ ] `REDIS_PASSWORD` coincide con DataSQL.
- [ ] `FLOWISE_SECRETKEY_OVERWRITE` está guardada en un lugar seguro.
- [ ] `$dkco/.env` contiene `SERVER_IP` y `TZ`.
- [ ] `db_net` existe como red externa.
- [ ] `compose.yml` usa `env_file: [../.env, .env]`.
- [ ] El worker usa `NODE_OPTIONS=--max-old-space-size=768`, límite `1G` y reserva `256M`.
- [ ] El worker inicia con `sleep 3; flowise worker` y mantiene healthcheck en `5566/healthz`.
- [ ] El compose de Flowise no publica PostgreSQL ni Redis a la LAN; el binding `127.0.0.1:5432` de DataSQL se reserva para Home Assistant host-network.
- [ ] `svc config flowise` termina correctamente.
- [ ] Main y worker aparecen `healthy`.
- [ ] `svc stats flowise` fue revisado antes de elevar concurrencia.
- [ ] Se respaldaron tanto `data` como `flowise_db`.

---

## Referencias del proyecto

- Configuración final del catálogo: `agent/catalog/services/flowise/compose.yml`
- Variables de ejemplo: `agent/catalog/services/flowise/.env.example`
- Metadatos: `agent/catalog/services/flowise/ficha.md`
- Entorno Docker: `docs/docker-entorno.md`
