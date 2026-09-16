#!/usr/bin/env bash
# Detecta Compose que no heredan los defaults de _common.yml.
set -Eeuo pipefail

: "${DOCKER_BASE:=${dkco:-/docker}}"

printf '=== Compose sin extends a _common.yml ===\n'
found=0

while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  if ! grep -Eq '^[[:space:]]+extends:[[:space:]]*$|^[[:space:]]+extends:' "$file"; then
    svc=$(basename "$(dirname "$file")")
    restart=$(grep -E '^[[:space:]]+restart:' "$file" | head -1 | sed 's/^[[:space:]]*//')
    printf '  %-24s %s (%s)\n' "$svc" "${restart:-restart: no declarado}" "$file"
    found=1
  fi
done < <(find "$DOCKER_BASE" -mindepth 2 -maxdepth 2 -type f \
  \( -name compose.yml -o -name compose.yaml \
     -o -name docker-compose.yml -o -name docker-compose.yaml \) \
  -print 2>/dev/null | sort)

if ((found == 0)); then
  echo '  Ninguno.'
fi
