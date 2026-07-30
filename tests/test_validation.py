"""Tests para validación de nombres de servicio y seguridad."""

import pytest
from agent.tools._shell import (
    validate_service_name,
    validated_service_path,
    InvalidServiceName,
    DOCKER_BASE,
)


class TestValidateServiceName:
    """Tests para validate_service_name()."""

    def test_nombre_valido_simple(self):
        assert validate_service_name("emqx") == "emqx"

    def test_nombre_valido_con_guion(self):
        assert validate_service_name("home-assistant") == "home-assistant"

    def test_nombre_valido_con_punto(self):
        assert validate_service_name("node.red") == "node.red"

    def test_nombre_valido_con_guion_bajo(self):
        assert validate_service_name("my_service") == "my_service"

    def test_nombre_valido_con_numeros(self):
        assert validate_service_name("n8n") == "n8n"

    def test_nombre_strip_espacios(self):
        assert validate_service_name("  emqx  ") == "emqx"

    def test_nombre_vacio_falla(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("")

    def test_nombre_none_falla(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name(None)

    def test_path_traversal_puntos(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("../etc")

    def test_path_traversal_slash(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("foo/bar")

    def test_path_traversal_backslash(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("foo\\bar")

    def test_nombre_reservado_backups(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("backups")

    def test_nombre_reservado_cli(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("cli")

    def test_nombre_reservado_punto(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name(".")

    def test_nombre_reservado_doble_punto(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("..")

    def test_nombre_mayusculas_pasa_validacion(self):
        # La regex se chequea contra .lower(), así que mayúsculas pasan
        # pero el valor retornado mantiene el case original (solo strip)
        result = validate_service_name("MyService")
        assert result == "MyService"

    def test_nombre_empieza_con_guion_falla(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("-invalid")

    def test_nombre_muy_largo_falla(self):
        with pytest.raises(InvalidServiceName):
            validate_service_name("a" * 65)

    def test_nombre_64_chars_ok(self):
        name = "a" * 64
        assert validate_service_name(name) == name


class TestValidatedServicePath:
    """Tests para validated_service_path()."""

    def test_ruta_valida(self):
        path = validated_service_path("emqx")
        assert path == DOCKER_BASE / "emqx"

    def test_ruta_resuelta_dentro_de_base(self):
        path = validated_service_path("homeassistant")
        assert str(path).startswith(str(DOCKER_BASE))
