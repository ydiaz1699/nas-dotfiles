# GitHub CLI (`gh`) — Instalación y autenticación

> Guía para configurar `gh` en un NAS Debian/Ubuntu y no volver a escribir credenciales.

---

## 1. Instalar GitHub CLI

```bash
# Agregar el repo oficial de GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  | sudo tee /usr/share/keyrings/githubcli-archive-keyring.gpg > /dev/null

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
  https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null

apt update
apt install gh -y
```

> Si tu NAS no es Debian/Ubuntu, consulta: https://github.com/cli/cli/blob/trunk/docs/install_linux.md

---

## 2. Autenticarse

### Opción A — Login con navegador web (recomendada si tienes PC/teléfono a mano)

```bash
gh auth login
```

1. **What account?** → `GitHub.com`
2. **Protocol?** → `HTTPS`
3. **Authenticate?** → `Login with a web browser`
4. Te muestra un código de 8 caracteres — cópialo
5. Abre https://github.com/login/device desde tu PC o teléfono
6. Pega el código y autoriza

```
✓ Logged in as ydiaz1699
```

> **Nota:** Si la NAS abre un navegador de terminal (w3m/lynx) y se queda colgada,
> usa la Opción B en su lugar.

---

### Opción B — Login con Personal Access Token (para NAS sin navegador)

#### Paso 1 — Crear token

Desde tu PC/teléfono ve a:
👉 https://github.com/settings/tokens/new

| Campo | Valor |
|-------|-------|
| Note | `nas-gh-cli` |
| Expiration | 90 days (o No expiration) |
| Scopes | ✅ `repo` + ✅ `read:org` |

Click **Generate token** → Copia el `ghp_...`

#### Paso 2 — Pegar en la NAS

```bash
gh auth login --with-token <<< "ghp_TU_TOKEN_AQUI"
```

O de forma interactiva:

```bash
gh auth login -p https -h github.com
# Elegir: Paste an authentication token
# Pegar el ghp_...
```

---

## 3. Verificar

```bash
gh auth status
```

Debe mostrar:

```
✓ Logged in to github.com account ydiaz1699
  Token scopes: 'repo', 'read:org'
```

---

## 4. Usar

```bash
# Push sin que pregunte credenciales
git push origin main

# Bonus: manejar PRs desde la terminal
gh pr list
gh pr create --title "mi cambio" --body "descripción"
```

---

## Troubleshooting

### `error: token invalid` o `403 Permission denied`

El token no tiene los permisos correctos. Solución:

1. Ve a https://github.com/settings/tokens
2. Click en el token → verifica que tenga ✅ `repo` y ✅ `read:org`
3. Si lo modificaste, copia el token actualizado y:

```bash
gh auth logout -h github.com -u ydiaz1699
gh auth login --with-token <<< "ghp_TOKEN_ACTUALIZADO"
```

### `missing required scope 'read:org'`

Edita el token en GitHub y agrega el scope `read:org`, luego repite el login.

### El navegador de terminal se queda colgado

Presiona `q` o `Ctrl+C` para salir, luego usa la **Opción B** (token).

---

## Dónde se guarda

| Qué | Ruta | Propósito |
|-----|------|-----------|
| Llave GPG | `/usr/share/keyrings/githubcli-archive-keyring.gpg` | Verificar paquete |
| Repo apt | `/etc/apt/sources.list.d/github-cli.list` | Fuente del paquete |
| Binario | `/usr/bin/gh` | El programa |
| Tu login | `~/.config/gh/hosts.yml` | Token de autenticación |
