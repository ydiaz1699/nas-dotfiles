#!/bin/bash
# ==========================================================
# nas-dotfiles — Pipeline de Auto-Documentación en Cascada
# ==========================================================
# Archivo: docker/cli/lib/catalog-sync.sh
# Descripción: Detecta archivos Compose válidos en $dkco/
#              (compose.yml/.yaml y docker-compose.yml/.yaml) y genera
#              automáticamente toda la documentación:
#              ficha.md, guía placeholder, entrada en SKILL.md,
#              script DebMenux placeholder.
#
# Uso:
#   svc catalog-sync              → Sincronizar todos los servicios
#   svc catalog-sync <servicio>   → Sincronizar uno específico
#   svc catalog-sync --dry-run    → Mostrar qué haría sin ejecutar
#   svc catalog-sync --status     → Mostrar estado de documentación
#
# Flujo:
#   compose.yml detectado
#     ├─→ agent/catalog/services/<svc>/ficha.md (si no existe)
#     ├─→ agent/catalog/services/<svc>/compose.yml (copia)
#     ├─→ agent/catalog/services/<svc>/.env.example (sanitizado)
#     ├─→ docs/services/<svc>-guide.md (placeholder si no existe)
#     ├─→ docker-nas/SKILL.md (actualiza tabla de guías)
#     └─→ Notificación ntfy (topic: docker)
#
# Licencia: MIT
# ==========================================================

# Evitar doble source
[[ -n "${__CATALOG_SYNC_LOADED:-}" ]] && return 0
__CATALOG_SYNC_LOADED=1

# ==============================================================================
# CONFIGURACIÓN
# ==============================================================================

CATALOG_DIR="${NAS_DOTFILES:-/nas-dotfiles}/agent/catalog/services"
DOCS_DIR="${NAS_DOTFILES:-/nas-dotfiles}/docs/services"
SKILL_FILE="${NAS_DOTFILES:-/nas-dotfiles}/docker-nas/SKILL.md"
DEBMENUX_SCRIPTS="/debmenux/scripts/services"
DOCKER_BASE="${DOCKER_BASE:-/docker}"
DRY_RUN=false

# ==============================================================================
# HELPERS
# ==============================================================================

_sync_log() {
    local level="$1" msg="$2"
    echo -e "  ${level} ${msg}"
}

_sync_info()  { _sync_log "📋" "$1"; }
_sync_ok()    { _sync_log "✅" "$1"; }
_sync_skip()  { _sync_log "⏭️ " "$1"; }
_sync_new()   { _sync_log "🆕" "$1"; }
_sync_warn()  { _sync_log "⚠️ " "$1"; }

# ==============================================================================
# EXTRACCIÓN DE METADATOS DESDE COMPOSE
# ==============================================================================

# Extraer datos básicos de un compose.yml usando grep/sed (sin dependencias Python)
_extract_from_compose() {
    local compose_file="$1"
    local svc_name="$2"

    # Imagen principal (primera que aparece)
    IMAGE=$(grep -m1 'image:' "$compose_file" | sed 's/.*image:\s*//' | tr -d '"' | tr -d "'" | xargs)

    # Puertos (primera línea de ports con formato "HOST:CONTAINER")
    PORTS=$(grep -A20 'ports:' "$compose_file" | grep -oP '"\K\d+:\d+' | head -5)
    PORT_MAIN=$(echo "$PORTS" | head -1 | cut -d: -f1)

    # Redes
    NETWORKS_LIST=$(grep -A10 'networks:' "$compose_file" | grep -oP '^\s+- \K\w+' | grep -v 'driver\|external' | sort -u)

    # Volúmenes
    VOLUMES_LIST=$(grep -E '^\s+- \./.*:' "$compose_file" | sed 's/^[[:space:]]*//' || true)

    # Variables de entorno requeridas (las que usan ${VAR})
    ENV_REQUIRED=$(grep -oP '\$\{([A-Z_]+)\}' "$compose_file" | tr -d '${} ' | sort -u)

    # Healthcheck
    HEALTHCHECK=$(grep -A5 'healthcheck:' "$compose_file" | grep 'test:' | sed 's/.*test:\s*//' | head -1)

    # Labels de Homepage
    HAS_HOMEPAGE_LABELS=$(grep -c 'homepage\.' "$compose_file" || echo "0")

    # Container name
    CONTAINER_NAME=$(grep -m1 'container_name:' "$compose_file" | sed 's/.*container_name:\s*//' | xargs)
}

# ==============================================================================
# GENERADORES
# ==============================================================================

# Generar ficha.md desde compose
_generate_ficha_from_compose() {
    local svc_name="$1"
    local compose_file="$2"
    local target="${CATALOG_DIR}/${svc_name}/ficha.md"

    if [[ -f "$target" ]]; then
        _sync_skip "ficha.md ya existe para ${svc_name}"
        return 0
    fi

    _extract_from_compose "$compose_file" "$svc_name"

    if [[ "$DRY_RUN" == "true" ]]; then
        _sync_new "[dry-run] Generaría ficha.md para ${svc_name}"
        return 0
    fi

    mkdir -p "${CATALOG_DIR}/${svc_name}"

    local networks_yaml=""
    if [[ -n "$NETWORKS_LIST" ]]; then
        networks_yaml=$(echo "$NETWORKS_LIST" | sed 's/^/  - /')
    fi

    local env_yaml=""
    if [[ -n "$ENV_REQUIRED" ]]; then
        env_yaml=$(echo "$ENV_REQUIRED" | sed 's/^/  - /')
    fi

    local volumes_yaml=""
    if [[ -n "$VOLUMES_LIST" ]]; then
        volumes_yaml=$(echo "$VOLUMES_LIST" | sed 's/^/  /')
    fi

    cat > "$target" <<EOF
---
id: "${svc_name}"
name: "${CONTAINER_NAME:-$svc_name}"
description: "Auto-generado por catalog-sync — completar"
image: "${IMAGE}"
category: "sin-categorizar"
port_default: ${PORT_MAIN:-0}
protocol: "http"
needs_proxy: false
needs_db: false
env_required:
${env_yaml}
healthcheck: '${HEALTHCHECK}'
backup_critical: true
backup_paths:
  - "./data"
protected: false
docs_url: "docs/services/${svc_name}-guide.md"
notes: "Auto-generado por catalog-sync $(date +%Y-%m-%d). Completar manualmente."
$(if [[ -n "$networks_yaml" ]]; then
echo "networks:"
echo "$networks_yaml"
fi)
ports:
  http: ${PORT_MAIN:-0}
aliases:
  - ${svc_name}
---

# ${CONTAINER_NAME:-$svc_name}

## Qué es

_(Completar: descripción del servicio y su función en el NAS)_

## Estructura

\`\`\`
\$dkco/${svc_name}/
├── compose.yml
├── .env
└── data/
\`\`\`

## Configuración detectada

- **Imagen:** \`${IMAGE}\`
- **Puerto:** ${PORT_MAIN:-ninguno}
- **Redes:** ${NETWORKS_LIST:-bridge default}
- **Homepage labels:** $(if [[ "$HAS_HOMEPAGE_LABELS" -gt 0 ]]; then echo "✅ sí"; else echo "❌ no (agregar)"; fi)
- **Generado:** $(date +%Y-%m-%d)

## docs_url

docs/services/${svc_name}-guide.md
EOF

    _sync_new "ficha.md generada para ${svc_name}"
}

# Convertir referencias del compose desplegado al contexto del catálogo.
# En /docker/<svc>/compose.yml la ruta es ../_common.yml; en el catálogo,
# agent/catalog/services/<svc>/compose.yml, es ../../_common.yml.
_catalogize_compose() {
    local source="$1"
    sed -E \
        's#^([[:space:]]*file:[[:space:]]*)\.\./_common\.yml([[:space:]]*)$#\1../../_common.yml\2#' \
        "$source"
}

# Copiar compose.yml al catálogo
_sync_compose() {
    local svc_name="$1"
    local compose_file="$2"
    local target="${CATALOG_DIR}/${svc_name}/compose.yml"

    # Copiar si no existe o si el source es más nuevo
    if [[ -f "$target" ]]; then
        if [[ "$compose_file" -nt "$target" ]]; then
            if [[ "$DRY_RUN" == "true" ]]; then
                _sync_new "[dry-run] Actualizaría compose.yml de ${svc_name}"
                return 0
            fi
            _catalogize_compose "$compose_file" > "$target"
            _sync_ok "compose.yml actualizado para ${svc_name} (extends adaptado al catálogo)"
        else
            _sync_skip "compose.yml sin cambios para ${svc_name}"
        fi
    else
        if [[ "$DRY_RUN" == "true" ]]; then
            _sync_new "[dry-run] Copiaría compose.yml de ${svc_name}"
            return 0
        fi
        mkdir -p "${CATALOG_DIR}/${svc_name}"
        _catalogize_compose "$compose_file" > "$target"
        _sync_new "compose.yml copiado para ${svc_name} (extends adaptado al catálogo)"
    fi
}

# Generar .env.example sanitizado
_sync_env_example() {
    local svc_name="$1"
    local svc_dir="${DOCKER_BASE}/${svc_name}"
    local target="${CATALOG_DIR}/${svc_name}/.env.example"

    if [[ ! -f "${svc_dir}/.env" ]]; then
        return 0
    fi

    if [[ -f "$target" ]]; then
        _sync_skip ".env.example ya existe para ${svc_name}"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        _sync_new "[dry-run] Generaría .env.example de ${svc_name}"
        return 0
    fi

    mkdir -p "${CATALOG_DIR}/${svc_name}"

    local secret_patterns="PASSWORD|SECRET|TOKEN|COOKIE|KEY|PASS"

    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
            echo "$line"
        elif [[ "$line" =~ ^([A-Z_]+)= ]]; then
            local key="${BASH_REMATCH[1]}"
            if [[ "$key" =~ ($secret_patterns) ]]; then
                echo "${key}=__pega_aqui__"
            else
                echo "$line"
            fi
        else
            echo "$line"
        fi
    done < "${svc_dir}/.env" > "$target"

    _sync_new ".env.example generado para ${svc_name}"
}

# Generar guía placeholder
_generate_guide_placeholder() {
    local svc_name="$1"
    local compose_file="$2"
    local target="${DOCS_DIR}/${svc_name}-guide.md"

    if [[ -f "$target" ]]; then
        _sync_skip "guía ya existe para ${svc_name}"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        _sync_new "[dry-run] Generaría guía placeholder para ${svc_name}"
        return 0
    fi

    mkdir -p "$DOCS_DIR"

    _extract_from_compose "$compose_file" "$svc_name"

    cat > "$target" <<EOF
# ${CONTAINER_NAME:-$svc_name} — Guía Operativa

> **Puerto:** ${PORT_MAIN:-N/A}
> **Imagen:** ${IMAGE}
> **Red:** ${NETWORKS_LIST:-bridge}
> **Instalado por:** DebMenux / manual
> **Tipo:** Docker container

---

## Qué es

_(Completar: qué hace este servicio y por qué está en el NAS)_

---

## Instalación

\`\`\`bash
mkdir -p \$dkco/${svc_name}/data
# Copiar compose.yml y .env
dk ${svc_name} && svc up ${svc_name}
\`\`\`

---

## Configuración

_(Completar: parámetros importantes, variables de entorno, config files)_

---

## Backup y recuperación

\`\`\`bash
svc backup ${svc_name}
\`\`\`

_(Completar: qué respaldar, frecuencia, cómo restaurar)_

---

## Troubleshooting

_(Completar: errores encontrados y cómo se resolvieron)_

---

> **Nota:** Esta guía fue generada automáticamente por \`catalog-sync\`.
> Completar con información operativa real según se use el servicio.
> Fecha de generación: $(date +%Y-%m-%d)
EOF

    _sync_new "guía placeholder generada: ${target}"
}

# Generar script DebMenux placeholder
_generate_debmenux_script() {
    local svc_name="$1"
    local compose_file="$2"
    local target="${DEBMENUX_SCRIPTS}/${svc_name}.sh"

    # Solo generar si DebMenux está instalado
    if [[ ! -d "/debmenux/scripts/services" ]]; then
        return 0
    fi

    if [[ -f "$target" ]]; then
        _sync_skip "script DebMenux ya existe para ${svc_name}"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        _sync_new "[dry-run] Generaría script DebMenux para ${svc_name}"
        return 0
    fi

    _extract_from_compose "$compose_file" "$svc_name"

    cat > "$target" <<EOF
#!/usr/bin/env bash
# ==========================================================
# DebMenux — Servicio: ${CONTAINER_NAME:-$svc_name}
# ==========================================================
# Auto-generado por catalog-sync el $(date +%Y-%m-%d)
# Completar install_service() con la lógica real.
# ==========================================================

APP="${CONTAINER_NAME:-$svc_name}"
APP_ID="${svc_name}"
CATEGORY="sin-categorizar"
IMAGE="${IMAGE}"
PORT_WEB="\${PORT_WEB:-${PORT_MAIN:-8080}}"

var_cpu="\${var_cpu:-1}"
var_ram="\${var_ram:-512M}"

NETWORKS=(${NETWORKS_LIST})

install_service() {
    local svc_dir="\${DOCKER_DIR}/\${APP_ID}"

    msg_info "Creando directorios para \${APP}"
    mkdir -p "\${svc_dir}/data"
    msg_ok "Directorios creados 📁"

    for net in "\${NETWORKS[@]}"; do
        ensure_network "\$net"
    done

    msg_info "Copiando compose.yml desde catálogo"
    if [[ -f "${CATALOG_DIR}/${svc_name}/compose.yml" ]]; then
        # El catálogo usa ../../_common.yml; el servicio desplegado necesita ../_common.yml.
        sed -E 's#^([[:space:]]*file:[[:space:]]*)\.\./\.\./_common\.yml([[:space:]]*)\$#\1../_common.yml\2#' \
            "${CATALOG_DIR}/${svc_name}/compose.yml" > "\${svc_dir}/compose.yml"
    else
        msg_error "No se encontró compose.yml en el catálogo"
        return 1
    fi
    msg_ok "compose.yml copiado 📄"

    if [[ -f "${CATALOG_DIR}/${svc_name}/.env.example" ]]; then
        cp "${CATALOG_DIR}/${svc_name}/.env.example" "\${svc_dir}/.env"
        secure_env "\${svc_dir}/.env"
        msg_warn "⚠️  Editar .env con valores reales: nano \${svc_dir}/.env"
    fi

    msg_info "Iniciando \${APP}"
    docker compose -f "\${svc_dir}/compose.yml" up -d
    msg_ok "\${APP} iniciado 🟢"

    local server_ip
    server_ip=\$(get_server_ip)
    echo -e ""
    msg_success "\${APP} instalado! 🚀"
    echo -e "\${TAB}\${BOLD}🌐 Acceso:\${CL} \${BL}http://\${server_ip}:\${PORT_WEB}\${CL}"
    echo -e ""

    register_to_catalog
}

update_service() {
    local svc_dir="\${DOCKER_DIR}/\${APP_ID}"
    if [[ ! -f "\${svc_dir}/compose.yml" ]]; then
        msg_error "No se encontró instalación de \${APP}."
        return 1
    fi
    msg_info "Actualizando \${APP}"
    docker compose -f "\${svc_dir}/compose.yml" pull
    docker compose -f "\${svc_dir}/compose.yml" up -d --force-recreate
    msg_ok "\${APP} actualizado 🆙"
}
EOF

    chmod +x "$target"
    _sync_new "script DebMenux generado: ${target}"
}

# Actualizar SKILL.md con la tabla de servicios
_update_skill_table() {
    if [[ "$DRY_RUN" == "true" ]]; then
        _sync_new "[dry-run] Actualizaría tabla en SKILL.md"
        return 0
    fi

    if [[ ! -f "$SKILL_FILE" ]]; then
        _sync_warn "SKILL.md no encontrado en ${SKILL_FILE}"
        return 0
    fi

    # Recolectar todos los servicios con guía
    local new_table=""
    for guide in "${DOCS_DIR}"/*-guide.md; do
        [[ -f "$guide" ]] || continue
        local svc_name
        svc_name=$(basename "$guide" | sed 's/-guide\.md//')
        local guide_rel="docs/services/${svc_name}-guide.md"

        # Verificar si ya está en SKILL.md
        if ! grep -q "$guide_rel" "$SKILL_FILE" 2>/dev/null; then
            # Extraer primera línea después del título para descripción
            local desc
            desc=$(grep -m1 "^>" "$guide" | sed 's/^> //' | cut -c1-60)
            new_table="${new_table}| **${svc_name}** | \`${guide_rel}\` | ${desc:-Auto-generado, completar} |\n"
        fi
    done

    if [[ -n "$new_table" ]]; then
        # Insertar antes de "### Hechos críticos"
        if grep -q "### Hechos críticos" "$SKILL_FILE"; then
            sed -i "/### Hechos críticos/i \\
${new_table}" "$SKILL_FILE"
            _sync_ok "SKILL.md actualizado con servicios nuevos"
        else
            _sync_warn "No se encontró '### Hechos críticos' en SKILL.md — agregar manualmente"
        fi
    else
        _sync_skip "SKILL.md ya tiene todos los servicios"
    fi
}

# ==============================================================================
# COMANDO PRINCIPAL
# ==============================================================================

catalog_sync() {
    local target_service="${1:-}"
    local services_found=0
    local services_new=0

    # Parsear flags
    case "$target_service" in
        --dry-run)
            DRY_RUN=true
            target_service=""
            ;;
        --status)
            _catalog_status
            return 0
            ;;
        --help|-h)
            echo "Uso: svc catalog-sync [servicio|--dry-run|--status]"
            echo ""
            echo "  (sin args)     Sincronizar todos los servicios"
            echo "  <servicio>     Sincronizar uno específico"
            echo "  --dry-run      Mostrar qué haría sin ejecutar"
            echo "  --status       Mostrar estado de documentación"
            return 0
            ;;
    esac

    echo ""
    echo "  ━━━ 📋 catalog-sync: Auto-documentación en cascada ━━━"
    echo ""

    if [[ -n "$target_service" ]]; then
        # Un solo servicio: resolver cualquiera de los nombres Compose válidos.
        local compose
        compose=$(svc_compose_file "$target_service")
        if [[ -z "$compose" ]]; then
            _sync_warn "No se encontró compose para ${target_service}"
            return 1
        fi
        _sync_service "$target_service" "$compose"
    else
        # Todos los servicios: svc_list() ya acepta las cuatro variantes.
        local svc_name compose
        while IFS= read -r svc_name; do
            [[ -z "$svc_name" ]] && continue
            [[ "$svc_name" == "backups" || "$svc_name" == "cli" ]] && continue
            compose=$(svc_compose_file "$svc_name")
            [[ -z "$compose" ]] && continue

            ((services_found++))
            _sync_service "$svc_name" "$compose"
        done < <(svc_list)
    fi

    # Actualizar SKILL.md al final
    echo ""
    _update_skill_table

    # Notificar (si ntfy disponible y no es dry-run)
    if [[ "$DRY_RUN" != "true" && "$services_new" -gt 0 ]]; then
        if command -v curl &>/dev/null && [[ -n "${NTFY_URL:-}" ]]; then
            source "${NAS_DOTFILES:-/nas-dotfiles}/docker/cli/lib/notifications.sh" 2>/dev/null
            ntfy_send "docker" "📋 catalog-sync" "${services_new} servicio(s) documentado(s)" "default" "books"
        fi
    fi

    echo ""
    echo "  ━━━ Resultado: ${services_found} servicios encontrados ━━━"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  (modo dry-run — nada fue modificado)"
    fi
    echo ""
}

_sync_service() {
    local svc_name="$1"
    local compose_file="$2"

    echo "  ┌─ ${svc_name}"

    # 1. Ficha
    _generate_ficha_from_compose "$svc_name" "$compose_file"

    # 2. Compose al catálogo
    _sync_compose "$svc_name" "$compose_file"

    # 3. .env.example
    _sync_env_example "$svc_name"

    # 4. Guía placeholder
    _generate_guide_placeholder "$svc_name" "$compose_file"

    # 5. Script DebMenux
    _generate_debmenux_script "$svc_name" "$compose_file"

    echo "  └─ done"
    echo ""
}

# ==============================================================================
# STATUS: Mostrar qué servicios tienen/faltan documentación
# ==============================================================================

_catalog_status() {
    echo ""
    echo "  ━━━ 📊 Estado de documentación de servicios ━━━"
    echo ""
    printf "  %-16s %-8s %-8s %-8s %-8s %-10s\n" "SERVICIO" "COMPOSE" "FICHA" "GUÍA" "DEBMENU" "HOMEPAGE"
    echo "  ──────────────────────────────────────────────────────────────────"

    local svc compose
    while IFS= read -r svc; do
        [[ -z "$svc" ]] && continue
        [[ "$svc" == "backups" || "$svc" == "cli" ]] && continue
        compose=$(svc_compose_file "$svc")
        [[ -z "$compose" ]] && continue

        local has_compose="✅"
        local has_ficha=$(  [[ -f "${CATALOG_DIR}/${svc}/ficha.md" ]]     && echo "✅" || echo "❌")
        local has_guide=$(  [[ -f "${DOCS_DIR}/${svc}-guide.md" ]]        && echo "✅" || echo "❌")
        local has_debmenu=$([[ -f "${DEBMENUX_SCRIPTS}/${svc}.sh" ]]      && echo "✅" || echo "❌")
        local has_homepage=$(grep -qc 'homepage\.' "$compose" 2>/dev/null  && echo "✅" || echo "❌")

        printf "  %-16s %-8s %-8s %-8s %-8s %-10s\n" "$svc" "$has_compose" "$has_ficha" "$has_guide" "$has_debmenu" "$has_homepage"
    done < <(svc_list)

    echo ""
    echo "  Leyenda: COMPOSE=en \$dkco | FICHA=catálogo agente | GUÍA=docs/ | DEBMENU=/debmenux | HOMEPAGE=labels"
    echo "  Ejecutar 'svc catalog-sync' para generar lo que falta."
    echo ""
}



# ==============================================================================
# REGENERAR nas-context.md (skill compacta para LLMs)
# ==============================================================================

_regenerate_nas_context() {
    local context_file="${NAS_DOTFILES:-/nas-dotfiles}/docker-nas/references/nas-context.md"

    if [[ "$DRY_RUN" == "true" ]]; then
        _sync_new "[dry-run] Regeneraría nas-context.md"
        return 0
    fi

    # Recolectar servicios activos
    local services_table=""
    local svc compose
    while IFS= read -r svc; do
        [[ -z "$svc" ]] && continue
        [[ "$svc" == "backups" || "$svc" == "cli" ]] && continue
        compose=$(svc_compose_file "$svc")
        [[ -z "$compose" ]] && continue

        # Puerto principal
        local port
        port=$(grep -m1 -oP '"\K\d+(?=:\d+")' "$compose" 2>/dev/null || echo "—")

        # Redes
        local nets
        nets=$(grep -A10 'networks:' "$compose" | grep -oP '^\s+- \K\w+' | grep -v 'driver\|external' | tr '\n' ',' | sed 's/,$//')
        [[ -z "$nets" ]] && nets="bridge"

        # Homepage labels
        local hp="❌"
        grep -q 'homepage\.' "$compose" 2>/dev/null && hp="✅ labels"

        services_table="${services_table}| ${svc} | ${port} | ${nets} | Docker | ${hp} |\n"
    done < <(svc_list)

    # Agregar usb-api (nativo)
    if systemctl is-active --quiet usb-api.service 2>/dev/null; then
        services_table="${services_table}| usb-api | 8091 | — | systemd nativo | services.yaml |\n"
    fi

    # Escribir fecha de actualización en el archivo existente
    if [[ -f "$context_file" ]]; then
        sed -i "s/^> Última actualización:.*/> Última actualización: $(date +%Y-%m-%d)/" "$context_file"
        _sync_ok "nas-context.md fecha actualizada"
    fi
}
