# Guia de Instalacion — nas-dotfiles

Guia paso a paso para instalar el framework en un NAS nuevo o existente.

---

## Requisitos previos

| Requisito | Minimo | Verificar |
|-----------|--------|-----------|
| Debian/Ubuntu | 11+ | `cat /etc/os-release` |
| Bash | 4.2+ | `bash --version` |
| Docker | 24+ | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| Python | 3.9+ | `python3 --version` |
| Git | cualquiera | `git --version` |

### Opcionales (recomendados)

```bash
apt install eza fzf bat lm-sensors
```

| Paquete | Para que |
|---------|----------|
| `eza` | Reemplazo moderno de `ls` (colores, iconos) |
| `fzf` | Menu interactivo (`svc menu`, `dkf`, `admf`) |
| `bat` | Ver archivos con syntax highlighting |
| `lm-sensors` | Temperatura en el dashboard `nas` |

---

## Instalacion rapida (3 comandos)

```bash
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
./setup
```

Eso es todo. El script `./setup` detecta el entorno y lanza el mejor instalador:

1. Si hay Python + Rich + InquirerPy → **TUI moderno** (wizard interactivo)
2. Si hay Python pero faltan deps → ofrece instalarlas, si no puede → bash
3. Si no hay Python → **instalador bash** (funcional, menos bonito)

---

## Que pregunta el instalador

El wizard (TUI o bash) pregunta:

```
? Ruta de home [/home/tu-usuario]:     → donde navega tu comando rapido
? Variable $[tuus]:                     → nombre de la variable ($tuus)
? Comando [tuu]:                        → nombre del atajo (tuu → cd $tuus)
? Ruta datos Docker [/docker]:          → donde viven los servicios Docker
? Timezone [America/New_York]:          → zona horaria
? Provider IA:                          → gemini / bedrock / ollama / saltar
? GOOGLE_API_KEY:                       → (solo si elegiste Gemini)
? Configurar para root? [S/n]:          → agrega el framework a /root/.bashrc
? Instalar deps Python? [S/n]:          → pip install de requirements.txt
```

### Valores por defecto inteligentes

El instalador sugiere valores basados en tu usuario. Si tu usuario es `nicolas`:

```
Ruta:     /home/nicolas
Variable: $nico
Comando:  nic
```

Resultado: escribes `nic` y te lleva a `/home/nicolas`.

---

## Que hace el instalador

Paso a paso:

### 1. Detecta el sistema

Verifica OS, Docker, Python, Bash, timezone. Muestra una tabla con checkmarks.

### 2. Pregunta configuracion

Los valores de arriba. Todo tiene defaults razonables — puedes dar Enter en todo.

### 3. Copia a /nas-dotfiles

Si clonaste en otro lugar (ej: `/tmp`), copia todo a `/nas-dotfiles/`. Si ya esta ahi, no copia nada.

### 4. Genera .config/user.conf

```bash
NAV_HOME="/home/nicolas"
NAV_VAR="nico"
NAV_CMD="nic"
```

Este archivo controla la navegacion personalizada. Editalo manualmente si quieres cambiar despues.

### 5. Configura ~/.bashrc

Agrega 2 lineas al final de tu `.bashrc`:

```bash
# nas-dotfiles shell framework
export NAS_DOTFILES="/nas-dotfiles"
source "$NAS_DOTFILES/shell/init.sh"
```

Si ya estaban, no las duplica. Antes hace backup: `.bashrc.bak.TIMESTAMP`

### 6. Genera .env.agent

```bash
NAS_AGENT_MODEL=gemini
GOOGLE_API_KEY=tu-key-aqui
DOCKER_BASE=/docker
TZ=America/New_York
```

Permisos 600 (solo tu usuario puede leerlo — tiene la API key).

### 7. Instala dependencias Python

```bash
pip install -r requirements.txt
```

Intenta con `--break-system-packages` (Python 3.12+). Si falla, intenta venv.

---

## Instalacion sin TUI (bash puro)

Si prefieres no instalar Rich/InquirerPy:

```bash
cd /nas-dotfiles
./install.sh
```

Mismo wizard pero con interfaz bash basica (read/echo). Hace exactamente lo mismo.

---

## Instalacion manual (sin wizard)

Si prefieres control total:

```bash
# 1. Clonar
sudo git clone git@github.com:ydiaz1699/nas-dotfiles.git /nas-dotfiles
cd /nas-dotfiles
sudo chown -R $(whoami):$(whoami) /nas-dotfiles

# 2. Crear config de navegacion
cat > .config/user.conf << 'EOF'
NAV_HOME="/home/tu-usuario"
NAV_VAR="tuusr"
NAV_CMD="tuu"
EOF

# 3. Configurar bashrc
echo '' >> ~/.bashrc
echo '# nas-dotfiles shell framework' >> ~/.bashrc
echo 'export NAS_DOTFILES="/nas-dotfiles"' >> ~/.bashrc
echo 'source "$NAS_DOTFILES/shell/init.sh"' >> ~/.bashrc

# 4. Crear .env.agent (para el agente IA)
cat > .env.agent << 'EOF'
NAS_AGENT_MODEL=gemini
GOOGLE_API_KEY=tu-api-key
DOCKER_BASE=/docker
TZ=America/New_York
EOF
chmod 600 .env.agent

# 5. Dependencias Python (opcional, solo para el agente)
pip install -r requirements.txt

# 6. Recargar
source ~/.bashrc
```

---

## Instalacion de Docker (si no esta instalado)

El proyecto incluye un script para instalar Docker Engine en Debian:

```bash
/nas-dotfiles/shell/scripts/install_docker.sh
```

O manualmente:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $(whoami)
# Cerrar sesion y volver a entrar
```

---

## Verificar la instalacion

Despues de `source ~/.bashrc`:

```bash
# Shell framework
svc lista              # Deberia listar servicios Docker
nas                    # Deberia mostrar dashboard
disk                   # Deberia mostrar uso de disco

# Navegacion (si configuraste como "adm")
adm                    # Deberia ir a tu home
dk                     # Deberia ir a /docker

# Agente IA (si instalaste deps Python + API key)
agent "hola"           # Deberia responder con Rich panel

# Doctor (chequeo de salud)
svc doctor             # 6-point health check
```

---

## Configurar para root

Si dijiste "si" en el instalador, `/root/.bashrc` ya esta configurado. Si no:

```bash
sudo bash -c 'echo "export NAS_DOTFILES=/nas-dotfiles" >> /root/.bashrc'
sudo bash -c 'echo "source \$NAS_DOTFILES/shell/init.sh" >> /root/.bashrc'
```

---

## Configurar el agente IA despues

Si saltaste el provider durante la instalacion:

```bash
# Editar .env.agent
nano /nas-dotfiles/.env.agent

# Agregar:
NAS_AGENT_MODEL=gemini
GOOGLE_API_KEY=tu-key-de-aistudio
```

O para Ollama (local, gratis):

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1

# Configurar
echo "NAS_AGENT_MODEL=ollama" >> /nas-dotfiles/.env.agent
echo "OLLAMA_HOST=http://localhost:11434" >> /nas-dotfiles/.env.agent
```

---

## Actualizar

```bash
cd /nas-dotfiles
git pull origin main
source ~/.bashrc
```

Si hay nuevas dependencias Python:

```bash
pip install -r requirements.txt
```

---

## Desinstalar

```bash
cd /nas-dotfiles
./uninstall.sh
```

Esto elimina las lineas de `.bashrc` y opcionalmente borra `/nas-dotfiles/`.

O manualmente:

```bash
# Quitar de bashrc (usuario + root)
sed -i '/nas-dotfiles/d' ~/.bashrc
sudo sed -i '/nas-dotfiles/d' /root/.bashrc

# Borrar proyecto
sudo rm -rf /nas-dotfiles
```

Los servicios Docker en `/docker/` **NO se tocan** — siguen funcionando.

---

## Troubleshooting

### "NAS_DOTFILES no definida"

Tu `.bashrc` no tiene la linea `export NAS_DOTFILES=...`. Agregar:

```bash
echo 'export NAS_DOTFILES="/nas-dotfiles"' >> ~/.bashrc
echo 'source "$NAS_DOTFILES/shell/init.sh"' >> ~/.bashrc
source ~/.bashrc
```

### "svc: command not found"

El alias no se cargo. Verificar:

```bash
type svc    # Deberia decir: svc is aliased to ...
```

Si no, hacer `source ~/.bashrc` o abrir nueva terminal.

### "agent: command not found"

El agente necesita Python. Verificar:

```bash
python3 -c "from agent.nas_agent import main; print('OK')"
```

Si falla, instalar deps: `pip install -r /nas-dotfiles/requirements.txt`

### "Error al inicializar" (en el agente)

Falta API key o provider mal configurado:

```bash
cat /nas-dotfiles/.env.agent    # Verificar contenido
```

### Docker no funciona

```bash
docker ps                       # Si da error de permisos:
sudo usermod -aG docker $USER   # Agregar al grupo docker
# Cerrar sesion y volver a entrar
```

### Prompt no muestra contenedores

El prompt necesita Docker accesible. Si `docker ps` funciona pero el prompt muestra `0↑`, esperar 5 segundos (tiene cache).

---

## Estructura post-instalacion

Despues de una instalacion exitosa, el NAS queda asi:

```
/nas-dotfiles/              Codigo del framework (git repo)
    .config/user.conf       Tu config de navegacion
    .env.agent              API keys del agente (chmod 600)

/docker/                    Datos de servicios Docker
    emqx/compose.yml
    homeassistant/compose.yml
    ...

~/.bashrc                   2 lineas agregadas al final
/root/.bashrc               (opcional) mismas 2 lineas
```
