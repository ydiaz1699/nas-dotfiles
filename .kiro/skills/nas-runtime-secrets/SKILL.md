---
name: nas-runtime-secrets
description: >
  Opera secretos locales de servicios NAS sin exponer credenciales al LLM:
  lee valores desde .env con claves explícitas, los pasa mediante variables
  temporales, sincroniza consumidores, verifica el resultado con evidencia
  segura y limpia la sesión. Activar al configurar o modificar credenciales,
  PostgreSQL, Redis, .env, PGPASSWORD, REDISCLI_AUTH o secretos de servicios.
---

# Skill `nas-runtime-secrets`

## Propósito

Esta skill define el patrón para trabajar con secretos que existen únicamente

en el NAS. Permite que el LLM dé comandos reproducibles y compruebe resultados
sin que el usuario tenga que pegar contraseñas, tokens, claves JWT o el contenido
real de un `.env` en el chat, Git o un checkpoint.

El patrón tiene dos propósitos simultáneos:

1. **Operar el NAS:** leer un secreto local, usarlo en el consumidor correcto,
   verificar la conexión y actualizar el archivo local cuando corresponda.
2. **Comunicar evidencia segura al LLM:** devolver solo estados, nombres de
   usuario/base, `PONG`, códigos de salida y errores sanitizados; nunca el valor
   del secreto.

La skill no inventa nombres de variables ni credenciales. Primero se consultan
la guía del servicio, la ficha, el compose y `.env.example`.

## Detección: instalación nueva o servicio existente

La detección cambia la operación y evita destruir secretos estables:

```bash
if [[ -f .env ]]; then
  ENV_MODE=existing
else
  ENV_MODE=new
fi
printf 'Modo de servicio: %s\n' "$ENV_MODE"
```

### Instalación nueva

Cuando el `.env` local no existe:

1. Crear primero las carpetas requeridas por la guía del servicio.
2. Copiar el `.env.example` del catálogo a `.env`; no reconstruirlo desde memoria
   con un heredoc incompleto. El `.env.example` es plantilla compartible, no una
   fuente de secretos.
3. Leer las credenciales compartidas desde su fuente de verdad. Ejemplo:
   `REDIS_PASSWORD` se copia de `$dkco/datasql/.env`; no se genera otra.
4. Generar con `openssl rand -hex 32` los secretos que son propios del
   consumidor y no existen en otra fuente.
5. Escribir únicamente las claves conocidas en `.env`, aplicar `chmod 600` y
   comprobar nombres/placeholders sin mostrar valores.
6. Crear el rol y la base dedicados en PostgreSQL, en llamadas separadas, y
   verificar el login del consumidor.
7. Verificar Redis compartido y solo entonces ejecutar `svc config <servicio>`.

La plantilla del catálogo puede estar en
`$NAS_DOTFILES/agent/catalog/services/<servicio>/.env.example`; no se debe
suponer que existe una copia de `.env.example` dentro de `$dkco/<servicio>`.

Antes de crear o validar el servicio nuevo, comprobar también los prerrequisitos
no secretos de su entorno:

```bash
dk <servicio>
test -f "$dkco/.env" || printf 'Falta $dkco/.env global.\n' >&2
test -f "$dkco/_common.yml" || printf 'Falta $dkco/_common.yml.\n' >&2
```

No corregir una ruta `extends` por intuición. Comparar la ruta relativa real del
`compose.yml` desplegado con la del compose del catálogo y con la ubicación
confirmada de `_common.yml` antes de editar.

### Decisiones de fusión

Se integran estas ideas del procedimiento de Flowise:

- para un servicio nuevo, copiar `.env.example`, generar secretos propios y
  derivar secretos compartidos desde la fuente existente;
- usar `openssl rand -hex 32` como formato canónico para secretos de una línea;
- conservar la verificación de `SERVER_IP`, `_common.yml`, `svc config` y
  permisos `600`;
- crear el rol PostgreSQL primero y la base en una operación separada;
- informar al LLM solo `PONG`, nombres de rol/base, estados y errores seguros.

Se rechazan o se limitan estas variantes:

- reescribir siempre `.env` con `cat >`: solo es válido para una instalación
  nueva; en una existente puede borrar secretos estables y personalizaciones;
- `openssl rand -base64 32` como formato general: se reemplaza por hexadecimal
  para evitar caracteres reservados en `.env` y URI; Base64 solo queda permitido
  si la aplicación lo exige explícitamente;
- `docker exec`: se reemplaza por `svc exec`;
- `psql -U/-d/-c` después de `svc exec`: se reemplaza por `PGUSER`, `PGDATABASE`,
  `PGPASSWORD` y sesiones interactivas;
- combinar `CREATE ROLE` y `CREATE DATABASE`: se rechaza porque son operaciones
  distintas y `CREATE DATABASE` no debe depender de una transacción conjunta;
- `echo` o `printf` de una contraseña generada: se reemplaza por escribirla
  localmente y reportar solo el nombre de la clave;
- `chown`/diagnóstico de permisos de `data`: queda en la guía del servicio,
  porque depende del UID real de la imagen y no es una regla universal de
  transporte de secretos.

### Servicio existente

Cuando `.env` ya existe:

- no ejecutar `cp`, `cat > .env` ni regenerar todos los secretos;
- detectar solo claves vacías o placeholders;
- generar únicamente una clave propia que falte;
- conservar `FLOWISE_SECRETKEY_OVERWRITE`, JWT y claves de cifrado ya usadas;
- sincronizar una clave compartida desde su fuente de verdad solo si la
  configuración del consumidor debe coincidir;
- si se desconoce una contraseña de base existente, no cambiarla a ciegas:
  confirmar el servicio y hacer un cambio deliberado en PostgreSQL y `.env`.

## Activación

Usar antes de cualquier operación que incluya:

- `.env`, `.env.example`, contraseñas, tokens, claves o secretos;
- `PGPASSWORD`, `PGUSER`, `PGDATABASE`, `REDISCLI_AUTH` u otras variables de
  autenticación temporal;
- crear o conectar una base PostgreSQL/Redis a un servicio;
- copiar una credencial entre el `.env` de DataSQL y el `.env` de un consumidor;
- errores de `permission denied` relacionados con `/docker/.env`;
- resultados que deban compartirse con un LLM sin exponer secretos.

## Reglas no negociables

1. **Nunca pedir el secreto al usuario por chat.** Pedir solo el nombre de la
   variable, el resultado seguro de una verificación o una decisión que no esté
   en el repositorio.
2. **Nunca pedir `.env` real, `secrets.yaml`, tokens o hashes.** Se pueden leer
   `.env.example`, fichas, guías y compose del catálogo.
3. **Nunca ejecutar `source .env`.** Leer únicamente las claves necesarias con
   `awk` o equivalente y mantener el valor en una variable temporal.
4. **Nunca imprimir el valor.** No usar `echo "$SECRET"`, `printf '%s' "$SECRET"`,
   `cat .env`, `bat .env` ni pegar `svc config` completo en el chat si contiene
   interpolaciones.
5. **Validar antes de mutar:** rechazar valor vacío, `__pega_aqui__`,
   `CHANGE_ME`, `changeme` y placeholders equivalentes.
6. **Usar una variable con propósito explícito:** por ejemplo
   `DATASQL_REDIS_PASSWORD`, `PG_ADMIN_PASSWORD` o `FLOWISE_DB_PASSWORD`.
   No reutilizar una variable administrativa para una aplicación.
7. **Limpiar al terminar:** ejecutar `unset` para cada variable temporal, tanto
   después de una verificación correcta como después de una corrección fallida.
8. **No generar un segundo secreto para un recurso compartido:** si DataSQL ya
   tiene `REDIS_PASSWORD`, los consumidores deben reutilizarlo y verificarse con
   esa misma credencial.
9. **Navegar al servicio antes de usar `svc`:** ejecutar `dk <servicio>` y
   comprobar el prompt. Desde `~`, `svc` puede resolver `/docker/.env` global y
   producir `permission denied` aunque el servicio esté bien.
10. **No cambiar de usuario accidentalmente:** si el procedimiento requiere la
    sesión privilegiada `root@Nas`, conservarla. No cambiar a `aadm` ni modificar
    permisos globales para ocultar un error de contexto.
11. **Nunca usar `exit` en un bloque pegado directamente en una shell
    interactiva:** puede cerrar la sesión privilegiada. Usar una función, una
    subshell explícita `( ... )`, o ramas `if/else`; si se usa `exit`, explicar
    que pertenece a una subshell.
12. **Separar Bash y `psql`:** `root@Nas ... #` ejecuta Bash; `aipostgres=#`,
    `homeassistant_db=>` o `flowise_db=>` ejecutan SQL/órdenes de `psql`.
    Después de una sesión interactiva, ejecutar `\q` y esperar el prompt de Bash
    antes de `read`, `printf`, `svc exec` o `unset`.
13. **Compatibilidad con `svc exec`:** el NAS tiene CLI Bash y CLI Python/Typer;
    no mezclar sus sintaxis. En Bash usar
    `NAS_CLI=bash svc exec <proyecto> <servicio> <comando>`. En Python usar
    `NAS_CLI=python svc exec <proyecto> -- <servicio> <comando>`; el `--` separa
    las opciones de Typer y evita que `-c`, `-e`, `-U`, `-d`, `-v` o `-T` sean
    interpretadas por `svc`. No usar `-T` con el CLI Python. Para PostgreSQL/
    Redis, preferir `PGUSER`, `PGDATABASE`, `PGPASSWORD` y `REDISCLI_AUTH`.
14. **No afirmar conexión por pertenencia a una red:** `db_net` permite llegar al
    servidor, pero la prueba debe confirmar configuración, autenticación y
    runtime.

## Flujo canónico

### 1. Resolver la fuente y el destino

Antes de escribir comandos, identificar:

```text
Fuente:  servicio/archivo y clave que ya contienen el secreto
Destino: servicio/archivo y clave que deben usarlo
Uso:     base PostgreSQL, Redis, API, sesión o cifrado
Prueba:  resultado seguro que demuestra que funcionó
```

Ejemplo de DataSQL compartido:

```text
Fuente:  $dkco/datasql/.env → REDIS_PASSWORD
Destino: $dkco/flowise/.env → REDIS_PASSWORD
Prueba:  redis-cli ping → PONG
```

La fuente de nombres y valores esperados es, en este orden:

1. `docs/services/<servicio>-guide.md`;
2. `.kiro/skills/datasql/SKILL.md` si interviene DataSQL;
3. `agent/catalog/services/<servicio>/ficha.md`;
4. `agent/catalog/services/<servicio>/compose.yml`;
5. `agent/catalog/services/<servicio>/.env.example`.

### 2. Entrar al contexto correcto

```bash
dk datasql
```

o:

```bash
dk <consumidor>
```

Si el prompt no muestra el directorio esperado, no continúes con `svc`.

### 3. Leer una clave local sin mostrarla

Plantilla segura:

```bash
SECRET_VALUE="$(awk -F= '$1=="NOMBRE_DE_CLAVE"{print substr($0,index($0,"=")+1); exit}' .env)"

if [[ -z "$SECRET_VALUE" ||
      "$SECRET_VALUE" == "__pega_aqui__" ||
      "$SECRET_VALUE" == "CHANGE_ME" ||
      "$SECRET_VALUE" == "changeme" ]]; then
  printf 'NOMBRE_DE_CLAVE falta o contiene un placeholder.\n' >&2
  unset SECRET_VALUE
else
  printf 'NOMBRE_DE_CLAVE cargada localmente.\n'
fi
```

Para procedimientos interactivos, no usar `exit 1` directamente en la shell del
usuario. Si hace falta abortar una secuencia completa, envolverla explícitamente:

```bash
(
  SECRET_VALUE="$(awk -F= '$1=="NOMBRE_DE_CLAVE"{print substr($0,index($0,"=")+1); exit}' .env)"
  if [[ -z "$SECRET_VALUE" || "$SECRET_VALUE" == "__pega_aqui__" ]]; then
    printf 'Falta NOMBRE_DE_CLAVE; no se modifica nada.\n' >&2
    exit 1
  fi
  # operaciones de la subshell
  unset SECRET_VALUE
)
```

### 4. Crear o completar el `.env` sin sobrescribir secretos

Para una instalación nueva, copia primero la plantilla del catálogo y luego
escribe los valores. Para un servicio existente, omite la copia y conserva lo
que ya funciona:

```bash
# Solo instalación nueva; no ejecutar si .env ya existe.
if [[ ! -f .env ]]; then
  cp "$NAS_DOTFILES/agent/catalog/services/<servicio>/.env.example" .env
fi
```

Para valores de una sola línea y generados en hexadecimal, este helper actualiza
una clave existente o la agrega si la plantilla no la contenía. No usarlo para
secretos con saltos de línea o caracteres reservados sin adaptar el mecanismo:

```bash
set_env_key() {
  local key="$1" value="$2" file="${3:-.env}"
  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}
```

Ejemplo de fusión para un consumidor nuevo de DataSQL:

```bash
# Fuente compartida: no generar una segunda contraseña Redis.
dk datasql
DATASQL_REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' .env)"

# Secretos propios: generar solo en la instalación nueva.
SERVICE_DB_PASSWORD="$(openssl rand -hex 32)"
SERVICE_APP_PASSWORD="$(openssl rand -hex 32)"
SERVICE_ENCRYPTION_SECRET="$(openssl rand -hex 32)"
SERVICE_AUTH_SECRET="$(openssl rand -hex 32)"

# Volver al consumidor; no imprimir ninguno de los valores.
dk <consumidor>
set_env_key SERVICE_DB_PASSWORD "$SERVICE_DB_PASSWORD"
set_env_key SERVICE_APP_PASSWORD "$SERVICE_APP_PASSWORD"
set_env_key SERVICE_ENCRYPTION_SECRET "$SERVICE_ENCRYPTION_SECRET"
set_env_key SERVICE_AUTH_SECRET "$SERVICE_AUTH_SECRET"
set_env_key REDIS_PASSWORD "$DATASQL_REDIS_PASSWORD"
chmod 600 .env
```

Los nombres `SERVICE_*` son marcadores del patrón: deben sustituirse por las
claves reales que aparecen en la guía, ficha, compose y `.env.example` del
servicio. No se deben inventar variables. El consumidor debe conservar la
misma contraseña de base que se usó al crear su rol PostgreSQL.

Después de una mutación, verificar solo la presencia de claves problemáticas:

```bash
awk -F= '$1 ~ /^[A-Z_]+$/ && ($2 == "" || $2 == "__pega_aqui__" || $2 == "...") {print $1}' .env
```

La salida vacía significa que no se detectaron claves vacías o placeholders;
no significa que se hayan mostrado los secretos.

6. Sincronizar una clave entre servicios

Solo después de validar la fuente y comprobar que la clave existe en el destino:

```bash
dk datasql
DATASQL_REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' .env)"

if [[ -z "$DATASQL_REDIS_PASSWORD" ||
      "$DATASQL_REDIS_PASSWORD" == "__pega_aqui__" ]]; then
  printf 'REDIS_PASSWORD de DataSQL falta o usa un placeholder.\n' >&2
  unset DATASQL_REDIS_PASSWORD
else
  dk <consumidor>
  if [[ ! -f .env ]]; then
    printf 'Falta el .env del consumidor.\n' >&2
    unset DATASQL_REDIS_PASSWORD
  elif ! grep -q '^REDIS_PASSWORD=' .env; then
    printf 'Falta REDIS_PASSWORD en el .env del consumidor.\n' >&2
    unset DATASQL_REDIS_PASSWORD
  else
    # Usar solo si la credencial es un valor seguro conocido, por ejemplo hex.
    sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=$DATASQL_REDIS_PASSWORD/" .env
    chmod 600 .env
    printf 'REDIS_PASSWORD del consumidor actualizado localmente.\n'
    unset DATASQL_REDIS_PASSWORD
  fi
fi
```

La modificación anterior afecta únicamente el `.env` local del consumidor. No
modifica DataSQL ni crea otro Redis. Para valores con caracteres reservados o
saltos de línea, no usar esta sustitución: aplicar el mecanismo de secreto
propio de la aplicación y codificar la URI según su documentación.

7. Verificar el consumidor sin exponer el secreto

Redis compartido:

```bash
dk datasql
DATASQL_REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' .env)"

svc exec datasql redis \
  env REDISCLI_AUTH="$DATASQL_REDIS_PASSWORD" \
  redis-cli ping

unset DATASQL_REDIS_PASSWORD
```

Resultado seguro esperado:

```text
PONG
```

PostgreSQL dedicado:

```bash
dk datasql
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' .env)"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' .env)"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1); exit}' .env)"

svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE=<base_admin> \
  psql
```

Dentro de `psql` ejecutar SQL solamente. Para probar el usuario dedicado,
salir con `\q`, cargar la contraseña desde el `.env` del consumidor en Bash y
abrir una nueva sesión con `PGUSER=<usuario>` y `PGDATABASE=<base>`. Nunca usar `-U`, `-d` ni `-c` en el vector de `svc exec`.

Prueba segura esperada:

```sql
SELECT current_user, current_database();
```

No consultar `rolpassword`: es un hash sensible y no prueba que la contraseña
configurada por el consumidor funcione.

8. Concluir con evidencia segura

El reporte al LLM debe contener únicamente:

- servicio y archivos afectados, sin valores;
- clave sincronizada, sin el valor;
- resultado `PONG`, `healthy`, código HTTP o salida de
  `current_user/current_database`;
- conteos, nombres de base/rol y errores no secretos;
- si una operación fue verificación o mutación;
- variables limpiadas.

Ejemplo correcto:

```text
REDIS_PASSWORD de Flowise actualizado desde DataSQL sin mostrar el valor.
redis-cli ping devolvió PONG.
DATASQL_REDIS_PASSWORD fue eliminado con unset.
```

Ejemplos prohibidos:

```text
REDIS_PASSWORD=4f...
cat /docker/datasql/.env
La contraseña de ha_user es ...
svc config <servicio>  # pegar la salida completa si incluye secretos
```

## Criterios de parada

Detenerse sin mutar cuando:

- la clave fuente no existe o es placeholder;
- la clave destino no está documentada;
- fuente y destino usan nombres diferentes sin decisión explícita;
- el valor de Redis no coincide con DataSQL;
- el usuario/DB no están confirmados;
- `svc` se ejecuta desde `~` y falla intentando leer `$dkco/.env`;
- el prompt indica que todavía se está dentro de `psql`;
- la prueba devuelve `authentication failed`, `connection refused` o un error
  cuya causa no está aislada.

No corregir una discrepancia generando otra contraseña a ciegas. Primero
identificar cuál servicio es la fuente de verdad y cuál archivo local debe
actualizarse.

## Checklist reutilizable

```text
[ ] Leí guía, ficha, compose y .env.example del servicio.
[ ] Identifiqué fuente, destino, clave y prueba.
[ ] No pedí ni mostré el secreto.
[ ] Usé dk <servicio> antes de svc.
[ ] Leí solo la clave necesaria sin source .env.
[ ] Rechacé vacío y placeholders.
[ ] Verifiqué la compatibilidad de la aplicación con el valor.
[ ] No usé -U/-d/-c directamente después de svc exec.
[ ] Separé Bash de psql y salí con \q antes de volver a Bash.
[ ] Hice la mutación solo después de validar la fuente.
[ ] Guardé permisos 600 después de crear/modificar el .env.
[ ] Ejecuté una prueba segura de runtime.
[ ] No pegué salida con secretos.
[ ] Ejecuté unset de todas las variables temporales.
[ ] Registré solo evidencia segura.
```

## Relación con otras skills

- `datasql`: decide la arquitectura, roles, bases, `db_net` y Redis compartido.
- `nas-dotfiles`/`dotfile-skill`: impone aliases, rutas y operaciones `svc`.
- `documentation-evolution`: se usa si la experiencia revela un hueco en una
  guía, skill, contrato o conexión del framework.

Esta skill controla **cómo transportar y verificar secretos en runtime**; no
reemplaza la guía del servicio ni autoriza a inventar su configuración.
