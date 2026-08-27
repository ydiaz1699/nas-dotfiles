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
13. **Compatibilidad con `svc exec`:** no colocar `-U`, `-d` ni `-c` directamente
    después de `svc exec`; pueden ser consumidas por el parser de `svc`. Usar
    `PGUSER`, `PGDATABASE`, `PGPASSWORD` y sesiones interactivas cuando aplique.
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

### 4. Sincronizar una clave entre servicios

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
  if [[ ! -f .env || ! -f .env.example ]]; then
    printf 'Falta el .env o .env.example del consumidor.\n' >&2
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

### 5. Verificar el consumidor sin exponer el secreto

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

### 6. Concluir con evidencia segura

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
