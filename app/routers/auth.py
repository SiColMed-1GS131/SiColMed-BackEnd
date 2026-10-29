"""Endpoints /auth/register, /auth/login y /auth/me.

PENDIENTE (Login y permisos): completar AuthService y, cuando funcione,
registrar este router en main.py con `app.include_router(auth.router)`.
Mientras no esté registrado, no aparece en Swagger.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import (
    LoginSolicitud,
    RegistroSolicitud,
    TokenRespuesta,
    UsuarioRespuesta,
)
from app.security.auth import UsuarioAutenticado, get_usuario_actual
from app.services.auth import (
    AuthService,
    CuentaYaRegistrada,
    CredencialesInvalidas,
    MedicoNoEncontrado,
    UsuarioInactivo,
    UsuarioNoEncontrado,
    get_auth_service,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

Servicio = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/register",
    response_model=TokenRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear la cuenta de un médico ya registrado",
)
def registrar(datos: RegistroSolicitud, servicio: Servicio):
    try:
        return servicio.registrar(datos)
    except MedicoNoEncontrado as error:
        raise HTTPException(status_code=404, detail="Médico no encontrado.") from error
    except CuentaYaRegistrada as error:
        raise HTTPException(
            status_code=409, detail="El correo o la cuenta ya están registrados."
        ) from error


@router.post("/login", response_model=TokenRespuesta, summary="Iniciar sesión")
def login(datos: LoginSolicitud, servicio: Servicio):
    try:
        return servicio.login(datos)
    except CredencialesInvalidas as error:
        raise HTTPException(
            status_code=401,
            detail="Credenciales inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except UsuarioInactivo as error:
        raise HTTPException(status_code=403, detail="El usuario está inactivo.") from error


@router.get("/me", response_model=UsuarioRespuesta, summary="Usuario autenticado")
def me(
    usuario: Annotated[UsuarioAutenticado, Depends(get_usuario_actual)],
    servicio: Servicio,
):
    try:
        return servicio.obtener_usuario(usuario.id_usuario)
    except UsuarioNoEncontrado as error:
        raise HTTPException(
            status_code=401,
            detail="El usuario ya no existe.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    except UsuarioInactivo as error:
        raise HTTPException(status_code=403, detail="El usuario está inactivo.") from error
