# ioBroker — Guía Operativa de Producción

> **Estado:** configuración preparada en el repositorio; Kiro Web no ejecuta operaciones en el NAS.
> **Imagen:** `buanet/iobroker:v11.1.0`
> **Puerto LAN:** `8181` → puerto interno `8081`
> **Red:** `iot_net`
> **Persistencia:** `$dkco/iobroker/data` → `/opt/iobroker`

Esta guía documenta el despliegue real y las decisiones operativas de ioBroker en
este NAS. La configuración del catálogo es la fuente versionada; el runtime debe
copiarse al NAS y validarse allí antes de levantarlo.

## 1. Arquitectura y alcance

ioBroker es una aplicación **stateful**: su directorio `/opt/iobroker` contiene el
controller, configuración, adapters, estados y credenciales. Por eso se usa una
única instancia con un bind mount completo y no se levantan réplicas que escriban
simultáneamente en el mismo directorio.

La preparación para crecimiento consiste en:

- imagen versionada, nunca `latest`;
- límites iniciales de 1 CPU y 1 GiB, con reserva de 0.25 CPU y 256 MiB;
- backup y snapshot antes de actualizar o cambiar configuración;
- comunicación interna con EMQX mediante `emqx:1883` en `iot_net`;
- crecimiento vertical primero, midiendo con `svc stats iobroker`;
- escalado horizontal solo después de resolver coordinación soportada por ioBroker,
  separación de estado, proxy/load balancer y soporte explícito en `svc`.

No se habilitan inicialmente `network_mode: host`, `privileged`, dispositivos USB,
`db_net`, PostgreSQL/Redis ni `cap_drop: [ALL]`. Un adapter futuro puede cambiar
estas decisiones únicamente con una guía y pruebas específicas.

### 1.1 Auditoría de propuestas externas

Se revisaron varias propuestas generadas sin el contexto de este NAS. No se
incorporan por similitud textual: cada variante se comparó con la imagen oficial,
las convenciones de `nas-dotfiles`, el catálogo y el funcionamiento real de `svc`.

| Contenido propuesto | Estado | Decisión y motivo |
|---|---|---|
| `iobroker/iobroker:latest` | RECHAZADO | La imagen mantenida por buanet/ioBroker es `buanet/iobroker`; `latest` además es mutable. |
| `buanet/iobroker:v11.1.0` | INTEGRADO | Es la release estable verificada y queda fijada para reproducibilidad. |
| `/opt/iobroker` completo persistente | INTEGRADO | Es la ruta oficial que contiene configuración, adapters, estados y credenciales. |
| `IOBROKER_UID`, `IOBROKER_GID`, `USERID`, `GROUPID` | RECHAZADO | No son las variables documentadas por la imagen; se usan `SETUID` y `SETGID`. |
| `IOB_ADMINPORT`, `PERMISSION_CHECK` | INTEGRADO | Son variables documentadas y necesarias para controlar el puerto y permisos iniciales. |
| `TZ` repetido en `.env` local o `environment:` | RECHAZADO | Este NAS hereda `TZ` desde `$dkco/.env` mediante `env_file: [../.env, .env]`. |
| `iobroker_net` privada por servicio | RECHAZADO | ioBroker debe resolver `emqx` en la red externa compartida `iot_net`; no se crea otra red paralela. |
| `network_mode: host` desde el primer día | FUERA DE ALCANCE | La documentación oficial lo deja como opción según adapters que necesiten multicast/broadcast; MQTT básico no lo requiere. |
| `curl` contra `localhost:8081` como healthcheck | RECHAZADO | Se usa el script de salud distribuido por la imagen, que comprueba startup o `iobroker.js-controller`. |
| Carpeta `backup/` montada dentro de `/opt/iobroker` | PENDIENTE | Solo se añadirá si se configura Backitup para escribir allí; `svc backup iobroker` ya respalda el bind mount completo. |
| Redis para objects/states | PENDIENTE | La imagen soporta `IOB_OBJECTSDB_*`/`IOB_STATESDB_*`, pero requiere diseño, credenciales, pruebas y decidir si se reutiliza `dataredis` de DataSQL. |
| MariaDB, InfluxDB y Grafana | FUERA DE ALCANCE INICIAL | Son adapters/servicios opcionales. No se agregan bases ni dashboards sin un caso de uso y un contrato de backups. |
| `IOB_MULTIHOST=master/slave` | PENDIENTE | Es una ruta oficial de crecimiento, pero exige objects/states externos, topología, pruebas de descubrimiento y cambios de operación; no equivale a réplicas Compose. |
| `restart: always` y comandos Docker directos | RECHAZADO | El NAS usa `unless-stopped` vía `_common.yml` y opera Docker mediante `svc`. |

La referencia primaria para tags, variables, persistencia y redes es la
[documentación oficial de la imagen](https://docs.buanet.de/iobroker-docker-image/docs)
y su [README de tags soportados](https://github.com/buanet/ioBroker.docker/blob/main/docs/README_docker_hub_buanet.md).

## 2. Prerrequisitos en el NAS

No ejecutes estos pasos desde Kiro Web. Hazlos en una sesión SSH del NAS, con el
checkout de `nas-dotfiles` actualizado y la red Docker disponible.

La secuencia temporal obligatoria es **crear carpetas → crear archivos → aplicar
permisos → validar → levantar**.

### 2.1 Crear la carpeta de datos

```bash
mkdir -p $dkco/iobroker/data
```

### 2.2 Crear el `.env` local y copiar el compose

La configuración inicial no necesita secretos locales. Aun así, el archivo debe
existir porque el compose lo referencia:

```bash
touch $dkco/iobroker/.env

sed 's#file: ../../_common.yml#file: ../_common.yml#' \
  "$NAS_DOTFILES/agent/catalog/services/iobroker/compose.yml" \
  > $dkco/iobroker/compose.yml
```

Si el checkout usa otra ruta, entra al repositorio con `nasfk` y sustituye
`$NAS_DOTFILES` por la variable configurada en ese NAS; no copies una ruta fija de
otro equipo. El catálogo usa `../../_common.yml`; el runtime usa `../_common.yml`
porque `$dkco/_common.yml` está junto a las carpetas de servicios.

### 2.3 Aplicar permisos después de crear los archivos

```bash
chmod 600 $dkco/iobroker/.env
```

La imagen usa `SETUID=1000` y `SETGID=1000`. Si el primer arranque deja archivos
con un propietario incompatible, detén el servicio y corrige el árbol de datos
con el UID/GID efectivo de la imagen antes de repetirlo. No uses `chown` antes de
crear `$dkco/iobroker/data`.

### 2.4 Verificar o crear `iot_net`

ioBroker debe compartir `iot_net` con EMQX. Comprueba primero si existe y créala
solo si falta:

```bash
docker network inspect iot_net >/dev/null 2>&1 || docker network create iot_net
```

El puerto `8181` y la disponibilidad de `iot_net` deben confirmarse en el NAS.
Esta guía no reserva ni prueba esos recursos desde Kiro Web.

## 3. Validar y levantar

Valida la configuración resuelta antes de iniciar:

```bash
dk iobroker
svc config iobroker
```

Si la validación muestra un error de `extends`, confirma que el compose del runtime
usa `file: ../_common.yml`, no la ruta del catálogo. Cuando `iot_net`, el puerto y
los archivos sean correctos:

```bash
svc up iobroker
svc ps iobroker
svc logs iobroker
```

El healthcheck usa el script incluido por la imagen:

```bash
svc exec iobroker /opt/scripts/healthcheck.sh
```

El acceso inicial es `http://${SERVER_IP}:8181`. Completa el asistente de ioBroker
únicamente después de confirmar que el contenedor está saludable.

## 4. Configurar MQTT con EMQX

Desde la interfaz de ioBroker instala el adapter MQTT después del smoke test. Para
la conexión usa:

| Campo | Valor |
|---|---|
| Host | `emqx` |
| Puerto | `1883` |
| Transporte | MQTT sin TLS dentro de `iot_net` |
| Usuario/contraseña | credenciales MQTT creadas en EMQX |

No uses una IP fija entre contenedores. Si el adapter necesita TLS, configura los
certificados y el puerto seguro de EMQX como una decisión separada; no abras
`db_net` para resolver una necesidad MQTT.

Los adapters de Zigbee, Z-Wave, USB o descubrimiento multicast pueden requerir
`devices:`, permisos concretos o `network_mode: host`. No los agregues por
anticipación: documenta el hardware, prueba el adapter y modifica el compose con
backup previo.

## 5. Backups y recuperación

Los datos críticos son todo `$dkco/iobroker/data`, el `.env` local y el compose.
Los adapters y su configuración forman parte de `/opt/iobroker`; no hagas backups
parciales de una sola subcarpeta.

Antes de cambios de imagen o configuración:

```bash
svc snapshot iobroker
svc backup iobroker
```

`svc snapshot` guarda la configuración ligera (compose y `.env`); `svc backup`
comprime el bind mount de datos en el directorio de backups configurado por el
CLI y verifica el archivo tar. Conserva también una copia segura del `.env` local
si cambia en el futuro: contiene secretos de adapters aunque el compose inicial no
los requiera.

### Recuperación

1. Detén o bloquea el servicio si está activo.
2. Crea `$dkco/iobroker/data` y vuelve a crear el `.env` antes de restaurar.
3. Restaura el archivo de datos con `svc restore iobroker` y selecciona el backup
   de tipo `bind` correspondiente.
4. Verifica que el compose mantiene `buanet/iobroker:v11.1.0`, `iot_net` y el
   puerto interno `8081`.
5. Levanta con `svc up iobroker` y revisa `svc ps`, `svc logs` y el healthcheck.
6. Si cambiaste UID/GID por una imagen o adapter, corrige los permisos antes de
   abrir la interfaz.

La recuperación no debe combinar una actualización de imagen con una restauración
sin comprobar primero la compatibilidad de los adapters.

## 6. Actualizaciones

No uses `latest` ni automatizaciones que actualicen la imagen sin revisión.
La secuencia recomendada es:

```bash
svc snapshot iobroker
svc backup iobroker
# editar la etiqueta de imagen a una versión previamente verificada
svc config iobroker
svc update iobroker
svc ps iobroker
svc logs iobroker
svc stats iobroker
```

La versión inicial queda fijada en `v11.1.0`. Una actualización debe cambiar la
etiqueta de forma explícita, probar adapters críticos y conservar un rollback
posible. Si falla, restaura primero la configuración con `svc rollback iobroker`
y recupera los datos solo si es necesario.

## 7. Escalabilidad y límites conocidos

`container_name: iobroker`, el puerto publicado y el directorio persistente hacen
que `svc scale` no sea una estrategia válida para esta instancia. Dos containers
con el mismo bind mount pueden corromper configuración y estado; dos directorios
separados tampoco crean por sí solos un cluster ioBroker coherente.

La imagen documenta una alternativa denominada **multihost**, mediante
`IOB_MULTIHOST=master` o `IOB_MULTIHOST=slave`, junto con configuración externa de
objects y states (`IOB_OBJECTSDB_*` y `IOB_STATESDB_*`). Eso no debe confundirse
con levantar réplicas idénticas de Compose: requiere una topología de datos,
credenciales, resolución entre nodos, puertos/adapters compatibles y un
procedimiento probado de backup y recuperación. En este NAS queda como fase
posterior; inicialmente se mantienen objects y states en JSONL local persistente.

Para evaluar escalado futuro se necesitan, como mínimo:

1. validar el modelo multihost con una instancia master y una slave aisladas;
2. decidir si el backend será Redis de DataSQL o una topología dedicada, sin
   exponer `6379` al host;
3. separar claramente estado compartido, configuración y estado local;
4. documentar proxy/load balancer, sesiones, healthchecks y rollback;
5. añadir soporte explícito en `svc` y probar adapters, backup y recuperación con
   el hardware real.

Hasta entonces, escala verticalmente solo después de observar CPU/RAM y mantén una
sola instancia con backups verificados.

## 8. Troubleshooting

### `extends` no se encuentra

El catálogo y el runtime usan rutas distintas. El catálogo debe tener
`../../_common.yml`; el runtime en `$dkco/iobroker` debe tener `../_common.yml`.
Corrige el archivo generado y vuelve a ejecutar `svc config iobroker`.

### Healthcheck falla durante el primer arranque

ioBroker instala o inicializa componentes en el primer arranque. Revisa:

```bash
svc ps iobroker
svc logs iobroker
svc exec iobroker /opt/scripts/healthcheck.sh
```

No reemplaces el healthcheck por `curl` sin comprobar la imagen: se usa el script
interno distribuido por `buanet/iobroker`.

### No conecta al broker MQTT

Comprueba que ambos containers están en `iot_net`, que el host es `emqx` y que
las credenciales pertenecen a un usuario MQTT válido de EMQX. No uses `localhost`:
desde ioBroker eso apunta al propio contenedor.

### El adapter necesita USB o multicast

No añadas `privileged` como primera respuesta. Identifica el dispositivo o protocolo,
lee la documentación del adapter, toma `svc snapshot iobroker` y aplica el permiso
mínimo probado. Si requiere host networking, documenta la pérdida de aislamiento y
valida el impacto en el puerto `8181`.

## Fuentes externas

- [Docker Hub — buanet/iobroker](https://hub.docker.com/r/buanet/iobroker)
- [Repositorio oficial de la imagen](https://github.com/buanet/ioBroker.docker)

Contenido externo consultado y reescrito de forma resumida para esta guía; no se
reproducen bloques extensos de las fuentes.
