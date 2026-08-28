"""Gateway MCP estrecho para consultar el framework nas-dotfiles desde LobeHub.

El proceso HTTP no tiene acceso al Docker socket ni ejecuta comandos del cliente.
Cuando ``MCP_HELPER_SOCKET`` está definido, delega a un helper host mediante un
Unix socket con un protocolo de una línea y una allowlist idéntica. El helper es
el único proceso que puede invocar ``svc lobehub`` y siempre usa argumentos
constantes.

Transportes soportados:
  - ``MCP_MODE=http``: Streamable HTTP mínimo en ``/mcp`` para LobeHub Web.
  - ``MCP_MODE=stdio``: MCP sobre stdin/stdout para clientes locales.
  - ``MCP_MODE=helper``: helper host restringido por Unix socket.

No se exponen operaciones de backup ni mutación.
"""
from __future__ import annotations

import argparse
import hmac
import http.server
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "nas-dotfiles-lobehub-gateway"
SERVER_VERSION = "1.0.0"
MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
MAX_HELPER_LINE_BYTES = 64 * 1024

# Esta lista es una frontera de seguridad, no una lista de sugerencias.
# Si se agrega una operación, debe añadirse aquí, documentarse y validarse.
PUBLIC_OPERATIONS: Dict[str, Dict[str, Any]] = {
    "lobehub_preflight": {
        "svc_action": "preflight",
        "capability_id": "lobehub.preflight",
        "description": "Valida la configuración local de LobeHub sin mostrar secretos.",
        "timeout": 60,
    },
    "lobehub_verify": {
        "svc_action": "verify",
        "capability_id": "lobehub.verify",
        "description": "Comprueba el runtime de LobeHub, Redis, PostgreSQL y avisos sanitizados.",
        "timeout": 120,
    },
    "lobehub_status": {
        "svc_action": "status",
        "capability_id": "lobehub.status",
        "description": "Devuelve el estado resumido de los contenedores de LobeHub.",
        "timeout": 30,
    },
    "lobehub_providers": {
        "svc_action": "providers",
        "capability_id": "lobehub.providers",
        "description": "Clasifica avisos de proveedores, QStash y marketplace sin volcar logs.",
        "timeout": 45,
    },
    "capabilities": {
        "svc_action": None,
        "capability_id": None,
        "description": "Descubre únicamente las capacidades read-only conectadas del framework.",
        "timeout": 30,
    },
}

TOOL_NAMES = frozenset(PUBLIC_OPERATIONS)
PATH_RE = re.compile(r"(?:/home/[^\s]+|/docker/[^\s]+|/nas-dotfiles/[^\s]+)")
IP_RE = re.compile(r"(?<![\w])(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?![\w])")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _redact_text(value: str) -> str:
    """Redacta rutas, IPs y valores con forma de secreto antes de responder."""
    value = PATH_RE.sub("<path>", value)
    value = IP_RE.sub("<address>", value)
    value = re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1<redacted>", value)
    return value[:500]


def _audit_path() -> Path:
    configured = os.environ.get("MCP_AUDIT_LOG", "").strip()
    if configured:
        return Path(configured)
    return Path.home() / ".nas-agent" / "lobehub-mcp-audit.jsonl"


def audit(event: str, tool: str, outcome: str, duration_ms: int = 0) -> None:
    """Registra metadatos sin argumentos, secretos ni stdout del helper."""
    path = _audit_path()
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        "tool": tool,
        "outcome": outcome,
        "duration_ms": max(0, duration_ms),
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        old_umask = os.umask(0o077)
        try:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            try:
                path.chmod(0o600)
            except OSError:
                pass
        finally:
            os.umask(old_umask)
    except OSError:
        # Un fallo del log no debe convertir un endpoint read-only en un
        # endpoint que revele información. El fallo queda en stderr del proceso.
        print("lobehub-mcp: no se pudo escribir el audit log", file=sys.stderr)


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": code, "message": message}


def _check_lines(stdout: str) -> list[Dict[str, str]]:
    """Convierte solo las líneas de resultado conocidas a datos estructurados."""
    checks: list[Dict[str, str]] = []
    pattern = re.compile(r"^\s*(?:✅|⚠️|❌)\s+([A-Za-z0-9_.:-]+)\s+(.*)$")
    for line in stdout.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        marker = line.lstrip()[:1]
        state = {"✅": "pass", "⚠": "warn", "❌": "fail"}.get(marker, "unknown")
        checks.append(
            {
                "name": match.group(1)[:80],
                "state": state,
                "detail": _redact_text(match.group(2)),
            }
        )
    return checks[:100]


def _status_services(stdout: str) -> list[Dict[str, str]]:
    """Extrae solo servicio/estado/health de ``docker compose ps``."""
    known = {
        "lobehub-rustfs-init": "rustfs-init",
        "lobehub-rustfs": "rustfs",
        "lobehub-mcp": "mcp",
        "lobehub": "lobehub",
    }
    result: list[Dict[str, str]] = []
    for line in stdout.splitlines():
        if line.startswith("NAME") or not line.strip():
            continue
        first_column = line.split(None, 1)[0]
        service = known.get(first_column)
        if service is None:
            continue
        lowered = line.lower()
        if "up" in lowered or "running" in lowered:
            state = "running"
        elif "exited" in lowered or "created" in lowered or "dead" in lowered:
            state = "stopped"
        else:
            state = "unknown"
        if "(healthy)" in lowered:
            health = "healthy"
        elif "(unhealthy)" in lowered:
            health = "unhealthy"
        else:
            health = "unknown"
        result.append({"service": service, "state": state, "health": health})
    return result


def _safe_capabilities() -> Dict[str, Any]:
    """Lee manifests y valida source/dispatch/guard sin importar código del checkout."""
    try:
        repo = Path(os.environ.get("NAS_DOTFILES", "")).resolve()
        capabilities_dir = repo / "agent" / "capabilities"
        if not repo.exists() or not capabilities_dir.is_dir():
            raise OSError("capabilities no disponible")
        allowed_ids = {
            spec["capability_id"]
            for spec in PUBLIC_OPERATIONS.values()
            if spec["capability_id"]
        }
        operations = []
        dispatch_pattern = re.compile(
            r"^\s*(?:[\w-]+\|)*([a-z][\w-]*)(?:\|[\w-]+)*\)",
            re.MULTILINE,
        )
        for manifest_path in sorted(capabilities_dir.glob("*.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            source = str(manifest.get("source", ""))
            source_path = (repo / source).resolve()
            try:
                source_inside_repo = source_path.is_relative_to(repo)
            except AttributeError:  # Python 3.10 compatibility
                source_inside_repo = str(source_path).startswith(str(repo) + os.sep)
            source_exists = bool(source) and source_inside_repo and source_path.is_file()
            source_text = source_path.read_text(encoding="utf-8") if source_exists else ""
            for item in manifest.get("operations", []):
                if item.get("id") not in allowed_ids:
                    continue
                action = str(item.get("id", "")).rsplit(".", 1)[-1]
                dispatch_exists = bool(
                    source_exists
                    and any(match.group(1) == action for match in dispatch_pattern.finditer(source_text))
                )
                guard_valid = (
                    item.get("mode") == "read_only"
                    and not item.get("confirm")
                    and "--confirm" not in str(item.get("command", ""))
                )
                operations.append(
                    {
                        "id": item.get("id"),
                        "service": manifest.get("service", ""),
                        "mode": "read_only",
                        "connected": bool(source_exists and dispatch_exists and guard_valid),
                        "description": _redact_text(str(item.get("description", ""))),
                    }
                )
        return {
            "ok": True,
            "framework": "nas-dotfiles",
            "mutations_exposed": False,
            "capabilities": operations,
            "not_exposed": [
                "lobehub.backup-db",
                "lobehub.repair-storage",
                "lobehub.reconcile-db",
            ],
        }
    except (OSError, TypeError, ValueError):
        audit("capabilities", "capabilities", "manifest_error")
        return {
            "ok": False,
            "error": "capabilities_unavailable",
            "message": "No se pudo verificar el inventario read-only del framework.",
        }


def _run_svc(action: str, timeout: int) -> Dict[str, Any]:
    """Ejecuta un único comando fijo; nunca incorpora argumentos del cliente."""
    repo = Path(os.environ.get("NAS_DOTFILES", "")).resolve()
    script = repo / "docker" / "cli" / "svc.sh"
    if not repo.exists() or not script.is_file():
        return _error("framework_unavailable", "No está disponible el entrypoint del framework.")

    env = os.environ.copy()
    env["NAS_DOTFILES"] = str(repo)
    env.setdefault("DOCKER_BASE", "/docker")
    env["LC_ALL"] = "C.UTF-8"
    started = time.monotonic()
    try:
        completed = subprocess.run(
            ["/bin/bash", str(script), "lobehub", action],
            cwd=str(repo),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _error("operation_timeout", "La comprobación excedió su tiempo máximo.")
    except OSError:
        return _error("framework_unavailable", "No se pudo iniciar la comprobación del framework.")

    duration_ms = int((time.monotonic() - started) * 1000)
    if action == "status":
        payload: Dict[str, Any] = {
            "ok": completed.returncode == 0,
            "operation": "lobehub_status",
            "services": _status_services(completed.stdout),
        }
    else:
        payload = {
            "ok": completed.returncode == 0,
            "operation": f"lobehub_{action if action != 'providers' else 'providers'}",
            "checks": _check_lines(completed.stdout),
        }
    if completed.returncode != 0 and not payload.get("checks") and not payload.get("services"):
        payload["error"] = "operation_failed"
        payload["message"] = "La comprobación read-only terminó con error; consulte el NAS."
    payload["duration_ms"] = duration_ms
    return payload


def _local_operation(operation: str) -> Dict[str, Any]:
    if operation == "capabilities":
        return _safe_capabilities()
    spec = PUBLIC_OPERATIONS.get(operation)
    if spec is None or not spec.get("svc_action"):
        return _error("operation_not_allowed", "La operación no está publicada.")
    return _run_svc(str(spec["svc_action"]), int(spec["timeout"]))


def _helper_request(operation: str, socket_path: str, timeout: int) -> Dict[str, Any]:
    if operation not in TOOL_NAMES:
        return _error("operation_not_allowed", "La operación no está publicada.")
    message = _json_bytes({"operation": operation}) + b"\n"
    if len(message) > MAX_HELPER_LINE_BYTES:
        return _error("request_too_large", "Solicitud demasiado grande.")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(socket_path)
            client.sendall(message)
            data = bytearray()
            while len(data) <= MAX_RESPONSE_BYTES:
                chunk = client.recv(8192)
                if not chunk:
                    break
                data.extend(chunk)
                if b"\n" in chunk:
                    break
        line = bytes(data).split(b"\n", 1)[0]
        if len(line) > MAX_RESPONSE_BYTES:
            return _error("response_too_large", "Respuesta demasiado grande.")
        value = json.loads(line.decode("utf-8"))
        return value if isinstance(value, dict) else _error("invalid_helper_response", "Respuesta inválida del helper.")
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return _error("helper_unavailable", "El helper read-only del NAS no está disponible.")


class Gateway:
    def __init__(self, helper_socket: Optional[str] = None, *, from_helper: bool = False) -> None:
        self.helper_socket = (
            None
            if from_helper
            else helper_socket or os.environ.get("MCP_HELPER_SOCKET", "").strip() or None
        )

    def call(self, operation: str, arguments: Any = None) -> Dict[str, Any]:
        started = time.monotonic()
        if operation not in TOOL_NAMES:
            audit("tool_call", operation, "denied")
            return _error("operation_not_allowed", "La operación no está publicada.")
        if arguments not in (None, {}):
            audit("tool_call", operation, "invalid_arguments")
            return _error("arguments_not_allowed", "Esta integración no acepta argumentos del cliente.")
        timeout = int(PUBLIC_OPERATIONS[operation]["timeout"])
        if self.helper_socket:
            result = _helper_request(operation, self.helper_socket, timeout)
        else:
            result = _local_operation(operation)
        outcome = "ok" if result.get("ok") else str(result.get("error", "failed"))
        audit("tool_call", operation, outcome, int((time.monotonic() - started) * 1000))
        return result


def _tool_schema(name: str) -> Dict[str, Any]:
    spec = PUBLIC_OPERATIONS[name]
    return {
        "name": name,
        "description": (
            f"{spec['description']} No acepta argumentos, rutas, comandos, SQL ni flags. "
            "Solo devuelve datos sanitizados."
        ),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    }


def _rpc_result(request_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _rpc_error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_rpc(message: Any, gateway: Gateway) -> Optional[Dict[str, Any]]:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _rpc_error(None, -32600, "Invalid Request")
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    if not isinstance(params, dict):
        return _rpc_error(request_id, -32602, "Invalid params")

    if method == "initialize":
        return _rpc_result(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "instructions": "Gateway read-only de nas-dotfiles; las mutaciones no están expuestas.",
            },
        )
    if method in {"notifications/initialized", "notifications/cancelled", "ping"}:
        if request_id is None:
            return None
        return _rpc_result(request_id, {})
    if method == "tools/list":
        return _rpc_result(request_id, {"tools": [_tool_schema(name) for name in PUBLIC_OPERATIONS]})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or name not in TOOL_NAMES:
            return _rpc_error(request_id, -32602, "Tool not available")
        result = gateway.call(name, arguments)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        tool_result = {
            "content": [{"type": "text", "text": text}],
            "structuredContent": result,
            "isError": not bool(result.get("ok")),
        }
        return _rpc_result(request_id, tool_result)
    return _rpc_error(request_id, -32601, "Method not found")


def _origin_allowed(headers: Mapping[str, str]) -> bool:
    origin = headers.get("Origin", "").strip()
    if not origin:
        return True  # LobeHub server-to-server no envía Origin.
    allowed = {
        item.strip()
        for item in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",")
        if item.strip()
    }
    return bool(allowed) and origin in allowed


def _authorized(headers: Mapping[str, str]) -> bool:
    expected = os.environ.get("MCP_SERVICE_TOKEN", "")
    presented = headers.get("Authorization", "")
    if not expected or not presented.startswith("Bearer "):
        return False
    return hmac.compare_digest(presented[7:].strip(), expected)


class MCPHTTPHandler(http.server.BaseHTTPRequestHandler):
    gateway: Gateway
    endpoint: str = "/mcp"

    def log_message(self, format: str, *args: Any) -> None:
        # No request line, URLs, headers ni cuerpos: podrían contener credenciales.
        print("lobehub-mcp: http request", file=sys.stderr)

    def _send_json(self, status: int, payload: Any, *, content_type: str = "application/json") -> None:
        body = _json_bytes(payload)
        if len(body) > MAX_RESPONSE_BYTES:
            body = _json_bytes(_error("response_too_large", "Respuesta demasiado grande."))
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)
        origin = self.headers.get("Origin", "")
        if origin and _origin_allowed(self.headers):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Expose-Headers", "MCP-Protocol-Version")
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def _authorized_request(self) -> bool:
        if not _origin_allowed(self.headers):
            self._send_json(403, _error("origin_not_allowed", "Origin no permitido."))
            return False
        if not _authorized(self.headers):
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Bearer")
            origin = self.headers.get("Origin", "")
            if origin and _origin_allowed(self.headers):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Expose-Headers", "MCP-Protocol-Version")
                self.send_header("Vary", "Origin")
            self.end_headers()
            audit("http_auth", "http", "denied")
            return False
        return True

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not _origin_allowed(self.headers):
            self._send_json(403, _error("origin_not_allowed", "Origin no permitido."))
            return
        self.send_response(204)
        self.send_header("Allow", "POST, GET, OPTIONS")
        self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)
        origin = self.headers.get("Origin", "")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, MCP-Protocol-Version")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            # Health no revela estado del NAS; sirve solo para Docker healthcheck.
            self._send_json(200, {"ok": True, "service": SERVER_NAME})
            return
        if self.path.rstrip("/") != self.endpoint.rstrip("/"):
            self._send_json(404, _error("not_found", "Ruta no encontrada."))
            return
        if not self._authorized_request():
            return
        # Este gateway no inicia streams servidor→cliente. MCP permite que el
        # cliente rechace GET cuando no necesita recibir notificaciones SSE.
        self.send_response(405)
        self.send_header("Allow", "POST, OPTIONS")
        self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != self.endpoint.rstrip("/"):
            self._send_json(404, _error("not_found", "Ruta no encontrada."))
            return
        if not self._authorized_request():
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._send_json(413, _error("request_too_large", "Solicitud ausente o demasiado grande."))
            return
        try:
            message = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, _rpc_error(None, -32700, "Parse error"))
            return
        if isinstance(message, list):
            self._send_json(400, _rpc_error(None, -32600, "Batch requests are not supported"))
            return
        response = handle_rpc(message, self.gateway)
        if response is None:
            self.send_response(202)
            self.end_headers()
            return
        self._send_json(200, response)


def run_http(gateway: Gateway) -> int:
    if not os.environ.get("MCP_SERVICE_TOKEN"):
        print("lobehub-mcp: MCP_SERVICE_TOKEN es obligatorio en modo HTTP", file=sys.stderr)
        return 2
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8790"))
    endpoint = os.environ.get("MCP_PATH", "/mcp")
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    handler = type("ConfiguredMCPHTTPHandler", (MCPHTTPHandler,), {})
    handler.gateway = gateway
    handler.endpoint = endpoint
    server = http.server.ThreadingHTTPServer((host, port), handler)
    print(f"lobehub-mcp: HTTP escuchando en {host}:{port}{endpoint}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


def _helper_client(conn: socket.socket, gateway: Gateway) -> None:
    conn.settimeout(90)
    try:
        data = bytearray()
        while len(data) <= MAX_HELPER_LINE_BYTES:
            chunk = conn.recv(8192)
            if not chunk:
                break
            data.extend(chunk)
            if b"\n" in chunk:
                break
        line = bytes(data).split(b"\n", 1)[0]
        if len(line) > MAX_HELPER_LINE_BYTES:
            result = _error("request_too_large", "Solicitud demasiado grande.")
        else:
            try:
                request = json.loads(line.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                request = None
            if not isinstance(request, dict) or set(request) != {"operation"}:
                result = _error("invalid_helper_request", "Solicitud del gateway inválida.")
            else:
                operation = request.get("operation")
                result = gateway.call(operation) if isinstance(operation, str) else _error(
                    "operation_not_allowed", "La operación no está publicada."
                )
        conn.sendall(_json_bytes(result) + b"\n")
    except OSError:
        pass
    finally:
        conn.close()


def run_helper(gateway: Gateway) -> int:
    socket_path = os.environ.get("MCP_HELPER_SOCKET", "").strip()
    if not socket_path:
        print("lobehub-mcp: MCP_HELPER_SOCKET es obligatorio en modo helper", file=sys.stderr)
        return 2
    path = Path(socket_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        print(f"lobehub-mcp: no se pudo preparar el socket: {exc}", file=sys.stderr)
        return 2

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(socket_path)
    socket_gid = os.environ.get("MCP_SOCKET_GID", "").strip()
    if not socket_gid.isdigit():
        print("lobehub-mcp: MCP_SOCKET_GID debe ser el GID del grupo dedicado", file=sys.stderr)
        server.close()
        try:
            path.unlink()
        except OSError:
            pass
        return 2
    try:
        os.chown(socket_path, -1, int(socket_gid))
        os.chmod(socket_path, 0o660)
    except OSError as exc:
        print(f"lobehub-mcp: no se pudo asignar el grupo del socket: {exc}", file=sys.stderr)
        server.close()
        try:
            path.unlink()
        except OSError:
            pass
        return 2
    server.listen(8)
    stop = threading.Event()

    def _stop(_signum: int, _frame: Any) -> None:
        stop.set()
        try:
            server.close()
        except OSError:
            pass

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    print("lobehub-mcp: helper Unix socket listo", file=sys.stderr)
    try:
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except OSError:
                if stop.is_set():
                    break
                continue
            thread = threading.Thread(target=_helper_client, args=(conn, gateway), daemon=True)
            thread.start()
    finally:
        server.close()
        try:
            path.unlink()
        except OSError:
            pass
    return 0


def run_stdio(gateway: Gateway) -> int:
    """Servidor MCP newline-delimited JSON-RPC sin escribir nada en stdout salvo respuestas."""
    for line in sys.stdin:
        if len(line.encode("utf-8")) > MAX_REQUEST_BYTES:
            response = _rpc_error(None, -32600, "Request too large")
        else:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                response = _rpc_error(None, -32700, "Parse error")
            else:
                response = handle_rpc(message, gateway)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Gateway MCP read-only de nas-dotfiles para LobeHub")
    parser.add_argument("--mode", choices=("http", "stdio", "helper"), default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    mode = args.mode or os.environ.get("MCP_MODE", "stdio").strip().lower()
    gateway = Gateway(from_helper=mode == "helper")
    if mode == "http":
        return run_http(gateway)
    if mode == "helper":
        return run_helper(gateway)
    return run_stdio(gateway)


if __name__ == "__main__":
    raise SystemExit(main())
