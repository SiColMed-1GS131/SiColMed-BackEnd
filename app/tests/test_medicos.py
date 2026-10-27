from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app
from app.routers.medicos import requiere_administrador
from app.services import medicos as service

DATOS = {
    "numero_idoneidad": "MED-001",
    "numero_registro_medico": "REG-001",
    "cedula": "8-123-456",
    "primer_nombre": "Ana",
    "apellido_paterno": "Gómez",
    "direccion": {"id_corregimiento": 1},
}

def test_registro_bloqueado_hasta_integrar_autenticacion():
    with TestClient(app) as client:
        assert client.post("/medicos", json=DATOS).status_code == 503

def test_registro_con_dependencias_simuladas(monkeypatch):
    app.dependency_overrides[requiere_administrador] = lambda: {"rol": "ADMIN"}
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

def test_id_invalido():
    with TestClient(app) as client:
        assert client.get("/medicos/0").status_code == 422
