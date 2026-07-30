"""Tests para ToolResult dataclass."""

import pytest
from agent.core._result import ToolResult, Status, Timer
import time


class TestToolResult:
    """Tests para ToolResult."""

    def test_ok_basico(self):
        r = ToolResult.ok("todo bien")
        assert r.success is True
        assert r.status == Status.OK
        assert r.message == "todo bien"
        assert str(r) == "todo bien"

    def test_error_basico(self):
        r = ToolResult.error("algo falló")
        assert r.success is False
        assert r.status == Status.ERROR
        assert str(r) == "algo falló"

    def test_warn_basico(self):
        r = ToolResult.warn("cuidado")
        assert r.success is True
        assert r.status == Status.WARNING

    def test_ok_con_data(self):
        r = ToolResult.ok("listo", data={"service": "emqx", "port": 1883})
        assert r.data["service"] == "emqx"
        assert r.data["port"] == 1883

    def test_ok_con_suggestions(self):
        r = ToolResult.ok("listo", suggestions=["siguiente paso"])
        assert "siguiente paso" in r.suggestions

    def test_ok_con_elapsed(self):
        r = ToolResult.ok("listo", elapsed_ms=123.45)
        assert r.elapsed_ms == 123.45

    def test_ok_con_tool_name(self):
        r = ToolResult.ok("listo", tool_name="service_restart")
        assert r.tool_name == "service_restart"

    def test_to_dict(self):
        r = ToolResult.ok("test", data={"k": "v"}, tool_name="t")
        d = r.to_dict()
        assert d["success"] is True
        assert d["status"] == "ok"
        assert d["message"] == "test"
        assert d["data"] == {"k": "v"}
        assert d["tool_name"] == "t"

    def test_str_backward_compat(self):
        """Verificar que str() retorna solo el mensaje (compat con Strands)."""
        r = ToolResult.ok("✅ Servicio reiniciado", data={"x": 1})
        # Strands SDK convierte el return a string
        assert str(r) == "✅ Servicio reiniciado"

    def test_defaults(self):
        r = ToolResult(success=True, message="m")
        assert r.status == Status.OK
        assert r.data == {}
        assert r.suggestions == []
        assert r.elapsed_ms is None
        assert r.tool_name == ""


class TestTimer:
    """Tests para Timer context manager."""

    def test_timer_mide_tiempo(self):
        with Timer() as t:
            time.sleep(0.01)  # 10ms
        assert t.elapsed_ms >= 5  # Al menos 5ms (slack por scheduler)
        assert t.elapsed_ms < 500  # No debería tomar medio segundo

    def test_timer_zero_sin_sleep(self):
        with Timer() as t:
            pass
        assert t.elapsed_ms >= 0
        assert t.elapsed_ms < 50  # Casi instantáneo
