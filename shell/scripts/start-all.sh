#!/usr/bin/env bash
# Compatibilidad: el arranque canónico ahora vive en boot-order.sh.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/boot-order.sh" "$@"
