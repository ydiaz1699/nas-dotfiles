"""
test_classify.py — Tests para la clasificación de queries (prompt dinámico).

_classify_query es pura (sin IO) — fácil y rápida de testear.
Nota: strands SDK mockeado via conftest.py
"""

from agent.nas_agent import _classify_query


class TestDiagnostico:
    def test_revisar(self):
        blocks = _classify_query("revisar emqx")
        assert "diagnostico" in blocks
        assert "memoria" in blocks

    def test_error(self):
        blocks = _classify_query("hay un error en nextcloud")
        assert "diagnostico" in blocks

    def test_no_funciona(self):
        blocks = _classify_query("plex no funciona")
        assert "diagnostico" in blocks

    def test_502(self):
        blocks = _classify_query("nextcloud da 502")
        assert "diagnostico" in blocks

    def test_por_que(self):
        blocks = _classify_query("por qué emqx está caído")
        assert "diagnostico" in blocks


class TestCreacion:
    def test_instalar(self):
        blocks = _classify_query("instalar vaultwarden")
        assert "creacion" in blocks
        assert "seguridad" in blocks

    def test_crear(self):
        blocks = _classify_query("crear servicio nuevo de jellyfin")
        assert "creacion" in blocks

    def test_quiero(self):
        blocks = _classify_query("quiero montar un media server")
        assert "creacion" in blocks


class TestBackup:
    def test_backup(self):
        blocks = _classify_query("backup de plex")
        assert "backup" in blocks

    def test_restaurar(self):
        blocks = _classify_query("restaurar nextcloud")
        assert "backup" in blocks

    def test_respaldo(self):
        blocks = _classify_query("hacer respaldo de todos los servicios")
        assert "backup" in blocks


class TestAdmin:
    def test_restart(self):
        blocks = _classify_query("restart emqx")
        assert "admin" in blocks

    def test_detener(self):
        blocks = _classify_query("detener plex")
        assert "admin" in blocks

    def test_actualizar(self):
        blocks = _classify_query("actualizar nextcloud")
        assert "admin" in blocks

    def test_start(self):
        blocks = _classify_query("start homeassistant")
        assert "admin" in blocks


class TestSistema:
    def test_servicios(self):
        blocks = _classify_query("qué servicios hay")
        assert "herramientas" in blocks

    def test_disco(self):
        blocks = _classify_query("cuánto disco queda")
        assert "herramientas" in blocks

    def test_puertos(self):
        blocks = _classify_query("qué puertos están en uso")
        assert "herramientas" in blocks


class TestIdentidad:
    def test_modelo(self):
        blocks = _classify_query("qué modelo eres")
        assert "identidad" in blocks
        assert "diagnostico" not in blocks

    def test_quien_eres(self):
        blocks = _classify_query("quién eres")
        assert "identidad" in blocks


class TestMemoria:
    def test_recuerda(self):
        blocks = _classify_query("qué recuerdas sobre emqx")
        assert "memoria" in blocks

    def test_skill(self):
        blocks = _classify_query("tienes algún skill guardado")
        assert "memoria" in blocks

    def test_que_sabes(self):
        blocks = _classify_query("qué sabes de mi configuración")
        assert "memoria" in blocks


class TestGeneral:
    def test_hola(self):
        blocks = _classify_query("hola")
        assert "reglas_core" in blocks
        assert "memoria" in blocks

    def test_siempre_tiene_identidad(self):
        blocks = _classify_query("cualquier cosa random")
        assert "identidad" in blocks

    def test_general_tiene_formato(self):
        blocks = _classify_query("cómo estás")
        assert "formato" in blocks
