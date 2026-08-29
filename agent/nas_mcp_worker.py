"""Worker y helper read-only para nas-mcp-gateway.

El front-door MCP no ejecuta Docker ni acepta comandos del cliente. En el primer
``tools/call`` inicia este proceso en modo ``client``; el proceso solo puede
enviar una operación de la allowlist al helper Unix. El modo ``helper`` es el
proceso host controlado por systemd y ejecuta comandos fijos de ``svc``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

MAX_LINE_BYTES = 64 * 1024
MAX_OUTPUT_LINES = 80
MAX_OUTPUT_LINE_BYTES = 500
DEFAULT_SOCKET = "/run/nas/nas-mcp-gateway.sock"

OPERATIONS: Dict[str, Dict[str, Any]] = {
    "nas_services": {"svc_args": ("lista",), "timeout": 30},
    "nas_health": {"svc_args": ("health",), "timeout": 60},
    "nas_capabilities": {"svc_args": ("capabilities",), "timeout": 30},
    "nas_diagnostics": {"svc_args": ("doctor",), "timeout": 120},
}

PATH_RE = re.compile(r"(?:/home/[^\s]+|/docker/[^\s]+|/nas-dotfiles/[^\s]+)")
IP_RE = re.compile(r"(?<![\w])(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?![\w])")


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": code, "message": message}


def _redact(value: str) -> str:
    value = PATH_RE.sub("<path>", value)
    value = IP_RE.sub("<address>", value)
    value = re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1<redacted>", value)
    value = re.sub(r"(?i)(password|secret|token|api[_-]?key)=([^\s]+)", r"\1=<redacted>", value)
    return value[:MAX_OUTPUT_LINE_BYTES]


def _safe_output(stdout: str) -> list[str]:
    lines = [_redact(line) for line in stdout.splitlines()[:MAX_OUTPUT_LINES]]
    if len(stdout.splitlines()) > MAX_OUTPUT_LINES:
        lines.append("<output_truncated>")
    return lines


def _audit(operation: str, outcome: str, duration_ms: int = 0) -> None:
    configured = os.environ.get("MCP_AUDIT_LOG", "").strip()
    if not configured:
        return
    path = Path(configured)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": operation,
        "outcome": outcome,
        "duration_ms": max(0, duration_ms),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        old_umask = os.umask(0o077)
        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            path.chmod(0o600)
        finally:
            os.umask(old_umask)
    except OSError:
        pass


def _run_fixed_svc(operation: str) -> Dict[str, Any]:
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return _error("operation_not_allowed", "La operación no está publicada.")

    spec = OPERATIONS[operation]
    repo = Path(os.environ.get("NAS_DOTFILES", "")).resolve()
    script = repo / "docker" / "cli" / "svc.sh"
    if not repo.is_dir() or not script.is_file():
        result = _error("framework_unavailable", "No está disponible el entrypoint del framework.")
        _audit(operation, result["error"])
        return result

    env = os.environ.copy()
    env["NAS_DOTFILES"] = str(repo)
    env["DOCKER_BASE"] = env.get("DOCKER_BASE", "").strip() or "/docker"
    env["NAS_CLI"] = "bash"
    env["LC_ALL"] = "C.UTF-8"
    if operation == "nas_diagnostics":
        # `svc doctor` normalmente guarda doctor-history.log. El gateway no
        # debe modificar el NAS: el CLI omite ese historial en esta llamada.
        env["SVC_DOCTOR_NO_HISTORY"] = "1"
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["/bin/bash", str(script), *spec["svc_args"]],
            cwd=str(repo),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=int(spec["timeout"]),
            check=False,
        )
    except subprocess.TimeoutExpired:
        result = _error("operation_timeout", "La operación excedió su tiempo máximo.")
        _audit(operation, result["error"])
        return result
    except OSError:
        result = _error("framework_unavailable", "No se pudo iniciar la operación del framework.")
        _audit(operation, result["error"])
        return result

    duration_ms = int((time.monotonic() - started) * 1000)
    payload: Dict[str, Any] = {
        "ok": completed.returncode == 0,
        "operation": operation,
        "duration_ms": duration_ms,
        "output": _safe_output(completed.stdout),
    }
    if completed.returncode != 0:
        payload["error"] = "operation_failed"
        payload["message"] = "La operación read-only terminó con error; consulte el NAS."
    _audit(operation, "ok" if payload["ok"] else str(payload["error"]), duration_ms)
    return payload


def _socket_path() -> str:
    return os.environ.get("MCP_HELPER_SOCKET", "").strip() or DEFAULT_SOCKET


def _helper_request(operation: str, timeout: int) -> Dict[str, Any]:
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return _error("operation_not_allowed", "La operación no está publicada.")
    request = json.dumps({"operation": operation}, separators=(",", ":")).encode() + b"\n"
    if len(request) > MAX_LINE_BYTES:
        return _error("request_too_large", "Solicitud demasiado grande.")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(_socket_path())
            client.sendall(request)
            data = bytearray()
            while len(data) <= MAX_LINE_BYTES:
                chunk = client.recv(8192)
                if not chunk:
                    break
                data.extend(chunk)
                if b"\n" in chunk:
                    break
        line = bytes(data).split(b"\n", 1)[0]
        if len(line) > MAX_LINE_BYTES:
            return _error("response_too_large", "Respuesta demasiado grande.")
        value = json.loads(line.decode("utf-8"))
        return value if isinstance(value, dict) else _error("invalid_helper_response", "Respuesta inválida del helper.")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return _error("helper_unavailable", "El helper read-only del NAS no está disponible.")


def _client_loop() -> int:
    for line in sys.stdin:
        if len(line.encode("utf-8")) > MAX_LINE_BYTES:
            result = _error("request_too_large", "Solicitud demasiado grande.")
        else:
            try:
                request = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                request = None
            if not isinstance(request, dict) or set(request) != {"operation"}:
                result = _error("invalid_worker_request", "Solicitud interna inválida.")
            else:
                operation = request.get("operation")
                timeout = int(OPERATIONS.get(str(operation), {}).get("timeout", 30))
                result = _helper_request(operation, timeout) if isinstance(operation, str) else _error(
                    "operation_not_allowed", "La operación no está publicada."
                )
        sys.stdout.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n")
        sys.stdout.flush()
    return 0


def _serve_helper() -> int:
    socket_path = _socket_path()
    path = Path(socket_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        return 2

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_path)
    socket_gid = os.environ.get("MCP_SOCKET_GID", "").strip()
    if not socket_gid.isdigit():
        server.close()
        path.unlink(missing_ok=True)
        print("nas-mcp-gateway: MCP_SOCKET_GID inválido", file=sys.stderr)
        return 2
    try:
        os.chown(socket_path, -1, int(socket_gid))
        os.chmod(socket_path, 0o660)
    except OSError:
        server.close()
        path.unlink(missing_ok=True)
        return 2

    server.listen(8)
    stopping = False

    def stop(_signum: int, _frame: Any) -> None:
        nonlocal stopping
        stopping = True
        try:
            server.close()
        except OSError:
            pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print("nas-mcp-gateway: helper Unix socket listo", file=sys.stderr)
    try:
        while not stopping:
            try:
                conn, _ = server.accept()
            except OSError:
                if stopping:
                    break
                continue
            with conn:
                conn.settimeout(90)
                data = bytearray()
                try:
                    while len(data) <= MAX_LINE_BYTES:
                        chunk = conn.recv(8192)
                        if not chunk:
                            break
                        data.extend(chunk)
                        if b"\n" in chunk:
                            break
                    line = bytes(data).split(b"\n", 1)[0]
                    request = json.loads(line.decode("utf-8")) if len(line) <= MAX_LINE_BYTES else None
                    if not isinstance(request, dict) or set(request) != {"operation"}:
                        result = _error("invalid_helper_request", "Solicitud del gateway inválida.")
                    else:
                        operation = request.get("operation")
                        result = _run_fixed_svc(operation) if isinstance(operation, str) else _error(
                            "operation_not_allowed", "La operación no está publicada."
                        )
                except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                    result = _error("invalid_helper_request", "Solicitud del gateway inválida.")
                try:
                    conn.sendall(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode() + b"\n")
                except OSError:
                    pass
    finally:
        server.close()
        path.unlink(missing_ok=True)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Worker read-only de nas-mcp-gateway")
    parser.add_argument("--mode", choices=("client", "helper"), default="client")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.mode == "helper":
        return _serve_helper()
    return _client_loop()


if __name__ == "__main__":
    raise SystemExit(main())
