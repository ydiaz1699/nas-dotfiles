# Guía de Servicio — Google Antigravity CLI (`agy`) en el NAS

> Asistente agéntico oficial de Google en terminal (TUI) ejecutado en contenedor Docker
> aislado bajo demanda, con capacidades autónomas avanzadas, subagentes, background tasks
> y control por lenguaje natural sobre los servicios del NAS mediante el protocolo MCP.

---

## 1. Arquitectura y Principios de Diseño

Google Antigravity CLI (`agy`) se ejecuta en el NAS dentro de un contenedor Docker aislado,
heredando la arquitectura de seguridad probada en el servidor:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ NAS Host (Debian 13)                                                        │
│                                                                             │
│  $aadm/.local/bin/agy-nas ──── (symlink) ───┐                               │
│  $aadm/.local/bin/mcp-build-agy ── (symlink) ┼┐                             │
│                                             │ │                             │
│  $dkco/agy-cli/                             │ │                             │
│  ├── bin/agy-nas <──────────────────────────┘ │                             │
│  ├── bin/mcp-build <──────────────────────────┘                             │
│  ├── nextdns.env, n8n.env, jdownloader.env, karakeep.env, gemini.env        │
│  │                                                                          │
│  └── Contenedor: agy-cli (agy-cli-nas:local, network_mode: host)            │
│      ├── /opt/agy/bin/agy    (binario oficial fuera del volumen)            │
│      ├── /opt/nextdns-venv   (Python 3.14 venv para nextdns-mcp)            │
│      ├── /opt/jdownloader-venv (Python 3.14 venv para proyec_jdw2)          │
│      └── /home/agy <── volumen bind `./data`                                │
│           └── .gemini/antigravity-cli/settings.json                         │
│                                                                             │
│      Servidores MCP conectados:                                             │
│      ├── rclone-mcp  ─── HTTP ──▶ daemon rclone-rcd (:5572)                 │
│      ├── nextdns-mcp ─── HTTPS ─▶ api.nextdns.io (multi-cuenta)             │
│      ├── n8n-mcp     ─── HTTP ──▶ n8n (:5678 en 192.168.1.200)             │
│      ├── jdownloader ─── HTTPS ─▶ api.jdownloader.org (My.JDownloader)      │
│      └── karakeep    ─── HTTP ──▶ karakeep (:3400 en 192.168.1.200)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Características Clave
- **Sin contaminación en el host**: Las herramientas y dependencias (Python 3.14, Node.js, compiladores) viven dentro de la imagen.
- **Bajo Demanda (`.no-boot`)**: No se ejecuta en segundo plano durante el arranque; se activa solo cuando el usuario ejecuta `agy-nas` en la terminal.
- **Red `network_mode: host`**: Permite comunicación directa con `localhost:5572` (rclone) e instancias en la LAN (`192.168.1.200`), sin puentes lentos de red ni túneles innecesarios.
- **Seguridad de Secretos**: Los tokens y claves de API nunca se guardan en el archivo `settings.json`; se resuelven dinámicamente como variables de entorno inyectadas por el wrapper.

---

## 2. Métodos de Autenticación en Servidor Headless

Para que el CLI funcione en el NAS sin entorno gráfico, existen dos opciones:

### Opción A: API Key de Google AI Studio (Recomendada para Servidores)
Es el método más robusto y desatendido:
1. Obtén tu clave en [Google AI Studio](https://aistudio.google.com/).
2. Guárdala en `$dkco/agy-cli/gemini.env`:
   ```bash
   GEMINI_API_KEY=AIzaSy...
   ```
3. El wrapper `agy-nas` la inyecta automáticamente. No expira por inactividad de sesión.

### Opción B: Flujo de Dispositivo (OAuth / Device Code)
1. Ejecutas dentro del contenedor:
   ```bash
   agy auth login
   ```
2. La terminal mostrará una URL y un código de verificación.
3. Abres la URL en el navegador de tu ordenador personal, autorizas tu cuenta y la sesión queda guardada en el volumen persistente `./data`.

---

## 3. Servidores MCP Integrados

El archivo `settings.json` de Antigravity CLI contiene los 5 servidores modulares:

| Servidor | Motor | Comunicación | Función |
|---|---|---|---|
| **`rclone`** | Node.js (`npx rclone-mcp-server`) | stdio ➔ `http://localhost:5572` | 98 herramientas: sincronización remota, gestión de nube y montajes en `/mnt`. |
| **`nextdns-infinix`** | Python 3.14 (`/opt/nextdns-venv`) | stdio ➔ HTTPS `api.nextdns.io` | Control de bloqueo y listas para el teléfono personal. |
| **`nextdns-papa`** | Python 3.14 (`/opt/nextdns-venv`) | stdio ➔ HTTPS `api.nextdns.io` | Control de listas de protección para la cuenta familiar. |
| **`n8n`** | Node.js (`npx n8n-mcp`) | stdio ➔ `http://192.168.1.200:5678` | Gestión, consulta de nodos y creación de workflows. |
| **`jdownloader`** | Python 3.14 (`/opt/jdownloader-venv`) | stdio ➔ HTTPS My.JDownloader | Control de descargas y resolución de captchas. |
| **`karakeep`** | Node.js (`npx @karakeep/mcp`) | stdio ➔ `http://192.168.1.200:3400` | Búsqueda semántica y etiquetado de marcadores. |

---

## 4. Despliegue en el NAS (Paso a Paso)

### Paso 1: Crear directorios en el NAS
```bash
mkdir -p $dkco/agy-cli/{bin,data}
mkdir -p $dkco/agy-cli/data/.gemini/antigravity-cli/mcp_tools
touch $dkco/agy-cli/.no-boot
```

### Paso 2: Copiar archivos desde nas-dotfiles
```bash
cp $NAS_DOTFILES/agent/catalog/services/agy-cli/Dockerfile $dkco/agy-cli/
cp $NAS_DOTFILES/agent/catalog/services/agy-cli/compose.yml $dkco/agy-cli/
cp $NAS_DOTFILES/agent/catalog/services/agy-cli/bin/* $dkco/agy-cli/bin/
chmod +x $dkco/agy-cli/bin/*

# Copiar trozos modulares de MCPs
cp $NAS_DOTFILES/agent/catalog/services/agy-cli/mcp_tools/*.json \
   $dkco/agy-cli/data/.gemini/antigravity-cli/mcp_tools/

# Crear enlace simbólico global
ln -sf $dkco/agy-cli/bin/agy-nas $aadm/.local/bin/agy-nas
```

### Paso 3: Configurar Secretos (`chmod 600`)
Copiar los archivos `.env` (o reutilizar los existentes de Kiro):
```bash
cp $dkco/kiro-cli/*.env $dkco/agy-cli/ 2>/dev/null || true
chmod 600 $dkco/agy-cli/*.env
```

### Paso 4: Construir la imagen y fijar permisos
```bash
dk agy-cli
svc build agy-cli

# Permisos uid 1000:
chown -R 1000:1000 $dkco/agy-cli/data

# Ensamblar configuración MCP:
$dkco/agy-cli/bin/mcp-build
```

### Paso 5: Ejecutar
```bash
agy-nas
```
Al iniciar, puedes comprobar las herramientas MCP escribiendo:
```text
/mcp
```
Verás listados los servidores `rclone`, `nextdns`, `n8n`, `jdownloader` y `karakeep` listos para ser utilizados por el agente.
