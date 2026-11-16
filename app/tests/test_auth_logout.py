"""DEF-008, parte 2: cerrar sesión también invalida el token en la API.

Decisión del líder: lista en memoria (app/security/revocacion.py). Después de
POST /auth/logout, ese token responde 401 aunque su firma y su exp sigan válidos.
"""

import time

import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.main import app
from app.repositories.auth import get_auth_repository
from app.security import roles
from app.security.auth import get_usuario_opcional
from app.security.jwt import crear_token_acceso
from app.security.revocacion import limpiar_revocados, revocar_token, token_revocado


class RepoAuthFalso:
    def obtener_usuario_por_id(self, id_usuario):
        return {
            "id_usuario": id_usuario,
            "nombre": "Admin QA",
            "correo": "admin@colmed.dev",
            "numero_idoneidad": None,
            "rol": roles.ADMIN_CMP,
            "activo": True,
        }


@pytest.fixture(autouse=True)
def lista_limpia(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret_key", "clave-de-pruebas-" * 4)
    limpiar_revocados()
    yield
    limpiar_revocados()


@pytest.fixture
def repo(cliente):
    app.dependency_overrides[get_auth_repository] = lambda: RepoAuthFalso()


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def test_logout_sin_token_responde_401(cliente, repo):
    assert cliente.post("/auth/logout").status_code == 401


def test_despues_del_logout_el_token_responde_401(cliente, repo):
    token = crear_token_acceso(1, roles.ADMIN_CMP)
    assert cliente.get("/auth/me", headers=bearer(token)).status_code == 200

    assert cliente.post("/auth/logout", headers=bearer(token)).status_code == 204

    respuesta = cliente.get("/auth/me", headers=bearer(token))
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "La sesión fue cerrada."


def test_un_segundo_logout_con_el_mismo_token_responde_401(cliente, repo):
    token = crear_token_acceso(1, roles.ADMIN_CMP)
    cliente.post("/auth/logout", headers=bearer(token))

    assert cliente.post("/auth/logout", headers=bearer(token)).status_code == 401


def test_el_logout_solo_cierra_ese_token(cliente, repo):
    cerrado = crear_token_acceso(1, roles.ADMIN_CMP)
    otra_sesion = jwt.encode(
        {"sub": "1", "role": roles.ADMIN_CMP, "exp": int(time.time()) + 600, "jti": "otra"},
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    cliente.post("/auth/logout", headers=bearer(cerrado))

    assert cliente.get("/auth/me", headers=bearer(otra_sesion)).status_code == 200


def test_endpoint_publico_trata_el_token_cerrado_como_anonimo():
    token = crear_token_acceso(1, roles.ADMIN_CMP)
    credenciales = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    assert get_usuario_opcional(credenciales) is not None

    revocar_token(token)

    assert get_usuario_opcional(credenciales) is None


def test_la_lista_descarta_los_tokens_ya_vencidos():
    vencido = jwt.encode(
        {"sub": "1", "role": roles.ADMIN_CMP, "exp": int(time.time()) - 5},
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    revocar_token(vencido)

    assert token_revocado(vencido) is False
