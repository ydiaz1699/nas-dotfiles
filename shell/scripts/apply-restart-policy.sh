#!/usr/bin/env bash
# Migra contenedores existentes a on-failure:5 sin arrancar todos los servicios.
# La configuración Compose debe declarar la misma policy para contenedores nuevos.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
: "${NAS_DOTFILES:=$REPO_ROOT}"
: "${DOCKER_BASE:=${dkco:-/docker}}"
export NAS_DOTFILES DOCKER_BASE

REPORT="${RESTART_POLICY_REPORT:-$DOCKER_BASE/scripts/restart-policy-report.txt}"
TARGET_NAME="on-failure"
TARGET_RETRIES="5"

mkdir -p "$(dirname "$REPORT")"
: > "$REPORT"

svc_cli() {
  NAS_CLI=bash "$NAS_DOTFILES/docker/cli/svc.sh" "$@"
}

compose_services() {
  find "$DOCKER_BASE" -mindepth 2 -maxdepth 2 -type f \
    \( -name compose.yml -o -name compose.yaml \
       -o -name docker-compose.yml -o -name docker-compose.yaml \) \
    -printf '%h\n' 2>/dev/null \
    | awk -F/ '{print $NF}' | sort -u
}

printf 'servicio|contenedor|policy_original|acción\n' >> "$REPORT"
failed=0
MANAGED=()

while IFS= read -r svc; do
  [[ -n "$svc" ]] || continue
  echo "-> $svc"
  mapfile -t containers < <(svc_cli ps "$svc" -q 2>/dev/null || true)

  if ((${#containers[@]} == 0)); then
    printf '%s|—|—|sin contenedor existente; se aplicará al próximo svc up\n' "$svc" >> "$REPORT"
    continue
  fi

  for cid in "${containers[@]}"; do
    MANAGED+=("$cid")
    name=$(docker inspect -f '{{.Name}}' "$cid" | sed 's#^/##')
    policy=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$cid")
    retries=$(docker inspect -f '{{.HostConfig.RestartPolicy.MaximumRetryCount}}' "$cid")

    # Jobs de inicialización (por ejemplo rustfs-init) deben seguir siendo no.
    if [[ "$policy" == "no" ]]; then
      printf '%s|%s|%s|conservado (job one-shot)\n' "$svc" "$name" "$policy" >> "$REPORT"
      continue
    fi

    if [[ "$policy" == "$TARGET_NAME" && "$retries" == "$TARGET_RETRIES" ]]; then
      printf '%s|%s|%s:%s|ya correcto\n' "$svc" "$name" "$policy" "$retries" >> "$REPORT"
      continue
    fi

    if docker update --restart "${TARGET_NAME}:${TARGET_RETRIES}" "$cid" >/dev/null; then
      new_policy=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$cid")
      new_retries=$(docker inspect -f '{{.HostConfig.RestartPolicy.MaximumRetryCount}}' "$cid")
      printf '%s|%s|%s:%s|migrado a %s:%s\n' "$svc" "$name" "$policy" "$retries" "$new_policy" "$new_retries" >> "$REPORT"
    else
      printf '%s|%s|%s:%s|ERROR: docker update falló\n' "$svc" "$name" "$policy" "$retries" >> "$REPORT"
      failed=1
    fi
  done
done < <(compose_services)

printf '\n=== Reporte ===\n'
if command -v column >/dev/null 2>&1; then
  column -t -s '|' "$REPORT"
else
  cat "$REPORT"
fi

# Verificación final basada en el ESTADO REAL de los contenedores, no en el
# texto del reporte: la columna policy_original es solo informativa.
pending=0
for cid in "${MANAGED[@]}"; do
  final_policy=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$cid" 2>/dev/null || echo desconocido)
  case "$final_policy" in
    "$TARGET_NAME"|no) ;;  # on-failure migrado, o job one-shot conservado
    *)
      name=$(docker inspect -f '{{.Name}}' "$cid" 2>/dev/null | sed 's#^/##')
      echo "ERROR: ${name:-$cid} sigue con restart policy '$final_policy'."
      pending=1
      ;;
  esac
done

if ((pending != 0)); then
  failed=1
fi

if ((failed != 0)); then
  echo
  echo 'Migración incompleta: revisa el reporte y los contenedores marcados.'
  exit 1
fi

echo
echo "Migración terminada. Reporte: $REPORT"
