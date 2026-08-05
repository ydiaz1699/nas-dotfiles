"""
test_memory.py — Tests para el sistema de memoria (MemoryManager).
"""

import re
from pathlib import Path

from agent.core._result import Status
from agent.core.memory import MemoryManager


class TestEnsureInitialized:
    def test_creates_files(self, isolate_memory):
        """ensure_initialized crea MEMORY.md, USER.md, SKILLS.md, sessions/."""
        MemoryManager.ensure_initialized()
        assert (isolate_memory / "MEMORY.md").exists()
        assert (isolate_memory / "USER.md").exists()
        assert (isolate_memory / "SKILLS.md").exists()
        assert (isolate_memory / "sessions").is_dir()

    def test_idempotent(self, isolate_memory):
        """Llamar dos veces no duplica contenido."""
        MemoryManager.ensure_initialized()
        content1 = (isolate_memory / "MEMORY.md").read_text()
        MemoryManager.ensure_initialized()
        content2 = (isolate_memory / "MEMORY.md").read_text()
        assert content1 == content2


class TestAddToMemory:
    def test_add_leccion(self, isolate_memory):
        result = MemoryManager.add_to_memory(
            "emqx necesita 512MB", "leccion", "2026-08-01T10:00:00"
        )
        assert result.success
        content = (isolate_memory / "MEMORY.md").read_text()
        assert "emqx necesita 512MB" in content
        assert "[2026-08-01]" in content

    def test_add_entorno(self, isolate_memory):
        result = MemoryManager.add_to_memory(
            "Docker v24.0.7", "entorno", "2026-08-01T10:00:00"
        )
        assert result.success
        content = (isolate_memory / "MEMORY.md").read_text()
        assert "Docker v24.0.7" in content

    def test_invalid_category(self, isolate_memory):
        result = MemoryManager.add_to_memory(
            "algo", "categoria_inventada", "2026-08-01T10:00:00"
        )
        assert not result.success
        assert result.status == Status.ERROR

    def test_too_long(self, isolate_memory):
        result = MemoryManager.add_to_memory(
            "x" * 201, "leccion", "2026-08-01T10:00:00"
        )
        assert not result.success
        assert "200" in result.message

    def test_duplicate_detection(self, isolate_memory):
        MemoryManager.add_to_memory("hecho único", "leccion", "2026-08-01T10:00:00")
        result = MemoryManager.add_to_memory("hecho único", "leccion", "2026-08-02T10:00:00")
        assert result.status == Status.WARNING
        assert "duplicó" in result.message.lower() or "similar" in result.message.lower()

    def test_updates_timestamp(self, isolate_memory):
        MemoryManager.add_to_memory("test", "leccion", "2026-08-05T15:30:00")
        content = (isolate_memory / "MEMORY.md").read_text()
        assert "2026-08-05T15:30:00" in content


class TestRecall:
    def test_recall_from_memory(self, populated_memory):
        result = MemoryManager.recall("emqx RAM")
        assert result.success
        assert result.data["found"] is True
        assert "512MB" in result.message

    def test_recall_from_skills(self, populated_memory):
        result = MemoryManager.recall("emqx OOM reinicia")
        assert result.success
        assert "SKILL" in result.message
        assert "diagnosticar-emqx-oom" in result.message

    def test_recall_from_sessions(self, populated_memory):
        result = MemoryManager.recall("emqx OOM fix")
        assert result.success
        assert "SESIÓN" in result.message

    def test_recall_not_found(self, isolate_memory):
        MemoryManager.ensure_initialized()
        result = MemoryManager.recall("algo que no existe en ningún lado")
        assert result.success
        assert result.data["found"] is False
        assert "nuevo" in result.message.lower()

    def test_recall_short_query(self, isolate_memory):
        MemoryManager.ensure_initialized()
        result = MemoryManager.recall("ab")
        assert "corta" in result.message.lower()


class TestAddSkill:
    def test_add_skill_success(self, isolate_memory):
        result = MemoryManager.add_skill(
            "reiniciar-plex",
            "1. service_restart(plex)\n2. Verificar logs",
            "plex no responde",
        )
        assert result.success
        content = (isolate_memory / "SKILLS.md").read_text()
        assert "## skill: reiniciar-plex" in content
        assert "plex no responde" in content
        assert "Total: 1 skills" in content

    def test_add_duplicate_skill(self, isolate_memory):
        MemoryManager.add_skill("test-skill", "paso 1", "trigger test")
        result = MemoryManager.add_skill("test-skill", "paso 2", "otro trigger")
        assert result.status == Status.WARNING
        assert "ya existe" in result.message.lower()

    def test_skill_counter_increments(self, isolate_memory):
        MemoryManager.add_skill("skill-1", "proc1", "trigger1")
        MemoryManager.add_skill("skill-2", "proc2", "trigger2")
        content = (isolate_memory / "SKILLS.md").read_text()
        assert "Total: 2 skills" in content


class TestUpdateUserModel:
    def test_add_new_key(self, isolate_memory):
        result = MemoryManager.update_user_model("nivel_tecnico", "avanzado")
        assert result.success
        assert "agregado" in result.data["action"]
        content = (isolate_memory / "USER.md").read_text()
        assert "nivel_tecnico: avanzado" in content

    def test_update_existing_key(self, populated_memory):
        result = MemoryManager.update_user_model("estilo", "detallado y técnico")
        assert result.success
        assert "actualizado" in result.data["action"]
        content = (populated_memory / "USER.md").read_text()
        assert "estilo: detallado y técnico" in content
        # Verificar que no queda el valor viejo
        assert "respuestas cortas" not in content


class TestSaveSession:
    def test_save_session(self, isolate_memory):
        result = MemoryManager.save_session(
            "Fix de nextcloud",
            "# Sesión: Fix nextcloud\nResumen del fix.",
        )
        assert result.success
        sessions = list((isolate_memory / "sessions").glob("*.md"))
        assert len(sessions) == 1
        assert "fix-de-nextcloud" in sessions[0].name


class TestCuration:
    def test_trim_sessions(self, isolate_memory):
        sessions_dir = isolate_memory / "sessions"
        # Crear sesión vieja (fecha en el nombre)
        (sessions_dir / "2020-01-01_old-session.md").write_text("vieja")
        # Crear sesión reciente
        (sessions_dir / "2026-08-01_recent.md").write_text("nueva")

        result = MemoryManager.trim_sessions(max_age_days=90)
        assert result.success
        assert result.data["removed"] == 1
        remaining = list(sessions_dir.glob("*.md"))
        assert len(remaining) == 1
        assert "recent" in remaining[0].name

    def test_prune_old_entries(self, isolate_memory):
        (isolate_memory / "MEMORY.md").write_text(
            "# Memoria del Agente NAS\n"
            "> Última actualización: 2026-08-01T10:00:00\n\n"
            "## Lecciones aprendidas\n"
            "- [2020-01-01] Entrada muy vieja\n"
            "- [2026-08-01] Entrada reciente\n",
            encoding="utf-8",
        )
        result = MemoryManager.prune_old_entries(max_age_days=90)
        assert result.success
        assert result.data["removed"] == 1
        content = (isolate_memory / "MEMORY.md").read_text()
        assert "Entrada muy vieja" not in content
        assert "Entrada reciente" in content


class TestMemoryStats:
    def test_stats_structure(self, isolate_memory):
        MemoryManager.ensure_initialized()
        stats = MemoryManager.get_memory_stats()
        assert "memory_kb" in stats
        assert "user_kb" in stats
        assert "skills_kb" in stats
        assert "skill_count" in stats
        assert "sessions_count" in stats
        assert "sessions_kb" in stats
        assert "total_kb" in stats
        assert stats["skill_count"] == 0

    def test_stats_with_data(self, populated_memory):
        stats = MemoryManager.get_memory_stats()
        assert stats["memory_kb"] > 0
        assert stats["skill_count"] == 1
        assert stats["sessions_count"] == 1
