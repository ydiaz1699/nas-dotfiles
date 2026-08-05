"""
test_validation.py — Tests para validación de inputs (seguridad).

Estas funciones son puras (sin IO) — validan que nombres de servicio
no contengan path traversal, inyección de comandos, etc.

validate_service_name raises InvalidServiceName en caso de error,
retorna el nombre limpio si es válido.
"""

import pytest

from agent.tools._shell import InvalidServiceName, validate_service_name


class TestValidateServiceName:
    def test_valid_simple(self):
        """Nombres válidos pasan y se retornan."""
        assert validate_service_name("nextcloud") == "nextcloud"

    def test_valid_with_dash(self):
        assert validate_service_name("home-assistant") == "home-assistant"

    def test_valid_with_numbers(self):
        assert validate_service_name("emqx5") == "emqx5"

    def test_valid_underscore(self):
        assert validate_service_name("my_service") == "my_service"

    def test_path_traversal(self):
        """Path traversal es rechazado."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("../../etc/passwd")

    def test_empty_name(self):
        """Nombre vacío es rechazado."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("")

    def test_command_injection_semicolon(self):
        """Inyección con ; es rechazada."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("svc;rm -rf /")

    def test_command_injection_pipe(self):
        """Inyección con | es rechazada."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("svc|cat /etc/shadow")

    def test_command_injection_backtick(self):
        """Inyección con backticks es rechazada."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("`whoami`")

    def test_absolute_path(self):
        """Paths absolutos son rechazados."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("/etc/passwd")

    def test_spaces(self):
        """Nombres con espacios son rechazados."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("my service")

    def test_dollar_sign(self):
        """Variables shell son rechazadas."""
        with pytest.raises(InvalidServiceName):
            validate_service_name("$HOME")
