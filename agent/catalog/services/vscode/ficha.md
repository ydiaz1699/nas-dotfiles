---
id: "vscode"
name: "VS Code Server"
description: "code-server accesible desde el navegador para editar el NAS y Home Assistant"
aliases:
  - vscode
  - vs-code
  - code-server
  - visual-studio-code-server
  - editor-web
image: "ghcr.io/coder/code-server:4.135.0-39"
category: "herramientas"
port_internal: 8080
port_default: 8443
protocol: "http"
needs_proxy: false
needs_db: false
volumes:
  - "./config:/home/coder/.config"
  - "./local:/home/coder/.local"
  - "./workspace:/home/coder/project/workspace"
  - "${NAS_DOTFILES}:/home/coder/project/nas-dotfiles"
  - "../homeassistant/data:/home/coder/project/homeassistant"
env_required:
  - NAS_DOTFILES
  - VSCODE_UID
  - VSCODE_GID
env_optional: []
healthcheck: '["CMD", "curl", "-fsS", "http://127.0.0.1:8080/healthz"]'
backup_critical: true
backup_paths:
  - "./config"
  - "./local"
  - "./workspace"
protected: true
docs_url: "docs/services/vscode-guide.md"
notes: "Contenedor no-root: user usa VSCODE_UID:VSCODE_GID y hereda no-new-privileges desde _common.yml. Debe usar entrypoint /usr/bin/code-server, no el entrypoint oficial que ejecuta fixuid/sudo; DOCKER_USER no se usa. Publica el editor en LAN mediante 8443:8080, decisión intencional que no autoriza exposición a Internet. La contraseña vive en config/code-server/config.yaml con modo 600 y no se guarda en .env ni Git. Monta únicamente config, local, workspace, el checkout NAS_DOTFILES y homeassistant/data. La ACL de aadm para editar Home Assistant requiere aplicación y verificación runtime; no dar escritura a secrets.yaml ni .storage. SERVER_IP y TZ se heredan del .env global. La configuración objetivo debe pasar svc config, healthcheck, curl /healthz y una prueba real de edición antes de declararse completamente confirmada."
networks: []
ports:
  http: 8443
resources:
  memory_limit: "512m"
  memory_reservation: "128m"
security_extra: {}
runtime_status: "fixuid-entrypoint-correction-confirmed"
target_status: "pending-homeassistant-acl-verification"
---

# VS Code Server

La guía operativa única es `docs/services/vscode-guide.md`. Esta ficha contiene
metadatos, aliases, límites y estado de confirmación para que el catálogo pueda
localizar el servicio sin duplicar el procedimiento.

## Resumen de arquitectura

- Imagen fijada `ghcr.io/coder/code-server:4.135.0-39`.
- Editor publicado en `${SERVER_IP}:8443`, con HTTP interno en `8080`.
- Proceso no-root como `VSCODE_UID:VSCODE_GID` (usuario `aadm`).
- `no-new-privileges:true` heredado desde `../../_common.yml`.
- Entry point directo `/usr/bin/code-server` para evitar el fallo de `fixuid`/`sudo` del entrypoint oficial.
- Sin `DOCKER_USER`, `/var/run/docker.sock`, montaje de `$dkco` completo o montaje de `/`.
- ACL puntual para editar Home Assistant; secretos y `.storage` quedan fuera de la ACL.

## Estado

La corrección del entrypoint se basa en el error de runtime observado y fue
confirmada como solución al bucle de reinicio. La verificación posterior de
`svc ps vscode`, `svc health`, `curl /healthz` y la ACL de Home Assistant debe
realizarse en el NAS antes de tratar toda la configuración como desplegada.
