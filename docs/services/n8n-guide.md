# Guía: n8n con PostgreSQL dedicado en DataSQL

> Guía de continuidad de la auditoría y reparación ejecutada en el NAS.
> No contiene secretos reales. Separa el runtime confirmado de los cambios
> propuestos que todavía no tienen evidencia de haberse aplicado.

## Estado

- **Runtime confirmado:** n8n arrancó correctamente contra PostgreSQL `n8n_db`.
- **Versión observada:** `n8nio/n8n:latest`, resuelta por el runtime a n8n `2.23.4`.
- **Evidencia:** migraciones completadas, `n8n_user` pudo iniciar sesión,
  `n8n_db` pertenece a `n8n_user`, el contenedor quedó `Up`, tuvo `0` reinicios
  y `/healthz` respondió `HTTP 200`.
- **Hardening pendiente:** aplicar `extends`, `env_file` global/local,
  eliminación de `TZ` duplicado e `ipv4_address`, healthcheck formal y pin de
  imagen. No se afirma que estos cambios ya estén desplegados porque no se
  recibió una verificación posterior.
- **Siguiente objetivo:** continuar con la instalación de LobeHub sin repetir
  la migración de DataSQL ni recrear la base de n8n.

Las referencias oficiales usadas para la versión son [release notes 2.x de
n8n](https://docs.n8n.io/changelog/release-notes-2.x) y [releases oficiales de
n8n en GitHub](https://github.com/n8n-io/n8n/releases). La documentación externa
se resume y se parafrasea aquí; no se copian bloques extensos.

---

## Auditoría de fuentes y variantes

| Fuente | Afirmación u operación | Tipo | Confianza | Decisión | Clasificación |
|---|---|---|---|---|---|
| Salida inicial de `svc logs n8n` | `password authentication failed for user "n8n_user"` | HECHO | ALTA | Investigar credencial antes de recrear datos | INTEGRADO |
| Runtime del usuario | El rol `n8n_user` inicialmente no existía | HECHO | ALTA | Crear rol dedicado, no usar `aiadmin` | INTEGRADO |
| Sesión interactiva de `psql` | `CREATE ROLE n8n_user LOGIN;` seguido de `\password n8n_user` | HECHO | ALTA | Mantener rol y contraseña en sesión separada | INTEGRADO |
| Conversación | `\password` no consume automáticamente `N8N_DB_PASSWORD` de Bash | INFERENCIA SEGURA | ALTA | Leer localmente el secreto y escribirlo en el prompt solo si la sesión lo solicita; no imprimirlo en chat | INTEGRADO |
| Variante `grep ... | cut ...` de otra LLM | Imprime el secreto en pantalla | HECHO | ALTA | Sustituir por `awk` en variable temporal consumida localmente | REEMPLAZADO |
| `.kiro/skills/nas-runtime-secrets/SKILL.md` | No usar `source .env`, no imprimir secretos, limpiar variables | HECHO | ALTA | Usar `awk`, `PGPASSWORD` y `unset` | INTEGRADO |
| `docs/services/datasql-guide.md` | Crear rol y base en llamadas separadas de `psql` | HECHO | ALTA | Aplicar `CREATE DATABASE` fuera de la sesión de creación del rol | INTEGRADO |
| Runtime del usuario | Login como `n8n_user` contra `aipostgres` fue correcto | HECHO | ALTA | Confirmar la contraseña de `$dkco/n8n/.env` antes de crear la base | INTEGRADO |
| Runtime del usuario | `CREATE DATABASE n8n_db OWNER n8n_user` y consulta del propietario | HECHO | ALTA | Conservar `n8n_db` y `n8n_user`; no recrearlos | INTEGRADO |
| Compose real auditado | `n8nio/n8n:latest`, solo `env_file: .env`, `TZ`, `ipv4_address`, sin healthcheck | HECHO | ALTA | Registrar como estado anterior y preparar hardening | INTEGRADO |
| Runtime del usuario | Migraciones completadas, versión `2.23.4`, editor en `5678`, runner JS registrado | HECHO | ALTA | Declarar n8n operativo antes de documentar | INTEGRADO |
| Runtime del usuario | `/healthz` devolvió `HTTP 200`, `svc health` mostró `0` reinicios | HECHO | ALTA | Aceptar la reparación funcional | INTEGRADO |
| `svc exec` ejecutado desde `aadm` | `open /docker/.env: permission denied` | HECHO | ALTA | Corregir contexto de usuario/root; no diagnosticarlo como fallo de Node | INTEGRADO |
| Release oficial de n8n | `2.36.7` aparece como estable y `2.37.3` como pre-release | HECHO | ALTA | No usar beta; proponer `2.36.7` como actualización separada | INTEGRADO |
| Compose corregido propuesto en el chat | `extends`, healthcheck Node, `SERVER_IP`, sin IP fija ni `TZ` inline | INFERENCIA SEGURA | MEDIA | Dejar como objetivo pendiente hasta verificarlo en el NAS | PENDIENTE |
| Error `Failed to connect to ACP` | Fallo de conexión Kiro Web, no de n8n | HECHO | MEDIA | Mantener fuera de la guía NAS | FUERA_DE_ALCANCE: Kiro |

---

## Hechos confirmados

1. El stack operativo de PostgreSQL es `$dkco/datasql`, con PostgreSQL en
   `datapostgres:5432` dentro de `db_net`.
2. El rol `n8n_user` existe y permite login.
3. La contraseña de `DB_PASSWORD` del `.env` de n8n permitió autenticarse como
   `n8n_user`.
4. La base `n8n_db` existe y su propietario verificado es `n8n_user`.
5. n8n completó migraciones de esquema y registró la versión `2.23.4`.
6. El contenedor observado fue `n8nio/n8n:latest`, con puerto `5678` publicado,
   `0` reinicios durante la comprobación y endpoint `/healthz` con `HTTP 200`.
7. La persistencia observada es `./data:/home/node/.n8n`; dentro de `data` se
   observaron `storage` y `nodes/node_modules`.
8. El compose real observado usa `DB_TYPE=postgresdb`, `datapostgres`, puerto
   `5432`, `n8n_db`, `n8n_user`, `DB_PASSWORD` y `N8N_ENCRYPTION_KEY`.
9. La imagen informó que Python 3 no estaba disponible para el task runner
   interno; el runner JavaScript sí quedó registrado. Esta advertencia no
   impidió el arranque, pero requiere una decisión posterior si se usan tareas
   Python.
10. No se verificó que el pin `2.36.7` ni el hardening del compose propuesto se
    hayan aplicado al NAS.

## Decisiones derivadas

1. No cambiar la contraseña de `n8n_user` después de comprobar que coincide con
   `DB_PASSWORD`; cambiarla a ciegas podía romper la instancia funcional.
2. No usar el usuario administrativo de DataSQL para n8n.
3. No crear un Redis adicional: n8n no mostró en su compose auditado ninguna
   configuración de Redis/queue.
4. No usar `depends_on` contra DataSQL: vive en otro compose y n8n debe tolerar
   su arranque independiente.
5. Separar la estabilización del runtime actual de la actualización a `2.36.7`.
   `latest` es mutable; la actualización debe tener backup, pin y verificación.
6. Mantener RustFS fuera de DataSQL. Solo se instalará como servicio S3 separado
   si la configuración oficial de LobeHub demuestra que necesita almacenamiento
   de objetos.
7. No crear todavía un instalador DebMenux de n8n: la instalación auditada es
   NAS-específica y depende del DataSQL compartido. Si se crea después, debe
   implementar el aprovisionamiento seguro del rol/base y no copiar el patrón
   inseguro antiguo de `flowise.sh`.

---

## Artefactos y estados

| Tipo | Identificador | Estado inicial | Operación | Estado confirmado o esperado |
|---|---|---|---|---|
| Servicio | `n8n` | Reiniciaba por error de DB | Detener, corregir dependencia y levantar | Arranca; `0` reinicios observados |
| Rol PostgreSQL | `n8n_user` | No existía | Crear con login y contraseña local | Existe, `rolcanlogin=t` |
| Base PostgreSQL | `n8n_db` | No existía | Crear en sesión separada con owner | Existe, owner `n8n_user` |
| Secreto local | `$dkco/n8n/.env` → `DB_PASSWORD` | Existía, valor no compartido | Consumir con `awk` en variable temporal | Coincide con el login probado |
| Clave de cifrado | `$dkco/n8n/.env` → `N8N_ENCRYPTION_KEY` | Existía | No regenerar | Debe conservarse estable |
| Datos n8n | `$dkco/n8n/data` | Existía | Montaje observado | Persistencia en `/home/node/.n8n` |
| Compose runtime | `$dkco/n8n/compose.yml` | Legacy | Snapshot creado antes del hardening | Hardening pendiente de verificar |
| Snapshot | `svc snapshot n8n` | No confirmado antes | Ejecutado antes del cambio propuesto | Disponible en el NAS; ruta interna gestionada por `svc` |
| Imagen | `n8nio/n8n:latest` | Mutable | Auditar versión resuelta | `2.23.4` observada; pin `2.36.7` pendiente |
| Red | `db_net` | Existía | n8n conectado con IP fija | Conectividad funcional; quitar `ipv4_address` pendiente |

---

## Secuencia ejecutada

### Paso 1 — Detener n8n antes de tocar PostgreSQL

```bash
dk n8n
svc stop n8n
svc ps n8n
```

**Postcondición observada:** el contenedor quedó detenido y no se siguió
reiniciando mientras se reparaba la base.

### Paso 2 — Crear el rol dedicado

La sesión administrativa se abrió desde `$dkco/datasql` usando `PGPASSWORD`
solo para la contraseña administrativa. En `psql` se ejecutó:

```sql
CREATE ROLE n8n_user LOGIN;
\password n8n_user
```

`\password` solicitó dos veces la contraseña que ya existía en el `.env` local
de n8n. Esa entrada ocurre dentro del prompt de `psql`; Bash no rellena el
prompt automáticamente por tener una variable con otro nombre.

**Verificación:**

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'n8n_user';
```

**Resultado seguro:** `n8n_user | t`.

### Paso 3 — Verificar el secreto sin imprimirlo

La variante canónica usada fue:

```bash
dk n8n
N8N_DB_PASSWORD="$(awk -F= '$1=="DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' .env)"
dk datasql
svc exec datasql postgres \
  env PGPASSWORD="$N8N_DB_PASSWORD" \
      PGUSER=n8n_user \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`:

```sql
SELECT current_user, current_database();
\q
```

**Resultado seguro:** `n8n_user | aipostgres`. Después se ejecutó `unset`.

La contraseña nunca se pegó en el chat. No usar como procedimiento canónico:

```bash
grep '^DB_PASSWORD=' <ruta>/n8n/.env | cut -d'=' -f2-
```

Esa variante imprime un secreto y además puede depender de una ruta fija.

### Paso 4 — Crear la base en una sesión separada

La primera consulta confirmó que `n8n_db` no existía. Después, con una nueva
sesión administrativa, se ejecutó:

```sql
CREATE DATABASE n8n_db OWNER n8n_user;

SELECT datname,
       pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'n8n_db';
```

**Resultado seguro:** `n8n_db | n8n_user`.

No se combinaron `CREATE ROLE` y `CREATE DATABASE` en una llamada, porque son
operaciones distintas y `CREATE DATABASE` no debe depender de una transacción
conjunta.

### Paso 5 — Probar el login contra la base dedicada

La prueba final debe usar la contraseña del consumidor, no la administrativa:

```bash
dk n8n
N8N_DB_PASSWORD="$(awk -F= '$1=="DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' .env)"
dk datasql
svc exec datasql postgres \
  env PGPASSWORD="$N8N_DB_PASSWORD" \
      PGUSER=n8n_user \
      PGDATABASE=n8n_db \
  psql
```

En `psql`:

```sql
SELECT current_user, current_database();
\q
```

**Postcondición:** `n8n_user | n8n_db`. Limpiar siempre:

```bash
unset N8N_DB_PASSWORD
```

### Paso 6 — Levantar y observar migraciones

```bash
dk n8n
svc up n8n
svc ps n8n
svc logs n8n
```

Las migraciones terminaron correctamente. Los logs informaron, entre otros
mensajes, que el Task Broker estaba listo en `127.0.0.1:5679`, el runner JS se
registró, n8n quedó en versión `2.23.4` y el editor se publicó en `5678`.

Detener únicamente el seguimiento con `Ctrl-C`; no detener el contenedor.

### Paso 7 — Verificar estabilidad y acceso

```bash
svc ps n8n
svc health | grep -E '(^|[[:space:]])n8n([[:space:]]|$)' || true
```

**Resultados observados:** `Up`, `0` reinicios.

La comprobación funcional fue:

```bash
SERVER_IP="$(awk -F= '$1=="SERVER_IP"{print substr($0,index($0,"=")+1); exit}' "$dkco/.env")"
curl -fsS -o /dev/null -w 'HTTP %{http_code}\n' "http://${SERVER_IP}:5678/healthz"
unset SERVER_IP
```

**Resultado observado:** `HTTP 200`.

### Paso 8 — Crear snapshot antes del hardening

```bash
dk n8n
svc snapshot n8n
```

**Postcondición:** el comando terminó sin error. El snapshot protege la
configuración anterior antes de reemplazar el compose; no sustituye un backup
de los datos persistentes.

---

## Hardening pendiente: compose objetivo

Este bloque es la configuración objetivo preparada durante la auditoría. **No
se debe afirmar que está desplegado hasta ejecutar `svc config`, recrear n8n y
verificar `svc ps`, logs, health y `/healthz` después del cambio.**

```yaml
services:
  n8n:
    extends:
      file: ../_common.yml
      service: _defaults
    image: n8nio/n8n:2.36.7
    container_name: n8n
    env_file:
      - ../.env
      - .env
    environment:
      N8N_SECURE_COOKIE: "false"
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: datapostgres
      DB_POSTGRESDB_PORT: "5432"
      DB_POSTGRESDB_DATABASE: n8n_db
      DB_POSTGRESDB_USER: n8n_user
      DB_POSTGRESDB_PASSWORD: ${DB_PASSWORD}
      N8N_ENCRYPTION_KEY: ${N8N_ENCRYPTION_KEY}
      WEBHOOK_URL: http://${SERVER_IP}:5678
    ports:
      - "5678:5678"
    volumes:
      - type: bind
        source: ./data
        target: /home/node/.n8n
        read_only: false
    networks:
      - db_net
    healthcheck:
      test:
        - CMD-SHELL
        - >-
          node -e "fetch('http://127.0.0.1:5678/healthz').then(response =>
          process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))"
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 120s
    cap_drop:
      - ALL
    labels:
      - homepage.group=IA y Automatización
      - homepage.name=n8n
      - homepage.icon=n8n
      - homepage.href=http://${SERVER_IP}:5678
      - homepage.description=Automatización de workflows
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G
        reservations:
          cpus: "0.25"
          memory: 256M

networks:
  db_net:
    external: true
```

### Orden para aplicar el hardening

1. Entrar como `root` y ejecutar `dk n8n`; desde `aadm` se observó
   `permission denied` al leer el `.env` global.
2. Confirmar que el snapshot existe.
3. Crear/editar el archivo completo; no tocar el `.env` real.
4. Validar con `svc config n8n >/dev/null`.
5. Descargar y recrear la versión fijada con `svc update n8n`.
6. Verificar `svc ps n8n`, `svc health`, logs y `/healthz`.
7. Si falla el arranque, no borrar `data`; usar el snapshot/rollback documentado
   y revisar el error exacto.

No usar `svc up` como sustituto de `svc update` cuando se cambie la etiqueta de
imagen: `svc update` descarga la imagen y recrea el servicio. Para un cambio
solo de configuración, `svc recreate n8n` puede ser suficiente después de
validar el compose.

### Advertencia del task runner

La imagen observada informó que Python 3 no estaba disponible para el task
runner interno. Eso no impidió que el runner JavaScript se registrara ni que el
editor arrancara. Antes de usar Code nodes o tareas Python en producción, revisar
la configuración de task runners de la versión fijada; no desactivar runners ni
inventar variables sin evidencia de la documentación oficial o una prueba en
el contenedor.

---

## Backup y recuperación

Antes de cualquier actualización o modificación que pueda recrear n8n:

```bash
dk n8n
svc backup n8n
svc snapshot n8n
```

- `svc snapshot n8n` protege compose y `.env` mediante el mecanismo del
  framework.
- `svc backup n8n` protege los datos persistentes de `./data` según la política
  de `svc`.
- No publicar el archivo generado ni el `.env` real.
- No borrar `$dkco/n8n/data` para corregir un error de conexión PostgreSQL.
- El rollback debe consumir el snapshot creado antes de la mutación; confirmar
  primero que el snapshot correspondiente existe.

---

## Continuidad hacia LobeHub

La migración de DataSQL necesaria para continuar quedó realizada. El siguiente
chat debe comenzar desde este estado:

```text
COMPLETADO: DataSQL operativo y n8n conectado
EVIDENCIA: n8n_user puede autenticarse; n8n_db pertenece a n8n_user;
           migraciones n8n terminadas; 0 reinicios; /healthz HTTP 200
CAMBIOS: rol/base dedicados; n8n persistente en ./data; runtime auditado
PENDIENTE: aplicar/verificar hardening del compose y pin 2.36.7 si se decide
NO_REPETIR: no recrear n8n_user, n8n_db ni N8N_ENCRYPTION_KEY;
           no cambiar passwords existentes a ciegas; no usar aipostgres como
           identidad de aplicación; no crear Redis adicional
SIGUIENTE: auditar la documentación oficial y el compose objetivo de LobeHub
           desde docs/docker-entorno.md, datasql-guide.md y esta guía
```

Para LobeHub:

1. Leer primero `docs/docker-entorno.md`, `.kiro/skills/datasql/SKILL.md` y
   `docs/services/datasql-guide.md`.
2. Confirmar en la documentación oficial de la versión elegida sus variables,
   imagen, persistencia, puerto, healthcheck, PostgreSQL, Redis y almacenamiento
   de objetos antes de crear archivos.
3. Crear un rol y base dedicados, por ejemplo `lobehub_user` y `lobehub_db`, solo
   después de confirmar los nombres de variables de la imagen. No reutilizar
   `n8n_user`, `n8n_db`, `aiadmin` ni `aipostgres`.
4. Reutilizar `dataredis:6379` y su contraseña de `$dkco/datasql/.env` si LobeHub
   realmente requiere Redis; no crear otro Redis.
5. Conectar LobeHub a `datapostgres:5432` y `dataredis:6379` por `db_net`; no
   publicar PostgreSQL ni Redis y no usar `depends_on` contra DataSQL.
6. Determinar si LobeHub exige S3/RustFS. RustFS permanece fuera de DataSQL y
   solo se instala como servicio separado si la documentación de LobeHub o una
   prueba real lo requiere.
7. Ejecutar la secuencia real: carpetas → `.env.example`/`.env` → permisos →
   base/rol → compose → `svc config` → `svc up` → health/logs/acceso →
   catalog-sync y scanner.

### Decisiones pendientes para LobeHub

- Versión estable exacta e imagen oficial.
- Variables PostgreSQL y Redis admitidas por esa versión.
- Si usa almacenamiento local, S3 compatible o RustFS.
- Puerto interno y puerto LAN.
- Healthcheck sin autenticación.
- Recursos adecuados para los 2 cores y 8 GB del NAS.
- Si necesita acceso externo y, en ese caso, qué proxy/TLS se usará.

### Bloqueados

La guía de n8n no puede resolver por sí sola esos puntos de LobeHub porque la
configuración exacta de la versión elegida todavía no forma parte de las
fuentes auditadas en este chat.

---

## Incidencias registradas

```yaml
- incident_id: n8n-db-authentication-failed
  service: n8n
  source: user-runtime-report
  symptom: 'password authentication failed for user n8n_user'
  root_cause: 'El rol dedicado no existía inicialmente; el compose ya esperaba ese rol.'
  mutations:
    - command: 'CREATE ROLE n8n_user LOGIN; \password n8n_user'
      target: 'DataSQL PostgreSQL roles'
      backup: 'NO_APLICA'
    - command: 'CREATE DATABASE n8n_db OWNER n8n_user;'
      target: 'DataSQL PostgreSQL databases'
      backup: 'NO_APLICA'
  verification:
    - command: 'SELECT current_user, current_database();'
      expected: 'n8n_user | n8n_db'
    - command: 'SELECT datname, pg_get_userbyid(datdba) ... WHERE datname = n8n_db;'
      expected: 'n8n_db | n8n_user'
  postcondition: confirmed
  owner_files:
    - docs/services/n8n-guide.md
    - docs/services/datasql-guide.md
  derived_files:
    - agent/catalog/services/n8n/ficha.md
    - agent/catalog/services/n8n/compose.yml
    - agent/catalog/services/n8n/.env.example
  classification: INTEGRADO
  next_action: 'No recrear; usar la conexión existente para continuar con LobeHub.'

- incident_id: n8n-runtime-restart-loop
  service: n8n
  source: user-runtime-report
  symptom: 'Muchos reinicios y error de inicialización DB'
  root_cause: 'Faltaban rol/base o no coincidía la autenticación PostgreSQL.'
  mutations:
    - command: 'svc stop n8n'
      target: 'contenedor n8n'
      backup: 'NO_APLICA'
    - command: 'svc up n8n'
      target: 'contenedor n8n'
      backup: 'snapshot/backup antes del hardening posterior'
  verification:
    - command: 'svc health'
      expected: 'n8n con 0 reinicios observados'
    - command: 'curl /healthz'
      expected: 'HTTP 200'
  postcondition: confirmed
  owner_files:
    - docs/services/n8n-guide.md
  derived_files:
    - docker-nas/references/nas-context.md
    - AGENTS.md
  classification: INTEGRADO
  next_action: 'Mantener monitorización después de fijar la imagen.'

- incident_id: svc-global-env-permission-denied
  service: n8n
  source: user-runtime-report
  symptom: 'open /docker/.env: permission denied al ejecutar svc exec desde aadm'
  root_cause: 'El contexto de usuario no podía leer el .env global requerido por svc.'
  mutations: []
  verification:
    - command: 'sudo -i; dk n8n; svc ...'
      expected: 'El comando puede resolver el .env global'
  postcondition: partial
  owner_files:
    - docs/services/n8n-guide.md
    - .kiro/skills/nas-runtime-secrets/SKILL.md
  derived_files: []
  classification: INTEGRADO
  next_action: 'Conservar root cuando el procedimiento requiera leer el .env global.'
```

---

## No repetir

- No ejecutar `CREATE ROLE` otra vez sin comprobar primero si existe.
- No ejecutar `CREATE DATABASE n8n_db` otra vez: ya existe.
- No cambiar la contraseña del rol sin comparar con `DB_PASSWORD` efectivo.
- No mostrar contraseñas con `grep | cut`, `echo`, `printf` o `cat .env`.
- No hacer `source .env`.
- No usar `aipostgres`/`aiadmin` como usuario de n8n o LobeHub.
- No publicar `5432` ni `6379` en la LAN.
- No copiar el `start-all.sh` antiguo como patrón: usa rutas hardcodeadas y
  espera PostgreSQL por loopback, lo que no corresponde a consumidores Docker.
- No afirmar que el pin `2.36.7` está desplegado hasta recibir la salida de la
  verificación posterior.
