"""Sección 5 de las decisiones: qué puede editar el médico en PATCH /medicos/{id}/perfil.

Fuente: sección 2.3 del documento del CMP ("Subrayado indica que la información no se
permite editar"). Lo no editable lo cambia solo el administrador (PATCH /medicos/{id}).
DEF-024 ("el médico cambia su nombre") queda como "no es defecto": nombre y apellidos
sí son editables según esa lista.
"""

import pytest

from app.database import get_db
from app.main import app
from app.routers import medicos_directorio as router_directorio
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado


class RepositorioCaptura:
    def __init__(self):
        self.datos = None

    def actualizar_medico(self, db, id_medico, id_usuario, datos):
        self.datos = datos
        return True


@pytest.fixture
def repo(cliente, monkeypatch):
    captura = RepositorioCaptura()
    monkeypatch.setattr(router_directorio, "repositorio", captura)
    app.dependency_overrides[get_db] = lambda: None
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1, rol=roles.MEDICO, id_medico=7
    )
    return captura


def editar_perfil(cliente, datos):
    return cliente.patch("/medicos/7/perfil", json=datos)


# Campos subrayados (no editables) de la sección 5, tal como se llaman en la API.
NO_EDITABLES = {
    "cédula": {"cedula": "8-999-999"},
    "número de registro médico": {"numero_registro_medico": "RM-9999"},
    "número de idoneidad": {"numero_idoneidad": "IDON-9999"},
    "título básico (institución, lugar, fecha)": {
        "estudio_medico": [{"id_estudio": 1, "institucion": "Otra", "lugar": "Otro", "fecha": "2001-01-01"}]
    },
    "información de certificación": {
        "certificacion": [{"id_certificacion": 1, "vigente": True, "puntaje": 100}]
    },
    "información de certificación (nombre de la BD)": {
        "certificaciones": [{"id_certificacion": 1, "fecha_expiracion": "2040-01-01"}]
    },
}


@pytest.mark.parametrize("datos", NO_EDITABLES.values(), ids=NO_EDITABLES.keys())
def test_el_medico_no_puede_editar_lo_subrayado(cliente, repo, datos):
    assert editar_perfil(cliente, datos).status_code == 422
    assert repo.datos is None


def test_nombre_y_apellidos_si_son_editables_def_024_no_es_defecto(cliente, repo):
    datos = {"primer_nombre": "Ana", "apellido_paterno": "Pérez", "apellido_materno": "Gómez"}

    assert editar_perfil(cliente, datos).status_code == 200
    assert repo.datos == {"medico": datos}


def test_fecha_de_nacimiento_es_editable(cliente, repo):
    assert editar_perfil(cliente, {"fecha_nacimiento": "1985-04-12"}).status_code == 200
    assert repo.datos["medico"]["fecha_nacimiento"].isoformat() == "1985-04-12"


def test_contacto_y_direccion_siguen_siendo_editables(cliente, repo):
    datos = {"celular": "6000-0000", "direccion": {"calle": "Calle 50"}}

    assert editar_perfil(cliente, datos).status_code == 200
    assert repo.datos == {"medico": {"celular": "6000-0000"}, "direccion": {"calle": "Calle 50"}}
