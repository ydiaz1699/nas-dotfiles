#!/usr/bin/env bash
# Simulador seguro de install_docker.sh.
# No instala paquetes, no inicia servicios, no ejecuta Docker y no modifica /etc.

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="$ROOT_DIR/shell/scripts/install_docker.sh"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/simulate-install-docker.XXXXXX")"
PASS_COUNT=0
FAIL_COUNT=0

cleanup() {
  rm -rf "$TEST_ROOT"
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

pass() {
  echo "PASS: $*"
  PASS_COUNT=$((PASS_COUNT + 1))
}

assert_contains() {
  local text="$1"
  local expected="$2"
  local description="$3"

  if grep -Fq -- "$expected" <<< "$text"; then
    pass "$description"
  else
    fail "$description (no apareció: $expected)"
  fi
}

assert_status() {
  local expected="$1"
  local actual="$2"
  local description="$3"

  if [[ "$actual" -eq "$expected" ]]; then
    pass "$description"
  else
    fail "$description (esperado=$expected, obtenido=$actual)"
  fi
}

write_os_release() {
  local path="$1"
  local os_id="$2"
  local codename="$3"

  printf 'ID=%s\nVERSION_CODENAME=%s\nPRETTY_NAME="Test %s %s"\n' \
    "$os_id" "$codename" "$os_id" "$codename" > "$path"
}

run_installer() {
  local os_release="$1"
  local sources_dir="$2"
  local keyrings_dir="$3"
  local log_file="$4"
  shift 4

  DOCKER_INSTALL_DRY_RUN=1 \
  DOCKER_INSTALL_ASSUME_DOCKER_ABSENT=1 \
  DOCKER_INSTALL_OS_RELEASE="$os_release" \
  DOCKER_INSTALL_APT_SOURCES_DIR="$sources_dir" \
  DOCKER_INSTALL_APT_KEYRINGS_DIR="$keyrings_dir" \
  DOCKER_INSTALL_LOG="$log_file" \
    bash "$INSTALLER" --dry-run "$@"
}

test_help() {
  local output
  output=$(bash "$INSTALLER" --help)
  assert_contains "$output" "--dry-run" "La ayuda expone --dry-run"
  assert_contains "$output" "--log-file" "La ayuda expone --log-file"
}

test_valid_debian() {
  local case_dir="$TEST_ROOT/valid"
  local os_release="$case_dir/os-release"
  local sources_dir="$case_dir/sources.list.d"
  local keyrings_dir="$case_dir/keyrings"
  local log_file="$case_dir/install.log"
  local output

  mkdir -p "$sources_dir" "$keyrings_dir"
  write_os_release "$os_release" debian trixie
  printf '%s\n' 'deb https://download.docker.com/linux/debian trixie stable' \
    > "$sources_dir/docker.list"

  if output=$(run_installer "$os_release" "$sources_dir" "$keyrings_dir" "$log_file" 2>&1); then
    pass "La simulación de Debian trixie termina correctamente"
  else
    fail "La simulación de Debian trixie falló"
  fi

  assert_contains "$output" "Modo simulación" "La salida indica que no se ejecutan cambios"
  assert_contains "$output" "curl -fsSLI" "La simulación muestra la comprobación de conectividad"
  assert_contains "$output" "apt install" "La simulación muestra la instalación prevista"
  assert_contains "$output" "docker run --rm hello-world" "La simulación muestra la prueba hello-world"
  assert_contains "$output" "Simulación terminada sin cambios" "La salida incluye el resumen simulado"

  if [[ -f "$sources_dir/docker.list" && ! -e "$sources_dir/docker.sources" ]]; then
    pass "El modo simulación no modifica el repositorio legacy ni crea docker.sources"
  else
    fail "El modo simulación modificó los archivos de repositorio"
  fi

  if [[ -s "$log_file" ]]; then
    pass "La simulación genera el archivo de log"
  else
    fail "La simulación no generó el archivo de log"
  fi
}

test_invalid_os() {
  local case_dir="$TEST_ROOT/invalid-os"
  local os_release="$case_dir/os-release"
  local output
  local status=0

  mkdir -p "$case_dir"
  write_os_release "$os_release" ubuntu jammy

  output=$(run_installer "$os_release" "$case_dir/sources" "$case_dir/keyrings" "$case_dir/install.log" 2>&1) || status=$?

  assert_status 1 "$status" "Se rechaza un sistema que no es Debian"
  assert_contains "$output" "Sistema no compatible" "El error de sistema no compatible es claro"
}

test_invalid_codename() {
  local case_dir="$TEST_ROOT/invalid-codename"
  local os_release="$case_dir/os-release"
  local output
  local status=0

  mkdir -p "$case_dir"
  write_os_release "$os_release" debian sid

  output=$(run_installer "$os_release" "$case_dir/sources" "$case_dir/keyrings" "$case_dir/install.log" 2>&1) || status=$?

  assert_status 1 "$status" "Se rechaza un codename no soportado"
  assert_contains "$output" "Codename de Debian no soportado" "El error de codename no soportado es claro"
}

test_explicit_user() {
  local case_dir="$TEST_ROOT/user"
  local os_release="$case_dir/os-release"
  local output
  local test_user="nobody"

  mkdir -p "$case_dir"
  write_os_release "$os_release" debian bookworm

  if ! getent passwd "$test_user" >/dev/null 2>&1; then
    echo "SKIP: no existe el usuario de prueba '$test_user'"
    return 0
  fi

  if output=$(DOCKER_INSTALL_USER="$test_user" run_installer \
      "$os_release" "$case_dir/sources" "$case_dir/keyrings" "$case_dir/install.log" 2>&1); then
    pass "La simulación acepta un usuario explícito existente"
  else
    fail "La simulación rechazó un usuario explícito existente"
  fi

  assert_contains "$output" "Usuario seleccionado por configuración: $test_user" \
    "La salida identifica el usuario seleccionado"
  assert_contains "$output" "usermod -aG docker $test_user" \
    "La simulación muestra la modificación del grupo"
}

test_help
test_valid_debian
test_invalid_os
test_invalid_codename
test_explicit_user

echo ""
echo "Resultado: $PASS_COUNT pruebas correctas, $FAIL_COUNT fallos."

if [[ "$FAIL_COUNT" -ne 0 ]]; then
  exit 1
fi
