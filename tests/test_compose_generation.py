"""Tests para generación y validación de compose."""

import pytest
from agent.core.compose_manager import ComposeManager
from agent.tools._shell import InvalidServiceName


class TestComposeManagerSanitize:
    """Tests para sanitización de valores YAML."""

    def test_valor_normal(self):
        assert ComposeManager.sanitize_value("hello", "test") == "hello"

    def test_strip_espacios(self):
        assert ComposeManager.sanitize_value("  hello  ", "test") == "hello"

    def test_path_traversal_falla(self):
        with pytest.raises(InvalidServiceName):
            ComposeManager.sanitize_value("../etc/passwd", "test")

    def test_backslash_falla(self):
        with pytest.raises(InvalidServiceName):
            ComposeManager.sanitize_value("foo\\bar", "test")

    def test_control_chars_falla(self):
        with pytest.raises(InvalidServiceName):
            ComposeManager.sanitize_value("foo\x00bar", "test")

    def test_backtick_falla(self):
        with pytest.raises(InvalidServiceName):
            ComposeManager.sanitize_value("`whoami`", "test")

    def test_imagen_valida(self):
        val = ComposeManager.sanitize_value("emqx/emqx:5.8.3", "image")
        assert val == "emqx/emqx:5.8.3"

    def test_ruta_volumen_valida(self):
        val = ComposeManager.sanitize_value("./data:/opt/emqx/data", "volumes")
        assert val == "./data:/opt/emqx/data"


class TestComposeManagerAnchors:
    """Tests para carga de anchors base."""

    def test_fallback_anchors_contiene_bloques(self):
        anchors = ComposeManager._fallback_anchors()
        assert "x-common-env" in anchors
        assert "x-security-defaults" in anchors
        assert "x-healthcheck-defaults" in anchors
        assert "x-logging-defaults" in anchors
        assert "x-resource-defaults" in anchors

    def test_load_compose_base_anchors_retorna_string(self):
        anchors = ComposeManager.load_compose_base_anchors()
        assert isinstance(anchors, str)
        assert len(anchors) > 50  # No está vacío
        assert "x-security-defaults" in anchors


class TestComposeManagerRules:
    """Tests para carga de reglas."""

    def test_load_rules_retorna_dict(self):
        rules = ComposeManager.load_rules()
        assert isinstance(rules, dict)
        # Si _rules.md existe, debería tener al menos 'nas'
        if rules:
            assert "nas" in rules
            assert "ports" in rules
