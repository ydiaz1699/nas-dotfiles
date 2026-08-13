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

| Host | Contenedor | Tipo |
|------|-----------|------|
| `./config` | `/config` | bind (configuración + DB) |
| `/NAS` | `/srv` | bind (archivos servidos) |

## Variables de entorno

### Requeridas (.env)

| Variable | Descripción |
|----------|-------------|
| `FILEBROWSER_USER` | Usuario admin para widget de Homepage |
| `FILEBROWSER_PASSWORD` | Contraseña admin para widget de Homepage |

### Fijas (inline)

| Variable | Valor |
|----------|-------|
| `TZ` | America/La_Paz |

## Redes

Sin red Docker personalizada (usa bridge default).

## Notas

- Corre como `root` (`user: "0:0"`) para acceso completo a `/NAS`
- La base de datos SQLite se guarda en `/config/database.db`
- Labels configuradas para integración con Homepage (dashboard)
- El bind mount `/NAS:/srv` requiere que `/NAS` exista en el host
- Puerto 8085 elegido para evitar conflictos con otros servicios web

## docs_url

docs/services/filebrowser-guide.md
