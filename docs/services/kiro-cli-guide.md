# Guía de Servicio — Kiro CLI en el NAS

> Asistente de inteligencia artificial en terminal (TUI) ejecutado en contenedor Docker
> aislado bajo demanda, con control por lenguaje natural sobre los servicios y herramientas
> del NAS mediante el protocolo Model Context Protocol (MCP).

---

## 1. Arquitectura y Decisiones de Diseño

Para no contaminar el sistema base Debian del NAS ni dejar residuos de Node.js o paquetes
globales en el host, Kiro CLI se configuró bajo aislamiento estricto en Docker:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NAS Host (Debian 13)                                                        │
│                                                                             │
│  $aadm/.local/bin/kiro ─────── (symlink) ───┐                               │
│  $aadm/.local/bin/mcp-build ── (symlink) ───┼─┐                             │
│                                             │ │                             │
│  $dkco/kiro-cli/                            │ │                             │
│  ├── bin/kiro <─────────────────────────────┘ │                             │
│  ├── bin/mcp-build <──────────────────────────┘                             │
│  ├── nextdns.env, n8n.env, jdownloader.env, karakeep.env (chmod 600)        │
│  │                                                                          │
│  └── Contenedor: kiro-cli (kiro-cli-nas:local, network_mode: host)          │
│      ├── /opt/kiro/kiro-cli (binario oficial fuera del volumen)             │
│      ├── /opt/nextdns-venv  (Python 3.14 venv para nextdns-mcp)             │
│      ├── /opt/jdownloader-venv (Python 3.14 venv para proyec_jdw2)          │
│      └── /home/kiro <── volumen bind `./data`                               │
│           └── .kiro/settings/mcp.json (generado por mcp-build)              │
│                                                                             │
│      Servicios MCP conectados (stdio / LAN):                                │
│      ├── rclone-mcp  ─── HTTP ──▶ daemon rclone-rcd (:5572)                 │
│      ├── nextdns-mcp ─── HTTPS ─▶ api.nextdns.io (multi-cuenta)             │
│      ├── n8n-mcp     ─── HTTP ──▶ n8n (:5678 en 192.168.1.200)             │
│      ├── jdownloader ─── HTTPS ─▶ api.jdownloader.org (My.JDownloader)      │
│      └── karakeep    ─── HTTP ──▶ karakeep (:3400 en 192.168.1.200)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Principios Fundamentales
- **Aislamiento Total**: No requiere instalar paquetes de Node/npm ni Python 3.14 en el host.
- **Bajo Demanda (`.no-boot`)**: NO arranca al reiniciar el NAS. Es un contenedor interactivo (TUI) que se levanta solo cuando el administrador lo necesita (`kiro`) y se detiene automáticamente al salir.
- **Red `network_mode: host`**: Permite al contenedor alcanzar el daemon `rclone-rcd` en `localhost:5572` y servicios del NAS en su IP LAN (`192.168.1.200:5678`, `:3400`) sin exponer sockets Docker ni abrir puertos a internet.
- **Sin Docker Socket**: Ningún contenedor ni MCP tiene acceso a `/var/run/docker.sock`, protegiendo el host de ejecuciones no controladas.

---

## 2. Inventario de Archivos y Ubicaciones

| Archivo en Catálogo Git | Ubicación en Disco del NAS | Función |
|---|---|---|
| `agent/catalog/services/kiro-cli/Dockerfile` | `$dkco/kiro-cli/Dockerfile` | Construcción de la imagen Debian + Node + uv + venvs. |
| `agent/catalog/services/kiro-cli/compose.yml` | `$dkco/kiro-cli/compose.yml` | Definición de contenedor, volumen y modo host. |
| `agent/catalog/services/kiro-cli/bin/kiro` | `$dkco/kiro-cli/bin/kiro` | Wrapper de ejecución que inyecta variables `.env`. |
| `agent/catalog/services/kiro-cli/bin/mcp-build` | `$dkco/kiro-cli/bin/mcp-build` | Ensambla los trozos modulares en `mcp.json`. |
| `agent/catalog/services/kiro-cli/mcp_tools/*.json` | `$dkco/kiro-cli/data/.kiro/settings/mcp_tools/*.json` | Configuración individual por servidor MCP. |
| `agent/catalog/services/kiro-cli/permissions.yaml` | `$dkco/kiro-cli/data/.kiro/settings/permissions.yaml` | Reglas de auto-aprobación y confirmación V3. |
| `agent/catalog/services/kiro-cli/steering/*.md` | `$dkco/kiro-cli/data/.kiro/steering/*.md` | Directivas de idioma y mapa de usuarios NextDNS. |
| `agent/catalog/services/kiro-cli/.env.example` | `$dkco/kiro-cli/*.env` (reales) | Plantilla de credenciales y variables de entorno. |

---

## 3. Servidores MCP Integrados

### 1. Rclone (`mcp_tools/rclone.json`)
- **Protocolo**: `npx rclone-mcp-server@1.0.3` (stdio) hacia daemon `rclone-rcd` en `http://localhost:5572`.
- **Alcance**: 98 endpoints con `RCLONE_TOOLSETS=all` (gestión de remotes, sincronización, transferencias y montajes en `/mnt`).
- **Seguridad**: Contraseña inyectada dinámicamente desde `/docker/rclone-rcd/.env`.

### 2. NextDNS Multi-cuenta (`mcp_tools/nextdns.json`)
- **Protocolo**: Python 3.14 aislado (`/opt/nextdns-venv/bin/python -m nextdns_mcp.server`).
- **Alcance**: Dos servidores independientes (`nextdns-infinix` con perfil `2511f5` y `nextdns-papa` con perfil `2f6df5`) para no agotar la cuota mensual gratuita.
- **Steering**: El archivo `steering/nextdns-usuarios.md` dirige al asistente a utilizar el servidor correspondiente según el lenguaje natural.

### 3. n8n (`mcp_tools/n8n.json`)
- **Protocolo**: `npx n8n-mcp@2.89.0` (stdio) hacia la API REST en `http://192.168.1.200:5678`.
- **Alcance**: Conoce ~525 nodos, valida configuraciones y gestiona workflows directamente en el n8n del NAS.
- **Ajuste crítico**: `WEBHOOK_SECURITY_MODE=permissive` para permitir llamadas a IPs LAN privadas en modo host.

### 4. JDownloader (`mcp_tools/jdownloader.json`)
- **Protocolo**: Python 3.14 aislado (`/opt/jdownloader-venv/bin/jdownloader-mcp`).
- **Alcance**: Conexión lazy con la nube My.JDownloader (`JDownloader@Alex`) controlando descargas, enlaces y captchas vía NopeCHA.
- **Optimización de Build**: Soporta el argumento de Docker `JD_MCP_REF=$(date +%s)` para reconstruir la capa del MCP en ~2 minutos sin recompilar el resto de la imagen.

### 5. Karakeep (`mcp_tools/karakeep.json`)
- **Protocolo**: `npx @karakeep/mcp@0.34.0` (stdio) hacia la API REST en `http://192.168.1.200:3400`.
- **Alcance**: Consulta, creación, búsqueda semántica y etiquetado de marcadores de la biblioteca de Karakeep.

---

## 4. Gestión de Permisos V3 (`permissions.yaml`)

Kiro CLI V3 implementa control de acceso estricto con precedencia `deny > ask > allow`:
- **Auto-aprobadas (`allow`)**: Consultas de estado, búsquedas de nodos en n8n, lectura de enlaces en JDownloader, listados de remotes en rclone y métricas de NextDNS.
- **Confirmación requerida (`ask`)**: Operaciones destructivas o de modificación (borrar archivos, sincronizar carpetas rclone, crear/borrar workflows de n8n, apagar descargas o alterar listas de bloqueo DNS).

---

## 5. Procedimiento de Despliegue en el NAS

### Paso 1: Crear carpetas y enlaces en el NAS
```bash
# 1. Crear estructura en /docker/kiro-cli
mkdir -p $dkco/kiro-cli/{bin,data}
mkdir -p $dkco/kiro-cli/data/.kiro/{settings/mcp_tools,steering}
touch $dkco/kiro-cli/.no-boot

# 2. Copiar archivos desde el catálogo de nas-dotfiles
cp $NAS_DOTFILES/agent/catalog/services/kiro-cli/Dockerfile $dkco/kiro-cli/
cp $NAS_DOTFILES/agent/catalog/services/kiro-cli/compose.yml $dkco/kiro-cli/
cp $NAS_DOTFILES/agent/catalog/services/kiro-cli/bin/* $dkco/kiro-cli/bin/
chmod +x $dkco/kiro-cli/bin/*

cp $NAS_DOTFILES/agent/catalog/services/kiro-cli/mcp_tools/*.json $dkco/kiro-cli/data/.kiro/settings/mcp_tools/
cp $NAS_DOTFILES/agent/catalog/services/kiro-cli/permissions.yaml $dkco/kiro-cli/data/.kiro/settings/
cp $NAS_DOTFILES/agent/catalog/services/kiro-cli/steering/*.md $dkco/kiro-cli/data/.kiro/steering/

# 3. Enlaces simbólicos en el PATH del usuario
ln -sf $dkco/kiro-cli/bin/kiro $aadm/.local/bin/kiro
ln -sf $dkco/kiro-cli/bin/mcp-build $aadm/.local/bin/mcp-build
```

### Paso 2: Configurar Secretos (`chmod 600`)
Crear los archivos `.env` en `$dkco/kiro-cli/` a partir de las plantillas de `.env.example`:
```bash
chmod 600 $dkco/kiro-cli/*.env
```

### Paso 3: Construir la imagen y fijar permisos del volumen
```bash
dk kiro-cli
svc build kiro-cli

# Obligatorio para evitar error de permisos con uid 1000:
chown -R 1000:1000 $dkco/kiro-cli/data

# Ensamblar mcp.json
mcp-build
```

### Paso 4: Login y Uso
```bash
# Autenticación inicial (headless / device flow):
docker run -it --rm --network host -v $dkco/kiro-cli/data:/home/kiro kiro-cli-nas:local login --use-device-flow

# Lanzar sesión normal:
kiro
```

---

## 6. Puente de Migración a Google (Antigravity CLI `agy`)

Esta misma estructura sirve como base directa para la migración a Google:
- Los archivos en `mcp_tools/*.json` se reutilizan al 100%.
- El ensamblador `mcp-build` se adaptará para volcar la configuración hacia `mcp_config.json` de Google.
- El wrapper `$dkco/kiro-cli/bin/kiro` servirá de plantilla exacta para el nuevo ejecutable `$dkco/agy-cli/bin/agy-nas`.
