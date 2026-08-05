"""
conftest.py — Fixtures compartidos para la suite de tests del agente NAS.

Principio: testear el core (lógica de negocio), no Strands SDK.
Mocks de subprocess/Docker para no requerir Docker en CI.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ─── Mock de strands SDK (no disponible en CI) ──────────────────────────────
# Debe ir ANTES de cualquier import de agent.*
_strands_mock = MagicMock()
# tool decorator: debe devolver la función tal cual
_strands_mock.tools.tool = lambda fn: fn
sys.modules.setdefault("strands", _strands_mock)
sys.modules.setdefault("strands.tools", _strands_mock.tools)
sys.modules["strands.tools"].tool = lambda fn: fn
sys.modules.setdefault("strands.models", MagicMock())
sys.modules.setdefault("strands.models.gemini", MagicMock())
sys.modules.setdefault("strands.models.bedrock", MagicMock())
sys.modules.setdefault("strands.models.ollama", MagicMock())
sys.modules.setdefault("strands.session", MagicMock())
sys.modules.setdefault("strands.session.file_session_manager", MagicMock())
sys.modules.setdefault("frontmatter", MagicMock())
sys.modules.setdefault("yaml", MagicMock())
sys.modules.setdefault("rich", MagicMock())
sys.modules.setdefault("rich.console", MagicMock())
sys.modules.setdefault("rich.panel", MagicMock())
sys.modules.setdefault("rich.markdown", MagicMock())
sys.modules.setdefault("rich.text", MagicMock())
sys.modules.setdefault("rich.box", MagicMock())


@pytest.fixture(autouse=True)
def isolate_memory(tmp_path, monkeypatch):
    """Aísla el directorio de memoria para cada test.

    Cada test obtiene un directorio temporal limpio para MEMORY.md,
    USER.md, SKILLS.md y sessions/. Evita interferencia entre tests.
    """
    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "sessions").mkdir()

    monkeypatch.setenv("NAS_AGENT_MEMORY_DIR", str(memory_dir))

    # Patchear las constantes del módulo memory
    import agent.core.memory as mem_module
    monkeypatch.setattr(mem_module, "MEMORY_DIR", memory_dir)
    monkeypatch.setattr(mem_module, "MEMORY_FILE", memory_dir / "MEMORY.md")
    monkeypatch.setattr(mem_module, "USER_FILE", memory_dir / "USER.md")
    monkeypatch.setattr(mem_module, "SKILLS_FILE", memory_dir / "SKILLS.md")
    monkeypatch.setattr(mem_module, "SESSIONS_DIR", memory_dir / "sessions")

    yield memory_dir


@pytest.fixture
def mock_safe_run(monkeypatch):
    """Mock de safe_run para no ejecutar comandos reales."""
    def _mock_safe_run(args, **kwargs):
        return "mocked output"

    monkeypatch.setattr(
        "agent.tools._shell.safe_run",
        _mock_safe_run,
        raising=False,
    )
    return _mock_safe_run


@pytest.fixture
def populated_memory(isolate_memory):
    """Memoria pre-poblada con datos de ejemplo para tests de recall."""
    memory_dir = isolate_memory

    (memory_dir / "MEMORY.md").write_text(
        "# Memoria del Agente NAS\n"
        "> Última actualización: 2026-08-01T10:00:00\n\n"
        "## Entorno\n"
        "- [2026-07-15] OS: Debian 12, kernel 6.1\n"
        "- [2026-07-15] Docker: v24.0.7\n\n"
        "## Lecciones aprendidas\n"
        "- [2026-07-20] emqx requiere al menos 512MB de RAM para arrancar\n"
        "- [2026-07-25] nextcloud necesita redis para sesiones en producción\n\n"
        "## Patrones que funcionaron\n"
        "- [2026-07-28] Backup: tar.gz local antes de update siempre\n\n"
        "## Estado pendiente\n",
        encoding="utf-8",
    )

    (memory_dir / "USER.md").write_text(
        "# Perfil del Usuario\n"
        "> Última actualización: 2026-08-01T10:00:00\n\n"
        "## Preferencias de interacción\n"
        "- estilo: respuestas cortas y directas\n\n"
        "## Decisiones técnicas\n"
        "- cifrado: siempre cifrar backups externos\n\n"
        "## Proyectos activos\n",
        encoding="utf-8",
    )

    (memory_dir / "SKILLS.md").write_text(
        "# Skills del Agente NAS\n"
        "> Total: 1 skills | Última actualización: 2026-08-01T10:00:00\n"
        "\n---\n\n"
        "## skill: diagnosticar-emqx-oom\n"
        '> Aprendido: 2026-07-20 | Usado: 2 veces | Último uso: 2026-07-28\n'
        '> Trigger: "emqx se reinicia por OOM"\n\n'
        "### Procedimiento\n"
        "1. troubleshoot(emqx)\n"
        "2. memory_info() → verificar RAM disponible\n"
        "3. read_compose(emqx) → verificar mem_limit\n"
        "4. Si mem_limit < 512MB → subir a 512MB\n"
        "5. service_restart(emqx)\n",
        encoding="utf-8",
    )

    # Session de ejemplo
    (memory_dir / "sessions" / "2026-07-20_emqx-oom-fix.md").write_text(
        "# Sesión: emqx OOM fix\n"
        "> Tools: 5 | Errores: sí | Duración: 180s\n\n"
        "## Resumen\n"
        "emqx se reiniciaba por OOM. Solución: subir mem_limit a 512MB.\n",
        encoding="utf-8",
    )

    return memory_dir
