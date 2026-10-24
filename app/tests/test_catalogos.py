"""Pruebas de las seis rutas sin conexión PostgreSQL."""
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app
from app.services import catalogos


def test_endpoints_catalogos(monkeypatch):
    app.dependency_overrides[get_db] = lambda: None
    rutas = [
        ("/provincias", "listar_provincias"),
        ("/provincias/1/distritos", "listar_distritos"),
        ("/distritos/1/corregimientos", "listar_corregimientos"),
        ("/especialidades", "listar_especialidades"),
        ("/subespecialidades", "listar_subespecialidades"),
        ("/asociaciones", "listar_asociaciones"),
    ]
    try:
        with TestClient(app) as client:
            for ruta, servicio in rutas:
                monkeypatch.setattr(catalogos, servicio, lambda *args: [])
                respuesta = client.get(ruta)
                assert respuesta.status_code == 200, (ruta, respuesta.text)
                assert respuesta.json() == []
            assert client.get("/provincias/0/distritos").status_code == 422
            assert client.get("/distritos/-1/corregimientos").status_code == 422
    finally:
        app.dependency_overrides.clear()
