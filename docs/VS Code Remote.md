# Guía: VS Code Remote SSH con `aadm` y `root`

> Todos los comandos marcados **[Windows]** se ejecutan en PowerShell, en tu PC.
> Todos los marcados **[NAS]** se ejecutan dentro de la sesión SSH ya conectada al NAS (prompt tipo `aadm@Nas ~` o `root@Nas ~`).
> Si tu prompt dice `PS C:\Users\...>` estás en Windows. Si dice `usuario@Nas ~` estás en el NAS. Nunca mezcles comandos de un lado en el otro — es la causa más común de errores en esta guía.

## 0. Antes de empezar: entiende las dos contraseñas

| Nombre | Qué es | Dónde se define |
|---|---|---|
| **Contraseña de sistema** (`root` o `aadm` del NAS) | La contraseña real de Debian, la de siempre | Ya existe en el NAS |
| **Passphrase de la clave SSH** | Candado opcional que protege el archivo de la clave privada en tu PC | La inventas tú al crear la clave con `ssh-keygen` |

Son cosas completamente distintas y no tienen que coincidir. Si te confunde, crea las claves **sin passphrase** (`-N '""'` en PowerShell) y confía solo en la contraseña real del sistema para instalar la clave.

## 1. Preparar PowerShell en Windows **[Windows]**

```powershell
ssh -V
```

Debe mostrar una versión de OpenSSH. Si no existe, instala **OpenSSH Client** desde "Características opcionales" de Windows.

```powershell
New-Item -ItemType Directory -Force "$HOME\.ssh" | Out-Null
```

## 2. Crear las claves SSH **[Windows]**

Para `aadm` (con passphrase, ya que se usa a diario y conviene protegerla):

```powershell
ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519_nas_aadm" -C "vscode-nas-aadm"
```

Para `root` (recomendado sin passphrase, ya que `PermitRootLogin` de Debian ya obliga a usar clave — ver nota de seguridad al final):

```powershell
ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519_nas_root" -N '""'
```

> **Nota sobre `-N ""`:** en PowerShell, `-N ""` a veces falla con `option requires an argument -- N` porque PowerShell descarta las comillas vacías antes de pasarlas a `ssh-keygen`. Usa `-N '""'` (comillas simples envolviendo comillas dobles) para evitarlo. Si aun así falla, omite `-N` y cuando pregunte la passphrase, presiona Enter dos veces para dejarla vacía.

Verifica que las 4 claves existen:

```powershell
Get-ChildItem "$HOME\.ssh\id_ed25519_nas_*"
```

Nunca compartas los archivos sin extensión `.pub` (`id_ed25519_nas_aadm`, `id_ed25519_nas_root`) — son las claves privadas.

## 3. Instalar la clave de `aadm` en el NAS **[Windows]**

```powershell
Get-Content -Raw "$HOME\.ssh\id_ed25519_nas_aadm.pub" | ssh aadm@Nas.local "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

Pedirá la contraseña **actual** de `aadm` (la del sistema). Ejecútalo una sola vez; repetirlo duplica la clave en el archivo.

Prueba:

```powershell
ssh -i "$HOME\.ssh\id_ed25519_nas_aadm" -o IdentitiesOnly=yes aadm@Nas.local "id -un; hostname"
```

Resultado esperado: `aadm` / `Nas`.

## 4. Instalar la clave de `root` en el NAS

⚠️ **Este paso es distinto al de `aadm` y es donde casi todo el mundo se traba.** La razón: por defecto, Debian trae en `/etc/ssh/sshd_config` la línea:

```text
PermitRootLogin prohibit-password
```

Esto significa que **root puede entrar por SSH, pero nunca usando contraseña — solo con clave pública ya instalada**. Es una medida de seguridad intencional. Por eso el método que funciona con `aadm` (mandar la clave por SSH usando la contraseña) **nunca funcionará con root**, sin importar cuántas veces repitas la contraseña correcta — el sistema la ignora a propósito.

La única forma de instalar la primera clave de root es haciéndolo manualmente, desde una sesión donde ya seas root localmente (por ejemplo, entrando primero como `aadm` y usando `su -` o `sudo -i`).

### 4.1 Consigue una sesión root en el NAS **[Windows → NAS]**

```powershell
ssh aadm@Nas.local
```

Dentro de esa sesión, **[NAS]**:

```bash
su -
```

Escribe la contraseña real de `root` cuando la pida. Confirma que quedaste como root:

```bash
id -un
```

Debe responder `root`.

### 4.2 Copia tu clave pública de root **[Windows]**

En una ventana de PowerShell **aparte** (no la sesión SSH):

```powershell
Get-Content "$HOME\.ssh\id_ed25519_nas_root.pub"
```

Copia la línea completa (empieza con `ssh-ed25519 AAAA...`), incluyendo el comentario final.

### 4.3 Pega la clave dentro del NAS **[NAS]**

Ya como root (paso 4.1):

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
```

Pega la clave pública (una sola línea, sin cortes). Guarda con `Ctrl+O`, `Enter`, sal con `Ctrl+X`.

```bash
chmod 600 ~/.ssh/authorized_keys
chmod 700 /root
cat ~/.ssh/authorized_keys
```

Confirma que el contenido mostrado coincide exactamente con lo que copiaste en el paso 4.2.

### 4.4 Prueba desde Windows **[Windows]**

```powershell
ssh -i "$HOME\.ssh\id_ed25519_nas_root" -o IdentitiesOnly=yes root@Nas.local "id -un; hostname"
```

Resultado esperado: `root` / `Nas`, sin pedir contraseña del sistema (solo la passphrase de la clave, si le pusiste una).

## 5. Crear el archivo de configuración SSH de Windows **[Windows]**

```powershell
if (-not (Test-Path "$HOME\.ssh\config")) {
    New-Item -ItemType File "$HOME\.ssh\config" | Out-Null
}
notepad "$HOME\.ssh\config"
```

Pega:

```sshconfig
Host nas-aadm
    HostName Nas.local
    User aadm
    IdentityFile ~/.ssh/id_ed25519_nas_aadm
    IdentitiesOnly yes

Host nas-root
    HostName Nas.local
    User root
    IdentityFile ~/.ssh/id_ed25519_nas_root
    IdentitiesOnly yes
```

Guarda y verifica:

```powershell
Get-Content "$HOME\.ssh\config"
```

## 6. Probar los alias **[Windows]**

```powershell
ssh nas-aadm "id -un; hostname"
ssh nas-root "id -un; hostname"
```

Para confirmar que usan clave y no contraseña:

```powershell
ssh -o PreferredAuthentications=publickey -o PasswordAuthentication=no nas-aadm "id -un; hostname"
ssh -o PreferredAuthentications=publickey -o PasswordAuthentication=no nas-root "id -un; hostname"
```

## 7. Configurar VS Code **[Windows]**

1. Instala **Visual Studio Code**.
2. `Ctrl+Shift+X` → instala la extensión **Remote - SSH** (Microsoft).
3. `Ctrl+Shift+P` → **Remote-SSH: Connect to Host...** → elige `nas-aadm`.
4. Si pregunta el sistema operativo remoto, elige **Linux**.
5. Introduce la passphrase de `id_ed25519_nas_aadm` si le pusiste una.

VS Code instala su servidor remoto dentro de la cuenta `aadm` únicamente; no toca Docker ni servicios.

## 8. Abrir carpetas del NAS **[dentro de VS Code, terminal integrada]**

Con `nas-aadm` conectado:

```bash
nasfk
pwd
```

Abre la ruta mostrada con `File → Open Folder`.

Para un servicio específico:

```bash
dk homeassistant
pwd
```

Para abrir una sesión como root: `Ctrl+Shift+P` → **Remote-SSH: Connect to Host...** → `nas-root`. Ábrelo en una ventana aparte y ciérrala cuando termines — cualquier extensión, tarea o comando corrido ahí tiene permisos totales sobre el NAS.

## 9. Uso recomendado del día a día

- Trabajo normal → `nas-aadm`.
- Tareas administrativas puntuales dentro de esa sesión → `sudo -i`.
- `nas-root` → solo cuando necesites que **toda** la sesión de VS Code (explorador de archivos, terminal, extensiones) corra como root.

## Apéndice: tabla de diagnóstico rápido

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Permission denied (publickey,password)` al usar `root@Nas.local` con contraseña | `PermitRootLogin prohibit-password` bloquea contraseña para root | Instalar la clave manualmente (sección 4), nunca por SSH con contraseña |
| `Get-Content: orden no encontrada` o `-bash: Get-Content: orden no encontrada` | Comando de PowerShell pegado dentro de la sesión SSH del NAS (bash) | Verifica el prompt: `PS C:\...>` = Windows, `usuario@Nas ~` = NAS |
| `option requires an argument -- N` en `ssh-keygen -N ""` | PowerShell descarta las comillas vacías | Usa `-N '""'` o crea la clave con passphrase manual |
| `cat: .../authorized_keys: No existe el fichero` | Primera instalación de clave nunca se completó | Repite sección 4 completa |
| Pide passphrase 3 veces y cae a pedir password | La passphrase escrita no coincide con la de la clave | Verifica con cuidado, o regenera la clave con `-N '""'` para eliminar la variable |
| `sudo: a terminal is required to read the password` | Se ejecutó `sudo` dentro de un pipe sin terminal interactiva (mezclando comandos de Windows y NAS) | Separa las terminales; usa el método manual de la sección 4 en vez de pipe+sudo |

## Nota de seguridad

Dejar la clave de `root` sin passphrase (sección 2) es cómodo pero significa que cualquiera con acceso a tu cuenta de Windows puede conectarse como root al NAS sin escribir nada más. Si tu PC no está cifrado (BitLocker) o lo comparten otras personas, considera:

- Ponerle passphrase a `id_ed25519_nas_root` de todos modos, o
- Usar `ssh-agent` para no tener que escribirla cada vez, o
- Restringir en `sshd_config` el acceso root por IP/red con `Match Address`.
