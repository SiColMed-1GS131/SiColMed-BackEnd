"""Pruebas de app/security: JWT y las dependencias get_usuario_actual y requiere_rol.

No necesitan una base de datos.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.security import roles
from app.security.auth import UsuarioAutenticado, get_usuario_actual, requiere_rol
from app.security.jwt import (
    ConfiguracionJWTError,
    TokenExpirado,
    TokenInvalido,
    crear_token_acceso,
    decodificar_token,
)

# 64 caracteres o más: suficiente incluso para HS512.
CLAVE = "clave-de-pruebas-" * 4
OTRA_CLAVE = "otra-clave-distinta-" * 4


@pytest.fixture(autouse=True)
def configuracion_jwt(monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret_key", CLAVE)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "jwt_access_token_expire_minutes", 60)


def firmar(claims, clave=CLAVE, algoritmo="HS256"):
    """Firma un token a mano para simular tokens vencidos o alterados."""
    return jwt.encode(claims, clave, algorithm=algoritmo)


def claims(**cambios):
    base = {
        "sub": "15",
        "role": roles.MEDICO,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    base.update(cambios)
    return {clave: valor for clave, valor in base.items() if valor is not None}


def con_token(rol=roles.MEDICO, id_usuario=15):
    return {"Authorization": f"Bearer {crear_token_acceso(id_usuario, rol)}"}


# --- Creación y validación del JWT ------------------------------------------


def test_crear_token_lleva_sub_role_iat_y_exp():
    token = crear_token_acceso(15, roles.MEDICO)

    contenido = jwt.decode(token, CLAVE, algorithms=["HS256"])

    assert set(contenido) == {"sub", "role", "iat", "exp"}
    assert contenido["sub"] == "15"
    assert contenido["role"] == roles.MEDICO
    assert contenido["exp"] - contenido["iat"] == 60 * 60


def test_crear_token_no_incluye_datos_sensibles():
    contenido = jwt.decode(crear_token_acceso(15, roles.MEDICO), CLAVE, algorithms=["HS256"])

    assert not {"password", "password_hash", "correo"} & set(contenido)


def test_decodificar_devuelve_el_usuario_del_token():
    token = crear_token_acceso(15, roles.ADMIN_CMP)

    assert decodificar_token(token) == UsuarioAutenticado(id_usuario=15, rol=roles.ADMIN_CMP)


def test_decodificar_rechaza_token_vencido():
    token = firmar(claims(exp=datetime.now(timezone.utc) - timedelta(seconds=1)))

    with pytest.raises(TokenExpirado):
        decodificar_token(token)


@pytest.mark.parametrize(
    "token",
    [
        pytest.param("no-es-un-jwt", id="mal-formado"),
        pytest.param(firmar(claims(), clave=OTRA_CLAVE), id="firmado-con-otra-clave"),
        pytest.param(firmar(claims(), algoritmo="HS512"), id="otro-algoritmo"),
        pytest.param(jwt.encode(claims(), None, algorithm="none"), id="sin-firma"),
        pytest.param(firmar(claims(sub=None)), id="sin-sub"),
        pytest.param(firmar(claims(role=None)), id="sin-role"),
        pytest.param(firmar(claims(exp=None)), id="sin-exp"),
        pytest.param(firmar(claims(sub="abc")), id="sub-no-numerico"),
        pytest.param(firmar(claims(sub="0")), id="sub-cero"),
        pytest.param(firmar(claims(role="")), id="role-vacio"),
        pytest.param(firmar(claims(role=5)), id="role-no-texto"),
    ],
)
def test_decodificar_rechaza_tokens_invalidos(token):
    with pytest.raises(TokenInvalido):
        decodificar_token(token)


@pytest.mark.parametrize("clave", ["", "corta"])
def test_sin_clave_valida_falla_con_mensaje_claro(monkeypatch, clave):
    monkeypatch.setattr(settings, "jwt_secret_key", clave)

    with pytest.raises(ConfiguracionJWTError, match="JWT_SECRET_KEY"):
        crear_token_acceso(15, roles.MEDICO)


# --- Dependencias en una app mínima -----------------------------------------

app_prueba = FastAPI()


@app_prueba.get("/yo")
def yo(usuario: UsuarioAutenticado = Depends(get_usuario_actual)):
    return {"id_usuario": usuario.id_usuario, "rol": usuario.rol}


@app_prueba.get("/solo-admin")
def solo_admin(usuario: UsuarioAutenticado = Depends(requiere_rol(roles.ADMIN_CMP))):
    return {"id_usuario": usuario.id_usuario}


@app_prueba.get("/contable")
def contable(
    usuario: UsuarioAutenticado = Depends(
        requiere_rol(roles.TESORERO, roles.ADMIN_ASOCIACION)
    ),
):
    return {"rol": usuario.rol}


@pytest.fixture
def cliente_prueba():
    return TestClient(app_prueba)


def test_get_usuario_actual_devuelve_el_usuario_del_token(cliente_prueba):
    respuesta = cliente_prueba.get("/yo", headers=con_token(id_usuario=15))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id_usuario": 15, "rol": roles.MEDICO}


@pytest.mark.parametrize(
    "headers",
    [
        pytest.param({}, id="sin-header"),
        pytest.param({"Authorization": "Basic dXN1YXJpbzpjbGF2ZQ=="}, id="esquema-basic"),
        pytest.param({"Authorization": "Bearer"}, id="bearer-sin-token"),
    ],
)
def test_get_usuario_actual_sin_credenciales_responde_401(cliente_prueba, headers):
    respuesta = cliente_prueba.get("/yo", headers=headers)

    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "No autenticado."}
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"


def test_get_usuario_actual_con_token_alterado_responde_401(cliente_prueba):
    token = crear_token_acceso(15, roles.MEDICO)
    alterado = token[:-2] + ("AA" if token[-2:] != "AA" else "BB")

    respuesta = cliente_prueba.get("/yo", headers={"Authorization": f"Bearer {alterado}"})

    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "Token inválido."}


def test_get_usuario_actual_con_token_vencido_responde_401(cliente_prueba):
    token = firmar(claims(exp=datetime.now(timezone.utc) - timedelta(minutes=1)))

    respuesta = cliente_prueba.get("/yo", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 401
    assert respuesta.json() == {"detail": "El token expiró."}


def test_requiere_rol_deja_pasar_el_rol_correcto(cliente_prueba):
    respuesta = cliente_prueba.get("/solo-admin", headers=con_token(rol=roles.ADMIN_CMP, id_usuario=3))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"id_usuario": 3}


def test_requiere_rol_rechaza_otro_rol_con_403(cliente_prueba):
    respuesta = cliente_prueba.get("/solo-admin", headers=con_token(rol=roles.MEDICO))

    assert respuesta.status_code == 403
    assert respuesta.json() == {"detail": "No tienes permiso para esta acción."}


def test_requiere_rol_sin_token_responde_401_y_no_403(cliente_prueba):
    assert cliente_prueba.get("/solo-admin").status_code == 401


@pytest.mark.parametrize(
    "rol, esperado",
    [(roles.TESORERO, 200), (roles.ADMIN_ASOCIACION, 200), (roles.MEDICO, 403)],
)
def test_requiere_rol_acepta_varios_roles(cliente_prueba, rol, esperado):
    assert cliente_prueba.get("/contable", headers=con_token(rol=rol)).status_code == esperado


def test_requiere_rol_sin_roles_es_un_error_de_programacion():
    with pytest.raises(ValueError):
        requiere_rol()


# --- Integración con un endpoint real protegido -----------------------------


def test_patch_medicos_exige_token(cliente):
    assert cliente.patch("/medicos/1", json={}).status_code == 401


def test_patch_medicos_rechaza_rol_no_autorizado(cliente):
    respuesta = cliente.patch("/medicos/1", json={}, headers=con_token(rol=roles.MEDICO))

    assert respuesta.status_code == 403
