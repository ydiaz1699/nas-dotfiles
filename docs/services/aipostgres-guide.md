# PostgreSQL IA — Guía de instalación y operación gradual

> Servicio separado de DataSQL para preparar PostgreSQL 17 con `pgvector` y
> `pg_search`, sin modificar ni migrar todavía Flowise, Home Assistant o n8n.
>
> Estado de esta guía: scaffolding y primera instalación aislada. No afirma que
> el servicio ya esté instalado en el NAS.

## Decisión de arquitectura

El NAS conserva dos clústeres durante la migración gradual:

```text
DataSQL existente (datapostgres)
├── Flowise       → flowise_db
├── Home Assistant → homeassistant_db
├── n8n           → n8n_db (configuración aún por auditar)
└── otros consumidores actuales

PostgreSQL IA (aipostgres)
├── sin bases de consumidores al instalar
├── LobeHub       → futura lobehub_db
└── agente/Hermes → futura nas_agent_db
```

Esta separación evita cambiar la imagen de PostgreSQL que ya utiliza DataSQL.
También evita que una prueba de búsqueda vectorial o full-text compita
inmediatamente con el Recorder de Home Assistant. El coste es mantener un
segundo proceso PostgreSQL y un segundo conjunto de datos/respaldos.

En un servidor nuevo sin datos, un único clúster compatible podría reducir el
consumo base y simplificar los respaldos. En este NAS existente no se toma esa
opción todavía: DataSQL tiene consumidores activos, aunque Flowise y n8n aún
contengan pocos datos.

## Qué aporta la imagen

`paradedb/paradedb:0.25.4-pg17` es una versión fijada de ParadeDB sobre
PostgreSQL 17. La imagen incluye:

- `pgvector` (`vector`): tipos, operadores e índices para almacenar y buscar
  embeddings, útil para memoria semántica y RAG.
- `pg_search` (`pg_search`): búsqueda full-text con ranking BM25 y capacidades
  de búsqueda híbrida junto a los datos PostgreSQL.

Las extensiones están disponibles en el clúster, pero deben habilitarse en cada
base que las necesite. La instalación inicial solo comprueba el clúster y las
habilita en la base administrativa `aipostgres` como smoke test; no crea bases
para LobeHub ni para un agente futuro.

La opción `shared_preload_libraries=pg_search` está incluida porque la guía de
LobeHub la usa explícitamente para la imagen ParadeDB. `pgvector` no necesita
esa precarga.

## Estructura del servicio

```text
$dkco/aipostgres/
├── compose.yml
├── .env                  ← crear en el NAS, permisos 600; no va a Git
└── data/                 ← clúster PostgreSQL; backup crítico
```

El catálogo contiene:

```text
agent/catalog/services/aipostgres/
├── compose.yml
├── .env.example
└── ficha.md
```

El `compose.yml` del catálogo usa `../../_common.yml` porque está dos niveles
por debajo de `agent/catalog/`. Al copiarlo al NAS, la ruta correcta pasa a
ser `../_common.yml`. La secuencia de instalación de esta guía hace esa
adaptación explícitamente.

## Preflight: no modificar nada todavía

Ejecutar primero los diagnósticos y confirmar que `db_net` existe. Estos
comandos son de lectura y no detienen ni recrean servicios:

```bash
svc health
svc ps datasql
svc net
svc port-map
nas
disk
```

Criterios para continuar:

- DataSQL permanece saludable; no se cambia su compose ni su imagen.
- `db_net` aparece como red existente.
- No se necesita un puerto libre del host: `aipostgres` no publica `5432`.
- Hay espacio suficiente para la imagen y el directorio persistente.
- Si `db_net` no existe, detenerse y resolver el bootstrap de redes según
  `docs/docker-entorno.md`; no crear una red alternativa con otro nombre.

## Instalación inicial

### 1. Crear el directorio de datos

Crear carpetas antes de copiar archivos o aplicar permisos:

```bash
mkdir -p $dkco/aipostgres/data
```

### 2. Copiar el compose y el ejemplo de entorno

Esta copia parte del checkout local de `nas-dotfiles`. El primer comando copia
el compose versionado; el segundo crea el `.env` local solo si aún no existe,
para no sobrescribir secretos en una reinstalación:

```bash
cp "$NAS_DOTFILES/agent/catalog/services/aipostgres/compose.yml" \
  "$dkco/aipostgres/compose.yml"

if [[ ! -f "$dkco/aipostgres/.env" ]]; then
  cp "$NAS_DOTFILES/agent/catalog/services/aipostgres/.env.example" \
    "$dkco/aipostgres/.env"
fi
```

El compose del catálogo necesita una adaptación de ruta para ejecutarse desde
`$dkco/aipostgres/`:

```bash
sed -i \
  's#file: ../../_common.yml#file: ../_common.yml#' \
  "$dkco/aipostgres/compose.yml"
```

No copiar `.env` al repositorio. El archivo real del NAS contiene la contraseña
administrativa del clúster.

### 3. Completar el `.env` local

Abrir el archivo recién creado después de que el directorio y el archivo
existan:

```bash
dk aipostgres
nano .env
```

Contenido mínimo:

```env
POSTGRES_DB=aipostgres
POSTGRES_USER=aiadmin
POSTGRES_PASSWORD=__pega_aqui__
```

Reemplazar `__pega_aqui__` por una contraseña fuerte. No reutilizar la
contraseña de DataSQL ni de Redis. Puede generarse una antes de editar:

```bash
openssl rand -base64 32
```

No agregar `TZ` al `.env` local: llega desde `$dkco/.env` mediante
`env_file: [../.env, .env]`.

### 4. Aplicar permisos después de crear los archivos

```bash
chmod 700 "$dkco/aipostgres/data"
chmod 600 "$dkco/aipostgres/.env"
```

No ejecutar `chown` a un UID supuesto antes de probar la imagen. El entrypoint
de PostgreSQL debe preparar el directorio persistente; si los logs muestran un
error de permisos, se diagnostica el UID real de esta imagen antes de corregirlo.

### 5. Validar el compose resuelto

```bash
dk aipostgres
svc config aipostgres
```

Antes de levantar, comprobar visualmente que la configuración resuelta cumple
lo siguiente:

- imagen `paradedb/paradedb:0.25.4-pg17`;
- contenedor `aipostgres`;
- volumen `./data:/var/lib/postgresql/data`;
- red externa `db_net`;
- `shared_preload_libraries=pg_search`;
- healthcheck `pg_isready`;
- ningún bloque `ports:` ni publicación de `5432`;
- `env_file` global y local;
- límite de `1536M` y `1.5` CPU;
- `security_opt: no-new-privileges:true` heredado desde `../_common.yml`;
- no hay `cap_drop: ALL` durante esta primera prueba.

Si `svc config aipostgres` falla, no ejecutar `svc up`; corregir primero la
ruta de `extends` o la sintaxis YAML.

### 6. Descargar y levantar solo PostgreSQL IA

```bash
svc pull aipostgres
svc up aipostgres
```

Esto no detiene, recrea ni modifica DataSQL.

### 7. Comprobar estado y logs

```bash
svc ps aipostgres
svc logs aipostgres
```

`svc logs` puede quedar siguiendo la salida; pulsar Ctrl-C solo cierra la
visualización, no detiene el contenedor.

El contenedor debe quedar `Up (healthy)`. Si no está saludable, detener el
procedimiento y conservar los logs completos antes de cambiar permisos,
comandos o límites.

## Verificación de PostgreSQL y extensiones

La implementación de `svc exec` del NAS abre una sesión TTY por defecto. Para
esta primera comprobación se usa `psql` interactivo, sin pipe. Así se evita el
error:

```text
cannot attach stdin to a TTY-enabled container because stdin is not a terminal
```

Desde `dk aipostgres`, leer las variables sin hacer `source .env`:

```bash
POSTGRES_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1)}' .env)"
POSTGRES_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1)}' .env)"
POSTGRES_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1)}' .env)"

svc exec aipostgres postgres env \
  PGPASSWORD="$POSTGRES_PASSWORD" \
  PGUSER="$POSTGRES_USER" \
  PGDATABASE="$POSTGRES_DB" \
  psql
```

En el prompt de `psql`, ejecutar primero las consultas de disponibilidad:

```sql
SELECT version();

SELECT name,
       default_version,
       installed_version
FROM pg_available_extensions
WHERE name IN ('vector', 'pg_search')
ORDER BY name;
```

La consulta debe mostrar `vector` y `pg_search`. `installed_version` puede estar
vacía: significa que la extensión está disponible en la imagen, pero todavía
no fue creada en la base seleccionada.

Para probar que ambas extensiones pueden habilitarse en la base administrativa
vacía, ejecutar en la misma sesión:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_search;

SELECT extname,
       extversion
FROM pg_extension
WHERE extname IN ('vector', 'pg_search')
ORDER BY extname;
```

La salida esperada contiene dos filas: `vector` y `pg_search`. Esto solo afecta
la base `aipostgres`; no toca ninguna base de DataSQL.

Salir y limpiar las variables temporales:

```text
\q
```

```bash
unset POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD
```

Si `pg_available_extensions` no muestra una extensión, o `CREATE EXTENSION`
falla, no crear bases de consumidores ni migrar nada. Guardar el error y
revisar primero la versión efectiva de la imagen y el `shared_preload_libraries`.

## Verificaciones de aislamiento y recursos

Confirmar que el nuevo servicio está en la red compartida sin publicar el
puerto PostgreSQL:

```bash
svc net
svc port-map
svc ps aipostgres
svc stats aipostgres
```

`svc stats` es una vista continua; pulsar Ctrl-C para salir. En `svc port-map`
no debe aparecer `5432` para `aipostgres`. La comunicación futura será interna
por `db_net` usando el hostname `aipostgres:5432`.

Durante esta primera fase observar especialmente:

- memoria real frente al límite de `1536M`;
- CPU durante arranque y creación de índices;
- tiempo del healthcheck;
- espacio ocupado en `$dkco/aipostgres/data`;
- ausencia de reinicios en `svc ps aipostgres`.

No agregar todavía `cap_drop: ALL`. Primero confirmar que la imagen funciona y
que el entrypoint puede inicializar y actualizar el clúster; después se puede
hacer un cambio de endurecimiento separado y verificable.

## Lo que no se hace en esta fase

No ejecutar aún ninguna de estas acciones:

- no detener ni recrear `datasql`;
- no cambiar `postgres:16-alpine` de DataSQL;
- no crear `lobehub_db`;
- no crear `nas_agent_db`;
- no migrar Flowise;
- no migrar Home Assistant;
- no migrar n8n hasta auditar su compose y runtime;
- no crear otro Redis;
- no publicar `5432` al host o a la LAN;
- no configurar LobeHub ni RustFS como parte de este scaffolding.

Cuando exista el primer consumidor real, se debe crear un rol y una base
separados dentro de `aipostgres`. Por ejemplo, LobeHub tendrá su propia
`lobehub_db` y su propio usuario; no debe usar `aiadmin`.

## Backup y recuperación

Aunque el clúster empieza sin datos de consumidores, `./data` se vuelve crítico
inmediatamente después de crear extensiones, roles o bases. Antes de migrar el
primer servicio:

```bash
svc backup aipostgres
```

Comprobar que el backup terminó correctamente y que contiene el directorio del
servicio. Para un backup lógico de una base concreta, usar la misma receta de
credenciales sin `source .env` y ejecutar `pg_dump` mediante `svc exec`; no
mezclar ese procedimiento con la migración hasta documentar el consumidor.

No borrar `./data` para resolver un fallo de arranque. Primero conservar logs,
validar permisos, comprobar el compose resuelto y confirmar si existe un backup.
Una recuperación que sobrescriba datos requiere confirmación explícita.

## Referencias oficiales

- [ParadeDB — instalación de extensiones de terceros](https://docs.paradedb.com/deploy/third-party-extensions): confirma que la imagen de ParadeDB incluye `pg_search` y `pgvector`, y explica cuándo se usa `shared_preload_libraries`.
- [ParadeDB — instalación](https://docs.paradedb.com/documentation/getting-started/install): indica que ParadeDB soporta PostgreSQL 15 o superior y que los tags permiten fijar la versión de PostgreSQL.
- [Docker Hub — `paradedb/paradedb:0.25.4-pg17`](https://hub.docker.com/v2/repositories/paradedb/paradedb/tags/0.25.4-pg17): confirma el tag fijado y sus imágenes amd64/arm64.
- [LobeHub — despliegue de su base con Docker](https://lobehub.com/docs/self-hosting/platform/docker): documenta `shared_preload_libraries=pg_search`, PostgreSQL 17 y el uso de pgvector/pg_search para RAG y búsqueda de conocimiento.

El contenido operativo anterior fue reexpresado y adaptado a las convenciones de
este NAS; las fuentes enlazadas son la referencia técnica original.
