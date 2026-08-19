# Flowise — Guía de instalación y operación

> **Estado:** prueba inicial con PostgreSQL de DataSQL
> **Puerto LAN:** `8100` → contenedor `3000`
> **Red:** `db_net`
> **Base:** `flowise_db`
> **Imagen:** `flowiseai/flowise:latest`

## Qué se va a instalar

Flowise se instala como un compose independiente en `$dkco/flowise/`. No se añade
otro PostgreSQL ni Redis: la aplicación usa la base dedicada `flowise_db` dentro
del stack DataSQL, a través de la red externa `db_net`.

La imagen oficial usa el puerto interno `3000`, persiste su directorio de datos
en `/home/node/.flowise` y ofrece el endpoint de salud
`/api/v1/ping`. Estas decisiones se contrastaron con la documentación y el
compose oficial de Flowise:

- [Configuración de bases de datos de Flowise](https://docs.flowiseai.com/configuration/databases)
- [Ejecución en producción](https://docs.flowiseai.com/configuration/running-in-production)
- [Compose oficial de Flowise](https://github.com/FlowiseAI/Flowise/blob/main/docker/docker-compose.yml)

## Requisitos previos

1. DataSQL debe estar instalado y saludable.
2. La red externa `db_net` debe existir.
3. `$dkco/.env` debe contener `SERVER_IP` y `TZ`.
4. Debe existir `$dkco/_common.yml`, porque el compose hereda sus defaults.
5. El puerto `8100` debe estar libre.

Comprobar el estado sin tocar el NAS desde otro compose:

```bash
svc health datasql
svc port datasql 5432
```

PostgreSQL no debe tener un puerto publicado al host. `svc port datasql 5432`
puede no mostrar una publicación; la conectividad de Flowise será interna por
`db_net`.

## Instalación manual

### 1. Crear directorios

```bash
mkdir -p $dkco/flowise/data
```

### 2. Crear la base y el usuario dedicados

Entrar al cliente PostgreSQL usando el servicio de DataSQL; no reutilizar el
usuario administrativo para Flowise:

```bash
svc exec datasql postgres psql -U admin -d appdb
```

Dentro de `psql`, usar una contraseña segura y conservar exactamente la misma en
el `.env` de Flowise:

```sql
CREATE USER flowise_user WITH PASSWORD 'REEMPLAZAR_CON_PASSWORD_SEGURA';
CREATE DATABASE flowise_db OWNER flowise_user;
\q
```

Si el usuario o la base ya existen, no ejecutar de nuevo el `CREATE` sin revisar
primero su estado. No hacer `source $dkco/datasql/.env`: los secretos pueden
contener caracteres que alteren el shell.

### 3. Crear el archivo local de secretos

Crear `$dkco/flowise/.env` con los valores reales:

```env
FLOWISE_DB_NAME=flowise_db
FLOWISE_DB_USER=flowise_user
FLOWISE_DB_PASSWORD=REEMPLAZAR_CON_PASSWORD_SEGURA
FLOWISE_SECRETKEY_OVERWRITE=REEMPLAZAR_CON_HEX_ALEATORIO
```

`FLOWISE_SECRETKEY_OVERWRITE` debe conservarse mientras existan credenciales
cifradas en Flowise. No cambiarlo arbitrariamente después de la instalación.

Aplicar permisos después de crear el archivo:

```bash
chmod 600 $dkco/flowise/.env
```

### 4. Instalar el compose

Copiar el compose de catálogo a `$dkco/flowise/compose.yml` o usar el instalador
de DebMenux. La versión desplegada debe cambiar únicamente la ruta de
`extends.file` a `../_common.yml`; el compose del catálogo usa `../../_common.yml`.

### 5. Validar y levantar

```bash
dk flowise
svc config flowise
svc up flowise
```

### 6. Verificar en orden

```bash
svc ps flowise
svc logs flowise
svc stats flowise
```

La comprobación de salud debe llegar a `healthy` y el panel debe responder en:

```text
http://${SERVER_IP}:8100
```

Si el contenedor reinicia, revisar primero:

```bash
svc logs flowise
svc health datasql
svc ps datasql
```

No usar `depends_on` contra `datapostgres`: Flowise y DataSQL viven en composes
separados. La aplicación debe tolerar que DataSQL se levante antes o reintentarse
manualmente.

## Persistencia y permisos

El bind mount usa una ruta relativa al archivo `compose.yml`: `./data` siempre
se resuelve como `$dkco/flowise/data`, no como una carpeta externa ni como un
volumen Docker administrado. Por tanto, la estructura persistente queda así:

```text
$dkco/flowise/
├── compose.yml
├── .env
└── data/
    ├── logs/
    └── storage/
```

Dentro del contenedor, esa misma carpeta aparece como `/home/node/.flowise` y
contiene claves, logs, almacenamiento local y datos auxiliares. El montaje se
declara como bind explícito y `read_only: false` porque Flowise debe escribir en
esa carpeta:

```yaml
volumes:
  - type: bind
    source: ./data
    target: /home/node/.flowise
    read_only: false
```

No se añade `bind: propagation: rshared`: Flowise no crea ni consume montajes
anidados dentro de `data`. Esa opción sí es necesaria en File Browser porque
los USB se montan posteriormente dentro de `/NAS/USB` y deben propagarse al
contenedor sin recrearlo.

La imagen actual corre con un usuario no root; si hay errores de escritura,
crear primero la carpeta y después aplicar:

```bash
chown -R 1000:1000 $dkco/flowise/data
```

No aplicar `chown` antes de `mkdir`. No montar directorios de `$dkco/datasql/`
en Flowise.

## Backup y recuperación

El backup mínimo tiene dos partes:

1. Datos de aplicación:

   ```bash
   svc backup flowise
   ```

2. Dump de PostgreSQL `flowise_db`, realizado con el procedimiento de backup de
   DataSQL y guardado en `$dkco/datasql/data/postgres/backups/`.

Para recuperar, detener Flowise, restaurar primero la base dedicada y después el
contenido de `$dkco/flowise/data`; finalmente levantar y revisar logs. Probar la
restauración en una base temporal antes de reemplazar la base real.

## Seguridad de la prueba

- El panel está publicado en la LAN en el puerto `8100` solo para esta prueba.
- No publicar `5432` ni `6379` al host.
- Mantener `no-new-privileges` y `cap_drop: [ALL]`; si la imagen falla con el
  capability drop, registrar el error y revisar la excepción antes de quitarlo.
- No exponer Flowise a Internet sin reverse proxy y autenticación.
- Flowise permite herramientas personalizadas/MCP que pueden ejecutar acciones
  sensibles; habilitarlas solo para usuarios de confianza y revisar las opciones
  de seguridad antes de usar el servicio fuera del entorno de prueba.
- Medir consumo con `svc stats flowise` antes de cambiar los límites provisionales.

## Operación habitual

```bash
svc restart flowise
svc logs flowise
svc update flowise
svc backup flowise
svc recreate flowise
svc catalog-sync flowise
```

Después de cambiar labels o el compose, usar `svc recreate flowise` para que
Homepage reciba la configuración nueva y consultar `docs/dependency-map.md` para
la cascada documental.

## Diagnóstico rápido

| Síntoma | Revisión |
|---|---|
| Flowise no inicia | `svc logs flowise`; revisar variables `FLOWISE_DB_*` |
| Error de conexión PostgreSQL | `svc health datasql`, `svc ps datasql`, red `db_net`, hostname `datapostgres` |
| Reinicios por memoria | `svc stats flowise`; revisar el límite provisional de 1G |
| `permission denied` en `/home/node/.flowise` | crear la carpeta y luego `chown -R 1000:1000` |
| No aparece en Homepage | verificar labels y ejecutar `svc recreate flowise` |
| Se pierden credenciales cifradas | comprobar que `FLOWISE_SECRETKEY_OVERWRITE` no cambió y que `./data` persiste |

## Referencias

- [Documentación oficial de bases de datos](https://docs.flowiseai.com/configuration/databases)
- [Documentación oficial de producción](https://docs.flowiseai.com/configuration/running-in-production)
- [Repositorio oficial y compose](https://github.com/FlowiseAI/Flowise/tree/main/docker)
