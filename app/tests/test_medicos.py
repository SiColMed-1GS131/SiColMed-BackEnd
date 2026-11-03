from unittest.mock import Mock
from fastapi.testclient import TestClient
from app.database import get_db
from app.main import app
from app.security import roles
from app.security.auth import get_usuario_actual, get_usuario_opcional
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
    app.dependency_overrides[get_usuario_opcional] = lambda: UsuarioAutenticado(
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


PERFIL_COMPLETO = {
    "datos_personales": {
        "id_medico": 7, "primer_nombre": "Ana", "segundo_nombre": "María",
        "apellido_paterno": "Gómez", "apellido_materno": None,
        "numero_idoneidad": "MED-001", "numero_registro_medico": "REG-001",
        "cedula": "8-123-456", "fecha_nacimiento": "1990-01-01",
        "telefono_residencial": "507-111-1111", "celular": "507-611-1111",
        "email_personal": "ana@example.com", "foto": None,
    },
    "direccion_residencial": {"provincia": "Panamá", "calle": "Calle 1", "corregimiento": "Bella Vista"},
    "lugares_trabajo": [{"empresa_institucion": "Hospital X", "telefono_trabajo": "500-0000",
                         "email_laboral": "ana@hospital.pa"}],
    "estudios": [{"titulo": "Doctor en Medicina"}],
    "especialidades": [{"id_especialidad": 1, "nombre": "Medicina General"}],
    "subespecialidades": [],
    "asociaciones": [{"id_asociacion": 2, "nombre": "Sociedad X"}],
    "certificaciones": [{"vigente": False}, {"vigente": True}],
}
CAMPOS_PRIVADOS = ("cedula", "telefono", "celular", "email", "correo", "calle", "fecha_nacimiento", "datos_personales")


def _consultar_como(monkeypatch, usuario, id_medico=7):
    """GET /medicos/{id} con el usuario indicado (None = sin token)."""
    if usuario is not None:
        app.dependency_overrides[get_usuario_opcional] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: Mock()
    monkeypatch.setattr(service, "obtener_perfil_medico", lambda db, id: PERFIL_COMPLETO)
    try:
        with TestClient(app) as client:
            return client.get(f"/medicos/{id_medico}")
    finally:
        app.dependency_overrides.clear()


def test_consulta_sin_token_devuelve_ficha_publica(monkeypatch):
    r = _consultar_como(monkeypatch, None)

    assert r.status_code == 200
    assert r.json() == {
        "id_medico": 7,
        "nombre_completo": "Ana María Gómez",
        "numero_idoneidad": "MED-001",
        "especialidades": [{"id_especialidad": 1, "nombre": "Medicina General"}],
        "subespecialidades": [],
        "asociaciones": [{"id_asociacion": 2, "nombre": "Sociedad X"}],
        "provincia": "Panamá",
        "certificacion_vigente": True,
        "lugar_trabajo": "Hospital X",
    }
    assert not any(privado in r.text for privado in CAMPOS_PRIVADOS)


def test_consulta_con_token_invalido_devuelve_ficha_publica(monkeypatch):
    app.dependency_overrides[get_db] = lambda: Mock()
    monkeypatch.setattr(service, "obtener_perfil_medico", lambda db, id: PERFIL_COMPLETO)
    try:
        with TestClient(app) as client:
            r = client.get("/medicos/7", headers={"Authorization": "Bearer no.es.valido"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert "cedula" not in r.text


def test_admin_ve_perfil_completo(monkeypatch):
    r = _consultar_como(monkeypatch, UsuarioAutenticado(id_usuario=1, rol=roles.ADMIN_CMP))

    assert r.status_code == 200
    assert r.json() == PERFIL_COMPLETO


def test_medico_ve_completo_solo_su_propio_perfil(monkeypatch):
    medico = UsuarioAutenticado(id_usuario=15, rol=roles.MEDICO, id_medico=7)

    propio = _consultar_como(monkeypatch, medico, id_medico=7)
    ajeno = _consultar_como(monkeypatch, medico, id_medico=8)

    assert propio.json() == PERFIL_COMPLETO
    assert ajeno.status_code == 200
    assert "cedula" not in ajeno.text


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
