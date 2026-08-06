# Multi-NAS — Arquitectura Distribuida

> **Estado:** Idea / diseño futuro (no implementado)
> **Fecha:** 2026-08-05
> **Requisito previo:** Tener 2-3 servidores NAS en ubicaciones distintas

---

## Objetivo

Distribuir datos, backups y servicios entre múltiples homelabs
para redundancia, disponibilidad y recuperación ante desastres.

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   NAS Principal │      │   NAS Offsite   │      │   NAS Terciario │
│   (Casa)        │      │   (Oficina)     │      │   (Familiar)    │
│                 │      │                 │      │                 │
│  • Servicios    │      │  • Mirror       │      │  • Backups      │
│  • Datos        │◄────►│  • Réplica      │◄────►│  • Cold storage │
│  • Agente       │      │  • Failover     │      │  • Archivos     │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────── VPN (Tailscale/WireGuard) ────────────┘
```

---

## Capas de la arquitectura

### 1. Conectividad — VPN mesh

| Opción | Complejidad | Ventaja |
|--------|:-----------:|---------|
| **Tailscale** | Baja | Zero-config, NAT traversal, MagicDNS |
| WireGuard | Media | Más rápido, sin dependencia externa |
| ZeroTier | Baja | Similar a Tailscale, self-hosteable |

**Recomendación:** Tailscale (instalas en los 3 y se ven entre sí automáticamente).

```bash
# En cada NAS:
instal tailscale
tailscale up
# Los 3 se ven como: nas-casa, nas-oficina, nas-familiar
```

---

### 2. Sincronización de datos

| Tipo de dato | Herramienta | Dirección | Frecuencia |
|:--|:--|:--|:--|
| Configs (nas-dotfiles) | **git** | Principal → todos | Push/pull manual o cron |
| Backups Docker (tar.gz) | **rclone sync** | Principal → offsite | Diario (post-backup) |
| Fotos/documentos | **Syncthing** | Bidireccional | Tiempo real |
| Media (películas, música) | **rclone sync** | Principal → offsite | Semanal |
| Bases de datos | **PostgreSQL replication** | Principal → réplica | Streaming (tiempo real) |
| Memoria del agente | **git o Syncthing** | Principal → todos | Después de curación |

---

### 3. Niveles de redundancia

```
Nivel 1: Backup local
  └── tar.gz en /docker/backups/ (ya implementado)

Nivel 2: Backup offsite
  └── rclone sync → NAS Offsite (nuevo)

Nivel 3: Replicación en vivo
  └── Syncthing / PostgreSQL streaming (futuro)

Nivel 4: Failover automático
  └── Si NAS Principal cae → Offsite toma el control (futuro avanzado)
```

---

### 4. Catálogo de servicios por nodo

Cada NAS puede correr servicios distintos. El catálogo define qué va dónde:

```yaml
# agent/catalog/nodes.yml (futuro)
nodes:
  casa:
    role: principal
    services: [homeassistant, emqx, n8n, nextcloud, postgres, adguard]
    backup_to: [oficina, familiar]

  oficina:
    role: mirror
    services: [adguard, syncthing, postgres-replica]
    receives_backup_from: [casa]

  familiar:
    role: offsite
    services: [syncthing]
    receives_backup_from: [casa]
    retention: 90 days
```

---

### 5. rclone — Backup offsite automatizado

```bash
# Después de svc backup <servicio>:
rclone sync /docker/backups/ nas-oficina:/docker/backups/ \
  --transfers 4 \
  --checkers 8 \
  --filter "+ *.tar.gz" \
  --filter "- *"

# Verificar integridad:
rclone check /docker/backups/ nas-oficina:/docker/backups/
```

Integración con el daemon:

```python
# agent/plugins/offsite_backup_plugin.py (futuro)
# Schedule: después de cada backup local → rclone sync al offsite
```

---

### 6. Syncthing — Sincronización bidireccional

Para datos que se editan desde cualquier ubicación (fotos, documentos).

```yaml
# docker/syncthing/docker-compose.yml
services:
  syncthing:
    image: syncthing/syncthing:latest
    restart: unless-stopped
    ports:
      - "8384:8384"   # Web UI
      - "22000:22000" # Sync
    volumes:
      - ./config:/var/syncthing/config
      - /datos/compartidos:/var/syncthing/data
```

Folders compartidos entre los 3 NAS:
- `/datos/fotos/` → synced, versionado
- `/datos/documentos/` → synced
- `/docker/backups/` → NO synced (usa rclone, unidireccional)

---

### 7. PostgreSQL — Replicación streaming

Si el NAS Offsite necesita una réplica de la base de datos:

```
NAS Casa (primary) ──streaming──► NAS Oficina (standby read-only)
```

```bash
# En primary (casa):
# postgresql.conf
wal_level = replica
max_wal_senders = 3

# En standby (oficina):
# standby.signal + primary_conninfo
primary_conninfo = 'host=nas-casa port=5432 user=replicator'
```

---

### 8. Failover (futuro avanzado)

Si el NAS principal se cae:

```
1. Monitoreo detecta caída (ping / healthcheck entre nodos)
2. NAS Offsite promueve PostgreSQL standby → primary
3. DNS/Tailscale redirige tráfico al offsite
4. Servicios críticos se levantan en offsite
5. Notificación al usuario (Telegram/ntfy)
```

Herramientas posibles:
- **Keepalived** — IP virtual flotante (si están en la misma red)
- **Tailscale + DNS** — redirect a nivel DNS
- **Agente distribuido** — cada NAS tiene su agente, se coordinan via MQTT

---

### 9. Seguridad

| Aspecto | Solución |
|---------|----------|
| Tráfico entre nodos | VPN (Tailscale/WireGuard) — cifrado |
| Backups en tránsito | rclone con `--crypt` o SFTP |
| Acceso SSH entre nodos | Solo via VPN, keys rotadas |
| Secretos (.env) | NUNCA se replican — cada nodo tiene los suyos |
| Certificados | Tailscale MagicDNS + HTTPS automático |

---

### 10. Integración con nas-dotfiles

Cuando se implemente, los cambios serían:

| Componente | Cambio |
|------------|--------|
| `agent/plugins/` | Nuevo: `offsite_backup_plugin.py` |
| `agent/config/` | Nuevo: `nodes.yml` (definición de nodos) |
| `systemd/` | Nuevo: `nas-agent-sync.timer` (rclone periódico) |
| `svc_py/commands/` | Nuevo: `sync.py` (`svc sync`, `svc sync-status`) |
| `docker/cli/lib/` | Nuevo: `sync.sh` (bash equivalent) |
| `shell/init.sh` | Nuevo alias: `nas-oficina`, `nas-familiar` (SSH rápido) |

---

## Orden de implementación recomendado

| Paso | Qué | Esfuerzo | Impacto |
|:----:|-----|:--------:|:-------:|
| 1 | Tailscale en los 3 NAS | 30 min | Conectividad base |
| 2 | rclone sync de backups (cron manual) | 1h | Redundancia offsite |
| 3 | `offsite_backup_plugin.py` (automatiza paso 2) | 2h | Automatización |
| 4 | Syncthing para datos compartidos | 1h | Fotos/docs sincronizados |
| 5 | `nodes.yml` + `svc sync` command | 3h | Gestión centralizada |
| 6 | PostgreSQL replication | 2h | BD redundante |
| 7 | Failover automático | Alto | Alta disponibilidad |

---

## Decisiones pendientes (para cuando se implemente)

- [ ] ¿Tailscale o WireGuard?
- [ ] ¿Qué servicios corren en cada nodo?
- [ ] ¿Syncthing para todo o solo ciertos folders?
- [ ] ¿Failover automático o manual?
- [ ] ¿Cuánto retención en offsite? (30, 60, 90 días)
- [ ] ¿PostgreSQL streaming o solo backups SQL?

---

## Por qué NO blockchain

| Necesidad | Blockchain | Solución correcta |
|-----------|:----------:|:-----------------|
| Redundancia | Overkill | rclone + Syncthing |
| Integridad | Overkill | sha256sum + git |
| Sincronización | No diseñado para eso | Syncthing / rclone |
| Confianza entre nodos | No aplica (son todos tuyos) | VPN + SSH keys |
| Historial inmutable | Overkill | git log |

Blockchain resuelve problemas de confianza entre extraños.
3 NAS tuyos = misma autoridad = replicación es suficiente.

---

## Referencias

- [Tailscale](https://tailscale.com/) — VPN mesh zero-config
- [Syncthing](https://syncthing.net/) — Sync bidireccional P2P
- [rclone](https://rclone.org/) — Swiss army knife de cloud storage
- [PostgreSQL Streaming Replication](https://www.postgresql.org/docs/current/warm-standby.html)
