"""
test_tool_result.py — Tests para la dataclass ToolResult.
"""

from agent.core._result import Status, Timer, ToolResult


class TestToolResultOk:
    def test_ok_is_success(self):
        r = ToolResult.ok("Todo bien")
        assert r.success is True
        assert r.status == Status.OK

    def test_ok_str(self):
        r = ToolResult.ok("Mensaje bonito", data={"port": 8080})
        assert str(r) == "Mensaje bonito"

    def test_ok_data(self):
        r = ToolResult.ok("OK", data={"key": "value"})
        assert r.data["key"] == "value"

    def test_ok_suggestions(self):
        r = ToolResult.ok("OK", suggestions=["hacer backup"])
        assert "hacer backup" in r.suggestions


class TestToolResultError:
    def test_error_not_success(self):
        r = ToolResult.error("Algo falló")
        assert r.success is False
        assert r.status == Status.ERROR

    def test_error_str(self):
        r = ToolResult.error("No encontrado")
        assert str(r) == "No encontrado"


class TestToolResultWarn:
    def test_warn_is_success(self):
        r = ToolResult.warn("Cuidado")
        assert r.success is True
        assert r.status == Status.WARNING


class TestToolResultSerialization:
    def test_to_dict(self):
        r = ToolResult.ok("Test", data={"x": 1}, tool_name="my_tool")
        d = r.to_dict()
        assert d["success"] is True
        assert d["status"] == "ok"
        assert d["data"] == {"x": 1}
        assert d["tool_name"] == "my_tool"

    def test_repr(self):
        r = ToolResult.ok("Test", data={"a": 1, "b": 2}, tool_name="t")
        rep = repr(r)
        assert "success=True" in rep
        assert "data_keys=" in rep


class TestTimer:
    def test_timer_measures_time(self):
        import time
        with Timer() as t:
            time.sleep(0.05)
        assert t.elapsed_ms >= 40  # al menos 40ms (con margen)
        assert t.elapsed_ms < 200  # no más de 200ms
