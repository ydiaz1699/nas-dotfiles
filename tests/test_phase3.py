"""Tests para Phase 3: plugins, event bus, scheduler, cache."""

import time
import pytest
from agent.events.bus import EventBus, Event
from agent.cache.store import Cache
from agent.plugins.base import BasePlugin, PluginMeta, ScheduleConfig, EventHandler
from agent.plugins.loader import PluginLoader


class TestEventBus:
    """Tests para EventBus."""

    def test_emit_y_handler(self):
        bus = EventBus()
        received = []
        bus.on("test.event", lambda e: received.append(e))
        bus.emit("test.event", {"key": "value"})
        assert len(received) == 1
        assert received[0].type == "test.event"
        assert received[0].data["key"] == "value"

    def test_wildcard_handler(self):
        bus = EventBus()
        received = []
        bus.on("docker.*", lambda e: received.append(e))
        bus.emit("docker.unhealthy", {"service": "emqx"})
        bus.emit("docker.started", {"service": "n8n"})
        bus.emit("mqtt.message", {})  # No debería matchear
        assert len(received) == 2

    def test_global_handler(self):
        bus = EventBus()
        received = []
        bus.on("*", lambda e: received.append(e))
        bus.emit("any.event")
        bus.emit("another.one")
        assert len(received) == 2

    def test_off_desregistra(self):
        bus = EventBus()
        received = []
        handler = lambda e: received.append(e)
        bus.on("test", handler)
        bus.emit("test")
        assert len(received) == 1
        bus.off("test", handler)
        bus.emit("test")
        assert len(received) == 1  # No incrementa

    def test_history(self):
        bus = EventBus(history_size=5)
        for i in range(10):
            bus.emit("test", {"i": i})
        assert bus.event_count == 10
        assert len(bus.history) == 5
        assert bus.history[0].data["i"] == 5  # Solo últimos 5

    def test_last_events_filtrado(self):
        bus = EventBus()
        bus.emit("a.event")
        bus.emit("b.event")
        bus.emit("a.event")
        assert len(bus.last_events(10, event_type="a.event")) == 2


class TestCache:
    """Tests para Cache."""

    def test_set_get(self):
        cache = Cache(ttl_seconds=60)
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_ttl_expiry(self):
        cache = Cache(ttl_seconds=1)
        cache.set("key", "value")
        # Forzar entrada ya expirada manipulando el store directamente
        cache._store["key"]["expires"] = time.time() - 1
        assert cache.get("key") is None

    def test_invalidate(self):
        cache = Cache()
        cache.set("key", "value")
        assert cache.invalidate("key") is True
        assert cache.get("key") is None

    def test_invalidate_prefix(self):
        cache = Cache()
        cache.set("ports.tcp", [80])
        cache.set("ports.udp", [53])
        cache.set("services.list", [])
        count = cache.invalidate_prefix("ports.")
        assert count == 2
        assert cache.get("services.list") == []

    def test_stats(self):
        cache = Cache()
        cache.set("a", 1)
        cache.get("a")       # hit
        cache.get("b")       # miss
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_clear(self):
        cache = Cache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert len(cache.keys()) == 0


class TestBasePlugin:
    """Tests para BasePlugin."""

    def test_plugin_basico(self):
        class MyPlugin(BasePlugin):
            meta = PluginMeta(name="test", version="1.0.0")
            def setup(self):
                self.register_tool(lambda: None)

        p = MyPlugin()
        p.setup()
        assert p.name == "test"
        assert len(p.tools) == 1

    def test_plugin_con_schedule(self):
        class ScheduledPlugin(BasePlugin):
            meta = PluginMeta(name="scheduled")
            def setup(self):
                self.register_schedule(ScheduleConfig(
                    name="my-task",
                    handler=lambda: None,
                    interval_minutes=10,
                ))

        p = ScheduledPlugin()
        p.setup()
        assert len(p.schedules) == 1
        assert p.schedules[0].name == "my-task"

    def test_plugin_con_event(self):
        class EventPlugin(BasePlugin):
            meta = PluginMeta(name="evented")
            def setup(self):
                self.register_event(EventHandler(
                    event_type="test.event",
                    handler=lambda e: None,
                ))

        p = EventPlugin()
        p.setup()
        assert len(p.event_handlers) == 1


class TestPluginLoader:
    """Tests para PluginLoader."""

    def test_load_plugin_manual(self):
        class TestPlugin(BasePlugin):
            meta = PluginMeta(name="manual-test", version="0.1.0")
            def setup(self):
                self.register_tool(lambda: "hello")

        loader = PluginLoader()
        instance = loader.load_plugin(TestPlugin)
        assert instance is not None
        assert "manual-test" in loader.plugins
        assert len(loader.all_tools()) == 1

    def test_unload_plugin(self):
        class TempPlugin(BasePlugin):
            meta = PluginMeta(name="temp")

        loader = PluginLoader()
        loader.load_plugin(TempPlugin)
        assert "temp" in loader.plugins
        loader.unload_plugin("temp")
        assert "temp" not in loader.plugins

    def test_summary(self):
        class SummaryPlugin(BasePlugin):
            meta = PluginMeta(name="summary-test", description="For testing")

        loader = PluginLoader()
        loader.load_plugin(SummaryPlugin)
        summary = loader.summary()
        assert "summary-test" in summary
        assert "For testing" in summary
