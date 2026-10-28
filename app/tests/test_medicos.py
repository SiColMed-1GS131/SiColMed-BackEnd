from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app
from app.security import roles
from app.security.auth import get_usuario_actual
from app.security.jwt import UsuarioAutenticado
from app.services import medicos as service

DATOS = {
    "medico": {
        "numero_idoneidad": "MED-001",
        "numero_registro_medico": "REG-001",
        "cedula": "8-123-456",
        "primer_nombre": "Ana",
        "apellido_paterno": "Gómez",
        "fecha_nacimiento": "1990-01-01",
    },
    "direccion": {"id_corregimiento": 1},
}

def test_registro_requiere_administrador():
    with TestClient(app) as client:
        assert client.post("/medicos", json=DATOS).status_code == 401

def test_registro_con_dependencias_simuladas(monkeypatch):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1,
        rol=roles.ADMIN_CMP,
    )
    app.dependency_overrides[get_db] = lambda: Mock()
    monkeypatch.setattr(service, "registrar_medico", lambda db, datos: 42)
    try:
        with TestClient(app) as client:
            r = client.post("/medicos", json=DATOS)
        assert r.status_code == 201
        assert r.json() == {"id_medico": 42}
    finally:
        app.dependency_overrides.clear()

def test_consulta_y_no_encontrado(monkeypatch):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1,
        rol=roles.ADMIN_CMP,
    )
    app.dependency_overrides[get_db] = lambda: Mock()
    try:
        monkeypatch.setattr(service, "obtener_perfil_medico", lambda db, id: {"id_medico": id, "datos_personales": {}})
        with TestClient(app) as client:
            r = client.get("/medicos/7")
        assert r.status_code == 200
        assert r.json()["id_medico"] == 7
        monkeypatch.setattr(service, "obtener_perfil_medico", lambda db, id: None)
        with TestClient(app) as client:
            assert client.get("/medicos/7").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_medico_solo_consulta_su_propio_perfil(monkeypatch):
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=15,
        rol=roles.MEDICO,
        id_medico=7,
    )
    app.dependency_overrides[get_db] = lambda: Mock()
    monkeypatch.setattr(
        service,
        "obtener_perfil_medico",
        lambda db, id: {"id_medico": id, "datos_personales": {}},
    )
    try:
        with TestClient(app) as client:
            permitido = client.get("/medicos/7")
            prohibido = client.get("/medicos/8")
        assert permitido.status_code == 200
        assert prohibido.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_id_invalido():
    app.dependency_overrides[get_usuario_actual] = lambda: UsuarioAutenticado(
        id_usuario=1,
        rol=roles.ADMIN_CMP,
    )
    try:
        with TestClient(app) as client:
            assert client.get("/medicos/0").status_code == 422
    finally:
        app.dependency_overrides.clear()
