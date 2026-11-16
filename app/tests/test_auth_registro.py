"""DEF-004: el registro exige idoneidad + cédula.

La idoneidad aparece en el directorio público, así que por sí sola no prueba que
quien se registra sea el médico. La comparación de la cédula la hace la función
crear_cuenta_medico en la BD; aquí se prueba el contrato de la API: la cédula es
obligatoria, viaja al repositorio y un dato que no coincide responde igual que una
idoneidad que no existe.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy.exc import DBAPIError

from app.config import settings
from app.main import app
from app.repositories.auth import get_auth_repository

DATOS = {
    "numero_idoneidad": "IDON-1234",
    "cedula": "8-123-456",
    "correo": "medico.nuevo@colmed.dev",
    "password": "ClaveSegura123!",
}


def error_bd(mensaje: str) -> DBAPIError:
    """Simula un RAISE EXCEPTION de crear_cuenta_medico."""
    original = RuntimeError(mensaje)
    original.diag = SimpleNamespace(message_primary=mensaje)
    return DBAPIError("SELECT crear_cuenta_medico()", {}, original, False)


class RepoRegistroFalso:
    def __init__(self):
        self.llamadas = []
        self.error = None

    def crear_cuenta_medico(self, numero_idoneidad, cedula, correo, password_hash):
        self.llamadas.append((numero_idoneidad, cedula, correo, password_hash))
        if self.error:
            raise self.error
        return 40

    def obtener_id_medico(self, id_usuario):
        return 12


@pytest.fixture
def repo(cliente, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret_key", "clave-de-pruebas-" * 4)
    falso = RepoRegistroFalso()
    app.dependency_overrides[get_auth_repository] = lambda: falso
    return falso


def registrar(cliente, **cambios):
    datos = {**DATOS, **cambios}
    datos = {clave: valor for clave, valor in datos.items() if valor is not None}
    return cliente.post("/auth/register", json=datos)


def test_registro_sin_cedula_responde_422(cliente, repo):
    respuesta = registrar(cliente, cedula=None)

    assert respuesta.status_code == 422
    assert repo.llamadas == []


@pytest.mark.parametrize("cedula", ["", "   "])
def test_registro_con_cedula_vacia_responde_422(cliente, repo, cedula):
    assert registrar(cliente, cedula=cedula).status_code == 422
    assert repo.llamadas == []


def test_registro_envia_idoneidad_y_cedula_a_la_bd(cliente, repo):
    respuesta = registrar(cliente, cedula="  8-123-456  ")

    assert respuesta.status_code == 201
    assert respuesta.json()["access_token"]
    idoneidad, cedula, correo, password_hash = repo.llamadas[0]
    assert (idoneidad, cedula, correo) == ("IDON-1234", "8-123-456", "medico.nuevo@colmed.dev")
    assert password_hash != DATOS["password"]  # a la BD solo llega el hash


def test_cedula_que_no_coincide_responde_igual_que_idoneidad_inexistente(cliente, repo):
    # crear_cuenta_medico usa el mismo RAISE en los dos casos.
    repo.error = error_bd("No existe un médico registrado con el número de idoneidad IDON-1234")
    cedula_ajena = registrar(cliente, cedula="8-999-999")

    repo.error = error_bd("No existe un médico registrado con el número de idoneidad IDON-0000")
    idoneidad_inexistente = registrar(cliente, numero_idoneidad="IDON-0000")

    assert cedula_ajena.status_code == idoneidad_inexistente.status_code == 404
    assert cedula_ajena.json() == idoneidad_inexistente.json() == {"detail": "Médico no encontrado."}
