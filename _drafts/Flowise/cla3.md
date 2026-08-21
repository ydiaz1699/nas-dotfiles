Buen archivo — está bien alineado con tu estructura real (`_common.yml`, `../.env` global, labels de homepage, límites de recursos). Le faltan las variables de **Redis/queue mode** para que el worker funcione, y el worker en sí. Te dejo el compose completo actualizado a tu estilo:

```yaml
# Flowise — constructor visual de agentes y flujos LLM
# En el NAS, este archivo se despliega como $dkco/flowise/compose.yml.
services:
  flowise:
    extends:
      file: ../../_common.yml
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
    ports:
      - "8100:3000"
    volumes:
      # Ruta relativa al compose: $dkco/flowise/data -> /home/node/.flowise
      - type: bind
        source: ./data
        target: /home/node/.flowise
        read_only: false
    networks:
      - db_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/v1/ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
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
      file: ../../_common.yml
      service: _defaults
    image: flowiseai/flowise:latest
    container_name: flowise-worker
    env_file:
      - ../.env
      - .env
    environment:
      MODE: queue
      QUEUE_NAME: flowise-queue
      WORKER_CONCURRENCY: "5"
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
      FLOWISE_SECRETKEY_OVERWRITE: ${FLOWISE_SECRETKEY_OVERWRITE}
    volumes:
      # Mismo storage/secrets que el nodo principal
      - type: bind
        source: ./data
        target: /home/node/.flowise
        read_only: false
    networks:
      - db_net
    depends_on:
      - flowise
    cap_drop: [ALL]
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    entrypoint: /bin/sh -c "sleep 5; flowise worker"

networks:
  db_net:
    external: true
```

### Cambios respecto a tu versión

- Agregué `MODE: queue`, `QUEUE_NAME`, `REDIS_HOST/PORT/PASSWORD` al nodo `flowise` — sin esto el modo queue no arranca aunque tengas el worker corriendo.
- Nuevo servicio `flowise-worker`, mismo storage (`./data`), sin puerto expuesto (no necesita, no sirve HTTP), sin healthcheck de tipo web ni `homepage.*` labels (no es un servicio "visible").
- `depends_on: flowise` para que el nodo principal (que corre migraciones de DB al iniciar) esté listo primero.
- Límites de recursos más bajos para el worker (no sirve UI, solo ejecuta).

### Falta en tu `.env` (local de flowise, `$dkco/flowise/.env`)

```bash
FLOWISE_DB_NAME=flowise_db
FLOWISE_DB_USER=flowise_user
FLOWISE_DB_PASSWORD=<el que creaste en postgres>
FLOWISE_SECRETKEY_OVERWRITE=<openssl rand -hex 24>
```

Y confirmá que `REDIS_PASSWORD` ya está disponible vía tu `../.env` global (compartido con `datasql`) — si no está ahí, copialo desde `$dkco/datasql/.env`.

### Levantar y verificar

```bash
dk flowise
svc config flowise
svc up flowise
svc ps flowise            # deben aparecer flowise y flowise-worker healthy
svc logs flowise-worker | grep -i "redis\|queue\|error"
```

Si más adelante necesitás más capacidad: `svc scale flowise-worker s=3`.