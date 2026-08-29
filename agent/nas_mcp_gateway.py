"""Front-door MCP lazy para nas-dotfiles.

El front-door mantiene disponible el catálogo MCP, pero no inicia el worker que
habla con el helper host hasta recibir el primer ``tools/call``. El worker se
cierra tras un periodo de inactividad configurable. Este proceso no ejecuta
Docker ni acepta comandos/rutas del cliente.
"""

from __future__ import annotations

import argparse
import hmac
import http.server
import json
import os
import selectors
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional

PROTOCOL_VERSION = "2025-03-26"
MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
DEFAULT_IDLE_SECONDS = 600
DEFAULT_HTTP_PATH = "/mcp"


class ManifestError(RuntimeError):
    pass


def _manifest_path() -> Path:
    configured = os.environ.get("NAS_MCP_MANIFEST", "").strip()
    return Path(configured) if configured else Path(__file__).with_name("nas_mcp_manifest.json")


def load_manifest() -> Dict[str, Any]:
    try:
        manifest = json.loads(_manifest_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError("No se pudo cargar el manifest canónico de nas-mcp-gateway") from exc
    tools = manifest.get("tools")
    server = manifest.get("server")
    if not isinstance(server, dict) or not isinstance(server.get("name"), str) or not isinstance(server.get("version"), str):
        raise ManifestError("El manifest no contiene metadatos válidos del servidor")
    if not isinstance(tools, list) or not tools:
        raise ManifestError("El manifest no contiene herramientas")
    names: set[str] = set()
    operations: set[str] = set()
    for tool in tools:
        if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
            raise ManifestError("Herramienta inválida en el manifest")
        name = tool["name"]
        operation = tool.get("operation")
        if name in names or not isinstance(operation, str) or operation in operations:
            raise ManifestError("Herramientas duplicadas o sin operación")
        names.add(name)
        operations.add(operation)
    try:
        from nas_mcp_worker import OPERATIONS
    except (ImportError, OSError) as exc:
        raise ManifestError("No se pudo cargar la allowlist del worker") from exc
    worker_operations = set(OPERATIONS)
    if operations != worker_operations:
        raise ManifestError("El manifest y la allowlist del worker no coinciden")
    return manifest


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": code, "message": message}


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _tool_schema(tool: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "name": tool["name"],
        "description": (
            f"{tool['description']} No acepta rutas, comandos, SQL ni flags. "
            "La operación es read-only y puede activar el worker lazy."
        ),
        "inputSchema": tool["input_schema"],
    }


class WorkerSupervisor:
    """Inicia un worker solo al primer uso y lo apaga tras inactividad."""

    def __init__(self, manifest: Mapping[str, Any]) -> None:
        activation = manifest.get("activation", {})
        configured_idle = os.environ.get("NAS_MCP_IDLE_SECONDS", "").strip()
        try:
            self.idle_seconds = max(
                30,
                int(configured_idle or activation.get("idle_seconds", DEFAULT_IDLE_SECONDS)),
            )
        except (TypeError, ValueError):
            self.idle_seconds = DEFAULT_IDLE_SECONDS
        self.worker_path = Path(__file__).with_name("nas_mcp_worker.py")
        self.process: Optional[subprocess.Popen[str]] = None
        self.last_used = 0.0
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.reaper = threading.Thread(target=self._reap_idle, name="nas-mcp-worker-reaper", daemon=True)
        self.reaper.start()

    def _reap_idle(self) -> None:
        interval = max(1, min(30, self.idle_seconds // 2))
        while not self.stop_event.wait(interval):
            with self.lock:
                if self.process is not None and self.last_used and time.monotonic() - self.last_used >= self.idle_seconds:
                    self._stop_unlocked()

    def _stop_unlocked(self) -> None:
        process = self.process
        self.process = None
        if process is None:
            return
        try:
            process.terminate()
            process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
            try:
                process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                pass

    def stop(self) -> None:
        with self.lock:
            self._stop_unlocked()

    def _start_unlocked(self) -> bool:
        if self.process is not None and self.process.poll() is None:
            return True
        self._stop_unlocked()
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(self.worker_path), "--mode", "client"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                env=os.environ.copy(),
            )
        except OSError:
            self.process = None
            return False
        self.last_used = time.monotonic()
        return True

    def _readline_with_timeout_unlocked(self, process: subprocess.Popen[str], timeout: int) -> Optional[str]:
        if process.stdout is None:
            return None
        selector = selectors.DefaultSelector()
        try:
            selector.register(process.stdout, selectors.EVENT_READ)
            events = selector.select(timeout=max(1, timeout))
            if not events:
                return None
            line = process.stdout.readline()
            return line if line else None
        finally:
            selector.close()

    def request(self, operation: str, timeout: int) -> Dict[str, Any]:
        with self.lock:
            now = time.monotonic()
            if self.process is not None and now - self.last_used >= self.idle_seconds:
                self._stop_unlocked()
            if not self._start_unlocked():
                return _error("worker_unavailable", "No se pudo iniciar el worker lazy.")
            assert self.process is not None
            process = self.process
            if process.stdin is None:
                self._stop_unlocked()
                return _error("worker_unavailable", "El worker no tiene stdin disponible.")
            try:
                process.stdin.write(json.dumps({"operation": operation}) + "\n")
                process.stdin.flush()
                line = self._readline_with_timeout_unlocked(process, timeout)
            except (BrokenPipeError, OSError):
                line = None
            self.last_used = time.monotonic()
            if line is None:
                self._stop_unlocked()
                return _error("worker_timeout", "El worker no respondió dentro del tiempo permitido.")
            try:
                result = json.loads(line)
            except json.JSONDecodeError:
                self._stop_unlocked()
                return _error("worker_invalid_response", "El worker devolvió una respuesta inválida.")
            return result if isinstance(result, dict) else _error("worker_invalid_response", "Respuesta inválida del worker.")

    def shutdown(self) -> None:
        self.stop_event.set()
        self.stop()


class Gateway:
    def __init__(self, manifest: Mapping[str, Any]) -> None:
        self.manifest = manifest
        self.tools = {tool["name"]: tool for tool in manifest["tools"]}
        self.worker = WorkerSupervisor(manifest)

    def call(self, name: str, arguments: Any) -> Dict[str, Any]:
        tool = self.tools.get(name)
        if tool is None:
            return _error("tool_not_available", "La herramienta no está publicada.")
        if arguments not in (None, {}):
            return _error("arguments_not_allowed", "Esta versión no acepta argumentos del cliente.")
        timeout = int(tool.get("timeout_seconds", 30))
        return self.worker.request(str(tool["operation"]), timeout)

    def close(self) -> None:
        self.worker.shutdown()


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
                "serverInfo": {
                    "name": gateway.manifest["server"]["name"],
                    "version": gateway.manifest["server"]["version"],
                },
                "instructions": "Gateway read-only de nas-dotfiles con worker lazy; las mutaciones no están expuestas.",
            },
        )
    if method in {"notifications/initialized", "notifications/cancelled", "ping"}:
        return None if request_id is None else _rpc_result(request_id, {})
    if method == "tools/list":
        return _rpc_result(request_id, {"tools": [_tool_schema(tool) for tool in gateway.manifest["tools"]]})
    if method == "tools/call":
        name = params.get("name")
        if not isinstance(name, str):
            return _rpc_error(request_id, -32602, "Tool name is required")
        result = gateway.call(name, params.get("arguments", {}))
        return _rpc_result(
            request_id,
            {
                "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                "structuredContent": result,
                "isError": not bool(result.get("ok")),
            },
        )
    return _rpc_error(request_id, -32601, "Method not found")


class StdioServer:
    def __init__(self, gateway: Gateway) -> None:
        self.gateway = gateway

    def run(self) -> int:
        try:
            for line in sys.stdin:
                if len(line.encode("utf-8")) > MAX_REQUEST_BYTES:
                    response = _rpc_error(None, -32600, "Request too large")
                else:
                    try:
                        message = json.loads(line)
                        response = handle_rpc(message, self.gateway)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response = _rpc_error(None, -32700, "Parse error")
                if response is not None:
                    body = _json_bytes(response)
                    if len(body) > MAX_RESPONSE_BYTES:
                        body = _json_bytes(_rpc_error(None, -32603, "Response too large"))
                    sys.stdout.buffer.write(body + b"\n")
                    sys.stdout.buffer.flush()
        finally:
            self.gateway.close()
        return 0


class HTTPHandler(http.server.BaseHTTPRequestHandler):
    gateway: Gateway
    endpoint = DEFAULT_HTTP_PATH

    def log_message(self, _format: str, *_args: Any) -> None:
        print("nas-mcp-gateway: http request", file=sys.stderr)

    def _authorized(self) -> bool:
        expected = os.environ.get("MCP_SERVICE_TOKEN", "")
        presented = self.headers.get("Authorization", "")
        return bool(expected and presented.startswith("Bearer ") and hmac.compare_digest(presented[7:].strip(), expected))

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin", "").strip()
        if not origin:
            return True
        allowed = {
            item.strip()
            for item in os.environ.get("MCP_ALLOWED_ORIGINS", "").split(",")
            if item.strip()
        }
        return origin in allowed

    def _send_json(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("MCP-Protocol-Version", PROTOCOL_VERSION)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            self._send_json(200, {"ok": True, "service": "nas-mcp-gateway"})
            return
        if not self._origin_allowed():
            self._send_json(403, _error("origin_not_allowed", "Origin no permitido."))
            return
        self._send_json(401 if not self._authorized() else 405, _rpc_error(None, -32001, "MCP endpoint requires POST"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != self.endpoint.rstrip("/"):
            self._send_json(404, _error("not_found", "Ruta no encontrada."))
            return
        if not self._origin_allowed():
            self._send_json(403, _error("origin_not_allowed", "Origin no permitido."))
            return
        if not self._authorized():
            self.send_response(401)
            self.send_header("WWW-Authenticate", "Bearer")
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._send_json(413, _rpc_error(None, -32600, "Request too large"))
            return
        try:
            message = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, _rpc_error(None, -32700, "Parse error"))
            return
        response = handle_rpc(message, self.gateway)
        if response is None:
            self.send_response(202)
            self.end_headers()
            return
        self._send_json(200, response)


def run_http(gateway: Gateway) -> int:
    if not os.environ.get("MCP_SERVICE_TOKEN"):
        print("nas-mcp-gateway: MCP_SERVICE_TOKEN es obligatorio en modo HTTP", file=sys.stderr)
        return 2
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8790"))
    endpoint = os.environ.get("MCP_PATH", DEFAULT_HTTP_PATH)
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    handler = type("ConfiguredHTTPHandler", (HTTPHandler,), {})
    handler.gateway = gateway
    handler.endpoint = endpoint
    server = http.server.ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        gateway.close()
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="nas-mcp-gateway: front-door MCP read-only lazy")
    parser.add_argument("--mode", choices=("stdio", "http"), default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        manifest = load_manifest()
    except ManifestError as exc:
        print(f"nas-mcp-gateway: {exc}", file=sys.stderr)
        return 2
    gateway = Gateway(manifest)
    mode = args.mode or os.environ.get("NAS_MCP_MODE", "stdio").strip().lower()
    if mode == "http":
        return run_http(gateway)
    return StdioServer(gateway).run()


if __name__ == "__main__":
    raise SystemExit(main())
