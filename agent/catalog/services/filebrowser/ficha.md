# filebrowser

## Metadata

| Campo | Valor |
|-------|-------|
| **nombre** | filebrowser |
| **imagen** | filebrowser/filebrowser:latest |
| **descripción** | Explorador de archivos web para el NAS |
| **puerto** | 8085 → 80 (HTTP) |
| **protocolo** | http |
| **categoría** | archivos |
| **aliases** | filebrowser, files, explorador |

## Servicios

| Servicio | Imagen | Puerto |
|----------|--------|--------|
| filebrowser | filebrowser/filebrowser:latest | 8085:80 |

## Volúmenes

| Host | Contenedor | Tipo | Nota |
|------|-----------|------|------|
| `./config` | `/config` | bind | configuración + DB SQLite |
| `/NAS` | `/srv` | bind (**:rshared**) | archivos servidos — propaga mounts USB en tiempo real |

## Variables de entorno

### Requeridas (.env local)

| Variable | Descripción |
|----------|-------------|
| `FILEBROWSER_USER` | Usuario admin para widget de Homepage |
| `FILEBROWSER_PASSWORD` | Contraseña admin para widget de Homepage |

### Globales (../.env → $dkco/.env)

| Variable | Descripción |
|----------|-------------|
| `SERVER_IP` | IP del NAS (para labels de Homepage) |
| `TZ` | Timezone (America/La_Paz) |

## Redes

Sin red Docker personalizada (usa bridge default).

## Notas

- Corre como `root` (`user: "0:0"`) para acceso completo a `/NAS`
- La base de datos SQLite se guarda en `/config/database.db`
- Labels configuradas para integración con Homepage (dashboard)
- El bind mount `/NAS` → `/srv` requiere que `/NAS` exista en el host
- **`bind.propagation: rshared` es OBLIGATORIO** — sin él, los mounts de USB automount que aparecen dentro de `/NAS/USB/` no son visibles para el contenedor
- Puerto 8085 elegido para evitar conflictos con otros servicios web
- USBs se montan en `/NAS/USB/usb-<dispositivo>` via usb-automount y aparecen en la UI automáticamente (sin recrear contenedor)

## docs_url

docs/services/filebrowser-guide.md
