"""Endpoints /auth/register, /auth/login y /auth/me.

PENDIENTE (Login y permisos): completar AuthService y, cuando funcione,
registrar este router en main.py con `app.include_router(auth.router)`.
Mientras no esté registrado, no aparece en Swagger.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.auth import (
    LoginSolicitud,
    RegistroSolicitud,
    TokenRespuesta,
    UsuarioRespuesta,
)
from app.security.auth import UsuarioAutenticado, get_usuario_actual
from app.services.auth import AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])

Servicio = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=TokenRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear la cuenta de un médico ya registrado",
)
def registrar(datos: RegistroSolicitud, servicio: Servicio):
    # TODO: traducir excepciones del service: médico no encontrado → 404,
    # correo o cuenta ya registrada → 409. Los errores de BD ya salen como 400.
    return servicio.registrar(datos)


@router.post("/login", response_model=TokenRespuesta, summary="Iniciar sesión")
def login(datos: LoginSolicitud, servicio: Servicio):
    # TODO: credenciales inválidas → 401 con {"detail": "Credenciales inválidas."}
    # (con WWW-Authenticate: Bearer); usuario inactivo → 403.
    return servicio.login(datos)


@router.get("/me", response_model=UsuarioRespuesta, summary="Usuario autenticado")
def me(
    usuario: Annotated[UsuarioAutenticado, Depends(get_usuario_actual)],
    servicio: Servicio,
):
    # get_usuario_actual ya responde 401 si falta el token, es inválido o expiró.
    # TODO: traducir excepciones del service: usuario inexistente → 401, inactivo → 403.
    return servicio.obtener_usuario(usuario.id_usuario)
