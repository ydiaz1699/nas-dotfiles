# Estructura Docker — guía completa

## Principios

1. Cada servicio vive en `$dkco/<servicio>/`
2. Crear **solo lo que el servicio realmente necesita**
3. `.env` solo para secretos reales (tokens, contraseñas, API keys)
4. Variables triviales (TZ, puertos, nombres) van inline en `compose.yml`
5. Aislamiento estricto: ningún servicio escribe en carpetas de otro
6. Nombres de servicio: `^[a-z0-9][a-z0-9._-]{0,63}$`

---

## Carpetas disponibles

| Carpeta | Cuándo crearla |
|---------|----------------|
| `config/` | el servicio tiene archivos de configuración |
| `data/` | el servicio persiste datos |
| `log/` | el servicio escribe logs fuera del contenedor |
| `.env` | hay secretos reales que no deben estar en el compose |

---

## Nombres de compose file (orden de preferencia)

1. `compose.yml` ← **preferido**
2. `compose.yaml`
3. `docker-compose.yml`
4. `docker-compose.yaml`

---

## Plantilla compose.yml

```yaml
services:
  <nombre>:
    image: <imagen>:<tag>
    container_name: <nombre>
    restart: unless-stopped
    environment:
      - TZ=America/La_Paz
    volumes:
      - ./data:/data
      - ./config:/config
    ports:
      - "XXXX:XXXX"
    networks:
      - <nombre>_net

networks:
  <nombre>_net:
    driver: bridge
```

---

## Plantilla con secretos (.env)

**compose.yml:**
```yaml
services:
  <nombre>:
    image: <imagen>:<tag>
    container_name: <nombre>
    restart: unless-stopped
    env_file: .env
    environment:
      - TZ=America/La_Paz
    volumes:
      - ./data:/data
    ports:
      - "XXXX:XXXX"
```

**.env:**
```env
API_KEY=tu_clave_secreta
DB_PASSWORD=contraseña_segura
```

---

## Ejemplos por tipo de servicio

### Simple (solo datos)
```
$dkco/grafana/
├── compose.yml
└── data/
```
```bash
mkdir -p $dkco/grafana/data
```

### Con configuración separada
```
$dkco/nginx/
├── compose.yml
├── config/
│   └── nginx.conf
└── data/
```
```bash
mkdir -p $dkco/nginx/{config,data}
```

### Con secretos
```
$dkco/nextcloud/
├── compose.yml
├── .env
├── config/
└── data/
```
```bash
mkdir -p $dkco/nextcloud/{config,data}
touch $dkco/nextcloud/.env
```

### Con logs externos
```
$dkco/traefik/
├── compose.yml
├── config/
├── data/
└── log/
```
```bash
mkdir -p $dkco/traefik/{config,data,log}
```

### Stack complejo (múltiples contenedores)
```
$dkco/monitoring/
├── compose.yml
├── grafana/
│   ├── config/
│   └── data/
└── prometheus/
    ├── config/
    │   └── prometheus.yml
    └── data/
```
```bash
mkdir -p $dkco/monitoring/{grafana/{config,data},prometheus/{config,data}}
```

---

## Flujo completo — nuevo servicio

```bash
# 1. Crear estructura
mkdir -p $dkco/<svc>/{config,data}

# 2. Crear compose
nano $dkco/<svc>/compose.yml

# 3. (Opcional) .env si hay secretos
nano $dkco/<svc>/.env

# 4. Navegar y levantar
dk <svc>
svc up <svc>

# 5. Verificar
svc ps <svc>
svc logs <svc>
svc health
```

---

## Reglas de red

- Cada servicio crea su red bridge aislada por defecto
- Para comunicación entre servicios: red compartida externa

```yaml
networks:
  shared_net:
    external: true
    name: shared_net
```

Crear una sola vez:
```bash
docker network create shared_net
```

---

## Backup y restauración

```bash
# Backup (volúmenes nombrados + bind mounts → tar.gz)
svc backup <svc>
# → $dkco/backups/<svc>_vol_<vol>_<timestamp>.tar.gz
# → $dkco/backups/<svc>_bind_<mount>_<timestamp>.tar.gz

# Listar backups
ls $dkco/backups/<svc>_*

# Restaurar (interactivo con fzf si disponible)
svc restore <svc>

# Rotación automática: conserva últimos $BACKUP_KEEP (default: 5)
```

---

## Convenciones de puertos

| Rango | Uso |
|-------|-----|
| 22, 53, 80, 443 | RESERVADOS — nunca asignar |
| 8100-8999 | Servicios nuevos del usuario |
| 1883, 8883 | MQTT (EMQX) |
| 1880 | Node-RED |
| 8123 | Home Assistant |
| 9090 | Prometheus |
| 3000 | Grafana |
