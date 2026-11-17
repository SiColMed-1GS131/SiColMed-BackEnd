"""Pruebas de solicitudes de cambio con repositorio falso (sin PostgreSQL)."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import DBAPIError

from app.database import get_db
from app.main import app
from app.repositories import solicitudes_cambio as repo
from app.repositories.auth import AuthRepository
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado


def error_bd(mensaje: str) -> DBAPIError:
    """Simula un RAISE EXCEPTION de PostgreSQL."""
    original = RuntimeError(mensaje)
    original.diag = SimpleNamespace(message_primary=mensaje)
    return DBAPIError("SELECT f()", {}, original, False)


class RepositorioFalso:
    """Reemplaza las funciones del repositorio y guarda las llamadas."""

    def __init__(self):
        self.llamadas: list[tuple] = []
        self.id_creado = 12
        self.crear_error: Exception | None = None
        self.procesar_resultado = True
        self.procesar_error: Exception | None = None
        self.filas: list[dict] = []

    def crear(self, db, id_medico, cambios):
        self.llamadas.append(("crear", id_medico, cambios))
        if self.crear_error:
            raise self.crear_error
        return self.id_creado

    def procesar(self, db, id_solicitud, id_admin, decisiones, comentario):
        self.llamadas.append(
            ("procesar", id_solicitud, id_admin, decisiones, comentario)
        )
        if self.procesar_error:
            raise self.procesar_error
        return self.procesar_resultado

    def listar(self, db, estado):
        self.llamadas.append(("listar", estado))
        return self.filas


@pytest.fixture
def repo_falso(cliente, monkeypatch):
    falso = RepositorioFalso()
    monkeypatch.setattr(repo, "crear_solicitud_cambio", falso.crear)
    monkeypatch.setattr(repo, "procesar_solicitud_cambio", falso.procesar)
    monkeypatch.setattr(repo, "listar_solicitudes_cambio", falso.listar)
    app.dependency_overrides[get_db] = lambda: Mock()
    return falso


def fijar_usuario(
    id_usuario: int = 1,
    rol: str = roles.MEDICO,
    id_medico: int | None = 5,
):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=id_usuario,
        rol=rol,
        id_medico=id_medico,
    )


CREAR_OK = {
    "lugar_trabajo": [{"id_lugar_trabajo": 3, "cargo": "Jefe de servicio"}],
    "especialidades": {"agregar": [3], "quitar": []},
}


# --- POST /solicitudes-cambio ---------------------------------------------


def test_crear_solicitud_exitosa(cliente, repo_falso):
    fijar_usuario(id_medico=5)

    respuesta = cliente.post("/solicitudes-cambio", json=CREAR_OK)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"id_solicitud_cambio": 12}
    assert repo_falso.llamadas == [(
        "crear",
        5,
        {
            "lugar_trabajo": [{"id_lugar_trabajo": 3, "cargo": "Jefe de servicio"}],
            "especialidades": {"agregar": [3], "quitar": []},
        },
    )]


def test_crear_usa_auth_repository_si_el_token_no_trae_medico(
    cliente, repo_falso, monkeypatch
):
    fijar_usuario(id_usuario=9, id_medico=None)
    monkeypatch.setattr(AuthRepository, "obtener_id_medico", lambda self, id_usuario: 7)

    respuesta = cliente.post("/solicitudes-cambio", json=CREAR_OK)

    assert respuesta.status_code == 201
    assert repo_falso.llamadas[0][1] == 7


def test_crear_sin_medico_asociado_da_403(cliente, repo_falso, monkeypatch):
    fijar_usuario(id_usuario=9, id_medico=None)
    monkeypatch.setattr(AuthRepository, "obtener_id_medico", lambda self, id_usuario: None)

    respuesta = cliente.post("/solicitudes-cambio", json=CREAR_OK)

    assert respuesta.status_code == 403
    assert repo_falso.llamadas == []


def test_crear_exige_rol_medico(cliente, repo_falso):
    fijar_usuario(rol=roles.ADMIN_CMP)

    respuesta = cliente.post("/solicitudes-cambio", json=CREAR_OK)

    assert respuesta.status_code == 403


@pytest.mark.parametrize("cuerpo", [
    {"medico": [{"id_medico": 1}]},
    {"direccion": {"calle": "X"}},
    {"seccion_inventada": []},
    {"lugar_trabajo": []},
    {"lugar_trabajo": [{"id_lugar_trabajo": 1, "campo_prohibido": "x"}]},
    {"especialidades": {"agregar": [1], "quitar": [1]}},
    {"especialidades": {"agregar": [], "quitar": []}},
])
def test_crear_rechaza_payload_invalido(cliente, repo_falso, cuerpo):
    fijar_usuario()

    respuesta = cliente.post("/solicitudes-cambio", json=cuerpo)

    assert respuesta.status_code == 422
    assert repo_falso.llamadas == []


def test_crear_propaga_error_de_bd_como_400(cliente, repo_falso):
    fijar_usuario()
    repo_falso.crear_error = error_bd("El registro 3 no existe o no pertenece al medico 5")

    respuesta = cliente.post("/solicitudes-cambio", json=CREAR_OK)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "El registro 3 no existe o no pertenece al medico 5"


# --- GET /solicitudes-cambio ----------------------------------------------


def test_listar_exige_admin(cliente, repo_falso):
    fijar_usuario(rol=roles.MEDICO)

    respuesta = cliente.get("/solicitudes-cambio")

    assert respuesta.status_code == 403


def test_listar_como_admin_filtra_por_estado(cliente, repo_falso):
    fijar_usuario(rol=roles.ADMIN_CMP)
    repo_falso.filas = [{
        "id_solicitud_cambio": 12,
        "id_medico": 5,
        "nombre_completo": "Ana Pérez",
        "estado": "PENDIENTE",
        "fecha_solicitud": "2026-10-18T09:30:00",
        "cambios": {},
    }]

    respuesta = cliente.get("/solicitudes-cambio?estado=PENDIENTE")

    assert respuesta.status_code == 200
    assert respuesta.json()[0]["id_solicitud_cambio"] == 12
    assert repo_falso.llamadas == [("listar", "PENDIENTE")]


# --- POST /solicitudes-cambio/{id}/procesar -------------------------------


DECISIONES_OK = {
    "lugar_trabajo": [{"cargo": "APROBADO"}],
    "especialidades": {"estado": "RECHAZADO"},
    "comentario": "Revisado",
}


def test_procesar_exitoso_como_admin(cliente, repo_falso):
    fijar_usuario(id_usuario=1, rol=roles.ADMIN_CMP, id_medico=None)

    respuesta = cliente.post("/solicitudes-cambio/8/procesar", json=DECISIONES_OK)

    assert respuesta.status_code == 200
    assert respuesta.json() is True
    assert repo_falso.llamadas == [(
        "procesar",
        8,
        1,
        {
            "lugar_trabajo": [{"cargo": "APROBADO"}],
            "especialidades": {"estado": "RECHAZADO"},
        },
        "Revisado",
    )]


def test_procesar_exige_admin(cliente, repo_falso):
    fijar_usuario(rol=roles.MEDICO)

    respuesta = cliente.post("/solicitudes-cambio/8/procesar", json=DECISIONES_OK)

    assert respuesta.status_code == 403
    assert repo_falso.llamadas == []


@pytest.mark.parametrize("cuerpo", [
    {"lugar_trabajo": [{"cargo": "NEGADO"}]},
    {"lugar_trabajo": [{"campo_prohibido": "APROBADO"}]},
    {"especialidades": {"estado": "ACEPTADO"}},
    {"especialidades": {"estado": "APROBADO", "extra": 1}},
    {},
])
def test_procesar_rechaza_decisiones_invalidas(cliente, repo_falso, cuerpo):
    fijar_usuario(rol=roles.ADMIN_CMP, id_medico=None)

    respuesta = cliente.post("/solicitudes-cambio/8/procesar", json=cuerpo)

    assert respuesta.status_code == 422
    assert repo_falso.llamadas == []


def test_procesar_solicitud_inexistente_da_400(cliente, repo_falso):
    fijar_usuario(rol=roles.ADMIN_CMP, id_medico=None)
    repo_falso.procesar_error = error_bd("La solicitud 999 no existe")

    respuesta = cliente.post("/solicitudes-cambio/999/procesar", json=DECISIONES_OK)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La solicitud 999 no existe"


def test_procesar_solicitud_ya_resuelta_da_400(cliente, repo_falso):
    fijar_usuario(rol=roles.ADMIN_CMP, id_medico=None)
    repo_falso.procesar_error = error_bd("La solicitud 8 ya no esta pendiente")

    respuesta = cliente.post("/solicitudes-cambio/8/procesar", json=DECISIONES_OK)

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La solicitud 8 ya no esta pendiente"
