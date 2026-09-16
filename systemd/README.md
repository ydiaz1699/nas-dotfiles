# Systemd — NAS Agent Daemon

Servicio systemd para mantener el agente corriendo 24/7 (scheduler + plugins).

## Qué hace el daemon

| Componente | Función | Intervalo |
|------------|---------|-----------|
| Scheduler | Ejecuta tareas periódicas de plugins | Según config |
| Memory curation | Limpia memoria vieja, consolida | 24h |
| Heartbeat | Log de que el daemon sigue vivo | 60 min |

## Instalación

```bash
# Copiar unit file
sudo cp /nas-dotfiles/systemd/nas-agent.service /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar (arranca con el NAS) + iniciar ahora
sudo systemctl enable --now nas-agent
```

## Arranque escalonado de Docker

El arranque de Compose está separado del daemon del agente. La unidad se
**genera desde una plantilla** con las rutas reales de la instalación
(`NAS_DOTFILES` y `DOCKER_BASE`), no se copia con rutas fijas. Tras crear
`$dkco/scripts/layers.conf`, sigue
[`docs/docker-boot-staged-guide.md`](../docs/docker-boot-staged-guide.md).
La unidad requiere `docker.service`, espera red/montajes y ejecuta
`$NAS_DOTFILES/shell/scripts/boot-order.sh` como root. No se debe habilitar hasta
probar primero el script manualmente.

```bash
# Genera /etc/systemd/system/docker-boot-staged.service con tus rutas
sudo NAS_DOTFILES="$NAS_DOTFILES" DOCKER_BASE="$DOCKER_BASE" \
  "$NAS_DOTFILES/shell/scripts/install-boot-service.sh"
# Habilitar cuando el arranque manual ya funcione
sudo systemctl enable docker-boot-staged.service
sudo systemctl start docker-boot-staged.service
```

Ver el resultado con `sudo systemctl status docker-boot-staged.service` y el
log operativo en `$dkco/scripts/boot-order.log`. El unit file en `/etc` es
generado: no editarlo a mano, regenerarlo con el instalador si cambian las rutas.

## Comandos

```bash
# Estado
sudo systemctl status nas-agent

# Logs en vivo
journalctl -u nas-agent -f

# Reiniciar
sudo systemctl restart nas-agent

# Detener
sudo systemctl stop nas-agent

# Deshabilitar (no arranca al boot)
sudo systemctl disable nas-agent
```

## Variables de entorno

Se leen de `/nas-dotfiles/.env.agent`. Variables relevantes:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NAS_AGENT_MODEL` | gemini | Provider del LLM |
| `NAS_AGENT_LOG_LEVEL` | INFO | Nivel de log (DEBUG/INFO/WARNING/ERROR) |
| `NAS_AGENT_AUDIT` | 1 | Registrar acciones en audit log |
| `NAS_AGENT_MEMORY_DIR` | agent/memory | Directorio de memoria persistente |
| `GOOGLE_API_KEY` | — | API key de Gemini |

## Notas

- El daemon **no** reemplaza al CLI — son independientes.
- CLI: `python -m agent.nas_agent "..."` (interactivo, bajo demanda)
- Daemon: scheduler + plugins corriendo en background
- Si el daemon crashea, systemd lo re-levanta en 10 segundos (máx 5 veces en 5 min).
- Logs van a journald — no se necesita logrotate.
