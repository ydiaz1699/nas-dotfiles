# Guía: LobeHub server/database en el NAS

> **Estado:** archivos preparados en el repositorio; todavía no es una
> instalación confirmada en el NAS porque esta sesión no ejecutó `svc` contra el
> servidor. No afirmar `lobehub_user`, `lobehub_db`, RustFS ni el contenedor como
> existentes hasta completar la verificación de la sección 10.
>
> Esta guía no repite ni recrea `n8n_user`/`n8n_db`. LobeHub usa una identidad
> PostgreSQL nueva y dedicada: `lobehub_user` / `lobehub_db`.

## 1. Decisión auditada y fuentes oficiales

La versión elegida es **LobeHub 2.2.14**, publicada el 16 de agosto de 2026.
La imagen se fija como `lobehub/lobehub:2.2.14` y además por el digest
multi-arquitectura confirmado en Docker Hub:
`sha256:1b571d94183ffee33759906b21e4c666d4bb5133a9f97f1266fc2a0b585b2b33`.

Fuentes oficiales consultadas y decisiones derivadas:

| Tema | Evidencia oficial | Decisión para este NAS |
|---|---|---|
| Imagen/tag | [Release v2.2.14](https://github.com/lobehub/lobehub/releases/tag/v2.2.14) y [tag de Docker Hub](https://hub.docker.com/layers/lobehub/lobehub/2.2.14/images/sha256-1b571d94183ffee33759906b21e4c666d4bb5133a9f97f1266fc2a0b585b2b33) | Pin `2.2.14` + digest; no usar `latest` |
| Variables | [Docker deployment](https://lobehub.com/docs/self-hosting/platform/docker) y [.env.example de v2.2.14](https://raw.githubusercontent.com/lobehub/lobehub/v2.2.14/docker-compose/deploy/.env.example) | Usar `DATABASE_URL`, secretos de auth, S3, Redis y `INTERNAL_APP_URL`; no copiar `POSTGRES_PASSWORD` del PostgreSQL incluido por upstream |
| PostgreSQL | La [guía oficial de Docker](https://lobehub.com/docs/self-hosting/platform/docker) y la migración observada de LobeHub usan ParadeDB/pgvector/pg_search | Reutilizar `datapostgres:5432` de DataSQL, crear `lobehub_user`/`lobehub_db` y precrear administrativamente `vector` y `pg_search` dentro de `lobehub_db`; nunca elevar el usuario de aplicación |
| Redis | La [guía oficial de Redis](https://lobehub.com/docs/self-hosting/advanced/redis) lo declara opcional; con `REDIS_URL` aporta sesiones/cache | Reutilizar `dataredis:6379` de DataSQL, con `REDIS_PASSWORD` existente y prefijo `lobehub`; no crear otro Redis |
| S3/RustFS | La [guía oficial S3](https://lobehub.com/docs/self-hosting/advanced/s3) y la [guía de knowledge base](https://lobehub.com/docs/self-hosting/advanced/knowledge-base) lo requieren para archivos, imágenes y knowledge base en la versión server/database | Sí instalar RustFS separado; no agregarlo al compose de DataSQL |
| SearXNG | La [guía oficial de búsqueda online](https://lobehub.com/docs/self-hosting/advanced/online-search) lo presenta como un proveedor opcional | No incluirlo en esta primera instalación; añadirlo solo si se habilita búsqueda web |
| Puerto | La [guía oficial Docker Compose](https://lobehub.com/docs/self-hosting/platform/docker-compose) muestra LobeHub en `3210` | Publicar `3210:3210` en LAN durante esta fase |
| Persistencia | El compose oficial persiste RustFS en `/data`; la DB externa conserva el esquema; LobeHub no necesita un bind mount propio en el despliegue oficial | Persistir `./data/rustfs`; respaldar además `lobehub_db` y `bucket.config.json` |
| Healthcheck | El compose oficial comprueba RustFS, PostgreSQL y Redis; no publica un endpoint HTTP de salud de LobeHub. Su Dockerfile v2.2.14 copia Node a `/bin/node` y define `PORT=3210` | Usar un healthcheck local con Node contra la raíz HTTP; validarlo en el NAS antes de tratarlo como evidencia |
| Recursos | La documentación Docker Compose oficial indica mínimo 2 cores, 4 GB RAM, 20 GB; recomienda 4+ cores, 8 GB y 50+ GB según uploads | El T20 tiene 2 cores/8 GB: cumple el mínimo, no el recomendado. LobeHub limita a 1.5 CPU/2 GB y RustFS a 0.5 CPU/512 MB; medir antes de endurecer más |

El compose oficial incluye PostgreSQL, Redis, RustFS, `rustfs-init` y SearXNG.
Este compose del NAS elimina PostgreSQL y Redis propios porque DataSQL ya es el
stack operativo único, conserva RustFS porque S3 sí es parte funcional de la
versión server/database y omite SearXNG porque la búsqueda online no es
obligatoria.

> Contenido externo consultado y reescrito de forma resumida; no se copian
> bloques extensos de las fuentes originales.

## 2. Arquitectura final

```text
LAN
 ├── http://${SERVER_IP}:3210 ── lobehub:3210
 └── http://${SERVER_IP}:9000 ── lobehub-rustfs:9000 (S3/browser)
                                  127.0.0.1:9001 (consola local)

 db_net (externa, existente)
 ├── datapostgres:5432 ── lobehub_db / lobehub_user
 └── dataredis:6379 ──── prefijo lobehub, REDIS_PASSWORD compartida

 lobe_storage (privada del compose)
 ├── lobehub:3210
 ├── lobehub-rustfs:9000
 └── rustfs-init (crea bucket y política GET)
```

Decisiones de aislamiento:

- `db_net` es externa y no se crea ni se elimina desde este compose.
- `lobe_storage` es una red privada del stack con nombre físico explícito para que RustFS no entre en la red de bases. Se justifica porque LobeHub necesita hablar con su S3 privado.
- El registro de cuentas queda restringido por `AUTH_ALLOWED_EMAILS`; no iniciar el servicio con una lista vacía.
- No hay `depends_on` contra `datapostgres` ni `dataredis`: pertenecen a otro
  compose. Se valida su salud antes de levantar LobeHub.
- RustFS publica el endpoint S3 en la LAN porque la documentación oficial avisa
  que el navegador no puede resolver `http://rustfs:9000`. La consola `9001`
  queda limitada a loopback y no es necesaria para el funcionamiento.
- `bucket.config.json` permite `s3:GetObject` anónimo únicamente para los
  objetos de `lobe`. Esto permite que el navegador/LLM recupere archivos, pero
  implica que cualquier cliente con acceso a la LAN que conozca una URL puede
  leer esos objetos. Si esa política no es aceptable, detenerse y decidir una
  estrategia de proxy/auth antes de usar uploads.

## 3. Requisitos y preflight

Antes de crear directorios o archivos, desde el contexto con permisos para que
`svc` lea los `.env` locales:

```bash
svc health
svc ps datasql
svc net
svc port-map
nas
disk
```

Continuar solo si:

- `datapostgres` y `dataredis` están saludables.
- `db_net` existe.
- Los puertos `3210` y `9000` están libres.
- `AUTH_ALLOWED_EMAILS` está definido con al menos una cuenta autorizada.
- `$dkco/_common.yml` y `$dkco/.env` existen.
- Se entiende que `9000` es un endpoint S3 de LAN y no una consola admin.

No pegar en GitHub ni en el chat la salida de `svc config`, porque puede
contener secretos interpolados.

## 4. Preparar el runtime y continuar desde aquí

Si ya ejecutaste el preflight de la sección 3 y tienes una instalación parcial
(o ya creaste `$dkco/lobehub`), **no borres ni sobrescribas archivos existentes**.
Este bloque crea la carpeta y copia solo los artefactos que todavía falten. La
única mutación permitida sobre un `compose.yml` existente es normalizar la ruta
conocida de `extends.file` del catálogo al runtime. Después continúa en la
sección 5 para completar o verificar el `.env`; todavía no ejecutes `svc up`.

El despliegue usa estos artefactos:

```text
$dkco/lobehub/
├── compose.yml
├── .env                         # secretos, modo 600
├── bucket.config.json           # política no secreta de lectura S3
└── data/
    └── rustfs/                  # objetos de LobeHub
```

Ejecuta el bloque completo desde el directorio local del repositorio
`nas-dotfiles`. Las salidas solo indican archivos, nunca imprimen secretos:

```bash
(
  set -e

  test -d "$NAS_DOTFILES"
  test -f "$NAS_DOTFILES/agent/catalog/services/lobehub/compose.yml"
  test -f "$NAS_DOTFILES/agent/catalog/services/lobehub/.env.example"
  test -f "$NAS_DOTFILES/agent/catalog/services/lobehub/bucket.config.json"
  test -f "$dkco/.env"
  test -f "$dkco/_common.yml"

  # (1) Carpetas antes de archivos.
  mkdir -p "$dkco/lobehub/data/rustfs"

  # (2) No sobrescribir una instalación parcial existente.
  [[ -e "$dkco/lobehub/compose.yml" ]] || \
    cp "$NAS_DOTFILES/agent/catalog/services/lobehub/compose.yml" \
       "$dkco/lobehub/compose.yml"
  [[ -e "$dkco/lobehub/bucket.config.json" ]] || \
    cp "$NAS_DOTFILES/agent/catalog/services/lobehub/bucket.config.json" \
       "$dkco/lobehub/bucket.config.json"
  [[ -e "$dkco/lobehub/.env" ]] || \
    cp "$NAS_DOTFILES/agent/catalog/services/lobehub/.env.example" \
       "$dkco/lobehub/.env"

  # El catálogo está dos niveles más abajo; el runtime solo uno.
  if grep -q 'file: ../../_common.yml' "$dkco/lobehub/compose.yml"; then
    sed -i 's|file: ../../_common.yml|file: ../_common.yml|g' \
      "$dkco/lobehub/compose.yml"
  elif ! grep -q 'file: ../_common.yml' "$dkco/lobehub/compose.yml"; then
    printf 'extends.file no coincide con catálogo ni runtime; detenerse.\n' >&2
    exit 1
  fi

  # (3) Verificar archivos; los permisos del secreto se aplican en la sección 5.
  test -s "$dkco/lobehub/compose.yml"
  test -s "$dkco/lobehub/.env"
  test -s "$dkco/lobehub/bucket.config.json"
)
status=$?
if (( status != 0 )); then
  printf 'No se pudo preparar el runtime de LobeHub; no continuar.\n' >&2
else
  printf 'Runtime de LobeHub preparado; continuar en la sección 5.\n'
fi
```

La modificación de `extends.file` es necesaria porque en el catálogo es
`../../_common.yml`, pero en `$dkco/lobehub/` debe ser `../_common.yml`. Si el
runtime ya contenía esa ruta, el bloque no la cambia.

### Permisos del bind mount de RustFS

RustFS ejecuta el proceso como el usuario no root con UID `10001`. El directorio
host `data/rustfs` debe existir antes de aplicar permisos y debe pertenecer a ese
UID; si queda propiedad de `root` con permisos `755`, RustFS puede iniciar pero
no escribir `/data` y termina con `Permission denied (os error 13)`. Esto fue el
fallo observado durante el primer `svc up`.

La secuencia correcta es: **crear la carpeta → copiar los archivos → aplicar
propietario/permisos → levantar el servicio**. Ejecuta el bloque siguiente después
del bloque de preparación y antes de `svc up`:

```bash
if [[ ! -d "$dkco/lobehub/data/rustfs" ]]; then
  printf 'Falta el directorio data/rustfs; no aplicar permisos.\n' >&2
else
  stat -c 'Antes: %n | uid=%u gid=%g modo=%a' "$dkco/lobehub/data/rustfs"

  chown -R 10001:10001 "$dkco/lobehub/data/rustfs"
  chmod -R u+rwX,go-rX "$dkco/lobehub/data/rustfs"

  stat -c 'Después: %n | uid=%u gid=%g modo=%a' "$dkco/lobehub/data/rustfs"
fi
```

La salida esperada es `uid=10001` y un modo que permita lectura/escritura al
propietario. Este `chown` solo aplica al almacenamiento persistente de RustFS;
no lo ejecutes sobre `$dkco/datasql`, `$dkco/lobehub/.env` ni directorios de otro
servicio. La referencia oficial de [instalación de RustFS en contenedor](https://docs.rustfs.com/en/installation/container/docker) también exige
que el directorio host montado en `/data` sea propiedad del UID `10001`.

### No exponer `RUSTFS_SECRET_KEY` en la línea de comandos

El compose inicial pasaba `RUSTFS_SECRET_KEY` como argumento
`--secret-key`. RustFS lo reflejó en el log de arranque, por lo que ese secreto
quedó expuesto durante el diagnóstico de este fallo. El compose corregido usa
`RUSTFS_ACCESS_KEY` y `RUSTFS_SECRET_KEY` únicamente mediante `environment:` y
arranca con `/data`; no debe aparecer `--secret-key` en `command:`.

Si el runtime se copió antes de esta corrección, detén el proyecto y aplica la
normalización siguiente después de actualizar el repositorio:

```bash
svc stop lobehub

python3 - "$dkco/lobehub/compose.yml" <<'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
newline = os.linesep
old = newline.join([
    "    command:",
    "      - --access-key",
    "      - lobehub",
    "      - --secret-key",
    "      - ${RUSTFS_SECRET_KEY}",
    "      - /data",
]) + newline
new = newline.join([
    "    command:",
    "      - /data",
]) + newline
if old not in text:
    if "      - --secret-key" + newline in text:
        raise SystemExit("Se encontró --secret-key en un formato no reconocido; no modificar")
else:
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(text.replace(old, new, 1))
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
PY
```

Como el secreto apareció en los logs compartidos, genera un
`RUSTFS_SECRET_KEY` nuevo antes del primer arranque exitoso. El cambio no borra
`data/rustfs`; RustFS todavía no llegó a iniciar correctamente:

```bash
python3 - "$dkco/lobehub/.env" <<'PY'
import os
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1])
lines = path.read_text().splitlines()
updated = []
found = False
value = secrets.token_hex(32)
for line in lines:
    if line.startswith("RUSTFS_SECRET_KEY="):
        updated.append(f"RUSTFS_SECRET_KEY={value}")
        found = True
    else:
        updated.append(line)
if not found:
    updated.append(f"RUSTFS_SECRET_KEY={value}")
temporary = path.with_name(path.name + ".tmp")
try:
    temporary.write_text(os.linesep.join(updated) + os.linesep)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
finally:
    if temporary.exists():
        temporary.unlink()
PY
chmod 600 "$dkco/lobehub/.env"
```

No compartas de nuevo el valor ni `svc logs lobehub` completo. En instalaciones
futuras, los secretos que aparecen en variables de entorno no deben imprimirse
en logs ni en salidas pegadas al chat.

```bash
svc stop lobehub
chown -R 10001:10001 "$dkco/lobehub/data/rustfs"
chmod -R u+rwX,go-rX "$dkco/lobehub/data/rustfs"
```

No borres `data/rustfs`, no ejecutes `docker prune` y no cambies secretos para
resolver un error de permisos. El contenido persistente debe conservarse.

## 5. Completar el `.env` con configuración interactiva y protegerlo

El `.env` se copia desde `.env.example`; no se recomienda crear un archivo vacío
con `touch`, porque los actualizadores no deben depender de que existan claves
que el usuario todavía no haya creado. Si el bloque anterior detectó un `.env`
existente, lo conserva y solo modifica las claves indicadas explícitamente.

El contenido siguiente es una referencia de las claves esperadas; no pegues
secretos reales en el repositorio ni en el chat. Para una instalación nueva, los
bloques interactivos de esta sección sustituyen el ejemplo localmente, por lo que
no es necesario abrir `nano` para configurar el correo, los secretos o `JWKS_KEY`.

```env
# Permitir solo estas cuentas, separadas por comas; no dejar vacío en LAN.
AUTH_ALLOWED_EMAILS=usuario@ejemplo.invalid

# PostgreSQL dedicado de LobeHub en DataSQL.
LOBE_DB_PASSWORD=__pega_aqui__

# Copiar localmente el valor de $dkco/datasql/.env; no generar otro Redis.
REDIS_PASSWORD=__pega_aqui__

# Generar valores nuevos y conservarlos estables para esta instalación.
KEY_VAULTS_SECRET=__pega_aqui__
AUTH_SECRET=__pega_aqui__
JWKS_KEY=__pega_aqui__

# Secreto de la cuenta RustFS usada por LobeHub y rustfs-init.
RUSTFS_SECRET_KEY=__pega_aqui__
```

### Generar los secretos locales sin imprimirlos

Ejecutar este bloque durante una instalación nueva o para reanudar una
instalación **antes del primer arranque**. Conserva los secretos propios que ya
sean reales y solo genera los que estén vacíos o sean `__pega_aqui__`. El
`REDIS_PASSWORD` de LobeHub nunca se genera: la fuente de verdad es siempre
`$dkco/datasql/.env`.

Después del primer arranque no lo ejecutes como una prueba, porque no debe rotar
identidades ya usadas. Si se necesita cambiar una credencial después del
arranque, debe hacerse mediante un procedimiento de rotación coordinado.

La lista `AUTH_ALLOWED_EMAILS` debe ser no vacía. Se configura de forma
interactiva, sin abrir un editor y sin dejar el correo de ejemplo:

```bash
if (
  read -r -p 'Correo(s) autorizado(s), separados por comas: ' LOBE_ALLOWED_EMAILS

  if [[ -z "$LOBE_ALLOWED_EMAILS" || "$LOBE_ALLOWED_EMAILS" == *'__pega_aqui__'* ]]; then
    printf 'AUTH_ALLOWED_EMAILS no puede quedar vacío ni contener placeholders.\n' >&2
    exit 1
  fi

  export LOBE_ALLOWED_EMAILS
  python3 - "$dkco/lobehub/.env" <<'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
value = os.environ["LOBE_ALLOWED_EMAILS"].strip()
lines = path.read_text().splitlines()
output = []
found = False

for line in lines:
    if line.startswith("AUTH_ALLOWED_EMAILS="):
        output.append(f"AUTH_ALLOWED_EMAILS={value}")
        found = True
    else:
        output.append(line)

if not found:
    output.append(f"AUTH_ALLOWED_EMAILS={value}")

temporary = path.with_name(path.name + ".tmp")
try:
    temporary.write_text(os.linesep.join(output) + os.linesep)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
finally:
    if temporary.exists():
        temporary.unlink()
PY

  status=$?
  unset LOBE_ALLOWED_EMAILS
  if (( status != 0 )); then
    printf 'No se pudo guardar AUTH_ALLOWED_EMAILS.\n' >&2
    exit "$status"
  fi
)
then
  printf 'AUTH_ALLOWED_EMAILS configurado localmente.\n'
else
  printf 'No se modificó AUTH_ALLOWED_EMAILS.\n' >&2
fi
```

LobeHub permite registrar cualquier cuenta si `AUTH_ALLOWED_EMAILS` queda vacío.
Para los secretos propios se usa un bloque Python heredoc; no usar un
`python3 -c` multilínea porque el shell puede convertir `\n` en saltos de línea
dentro del código y producir un `SyntaxError` antes de escribir el archivo. Los
bloques están dentro de una subshell para que un fallo no cierre la sesión SSH.

Los bloques Python de esta guía usan `os.linesep` y `chr(10)` en lugar de
literales Python como `"\\n"`. En el terminal del NAS, ciertos pegados pueden
convertir ese escape en un salto de línea dentro del heredoc y producir
`SyntaxError: unterminated string literal`. No reemplaces estos bloques por
`python3 -c` ni reintroduzcas `"\\n"` dentro de ellos.

```bash
if (
  set -u
  ENV_FILE="$dkco/lobehub/.env"

  test -s "$ENV_FILE"
  REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"

  if [[ -z "$REDIS_PASSWORD" ]]; then
    printf 'No se encontró REDIS_PASSWORD en %s/datasql/.env.\n' "$dkco" >&2
    exit 1
  fi

  export REDIS_PASSWORD
  python3 - "$ENV_FILE" <<'PY'
import os
import re
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(f"No existe {path}")

secret_keys = (
    "LOBE_DB_PASSWORD",
    "KEY_VAULTS_SECRET",
    "AUTH_SECRET",
    "RUSTFS_SECRET_KEY",
)
all_keys = ("REDIS_PASSWORD",) + secret_keys
lines = path.read_text().splitlines()
existing = {}
for line in lines:
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        if key in all_keys:
            existing[key] = value

values = {"REDIS_PASSWORD": os.environ["REDIS_PASSWORD"]}
for key in secret_keys:
    old = existing.get(key, "").strip()
    if old and old != "__pega_aqui__":
        if key == "LOBE_DB_PASSWORD" and not re.fullmatch(r"[0-9a-fA-F]+", old):
            raise SystemExit(
                "LOBE_DB_PASSWORD existente no es hexadecimal; no se sobrescribe"
            )
        values[key] = old
    else:
        values[key] = secrets.token_hex(32)

output = []
seen = set()
for line in lines:
    key = (
        line.split("=", 1)[0]
        if "=" in line and not line.lstrip().startswith("#")
        else None
    )
    if key in values:
        output.append(f"{key}={values[key]}")
        seen.add(key)
    else:
        output.append(line)

for key in all_keys:
    if key not in seen:
        output.append(f"{key}={values[key]}")

final_values = {}
for line in output:
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        if key in all_keys:
            final_values[key] = value

if any(not final_values.get(key) or final_values[key] == "__pega_aqui__" for key in all_keys):
    raise SystemExit("No se pudieron completar todas las claves de secretos")

temporary = path.with_name(path.name + ".tmp")
try:
    temporary.write_text(os.linesep.join(output) + os.linesep)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
finally:
    if temporary.exists():
        temporary.unlink()
PY

  status=$?
  unset REDIS_PASSWORD ENV_FILE
  if (( status != 0 )); then
    printf 'No se pudo actualizar el .env; no continuar.\n' >&2
    exit "$status"
  fi
)
then
  chmod 600 "$dkco/lobehub/.env"
  printf 'Secretos locales preparados sin imprimir sus valores.\n'
else
  printf 'No se modificaron los secretos locales.\n' >&2
fi
```

El bloque copia siempre el `REDIS_PASSWORD` vigente de DataSQL, pero conserva los
secretos propios que ya sean reales y solo genera los que todavía sean vacíos o
`__pega_aqui__`. Para mantener la reconciliación segura, un
`LOBE_DB_PASSWORD` existente debe ser hexadecimal; si no lo es, el bloque se
detiene sin sobrescribirlo y exige una rotación deliberada documentada.

### Fuentes de verdad y sincronización obligatoria

Estas reglas evitan la discrepancia que ocurre cuando el `.env` contiene una
contraseña nueva pero el servidor todavía conserva otra:

| Credencial | Fuente de verdad | Acción durante esta instalación |
|---|---|---|
| `REDIS_PASSWORD` | `$dkco/datasql/.env` | Copiarla al `.env` de LobeHub; nunca generar otra ni crear otro Redis |
| `LOBE_DB_PASSWORD` | `$dkco/lobehub/.env` | Crear o sincronizar explícitamente la contraseña de `lobehub_user` |
| `PG_ADMIN_PASSWORD` | `$dkco/datasql/.env` | Usarla solo temporalmente para administrar PostgreSQL |
| `RUSTFS_SECRET_KEY` | `$dkco/lobehub/.env` | Usarla igual en RustFS, `rustfs-init` y LobeHub |

Generar `LOBE_DB_PASSWORD` en el archivo **no crea ni cambia automáticamente** la
contraseña de PostgreSQL. La guía debe ejecutar la reconciliación del rol en la
sección 6 antes de crear la base o levantar LobeHub. De la misma forma, copiar
`REDIS_PASSWORD` al nuevo `.env` solo funciona si se verifica con `redis-cli PING`.

`JWKS_KEY` es distinto: no es una contraseña aleatoria. Debe generarse con el
botón **Click button to generate** de la [sección oficial de JWKS_KEY](https://lobehub.com/docs/self-hosting/environment-variables/auth#jwks_key). El valor debe ser un
JSON JWKS con una clave privada RSA `RS256`; no usar el valor de un gist o de otra
instalación.

Solicitarlo de forma interactiva y validarlo antes de escribirlo. El generador
oficial entrega normalmente una línea JSON minificada; `read` captura una sola
línea para no guardar accidentalmente un valor incompleto. Si la validación falla,
el archivo permanece sin cambios y no se imprime un mensaje de éxito falso:

```bash
if (
  read -r -s -p 'Pega el JWKS_KEY nuevo; no se mostrará: ' JWKS_INPUT
  printf '\n'

  if [[ -z "$JWKS_INPUT" ]]; then
    printf 'JWKS_KEY vacío; no se modificó el archivo.\n' >&2
    exit 1
  fi

  export JWKS_INPUT
  python3 - "$dkco/lobehub/.env" <<'PY'
import base64
import json
import math
import os
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
raw = os.environ["JWKS_INPUT"]
if raw.startswith("JWKS_KEY="):
    raw = raw.split("=", 1)[1]
if chr(10) in raw or chr(13) in raw:
    raise SystemExit("JWKS_KEY debe ser un JSON de una sola línea")

try:
    document = json.loads(raw)
except json.JSONDecodeError as exc:
    raise SystemExit("JWKS_KEY no contiene JSON válido") from exc

keys = document.get("keys") if isinstance(document, dict) else None
required = {"d", "dp", "dq", "e", "n", "p", "q", "qi", "kty", "use", "kid", "alg"}
if not isinstance(keys, list) or len(keys) != 1 or not isinstance(keys[0], dict):
    raise SystemExit("JWKS_KEY debe contener exactamente una clave")

key = keys[0]
if not required.issubset(key) or key["kty"] != "RSA" or key["alg"] != "RS256" or key["use"] != "sig":
    raise SystemExit("JWKS_KEY no es una clave privada RSA RS256 válida")

rsa_fields = ("d", "dp", "dq", "e", "n", "p", "q", "qi")
components = {}
for field in rsa_fields:
    value = key[field]
    if not isinstance(value, str) or not value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise SystemExit(f"JWKS_KEY tiene un campo RSA inválido: {field}")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise SystemExit(f"JWKS_KEY tiene un campo RSA ilegible: {field}") from exc
    components[field] = int.from_bytes(decoded, "big")
    if components[field] <= 0:
        raise SystemExit(f"JWKS_KEY tiene un campo RSA vacío: {field}")

kid = key["kid"]
if not isinstance(kid, str) or not kid.strip():
    raise SystemExit("JWKS_KEY necesita un kid no vacío")
if components["e"] < 3 or components["n"] != components["p"] * components["q"]:
    raise SystemExit("JWKS_KEY tiene componentes RSA inconsistentes")
if components["dp"] != components["d"] % (components["p"] - 1):
    raise SystemExit("JWKS_KEY tiene dp inconsistente")
if components["dq"] != components["d"] % (components["q"] - 1):
    raise SystemExit("JWKS_KEY tiene dq inconsistente")
if components["qi"] != pow(components["q"], -1, components["p"]):
    raise SystemExit("JWKS_KEY tiene qi inconsistente")
if (components["d"] * components["e"]) % math.lcm(components["p"] - 1, components["q"] - 1) != 1:
    raise SystemExit("JWKS_KEY no corresponde a una clave RSA válida")

compact = json.dumps(document, separators=(",", ":"), ensure_ascii=True)
lines = path.read_text().splitlines()
positions = [index for index, line in enumerate(lines) if line.startswith("JWKS_KEY=")]
if len(positions) > 1:
    raise SystemExit(".env contiene más de una línea JWKS_KEY=")
updated = list(lines)
if positions:
    updated[positions[0]] = "JWKS_KEY=" + compact
else:
    updated.append("JWKS_KEY=" + compact)

temporary = path.with_name(path.name + ".tmp")
try:
    temporary.write_text(os.linesep.join(updated) + os.linesep)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
finally:
    if temporary.exists():
        temporary.unlink()
PY

  status=$?
  unset JWKS_INPUT
  if (( status != 0 )); then
    printf 'JWKS_KEY inválido; no se confirmó la configuración.\n' >&2
    exit "$status"
  fi
)
then
  chmod 600 "$dkco/lobehub/.env"
  printf 'JWKS_KEY validado y guardado localmente.\n'
else
  printf 'No se modificó JWKS_KEY.\n' >&2
fi
```

Verificar sin mostrar ningún secreto:

```bash
if ! (
  set -u
  ENV_FILE="$dkco/lobehub/.env"

  awk -F= '
  /^(LOBE_DB_PASSWORD|REDIS_PASSWORD|AUTH_ALLOWED_EMAILS|KEY_VAULTS_SECRET|AUTH_SECRET|JWKS_KEY|RUSTFS_SECRET_KEY)=/ {
    print $1 "=configured"
  }
  ' "$ENV_FILE"

  required_keys=(
    LOBE_DB_PASSWORD REDIS_PASSWORD AUTH_ALLOWED_EMAILS
    KEY_VAULTS_SECRET AUTH_SECRET JWKS_KEY RUSTFS_SECRET_KEY
  )
  for key in "${required_keys[@]}"; do
    mapfile -t matches < <(grep -E "^${key}=" "$ENV_FILE" || true)
    if (( ${#matches[@]} != 1 )); then
      printf 'Debe existir exactamente una línea para: %s.\n' "$key" >&2
      exit 1
    fi
    value="${matches[0]#*=}"
    if [[ -z "$value" || "$value" == '__pega_aqui__' ]]; then
      printf 'Falta o está vacío: %s.\n' "$key" >&2
      exit 1
    fi
  done

  if [[ "${value:-}" == 'usuario@ejemplo.invalid' ]] || \
     grep -q '^AUTH_ALLOWED_EMAILS=usuario@ejemplo.invalid$' "$ENV_FILE"; then
    printf 'Sustituye el correo de ejemplo por una cuenta autorizada real.\n' >&2
    exit 1
  fi
)
then
  printf 'El .env todavía no está completo; no continuar.\n' >&2
else
  chmod 600 "$dkco/lobehub/.env"
  printf 'Configuración local completa y protegida.\n'
fi
```

Este patrón (`read` interactivo → validación → escritura atómica → `unset` →
comprobación del estado) es el patrón reutilizable para futuros servicios que
necesiten recibir datos sensibles durante la instalación. Nunca se debe imprimir
el valor introducido ni asumir éxito porque el comando anterior terminó con un
mensaje parcial.

`SERVER_IP` y `TZ` no se duplican: llegan desde `$dkco/.env` mediante
`env_file: [../.env, .env]`.

## 6. Aprovisionar PostgreSQL sin repetir n8n

LobeHub requiere su propia identidad. No tocar `n8n_user`, `n8n_db`, `aiadmin`
ni `aipostgres` como identidad de aplicación. Los valores de esta instalación
son:

```text
APP_DB_USER=lobehub_user
APP_DB_NAME=lobehub_db
APP_DB_PASSWORD=LOBE_DB_PASSWORD del .env de LobeHub
```

Preflight ya ejecutado en la sección 3. Leer las credenciales administrativas
sin hacer `source` ni mostrarlas:

```bash
PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
APP_DB_PASSWORD="$(awk -F= '$1=="LOBE_DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/lobehub/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" || -z "$APP_DB_PASSWORD" ]]; then
  printf 'Falta una credencial necesaria; no se crea ni modifica nada.\n' >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB APP_DB_PASSWORD
  exit 1
fi
```

La contraseña de `LOBE_DB_PASSWORD` debe quedar sincronizada con el rol antes
de crear la base. La consulta siguiente es opcional para inspeccionar el estado;
si el rol no existe, el bloque de reconciliación posterior lo crea.

**Las consultas SQL solo se escriben cuando el prompt termina en `=#` o `=>`,
dentro de `psql`; nunca en el prompt `root@Nas ... #` de Bash.**

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`, consultar el estado si lo necesitas y salir antes de
continuar con el bloque automático:

```sql
SELECT rolname, rolcanlogin
FROM pg_roles
WHERE rolname = 'lobehub_user';
\q
```

No crees ni cambies el rol manualmente antes del bloque automático. Así la guía
usa un único camino idempotente y evita que `LOBE_DB_PASSWORD` y PostgreSQL
queden desincronizados.

### Reconciliar automáticamente el rol y su contraseña

Este es el camino canónico para una instalación nueva o parcial. Si
`lobehub_user` no existe, lo crea; si existe, sincroniza deliberadamente su
contraseña con `LOBE_DB_PASSWORD`. Solo afecta al rol dedicado de LobeHub, no a
`n8n_user`, `aiadmin` ni `aipostgres`.

El secreto viaja por stdin como SQL generado localmente. No se imprime ni se pasa
como argumento de `psql`. Como este es un flujo no interactivo, usa
`NAS_CLI=bash ... -T`: la implementación Bash permite pasar `-T` a Compose y
elimina la pseudo-TTY. No uses `psql -v`, `-U`, `-d` o `-c` después de la forma
Python de `svc exec`, porque el wrapper puede interpretarlos como opciones propias:

```bash
if [[ -z "${PG_ADMIN_PASSWORD:-}" || -z "${PG_ADMIN_USER:-}" ||
      -z "${PG_ADMIN_DB:-}" || -z "${APP_DB_PASSWORD:-}" ]]; then
  printf 'Faltan credenciales temporales; no se modifica el rol.\n' >&2
else
  export APP_DB_PASSWORD
  SQL_OUTPUT="$(mktemp)"

  python3 - <<'PY' | \
    NAS_CLI=bash svc exec datasql -T postgres \
      env PGPASSWORD="$PG_ADMIN_PASSWORD" \
          PGUSER="$PG_ADMIN_USER" \
          PGDATABASE="$PG_ADMIN_DB" \
      psql >"$SQL_OUTPUT" 2>&1
import os

password = os.environ["APP_DB_PASSWORD"]
if not password or password == "__pega_aqui__":
    raise SystemExit("LOBE_DB_PASSWORD vacío o placeholder")
if any(char not in "0123456789abcdefABCDEF" for char in password):
    raise SystemExit("LOBE_DB_PASSWORD debe ser hexadecimal")

print("\\set ON_ERROR_STOP on")
print("DO $$")
print("BEGIN")
print("  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lobehub_user') THEN")
print(f"    ALTER ROLE lobehub_user LOGIN PASSWORD '{password}';")
print("  ELSE")
print(f"    CREATE ROLE lobehub_user LOGIN PASSWORD '{password}';")
print("  END IF;")
print("END")
print("$$;")
PY

  pipeline_status=("${PIPESTATUS[@]}")
  unset APP_DB_PASSWORD

  if (( pipeline_status[0] != 0 || pipeline_status[1] != 0 )); then
    cat "$SQL_OUTPUT" >&2
    printf 'No se pudo sincronizar lobehub_user; no continuar.\n' >&2
  else
    printf 'lobehub_user creado o sincronizado con LOBE_DB_PASSWORD.\n'
  fi

  rm -f "$SQL_OUTPUT"
fi
```

Si el bloque informa éxito, la contraseña del rol y la del `.env` ya representan
la misma credencial. No ejecutes además `CREATE ROLE` ni `\password` a ciegas.
La variante interactiva `\password lobehub_user` queda reservada para un cambio
manual deliberado; una variable Bash no rellena ese prompt de `psql`.

Crear o verificar la base en **otra** sesión, fuera de una transacción:

```bash
svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE="$PG_ADMIN_DB" \
  psql
```

Dentro de `psql`, consultar primero:

```sql
SELECT datname, pg_get_userbyid(datdba) AS owner
FROM pg_database
WHERE datname = 'lobehub_db';
```

Si no existe:

```sql
CREATE DATABASE lobehub_db OWNER lobehub_user;
```

Si existe, no ejecutar `CREATE DATABASE` otra vez. Continuar solo si el owner
verificado es `lobehub_user`. No combinar `CREATE ROLE` y `CREATE DATABASE` en
una llamada o transacción. Salir con `\q`.

### Precrear `vector` y `pg_search` en la base de LobeHub

DataSQL proporciona `vector` y `pg_search`, pero PostgreSQL registra las
extensiones por base de datos. Que estén disponibles en la imagen o precargadas
con `shared_preload_libraries` no significa que existan dentro de
`lobehub_db`.

La migración real de LobeHub 2.2.14 ejecuta:

```sql
CREATE EXTENSION IF NOT EXISTS pg_search;
```

Si `pg_search` todavía no existe, `lobehub_user` recibe `must be superuser to
create a base type`. Ese error no indica una contraseña incorrecta ni justifica
elevar el usuario de LobeHub: `pg_search` debe crearse una vez con el usuario
administrativo antes de iniciar la aplicación. Después, la migración encuentra
la extensión existente y `lobehub_user` continúa siendo un rol de aplicación no
privilegiado.

Detén solo LobeHub antes de preparar las extensiones. No detengas DataSQL ni
borres `lobehub_db` o `data/rustfs`:

```bash
svc stop lobehub

PG_ADMIN_PASSWORD="$(awk -F= '$1=="POSTGRES_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_USER="$(awk -F= '$1=="POSTGRES_USER"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
PG_ADMIN_DB="$(awk -F= '$1=="POSTGRES_DB"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"

if [[ -z "$PG_ADMIN_PASSWORD" || -z "$PG_ADMIN_USER" || -z "$PG_ADMIN_DB" ]]; then
  printf 'Faltan credenciales administrativas de DataSQL; no continuar.\n' >&2
  unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB
  exit 1
fi

svc exec datasql postgres \
  env PGPASSWORD="$PG_ADMIN_PASSWORD" \
      PGUSER="$PG_ADMIN_USER" \
      PGDATABASE=lobehub_db \
  psql
```

En el prompt de `psql` (`lobehub_db=#`), ejecuta el SQL siguiente. El usuario
administrativo crea las extensiones; el usuario de aplicación no recibe ningún
privilegio adicional:

```sql
SELECT current_user, current_database();

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_search;

SELECT extname, extversion, pg_get_userbyid(extowner) AS owner
FROM pg_extension
WHERE extname IN ('vector', 'pg_search')
ORDER BY extname;

SELECT rolname, rolsuper, rolcreaterole, rolcreatedb,
       rolreplication, rolbypassrls
FROM pg_roles
WHERE rolname = 'lobehub_user';
\q
```

La consulta de extensiones debe mostrar `vector` y `pg_search`. La consulta del
rol debe mostrar todos los indicadores de privilegio como `f` (`false`), en
particular `rolsuper = f`. Si alguna extensión no aparece o la creación falla,
detente la instalación y conserva el error; no ejecutes
`ALTER ROLE lobehub_user SUPERUSER`.

Después de salir de `psql`, limpia las credenciales temporales y levanta solo
LobeHub:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB
svc up lobehub
svc ps lobehub
svc health
```

`pg_cron` no se habilita en `lobehub_db`: DataSQL lo mantiene en la base
administrativa configurada por `cron.database_name`. Si `CREATE EXTENSION` falla
incluso con el usuario administrativo, verifica `pg_available_extensions` y la
salud de DataSQL; no concedas privilegios permanentes a `lobehub_user`.

Verificar el login dedicado en una tercera sesión usando la contraseña de
LobeHub, no la administrativa. El bloque de reconciliación limpió la variable
por seguridad, por lo que se vuelve a leer desde el archivo local sin imprimirla:

```bash
(
  trap 'unset APP_DB_PASSWORD' EXIT
  APP_DB_PASSWORD="$(awk -F= '$1=="LOBE_DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/lobehub/.env")"

  if [[ -z "$APP_DB_PASSWORD" || "$APP_DB_PASSWORD" == '__pega_aqui__' ]]; then
    printf 'Falta una LOBE_DB_PASSWORD válida; no probar el login.\n' >&2
  else
    svc exec datasql postgres \
      env PGPASSWORD="$APP_DB_PASSWORD" \
          PGUSER=lobehub_user \
          PGDATABASE=lobehub_db \
      psql
  fi
)
```

En `psql`:

```sql
SELECT current_user, current_database();
\q
```

La salida esperada es `lobehub_user | lobehub_db`. Limpiar secretos temporales:

```bash
unset PG_ADMIN_PASSWORD PG_ADMIN_USER PG_ADMIN_DB APP_DB_PASSWORD
```

Las extensiones `vector` y `pg_search` deben existir en `lobehub_db` antes de
la migración y se crean con las credenciales administrativas. `lobehub_user`
solo ejecuta las migraciones de sus tablas y nunca se convierte en
superusuario. `pg_cron` permanece únicamente en la base configurada por
`cron.database_name`.

## 7. Compose final

Crear `$dkco/lobehub/compose.yml` con el contenido completo de
`agent/catalog/services/lobehub/compose.yml`. La única diferencia entre ambos
contextos es `extends.file`:

- catálogo: `../../_common.yml`;
- NAS: `../_common.yml`.

El archivo del catálogo es la configuración final auditada y está incluido en
esta PR junto con `bucket.config.json`; no copiar el compose oficial sin estos
ajustes:

- elimina PostgreSQL/Redis propios y sus puertos;
- añade `db_net` externa y el usuario/base dedicados;
- añade autenticación al Redis compartido;
- fija LobeHub 2.2.14 por digest;
- añade RustFS S3 persistente y `rustfs-init` versionados;
- crea `lobe_storage` con nombre físico explícito, sin depender del prefijo del proyecto;
- no publica la consola RustFS `9001` en la LAN;
- no usa `depends_on` contra DataSQL;
- añade healthcheck local compatible con la imagen `scratch` de LobeHub;
- añade labels de Homepage y límites iniciales de recursos.

Crear también `$dkco/lobehub/bucket.config.json` copiando el archivo del
catálogo. El bucket debe existir antes de que LobeHub intente guardar objetos.

## 8. Validar configuración y dependencias antes de levantar

Primero verifica que el `REDIS_PASSWORD` copiado desde DataSQL realmente
funciona. Esta comprobación es una precondición; no esperes a que LobeHub esté
levantado para descubrir una contraseña Redis incorrecta:

```bash
if (
  DATA_REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
  LOBE_REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/lobehub/.env")"

  if [[ -z "$DATA_REDIS_PASSWORD" || -z "$LOBE_REDIS_PASSWORD" ||
        "$DATA_REDIS_PASSWORD" != "$LOBE_REDIS_PASSWORD" ]]; then
    printf 'REDIS_PASSWORD de LobeHub no coincide con DataSQL; no continuar.\n' >&2
    exit 1
  fi

  export REDIS_PASSWORD="$DATA_REDIS_PASSWORD"
  svc exec datasql redis \
    env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
  status=$?
  unset REDIS_PASSWORD DATA_REDIS_PASSWORD LOBE_REDIS_PASSWORD
  exit "$status"
)
then
  printf 'Redis verificado con la credencial sincronizada de DataSQL.\n'
else
  printf 'Redis no responde o sus credenciales no coinciden; no continuar.\n' >&2
fi
```

Debe devolver `PONG`. El bloque limpia la variable incluso si el comando
termina con error; no crear otro Redis ni generar otra contraseña.

```bash
dk lobehub
svc config lobehub
svc port-map
```

`svc config` no debe mostrar variables sin resolver. No compartir su salida:
puede contener `DATABASE_URL`, `JWKS_KEY`, `REDIS_PASSWORD` o credenciales S3.
Si el wrapper local necesita leer el `.env` global, ejecutar desde el contexto
con permisos adecuado; el handoff de n8n documenta el `permission denied` que
puede aparecer desde un usuario sin acceso a `$dkco/.env`.

## 9. Levantar en el orden real

Después de directorios → archivos → propietario/permisos → validación de
credenciales y configuración:

```bash
# Si el proyecto ya tuvo un arranque fallido, detener el bucle de reinicio.
svc stop lobehub

# Repetir la corrección de permisos sin borrar el almacenamiento.
chown -R 10001:10001 "$dkco/lobehub/data/rustfs"
chmod -R u+rwX,go-rX "$dkco/lobehub/data/rustfs"

svc pull lobehub
svc up lobehub
svc ps lobehub
svc logs lobehub
svc health
svc stats lobehub
```

Si es la primera ejecución y los contenedores todavía no existen, `svc stop`
puede informar que no hay nada que detener; continúa con `chown`, `svc pull` y
`svc up`. No uses `svc down` como reparación genérica: conservar el directorio
bind-mounted y sus permisos es lo importante.

La primera ejecución debe mostrar, en el contenedor LobeHub, migración de base
completada y el servidor Next.js listo. `rustfs-init` debe terminar con código 0
tras crear `lobe`; no debe imprimir secretos. Si RustFS vuelve a mostrar
`Permission denied (os error 13)`, detente y revisa primero `stat`/`chown` del
paso 4; no cambies contraseñas ni borres `data/rustfs`. No usar `svc update`
sobre otro servicio y no detener DataSQL como parte de esta instalación.

## 10. Verificación posterior y criterios de aceptación

La instalación solo puede declararse operativa si se verifican todos estos
puntos en el NAS:

1. `svc ps lobehub` muestra `lobehub` y `lobehub-rustfs` activos; el init terminó
   correctamente.
2. `svc health` muestra LobeHub y RustFS saludables; si el healthcheck de
   LobeHub falla por una diferencia de imagen, registrar el motivo antes de
   cambiarlo, no desactivarlo silenciosamente.
3. `curl -fsS http://${SERVER_IP}:3210` devuelve HTTP válido desde el NAS/LAN y
   la UI carga en el navegador.
4. `curl -fsS http://${SERVER_IP}:9000/health` devuelve éxito y el endpoint S3
   es accesible desde el navegador de la LAN.
5. Los logs contienen migración completada, sin errores de PostgreSQL, Redis o
   S3 y sin reinicios repetidos.
6. La sesión de prueba de la sección 6 devuelve
   `lobehub_user | lobehub_db`.
7. La sesión administrativa de la sección 6 confirma que las extensiones
   `vector` y `pg_search` existen dentro de `lobehub_db`, ambas fueron creadas
   antes de iniciar LobeHub y `lobehub_user` conserva `rolsuper = false`. `pg_cron`
   no se habilita en esta base.
8. Redis responde `PONG` usando el secreto existente, sin crear otro contenedor:

   ```bash
   REDIS_PASSWORD="$(awk -F= '$1=="REDIS_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/datasql/.env")"
   svc exec datasql redis env REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli PING
   unset REDIS_PASSWORD
   ```

9. Después del primer login, validar un chat y, si se habilita, una imagen o
   archivo para comprobar realmente S3; el bucket debe conservar objetos en
   `$dkco/lobehub/data/rustfs`.
10. `svc port-map` no muestra `5432` ni `6379` publicados por LobeHub y `9001`
    solo está en loopback.
11. Medir `svc stats lobehub` y `svc stats datasql` antes de ajustar límites.

La presencia de `db_net` por sí sola no prueba que la aplicación use la base o
Redis correctos: deben coincidir compose, variables, logs y consultas runtime.

## 11. Backup, actualización y recuperación

Antes del primer arranque y antes de actualizar:

```bash
svc snapshot lobehub
```

Respaldar el almacenamiento de objetos y la base dedicada. `svc backup lobehub`
protege el bind mount de RustFS según la implementación del NAS; el dump
PostgreSQL debe hacerse aparte con credenciales temporales no impresas. El
procedimiento lógico siguiente escribe el dump en el directorio de backups de
DataSQL y no versiona el secreto:

```bash
BACKUP_TS="$(date +%Y%m%d-%H%M%S)"
DUMP_FILE="$dkco/datasql/data/postgres/backups/lobehub_db_${BACKUP_TS}.sql"
APP_DB_PASSWORD="$(awk -F= '$1=="LOBE_DB_PASSWORD"{print substr($0,index($0,"=")+1); exit}' "$dkco/lobehub/.env")"

if [[ -z "$APP_DB_PASSWORD" ]]; then
  printf 'No se encontró LOBE_DB_PASSWORD en %s/lobehub/.env.\n' "$dkco" >&2
  unset BACKUP_TS DUMP_FILE APP_DB_PASSWORD
  exit 1
fi

if ! svc exec datasql postgres \
  env PGPASSWORD="$APP_DB_PASSWORD" \
      PGUSER=lobehub_user \
      PGDATABASE=lobehub_db \
  pg_dump --format=plain --no-owner --no-privileges > "$DUMP_FILE"; then
  printf 'El dump de LobeHub falló; se elimina solo el archivo parcial.\n' >&2
  rm -f "$DUMP_FILE"
  unset BACKUP_TS DUMP_FILE APP_DB_PASSWORD
  exit 1
fi

printf 'Dump lógico creado en %s.\n' "$DUMP_FILE"
unset BACKUP_TS DUMP_FILE APP_DB_PASSWORD
```

Este comando debe ejecutarse con DataSQL saludable y después de verificar que
el archivo no está vacío. La restauración sobre `lobehub_db` no se automatiza en
esta guía: es una operación potencialmente destructiva que debe planificarse,
confirmar el dump y detener LobeHub antes de usar `psql --set ON_ERROR_STOP=1`.
El procedimiento de dump está documentado pero no fue ejecutado en este entorno;
verificarlo en el NAS antes de tratarlo como backup probado. Seguir también el
procedimiento de backups de [`docs/services/datasql-guide.md`](datasql-guide.md)
y no presentar un tar del bind mount como sustituto de un dump lógico.

Para una actualización de LobeHub, primero consultar las release notes y cambiar
el tag/digest en catálogo y compose; luego validar `svc config`, tomar snapshot,
crear dump, usar `svc pull lobehub` y verificar migraciones. No borrar
`$dkco/lobehub/data/rustfs` ni el contenido de `lobehub_db` para resolver un fallo.

Si una migración falla:

1. conservar logs y el tag/digest usado;
2. no ejecutar `rm -rf data`;
3. detenerse y revisar compatibilidad de release, PostgreSQL y RustFS;
4. recuperar desde backup/snapshot solo con confirmación explícita;
5. repetir las verificaciones de la sección 10.

## 12. Fuera de alcance y pendientes

- No se instala SearXNG en esta primera versión; la búsqueda web es opcional.
- No se instala proxy/TLS ni se afirma que la exposición HTTP en LAN sea apta
  para Internet; la lista de `AUTH_ALLOWED_EMAILS` es obligatoria antes del
  primer arranque.
- No se crea un script DebMenux en esta PR; `debmenu install lobehub` queda
  fuera de alcance y esta propuesta se despliega manualmente siguiendo esta
  guía.
- No se modifica ni verifica n8n; `n8n_user`, `n8n_db` y su clave de cifrado se
  conservan intactos.
- No se instala un PostgreSQL, Redis o RustFS dentro de DataSQL.
- La política pública de lectura S3 debe revisarse si se manejarán documentos
  sensibles.
- Debe hacerse la prueba runtime de healthcheck, recursos, migración, uploads y
  backups antes de marcar la ficha como `protected` o decir que el servicio está
  operativo.
