# IDEA: Estrategia de Disaster Recovery (DR) y Resiliencia para el NAS

> **Origen e inspiración:**
> Principios del video de KodeKloud: *"Disaster Recovery in Kubernetes"* ([YouTube Short NDABiL0N6Dw](https://www.youtube.com/shorts/NDABiL0N6Dw)).
> Adaptados al framework `nas-dotfiles` (Debian 13, Docker Compose + CLI `svc`, Dell PowerEdge T20).

---

## 1. Fundamentos Teóricos (El Modelo del Video)

El modelo de recuperación ante desastres plantea tres conceptos axiales:

### A. Los Dos Pilares de un Sistema
1. **Configuración (Infraestructura como Código):**
   * Manifiestos, `compose.yml`, variables de entorno, redes, configuraciones de arranque y proxy.
   * *Característica:* Es estática o versionable. Si se pierde el host pero la configuración sobrevive, la infraestructura se recrea en minutos.
2. **Datos (Estado Vivo):**
   * Bases de datos relacionales/vectoriales (`datapostgres`), bases clave-valor (`dataredis`), almacenamiento de objetos (RustFS / MinIO), volúmenes de usuarios y datos persistentes.
   * *Característica:* Es dinámica y cambiante. Sin estos datos, los contenedores arrancan vacíos.

### B. Métricas Operativas
* **RPO (Recovery Point Objective):** Tolerancia máxima a la pérdida de datos en el tiempo. Dicta con qué frecuencia se debe respaldar (ej. RPO = 24h implica backup diario; RPO = 1h requiere replicación continua o snapshots horarios).
* **RTO (Recovery Time Objective):** Tiempo máximo admisible de caída del servicio hasta estar 100% operativo nuevamente. Dicta el nivel de automatización y simplicidad del proceso de restore.

### C. Regla de Oro del Almacenamiento Externo y Pruebas
* **Almacenamiento Offsite:** Un backup almacenado en el mismo disco, servidor o cluster que protege **no es un backup**. Si el hardware falla, se pierde el servicio y el respaldo al mismo tiempo.
* **Test Your Restores:** Disponer de archivos `.tar.gz` no garantiza recuperación. Un plan de DR requiere simulacros periódicos de restauración y runbooks claros.

---

## 2. Diagnóstico del Estado Actual en `nas-dotfiles`

| Componente | Estado Actual | Evaluación |
|:---|:---|:---|
| **Configuración** | Versionada en Git (`$NAS_DOTFILES` en GitHub) + `svc snapshot` y `rollback` locales. | **Fuerte.** La recreación del entorno y los configs están centralizados. |
| **Secretos (.env)** | Almacenados en `$dkco/<svc>/.env` con permisos `600`. Se guardan copias en `.snapshots`. | **Aceptable.** Requiere copia de seguridad segura fuera del NAS (custodia encriptada). |
| **Backups de Datos** | `svc backup <svc>` y `svc backup-all` empaquetan volúmenes en `$BACKUP_DIR` (`/docker/backups/`) vía contenedor Alpine `tar czf` con verificación `tar -tzf`. | **Parcial.** Buen mecanismo local, pero vulnerable a fallos globales del servidor. |
| **Consistencia DB** | Respaldos a nivel de archivo/directorio (`/data`). Solo LobeHub cuenta con dump lógico específico (`svc lobehub backup-db`). | **Riesgo:** Copiar archivos crudos de PostgreSQL (`datapostgres`) en caliente puede dejar bases de datos inconsistentes o corruptas si hay escrituras activas. |
| **Almacenamiento Externo** | `$BACKUP_DIR` reside en el almacenamiento interno del NAS. No hay sincronización automática fuera del host. | **Punto Crítico:** Vulnerable a fallo físico de disco, controladora o placa del T20. |
| **Procedimiento de Restore** | Existe `svc restore <svc>` con selector `fzf` para sobreescribir `/data`. | **Parcial.** Funciona para recuperación rápida de un servicio, pero no se prueban restauraciones integrales "en frío". |

---

## 3. Hoja de Ruta para Evolución Futura

Para elevar la resiliencia del NAS a nivel de producción homelab:

### Fase 1: Consistencia en Bases de Datos (Dumps Lógicos de DataSQL)
* **Problema:** Respaldar `/docker/datasql/data/postgres` en caliente con `tar` puede provocar bloqueos o corrupción en WAL/tablas.
* **Solución propuesta:**
  * Crear un helper o hook en `svc backup datasql` que invoque un volcado lógico limpio:
    ```bash
    # En datasql: volcado lógico consistente de todas las bases antes de comprimir
    svc exec datasql pg_dumpall -U aadm > "$BACKUP_DIR/datasql_dump_$(date +%Y%m%d).sql"
    ```
  * Respaldar el dump SQL junto con la estructura de configuración.

### Fase 2: Almacenamiento Externo (Regla 3-2-1)
* **Objetivo:** Cumplir 3 copias, 2 soportes diferentes, 1 offsite.
* **Opciones de implementación:**
  1. **USB Automount Offsite (Local físico):**
     * Aprovechar el sistema de automount de USB del NAS (`/NAS/USB/`).
     * Agregar un script/cron o trigger de udev que, al conectar un pendrive o disco externo etiquetado como `NAS-BACKUP`, sincronice automáticamente `/docker/backups/` hacia el dispositivo desmontándolo al finalizar con notificación `ntfy`.
  2. **Offsite Remoto / Cloud:**
     * Integrar una herramienta como `rclone`, `restic` o `borgbackup` con cifrado en origen hacia almacenamiento S3 (Backblaze B2, Cloudflare R2, o almacenamiento remoto).

### Fase 3: RPO y RTO Definidos
* **Agendamiento:**
  * Servicios críticos (DataSQL, n8n, Flowise, Home Assistant): RPO = 24h (`svc cron add backup datasql daily`).
  * Servicios estáticos o sin estado dinámico pesado: RPO = 7 días (`svc cron add backup-all weekly`).
* **Rotación:**
  * Mantener los 5 backups locales (`BACKUP_KEEP=5`) y rotación temporal (7 diarios, 4 semanales) en el almacenamiento externo.

### Fase 4: Protocolo de Simulacro de Restauración (Drill Runbook)
* Documentar en `docs/troubleshooting.md` o crear una guía `docs/disaster-recovery-guide.md` con los pasos exactos para levantar el NAS desde cero en otra máquina:
  1. Clonar `$NAS_DOTFILES` vía Git.
  2. Restaurar los `.env` desde el almacén cifrado externo.
  3. Ejecutar `docker-boot-staged` o arranque secuencial de capas.
  4. Restaurar volúmenes y bases con `svc restore` o restauración de dumps SQL.
  5. Medir y documentar el RTO real.

---

## 4. Archivos y Puntos de Extensión en el Framework

* `docker/cli/lib/backup.sh`: Lógica actual de `svc_backup` y `svc_backup_all`.
* `docker/cli/lib/extras.sh`: Gestión de `svc cron`.
* `docker/cli/lib/notifications.sh`: Alertas vía `ntfy_send` para topic `backups`.
* `docs/services/datasql-guide.md`: Guía de administración y respaldo de bases de datos.
