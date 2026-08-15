#!/bin/bash
# ==========================================================
# nas-dotfiles — Librería de Notificaciones (ntfy)
# ==========================================================
# Archivo: docker/cli/lib/notifications.sh
# Descripción: Función ntfy_send() para uso en scripts svc
#              y otros scripts del NAS. Envía notificaciones
#              push al servidor ntfy local.
#
# Se carga automáticamente desde svc.sh via source.
#
# Topics:
#   usb        → automontaje/desmontaje de USBs
#   docker     → eventos de servicios Docker (down, update, restart)
#   backups    → backups (cron, svc backup)
#   system     → SMART, SSH, disco lleno
#   alarma     → alarma + cámara (Home Assistant)
#   nas-alerts → catch-all general
#
# Prioridades: min, low, default, high, urgent
# ==========================================================

# Evitar doble source
[[ -n "${__NAS_NOTIFICATIONS_LOADED:-}" ]] && return 0
__NAS_NOTIFICATIONS_LOADED=1

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

NTFY_URL="${NTFY_URL:-http://localhost:8090}"
NTFY_DEFAULT_TOPIC="${NTFY_DEFAULT_TOPIC:-nas-alerts}"

# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

# ntfy_send — Enviar notificación push via ntfy
#
# Argumentos:
#   $1 — topic (default: nas-alerts)
#   $2 — título (opcional)
#   $3 — mensaje/body (requerido)
#   $4 — prioridad: min|low|default|high|urgent (default: default)
#   $5 — tags/emojis separados por coma (ej. "warning,usb")
#
# Variables de entorno opcionales:
#   NTFY_URL    — URL base del servidor (default: http://localhost:8090)
#   NTFY_TOKEN  — Token de autenticación Bearer (si auth habilitada)
#
# Retorno: siempre 0 (fallo silencioso)
#
ntfy_send() {
    local topic="${1:-$NTFY_DEFAULT_TOPIC}"
    local title="${2:-}"
    local message="${3:-}"
    local priority="${4:-default}"
    local tags="${5:-}"

    # Sin mensaje = no enviar
    [[ -z "$message" ]] && return 0

    # Construir headers
    local -a headers=()
    [[ -n "$title" ]] && headers+=(-H "Title: $title")
    [[ -n "$priority" && "$priority" != "default" ]] && headers+=(-H "Priority: $priority")
    [[ -n "$tags" ]] && headers+=(-H "Tags: $tags")
    [[ -n "${NTFY_TOKEN:-}" ]] && headers+=(-H "Authorization: Bearer $NTFY_TOKEN")

    # Enviar (silencioso, timeout 5s)
    curl -s --max-time 5 \
        "${headers[@]}" \
        -d "$message" \
        "${NTFY_URL}/${topic}" \
        >/dev/null 2>&1 || true
}

# ==============================================================================
# FUNCIONES DE CONVENIENCIA PARA SVC
# ==============================================================================

# Servicio Docker caído
ntfy_service_down() {
    local service="$1"
    ntfy_send "docker" "⚠️ Servicio caído" \
        "${service} DOWN desde $(date '+%H:%M:%S')" \
        "high" "warning,whale"
}

# Servicio Docker reiniciado
ntfy_service_restarted() {
    local service="$1"
    ntfy_send "docker" "🔄 Servicio reiniciado" \
        "${service} reiniciado correctamente" \
        "default" "whale,arrows_counterclockwise"
}

# Actualización completada (svc update-all)
ntfy_update_complete() {
    local count="$1"
    local details="${2:-}"
    ntfy_send "docker" "🆙 Actualización completada" \
        "${count} servicios actualizados${details:+. ${details}}" \
        "default" "whale,up"
}

# Backup completado
ntfy_backup_complete() {
    local service="$1"
    local size="${2:-}"
    ntfy_send "backups" "✅ Backup ${service}" \
        "Completado${size:+: ${size}}" \
        "default" "floppy_disk"
}

# Backup fallido
ntfy_backup_failed() {
    local service="$1"
    local error="${2:-}"
    ntfy_send "backups" "❌ Backup fallido: ${service}" \
        "Error${error:+: ${error}}" \
        "high" "x,floppy_disk"
}

# Alerta del sistema
ntfy_system_alert() {
    local title="$1"
    local message="$2"
    local priority="${3:-high}"
    ntfy_send "system" "$title" "$message" "$priority" "rotating_light"
}

# Health check fallido (usado por svc health)
ntfy_health_failed() {
    local service="$1"
    local details="${2:-no responde al healthcheck}"
    ntfy_send "docker" "🏥 Health check fallido" \
        "${service}: ${details}" \
        "high" "warning,hospital"
}
